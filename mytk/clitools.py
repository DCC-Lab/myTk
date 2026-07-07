"""clitools.py — install a launcher for this program onto the user's PATH.

Lets a packaged myTk app (or a source checkout) expose a command-line entry
point — e.g. a control CLI for a :class:`~mytk.remotecontrollable.RemoteControllable`
app — without the user hand-writing shell scripts. Pairs with
:func:`mytk.remote_cli`: the installed launcher re-enters this same program in
CLI mode, which then talks to the running app over the remote API.
"""

import os
import sys
from pathlib import Path

__all__ = ["install_command_on_path"]

DEFAULT_BIN_DIRS = ("/usr/local/bin", "~/.local/bin", "~/bin")


def install_command_on_path(name, *, arguments=(), directories=None):
    """Install a ``name`` command that re-launches this program, on PATH.

    Writes a small POSIX wrapper (NOT a bare symlink) that runs the current
    program with the SAME interpreter/binary it was installed from, so the
    command keeps this environment's dependencies:

      * packaged app (``sys.frozen``): the wrapper calls the bundle binary;
      * source checkout: it calls this interpreter + the ``__main__`` script.

    ``arguments`` are inserted before the user's args, so an entry point that
    dispatches on a subcommand can be routed into CLI mode — e.g.
    ``arguments=("ctl",)`` makes the wrapper run ``<program> ctl "$@"``.

    Tries each of ``directories`` (default: ``/usr/local/bin``, ``~/.local/bin``,
    ``~/bin``) and installs into the first writable one, so it works with or
    without admin rights.

    Args:
        name (str): The command name to create (the launcher's filename).
        arguments (tuple[str, ...]): Tokens inserted before the user's args, to
            route the launcher into a subcommand/CLI mode.
        directories (list, optional): Candidate bin directories, tried in order.
            Defaults to :data:`DEFAULT_BIN_DIRS`.

    Returns:
        tuple[pathlib.Path, str]: the created command path, and a note (empty
        unless its directory is not on PATH, then it explains how to add it).

    Raises:
        RuntimeError: if none of the directories are writable.
        NotImplementedError: on Windows (POSIX wrapper does not apply).
    """
    if sys.platform.startswith("win"):
        raise NotImplementedError(
            "install_command_on_path writes a POSIX /bin/sh wrapper; Windows "
            "needs a different launcher (not implemented).")

    # sys.executable VERBATIM — never resolve() it. A venv's python is a symlink
    # to the base interpreter; following it drops the venv's site-packages, so
    # the installed command would silently lose this env's dependencies.
    if getattr(sys, "frozen", False):
        parts = [sys.executable]
    else:
        main = sys.modules.get("__main__")
        script = getattr(main, "__file__", None) or sys.argv[0]
        parts = [sys.executable, os.path.abspath(script)]
    parts += list(arguments)
    command = " ".join('"{0}"'.format(part) for part in parts)
    wrapper = '#!/bin/sh\nexec {0} "$@"\n'.format(command)

    candidates = DEFAULT_BIN_DIRS if directories is None else directories
    candidates = [Path(str(d)).expanduser() for d in candidates]

    problems = []
    for directory in candidates:
        entry = directory / name
        try:
            directory.mkdir(parents=True, exist_ok=True)
            if entry.is_symlink() or entry.exists():
                entry.unlink()
            entry.write_text(wrapper)
            entry.chmod(0o755)
        except OSError as err:
            problems.append("{0} ({1})".format(directory, err))
            continue

        note = ""
        if str(directory) not in os.environ.get("PATH", "").split(os.pathsep):
            note = ("{0} is not on your PATH — add it to your shell profile:\n"
                    "    export PATH=\"{0}:$PATH\"".format(directory))
        return entry, note

    raise RuntimeError(
        "Could not write {0} to any of:\n  {1}".format(
            name, "\n  ".join(problems)))
