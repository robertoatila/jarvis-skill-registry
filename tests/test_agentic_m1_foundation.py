"""
test_agentic_m1_foundation.py // Milestone 1 Foundation Test Suite
Pure Python 3.12 Standard Library (Zero External PIP Dependencies)

Validates Milestone 1 (M1) Hardened Execution & Trust Foundation:
1. Fail-closed RiskLevel.normalize & strict state enum validation
2. Action-bound approval digests (context_hash) & verifiable operator signatures
3. Anti-self-approval enforcement preventing autonomous privilege escalation
4. Real ExecutionAttempt recording via task.record_attempt() in runtime.execute_goal
5. Multi-dimensional state separation (ExecutionState != VerificationState != Outcome)
6. Mission resume recovery tracking without attempts/retry regression
7. Skill fitness penalty attribution & automatic compensation provenance gating
"""

import unittest
import tempfile
import uuid
import hashlib
from pathlib import Path
from datetime import datetime, timezone

from tooling.agentic.models import (
    Mission,
    MissionStatus,
    TaskNode,
    TaskStatus,
    VerificationRequirement,
    VerificationType,
    VerificationStatus,
    RiskLevel,
    ApprovalStatus,
    ExecutionAttempt,
    ExecutionState,
    VerificationState,
    RecoveryState,
    MissionOutcome,
    FailureClass,
    FailureAttribution,
    SideEffectRecord,
    SideEffectType,
    IdempotencySemantics,
    Artifact,
    ArtifactType,
    SCHEMA_VERSION
)
from tooling.agentic.config import JarvisRuntimeConfig
from tooling.agentic.policy import PolicyEngine, PolicyDecision, ApprovalRequest
from tooling.agentic.fitness import SkillFitnessEngine
from tooling.agentic.resilience import CheckpointManager
from tooling.agentic.dag import ExecutionDAG
from tooling.agentic.runtime import JarvisAgenticRuntime
from tooling.agentic.profiles import AgentProfile, AgentConstraints


class TestAgenticM1Foundation(unittest.TestCase):
    """Verifies all Milestone 1 (M1) architectural and security invariants."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp_dir.name)
        self.config = JarvisRuntimeConfig(registry_root=self.root)
        self.config.ensure_directories()
        self.policy = PolicyEngine(config=self.config)
        self.runtime = JarvisAgenticRuntime(config=self.config)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_01_risk_level_normalize_fail_closed(self):
        """Invariant: RiskLevel.normalize preserves legacy values but fails closed on unrecognized strings."""
        # Known legacy values must map correctly
        self.assertEqual(RiskLevel.normalize("UNKNOWN"), RiskLevel.R0_READ_ONLY)
        self.assertEqual(RiskLevel.normalize("LOW"), RiskLevel.R0_READ_ONLY)
        self.assertEqual(RiskLevel.normalize("MEDIUM"), RiskLevel.R1_LOCAL_WRITE)
        self.assertEqual(RiskLevel.normalize("HIGH"), RiskLevel.R2_REPO_MUTATION)
        self.assertEqual(RiskLevel.normalize("CRITICAL"), RiskLevel.R4_INFRA_MUTATION)
        self.assertEqual(RiskLevel.normalize("R0"), RiskLevel.R0_READ_ONLY)
        self.assertEqual(RiskLevel.normalize("R5"), RiskLevel.R5_DESTRUCTIVE)
        self.assertEqual(RiskLevel.normalize(RiskLevel.R2_REPO_MUTATION), RiskLevel.R2_REPO_MUTATION)

        # Unrecognized strings must fail closed (raise ValueError)
        with self.assertRaises(ValueError):
            RiskLevel.normalize("BOGUS_RISK")

        with self.assertRaises(ValueError):
            RiskLevel.normalize("ADMIN_OVERRIDE")

    def test_02_strict_state_validation_and_migration_provenance(self):
        """Invariant: SideEffectRecord and ExecutionAttempt strictly validate states and record migration provenance."""
        # Invalid side_effect_type
        with self.assertRaises(ValueError):
            SideEffectRecord(
                side_effect_id="se-invalid",
                side_effect_type="INVALID_TYPE"
            )

        # Invalid execution_state
        with self.assertRaises(ValueError):
            ExecutionAttempt(
                attempt_id="att-inv-1",
                mission_id="mis-1",
                task_id="tsk-1",
                execution_state="INVALID_EXEC_STATE"
            )

        # Invalid verification_state
        with self.assertRaises(ValueError):
            ExecutionAttempt(
                attempt_id="att-inv-2",
                mission_id="mis-1",
                task_id="tsk-1",
                verification_state="NOT_A_VALID_VERIF_STATE"
            )

        # Legacy attempt without mission_id/task_id marks migration provenance
        legacy_data = {
            "schema_version": SCHEMA_VERSION,
            "attempt_id": "att-leg-01"
        }
        restored = ExecutionAttempt.from_dict(legacy_data)
        self.assertEqual(restored.mission_id, "mis-legacy")
        self.assertEqual(restored.task_id, "tsk-legacy")
        self.assertEqual(
            restored.environment_fingerprint.get("_migration_provenance"),
            "LEGACY_SYNTHESIZED_IDENTIFIERS"
        )

    def test_03_approval_request_context_hash_and_signature(self):
        """Invariant: ApprovalRequest binds to context_hash digest and stores verifiable operator signature."""
        req = self.policy.create_approval_request(
            task_id="tsk-infra-01",
            agent_profile="Quantum-ExecutorAgent",
            action="deploy_service",
            tool_or_skill="infrastructure",
            resource="cluster/worker-01",
            risk_level=RiskLevel.R4_INFRA_MUTATION,
            justification="Deploying containerized microservice"
        )

        expected_raw = "tsk-infra-01:Quantum-ExecutorAgent:deploy_service:infrastructure:cluster/worker-01:R4"
        expected_hash = hashlib.sha256(expected_raw.encode("utf-8")).hexdigest()
        self.assertEqual(req.context_hash, expected_hash)
        self.assertIsNone(req.signature)

        # Anti-self-approval blocks agent
        agent_granted = self.policy.grant_approval(req.approval_id, operator_id="Quantum-ExecutorAgent")
        self.assertFalse(agent_granted)
        self.assertEqual(req.status, ApprovalStatus.DENIED)

        # Create fresh approval for human operator
        req2 = self.policy.create_approval_request(
            task_id="tsk-infra-02",
            agent_profile="Quantum-ExecutorAgent",
            action="deploy_service",
            tool_or_skill="infrastructure",
            resource="cluster/worker-02",
            risk_level=RiskLevel.R4_INFRA_MUTATION,
            justification="Deploying containerized microservice 2"
        )

        operator_sig = "ed25519:sig-9876543210fedcba"
        human_granted = self.policy.grant_approval(
            req2.approval_id,
            operator_id="HumanOperator_Roberto",
            signature=operator_sig
        )
        self.assertTrue(human_granted)
        self.assertEqual(req2.status, ApprovalStatus.APPROVED)
        self.assertEqual(req2.approved_by, "HumanOperator_Roberto")
        self.assertEqual(req2.signature, operator_sig)

        # Verify serialization includes context_hash and signature
        d = req2.to_dict()
        self.assertIn("context_hash", d)
        self.assertEqual(d["signature"], operator_sig)

    def test_04_runtime_persists_real_execution_attempts(self):
        """Invariant: Runtime execute_goal records ExecutionAttempt instances on TaskNode.attempts."""
        mission_id = f"mis-{uuid.uuid4().hex[:8]}"
        mission = Mission(mission_id=mission_id, goal="M1 Real Attempt Persistence")
        dag = ExecutionDAG()

        # Task writing a local file
        test_file = self.root / "output_test.txt"
        t1 = TaskNode(
            task_id="tsk-write-01",
            title="Write Output File",
            agent_profile="Quantum-ExecutorAgent",
            risk_level=RiskLevel.R1_LOCAL_WRITE,
            write_scopes=[str(test_file)]
        )
        t1.verification_requirements.append(VerificationRequirement(
            check_type=VerificationType.COMMAND_EXIT_ZERO,
            target=f'python -c "import pathlib; pathlib.Path(r\'{test_file}\').write_text(\'M1 Evidence\')"'
        ))
        t1.verification_requirements.append(VerificationRequirement(
            check_type=VerificationType.FILE_EXISTS,
            target=str(test_file)
        ))

        dag.add_node(t1)
        mission.dag = dag

        result = self.runtime.execute_goal(mission)
        self.assertEqual(result["status"], "SUCCESS")

        # Load persisted mission
        reloaded = self.runtime.load_mission(mission_id)
        self.assertIsNotNone(reloaded)
        task_out = reloaded.dag.nodes["tsk-write-01"]

        self.assertEqual(task_out.status, TaskStatus.VERIFIED)
        self.assertEqual(len(task_out.attempts), 1)

        att = task_out.attempts[0]
        self.assertIsInstance(att, ExecutionAttempt)
        self.assertEqual(att.attempt_number, 1)
        self.assertEqual(att.execution_state, ExecutionState.FINISHED)
        self.assertEqual(att.verification_state, VerificationState.VERIFIED)
        self.assertEqual(att.outcome, MissionOutcome.SUCCEEDED)
        self.assertEqual(att.mission_id, mission_id)
        self.assertEqual(att.task_id, "tsk-write-01")
        self.assertGreater(len(att.side_effects), 0)
        self.assertEqual(att.side_effects[0].target, str(test_file))
        self.assertTrue(bool(att.side_effects[0].provenance_hash))

    def test_05_multidimensional_state_separation_on_verification_failure(self):
        """
        Invariant: Command exit 0 != Verified.
        When execution succeeds (exit 0) but verification check fails,
        ExecutionState is FINISHED, VerificationState is REJECTED, and Outcome is FAILED.
        """
        mission_id = f"mis-{uuid.uuid4().hex[:8]}"
        mission = Mission(mission_id=mission_id, goal="M1 Separation Test")
        dag = ExecutionDAG()

        missing_target = self.root / "does_not_exist.txt"
        t1 = TaskNode(
            task_id="tsk-exit0-fail-verify",
            title="Command Exit Zero but Missing Verification Target",
            agent_profile="Quantum-ExecutorAgent",
            risk_level=RiskLevel.R0_READ_ONLY
        )
        # Execution command exits 0
        t1.verification_requirements.append(VerificationRequirement(
            check_type=VerificationType.COMMAND_EXIT_ZERO,
            target='python -c "import sys; sys.exit(0)"'
        ))
        # But required file does NOT exist
        t1.verification_requirements.append(VerificationRequirement(
            check_type=VerificationType.FILE_EXISTS,
            target=str(missing_target)
        ))

        dag.add_node(t1)
        mission.dag = dag

        result = self.runtime.execute_goal(mission)
        self.assertEqual(result["status"], "FAILED")

        reloaded = self.runtime.load_mission(mission_id)
        task_out = reloaded.dag.nodes["tsk-exit0-fail-verify"]

        self.assertEqual(task_out.status, TaskStatus.FAILED)
        self.assertEqual(len(task_out.attempts), 1)

        att = task_out.attempts[0]
        # Strict state separation verified!
        self.assertEqual(att.execution_state, ExecutionState.FINISHED)
        self.assertEqual(att.verification_state, VerificationState.REJECTED)
        self.assertEqual(att.outcome, MissionOutcome.FAILED)
        self.assertEqual(att.failure_class, FailureClass.VALIDATION)
        self.assertEqual(att.failure_attribution, FailureAttribution.AGENT)

    def test_06_mission_resume_preserves_attempts_and_retry_count(self):
        """Invariant: Resuming an interrupted mission records recovery attempt and preserves attempt history."""
        mission_id = f"mis-resume-{uuid.uuid4().hex[:8]}"
        mission = Mission(mission_id=mission_id, goal="Resume Invariant Test")
        dag = ExecutionDAG()

        t1 = TaskNode(
            task_id="tsk-interrupted-01",
            title="Interrupted Running Task",
            agent_profile="Quantum-ExecutorAgent",
            status=TaskStatus.RUNNING,
            retry_count=0,
            max_retries=3
        )
        t1.verification_requirements.append(VerificationRequirement(
            check_type=VerificationType.COMMAND_EXIT_ZERO,
            target='python -c "import sys; sys.exit(0)"'
        ))

        dag.add_node(t1)
        mission.dag = dag
        self.runtime.state_store.save_mission(mission)

        # Resume mission
        res = self.runtime.resume_mission(mission_id)
        self.assertEqual(res["status"], "SUCCESS")

        reloaded = self.runtime.load_mission(mission_id)
        task_out = reloaded.dag.nodes["tsk-interrupted-01"]

        self.assertEqual(task_out.status, TaskStatus.VERIFIED)
        self.assertEqual(task_out.retry_count, 1)
        # 1 recovery attempt + 1 execution attempt = 2 attempts preserved
        self.assertEqual(len(task_out.attempts), 2)
        self.assertEqual(task_out.attempts[0].recovery_state, RecoveryState.RECOVERED)
        self.assertEqual(task_out.attempts[1].execution_state, ExecutionState.FINISHED)
        self.assertEqual(task_out.attempts[1].verification_state, VerificationState.VERIFIED)

    def test_07_skill_fitness_penalty_attribution_and_compensation_provenance(self):
        """Invariant: SkillFitnessEngine ignores non-skill failures; CheckpointManager gates compensation on provenance."""
        # 1. Skill fitness attribution
        self.assertFalse(SkillFitnessEngine.is_skill_penalizable("NODE"))
        self.assertFalse(SkillFitnessEngine.is_skill_penalizable("POLICY"))
        self.assertFalse(SkillFitnessEngine.is_skill_penalizable(FailureAttribution.ENVIRONMENT))
        self.assertFalse(SkillFitnessEngine.is_skill_penalizable(FailureAttribution.EXTERNAL_SERVICE))
        self.assertTrue(SkillFitnessEngine.is_skill_penalizable("SKILL"))
        self.assertTrue(SkillFitnessEngine.is_skill_penalizable(FailureAttribution.SKILL))

        # 2. Compensation provenance gate
        se_unprovenanced = SideEffectRecord(
            side_effect_id="se-noprov",
            side_effect_type=SideEffectType.INFRASTRUCTURE_MUTATION,
            target="resource/target",
            idempotency=IdempotencySemantics.COMPENSATION_REQUIRED,
            compensation_action="rollback_action",
            provenance_hash=""  # Empty!
        )
        se_provenanced = SideEffectRecord(
            side_effect_id="se-prov",
            side_effect_type=SideEffectType.INFRASTRUCTURE_MUTATION,
            target="resource/target",
            idempotency=IdempotencySemantics.COMPENSATION_REQUIRED,
            compensation_action="rollback_action",
            provenance_hash="sha256:abcd1234ef567890abcd1234ef567890abcd1234ef567890abcd1234ef567890"
        )

        self.assertFalse(CheckpointManager.can_automatically_compensate(se_unprovenanced))
        self.assertTrue(CheckpointManager.can_automatically_compensate(se_provenanced))

        # CheckpointManager refuses automatic compensating DAG for unprovenanced mutation
        mgr = CheckpointManager(config=self.config)
        failed_task = TaskNode(
            task_id="tsk-failed-mut",
            title="Failed Mutation Task",
            agent_profile="Quantum-ExecutorAgent",
            write_scopes=["some/file.txt"]
        )
        failed_att = ExecutionAttempt(
            attempt_id="att-fail-1",
            mission_id="mis-test",
            task_id="tsk-failed-mut",
            side_effects=[se_unprovenanced]
        )
        failed_task.record_attempt(failed_att)

        comp_dag = mgr.generate_compensating_action_dag(failed_task)
        self.assertIsNone(comp_dag, "Must refuse compensation DAG when provenance is missing!")

        # With valid provenance, compensating DAG is admitted
        failed_task_prov = TaskNode(
            task_id="tsk-failed-mut-2",
            title="Failed Mutation Task 2",
            agent_profile="Quantum-ExecutorAgent",
            write_scopes=["some/file.txt"]
        )
        failed_att_prov = ExecutionAttempt(
            attempt_id="att-fail-2",
            mission_id="mis-test",
            task_id="tsk-failed-mut-2",
            side_effects=[se_provenanced]
        )
        failed_task_prov.record_attempt(failed_att_prov)

        comp_dag_valid = mgr.generate_compensating_action_dag(failed_task_prov)
        self.assertIsNotNone(comp_dag_valid, "Must allow compensating DAG when provenance is verified!")
        self.assertIn("compensate-tsk-failed-mut-2", comp_dag_valid.nodes)


if __name__ == "__main__":
    unittest.main()
