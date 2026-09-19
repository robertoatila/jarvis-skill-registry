#!/usr/bin/env python3
"""Read-only readiness contracts for the Windows PC remote host."""

import json
import subprocess
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from tooling.remote_doctor import remote_doctor
from tooling.remote_service import RUN_KEY_PATH, RUN_VALUE_NAME


class _FakeRegistry:
    HKEY_CURRENT_USER = "HKCU"
    REG_SZ = 1
    KEY_SET_VALUE = 2

    def __init__(self, command=None):
        self.values = {}
        if command is not None:
            self.values[("HKCU", RUN_KEY_PATH)] = {
                RUN_VALUE_NAME: (command, self.REG_SZ)
            }

    def OpenKey(self, hive, path, *_args):
        if (hive, path) not in self.values:
            raise FileNotFoundError(path)
        return (hive, path)

    def QueryValueEx(self, key, name):
        try:
            return self.values[key][name]
        except KeyError as exc:
            raise FileNotFoundError(name) from exc

    def CloseKey(self, _key):
        return None


class TestRemoteDoctor(unittest.TestCase):
    def _root(self, tmp: str) -> Path:
        root = Path(tmp)
        (root / "tooling").mkdir()
        (root / "jarvis.py").write_text("# launcher\n", encoding="utf-8")
        return root

    def test_ready_windows_pc_reports_https_remote_next_step(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(tmp)
            state_dir = root / "state"

            def runner(args, **kwargs):
                if args == ["tailscale", "version"]:
                    return subprocess.CompletedProcess(args, 0, "1.92.0\n", "")
                if args == ["tailscale", "status", "--json"]:
                    payload = {
                        "BackendState": "Running",
                        "Self": {
                            "Online": True,
                            "DNSName": "home-pc.example.ts.net.",
                            "TailscaleIPs": ["100.101.102.103"],
                        },
                    }
                    return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")
                if args == ["tailscale", "serve", "status", "--json"]:
                    payload = {
                        "TCP": {"443": {"HTTPS": True}},
                        "Web": {
                            "home-pc.example.ts.net:443": {
                                "Handlers": {
                                    "/": {"Proxy": "http://127.0.0.1:54321"}
                                }
                            }
                        },
                    }
                    return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")
                if args[:4] == ["schtasks.exe", "/Query", "/TN", "JARVIS Remote Host"]:
                    return subprocess.CompletedProcess(args, 0, "Status: Ready", "")
                raise AssertionError(f"unexpected command: {args}")

            result = remote_doctor(
                root,
                state_dir,
                port=54321,
                runner=runner,
                platform_name="nt",
                registry_module=_FakeRegistry("pythonw jarvis_remote_host.pyw"),
            )

            self.assertEqual(result["status"], "READY")
            self.assertEqual(result["checks"]["tailscale_node"]["state"], "PASS")
            self.assertEqual(result["checks"]["tailnet_dns"]["state"], "PASS")
            self.assertEqual(result["checks"]["windows_autostart"]["state"], "WARN")
            self.assertEqual(
                result["next_command"],
                "python jarvis.py service install --transport tailscale-serve",
            )

    def test_unprovisioned_serve_reports_setup_required_and_provision_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(tmp)

            def runner(args, **kwargs):
                if args == ["tailscale", "version"]:
                    return subprocess.CompletedProcess(args, 0, "1.92.0\n", "")
                if args == ["tailscale", "status", "--json"]:
                    payload = {
                        "BackendState": "Running",
                        "Self": {
                            "Online": True,
                            "DNSName": "home-pc.example.ts.net.",
                            "TailscaleIPs": ["100.101.102.103"],
                        },
                    }
                    return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")
                if args == ["tailscale", "serve", "status", "--json"]:
                    return subprocess.CompletedProcess(args, 0, "{}", "")
                raise AssertionError(f"unexpected command: {args}")

            result = remote_doctor(
                root,
                root / "state",
                port=54325,
                runner=runner,
                platform_name="posix",
            )

            self.assertEqual(result["status"], "SETUP_REQUIRED")
            self.assertEqual(result["checks"]["tailscale_serve"]["state"], "WARN")
            self.assertFalse(result["checks"]["tailscale_serve"]["mapping_active"])
            self.assertEqual(
                result["next_command"],
                "python jarvis.py remote-serve provision",
            )

    def test_task_planner_readiness_reports_presence_without_exposing_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(tmp)
            config_dir = root / "config"
            config_dir.mkdir()
            (config_dir / "api_keys.json").write_text(
                json.dumps(
                    {
                        "preferred_provider": "groq",
                        "groq_model": "model-x",
                        "groq": "super-secret-provider-key",
                    }
                ),
                encoding="utf-8",
            )

            def runner(args, **kwargs):
                if args == ["tailscale", "version"]:
                    return subprocess.CompletedProcess(args, 0, "1.92.0\n", "")
                if args == ["tailscale", "status", "--json"]:
                    payload = {
                        "BackendState": "Running",
                        "Self": {
                            "Online": True,
                            "DNSName": "home-pc.example.ts.net.",
                            "TailscaleIPs": ["100.101.102.103"],
                        },
                    }
                    return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")
                if args == ["tailscale", "serve", "status", "--json"]:
                    return subprocess.CompletedProcess(args, 0, "{}", "")
                raise AssertionError(f"unexpected command: {args}")

            with mock.patch.dict(
                "os.environ",
                {
                    "JARVIS_CHAT_ALLOW_CLOUD": "1",
                    "JARVIS_CHAT_TOKEN": "pc-only-token",
                    "JARVIS_CHAT_PROVIDERS": "groq",
                },
                clear=False,
            ):
                result = remote_doctor(
                    root,
                    root / "state",
                    port=54324,
                    runner=runner,
                    platform_name="posix",
                )

            planner = result["checks"]["task_planner"]
            self.assertEqual(planner["state"], "PASS")
            self.assertTrue(planner["provider_key_present"])
            serialized = json.dumps(result)
            self.assertNotIn("super-secret-provider-key", serialized)
            self.assertNotIn("pc-only-token", serialized)

    def test_missing_tailscale_is_not_ready_without_fabricating_endpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(tmp)

            def runner(args, **kwargs):
                raise FileNotFoundError("tailscale")

            result = remote_doctor(
                root,
                root / "state",
                port=54322,
                runner=runner,
                platform_name="nt",
            )

            self.assertEqual(result["status"], "NOT_READY")
            self.assertIn("tailscale_cli", result["hard_failures"])
            self.assertIn("tailscale_node", result["hard_failures"])
            self.assertIsNone(result["next_command"])

    def test_corrupt_host_state_is_reported_instead_of_crashing_doctor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(tmp)
            state_dir = root / "state"
            state_dir.mkdir()
            (state_dir / "remote_host.json").write_text("{broken", encoding="utf-8")

            def runner(args, **kwargs):
                if args == ["tailscale", "version"]:
                    return subprocess.CompletedProcess(args, 0, "1.92.0\n", "")
                if args == ["tailscale", "status", "--json"]:
                    payload = {
                        "BackendState": "Running",
                        "Self": {
                            "Online": True,
                            "DNSName": "home-pc.example.ts.net.",
                            "TailscaleIPs": ["100.101.102.103"],
                        },
                    }
                    return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")
                if args == ["tailscale", "serve", "status", "--json"]:
                    return subprocess.CompletedProcess(args, 0, "{}", "")
                if args[:4] == ["schtasks.exe", "/Query", "/TN", "JARVIS Remote Host"]:
                    return subprocess.CompletedProcess(args, 1, "", "not installed")
                raise AssertionError(f"unexpected command: {args}")

            result = remote_doctor(
                root,
                state_dir,
                port=54323,
                runner=runner,
                platform_name="nt",
            )

            self.assertEqual(result["checks"]["resident_host"]["state"], "OFFLINE")
            self.assertEqual(
                result["checks"]["resident_host"]["detail"]["reason"],
                "STATE_ERROR",
            )


if __name__ == "__main__":
    unittest.main()
