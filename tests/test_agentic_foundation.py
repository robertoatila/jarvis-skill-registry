"""
test_agentic_foundation.py // Unit Tests for Tier 1 Foundation
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
Tests:
- Policy & Authorization Engine (R0-R5, scope confinement, anti-self-approval)
- Artifact & Cryptographic Provenance Model (SHA-256 computation, roundtrip)
- Authoritative State Store (Atomic saves, corrupted state quarantine)
- Canonical Runtime Configuration
"""

import os
import json
import tempfile
import unittest
from pathlib import Path

from tooling.agentic.models import (
    RiskLevel,
    ApprovalStatus,
    ArtifactType,
    Artifact,
    TaskNode,
    TaskStatus,
    Mission,
    MissionStatus
)
from tooling.agentic.profiles import AgentProfile, AgentConstraints
from tooling.agentic.config import JarvisRuntimeConfig
from tooling.agentic.policy import PolicyEngine, PolicyDecision, PolicyEvaluationResult
from tooling.agentic.state_store import AuthoritativeStateStore, CorruptedStateFileError


class TestAgenticFoundation(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp_dir.name).resolve()
        self.config = JarvisRuntimeConfig(registry_root=self.root)
        self.config.ensure_directories()
        self.policy = PolicyEngine(config=self.config)
        self.state_store = AuthoritativeStateStore(config=self.config)

    def tearDown(self):
        self.tmp_dir.cleanup()

    # --- 1. Artifact & Provenance Tests ---

    def test_artifact_creation_and_hash_computation(self):
        sample_file = self.root / "sample_code.py"
        sample_file.write_text("print('hello sovereign jarvis')\n", encoding="utf-8")

        art = Artifact(
            artifact_id="art-001",
            mission_id="mis-001",
            task_id="tsk-01",
            producer="runtime:Quantum-AuditAgent",
            artifact_type=ArtifactType.SOURCE_CODE,
            path="sample_code.py"
        )
        calculated_hash = art.compute_hash(base_dir=self.root)
        self.assertTrue(len(calculated_hash) == 64)
        self.assertEqual(art.size_bytes, sample_file.stat().st_size)

        # Roundtrip serialization
        data = art.to_dict()
        reconstructed = Artifact.from_dict(data)
        self.assertEqual(reconstructed.artifact_id, "art-001")
        self.assertEqual(reconstructed.sha256, calculated_hash)
        self.assertEqual(reconstructed.artifact_type, ArtifactType.SOURCE_CODE)

    def test_task_node_with_structured_artifacts_and_legacy_strings(self):
        art = Artifact(
            artifact_id="art-002",
            mission_id="mis-001",
            task_id="tsk-01",
            producer="runtime:Quantum-AuditAgent",
            path="output.txt"
        )
        task = TaskNode(
            task_id="tsk-01",
            title="Artifact Test Task",
            artifacts=[art, "legacy_path.json"],
            risk_level="CRITICAL"
        )
        # Verify backward-compatible risk mapping: CRITICAL -> R4 via canonical_risk_level
        self.assertEqual(task.risk_level, "CRITICAL")
        self.assertEqual(task.canonical_risk_level, RiskLevel.R4_INFRA_MUTATION)

        data = task.to_dict()
        self.assertEqual(len(data["artifacts"]), 2)
        self.assertIsInstance(data["artifacts"][0], dict)
        self.assertEqual(data["artifacts"][1], "legacy_path.json")

        reconstructed = TaskNode.from_dict(data)
        self.assertEqual(len(reconstructed.artifacts), 2)
        self.assertIsInstance(reconstructed.artifacts[0], Artifact)
        self.assertEqual(reconstructed.artifacts[0].artifact_id, "art-002")
        self.assertEqual(reconstructed.artifacts[1], "legacy_path.json")

    # --- 2. Policy & Authorization Engine Tests ---

    def test_policy_allow_safe_read(self):
        profile = AgentProfile(
            agent_id="Quantum-AuditAgent",
            name="Audit Agent",
            domain="Security",
            allowed_tools=["mcp:*", "local_cli:*"],
            constraints=AgentConstraints(read_only=False, network_access=True)
        )
        res = self.policy.evaluate_policy(
            agent_profile=profile,
            action="read",
            tool_or_skill="local_cli:cat",
            resource="src/main.py",
            risk_level=RiskLevel.R0_READ_ONLY
        )
        self.assertEqual(res.decision, PolicyDecision.ALLOW)

    def test_policy_deny_path_traversal(self):
        profile = AgentProfile(
            agent_id="Quantum-AuditAgent",
            name="Audit Agent",
            domain="Security"
        )
        res = self.policy.evaluate_policy(
            agent_profile=profile,
            action="read",
            tool_or_skill="local_cli:cat",
            resource="../../windows/system32/cmd.exe",
            risk_level=RiskLevel.R0_READ_ONLY
        )
        self.assertEqual(res.decision, PolicyDecision.DENY)
        self.assertIn("Path traversal", res.reason)

    def test_policy_deny_write_for_read_only_agent(self):
        profile = AgentProfile(
            agent_id="Quantum-AuditAgent",
            name="Audit Agent",
            domain="Security",
            constraints=AgentConstraints(read_only=True, network_access=True)
        )
        res = self.policy.evaluate_policy(
            agent_profile=profile,
            action="write",
            tool_or_skill="local_cli:edit",
            resource="reports/audit.json",
            risk_level=RiskLevel.R1_LOCAL_WRITE
        )
        self.assertEqual(res.decision, PolicyDecision.DENY)
        self.assertIn("read-only execution", res.reason)

    def test_policy_deny_out_of_scope_write(self):
        profile = AgentProfile(
            agent_id="Quantum-AuditAgent",
            name="Audit Agent",
            domain="Security",
            constraints=AgentConstraints(read_only=False)
        )
        res = self.policy.evaluate_policy(
            agent_profile=profile,
            action="write",
            tool_or_skill="local_cli:edit",
            resource="secrets/keys.json",
            risk_level=RiskLevel.R2_REPO_MUTATION,
            write_scopes=["reports/"]
        )
        self.assertEqual(res.decision, PolicyDecision.DENY)
        self.assertIn("not permitted by declared write_scopes", res.reason)

    def test_policy_deny_network_call_when_offline(self):
        profile = AgentProfile(
            agent_id="Quantum-AuditAgent",
            name="Audit Agent",
            domain="Security",
            constraints=AgentConstraints(network_access=False)
        )
        res = self.policy.evaluate_policy(
            agent_profile=profile,
            action="http_request",
            tool_or_skill="mcp:curl",
            resource="https://api.github.com",
            risk_level=RiskLevel.R3_EXTERNAL_SIDE_EFFECT
        )
        self.assertEqual(res.decision, PolicyDecision.DENY)
        self.assertIn("network access is disabled", res.reason)

    def test_policy_deny_r5_destructive(self):
        profile = AgentProfile(
            agent_id="Quantum-AuditAgent",
            name="Audit Agent",
            domain="Security"
        )
        res = self.policy.evaluate_policy(
            agent_profile=profile,
            action="execute",
            tool_or_skill="local_cli:git_push_force",
            risk_level=RiskLevel.R5_DESTRUCTIVE
        )
        self.assertEqual(res.decision, PolicyDecision.DENY)
        self.assertIn("prohibited from autonomous execution", res.reason)

    def test_policy_r4_requires_approval_and_anti_self_approval(self):
        profile = AgentProfile(
            agent_id="Quantum-AuditAgent",
            name="Audit Agent",
            domain="Security"
        )
        res = self.policy.evaluate_policy(
            agent_profile=profile,
            action="install_package",
            tool_or_skill="local_cli:pip_install",
            risk_level=RiskLevel.R4_INFRA_MUTATION,
            task_id="tsk-infra-01"
        )
        self.assertEqual(res.decision, PolicyDecision.REQUIRE_APPROVAL)
        self.assertIsNotNone(res.approval_id)

        # Test Anti-Self-Approval: The agent cannot approve its own request
        self_grant = self.policy.grant_approval(
            approval_id=res.approval_id,
            operator_id="Quantum-AuditAgent"
        )
        self.assertFalse(self_grant)
        req = self.policy.get_approval_request(res.approval_id)
        self.assertEqual(req.status, ApprovalStatus.DENIED)

        # Create new request for valid human operator approval
        res2 = self.policy.evaluate_policy(
            agent_profile=profile,
            action="install_package",
            tool_or_skill="local_cli:pip_install",
            risk_level=RiskLevel.R4_INFRA_MUTATION,
            task_id="tsk-infra-02"
        )
        human_grant = self.policy.grant_approval(
            approval_id=res2.approval_id,
            operator_id="human-operator-roberto"
        )
        self.assertTrue(human_grant)
        req2 = self.policy.get_approval_request(res2.approval_id)
        self.assertEqual(req2.status, ApprovalStatus.APPROVED)
        self.assertEqual(req2.approved_by, "human-operator-roberto")

    # --- 3. Authoritative State Store Tests ---

    def test_authoritative_state_save_and_load(self):
        from tooling.agentic.dag import ExecutionDAG
        dag = ExecutionDAG()
        dag.add_node(TaskNode(task_id="t1", title="Task 1"))

        mission = Mission(
            mission_id="mis-test-100",
            goal="Test Authoritative State Persistence",
            status=MissionStatus.RUNNING,
            dag=dag
        )
        saved_path = self.state_store.save_mission(mission)
        self.assertTrue(saved_path.exists())

        loaded = self.state_store.load_mission("mis-test-100")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.mission_id, "mis-test-100")
        self.assertEqual(loaded.status, MissionStatus.RUNNING)
        self.assertEqual(len(loaded.dag.nodes), 1)

        active = self.state_store.list_active_missions()
        self.assertIn("mis-test-100", active)

    def test_corrupted_state_quarantine(self):
        corrupt_file = self.config.missions_dir / "mis-corrupt-999.json"
        corrupt_file.write_text("{ incomplete broken json: ", encoding="utf-8")

        with self.assertRaises(CorruptedStateFileError) as ctx:
            self.state_store.load_mission("mis-corrupt-999")

        # Assert original file was moved/quarantined
        self.assertFalse(corrupt_file.exists())
        quarantine_file = ctx.exception.quarantine_path
        self.assertTrue(quarantine_file.exists())
        self.assertIn(str(self.config.corrupted_dir), str(quarantine_file))


if __name__ == "__main__":
    unittest.main()
