#!/usr/bin/env python3
"""Contracts for the evidence-backed public demo renderer."""

from __future__ import annotations

import unittest

from tooling.render_demo_assets import DURATION_SECONDS, GIF_DURATION_SECONDS, build_ass


class DemoCaptureContracts(unittest.TestCase):
    @staticmethod
    def _demo():
        return {
            "commit_sha": "a" * 40,
            "doctor": {"status": "PASS"},
            "skill": {
                "requested_capability": "systematic-code-debugging",
                "selected_skill": "systematic-code-debugging",
            },
            "context_benchmark": {
                "bounded_serialized_bytes": 2197,
                "budget_bytes": 2200,
                "sources_loaded": ["required-a", "required-b"],
                "sources_omitted": ["optional-a"],
                "naive_serialized_bytes": 4140,
                "bytes_not_admitted": 1943,
                "token_estimate": None,
            },
            "inference": {
                "status": "SUCCESS",
                "reason": "VERIFIED_CONFIDENCE_ACCEPTED",
                "routing": {"selected_candidate": "demo-local-fixture"},
                "governor": {"action": "CONTINUE", "reason_code": "EVIDENCE_SUFFICIENT"},
                "execution_receipt": {
                    "adapter": "inference:demo-local-fixture",
                    "invocation_occurred": True,
                    "resource_usage": {
                        "tokens": {"value": 41.0, "status": "MEASURED"},
                        "cost_usd": {"value": None, "status": "UNKNOWN"},
                    },
                },
                "verification_receipt": {
                    "verification_state": "VERIFIED",
                    "evidence_ids": ["benchmark:repository-context-admission-v2"],
                },
            },
            "local_execution": {
                "execution_receipt": {
                    "adapter": "local.read_file",
                    "execution_state": "FINISHED",
                },
                "verification_receipt": {
                    "verification_state": "VERIFIED",
                    "evidence_ids": ["ev-local"],
                },
            },
        }

    @staticmethod
    def _quickstart():
        return {
            "checks": {
                "launch": {
                    "http_status": 200,
                    "url": "http://127.0.0.1:43123/",
                }
            }
        }

    def test_public_demo_duration_and_loop_satisfy_issue_contract(self):
        self.assertGreaterEqual(DURATION_SECONDS, 60)
        self.assertLessEqual(DURATION_SECONDS, 90)
        self.assertGreaterEqual(GIF_DURATION_SECONDS, 10)
        self.assertLessEqual(GIF_DURATION_SECONDS, 20)

    def test_ass_exposes_receipts_without_private_reasoning(self):
        ass = build_ass(self._demo(), self._quickstart())

        self.assertIn("HTTP 200", ass)
        self.assertIn("SKILL", ass)
        self.assertIn("MODEL", ass)
        self.assertIn("EXECUTION IS NOT VERIFICATION", ass)
        self.assertIn("VERIFIED", ass)
        self.assertIn("REAL RUNTIME", ass)
        self.assertIn("DETERMINISTIC LOCAL FIXTURE", ass)
        lowered = ass.lower()
        self.assertNotIn("chain-of-thought:", lowered)
        self.assertNotIn("private reasoning:", lowered)


if __name__ == "__main__":
    unittest.main()
