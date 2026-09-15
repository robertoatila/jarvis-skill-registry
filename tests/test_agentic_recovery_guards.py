"""Recovery must not dispatch effects with unmet recovery requirements."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tooling.agentic.dag import ExecutionDAG
from tooling.agentic.models import (
    Mission, TaskNode, TaskStatus, ExecutionAttempt, SideEffectRecord,
    SideEffectType, IdempotencySemantics, RecoveryState, MissionOutcome,
)
from tooling.agentic.resilience import CheckpointManager, ReplayEngine
from tooling.agentic.runtime import JarvisAgenticRuntime


class TestRecoveryGuards(unittest.TestCase):
    def task(self, mode=IdempotencySemantics.RECONCILIATION_REQUIRED):
        task = TaskNode(task_id="task-effect", title="Interrupted effect", status=TaskStatus.RUNNING)
        task.record_attempt(ExecutionAttempt(
            attempt_id="attempt-effect", mission_id="mission-effect", task_id=task.task_id,
            side_effects=[SideEffectRecord(
                side_effect_id="effect", side_effect_type=SideEffectType.EXTERNAL_WRITE,
                target="synthetic-resource", idempotency=mode,
                compensation_action="proposed-only", provenance_hash="unverified-hash",
            )],
        ))
        return task

    def mission(self, task):
        mission = Mission(mission_id="mission-effect", goal="Recovery guard")
        mission.dag = ExecutionDAG()
        mission.dag.add_node(task)
        return mission

    def test_required_effect_modes_cannot_replay_even_with_proposed_compensation(self):
        for mode in (IdempotencySemantics.RECONCILIATION_REQUIRED,
                     IdempotencySemantics.COMPENSATION_REQUIRED,
                     IdempotencySemantics.IDEMPOTENCY_KEY_REQUIRED,
                     IdempotencySemantics.UNSAFE_TO_RETRY):
            with self.subTest(mode=mode):
                task = self.task(mode)
                before = task.to_dict()
                allowed, reason = ReplayEngine().can_replay_task(task)
                self.assertFalse(allowed)
                self.assertIn(mode.value, reason)
                self.assertEqual(task.to_dict(), before)

    def test_pending_recovery_blocks_even_explicitly_idempotent_effect(self):
        for state in (RecoveryState.RECONCILIATION_PENDING, RecoveryState.COMPENSATION_PENDING,
                      RecoveryState.RECOVERY_PENDING, RecoveryState.UNRECOVERABLE):
            with self.subTest(state=state):
                task = self.task(IdempotencySemantics.IDEMPOTENT)
                task.attempts[0].recovery_state = state
                self.assertFalse(ReplayEngine().can_replay_task(task)[0])

    def test_explicit_idempotent_effect_without_pending_recovery_remains_eligible(self):
        self.assertTrue(ReplayEngine().can_replay_task(self.task(IdempotencySemantics.IDEMPOTENT))[0])

    def test_forced_replay_does_not_override_effect_guard(self):
        task = self.task()
        mission = self.mission(task)
        before = task.to_dict()
        result = ReplayEngine().replay_mission_dag(mission.dag, force=True)
        self.assertEqual(result["eligible_count"], 0)
        self.assertEqual(result["blocked_tasks"][0]["task_id"], task.task_id)
        self.assertEqual(task.to_dict(), before)

    def test_checkpoint_recovery_preserves_unknown_outcome_and_retry_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = CheckpointManager(checkpoints_dir=Path(directory))
            task = self.task()
            mission = self.mission(task)
            checkpoint = manager.save_checkpoint(mission, mission.dag)
            before = task.to_dict()
            result = manager.recover_mission(checkpoint.checkpoint_id)
            self.assertFalse(result["dag_ready"])
            self.assertEqual(result["recovered_tasks"], [])
            self.assertEqual(result["blocked_tasks"][0]["task_id"], task.task_id)
            _, restored, _ = manager.load_checkpoint(checkpoint.checkpoint_id)
            self.assertEqual(restored.nodes[task.task_id].to_dict(), before)
            self.assertEqual(restored.nodes[task.task_id].attempts[0].outcome, MissionOutcome.OUTCOME_UNKNOWN)

    def test_runtime_entry_points_block_before_scheduling_or_invocation(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = JarvisAgenticRuntime(registry_root=Path(directory))
            task = self.task()
            mission = self.mission(task)
            path = runtime.state_store.save_mission(mission)
            before = path.read_bytes()
            with patch.object(runtime.scheduler, "replan_waves", side_effect=AssertionError("scheduled")), \
                 patch.object(runtime.infra, "run_command", side_effect=AssertionError("executed")), \
                 patch.object(runtime.local_adapter, "execute", side_effect=AssertionError("wrote")):
                for result in (runtime.resume_mission(mission.mission_id), runtime.execute_goal(mission)):
                    self.assertEqual(result["status"], "BLOCKED")
                    self.assertEqual(result["waves_executed"], 0)
                    self.assertEqual(result["blocked_tasks"][0]["task_id"], task.task_id)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(task.retry_count, 0)


if __name__ == "__main__":
    unittest.main()
