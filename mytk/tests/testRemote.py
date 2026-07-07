import threading
import unittest
import xmlrpc.client

import mytk
from mytk import App, RemoteControllable, remote_command


class RemoteApp(App, RemoteControllable):
    """An App made controllable by mixing in the capability."""


class TestRemoteRegistration(unittest.TestCase):
    """Pure registration behavior, no server or mainloop needed."""

    def setUp(self):
        self.app = RemoteApp(name=self.id())

    def tearDown(self):
        self.app.quit()

    def test_app_is_remote_controllable(self):
        self.assertIsInstance(self.app, RemoteControllable)

    def test_remote_as_decorator(self):
        @self.app.remote
        def foo():
            return 1

        self.assertIn("foo", self.app.remote_functions)
        self.assertIs(self.app.remote_functions["foo"], foo)

    def test_remote_direct_call_with_name(self):
        def bar():
            return 2

        returned = self.app.remote(bar, name="renamed")
        self.assertIs(returned, bar)
        self.assertIn("renamed", self.app.remote_functions)
        self.assertNotIn("bar", self.app.remote_functions)

    def test_remote_signatures(self):
        @self.app.remote
        def add(a, b):
            return a + b

        @self.app.remote
        def greet(name, greeting="hello"):
            return f"{greeting}, {name}"

        signatures = self.app.remote_signatures()
        self.assertEqual(signatures["add"], "(a, b)")
        self.assertEqual(signatures["greet"], "(name, greeting='hello')")


class TestRemoteServer(unittest.TestCase):
    """End-to-end: a client thread calls the server while the app runs."""

    def setUp(self):
        self.app = RemoteApp(name=self.id())
        self.result = None
        self.title_result = None
        self.blocked = False
        self.fault_message = None

    def tearDown(self):
        self.app.quit()

    def _run_with_client(self, client_call, timeout=5000):
        # Client runs off the main thread; the Tk mainloop drains the queue.
        # Quit as soon as the client thread finishes (polled on the main
        # thread) rather than after a fixed delay, so a slow runner gets as
        # long as it needs — the queue keeps draining until the client is done.
        # `timeout` is only a safety net so a genuinely hung call cannot wedge
        # the suite.
        thread = threading.Thread(target=client_call)

        def check(remaining):
            if not thread.is_alive() or remaining <= 0:
                self.app.quit()
            else:
                self.app.after(25, lambda: check(remaining - 25))

        def start():
            thread.start()
            check(timeout)

        self.app.after(50, start)
        self.app.mainloop()
        thread.join(timeout=3)

    def test_remote_call_returns_value(self):
        @self.app.remote
        def add(a, b):
            return a + b

        port = self.app.start_remote(port=0)

        def client_call():
            self.result = mytk.connect(port=port).add(2, 3)

        self._run_with_client(client_call)
        self.assertEqual(self.result, 5)

    def test_remote_runs_on_main_thread(self):
        # Touching a Tk widget only works on the main thread; getting the
        # value back proves the call was marshaled there.
        @self.app.remote
        def set_title(text):
            self.app.window.widget.title(text)
            return self.app.window.widget.title()

        port = self.app.start_remote(port=0)

        def client_call():
            self.title_result = mytk.connect(port=port).set_title("hello-remote")

        self._run_with_client(client_call)
        self.assertEqual(self.title_result, "hello-remote")

    def test_remote_signatures_over_the_wire(self):
        @self.app.remote
        def add(a, b):
            return a + b

        port = self.app.start_remote(port=0)

        def client_call():
            self.result = mytk.connect(port=port).remote_signatures()

        self._run_with_client(client_call)
        self.assertEqual(self.result["add"], "(a, b)")

    def test_remote_app_name(self):
        port = self.app.start_remote(port=0, app_name="Server-A")

        def client_call():
            self.result = mytk.connect(port=port).remote_app_name()

        self._run_with_client(client_call)
        self.assertEqual(self.result, "Server-A")

    def test_remote_app_name_defaults_to_app_name(self):
        # No explicit app_name -> falls back to the App's name.
        port = self.app.start_remote(port=0)

        def client_call():
            self.result = mytk.connect(port=port).remote_app_name()

        self._run_with_client(client_call)
        self.assertEqual(self.result, self.app.name)

    def test_connect_matching_app_name_ok(self):
        @self.app.remote
        def add(a, b):
            return a + b

        port = self.app.start_remote(port=0, app_name="Server-A")

        def client_call():
            self.result = mytk.connect(port=port, app_name="Server-A").add(1, 1)

        self._run_with_client(client_call)
        self.assertEqual(self.result, 2)

    def test_connect_wrong_app_name_raises(self):
        port = self.app.start_remote(port=0, app_name="Server-A")

        def client_call():
            try:
                mytk.connect(port=port, app_name="Server-B")
            except mytk.RemoteAppMismatch:
                self.blocked = True

        self._run_with_client(client_call)
        self.assertTrue(self.blocked)

    def test_proxy_validates_against_signatures(self):
        @self.app.remote
        def add(a, b):
            return a + b

        port = self.app.start_remote(port=0)

        def client_call():
            from mytk.remote import RemoteAppProxy

            proxy = RemoteAppProxy()
            proxy.configure(port=port)
            self.result = proxy.add(2, 3)  # known -> forwarded
            try:
                proxy.nope()  # unknown -> caught before the network call
            except AttributeError:
                self.blocked = True

        self._run_with_client(client_call)
        self.assertEqual(self.result, 5)
        self.assertTrue(self.blocked)

    def test_unregistered_function_not_exposed(self):
        @self.app.remote
        def ping():
            return "pong"

        port = self.app.start_remote(port=0)

        def client_call():
            try:
                mytk.connect(port=port).not_exposed()
            except xmlrpc.client.Fault:
                self.blocked = True

        self._run_with_client(client_call)
        self.assertTrue(self.blocked)

    def test_remote_exception_propagates(self):
        @self.app.remote
        def boom():
            raise ValueError("nope")

        port = self.app.start_remote(port=0)

        def client_call():
            try:
                mytk.connect(port=port).boom()
            except xmlrpc.client.Fault as exc:
                self.fault_message = str(exc)

        self._run_with_client(client_call)
        self.assertIsNotNone(self.fault_message)
        self.assertIn("nope", self.fault_message)


class CommandApp(App, RemoteControllable):
    """An App exposing methods declared in its class body via @remote_command."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.flag = False

    @remote_command
    def flip(self):
        self.flag = True
        return self.flag

    @remote_command(name="status")
    def read_status(self):
        return {"flag": self.flag}

    @property
    def boom(self):  # scanning must never invoke this getter
        raise RuntimeError("property getter triggered during scan")


class TestRemoteCommands(unittest.TestCase):
    """Class-body @remote_command markers registered via register_remote_commands()."""

    def setUp(self):
        self.app = CommandApp(name=self.id())
        self.result = None

    def tearDown(self):
        self.app.quit()

    def _run_with_client(self, client_call, timeout=5000):
        # Quit as soon as the client thread finishes (polled on the main
        # thread) instead of after a fixed delay; `timeout` is only a safety
        # net. See TestRemoteServer._run_with_client for the rationale.
        thread = threading.Thread(target=client_call)

        def check(remaining):
            if not thread.is_alive() or remaining <= 0:
                self.app.quit()
            else:
                self.app.after(25, lambda: check(remaining - 25))

        def start():
            thread.start()
            check(timeout)

        self.app.after(50, start)
        self.app.mainloop()
        thread.join(timeout=3)

    def test_register_scans_class_without_triggering_properties(self):
        # Sanity: the property really does raise when its getter runs...
        with self.assertRaises(RuntimeError):
            _ = self.app.boom
        # ...yet scanning the class to register commands must not touch it.
        names = self.app.register_remote_commands()
        self.assertEqual(set(names), {"flip", "status"})

    def test_start_remote_auto_registers_commands(self):
        # No explicit register_remote_commands() call — start_remote does it.
        self.app.start_remote(port=0)
        signatures = self.app.remote_signatures()
        self.assertIn("flip", signatures)
        self.assertIn("status", signatures)

    def test_bare_command_uses_method_name(self):
        self.app.register_remote_commands()
        self.assertIn("flip", self.app.remote_signatures())

    def test_named_command_uses_custom_name(self):
        self.app.register_remote_commands()
        signatures = self.app.remote_signatures()
        self.assertIn("status", signatures)
        self.assertNotIn("read_status", signatures)

    def test_command_round_trip(self):
        self.app.register_remote_commands()
        port = self.app.start_remote(port=0)

        def client_call():
            proxy = mytk.connect(port=port)
            self.result = (proxy.flip(), proxy.status())

        self._run_with_client(client_call)
        self.assertEqual(self.result, (True, {"flag": True}))

    def test_remote_still_works_alongside_commands(self):
        # Backward-compat: imperative registration coexists with tagged methods.
        self.app.register_remote_commands()

        @self.app.remote
        def extra():
            return 42

        self.assertEqual({"flip", "status", "extra"}, set(self.app.remote_signatures()))


if __name__ == "__main__":
    unittest.main()
