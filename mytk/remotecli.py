"""remotecli.py — Command-line client for a RemoteControllable mytk app.

Send a single call to a running app that exposed functions with
:class:`~mytk.remotecontrollable.RemoteControllable` and print the result::

    python -m mytk --remote "turn_on()"
    python -m mytk --remote "set_power(2.5)" --port 9000
    mytk-remote "add(2, 3)"                  # standalone console script
    mytk-remote --app-name Acquisition "status()"
    mytk-remote --list                       # show the exposed functions

Arguments in the call string must be Python literals (numbers, strings,
True/False/None, lists, dicts, tuples); a bare ``"turn_on"`` is treated as
``"turn_on()"``. Keyword arguments are not supported — XML-RPC carries
positional arguments only.
"""

import argparse
import ast
import sys
import xmlrpc.client

from .remote import DEFAULT_HOST, DEFAULT_PORT, RemoteAppMismatch, connect


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


def build_parser(prog=None):
    """Build the argument parser for the remote command-line client."""
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
        "--host", default=DEFAULT_HOST, help=f"server host (default: {DEFAULT_HOST})"
    )
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT,
        help=f"server port (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--app-name", default=None,
        help="verify the server identifies as this name before calling",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="list the exposed functions and their signatures, then exit",
    )
    return parser


def run(argv=None, prog=None):
    """Run one remote command-line invocation.

    Args:
        argv (list[str], optional): Arguments to parse (defaults to
            ``sys.argv[1:]``).
        prog (str, optional): Program name shown in usage/errors.

    Returns:
        int: Process exit code (0 success, 1 runtime error, 2 usage/identity).
    """
    parser = build_parser(prog)
    args = parser.parse_args(argv)

    if not args.list and not args.command:
        parser.error("a command is required unless --list is given")

    try:
        proxy = connect(args.host, args.port, app_name=args.app_name)

        if args.list:
            signatures = proxy.remote_signatures()
            for name in sorted(signatures):
                print(f"{name}{signatures[name]}")
            return 0

        name, call_args = parse_command(args.command)
        result = getattr(proxy, name)(*call_args)
        if result is not None:
            print(result)
        return 0
    except ValueError as exc:  # bad command string
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except RemoteAppMismatch as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except xmlrpc.client.Fault as exc:
        print(f"error: remote call failed: {exc.faultString}", file=sys.stderr)
        return 1
    except (ConnectionError, OSError) as exc:
        print(
            f"error: could not reach a mytk app at {args.host}:{args.port} ({exc})",
            file=sys.stderr,
        )
        return 1


def main():
    """Console-script entry point (``mytk-remote``)."""
    raise SystemExit(run(prog="mytk-remote"))


if __name__ == "__main__":
    main()
