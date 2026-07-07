"""Tests for network discovery of remote apps (mytk.discover and --discover).

These are hermetic: a fake ``zeroconf`` module stands in for real mDNS, so no
multicast traffic, sockets, or Tk window are needed. End-to-end socket behavior
of the remote server itself is covered by testRemote.py / testRemoteCLI.py.
"""

import contextlib
import io
import sys
import types
import unittest
from unittest import mock

from mytk import remote
from mytk.remotecli import run


def _make_fake_zeroconf(services):
    """Build a stand-in ``zeroconf`` module advertising the given services.

    Args:
        services (list[tuple[str, str, str, int, dict]]): Each entry is
            ``(service_type, instance_name, ip, port, properties)`` where
            ``properties`` maps str keys to str values (as an app would pass).

    Returns:
        types.ModuleType: A module exposing ``ServiceInfo``, ``Zeroconf`` and
        ``ServiceBrowser`` compatible with how ``discover()`` uses them.
    """

    class FakeServiceInfo:
        def __init__(self, type_, name, ip, port, properties):
            self.type = type_
            self.name = name
            self._ip = ip
            self.port = port
            self.properties = {
                key.encode(): value.encode() for key, value in properties.items()
            }

        def parsed_addresses(self):
            return [self._ip]

    infos = [
        FakeServiceInfo(service_type, name, ip, port, properties)
        for service_type, name, ip, port, properties in services
    ]

    class FakeZeroconf:
        def get_service_info(self, type_, name):
            for info in infos:
                if info.type == type_ and info.name == name:
                    return info
            return None

        def close(self):
            pass

    class FakeServiceBrowser:
        def __init__(self, zc, type_, listener):
            for info in infos:
                if info.type == type_:
                    listener.add_service(zc, type_, info.name)

    module = types.ModuleType("zeroconf")
    module.ServiceInfo = FakeServiceInfo
    module.Zeroconf = FakeZeroconf
    module.ServiceBrowser = FakeServiceBrowser
    return module


class TestDiscover(unittest.TestCase):
    """mytk.discover() browsing behavior, with real connect() stubbed out."""

    SERVICE_TYPE = "_mytk._tcp.local."

    def _install_zeroconf(self, services):
        fake = _make_fake_zeroconf(services)
        patcher = mock.patch.dict(sys.modules, {"zeroconf": fake})
        patcher.start()
        self.addCleanup(patcher.stop)

    def _capture_connect(self):
        # discover() ends by calling remote.connect(host, port, app_name); capture
        # its arguments and hand back a sentinel instead of opening a socket.
        calls = []

        def fake_connect(host, port, app_name=None):
            calls.append((host, port, app_name))
            return f"proxy://{host}:{port}"

        patcher = mock.patch.object(remote, "connect", fake_connect)
        patcher.start()
        self.addCleanup(patcher.stop)
        return calls

    def test_discover_connects_to_advertised_server(self):
        self._install_zeroconf(
            [(self.SERVICE_TYPE, "Microscope." + self.SERVICE_TYPE,
              "192.168.1.42", 54321, {"app": "Microscope", "path": "/"})]
        )
        calls = self._capture_connect()

        proxy = remote.discover(timeout=1.0)

        self.assertEqual(proxy, "proxy://192.168.1.42:54321")
        self.assertEqual(calls, [("192.168.1.42", 54321, None)])

    def test_discover_filters_by_app_name(self):
        self._install_zeroconf([
            (self.SERVICE_TYPE, "A." + self.SERVICE_TYPE,
             "192.168.1.10", 1111, {"app": "A"}),
            (self.SERVICE_TYPE, "B." + self.SERVICE_TYPE,
             "192.168.1.20", 2222, {"app": "B"}),
        ])
        calls = self._capture_connect()

        remote.discover(app_name="B", timeout=1.0)

        # Only B's endpoint is used, and its identity is passed to connect().
        self.assertEqual(calls, [("192.168.1.20", 2222, "B")])

    def test_discover_times_out_when_no_service(self):
        self._install_zeroconf([])
        self._capture_connect()

        with self.assertRaises(TimeoutError):
            remote.discover(timeout=0.2)

    def test_discover_times_out_when_app_name_absent(self):
        self._install_zeroconf(
            [(self.SERVICE_TYPE, "A." + self.SERVICE_TYPE,
              "192.168.1.10", 1111, {"app": "A"})]
        )
        self._capture_connect()

        with self.assertRaises(TimeoutError):
            remote.discover(app_name="B", timeout=0.2)

    def test_discover_without_zeroconf_raises_importerror(self):
        # Setting the entry to None makes `from zeroconf import ...` raise.
        patcher = mock.patch.dict(sys.modules, {"zeroconf": None})
        patcher.start()
        self.addCleanup(patcher.stop)

        with self.assertRaises(ImportError):
            remote.discover(timeout=0.2)


class TestRemoteCLIDiscovery(unittest.TestCase):
    """`mytk-remote --discover` wiring, with discover() itself stubbed out."""

    class FakeProxy:
        def remote_signatures(self):
            return {"add": "(a, b)", "flip": "()"}

        def add(self, a, b):
            return a + b

    def _run(self, argv):
        out = io.StringIO()
        err = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = run(argv, prog="mytk-remote")
        return code, out.getvalue(), err.getvalue()

    def test_discover_list(self):
        with mock.patch(
            "mytk.remotecli.discover", return_value=self.FakeProxy()
        ) as discover:
            code, out, _ = self._run(["--discover", "--list"])
        self.assertEqual(code, 0)
        self.assertIn("add(a, b)", out)
        self.assertIn("flip()", out)
        discover.assert_called_once()

    def test_discover_call(self):
        with mock.patch("mytk.remotecli.discover", return_value=self.FakeProxy()):
            code, out, _ = self._run(["--discover", "add(2, 3)"])
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "5")

    def test_discover_passes_app_name_and_options(self):
        with mock.patch(
            "mytk.remotecli.discover", return_value=self.FakeProxy()
        ) as discover:
            self._run([
                "--discover", "--app-name", "Microscope",
                "--service-type", "_custom._tcp.local.", "--timeout", "1.5",
                "--list",
            ])
        discover.assert_called_once_with(
            app_name="Microscope",
            service_type="_custom._tcp.local.",
            timeout=1.5,
        )

    def test_discover_timeout_reports_error(self):
        with mock.patch(
            "mytk.remotecli.discover", side_effect=TimeoutError("nothing found")
        ):
            code, _, err = self._run(["--discover", "flip()"])
        self.assertEqual(code, 1)
        self.assertIn("nothing found", err)

    def test_discover_missing_zeroconf_reports_error(self):
        with mock.patch(
            "mytk.remotecli.discover",
            side_effect=ImportError("needs the 'zeroconf' package"),
        ):
            code, _, err = self._run(["--discover", "flip()"])
        self.assertEqual(code, 2)
        self.assertIn("zeroconf", err)


if __name__ == "__main__":
    unittest.main()
