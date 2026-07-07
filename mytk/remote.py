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


def connect(host=DEFAULT_HOST, port=DEFAULT_PORT):
    """Return a proxy to a myTk remote server.

    Exposed functions are called as attributes of the proxy::

        proxy = connect("127.0.0.1", 8777)
        proxy.blabla(1, 2)

    Args:
        host (str): Server host. Defaults to localhost.
        port (int): Server port. Defaults to 8777.

    Returns:
        xmlrpc.client.ServerProxy: A proxy whose attribute calls become
        remote calls.
    """
    from xmlrpc.client import ServerProxy

    return ServerProxy(f"http://{host}:{port}/", allow_none=True)


class RemoteAppProxy:
    """Module-level proxy that connects on first use.

    Lets ``mytk.remote_app.blabla()`` work without an explicit ``connect()``.
    Defaults to localhost:8777; call :meth:`configure` to target another
    server before the first call.

    Every attribute access that is not one of this proxy's own names is
    forwarded to the remote server as a callable, so avoid exposing remote
    functions literally named ``host``, ``port``, ``proxy``, or ``configure``.
    """

    def __init__(self):
        self.host = DEFAULT_HOST
        self.port = DEFAULT_PORT
        self.proxy = None

    def configure(self, host=None, port=None):
        """Point the proxy at a different server, dropping any open connection.

        Args:
            host (str, optional): New host. Unchanged if None.
            port (int, optional): New port. Unchanged if None.
        """
        if host is not None:
            self.host = host
        if port is not None:
            self.port = port
        self.proxy = None

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
            )
            self.proxy = proxy
        return getattr(proxy, name)


remote_app = RemoteAppProxy()
