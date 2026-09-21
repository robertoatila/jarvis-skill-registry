"""v0.2.0 policy/admission integration for durable authorization grants."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tooling.agentic.adapters.local import LocalAction, LocalAdapterType
from tooling.agentic.admission import AdmissionDecision, AdmissionGate
from tooling.agentic.authorization import AuthorizationDeniedError
from tooling.agentic.config import JarvisRuntimeConfig
from tooling.agentic.models import ApprovalStatus, RiskLevel, TaskNode
from tooling.agentic.policy import PolicyDecision, PolicyEngine
from tooling.agentic.profiles import AgentConstraints, AgentProfile


class TestV020AuthorizationIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.config = JarvisRuntimeConfig(registry_root=self.root)
        self.policy = PolicyEngine(
            config=self.config,
            operator_verifier=lambda op, pay, sig: bool(op and not op.startswith("agent:")),
        )
        self.profile = AgentProfile(
            agent_id="Quantum-ExecutorAgent",
            name="Executor",
            domain="Execution",
            allowed_tools=["*"],
            constraints=AgentConstraints(read_only=False, network_access=False),
        )
        self.gate = AdmissionGate(policy_engine=self.policy)

    def tearDown(self):
        self.tmp.cleanup()

    def _approved_grant(self):
        result = self.policy.evaluate_policy(
            agent_profile=self.profile,
            action="write",
            tool_or_skill="general",
            resource="workspace/config.json",
            risk_level=RiskLevel.R4_INFRA_MUTATION,
            task_id="tsk-r4",
            write_scopes=["workspace"],
            action_context={
                "write_scopes": ["workspace"],
                "read_scopes": [],
                "estimated_tokens": 1000,
                "estimated_cost_usd": 0.25,
            },
        )
        self.assertEqual(result.decision, PolicyDecision.REQUIRE_APPROVAL)
        self.assertTrue(self.policy.grant_approval(result.approval_id, operator_id="operator:alice"))
        grant = self.policy.issue_authorization_grant(
            result.approval_id,
            scopes=["workspace/config.json"],
            budget={"tokens": 1000, "cost_usd": 0.25},
        )
        return result, grant

    def _task(self):
        return TaskNode(
            task_id="tsk-r4",
            title="Write governed config",
            agent_profile=self.profile.agent_id,
            write_scopes=["workspace/config.json"],
            risk_level=RiskLevel.R4_INFRA_MUTATION,
            approval_status=ApprovalStatus.APPROVED,
            estimated_tokens=1000,
            estimated_cost_usd=0.25,
            action={"type": "write"},
        )

    def test_policy_issues_and_persists_grant_only_after_human_approval(self):
        result, grant = self._approved_grant()
        self.assertEqual(grant.task_id, "tsk-r4")
        self.assertEqual(grant.subject, self.profile.agent_id)
        self.assertEqual(grant.action, "write")
        self.assertTrue((self.config.authorizations_dir / f"{grant.grant_id}.json").is_file())
        restored = self.policy.get_authorization_grant(grant.grant_id)
        self.assertIsNotNone(restored)
        self.assertEqual(restored.to_dict(), grant.to_dict())

    def test_approved_flag_without_durable_grant_is_not_executable_authority(self):
        self._approved_grant()
        result = self.gate.evaluate_task(task=self._task(), agent_profile=self.profile)
        self.assertEqual(result.decision, AdmissionDecision.BLOCKED)
        self.assertFalse(result.admitted)
        self.assertTrue(any("durable authorization grant" in reason.lower() for reason in result.rejection_reasons))

    def test_matching_grant_admits_but_budget_expansion_fails_closed(self):
        _, grant = self._approved_grant()
        task = self._task()
        admitted = self.gate.evaluate_task(
            task=task,
            agent_profile=self.profile,
            authorization_grant_id=grant.grant_id,
        )
        self.assertEqual(admitted.decision, AdmissionDecision.ADMITTED)
        self.assertTrue(admitted.admitted)

        task.estimated_tokens = 1001
        expanded = self.gate.evaluate_task(
            task=task,
            agent_profile=self.profile,
            authorization_grant_id=grant.grant_id,
        )
        self.assertEqual(expanded.decision, AdmissionDecision.BLOCKED)
        self.assertFalse(expanded.admitted)
        self.assertTrue(any("authorization" in reason.lower() for reason in expanded.rejection_reasons))

    def test_grant_cannot_expand_scope_or_budget_beyond_signed_approval(self):
        result, _ = self._approved_grant()

        with self.assertRaisesRegex(AuthorizationDeniedError, "SCOPE_EXCEEDS_APPROVAL"):
            self.policy.issue_authorization_grant(
                result.approval_id,
                scopes=["outside/config.json"],
                budget={"tokens": 1000, "cost_usd": 0.25},
            )

        with self.assertRaisesRegex(AuthorizationDeniedError, "BUDGET_EXCEEDS_APPROVAL"):
            self.policy.issue_authorization_grant(
                result.approval_id,
                scopes=["workspace/config.json"],
                budget={"tokens": 1001, "cost_usd": 0.25},
            )

        with self.assertRaisesRegex(AuthorizationDeniedError, "BUDGET_EXCEEDS_APPROVAL"):
            self.policy.issue_authorization_grant(
                result.approval_id,
                scopes=["workspace/config.json"],
                budget={"tokens": 1000, "cost_usd": 0.26},
            )

    def test_grant_issuance_rejects_in_memory_approval_tampering(self):
        result, _ = self._approved_grant()
        req = self.policy.get_approval_request(result.approval_id)
        self.assertIsNotNone(req)
        req.action_context["write_scopes"] = ["outside"]

        with self.assertRaisesRegex(AuthorizationDeniedError, "APPROVAL_INTEGRITY_INVALID"):
            self.policy.issue_authorization_grant(
                result.approval_id,
                scopes=["outside/config.json"],
                budget={"tokens": 1000, "cost_usd": 0.25},
            )

    def test_local_adapter_action_round_trips_into_matching_grant_context(self):
        action = LocalAction(
            adapter=LocalAdapterType.WRITE_TEXT,
            path="workspace/config.json",
            content="governed",
        )
        task = TaskNode(
            task_id="tsk-local-r4",
            title="Governed local adapter write",
            agent_profile=self.profile.agent_id,
            write_scopes=["workspace/config.json"],
            risk_level=RiskLevel.R4_INFRA_MUTATION,
            approval_status=ApprovalStatus.APPROVED,
            action=action.to_dict(),
        )
        result = self.policy.evaluate_policy(
            agent_profile=self.profile,
            action=LocalAdapterType.WRITE_TEXT.value,
            tool_or_skill="general",
            resource="workspace/config.json",
            risk_level=RiskLevel.R4_INFRA_MUTATION,
            task_id=task.task_id,
            write_scopes=task.write_scopes,
        )
        self.assertEqual(result.decision, PolicyDecision.REQUIRE_APPROVAL)
        self.assertTrue(self.policy.grant_approval(result.approval_id, operator_id="operator:alice"))
        grant = self.policy.issue_authorization_grant(
            result.approval_id,
            scopes=task.write_scopes,
            budget={},
        )
        task.action["authorization_grant_id"] = grant.grant_id

        admitted = self.gate.evaluate_task(task=task, agent_profile=self.profile)
        self.assertEqual(admitted.decision, AdmissionDecision.ADMITTED)
        self.assertTrue(admitted.admitted)


if __name__ == "__main__":
    unittest.main()
