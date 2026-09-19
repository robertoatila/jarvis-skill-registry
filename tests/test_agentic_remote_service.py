#!/usr/bin/env python3
"""Contracts for non-elevated Windows resident-host autostart."""

import json
import tempfile
import unittest
from pathlib import Path

from tooling.remote_service import (
    RUN_KEY_PATH,
    RUN_VALUE_NAME,
    WindowsRemoteService,
    build_windows_launcher,
)


class _FakeRegistry:
    HKEY_CURRENT_USER = "HKCU"
    REG_SZ = 1
    KEY_SET_VALUE = 2

    def __init__(self):
        self.values = {}

    def CreateKey(self, hive, path):
        self.values.setdefault((hive, path), {})
        return (hive, path)

    def OpenKey(self, hive, path, *_args):
        if (hive, path) not in self.values:
            raise FileNotFoundError(path)
        return (hive, path)

    def SetValueEx(self, key, name, _reserved, kind, value):
        self.values.setdefault(key, {})[name] = (value, kind)

    def QueryValueEx(self, key, name):
        try:
            return self.values[key][name]
        except KeyError as exc:
            raise FileNotFoundError(name) from exc

    def DeleteValue(self, key, name):
        try:
            del self.values[key][name]
        except KeyError as exc:
            raise FileNotFoundError(name) from exc

    def CloseKey(self, _key):
        return None


class _FakeProcess:
    pid = 4242


class _Response:
    status = 202

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps({"status": "STOPPING"}).encode("utf-8")


class TestWindowsRemoteService(unittest.TestCase):
    def test_launcher_restores_checkout_and_uses_requested_transport(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            launcher = build_windows_launcher(
                registry_root=root,
                port=8899,
                transport="tailscale",
            )
            self.assertIn(str(root.resolve()), launcher)
            self.assertIn("os.chdir(ROOT)", launcher)
            self.assertIn("tooling.remote_host", launcher)
            self.assertIn("'--transport', 'tailscale'", launcher)

    def test_launcher_accepts_tailscale_serve_transport(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            launcher = build_windows_launcher(
                registry_root=root,
                port=8899,
                transport="tailscale-serve",
            )
            self.assertIn("'--transport', 'tailscale-serve'", launcher)

    def test_install_registers_current_user_hkcu_run_without_schtasks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = _FakeRegistry()
            manager = WindowsRemoteService(
                root,
                root / "state",
                registry_module=registry,
                platform_name="nt",
            )

            metadata = manager.install(port=8899, transport="tailscale-serve")

            self.assertEqual(metadata["autostart"], "HKCU_RUN")
            self.assertEqual(metadata["run_key"], RUN_KEY_PATH)
            self.assertEqual(metadata["run_value"], RUN_VALUE_NAME)
            self.assertEqual(metadata["transport"], "tailscale-serve")
            self.assertTrue(manager.launcher_path.is_file())
            self.assertTrue(manager.metadata_path.is_file())
            command, kind = registry.values[("HKCU", RUN_KEY_PATH)][RUN_VALUE_NAME]
            self.assertEqual(kind, registry.REG_SZ)
            self.assertEqual(command, metadata["command"])
            self.assertNotIn("schtasks", command.lower())

    def test_status_reports_registry_install_and_metadata_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = _FakeRegistry()
            manager = WindowsRemoteService(
                root,
                root / "state",
                registry_module=registry,
                platform_name="nt",
            )
            manager.install(port=8899, transport="local")

            result = manager.status()

            self.assertTrue(result["installed"])
            self.assertTrue(result["matches_metadata"])
            self.assertEqual(result["autostart"], "HKCU_RUN")
            self.assertEqual(result["run_value"], RUN_VALUE_NAME)

    def test_start_spawns_generated_python_launcher_without_shell(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = _FakeRegistry()
            calls = []

            def popen(args, **kwargs):
                calls.append((list(args), dict(kwargs)))
                return _FakeProcess()

            manager = WindowsRemoteService(
                root,
                root / "state",
                registry_module=registry,
                platform_name="nt",
                popen_factory=popen,
            )
            manager.install(port=8899, transport="local")

            result = manager.start()

            self.assertEqual(result["status"], "START_REQUESTED")
            self.assertEqual(result["pid"], 4242)
            self.assertEqual(len(calls), 1)
            self.assertFalse(calls[0][1]["shell"])
            self.assertEqual(Path(calls[0][0][1]), manager.launcher_path)

    def test_stop_uses_loopback_control_endpoint_not_pid_kill(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = _FakeRegistry()
            calls = []

            def urlopen(request, timeout=0):
                calls.append((request.full_url, request.method, timeout))
                return _Response()

            manager = WindowsRemoteService(
                root,
                root / "state",
                registry_module=registry,
                platform_name="nt",
                urlopen=urlopen,
            )
            manager.install(port=8899, transport="local")

            result = manager.stop()

            self.assertEqual(result["status"], "STOPPING")
            self.assertEqual(
                calls,
                [
                    (
                        "http://127.0.0.1:8899/api/remote/v1/admin/stop",
                        "POST",
                        5,
                    )
                ],
            )

    def test_uninstall_removes_only_current_user_run_value_and_generated_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = _FakeRegistry()
            manager = WindowsRemoteService(
                root,
                root / "state",
                registry_module=registry,
                platform_name="nt",
            )
            manager.install(port=8899, transport="local")

            result = manager.uninstall()

            self.assertEqual(result["status"], "UNINSTALLED")
            self.assertNotIn(
                RUN_VALUE_NAME,
                registry.values.get(("HKCU", RUN_KEY_PATH), {}),
            )
            self.assertFalse(manager.launcher_path.exists())
            self.assertFalse(manager.metadata_path.exists())


if __name__ == "__main__":
    unittest.main()
