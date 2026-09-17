#!/usr/bin/env python3
"""Repository-scale Context Governor benchmark contracts."""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from benchmarks import context_budget_benchmark as benchmark


class RepositoryContextBudgetBenchmarkTests(unittest.TestCase):
    def test_default_fixture_is_public_repository_scale_and_auditable(self):
        fixture = benchmark.load_fixture()

        self.assertEqual(fixture["schema_version"], 1)
        self.assertEqual(fixture["benchmark"], "repository-context-admission-v2")
        self.assertGreaterEqual(len(fixture["items"]), 12)
        self.assertGreaterEqual(
            sum(1 for item in fixture["items"] if item.get("required")),
            2,
        )
        self.assertTrue(all(item["source"] for item in fixture["items"]))
        self.assertTrue(all(isinstance(item["content"], str) for item in fixture["items"]))

        result = benchmark.evaluate_fixture(fixture, commit_sha="fixture-commit")

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["commit_sha"], "fixture-commit")
        self.assertEqual(len(result["fixture_sha256"]), 64)
        self.assertGreater(result["naive_serialized_bytes"], result["bounded_serialized_bytes"])
        self.assertLessEqual(result["bounded_serialized_bytes"], result["budget_bytes"])
        self.assertEqual(
            sorted(result["sources_loaded"] + result["sources_omitted"]),
            result["sources_considered"],
        )
        self.assertTrue(set(result["required_sources"]).issubset(result["sources_loaded"]))
        self.assertEqual(result["required_sources_missing"], [])
        self.assertTrue(result["invariants"]["required_context_admitted"])
        self.assertTrue(result["invariants"]["bounded_within_budget"])
        self.assertTrue(result["invariants"]["demonstrates_bounded_admission"])
        self.assertIsNone(result["token_estimate"])
        self.assertIsNone(result["token_estimation_method"])
        self.assertIn("serialized UTF-8 bytes only", result["claim_boundary"])

    def test_required_context_overflow_is_explicit_failure_not_silent_omission(self):
        fixture = {
            "schema_version": 1,
            "benchmark": "repository-context-admission-v2",
            "task": "Required context overflow fixture",
            "budget_bytes": 96,
            "now": 1_800_000_000.0,
            "items": [
                {
                    "source": "AGENTS.md",
                    "content": "mandatory-authority-contract-" * 30,
                    "priority": 0,
                    "required": True,
                },
                {
                    "source": "src/optional.py",
                    "content": "optional",
                    "priority": 4,
                    "required": False,
                },
            ],
        }

        result = benchmark.evaluate_fixture(fixture, commit_sha="fixture-commit")

        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["failure_reason"], "MANDATORY_CONTEXT_OVERFLOW")
        self.assertFalse(result["invariants"]["required_context_admitted"])
        self.assertIn("AGENTS.md", result["required_sources"])

    def test_cli_writes_machine_readable_json_with_exact_runtime_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "evidence.json"
            stdout = io.StringIO()
            with (
                patch.object(benchmark, "resolve_commit_sha", return_value="abc123exact"),
                contextlib.redirect_stdout(stdout),
            ):
                code = benchmark.main(["--json-output", str(output)])

            self.assertEqual(code, 0)
            printed = json.loads(stdout.getvalue())
            archived = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(printed, archived)
            self.assertEqual(archived["commit_sha"], "abc123exact")
            self.assertEqual(archived["status"], "PASS")
            self.assertEqual(archived["fixture_path"], "benchmarks/fixtures/repository_context_task.json")

    def test_cli_exits_nonzero_when_fixture_fails_invariants(self):
        bad_fixture = {
            "schema_version": 1,
            "benchmark": "repository-context-admission-v2",
            "task": "Unbounded fixture should fail benchmark invariants",
            "budget_bytes": 4096,
            "now": 1_800_000_000.0,
            "items": [
                {
                    "source": "AGENTS.md",
                    "content": "small mandatory contract",
                    "priority": 0,
                    "required": True,
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            fixture_path = Path(tmp) / "bad.json"
            fixture_path.write_text(json.dumps(bad_fixture), encoding="utf-8")
            stdout = io.StringIO()
            with (
                patch.object(benchmark, "resolve_commit_sha", return_value="bad-fixture-commit"),
                contextlib.redirect_stdout(stdout),
            ):
                code = benchmark.main(["--fixture", str(fixture_path)])

        result = json.loads(stdout.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(result["status"], "FAIL")
        self.assertFalse(result["invariants"]["demonstrates_bounded_admission"])


if __name__ == "__main__":
    unittest.main()
