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


DEFAULT_SERVICE_TYPE = "_mytk._tcp.local."


def discover(app_name=None, service_type=DEFAULT_SERVICE_TYPE, timeout=3.0):
    """Find a myTk remote server on the local network and connect to it.

    Browses for services advertised by :meth:`~mytk.remotecontrollable.RemoteControllable.advertise_remote`
    and returns a proxy to the first match, so callers never need a hard-coded
    host or port::

        far = mytk.discover(app_name="Microscope")
        far.turn_on()

    Requires the optional ``zeroconf`` package. Unlike the server side, this is
    imported directly (not through ``ModulesManager``) because a client is often
    a plain script with no Tk root, so a dialog-based installer would be wrong
    here; a clear ImportError is raised instead if the package is missing.

    Args:
        app_name (str, optional): If given, only match a server advertising this
            name (via its TXT record), and verify identity on connect. If None,
            the first server found for ``service_type`` is used.
        service_type (str): DNS-SD service type to browse. Must match what the
            server advertised.
        timeout (float): Seconds to wait for an advertisement before giving up.

    Returns:
        xmlrpc.client.ServerProxy: A proxy to the discovered server, as returned
        by :func:`connect`.

    Raises:
        ImportError: If the ``zeroconf`` package is not installed.
        TimeoutError: If no matching service appears within ``timeout``.
    """
    import time

    try:
        from zeroconf import ServiceBrowser, Zeroconf
    except ImportError as err:
        raise ImportError(
            "discover() needs the 'zeroconf' package. Install it with "
            "'pip install zeroconf'."
        ) from err

    found = {}

    class _Listener:
        def add_service(self, zc, type_, name):
            info = zc.get_service_info(type_, name)
            if info is not None:
                found[name] = info

        def update_service(self, zc, type_, name):
            info = zc.get_service_info(type_, name)
            if info is not None:
                found[name] = info

        def remove_service(self, zc, type_, name):
            found.pop(name, None)

    zc = Zeroconf()
    ServiceBrowser(zc, service_type, _Listener())
    try:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for info in list(found.values()):
                properties = {
                    key.decode(): (value or b"").decode()
                    for key, value in info.properties.items()
                }
                if app_name is not None and properties.get("app") != app_name:
                    continue
                addresses = info.parsed_addresses()
                if not addresses:
                    continue
                return connect(addresses[0], info.port, app_name)
            time.sleep(0.05)
    finally:
        zc.close()

    target = f" for app {app_name!r}" if app_name is not None else ""
    raise TimeoutError(
        f"No {service_type} server found{target} within {timeout}s"
    )


def browse(service_type=DEFAULT_SERVICE_TYPE, timeout=3.0):
    """List every myTk remote server advertised on the local network.

    Unlike :func:`discover`, which connects to the first match, this collects
    every service seen within ``timeout`` and returns their addresses *without*
    connecting, so a caller (or ``mytk-remote --browse``) can show what is
    running::

        for server in mytk.browse():
            print(server["app"], server["host"], server["port"])

    Requires the optional ``zeroconf`` package, imported directly (as in
    :func:`discover`) so a plain client script gets a clear ImportError rather
    than a Tk install dialog.

    Args:
        service_type (str): DNS-SD service type to browse. Must match what the
            servers advertised.
        timeout (float): Seconds to collect advertisements before returning.

    Returns:
        list[dict]: One entry per server, sorted by advertised name then
        address, each with keys ``"app"`` (advertised name, or None), ``"host"``
        (IP address), ``"port"`` (int), and ``"service"`` (the raw mDNS instance
        name).

    Raises:
        ImportError: If the ``zeroconf`` package is not installed.
    """
    import time

    try:
        from zeroconf import ServiceBrowser, Zeroconf
    except ImportError as err:
        raise ImportError(
            "browse() needs the 'zeroconf' package. Install it with "
            "'pip install zeroconf'."
        ) from err

    found = {}

    class _Listener:
        def add_service(self, zc, type_, name):
            info = zc.get_service_info(type_, name)
            if info is not None:
                found[name] = info

        def update_service(self, zc, type_, name):
            info = zc.get_service_info(type_, name)
            if info is not None:
                found[name] = info

        def remove_service(self, zc, type_, name):
            found.pop(name, None)

    zc = Zeroconf()
    ServiceBrowser(zc, service_type, _Listener())
    try:
        time.sleep(timeout)  # collect for the whole window, don't stop early
    finally:
        zc.close()

    servers = []
    for name, info in found.items():
        addresses = info.parsed_addresses()
        if not addresses:
            continue
        properties = {
            key.decode(): (value or b"").decode()
            for key, value in info.properties.items()
        }
        servers.append(
            {
                "app": properties.get("app"),
                "host": addresses[0],
                "port": info.port,
                "service": name,
            }
        )
    servers.sort(key=lambda server: (server["app"] or "", server["host"], server["port"]))
    return servers


def remote_cli(argv=None, *, host=DEFAULT_HOST, port=DEFAULT_PORT,
               app_name=None, prog="remote-ctl"):
    """A ready-made command-line client for a RemoteControllable app.

    A thin, embeddable wrapper over :func:`mytk.remotecli.run` — the same engine
    behind the ``mytk`` command — so a downstream app gets a *branded* CLI from
    its own entry point with almost no code::

        import sys, mytk
        sys.exit(mytk.remote_cli(app_name="My App", prog="my-cli"))

    Then, with the app running (and its remote server started)::

        my-cli "turn_on()"           # call an exposed function
        my-cli --list                # show what the server exposes
        my-cli "add(2, 3)"           # arguments are Python literals
        my-cli --host H --port P …    # override the baked-in target

    ``host``/``port``/``app_name`` become the defaults the user can still
    override on the command line. Command syntax, the discovery flags
    (``--discover``/``--browse``) and exit codes are exactly those of the
    ``mytk`` command, so there is one CLI to learn and one implementation to
    maintain. Pair it with :func:`mytk.install_command_on_path` to put the
    branded command on the user's PATH.

    Args:
        argv (list[str], optional): Arguments to parse (defaults to
            ``sys.argv[1:]``).
        host (str): Default server host, overridable with ``--host``.
        port (int): Default server port, overridable with ``--port``.
        app_name (str, optional): Default identity to verify/select,
            overridable with ``--app-name``.
        prog (str): Program name shown in usage/errors (the branded command).

    Returns:
        int: exit code — 0 ok, 1 remote error, 2 connection/usage error.
    """
    from .remotecli import run

    # run() parses with argparse, which raises SystemExit on a usage error
    # (e.g. no command). As an embeddable function we return that code instead
    # of letting SystemExit escape, so callers get the documented int contract.
    try:
        return run(
            argv, prog=prog, default_host=host, default_port=port,
            default_app_name=app_name,
        )
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2


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
