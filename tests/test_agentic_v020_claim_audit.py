"""Plan 4 Task 6 contracts for machine evidence and public-claim auditing."""

from __future__ import annotations

import unittest
from pathlib import Path

from tooling.audit_documentation_claims import (
    HISTORICAL_MARKER,
    audit_repository,
    audit_text,
    load_manifest,
)


ROOT = Path(__file__).resolve().parents[1]


def manifest_fixture() -> dict:
    return {
        "schema_version": "1.0.0",
        "release": {
            "version": "0.2.0",
            "status": "DIRECT_VALIDATION_REQUIRED",
            "evidence_status": "INCOMPLETE",
        },
        "validation": {
            "authority": "direct_evidence_gates",
            "github_actions_authority": False,
        },
        "portable_runtime": {
            "status": "DIRECT_VALIDATION_REQUIRED",
            "required_platforms": ["windows", "linux", "macos"],
        },
        "browser_smoke": {
            "status": "DIRECT_VALIDATION_REQUIRED",
            "runner": "npm run test:browser",
            "browser": "chromium",
        },
        "context_benchmark": {
            "status": "IMPLEMENTED",
            "metric": "serialized_utf8_bytes",
            "token_savings_claim": False,
            "cost_savings_claim": False,
            "benchmark": "benchmarks/repository_context_benchmark.py",
        },
        "provider_fixture": {
            "status": "IMPLEMENTED",
            "network": False,
            "credentials": False,
            "fixture": "tests/fixtures/v020/deterministic_provider.py",
        },
        "node_tests": {
            "status": "PRESENT",
            "entrypoints": ["tests/test_chat_session.cjs"],
        },
        "claim_audit": {
            "status": "IMPLEMENTED",
            "governed_docs": ["README.md"],
            "historical_docs": [],
        },
    }


class ClaimAuditTests(unittest.TestCase):
    def test_checked_in_manifest_is_machine_only_and_sources_exist(self):
        manifest = load_manifest(ROOT / "evidence" / "current.json")

        self.assertEqual(manifest["validation"]["authority"], "direct_evidence_gates")
        self.assertFalse(manifest["validation"]["github_actions_authority"])
        self.assertEqual(manifest["context_benchmark"]["metric"], "serialized_utf8_bytes")
        self.assertFalse(manifest["provider_fixture"]["network"])
        self.assertFalse(manifest["provider_fixture"]["credentials"])

        for path in manifest["node_tests"]["entrypoints"]:
            self.assertTrue((ROOT / path).is_file(), path)
        self.assertTrue((ROOT / manifest["provider_fixture"]["fixture"]).is_file())
        self.assertTrue((ROOT / manifest["context_benchmark"]["benchmark"]).is_file())

    def test_stale_node_absence_claim_is_detected_when_entrypoint_exists(self):
        violations = audit_text(
            "README.md",
            "Older notes say no current Node test entry point is present.",
            manifest_fixture(),
            node_tests_present=True,
        )
        self.assertEqual([item.code for item in violations], ["NODE_TEST_ABSENCE_STALE"])

    def test_actions_authority_phrase_is_rejected_for_current_docs(self):
        violations = audit_text(
            "QUICKSTART.md",
            "CI runs this portable Python/runtime path on Windows, Ubuntu and macOS.",
            manifest_fixture(),
            node_tests_present=True,
        )
        self.assertEqual(
            [item.code for item in violations],
            ["GITHUB_ACTIONS_AUTHORITY_STALE"],
        )

    def test_historical_marker_keeps_old_ci_evidence_as_history_not_current_authority(self):
        text = (
            f"> {HISTORICAL_MARKER} — retained for v0.1.0 provenance.\n\n"
            "CI green on the launch PR and on the merged main commit."
        )
        violations = audit_text(
            "docs/launch/LAUNCH_PLAN.md",
            text,
            manifest_fixture(),
            node_tests_present=True,
        )
        self.assertEqual(violations, [])

    def test_positive_token_or_cost_savings_require_machine_metric(self):
        token = audit_text(
            "README.md",
            "This runtime reduces tokens by 40 percent.",
            manifest_fixture(),
            node_tests_present=True,
        )
        cost = audit_text(
            "README.md",
            "This change delivers dollar savings in production.",
            manifest_fixture(),
            node_tests_present=True,
        )
        negated = audit_text(
            "README.md",
            "This benchmark does not claim provider-token savings or dollar savings.",
            manifest_fixture(),
            node_tests_present=True,
        )

        self.assertEqual(token[0].code, "UNSUPPORTED_RESOURCE_SAVINGS_CLAIM")
        self.assertEqual(cost[0].code, "UNSUPPORTED_RESOURCE_SAVINGS_CLAIM")
        self.assertEqual(negated, [])

    def test_whole_system_certification_requires_release_pass(self):
        violations = audit_text(
            "README.md",
            "The whole system is fully validated.",
            manifest_fixture(),
            node_tests_present=True,
        )
        self.assertTrue(
            any(
                item.code == "WHOLE_SYSTEM_VALIDATION_REQUIRES_RELEASE_EVIDENCE"
                for item in violations
            )
        )

    def test_repository_audit_is_structured_even_when_current_docs_have_violations(self):
        report = audit_repository(ROOT)

        self.assertIn(report["status"], {"PASS", "FAIL"})
        self.assertEqual(report["validation_authority"], "direct_evidence_gates")
        self.assertFalse(report["github_actions_authority"])
        self.assertIsInstance(report["violations"], list)
        self.assertEqual(report["violation_count"], len(report["violations"]))


if __name__ == "__main__":
    unittest.main()
