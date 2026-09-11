"""
test_agentic_contracts.py // Tests for J.A.R.V.I.S. Runtime Execution & Failure Semantics Contracts
Pure Python 3.12 Standard Library (Zero External PIP Dependencies)
Validates:
- Multi-dimensional state separation (Execution, Verification, Recovery, Outcome)
- ExecutionAttempt tracking and historical preservation
- Failure classification and attribution invariants
- Side effect registration, idempotency semantics, and compensation provenance
- Backward compatibility of TaskNode and serialization
"""

import unittest
from datetime import datetime, timezone

from tooling.agentic.models import (
    TaskNode,
    TaskStatus,
    ExecutionState,
    VerificationState,
    RecoveryState,
    MissionOutcome,
    FailureClass,
    FailureAttribution,
    SideEffectType,
    IdempotencySemantics,
    SideEffectRecord,
    ExecutionAttempt,
    Artifact,
    RiskLevel,
    VerificationRequirement,
    VerificationType,
    VerificationStatus,
    SCHEMA_VERSION
)


class TestAgenticContracts(unittest.TestCase):
    """Verifies foundational contracts and runtime invariants."""

    def test_execution_attempt_lifecycle_and_serialization(self):
        """Validates ExecutionAttempt creation, field validation, and round-trip serialization."""
        side_effect = SideEffectRecord(
            side_effect_id="se-001",
            side_effect_type=SideEffectType.LOCAL_WRITE,
            target="config/settings.json",
            expected_change="update timeout parameter",
            observed_change="timeout set to 120s",
            idempotency=IdempotencySemantics.IDEMPOTENCY_KEY_REQUIRED,
            rollback_target="config/settings.json.bak",
            compensation_action="restore_backup",
            provenance_hash="a1b2c3d4e5f678901234567890abcdef"
        )

        attempt = ExecutionAttempt(
            attempt_id="att-001",
            mission_id="mis-100",
            task_id="tsk-100",
            attempt_number=1,
            agent_id="Quantum-AuditAgent",
            skill_id="system-troubleshooter",
            node_id="worker-node-1",
            idempotency_key="idemp-key-xyz",
            execution_state=ExecutionState.RUNNING,
            verification_state=VerificationState.UNVERIFIED,
            recovery_state=RecoveryState.NOT_REQUIRED,
            outcome=MissionOutcome.OUTCOME_UNKNOWN,
            side_effects=[side_effect],
            trace_id="trc-001",
            environment_fingerprint={"os": "Windows", "python": "3.12.0"}
        )

        self.assertEqual(attempt.execution_state, ExecutionState.RUNNING)
        self.assertEqual(attempt.verification_state, VerificationState.UNVERIFIED)
        self.assertEqual(attempt.outcome, MissionOutcome.OUTCOME_UNKNOWN)
        self.assertEqual(len(attempt.side_effects), 1)

        # Serialization round-trip
        data = attempt.to_dict()
        self.assertEqual(data["schema_version"], SCHEMA_VERSION)
        self.assertEqual(data["execution_state"], "RUNNING")
        self.assertEqual(data["verification_state"], "UNVERIFIED")
        self.assertEqual(data["outcome"], "OUTCOME_UNKNOWN")

        restored = ExecutionAttempt.from_dict(data)
        self.assertEqual(restored.attempt_id, attempt.attempt_id)
        self.assertEqual(restored.execution_state, ExecutionState.RUNNING)
        self.assertEqual(len(restored.side_effects), 1)
        self.assertEqual(restored.side_effects[0].target, "config/settings.json")
        self.assertEqual(restored.side_effects[0].idempotency, IdempotencySemantics.IDEMPOTENCY_KEY_REQUIRED)

    def test_task_preserves_multiple_attempts_history(self):
        """
        Validates that a TaskNode preserves all execution attempts independently
        instead of overwriting execution state on retry.
        """
        task = TaskNode(
            task_id="tsk-retry-01",
            title="Deploy Service Micro-Component",
            agent_profile="Quantum-ExecutorAgent",
            max_retries=3,
            risk_level=RiskLevel.R2_REPO_MUTATION
        )

        self.assertEqual(task.retry_count, 0)
        self.assertEqual(len(task.attempts), 0)

        # Attempt 1: Worker timeout resulting in OUTCOME_UNKNOWN, attributed to NODE
        att1 = ExecutionAttempt(
            attempt_id="att-001",
            mission_id="mis-001",
            task_id="tsk-retry-01",
            attempt_number=1,
            agent_id="Quantum-ExecutorAgent",
            node_id="remote-node-east",
            execution_state=ExecutionState.TIMED_OUT,
            verification_state=VerificationState.UNVERIFIED,
            recovery_state=RecoveryState.RECONCILIATION_PENDING,
            outcome=MissionOutcome.OUTCOME_UNKNOWN,
            failure_class=FailureClass.TIMEOUT,
            failure_attribution=FailureAttribution.NODE,
            retryable=True
        )
        task.record_attempt(att1)

        self.assertEqual(task.retry_count, 0)
        self.assertEqual(len(task.attempts), 1)
        self.assertEqual(task.attempts[0].failure_attribution, FailureAttribution.NODE)
        self.assertEqual(task.attempts[0].outcome, MissionOutcome.OUTCOME_UNKNOWN)

        # Attempt 2: Reconciled and retried on local node, succeeds and verified
        att2 = ExecutionAttempt(
            attempt_id="att-002",
            mission_id="mis-001",
            task_id="tsk-retry-01",
            attempt_number=2,
            agent_id="Quantum-ExecutorAgent",
            node_id="local",
            execution_state=ExecutionState.FINISHED,
            verification_state=VerificationState.VERIFIED,
            recovery_state=RecoveryState.RECOVERED,
            outcome=MissionOutcome.SUCCEEDED,
            failure_class=None,
            failure_attribution=None,
            retryable=False
        )
        task.record_attempt(att2)

        self.assertEqual(task.retry_count, 1)
        self.assertEqual(len(task.attempts), 2)
        # Verify history is completely preserved
        self.assertEqual(task.attempts[0].node_id, "remote-node-east")
        self.assertEqual(task.attempts[0].execution_state, ExecutionState.TIMED_OUT)
        self.assertEqual(task.attempts[1].node_id, "local")
        self.assertEqual(task.attempts[1].execution_state, ExecutionState.FINISHED)
        self.assertEqual(task.attempts[1].verification_state, VerificationState.VERIFIED)

        # Test full TaskNode serialization with attempts
        task_data = task.to_dict()
        self.assertIn("attempts", task_data)
        self.assertEqual(len(task_data["attempts"]), 2)

        restored_task = TaskNode.from_dict(task_data)
        self.assertEqual(len(restored_task.attempts), 2)
        self.assertEqual(restored_task.attempts[0].attempt_id, "att-001")
        self.assertEqual(restored_task.attempts[1].attempt_id, "att-002")

    def test_state_dimensions_do_not_collapse(self):
        """
        Validates the strict invariant:
        Command Exit 0 != Verified
        Execution Finished != Verification State
        Failure != Outcome Unknown
        """
        # Scenario A: Command exits 0, but verification rejected
        attempt_a = ExecutionAttempt(
            attempt_id="att-dim-a",
            mission_id="mis-dim",
            task_id="tsk-dim",
            execution_state=ExecutionState.FINISHED,
            verification_state=VerificationState.REJECTED,
            outcome=MissionOutcome.FAILED,
            failure_class=FailureClass.VALIDATION,
            failure_attribution=FailureAttribution.AGENT
        )
        self.assertNotEqual(attempt_a.execution_state, attempt_a.verification_state)
        self.assertEqual(attempt_a.execution_state, ExecutionState.FINISHED)
        self.assertEqual(attempt_a.verification_state, VerificationState.REJECTED)

        # Scenario B: Network timeout is OUTCOME_UNKNOWN, NOT confirmed FAILED
        attempt_b = ExecutionAttempt(
            attempt_id="att-dim-b",
            mission_id="mis-dim",
            task_id="tsk-dim",
            execution_state=ExecutionState.TIMED_OUT,
            verification_state=VerificationState.UNVERIFIED,
            recovery_state=RecoveryState.RECONCILIATION_PENDING,
            outcome=MissionOutcome.OUTCOME_UNKNOWN,
            failure_class=FailureClass.TIMEOUT,
            failure_attribution=FailureAttribution.EXTERNAL_SERVICE
        )
        self.assertEqual(attempt_b.outcome, MissionOutcome.OUTCOME_UNKNOWN)
        self.assertNotEqual(attempt_b.outcome, MissionOutcome.FAILED)
        self.assertEqual(attempt_b.recovery_state, RecoveryState.RECONCILIATION_PENDING)

    def test_failure_attribution_protects_skill_fitness(self):
        """
        Validates invariant: When failure is attributed to NODE or POLICY,
        it must not be counted as a skill failure.
        """
        # Node failure
        attempt_node_crash = ExecutionAttempt(
            attempt_id="att-nc",
            mission_id="mis-fit",
            task_id="tsk-fit",
            skill_id="fastapi-pro",
            execution_state=ExecutionState.FAILED,
            failure_class=FailureClass.TRANSIENT,
            failure_attribution=FailureAttribution.NODE
        )
        # Policy denial
        attempt_policy_deny = ExecutionAttempt(
            attempt_id="att-pd",
            mission_id="mis-fit",
            task_id="tsk-fit",
            skill_id="fastapi-pro",
            execution_state=ExecutionState.FAILED,
            failure_class=FailureClass.POLICY,
            failure_attribution=FailureAttribution.POLICY
        )
        # Genuine Skill Bug
        attempt_skill_bug = ExecutionAttempt(
            attempt_id="att-sb",
            mission_id="mis-fit",
            task_id="tsk-fit",
            skill_id="fastapi-pro",
            execution_state=ExecutionState.FAILED,
            failure_class=FailureClass.MALFORMED_RESULT,
            failure_attribution=FailureAttribution.SKILL
        )

        def is_skill_penalizable(att: ExecutionAttempt) -> bool:
            return att.failure_attribution == FailureAttribution.SKILL

        self.assertFalse(is_skill_penalizable(attempt_node_crash))
        self.assertFalse(is_skill_penalizable(attempt_policy_deny))
        self.assertTrue(is_skill_penalizable(attempt_skill_bug))

    def test_compensation_provenance_rule(self):
        """
        Validates mandatory rule: NO PROVENANCE -> NO AUTOMATIC COMPENSATION
        """
        side_effect_without_provenance = SideEffectRecord(
            side_effect_id="se-no-prov",
            side_effect_type=SideEffectType.INFRASTRUCTURE_MUTATION,
            target="aws:s3:bucket-abc",
            expected_change="create bucket",
            observed_change=None,
            idempotency=IdempotencySemantics.COMPENSATION_REQUIRED,
            rollback_target=None,
            compensation_action="delete_bucket",
            provenance_hash=""  # Missing provenance!
        )

        side_effect_with_provenance = SideEffectRecord(
            side_effect_id="se-prov",
            side_effect_type=SideEffectType.INFRASTRUCTURE_MUTATION,
            target="aws:s3:bucket-abc",
            expected_change="create bucket",
            observed_change="bucket created with arn:aws:s3:::bucket-abc",
            idempotency=IdempotencySemantics.COMPENSATION_REQUIRED,
            rollback_target=None,
            compensation_action="delete_bucket",
            provenance_hash="sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069"
        )

        def can_automatically_compensate(record: SideEffectRecord) -> bool:
            return bool(record.provenance_hash and record.compensation_action)

        self.assertFalse(can_automatically_compensate(side_effect_without_provenance))
        self.assertTrue(can_automatically_compensate(side_effect_with_provenance))


if __name__ == "__main__":
    unittest.main()
