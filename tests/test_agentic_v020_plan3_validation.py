"""Contracts for the direct v0.2.0 Plan 3 validation gate."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tooling.validate_v020_plan3 import (
    build_commands,
    redact_output,
    run_validation,
    write_report,
)


ROOT = Path(__file__).resolve().parents[1]


class Plan3DirectValidationGateTests(unittest.TestCase):
    def test_command_matrix_matches_canonical_task8_order(self):
        commands = build_commands(ROOT)
        normalized = [
            [Path(argv[0]).name if index == 0 else item for index, item in enumerate(argv)]
            for argv in (spec["argv"] for spec in commands)
        ]

        expected = [
            [Path(sys.executable).name, "-m", "unittest", "tests.test_agentic_v020_observability", "-v"],
            [Path(sys.executable).name, "-m", "unittest", "tests.test_agentic_v020_mission_timeline", "-v"],
            [Path(sys.executable).name, "-m", "unittest", "tests.test_agentic_v020_server_observability", "-v"],
            [Path(sys.executable).name, "-m", "unittest", "tests.test_agentic_v020_hud_runtime_integration", "-v"],
            ["node", "--test", "tests/test_chat_session.cjs"],
            ["node", "--test", "tests/test_runtime_observability.cjs"],
            ["node", "--test", "tests/test_operational_cockpit.cjs"],
            [Path(sys.executable).name, "run_tests.py"],
            [Path(sys.executable).name, "jarvis.py", "--doctor"],
            [Path(sys.executable).name, "jarvis.py", "--test"],
            [Path(sys.executable).name, "benchmarks/context_budget_benchmark.py"],
            [Path(sys.executable).name, "tooling/audit_pre_publish_security.py"],
        ]

        self.assertEqual(normalized, expected)
        self.assertEqual(len(commands), 12)

    def test_gate_runs_all_commands_and_fails_if_any_command_fails(self):
        commands = [
            {"name": "one", "argv": [sys.executable, "-c", "pass"]},
            {"name": "two", "argv": [sys.executable, "-c", "raise SystemExit(3)"]},
            {"name": "three", "argv": [sys.executable, "-c", "pass"]},
        ]
        calls = []

        def fake_runner(argv, cwd):
            calls.append((list(argv), cwd))
            code = 3 if argv[-1] == "raise SystemExit(3)" else 0
            return subprocess.CompletedProcess(argv, code, stdout=f"exit={code}")

        report = run_validation(ROOT, commands=commands, runner=fake_runner)

        self.assertEqual([item["status"] for item in report["results"]], ["PASS", "FAIL", "PASS"])
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["passed"], 2)
        self.assertEqual(report["failed"], 1)
        self.assertEqual(report["command_count"], 3)
        self.assertEqual(len(calls), 3)
        self.assertFalse(report["github_actions_used"])

    def test_gate_passes_only_when_every_command_passes(self):
        commands = [
            {"name": "one", "argv": [sys.executable, "-c", "pass"]},
            {"name": "two", "argv": [sys.executable, "-c", "pass"]},
        ]

        def fake_runner(argv, cwd):
            return subprocess.CompletedProcess(argv, 0, stdout="ok")

        report = run_validation(ROOT, commands=commands, runner=fake_runner)

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["passed"], 2)
        self.assertEqual(report["failed"], 0)

    def test_output_redaction_removes_common_bearer_and_provider_key_shapes(self):
        raw = (
            "Authorization: Bearer abcdef1234567890\n"
            "openai=sk-abcdefghijklmnopqrstuvwxyz\n"
            "groq=gsk_abcdefghijklmnopqrstuvwxyz\n"
            "google=AIzaabcdefghijklmnopqrstuvwxyz012345\n"
        )

        cleaned = redact_output(raw)

        self.assertNotIn("abcdef1234567890", cleaned)
        self.assertNotIn("sk-abcdefghijklmnopqrstuvwxyz", cleaned)
        self.assertNotIn("gsk_abcdefghijklmnopqrstuvwxyz", cleaned)
        self.assertNotIn("AIzaabcdefghijklmnopqrstuvwxyz012345", cleaned)
        self.assertIn("[REDACTED]", cleaned)

    def test_json_report_is_machine_readable_and_does_not_serialize_environment(self):
        report = {
            "schema_version": "1.0.0",
            "gate": "jarvis-v0.2.0-plan3-direct-validation",
            "status": "PASS",
            "github_actions_used": False,
            "command_count": 0,
            "passed": 0,
            "failed": 0,
            "results": [],
        }

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            write_report(report, path)
            loaded = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(loaded, report)
        self.assertNotIn("environment", loaded)
        self.assertNotIn("env", loaded)
        self.assertFalse(loaded["github_actions_used"])


if __name__ == "__main__":
    unittest.main()
