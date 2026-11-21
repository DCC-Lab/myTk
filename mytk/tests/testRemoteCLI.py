import contextlib
import io
import threading
import unittest

from mytk import App, RemoteControllable, remote_command
from mytk.remotecli import parse_command, run


class TestParseCommand(unittest.TestCase):
    """Pure parsing of the "name(args)" call string."""

    def test_no_args(self):
        self.assertEqual(parse_command("turn_on()"), ("turn_on", []))

    def test_bare_name(self):
        self.assertEqual(parse_command("turn_on"), ("turn_on", []))

    def test_positional_literals(self):
        self.assertEqual(parse_command("add(2, 3)"), ("add", [2, 3]))
        self.assertEqual(parse_command("greet('bob')"), ("greet", ["bob"]))
        self.assertEqual(
            parse_command("configure([1, 2], {'k': True})"),
            ("configure", [[1, 2], {"k": True}]),
        )

    def test_keyword_args_rejected(self):
        with self.assertRaises(ValueError):
            parse_command("f(a=1)")

    def test_non_call_rejected(self):
        with self.assertRaises(ValueError):
            parse_command("1 + 1")

    def test_non_literal_args_rejected(self):
        with self.assertRaises(ValueError):
            parse_command("f(some_variable)")


class CLIApp(App, RemoteControllable):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.flag = False

    @remote_command
    def flip(self):
        self.flag = True
        return self.flag


class TestRemoteCLI(unittest.TestCase):
    """End-to-end: the CLI drives a live server over a real socket."""

    def setUp(self):
        self.app = CLIApp(name=self.id())  # start_remote auto-registers commands
        self.rc = None
        self.output = None

    def tearDown(self):
        self.app.quit()

    def _run_cli(self, argv, timeout=1500):
        def client_call():
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                self.rc = run(argv)
            self.output = buffer.getvalue()

        thread = threading.Thread(target=client_call)
        self.app.after(int(timeout / 4), thread.start)
        self.app.after(timeout, self.app.quit)
        self.app.mainloop()
        thread.join(timeout=3)

    def test_call_prints_result(self):
        port = self.app.start_remote(port=0)
        self._run_cli(["flip()", "--port", str(port)])
        self.assertEqual(self.rc, 0)
        self.assertEqual(self.output.strip(), "True")
        self.assertTrue(self.app.flag)

    def test_list_shows_signatures(self):
        port = self.app.start_remote(port=0)
        self._run_cli(["--list", "--port", str(port)])
        self.assertEqual(self.rc, 0)
        self.assertIn("flip()", self.output)

    def test_app_name_mismatch_exits_nonzero(self):
        port = self.app.start_remote(port=0, app_name="Real")
        self._run_cli(["flip()", "--port", str(port), "--app-name", "Wrong"])
        self.assertEqual(self.rc, 2)
        self.assertFalse(self.app.flag)


class TestRemoteCLIOffline(unittest.TestCase):
    """Errors that do not need a running server."""

    def test_connection_refused_exits_1(self):
        # Nothing is listening on this port.
        rc = run(["flip()", "--port", "1"])
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
