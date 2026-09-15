"""v0.2.0 restart/recovery contracts for durable authority and mutable effects."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from tooling.agentic.adapters.local import LocalAction, LocalAdapterType
from tooling.agentic.authorization import AuthorizationGrant
from tooling.agentic.dag import ExecutionDAG
from tooling.agentic.models import (
    ApprovalStatus,
    ExecutionAttempt,
    ExecutionState,
    IdempotencySemantics,
    Mission,
    MissionOutcome,
    MissionStatus,
    RecoveryState,
    RiskLevel,
    SideEffectRecord,
    SideEffectType,
    TaskNode,
    TaskStatus,
    VerificationRequirement,
    VerificationState,
    VerificationType,
)
from tooling.agentic.runtime import JarvisAgenticRuntime


class TestV020RestartRecovery(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def _mission(mission_id: str, *tasks: TaskNode) -> Mission:
        dag = ExecutionDAG()
        for task in tasks:
            dag.add_node(task)
        return Mission(
            mission_id=mission_id,
            goal=mission_id,
            dag=dag,
            status=MissionStatus.RUNNING,
        )

    def _interrupted_mutation(
        self,
        *,
        task_id: str = "tsk-restart-write",
        path: str = "restart-output.txt",
        idempotency: IdempotencySemantics = IdempotencySemantics.IDEMPOTENT,
    ) -> TaskNode:
        action = LocalAction(
            adapter=LocalAdapterType.WRITE_TEXT,
            path=path,
            content="replayed exactly once",
        ).to_dict()
        task = TaskNode(
            task_id=task_id,
            title="Restart-safe mutation",
            agent_profile="Quantum-ExecutorAgent",
            required_skills=["general"],
            action=action,
            risk_level=RiskLevel.R4_INFRA_MUTATION,
            approval_status=ApprovalStatus.APPROVED,
            write_scopes=[path],
            status=TaskStatus.RUNNING,
            verification_requirements=[
                VerificationRequirement(
                    check_type=VerificationType.FILE_EXISTS,
                    target=path,
                )
            ],
        )
        task.record_attempt(
            ExecutionAttempt(
                attempt_id=f"att-interrupted-{task_id}",
                mission_id="mis-restart",
                task_id=task_id,
                attempt_number=1,
                agent_id="Quantum-ExecutorAgent",
                tool_id="local.write_text",
                execution_state=ExecutionState.RUNNING,
                verification_state=VerificationState.UNVERIFIED,
                recovery_state=RecoveryState.NOT_REQUIRED,
                outcome=MissionOutcome.OUTCOME_UNKNOWN,
                side_effects=[
                    SideEffectRecord(
                        side_effect_id=f"effect-{task_id}",
                        side_effect_type=SideEffectType.LOCAL_WRITE,
                        target=path,
                        observed_change="process interrupted after mutable dispatch",
                        idempotency=idempotency,
                        provenance_hash="a" * 64,
                    )
                ],
                trace_id=f"trace-interrupted-{task_id}",
            )
        )
        return task

    def _persist_grant(
        self,
        runtime: JarvisAgenticRuntime,
        task: TaskNode,
        *,
        scopes: list[str] | None = None,
        expires_delta: timedelta = timedelta(hours=1),
    ) -> AuthorizationGrant:
        now = datetime.now(timezone.utc)
        grant = AuthorizationGrant.issue(
            task_id=task.task_id,
            subject="Quantum-ExecutorAgent",
            action="command",
            scopes=scopes if scopes is not None else list(task.write_scopes),
            budget={},
            approved_by="operator:fixture",
            issued_utc=(now - timedelta(minutes=1)).isoformat(),
            expires_utc=(now + expires_delta).isoformat(),
            registry_root=self.root,
        )
        runtime.policy.authorization_store.save(grant)
        task.action["authorization_grant_id"] = grant.grant_id
        return grant

    def _persist_mission_with_grant(
        self,
        *,
        idempotency: IdempotencySemantics = IdempotencySemantics.IDEMPOTENT,
        scopes: list[str] | None = None,
        expires_delta: timedelta = timedelta(hours=1),
    ) -> tuple[JarvisAgenticRuntime, Mission, TaskNode, AuthorizationGrant]:
        runtime = JarvisAgenticRuntime(registry_root=self.root)
        task = self._interrupted_mutation(idempotency=idempotency)
        grant = self._persist_grant(
            runtime,
            task,
            scopes=scopes,
            expires_delta=expires_delta,
        )
        mission = self._mission("mis-restart", task)
        runtime.state_store.save_mission(mission)
        return runtime, mission, task, grant

    def test_revoked_grant_blocks_restart_before_adapter_invocation(self):
        runtime, mission, _, grant = self._persist_mission_with_grant()
        grant.revoke(datetime.now(timezone.utc).isoformat())
        runtime.policy.authorization_store.save(grant)
        mission_path = runtime.state_store.get_mission_path(mission.mission_id)
        before = mission_path.read_bytes()

        restarted = JarvisAgenticRuntime(registry_root=self.root)
        with patch.object(
            restarted.local_adapter,
            "execute",
            side_effect=AssertionError("adapter must not run under revoked authority"),
        ):
            result = restarted.resume_mission(mission.mission_id)

        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["waves_executed"], 0)
        self.assertIn("GRANT_REVOKED", result["blocked_tasks"][0]["reason"])
        self.assertEqual(mission_path.read_bytes(), before)

    def test_expired_grant_blocks_restart_before_adapter_invocation(self):
        runtime, mission, _, _ = self._persist_mission_with_grant(
            expires_delta=timedelta(seconds=-1)
        )
        mission_path = runtime.state_store.get_mission_path(mission.mission_id)
        before = mission_path.read_bytes()

        restarted = JarvisAgenticRuntime(registry_root=self.root)
        with patch.object(
            restarted.local_adapter,
            "execute",
            side_effect=AssertionError("adapter must not run under expired authority"),
        ):
            result = restarted.resume_mission(mission.mission_id)

        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("GRANT_EXPIRED", result["blocked_tasks"][0]["reason"])
        self.assertEqual(mission_path.read_bytes(), before)

    def test_scope_mismatch_blocks_restart_before_adapter_invocation(self):
        runtime, mission, _, _ = self._persist_mission_with_grant(scopes=["other.txt"])
        mission_path = runtime.state_store.get_mission_path(mission.mission_id)
        before = mission_path.read_bytes()

        restarted = JarvisAgenticRuntime(registry_root=self.root)
        with patch.object(
            restarted.local_adapter,
            "execute",
            side_effect=AssertionError("adapter must not run outside granted scope"),
        ):
            result = restarted.resume_mission(mission.mission_id)

        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("SCOPE_MISMATCH", result["blocked_tasks"][0]["reason"])
        self.assertEqual(mission_path.read_bytes(), before)

    def test_missing_durable_grant_blocks_restart(self):
        runtime = JarvisAgenticRuntime(registry_root=self.root)
        task = self._interrupted_mutation()
        mission = self._mission("mis-restart", task)
        runtime.state_store.save_mission(mission)

        restarted = JarvisAgenticRuntime(registry_root=self.root)
        with patch.object(
            restarted.local_adapter,
            "execute",
            side_effect=AssertionError("adapter must not run without durable authority"),
        ):
            result = restarted.resume_mission(mission.mission_id)

        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("durable authorization grant", result["blocked_tasks"][0]["reason"].lower())

    def test_reconciliation_required_remains_blocked_even_with_valid_grant(self):
        _, mission, task, _ = self._persist_mission_with_grant(
            idempotency=IdempotencySemantics.RECONCILIATION_REQUIRED
        )
        restarted = JarvisAgenticRuntime(registry_root=self.root)

        with patch.object(
            restarted.local_adapter,
            "execute",
            side_effect=AssertionError("ambiguous mutable effect must reconcile first"),
        ):
            result = restarted.resume_mission(mission.mission_id)

        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("RECONCILIATION_REQUIRED", result["blocked_tasks"][0]["reason"])
        restored = restarted.state_store.load_mission(mission.mission_id)
        self.assertEqual(restored.dag.nodes[task.task_id].attempts[0].outcome, MissionOutcome.OUTCOME_UNKNOWN)

    def test_valid_matching_grant_allows_idempotent_replay_and_preserves_verified_task(self):
        runtime, mission, task, _ = self._persist_mission_with_grant()
        verified = TaskNode(
            task_id="tsk-already-verified",
            title="Already verified",
            agent_profile="Quantum-ExecutorAgent",
            status=TaskStatus.VERIFIED,
        )
        mission.dag.add_node(verified)
        runtime.state_store.save_mission(mission)

        restarted = JarvisAgenticRuntime(registry_root=self.root)
        result = restarted.resume_mission(mission.mission_id)

        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual((self.root / "restart-output.txt").read_text(encoding="utf-8"), "replayed exactly once")
        restored = restarted.state_store.load_mission(mission.mission_id)
        replayed = restored.dag.nodes[task.task_id]
        preserved = restored.dag.nodes[verified.task_id]
        self.assertEqual(replayed.status, TaskStatus.VERIFIED)
        self.assertEqual(len(replayed.attempts), 2)
        self.assertEqual(preserved.status, TaskStatus.VERIFIED)
        self.assertEqual(preserved.attempts, [])


if __name__ == "__main__":
    unittest.main()
