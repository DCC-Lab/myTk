"""remote.py — Lightweight client access to a running myTk App's remote API.

An `App` that mixes in :class:`~mytk.remotecontrollable.RemoteControllable` can
expose functions with the ``@app.remote`` decorator and serve them with
``app.start_remote()``. From another process, connect and call them by name::

    import mytk
    mytk.remote_app.blabla(1, 2)          # default localhost:8777
    far = mytk.connect("192.168.1.5", 9000)
    far.blabla(1, 2)

The transport is stdlib XML-RPC, so arguments and return values must be
XML-RPC serializable (numbers, str, bool, None, list, dict).
"""

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8777

# Methods every RemoteControllable server auto-exposes (see start_remote); they
# are not listed by remote_signatures (which reports user functions only), so
# the client must treat them as always available.
BUILTIN_REMOTE_METHODS = ("remote_signatures", "remote_app_name")


class RemoteAppMismatch(Exception):
    """Raised when a server's app name does not match the expected one.

    Lets a client be sure it reached the intended app when several apps run on
    the same machine (see :meth:`mytk.remotecontrollable.RemoteControllable.remote_app_name`).
    """


def connect(host=DEFAULT_HOST, port=DEFAULT_PORT, app_name=None):
    """Return a proxy to a myTk remote server.

    Exposed functions are called as attributes of the proxy::

        proxy = connect("127.0.0.1", 8777)
        proxy.blabla(1, 2)

    Args:
        host (str): Server host. Defaults to localhost.
        port (int): Server port. Defaults to 8777.
        app_name (str, optional): If given, verify the server reports this name
            and raise :class:`RemoteAppMismatch` otherwise. Useful when several
            apps run on the same machine.

    Returns:
        xmlrpc.client.ServerProxy: A proxy whose attribute calls become
        remote calls.

    Raises:
        RemoteAppMismatch: If ``app_name`` is given and does not match.
    """
    from xmlrpc.client import ServerProxy

    proxy = ServerProxy(f"http://{host}:{port}/", allow_none=True)
    if app_name is not None:
        actual = proxy.remote_app_name()
        if actual != app_name:
            raise RemoteAppMismatch(
                f"Expected app {app_name!r} at {host}:{port}, "
                f"but it identifies as {actual!r}"
            )
    return proxy


class RemoteAppProxy:
    """Module-level proxy that connects on first use.

    Lets ``mytk.remote_app.blabla()`` work without an explicit ``connect()``.
    Defaults to localhost:8777; call :meth:`configure` to target another
    server before the first call.

    On first use it fetches the server's exposed API (``remote_signatures``)
    and validates every call against it, so an unknown method raises a clear
    ``AttributeError`` here instead of a cryptic XML-RPC fault when called.

    Every attribute access that is not one of this proxy's own names is
    forwarded to the remote server, so avoid exposing remote functions literally
    named ``host``, ``port``, ``proxy``, ``app_name``, ``signatures``, or
    ``configure``.
    """

    def __init__(self):
        self.host = DEFAULT_HOST
        self.port = DEFAULT_PORT
        self.app_name = None
        self.proxy = None
        self.signatures = None

    def configure(self, host=None, port=None, app_name=None):
        """Point the proxy at a different server, dropping any open connection.

        Args:
            host (str, optional): New host. Unchanged if None.
            port (int, optional): New port. Unchanged if None.
            app_name (str, optional): Expected server identity to verify on the
                next connection. Unchanged if None.
        """
        if host is not None:
            self.host = host
        if port is not None:
            self.port = port
        if app_name is not None:
            self.app_name = app_name
        self.proxy = None
        self.signatures = None

    def __getattr__(self, name):
        # __getattr__ only runs for names not found normally. Dunders and other
        # underscore-prefixed names are Python internals (copy/pickle probes),
        # never remote calls. Reach into __dict__ for our own state so this can
        # never recurse, even before __init__ has run.
        if name.startswith("_"):
            raise AttributeError(name)

        proxy = self.__dict__.get("proxy")
        if proxy is None:
            proxy = connect(
                self.__dict__.get("host", DEFAULT_HOST),
                self.__dict__.get("port", DEFAULT_PORT),
                self.__dict__.get("app_name"),
            )
            self.proxy = proxy
            self.signatures = None  # refetch for the new connection

        available = self.__dict__.get("signatures")
        if available is None:
            available = proxy.remote_signatures()
            self.signatures = available

        if name not in available and name not in BUILTIN_REMOTE_METHODS:
            offered = sorted(set(available) | set(BUILTIN_REMOTE_METHODS))
            raise AttributeError(
                f"{name!r} is not exposed by the remote app. "
                f"Available: {offered}"
            )
        return getattr(proxy, name)


remote_app = RemoteAppProxy()
