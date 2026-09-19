#!/usr/bin/env python3
"""Contracts for Windows resident-host autostart registration."""

import subprocess
import tempfile
import unittest
from pathlib import Path
from tooling.remote_service import (
    TASK_NAME,
    WindowsRemoteService,
    build_windows_launcher,
)


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

    def test_install_registers_per_user_onlogon_task_without_admin_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            calls = []

            def runner(args, **kwargs):
                calls.append((list(args), dict(kwargs)))
                return subprocess.CompletedProcess(args=args, returncode=0, stdout="SUCCESS", stderr="")

            manager = WindowsRemoteService(
                root,
                root / "state",
                runner=runner,
                platform_name="nt",
            )
            metadata = manager.install(port=8899, transport="tailscale")

            self.assertEqual(metadata["task_name"], TASK_NAME)
            self.assertEqual(metadata["transport"], "tailscale")
            self.assertTrue(manager.launcher_path.is_file())
            self.assertTrue(manager.metadata_path.is_file())
            args = calls[0][0]
            self.assertEqual(args[0], "schtasks.exe")
            self.assertIn("/Create", args)
            self.assertIn("ONLOGON", args)
            self.assertIn("LIMITED", args)
            self.assertNotIn("HIGHEST", args)

    def test_status_uses_query_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            calls = []

            def runner(args, **kwargs):
                calls.append(list(args))
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=0,
                    stdout="Status: Ready",
                    stderr="",
                )

            manager = WindowsRemoteService(
                root,
                root / "state",
                runner=runner,
                platform_name="nt",
            )
            result = manager.status()

            self.assertTrue(result["installed"])
            self.assertEqual(calls, [["schtasks.exe", "/Query", "/TN", TASK_NAME, "/FO", "LIST", "/V"]])


if __name__ == "__main__":
    unittest.main()
