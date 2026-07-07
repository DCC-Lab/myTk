"""remotecli.py — Command-line client for a RemoteControllable mytk app.

Send a single call to a running app that exposed functions with
:class:`~mytk.remotecontrollable.RemoteControllable` and print the result::

    mytk "add(2, 3)"                        # the `mytk` console script
    mytk --app-name Acquisition "status()"
    mytk --list                             # show the exposed functions
    python -m mytk --remote "turn_on()"     # equivalent module form
    python -m mytk --remote "set_power(2.5)" --port 9000

(``mytk-remote`` is a kept-for-compatibility alias of ``mytk``.) Instead of a
fixed ``--host``/``--port``, the server can be located on the local network via
mDNS/Bonjour (as published by ``advertise_remote``)::

    mytk --discover "turn_on()"
    mytk --discover --app-name Microscope "status()"
    mytk --discover --list
    mytk --browse                           # list all apps on the network

Arguments in the call string must be Python literals (numbers, strings,
True/False/None, lists, dicts, tuples); a bare ``"turn_on"`` is treated as
``"turn_on()"``. Keyword arguments are not supported — XML-RPC carries
positional arguments only.
"""

import argparse
import ast
import sys
import xmlrpc.client

from .remote import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_SERVICE_TYPE,
    RemoteAppMismatch,
    browse,
    connect,
    discover,
)


def parse_command(command):
    """Parse a ``"name(arg, ...)"`` call string into ``(name, args)``.

    Args:
        command (str): A call such as ``"turn_on()"`` or ``"add(2, 3)"``. A
            bare name (``"turn_on"``) is accepted and means a no-argument call.

    Returns:
        tuple[str, list]: The function name and its positional arguments.

    Raises:
        ValueError: If it is not a simple call of literal arguments, or uses
            keyword arguments (unsupported over XML-RPC).
    """
    try:
        node = ast.parse(command.strip(), mode="eval").body
    except SyntaxError as exc:
        raise ValueError(f"Could not parse command {command!r}: {exc}") from exc

    if isinstance(node, ast.Name):
        return node.id, []
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        raise ValueError(f"Not a function call: {command!r}")
    if node.keywords:
        raise ValueError("Keyword arguments are not supported over XML-RPC")

    try:
        args = [ast.literal_eval(argument) for argument in node.args]
    except (ValueError, SyntaxError) as exc:
        raise ValueError(
            f"Arguments must be literals (numbers, strings, lists, ...): {exc}"
        ) from exc
    return node.func.id, args


def build_parser(prog=None, *, default_host=DEFAULT_HOST,
                 default_port=DEFAULT_PORT, default_app_name=None):
    """Build the argument parser for the remote command-line client.

    ``default_host``/``default_port``/``default_app_name`` let an embedding app
    (see :func:`mytk.remote_cli`) bake in its own connection defaults while
    still allowing the user to override them with ``--host``/``--port``/
    ``--app-name``.
    """
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Call a function on a running RemoteControllable mytk app.",
    )
    parser.add_argument(
        "command",
        nargs="?",
        help='function call, e.g. "turn_on()" or "add(2, 3)"',
    )
    parser.add_argument(
        "--host", default=default_host,
        help=f"server host (default: {default_host})",
    )
    parser.add_argument(
        "--port", type=int, default=default_port,
        help=f"server port (default: {default_port})",
    )
    parser.add_argument(
        "--app-name", default=default_app_name,
        help="verify the server identifies as this name before calling; "
             "with --discover, also selects which advertised app to use",
    )
    parser.add_argument(
        "--discover", action="store_true",
        help="find the server on the local network via mDNS instead of "
             "using --host/--port",
    )
    parser.add_argument(
        "--browse", action="store_true",
        help="list every myTk app advertised on the local network "
             "(name and address), then exit; uses --service-type/--timeout",
    )
    parser.add_argument(
        "--service-type", default=DEFAULT_SERVICE_TYPE,
        help=f"mDNS service type to browse with --discover "
             f"(default: {DEFAULT_SERVICE_TYPE})",
    )
    parser.add_argument(
        "--timeout", type=float, default=3.0,
        help="seconds to wait for a service with --discover (default: 3.0)",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="list the exposed functions and their signatures, then exit",
    )
    return parser


def _print_result(result):
    """Print a remote call's return value.

    A ``dict`` is shown as an aligned ``key  value`` table (nicer for status
    snapshots); anything else is printed as-is. ``None`` prints nothing.
    """
    if result is None:
        return
    if isinstance(result, dict):
        width = max((len(str(key)) for key in result), default=0)
        for key, value in result.items():
            print(f"{str(key):<{width}}  {value}")
    else:
        print(result)


def run(argv=None, prog=None, *, default_host=DEFAULT_HOST,
        default_port=DEFAULT_PORT, default_app_name=None):
    """Run one remote command-line invocation.

    Args:
        argv (list[str], optional): Arguments to parse (defaults to
            ``sys.argv[1:]``).
        prog (str, optional): Program name shown in usage/errors.
        default_host (str): Host used when ``--host`` is not given. An embedding
            app (via :func:`mytk.remote_cli`) can bake in its own default.
        default_port (int): Port used when ``--port`` is not given.
        default_app_name (str, optional): Identity to verify/select when
            ``--app-name`` is not given.

    Returns:
        int: Process exit code (0 success, 1 runtime error, 2 usage/identity).
    """
    parser = build_parser(
        prog, default_host=default_host, default_port=default_port,
        default_app_name=default_app_name,
    )
    args = parser.parse_args(argv)

    if not args.list and not args.browse and not args.command:
        parser.error("a command is required unless --list or --browse is given")

    try:
        if args.browse:
            for server in browse(
                service_type=args.service_type, timeout=args.timeout
            ):
                label = server["app"] or server["service"]
                print(f"{label}\t{server['host']}:{server['port']}")
            return 0

        if args.discover:
            proxy = discover(
                app_name=args.app_name,
                service_type=args.service_type,
                timeout=args.timeout,
            )
        else:
            proxy = connect(args.host, args.port, app_name=args.app_name)

        if args.list:
            signatures = proxy.remote_signatures()
            for name in sorted(signatures):
                print(f"{name}{signatures[name]}")
            return 0

        name, call_args = parse_command(args.command)
        result = getattr(proxy, name)(*call_args)
        _print_result(result)
        return 0
    except ValueError as exc:  # bad command string
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except RemoteAppMismatch as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ImportError as exc:  # --discover without the zeroconf package
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except TimeoutError as exc:  # --discover found nothing in time
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except xmlrpc.client.Fault as exc:
        print(f"error: remote call failed: {exc.faultString}", file=sys.stderr)
        return 1
    except (ConnectionError, OSError) as exc:
        target = (
            "the discovered mytk app"
            if args.discover
            else f"a mytk app at {args.host}:{args.port}"
        )
        print(f"error: could not reach {target} ({exc})", file=sys.stderr)
        return 1


def main():
    """Console-script entry point for ``mytk`` (and its ``mytk-remote`` alias)."""
    raise SystemExit(run(prog="mytk"))


if __name__ == "__main__":
    main()
