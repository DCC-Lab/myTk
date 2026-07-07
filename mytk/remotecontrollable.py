"""remotecontrollable.py — Capability mixin exposing an App over RPC.

`RemoteControllable` is a capability mixin, in the same spirit as
`EventCapable` and `DragAndDropCapable`. Mix it into an `App` subclass to let
external processes call selected functions on the running application::

    from mytk import App, RemoteControllable

    class MyApp(App, RemoteControllable):
        pass

    app = MyApp(name="Server")

    @app.remote
    def add(a, b):
        return a + b

    app.start_remote()      # localhost:8777
    app.mainloop()

Clients connect with ``mytk.connect(...)`` or ``mytk.remote_app`` (see
:mod:`mytk.remote`). The transport is stdlib XML-RPC, so arguments and return
values must be XML-RPC serializable (numbers, str, bool, None, list, dict).

The host class must provide ``schedule_on_main_thread`` and ``root`` (both are
supplied by `App`): every call is marshaled onto the Tk main thread, so exposed
functions may safely touch widgets.
"""

from contextlib import suppress


class RemoteControllable:
    """Mixin adding a remote-procedure-call server to an `App`.

    Designed to be combined with `App`, which provides the Tk main-thread queue
    (`schedule_on_main_thread`) and the root window (`root`). Not usable on its
    own. Works in either inheritance order — ``class MyApp(App,
    RemoteControllable)`` or ``class MyApp(RemoteControllable, App)`` — because
    it cooperates through ``super().__init__`` and shuts the server down from a
    root ``<Destroy>`` binding rather than by overriding ``quit``.
    """

    def __init__(self, *args, **kwargs):
        """Initialize remote-call state for cooperative multiple inheritance."""
        self.remote_functions = {}
        self.remote_server = None
        self.remote_call_timeout = 30
        self.app_name = None
        super().__init__(*args, **kwargs)  # cooperative!

    def remote(self, fct=None, *, name=None):
        """Exposes a function for remote invocation by clients.

        Usable as a decorator (``@app.remote``) or directly
        (``app.remote(fct)``). Only exposed functions are reachable. The call
        runs on the Tk main thread, so it may safely touch widgets. Arguments
        and the return value must be XML-RPC serializable (numbers, str, bool,
        None, list, dict).

        Args:
            fct (callable, optional): The function to expose. Omitted when used
                as a bare ``@app.remote`` decorator.
            name (str, optional): Name clients use to call it. Defaults to the
                function's own name.

        Returns:
            callable: The function, so it can be used as a decorator.
        """
        if fct is None:
            return lambda f: self.remote(f, name=name)
        self.remote_functions[name or fct.__name__] = fct
        return fct

    def remote_signatures(self):
        """Returns the signature of every exposed function.

        Useful for discovering the remote API. Keys are the names clients use;
        values are signature strings such as ``"(a, b)"``. Also exposed
        remotely, so a client can call ``remote_app.remote_signatures()`` to
        introspect the server.

        Returns:
            dict[str, str]: Mapping of function name to its signature string.
        """
        import inspect

        return {
            name: str(inspect.signature(fct))
            for name, fct in self.remote_functions.items()
        }

    def remote_app_name(self):
        """Returns this app's name so a client can confirm it reached the
        intended server when several apps run on the same machine.

        Exposed remotely and used by :func:`mytk.remote.connect` when its
        ``app_name`` argument is given.

        Returns:
            str | None: The app name (see :meth:`start_remote`).
        """
        return self.app_name

    def start_remote(self, port=8777, host="127.0.0.1", app_name=None):
        """Starts a background server exposing the functions registered with
        :meth:`remote`.

        Localhost-only by default. The server runs in a daemon thread; each
        call is marshaled onto the Tk main thread and its return value sent
        back to the client. Safe to call once; further calls are no-ops.

        Args:
            port (int): Port to bind. Use 0 to let the OS pick a free port.
            host (str): Interface to bind. Defaults to localhost.
            app_name (str, optional): Identity clients can verify (see
                :meth:`remote_app_name`). Defaults to ``self.app_name`` if
                already set, otherwise the App's ``name``.

        Returns:
            int: The port actually bound (useful with ``port=0``).
        """
        import threading
        from xmlrpc.server import SimpleXMLRPCServer

        if self.remote_server is not None:
            return self.remote_server.server_address[1]

        if app_name is not None:
            self.app_name = app_name
        if self.app_name is None:
            self.app_name = getattr(self, "name", None)

        server = SimpleXMLRPCServer(
            (host, port), allow_none=True, logRequests=False
        )
        for exposed_name, fct in self.remote_functions.items():
            server.register_function(self.remote_wrapper(fct), exposed_name)

        # Always let clients introspect the exposed API and verify identity.
        server.register_function(
            self.remote_wrapper(self.remote_signatures), "remote_signatures"
        )
        server.register_function(
            self.remote_wrapper(self.remote_app_name), "remote_app_name"
        )

        self.remote_server = server
        thread = threading.Thread(
            target=server.serve_forever, name="mytk-remote", daemon=True
        )
        thread.start()

        # Stop the server when the app window goes away, without overriding
        # quit() (keeps this independent of the inheritance order). add="+"
        # preserves App's own root <Destroy> handler.
        self.root.bind("<Destroy>", self.stop_remote_on_destroy, add="+")
        return server.server_address[1]

    def stop_remote(self):
        """Shuts down the remote server if it is running."""
        if self.remote_server is not None:
            server, self.remote_server = self.remote_server, None
            with suppress(Exception):
                server.shutdown()
            with suppress(Exception):
                server.server_close()

    def stop_remote_on_destroy(self, event):
        """Root <Destroy> handler: shut the server down with the window."""
        if event.widget is self.root:
            self.stop_remote()

    def remote_wrapper(self, fct):
        """Wraps an exposed function so the RPC thread runs it on the main
        thread and blocks for its result."""

        def wrapper(*args):
            return self.call_on_main_thread(fct, args)

        return wrapper

    def call_on_main_thread(self, fct, args=(), kwargs=None):
        """Runs `fct` on the Tk main thread and returns its result, blocking
        the calling (RPC) thread. Exceptions propagate to the caller."""
        from concurrent.futures import Future

        future = Future()

        def task():
            try:
                future.set_result(fct(*args, **(kwargs or {})))
            except Exception as exc:
                future.set_exception(exc)

        self.schedule_on_main_thread(task)
        return future.result(timeout=self.remote_call_timeout)
