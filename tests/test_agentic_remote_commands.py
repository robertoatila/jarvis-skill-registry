#!/usr/bin/env python3
"""Contracts for approval-bound remote command execution on the authoritative PC."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tooling.remote_commands import (
    RemoteCommandController,
    RemoteCommandError,
    normalize_command_payload,
)


class TestRemoteCommandController(unittest.TestCase):
    def test_command_requires_digest_bound_approval_and_executes_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "state"
            script = root / "probe.py"
            script.write_text(
                "from pathlib import Path\n"
                "p = Path('runs.txt')\n"
                "p.write_text((p.read_text() if p.exists() else '') + 'x')\n"
                "print('remote-pc-pass')\n",
                encoding="utf-8",
            )
            controller = RemoteCommandController(
                state,
                workspace_root=root,
                id_factory=lambda: "rcmd-" + ("a" * 24),
            )
            action = controller.prepare(
                {"argv": ["python", "probe.py"], "cwd": ".", "timeout_seconds": 30},
                session_id="session-1",
                device_id="phone-1",
                request_id="request-1",
            )

            self.assertEqual(action["status"], "PENDING")
            self.assertEqual(len(action["action_digest"]), 64)
            self.assertFalse((root / "runs.txt").exists())

            first = controller.approve_and_execute(
                action_id=action["action_id"],
                action_digest=action["action_digest"],
                session_id="session-1",
                device_id="phone-1",
            )
            second = controller.approve_and_execute(
                action_id=action["action_id"],
                action_digest=action["action_digest"],
                session_id="session-1",
                device_id="phone-1",
            )

            self.assertEqual(first["status"], "PASS")
            self.assertEqual(first["exit_code"], 0)
            self.assertIn("remote-pc-pass", first["stdout"])
            self.assertEqual(second, first)
            self.assertEqual((root / "runs.txt").read_text(encoding="utf-8"), "x")

    def test_wrong_digest_never_executes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "probe.py").write_text(
                "from pathlib import Path\nPath('should-not-exist.txt').write_text('bad')\n",
                encoding="utf-8",
            )
            controller = RemoteCommandController(
                root / "state",
                workspace_root=root,
                id_factory=lambda: "rcmd-" + ("b" * 24),
            )
            action = controller.prepare(
                {"argv": ["python", "probe.py"]},
                session_id="session-1",
                device_id="phone-1",
                request_id="request-1",
            )
            with self.assertRaises(RemoteCommandError):
                controller.approve_and_execute(
                    action_id=action["action_id"],
                    action_digest="0" * 64,
                    session_id="session-1",
                    device_id="phone-1",
                )
            self.assertFalse((root / "should-not-exist.txt").exists())

    def test_inline_interpreters_are_rejected(self):
        invalid = [
            {"argv": ["python", "-c", "print('x')"]},
            {"argv": ["node", "--eval", "console.log('x')"]},
            {"argv": ["powershell", "-Command", "Get-ChildItem"]},
        ]
        for payload in invalid:
            with self.subTest(payload=payload), self.assertRaises(RemoteCommandError):
                normalize_command_payload(payload)

    def test_python_alias_uses_python_exe_when_resident_host_runs_under_pythonw(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pythonw = root / "pythonw.exe"
            python_cli = root / "python.exe"
            pythonw.write_bytes(b"")
            python_cli.write_bytes(b"")
            with mock.patch("tooling.remote_commands.sys.executable", str(pythonw)):
                resolved = RemoteCommandController._resolve_executable("python")
            self.assertEqual(Path(resolved), python_cli.resolve())

    def test_missing_cwd_finishes_with_error_receipt_instead_of_stuck_running(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            controller = RemoteCommandController(
                root / "state",
                workspace_root=root,
                id_factory=lambda: "rcmd-" + ("f" * 24),
            )
            action = controller.prepare(
                {"argv": ["python", "missing.py"], "cwd": "missing-dir"},
                session_id="session-1",
                device_id="phone-1",
                request_id="request-1",
            )
            result = controller.approve_and_execute(
                action_id=action["action_id"],
                action_digest=action["action_digest"],
                session_id="session-1",
                device_id="phone-1",
            )
            self.assertEqual(result["status"], "ERROR")
            self.assertIn("cwd", result["reason"].lower())
            self.assertEqual(controller.get(action["action_id"])["status"], "COMPLETED")

    def test_cwd_cannot_escape_repository(self):
        with self.assertRaises(RemoteCommandError):
            normalize_command_payload({"argv": ["python", "probe.py"], "cwd": "../outside"})


if __name__ == "__main__":
    unittest.main()
