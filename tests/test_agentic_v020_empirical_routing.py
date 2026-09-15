"""v0.2.0 empirical routing contracts with hard constraints first."""

from __future__ import annotations

import unittest

from tooling.agentic.decision_receipt import CandidateEvidence
from tooling.agentic.model_router import (
    InferencePolicy,
    InferenceRequirements,
    ModelCandidate,
    ModelRouter,
)
from tooling.agentic.models import RiskLevel, TaskNode
from tooling.agentic.tool_router import ToolCandidate, ToolRouter


NOW = "2026-09-15T19:00:00+00:00"
FRESH = "2026-09-15T18:55:00+00:00"
STALE = "2026-09-15T10:00:00+00:00"
ENV = "linux-py312-fixture"


class TestV020EmpiricalRouting(unittest.TestCase):
    def setUp(self):
        self.task = TaskNode("tsk-routing-evidence", "Route with qualified evidence")

    @staticmethod
    def _evidence(rate, *, samples=20, latency=50.0, cost=0.01, env=ENV, freshness=FRESH):
        return CandidateEvidence(
            sample_count=samples,
            verified_success_rate=rate,
            median_latency_ms=latency,
            measured_cost_usd=cost,
            environment_fingerprint=env,
            freshness_utc=freshness,
        )

    def _model_route(self, candidates, evidence, *, policy=None):
        return ModelRouter(candidates).route_model(
            self.task,
            policy=policy or InferencePolicy(local_only=True, network_allowed=False),
            requirements=InferenceRequirements(min_capability=0.8, context_tokens=1000),
            candidate_evidence=evidence,
            environment_fingerprint=ENV,
            evidence_now_utc=NOW,
            max_evidence_age_seconds=3600,
        )

    def test_qualified_model_evidence_ranks_only_hard_constraint_survivors(self):
        local = ModelCandidate("a-local", "local", 8000, 0.0, 0.9, is_local=True)
        cloud = ModelCandidate("z-cloud", "cloud", 8000, 0.0, 0.9, is_local=False)
        winner, receipt = self._model_route(
            [local, cloud],
            {
                "a-local": self._evidence(0.70),
                "z-cloud": self._evidence(1.00),
            },
        )

        self.assertEqual(winner.model_id, "a-local")
        self.assertEqual(receipt.rejected_candidates["z-cloud"], "LOCAL_ONLY")
        self.assertEqual(receipt.metadata["evidence_status"]["z-cloud"], "HARD_REJECTED")

    def test_fresh_compatible_model_evidence_can_reorder_equal_prior_candidates(self):
        prior = ModelCandidate("a-prior", "local", 8000, 0.0, 0.9, is_local=True)
        empirical = ModelCandidate("z-empirical", "local", 8000, 0.0, 0.9, is_local=True)
        winner, receipt = self._model_route(
            [prior, empirical],
            {
                "a-prior": self._evidence(0.70),
                "z-empirical": self._evidence(0.96),
            },
        )

        self.assertEqual(winner.model_id, "z-empirical")
        self.assertEqual(receipt.metadata["ranking_mode"], "qualified_empirical_then_prior")
        self.assertEqual(receipt.metadata["evidence_status"]["z-empirical"], "QUALIFIED")
        self.assertEqual(receipt.metadata["eligible_order"][0], "z-empirical")

    def test_stale_and_incompatible_evidence_are_ignored_with_explicit_reason(self):
        prior = ModelCandidate("a-prior", "local", 8000, 0.0, 0.9, is_local=True)
        stale = ModelCandidate("z-stale", "local", 8000, 0.0, 0.9, is_local=True)
        mismatch = ModelCandidate("y-mismatch", "local", 8000, 0.0, 0.9, is_local=True)
        winner, receipt = self._model_route(
            [prior, stale, mismatch],
            {
                "z-stale": self._evidence(1.0, freshness=STALE),
                "y-mismatch": self._evidence(1.0, env="different-environment"),
            },
        )

        self.assertEqual(winner.model_id, "a-prior")
        self.assertEqual(receipt.metadata["evidence_status"]["z-stale"], "STALE_EVIDENCE")
        self.assertEqual(receipt.metadata["evidence_status"]["y-mismatch"], "ENVIRONMENT_MISMATCH")

    def test_zero_samples_remain_unknown_prior_not_numeric_failure_score(self):
        prior = ModelCandidate("a-prior", "local", 8000, 0.0, 0.9, is_local=True)
        zero = ModelCandidate("z-zero", "local", 8000, 0.0, 0.9, is_local=True)
        winner, receipt = self._model_route(
            [zero, prior],
            {
                "z-zero": CandidateEvidence(
                    sample_count=0,
                    verified_success_rate=None,
                    median_latency_ms=None,
                    measured_cost_usd=None,
                    environment_fingerprint=ENV,
                    freshness_utc=FRESH,
                )
            },
        )

        self.assertEqual(winner.model_id, "a-prior")
        self.assertEqual(receipt.metadata["evidence_status"]["z-zero"], "UNKNOWN_ZERO_SAMPLES")
        self.assertEqual(receipt.scores["z-zero"], receipt.scores["a-prior"])
        self.assertNotEqual(receipt.scores["z-zero"], 0)

    def test_tool_evidence_ranks_survivors_but_cannot_resurrect_policy_rejection(self):
        local_a = ToolCandidate("a-local", "A", ["read"], risk_level=RiskLevel.R0_READ_ONLY)
        local_z = ToolCandidate("z-local", "Z", ["read"], risk_level=RiskLevel.R0_READ_ONLY)
        denied = ToolCandidate(
            "zz-network",
            "Network",
            ["read"],
            risk_level=RiskLevel.R0_READ_ONLY,
            requires_network=True,
        )
        router = ToolRouter([local_a, local_z, denied])
        winner, receipt = router.route_tool(
            self.task,
            required_capabilities=["read"],
            policy=InferencePolicy(
                local_only=False,
                network_allowed=False,
                allowed_tools=("a-local", "z-local", "zz-network"),
            ),
            candidate_evidence={
                "a-local": self._evidence(0.80),
                "z-local": self._evidence(0.98),
                "zz-network": self._evidence(1.00),
            },
            environment_fingerprint=ENV,
            evidence_now_utc=NOW,
            max_evidence_age_seconds=3600,
        )

        self.assertEqual(winner.tool_id, "z-local")
        self.assertEqual(receipt.rejected_candidates["zz-network"], "NETWORK_DENIED")
        self.assertEqual(receipt.metadata["evidence_status"]["zz-network"], "HARD_REJECTED")
        self.assertEqual(receipt.metadata["evidence_status"]["z-local"], "QUALIFIED")

    def test_empirical_ties_remain_deterministic(self):
        a = ModelCandidate("a-model", "local", 8000, 0.0, 0.9, is_local=True)
        b = ModelCandidate("b-model", "local", 8000, 0.0, 0.9, is_local=True)
        evidence = {
            "a-model": self._evidence(0.9, latency=20.0, cost=0.0),
            "b-model": self._evidence(0.9, latency=20.0, cost=0.0),
        }
        first, first_receipt = self._model_route([b, a], evidence)
        second, second_receipt = self._model_route([a, b], evidence)

        self.assertEqual(first.model_id, "a-model")
        self.assertEqual(second.model_id, "a-model")
        self.assertEqual(first_receipt.metadata["eligible_order"], second_receipt.metadata["eligible_order"])


if __name__ == "__main__":
    unittest.main()
