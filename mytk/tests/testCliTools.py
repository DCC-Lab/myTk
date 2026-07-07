"""Tests for the CLI-tool helpers: install_command_on_path, remote_cli, and
App.add_file_menu_command.

The install tests are POSIX-only (the helper writes a /bin/sh wrapper and raises
NotImplementedError on Windows). The remote_cli tests spin up a real server and
drive it over a socket, like testRemote.py / testRemoteCLI.py.
"""

import contextlib
import io
import os
import stat
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from mytk import App, RemoteControllable
from mytk.clitools import install_command_on_path
from mytk.remote import remote_cli
from mytk.remotecli import _print_result


@unittest.skipIf(sys.platform.startswith("win"),
                 "install_command_on_path is POSIX-only")
class TestInstallCommandOnPath(unittest.TestCase):
    """Writing an executable launcher into a writable bin dir."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_writes_executable_wrapper_with_verbatim_executable(self):
        good = self.root / "bin"
        path, note = install_command_on_path(
            "my-cli", arguments=("ctl",), directories=[good])

        self.assertTrue(path.exists())
        mode = stat.S_IMODE(path.stat().st_mode)
        self.assertEqual(mode, 0o755)
        content = path.read_text()
        self.assertTrue(content.startswith("#!/bin/sh"))
        # The exact interpreter this env runs, NOT a resolved base interpreter.
        self.assertIn(sys.executable, content)
        # arguments are placed before the forwarded user args ("$@").
        self.assertIn('"ctl" "$@"', content)

    def test_falls_back_to_next_writable_directory(self):
        # A path *under a regular file* cannot be created as a directory.
        blocker = self.root / "not-a-dir"
        blocker.write_text("x")
        bad = blocker / "bin"
        good = self.root / "good"

        path, _ = install_command_on_path(
            "my-cli", directories=[bad, good])

        self.assertEqual(path.parent, good)
        self.assertTrue(path.exists())

    def test_raises_when_no_directory_is_writable(self):
        blocker = self.root / "file"
        blocker.write_text("x")
        bad = blocker / "bin"
        with self.assertRaises(RuntimeError):
            install_command_on_path("my-cli", directories=[bad])

    def test_note_empty_when_dir_on_path_else_explains(self):
        good = self.root / "bin"

        with mock.patch.dict(os.environ, {"PATH": str(good)}):
            _, note = install_command_on_path("my-cli", directories=[good])
        self.assertEqual(note, "")

        with mock.patch.dict(os.environ, {"PATH": "/usr/bin"}):
            _, note = install_command_on_path("my-cli", directories=[good])
        self.assertIn("not on your PATH", note)

    def test_overwrites_existing_file_or_symlink(self):
        good = self.root / "bin"
        good.mkdir()
        stale = good / "my-cli"
        stale.write_text("old contents")

        path, _ = install_command_on_path("my-cli", directories=[good])
        self.assertEqual(path, stale)
        self.assertTrue(path.read_text().startswith("#!/bin/sh"))


class _CliApp(App, RemoteControllable):
    def __init__(self, **kwargs):
        super().__init__(no_window=True, **kwargs)

    def add(self, a, b):
        return a + b

    def snapshot(self):
        return {"x": 1, "y": 2}


class TestRemoteCli(unittest.TestCase):
    """remote_cli() drives a live RemoteControllable app end-to-end, reusing the
    general `mytk` CLI engine (paren-call syntax, its exit codes)."""

    def setUp(self):
        self.app = _CliApp(name="T")
        self.app.remote(self.app.add)
        self.app.remote(self.app.snapshot)
        self.rc = None
        self.output = None

    def tearDown(self):
        self.app.quit()

    def _run_cli(self, argv, *, app_name=None, host=None, port=None,
                 timeout=5000):
        # Quit as soon as the client thread finishes (polled on the main
        # thread); the queue keeps draining until then. `timeout` is a safety
        # net. (Same robust pattern as testRemote._run_with_client.)
        kwargs = {}
        if app_name is not None:
            kwargs["app_name"] = app_name
        if host is not None:
            kwargs["host"] = host
        if port is not None:
            kwargs["port"] = port

        def client_call():
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                self.rc = remote_cli(argv, **kwargs)
            self.output = buffer.getvalue()

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

    def test_call_prints_result(self):
        port = self.app.start_remote(port=0)
        self._run_cli(["add(2, 3)"], app_name="T", port=port)
        self.assertEqual(self.rc, 0)
        self.assertEqual(self.output.strip(), "5")

    def test_dict_result_printed_as_table(self):
        port = self.app.start_remote(port=0)
        self._run_cli(["snapshot()"], app_name="T", port=port)
        self.assertEqual(self.rc, 0)
        self.assertIn("x  1", self.output)
        self.assertIn("y  2", self.output)

    def test_list_uses_introspected_api(self):
        port = self.app.start_remote(port=0)
        self._run_cli(["--list"], port=port)
        self.assertEqual(self.rc, 0)
        self.assertIn("add(a, b)", self.output)
        self.assertIn("snapshot()", self.output)

    def test_unknown_command_exits_1(self):
        # Reconciled with the `mytk` tool: an unknown command is not
        # pre-validated (that would cost a round-trip per call); the server
        # faults and the CLI reports a remote error (exit 1).
        port = self.app.start_remote(port=0)
        self._run_cli(["nope()"], port=port)
        self.assertEqual(self.rc, 1)

    def test_no_command_is_usage_error_2(self):
        port = self.app.start_remote(port=0)
        self._run_cli([], port=port)
        self.assertEqual(self.rc, 2)

    def test_app_name_mismatch_exits_2(self):
        port = self.app.start_remote(port=0, app_name="Real")
        self._run_cli(["add(2, 3)"], app_name="Wrong", port=port)
        self.assertEqual(self.rc, 2)

    def test_connection_refused_exits_1(self):
        # No server here; myTk's convention is 1 (runtime) for an unreachable
        # app, same as the `mytk` command — no mainloop needed.
        self.assertEqual(remote_cli(["add(2, 3)"], host="127.0.0.1", port=1), 1)


class TestPrintResult(unittest.TestCase):
    """_print_result formatting, in isolation."""

    def _capture(self, value):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            _print_result(value)
        return buffer.getvalue()

    def test_none_prints_nothing(self):
        self.assertEqual(self._capture(None), "")

    def test_scalar_printed_plainly(self):
        self.assertEqual(self._capture(5).strip(), "5")

    def test_dict_aligned(self):
        out = self._capture({"aa": 1, "b": 2})
        # keys padded to the widest key ("aa" -> width 2).
        self.assertIn("aa  1", out)
        self.assertIn("b   2", out)


class TestAddFileMenuCommand(unittest.TestCase):
    """App.add_file_menu_command inserts into the File menu."""

    def setUp(self):
        self.app = App(name=self.id(), no_window=True)

    def tearDown(self):
        self.app.quit()

    def _file_menu(self):
        menubar = self.app.root.nametowidget(self.app.root["menu"])
        return self.app.root.nametowidget(menubar.entrycget("File", "menu"))

    def test_inserts_above_quit(self):
        self.app.add_file_menu_command("Do Thing", lambda: None, separator=False)
        file_menu = self._file_menu()
        do_index = file_menu.index("Do Thing")
        quit_index = file_menu.index("Quit")
        self.assertIsNotNone(do_index)
        self.assertLess(do_index, quit_index)

    def test_appends_when_before_absent(self):
        self.app.add_file_menu_command(
            "Tail", lambda: None, before="Nonexistent", separator=False)
        file_menu = self._file_menu()
        self.assertEqual(file_menu.index("Tail"), file_menu.index("end"))


if __name__ == "__main__":
    unittest.main()
