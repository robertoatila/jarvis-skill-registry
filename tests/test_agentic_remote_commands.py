#!/usr/bin/env python3
"""Contracts for approval-bound remote command execution on the authoritative PC."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tooling.remote_commands import (
    RemoteCommandController,
    RemoteCommandError,
    _sanitized_environment,
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

    def test_persisted_command_tampering_is_rejected_on_reload(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "state"
            (root / "safe.py").write_text(
                "from pathlib import Path\nPath('safe-ran.txt').write_text('safe')\n",
                encoding="utf-8",
            )
            (root / "tampered.py").write_text(
                "from pathlib import Path\nPath('tampered-ran.txt').write_text('bad')\n",
                encoding="utf-8",
            )
            controller = RemoteCommandController(
                state,
                workspace_root=root,
                id_factory=lambda: "rcmd-" + ("c" * 24),
            )
            action = controller.prepare(
                {"argv": ["python", "safe.py"]},
                session_id="session-1",
                device_id="phone-1",
                request_id="request-1",
            )

            state_path = state / "remote_commands.json"
            persisted = json.loads(state_path.read_text(encoding="utf-8"))
            persisted["actions"][action["action_id"]]["command"]["argv"] = [
                "python",
                "tampered.py",
            ]
            state_path.write_text(
                json.dumps(persisted, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                RemoteCommandError,
                "persisted digest mismatch",
            ):
                RemoteCommandController(state, workspace_root=root)

            self.assertFalse((root / "safe-ran.txt").exists())
            self.assertFalse((root / "tampered-ran.txt").exists())

    def test_remote_subprocess_environment_withholds_credentials(self):
        clean = _sanitized_environment(
            {
                "PATH": "safe-path",
                "SAFE_FLAG": "1",
                "OPENAI_API_KEY": "secret-openai",
                "MY_TOKEN": "secret-token",
                "DATABASE_URL": "postgres://user:pass@example/db",
                "CUSTOM_DSN": "secret-dsn",
                "PWD": "/private/workspace",
            }
        )
        self.assertEqual(clean["PATH"], "safe-path")
        self.assertEqual(clean["SAFE_FLAG"], "1")
        self.assertEqual(clean["PYTHONUTF8"], "1")
        self.assertEqual(clean["PYTHONUNBUFFERED"], "1")
        for forbidden in (
            "OPENAI_API_KEY",
            "MY_TOKEN",
            "DATABASE_URL",
            "CUSTOM_DSN",
            "PWD",
        ):
            self.assertNotIn(forbidden, clean)

    def test_inline_interpreters_are_rejected(self):
        invalid = [
            {"argv": ["python", "-c", "print('x')"]},
            {"argv": ["node", "--eval", "console.log('x')"]},
            {"argv": ["powershell", "-Command", "Get-ChildItem"]},
        ]
        for payload in invalid:
            with self.subTest(payload=payload), self.assertRaises(RemoteCommandError):
                normalize_command_payload(payload)

    def test_attached_and_clustered_inline_options_are_rejected(self):
        invalid = (
            ["python", "-cprint(23)"],
            ["python", "-Icprint(23)"],
            ["py", "-3", "-cprint(23)"],
            ["python", "-Imtimeit", "print(23)"],
            ["node", "--eval=console.log(23)"],
            ["node", "-pe", "23"],
            ["pwsh", "-ec", "ignored", "-File", "safe.ps1"],
            ["powershell", "-CommandWithArgs", "ignored", "-File", "safe.ps1"],
        )
        for argv in invalid:
            with self.subTest(argv=argv), self.assertRaises(RemoteCommandError):
                normalize_command_payload({"argv": argv})

    def test_script_arguments_and_supported_options_are_preserved(self):
        valid = (
            ["python", "-I", "-u", "probe.py", "-c", "literal"],
            ["python", "-m", "unittest", "discover"],
            ["py", "-3.12", "probe.py"],
            ["node", "--test", "tests/probe.cjs"],
            ["node", "probe.js", "--eval=literal"],
            ["pwsh", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "probe.ps1", "-c"],
        )
        for argv in valid:
            with self.subTest(argv=argv):
                self.assertEqual(normalize_command_payload({"argv": argv})["argv"], argv)

    def test_autonomous_plan_rejects_attached_inline_options(self):
        from tooling.remote_tasks import RemoteTaskPlanner
        for argv in (["python", "-cprint(23)"], ["node", "--eval=console.log(23)", "probe.js"]):
            with self.subTest(argv=argv), self.assertRaises(RemoteCommandError):
                RemoteTaskPlanner._normalize_command_action({"type": "command", "argv": argv})

    def _run_probe(self, source, *, timeout=5, output_limit=1024):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "probe.py").write_text(source, encoding="utf-8")
            controller = RemoteCommandController(root / "state", workspace_root=root)
            action = controller.prepare(
                {"argv": ["python", "probe.py"], "timeout_seconds": timeout},
                session_id="session-1", device_id="phone-1", request_id="probe",
            )
            with mock.patch("tooling.remote_commands.MAX_OUTPUT_CHARS", output_limit):
                result = controller.approve_and_execute(
                    action_id=action["action_id"], action_digest=action["action_digest"],
                    session_id="session-1", device_id="phone-1",
                )
            replay = controller.approve_and_execute(
                action_id=action["action_id"], action_digest=action["action_digest"],
                session_id="session-1", device_id="phone-1",
            )
            self.assertEqual(result, replay)
            return result

    def test_output_flood_stops_child_and_bounds_each_stream(self):
        for stream in ("stdout", "stderr"):
            with self.subTest(stream=stream):
                result = self._run_probe(
                    "import sys\nwhile True:\n sys." + stream + ".write('x' * 4096)\n sys." + stream + ".flush()\n"
                )
                self.assertEqual(result["status"], "ERROR")
                self.assertEqual(result["reason"], "COMMAND_OUTPUT_LIMIT")
                self.assertEqual(result[stream], "x" * 1024)
                self.assertTrue(result[stream + "_truncated"])
                self.assertLessEqual(len(result["stdout"]), 1024)
                self.assertLessEqual(len(result["stderr"]), 1024)

    def test_timeout_preserves_partial_output_and_does_not_replay(self):
        result = self._run_probe("import time\nprint('before timeout', flush=True)\ntime.sleep(30)\n", timeout=1)
        self.assertEqual(result["status"], "TIMEOUT")
        self.assertEqual(result["reason"], "COMMAND_TIMEOUT")
        self.assertIn("before timeout", result["stdout"])

    def test_output_exactly_at_limit_is_not_truncated(self):
        result = self._run_probe("import sys\nsys.stdout.write('x' * 1024)\nsys.stderr.write('y' * 1024)\n")
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["stdout"], "x" * 1024)
        self.assertEqual(result["stderr"], "y" * 1024)
        self.assertFalse(result["stdout_truncated"])
        self.assertFalse(result["stderr_truncated"])

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

    def test_cwd_rejects_in_workspace_symlink_before_resolution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "real").mkdir()
            try:
                (root / "alias").symlink_to(root / "real", target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            controller = RemoteCommandController(root / "state", workspace_root=root)
            with self.assertRaisesRegex(RemoteCommandError, "symlink/reparse"):
                controller._resolve_cwd("alias")
            self.assertEqual(controller._resolve_cwd("real"), (root / "real").resolve())

    def test_manual_interpreter_script_cannot_escape_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside = root.parent / "outside.py"
            outside.write_text("print('outside')\n", encoding="utf-8")
            controller = RemoteCommandController(root / "state", workspace_root=root)
            cwd = controller._resolve_cwd(".")

            with self.assertRaisesRegex(
                RemoteCommandError,
                "repository-relative",
            ):
                controller._validate_script_target(cwd, "python", ["../outside.py"])

            with self.assertRaisesRegex(
                RemoteCommandError,
                "repository-relative",
            ):
                controller._validate_script_target(
                    cwd,
                    "python",
                    [str(outside.resolve())],
                )

    def test_manual_interpreter_script_rejects_in_workspace_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "safe.py"
            target.write_text("print('safe')\n", encoding="utf-8")
            alias = root / "alias.py"
            try:
                alias.symlink_to(target)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            controller = RemoteCommandController(root / "state", workspace_root=root)
            cwd = controller._resolve_cwd(".")
            with self.assertRaisesRegex(RemoteCommandError, "symlink/reparse"):
                controller._validate_script_target(cwd, "python", ["alias.py"])

    def test_cwd_cannot_escape_repository(self):
        with self.assertRaises(RemoteCommandError):
            normalize_command_payload({"argv": ["python", "probe.py"], "cwd": "../outside"})


if __name__ == "__main__":
    unittest.main()
