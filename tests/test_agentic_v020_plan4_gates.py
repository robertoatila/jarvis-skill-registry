"""Contracts for responsibility-scoped direct Plan 4 evidence gates."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tooling.validate_v020_plan4 import (
    build_gate_commands,
    resolve_commit_sha,
    run_gate,
    supported_platforms,
)


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_GATES = {
    "contracts",
    "integration",
    "recovery",
    "browser-ui",
    "benchmarks-claims",
    "portable-runtime",
    "legacy-governance",
}


class Plan4EvidenceGateTests(unittest.TestCase):
    def test_git_checkout_sha_is_bound_into_gate_reports(self):
        commit_sha = resolve_commit_sha(ROOT)
        self.assertRegex(commit_sha, r"^[0-9a-f]{40}$")

        def fake_runner(argv, cwd):
            return subprocess.CompletedProcess(argv, 0, stdout="fixture-output")

        report = run_gate(
            "contracts",
            root=ROOT,
            current_platform="linux",
            runner=fake_runner,
        )
        self.assertEqual(report["commit_sha"], commit_sha)
        self.assertEqual(report["status"], "PASS")
        self.assertIsNone(report["failure_reason"])

    def test_non_git_root_never_invents_commit_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(resolve_commit_sha(root), "UNKNOWN")

            report = run_gate(
                "legacy-governance",
                root=root,
                current_platform="linux",
            )
        self.assertEqual(report["commit_sha"], "UNKNOWN")

    def test_successful_commands_without_commit_identity_are_not_passing_evidence(self):
        calls = []

        def fake_runner(argv, cwd):
            calls.append(list(argv))
            return subprocess.CompletedProcess(argv, 0, stdout="fixture-output")

        with tempfile.TemporaryDirectory() as directory:
            report = run_gate(
                "contracts", root=Path(directory), current_platform="linux",
                runner=fake_runner,
            )

        self.assertEqual(len(calls), 1)
        self.assertEqual(report["passed"], 1)
        self.assertEqual(report["failed"], 0)
        self.assertEqual(report["results"][0]["status"], "PASS")
        self.assertEqual(report["commit_sha"], "UNKNOWN")
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["failure_reason"], "UNKNOWN_COMMIT")

    def test_exact_responsibility_gate_set_is_exposed(self):
        observed = {
            gate
            for gate in EXPECTED_GATES
            if build_gate_commands(gate, current_platform="linux")
        }
        self.assertEqual(observed, EXPECTED_GATES)

    def test_no_gate_invokes_github_actions_or_workflow_commands(self):
        serialized = repr({
            gate: build_gate_commands(gate, current_platform="windows")
            for gate in EXPECTED_GATES
        }).casefold()

        self.assertNotIn("actions/", serialized)
        self.assertNotIn("workflow", serialized)
        self.assertNotIn("gh run", serialized)
        self.assertNotIn("github actions", serialized)

    def test_browser_gate_is_only_the_pinned_repository_browser_entrypoint(self):
        self.assertEqual(
            build_gate_commands("browser-ui", current_platform="linux"),
            [["npm", "run", "test:browser"]],
        )

    def test_recovery_has_dedicated_machine_evidence_and_contract_test(self):
        commands = build_gate_commands("recovery", current_platform="linux")
        flattened = " ".join(" ".join(command) for command in commands)

        self.assertIn("tooling/run_v020_recovery_gate.py", flattened)
        self.assertIn("reports/v020-recovery-gate.json", flattened)
        self.assertIn("tests.test_agentic_v020_recovery_gate", flattened)

    def test_portable_runtime_does_not_repeat_benchmarks_or_browser(self):
        commands = build_gate_commands("portable-runtime", current_platform="macos")
        flattened = " ".join(" ".join(command) for command in commands)

        self.assertIn("run_tests.py", flattened)
        self.assertIn("jarvis.py --doctor", flattened)
        self.assertIn("quickstart-macos.json", flattened)
        self.assertNotIn("benchmark", flattened)
        self.assertNotIn("playwright", flattened)
        self.assertNotIn("test:browser", flattened)

    def test_legacy_governance_script_never_overwrites_existing_legacy_root(self):
        script = (
            ROOT / "tooling" / "run_v020_legacy_governance_gate.ps1"
        ).read_text(encoding="utf-8")

        self.assertIn("$createdLegacyRoot = $false", script)
        self.assertIn("[Guid]::NewGuid()", script)
        self.assertIn(
            "legacy-governance refused to overwrite existing E:\\.skill-registry",
            script,
        )
        self.assertIn(
            "if ($createdLegacyRoot -and (Test-Path $legacyRoot))",
            script,
        )
        self.assertNotIn("subst E: $env:TEMP", script)

    def test_legacy_governance_is_windows_only(self):
        self.assertEqual(supported_platforms("legacy-governance"), ("windows",))

        report = run_gate(
            "legacy-governance",
            root=ROOT,
            current_platform="linux",
        )
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["failure_reason"], "UNSUPPORTED_PLATFORM")
        self.assertEqual(report["results"], [])
        self.assertFalse(report["github_actions_used"])

    def test_gate_runs_complete_command_group_and_aggregates_failures(self):
        calls = []

        def fake_runner(argv, cwd):
            calls.append(list(argv))
            return subprocess.CompletedProcess(
                argv,
                2 if len(calls) == 1 else 0,
                stdout="fixture-output",
            )

        with tempfile.TemporaryDirectory() as directory:
            report = run_gate(
                "recovery",
                root=Path(directory),
                current_platform="linux",
                runner=fake_runner,
            )

        self.assertEqual(len(calls), 2)
        self.assertEqual(report["command_count"], 2)
        self.assertEqual(report["passed"], 1)
        self.assertEqual(report["failed"], 1)
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["github_actions_used"])


if __name__ == "__main__":
    unittest.main()
