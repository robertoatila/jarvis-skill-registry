"""
test_agentic_resilience.py // Unit tests for Failure Recovery & Restart Resilience (Phase 21)
"""

import unittest
import tempfile
from pathlib import Path

from tooling.agentic.models import Mission, TaskNode, TaskStatus, MissionStatus
from tooling.agentic.dag import ExecutionDAG
from tooling.agentic.resilience import CheckpointManager, MissionCheckpoint


class TestFailureRecoveryResilience(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.work_dir = Path(self.temp_dir.name)
        self.manager = CheckpointManager(checkpoints_dir=self.work_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_01_save_and_load_checkpoint(self):
        dag = ExecutionDAG()
        t1 = TaskNode(task_id="t1", title="Task 1", status=TaskStatus.VERIFIED)
        t2 = TaskNode(task_id="t2", title="Task 2", status=TaskStatus.RUNNING)
        dag.add_node(t1)
        dag.add_node(t2)
        dag.add_dependency("t1", "t2")

        mission = Mission(mission_id="msn-test-resilience", goal="Resilience Goal")
        mission.status = MissionStatus.RUNNING

        chk = self.manager.save_checkpoint(mission, dag, current_wave=1, active_task_ids=["t2"])
        self.assertTrue(chk.checkpoint_id.startswith("chk-"))

        # Verify file exists on disk
        saved_file = self.work_dir / f"{chk.checkpoint_id}.json"
        self.assertTrue(saved_file.exists())

        # Load back
        loaded_mission, loaded_dag, wave = self.manager.load_checkpoint(chk.checkpoint_id)
        self.assertEqual(loaded_mission.mission_id, "msn-test-resilience")
        self.assertEqual(wave, 1)
        self.assertEqual(len(loaded_dag.nodes), 2)
        self.assertEqual(loaded_dag.nodes["t1"].status, TaskStatus.VERIFIED)
        self.assertEqual(loaded_dag.nodes["t2"].status, TaskStatus.RUNNING)

    def test_02_idempotent_recovery_and_retry_increment(self):
        dag = ExecutionDAG()
        # t1 is already verified: MUST NOT be re-executed
        t1 = TaskNode(task_id="t1", title="Step 1", status=TaskStatus.VERIFIED)
        # t2 crashed while running: should be recovered to READY with retry_count=1
        t2 = TaskNode(task_id="t2", title="Step 2", status=TaskStatus.RUNNING, retry_count=0, max_retries=3)
        # t3 failed and exhausted all retries: should stay FAILED
        t3 = TaskNode(task_id="t3", title="Step 3", status=TaskStatus.FAILED, retry_count=3, max_retries=3)
        dag.add_node(t1)
        dag.add_node(t2)
        dag.add_node(t3)

        mission = Mission(mission_id="msn-crash-recovery", goal="Crash Recovery")
        chk = self.manager.save_checkpoint(mission, dag, current_wave=2)

        # Execute recovery
        recovery = self.manager.recover_mission(chk.checkpoint_id)

        self.assertIn("t1", recovery["untouched_verified_tasks"])
        self.assertIn("t2", recovery["recovered_tasks"])
        self.assertIn("t3", recovery["exhausted_tasks"])

        # Reload recovered checkpoint and verify state
        _, rec_dag, _ = self.manager.load_checkpoint(chk.checkpoint_id)
        # t1 remains VERIFIED (idempotency preserved!)
        self.assertEqual(rec_dag.nodes["t1"].status, TaskStatus.VERIFIED)
        # t2 is reset to READY with retry count incremented
        self.assertEqual(rec_dag.nodes["t2"].status, TaskStatus.READY)
        self.assertEqual(rec_dag.nodes["t2"].retry_count, 1)
        # t3 remains FAILED
        self.assertEqual(rec_dag.nodes["t3"].status, TaskStatus.FAILED)


if __name__ == "__main__":
    unittest.main()
