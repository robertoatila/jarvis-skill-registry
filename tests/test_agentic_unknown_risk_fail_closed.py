"""Fail-closed regression tests for unknown task risk authority."""

import unittest

from tooling.agentic.admission import AdmissionDecision, AdmissionGate
from tooling.agentic.models import RiskLevel, TaskNode
from tooling.agentic.policy import PolicyDecision, PolicyEngine
from tooling.agentic.profiles import AgentProfile


class TestUnknownRiskFailClosed(unittest.TestCase):
    def setUp(self):
        self.profile = AgentProfile(
            agent_id="test-agent",
            name="Test Agent",
            domain="Tests",
            capabilities=[],
            skills=[],
        )

    def test_unknown_and_missing_risk_remain_explicit(self):
        self.assertEqual(RiskLevel.normalize("UNKNOWN"), RiskLevel.UNKNOWN)
        self.assertEqual(RiskLevel.normalize(None), RiskLevel.UNKNOWN)
        self.assertEqual(RiskLevel.normalize("R0"), RiskLevel.R0_READ_ONLY)

    def test_unrecognized_risk_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unrecognized risk level"):
            RiskLevel.normalize("harmless-ish")

    def test_policy_denies_unknown_risk_before_action_evaluation(self):
        result = PolicyEngine().evaluate_policy(
            self.profile,
            action="read",
            tool_or_skill="local.read_file",
            risk_level="UNKNOWN",
        )
        self.assertEqual(result.decision, PolicyDecision.DENY)
        self.assertEqual(result.risk_level, RiskLevel.UNKNOWN)
        self.assertIn("not executable authority", result.reason)

    def test_admission_blocks_default_unknown_task_risk(self):
        task = TaskNode(task_id="tsk-unknown-risk", title="Unclassified task")
        result = AdmissionGate().evaluate_task(task, agent_profile=self.profile)
        self.assertEqual(result.decision, AdmissionDecision.BLOCKED)
        self.assertFalse(result.admitted)
        self.assertEqual(result.evaluated_constraints["canonical_risk"], "UNKNOWN")
        self.assertFalse(result.evaluated_constraints["risk_classified"])
        self.assertTrue(
            any("UNKNOWN is not executable authority" in reason for reason in result.rejection_reasons)
        )

    def test_explicit_r0_read_only_task_remains_admissible(self):
        task = TaskNode(
            task_id="tsk-explicit-r0",
            title="Explicit read-only task",
            risk_level=RiskLevel.R0_READ_ONLY,
        )
        result = AdmissionGate().evaluate_task(task, agent_profile=self.profile)
        self.assertEqual(result.decision, AdmissionDecision.ADMITTED)
        self.assertTrue(result.admitted)
        self.assertTrue(result.evaluated_constraints["risk_classified"])


if __name__ == "__main__":
    unittest.main()
