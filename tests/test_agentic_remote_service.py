#!/usr/bin/env python3
"""Contracts for non-elevated Windows resident-host autostart."""

import json
import tempfile
import unittest
from pathlib import Path

from tooling.remote_service import (
    RUN_KEY_PATH,
    RUN_VALUE_NAME,
    RemoteServiceError,
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


class _FailOnceRegistry(_FakeRegistry):
    def __init__(self):
        super().__init__()
        self.fail_next_write = False

    def SetValueEx(self, key, name, reserved, kind, value):
        if self.fail_next_write:
            self.fail_next_write = False
            raise OSError("simulated registry write failure")
        return super().SetValueEx(key, name, reserved, kind, value)


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
            self.assertIn(repr(str(root.resolve())), launcher)
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

    def test_failed_reinstall_restores_previous_autostart_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = _FailOnceRegistry()
            manager = WindowsRemoteService(
                root,
                root / "state",
                registry_module=registry,
                platform_name="nt",
            )
            original = manager.install(port=8899, transport="local")
            original_launcher = manager.launcher_path.read_text(encoding="utf-8")
            original_metadata = manager.metadata_path.read_text(encoding="utf-8")
            original_command = registry.values[("HKCU", RUN_KEY_PATH)][RUN_VALUE_NAME][0]

            registry.fail_next_write = True
            with self.assertRaisesRegex(
                RemoteServiceError,
                "failed to install resident host autostart",
            ):
                manager.install(port=9000, transport="lan")

            self.assertEqual(
                manager.launcher_path.read_text(encoding="utf-8"),
                original_launcher,
            )
            self.assertEqual(
                manager.metadata_path.read_text(encoding="utf-8"),
                original_metadata,
            )
            self.assertEqual(
                registry.values[("HKCU", RUN_KEY_PATH)][RUN_VALUE_NAME][0],
                original_command,
            )
            self.assertEqual(json.loads(original_metadata)["port"], original["port"])

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

    def test_start_rejects_tampered_launcher_content(self):
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
            manager.launcher_path.write_text(
                "raise SystemExit('tampered')\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RemoteServiceError, "launcher content mismatch"):
                manager.start()

            status = manager.status()
            self.assertFalse(status["matches_metadata"])
            self.assertIn("launcher content mismatch", status["validation_error"])

    def test_start_rejects_metadata_redirect_to_other_launcher(self):
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
            metadata = json.loads(manager.metadata_path.read_text(encoding="utf-8"))
            other = root / "other.pyw"
            other.write_text("print('other')\n", encoding="utf-8")
            metadata["launcher"] = str(other)
            manager.metadata_path.write_text(
                json.dumps(metadata),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RemoteServiceError, "launcher path mismatch"):
                manager.start()

    def test_install_replaces_generated_files_without_temp_artifacts(self):
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

            self.assertEqual(list(manager.service_dir.glob("*.tmp")), [])
            self.assertTrue(manager.launcher_path.is_file())
            self.assertTrue(manager.metadata_path.is_file())

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

    def test_uninstall_disables_run_value_without_following_symlinked_service_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "state"
            state.mkdir()
            outside = root / "outside"
            outside.mkdir()
            protected = outside / "preserve.txt"
            protected.write_text("preserve-me", encoding="utf-8")

            registry = _FakeRegistry()
            registry.values[("HKCU", RUN_KEY_PATH)] = {
                RUN_VALUE_NAME: ("pythonw malicious.pyw", registry.REG_SZ)
            }
            manager = WindowsRemoteService(
                root,
                state,
                registry_module=registry,
                platform_name="nt",
            )
            try:
                manager.service_dir.symlink_to(outside, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")

            with self.assertRaisesRegex(
                RemoteServiceError,
                "autostart disabled but resident host service directory is unsafe",
            ):
                manager.uninstall()

            self.assertNotIn(
                RUN_VALUE_NAME,
                registry.values.get(("HKCU", RUN_KEY_PATH), {}),
            )
            self.assertEqual(protected.read_text(encoding="utf-8"), "preserve-me")

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
