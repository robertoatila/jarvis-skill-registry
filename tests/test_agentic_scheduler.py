"""
test_agentic_scheduler.py // Unit and Integration Tests for Phase 02 (Wave Scheduler)
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
"""

import unittest
from tooling.agentic.models import TaskNode, TaskStatus
from tooling.agentic.dag import ExecutionDAG
from tooling.agentic.scheduler import WaveScheduler, scopes_conflict, has_concurrency_conflict


class TestWaveScheduler(unittest.TestCase):

    def test_scope_conflict_detection(self):
        # Exact match
        self.assertTrue(scopes_conflict("state/data.json", "state/data.json"))
        # Hierarchical prefix
        self.assertTrue(scopes_conflict("src", "src/main.py"))
        self.assertTrue(scopes_conflict("src/main.py", "src"))
        # Non-conflicting sibling
        self.assertFalse(scopes_conflict("src/a.py", "src/b.py"))
        self.assertFalse(scopes_conflict("reports/sec", "reports/perf"))

    def test_concurrency_rules(self):
        # READ + READ = ALLOWED
        t1 = TaskNode(task_id="t1", title="Reader 1", read_scopes=["config.json"])
        t2 = TaskNode(task_id="t2", title="Reader 2", read_scopes=["config.json"])
        conflict, _ = has_concurrency_conflict(t1, t2)
        self.assertFalse(conflict, "READ + READ on same resource must be allowed")

        # WRITE + WRITE = CONFLICT
        t3 = TaskNode(task_id="t3", title="Writer 1", write_scopes=["data.db"])
        t4 = TaskNode(task_id="t4", title="Writer 2", write_scopes=["data.db"])
        conflict, msg = has_concurrency_conflict(t3, t4)
        self.assertTrue(conflict)
        self.assertIn("WRITE-WRITE", msg)

        # WRITE + READ = CONFLICT
        conflict, msg = has_concurrency_conflict(t3, t1)
        self.assertFalse(conflict)  # different scopes: data.db vs config.json

        t5 = TaskNode(task_id="t5", title="Writer Config", write_scopes=["config.json"])
        conflict, msg = has_concurrency_conflict(t5, t1)
        self.assertTrue(conflict)
        self.assertIn("WRITE-READ", msg)

    def test_independent_tasks_single_wave(self):
        dag = ExecutionDAG()
        dag.add_node(TaskNode(task_id="A", title="Task A", agent_profile="Agent-1"))
        dag.add_node(TaskNode(task_id="B", title="Task B", agent_profile="Agent-2"))
        dag.add_node(TaskNode(task_id="C", title="Task C", agent_profile="Agent-3"))

        scheduler = WaveScheduler(max_parallel_tasks=4)
        waves = scheduler.schedule(dag)

        self.assertEqual(len(waves), 1)
        self.assertEqual(waves[0].task_ids, ["A", "B", "C"])

    def test_dependent_tasks_sequential_waves(self):
        dag = ExecutionDAG()
        dag.add_node(TaskNode(task_id="A", title="Task A"))
        dag.add_node(TaskNode(task_id="B", title="Task B", dependencies=["A"]))
        dag.add_node(TaskNode(task_id="C", title="Task C", dependencies=["B"]))

        scheduler = WaveScheduler()
        waves = scheduler.schedule(dag)

        self.assertEqual(len(waves), 3)
        self.assertEqual(waves[0].task_ids, ["A"])
        self.assertEqual(waves[1].task_ids, ["B"])
        self.assertEqual(waves[2].task_ids, ["C"])

    def test_write_write_conflict_partitions_into_waves(self):
        dag = ExecutionDAG()
        # No explicit DAG dependency, but they write to the same file
        dag.add_node(TaskNode(task_id="Write1", title="W1", write_scopes=["index/resources.jsonl"], agent_profile="Ag1"))
        dag.add_node(TaskNode(task_id="Write2", title="W2", write_scopes=["index/resources.jsonl"], agent_profile="Ag2"))

        scheduler = WaveScheduler()
        waves = scheduler.schedule(dag)

        self.assertEqual(len(waves), 2, "Conflicting writes must be partitioned into 2 waves")
        self.assertEqual(waves[0].task_ids, ["Write1"])
        self.assertEqual(waves[1].task_ids, ["Write2"])

    def test_agent_capacity_prevents_duplicate_assignment(self):
        dag = ExecutionDAG()
        # 3 tasks with no dependency conflicts, but all need Quantum-AuditAgent
        dag.add_node(TaskNode(task_id="Audit1", title="A1", agent_profile="Quantum-AuditAgent"))
        dag.add_node(TaskNode(task_id="Audit2", title="A2", agent_profile="Quantum-AuditAgent"))
        dag.add_node(TaskNode(task_id="Audit3", title="A3", agent_profile="Quantum-AuditAgent"))

        scheduler = WaveScheduler(allow_agent_concurrency=False)
        waves = scheduler.schedule(dag)

        self.assertEqual(len(waves), 3, "Same agent cannot be scheduled concurrently in same wave")

    def test_max_parallel_tasks_cap(self):
        dag = ExecutionDAG()
        for i in range(6):
            dag.add_node(TaskNode(task_id=f"Task-{i}", title=f"T{i}", agent_profile=f"Agent-{i}"))

        scheduler = WaveScheduler(max_parallel_tasks=2)
        waves = scheduler.schedule(dag)

        self.assertEqual(len(waves), 3)
        for w in waves:
            self.assertEqual(len(w.tasks), 2)

    def test_deterministic_scheduling(self):
        def build_dag():
            dag = ExecutionDAG()
            dag.add_node(TaskNode(task_id="D", title="TD", agent_profile="AgD"))
            dag.add_node(TaskNode(task_id="B", title="TB", agent_profile="AgB"))
            dag.add_node(TaskNode(task_id="A", title="TA", agent_profile="AgA"))
            dag.add_node(TaskNode(task_id="C", title="TC", agent_profile="AgC"))
            return dag

        sched = WaveScheduler(max_parallel_tasks=2)
        w1 = sched.schedule(build_dag())
        w2 = sched.schedule(build_dag())

        self.assertEqual([w.task_ids for w in w1], [w.task_ids for w in w2])
        self.assertEqual(w1[0].task_ids, ["A", "B"])
        self.assertEqual(w1[1].task_ids, ["C", "D"])


class TestDispatchGates(unittest.TestCase):
    def test_scope_aliases_share_write_lock(self):
        self.assertTrue(scopes_conflict("src/../config", "config/app.json"))
        self.assertTrue(scopes_conflict("./src//module", "src/module/a.py"))
        self.assertTrue(scopes_conflict(".", "src/main.py"))
        self.assertFalse(scopes_conflict("src", "src-other"))

    def test_dispatch_uses_verified_dependencies_and_excludes_finished_tasks(self):
        from tooling.agentic.models import TaskStatus
        dag = ExecutionDAG()
        dag.add_node(TaskNode("A", "A", status=TaskStatus.FAILED))
        dag.add_node(TaskNode("B", "B", dependencies=["A"]))
        scheduler = WaveScheduler()
        self.assertEqual(scheduler.next_wave(dag).tasks, [])
        dag.mark_task_status("A", TaskStatus.VERIFIED)
        self.assertEqual(scheduler.next_wave(dag).task_ids, ["B"])

    def test_running_tasks_hold_locks_and_node_capacity(self):
        from tooling.agentic.models import TaskStatus
        dag = ExecutionDAG()
        dag.add_node(TaskNode("A", "A", agent_profile="one", status=TaskStatus.RUNNING, write_scopes=["src"]))
        dag.add_node(TaskNode("B", "B", agent_profile="two", read_scopes=["src/a.py"]))
        dag.add_node(TaskNode("C", "C", agent_profile="three", read_scopes=["docs"]))
        wave = WaveScheduler().next_wave(dag)
        self.assertEqual(wave.task_ids, ["C"])
        self.assertIn("WRITE-READ", wave.rejections["B"])
        self.assertEqual(WaveScheduler(node_capacities={"local": 1}).next_wave(dag).tasks, [])

    def test_capacity_configuration_and_unknown_nodes_fail_explicitly(self):
        for value in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                WaveScheduler(max_parallel_tasks=value)
        dag = ExecutionDAG()
        dag.add_node(TaskNode("A", "A", node_id="unregistered"))
        wave = WaveScheduler().next_wave(dag)
        self.assertIn("Unknown node", wave.rejections["A"])
        with self.assertRaises(RuntimeError):
            WaveScheduler().schedule(dag)

    def test_agent_and_node_capacities_are_independent(self):
        dag = ExecutionDAG()
        for name in "ABC":
            dag.add_node(TaskNode(name, name, agent_profile="worker", node_id="node1" if name != "C" else "node2"))
        scheduler = WaveScheduler(agent_capacities={"worker": 2}, node_capacities={"node1": 1, "node2": 2})
        self.assertEqual(scheduler.next_wave(dag).task_ids, ["A", "C"])

    def test_cancel_and_deadline_prevent_dispatch(self):
        from datetime import datetime, timezone, timedelta
        dag = ExecutionDAG()
        dag.add_node(TaskNode("A", "A"))
        scheduler = WaveScheduler()
        self.assertEqual(scheduler.next_wave(dag, cancelled=True).status, "CANCELLED")
        now = datetime.now(timezone.utc)
        self.assertEqual(scheduler.next_wave(dag, now_utc=now, deadline_utc=now-timedelta(seconds=1)).tasks, [])
        self.assertEqual(dag.nodes["A"].status.value, "PENDING")

    def test_risk_and_unknown_or_exhausted_estimates_block_dispatch(self):
        dag = ExecutionDAG()
        dag.add_node(TaskNode("A", "A", agent_profile="one"))
        dag.add_node(TaskNode("B", "B", agent_profile="two", risk_level="LOW", estimated_tokens=20, estimated_cost_usd=.1))
        dag.add_node(TaskNode("C", "C", agent_profile="three", risk_level="LOW", estimated_tokens=20, estimated_cost_usd=.1))
        scheduler = WaveScheduler()
        wave = scheduler.next_wave(dag, allowed_risks={"LOW"}, remaining_tokens=30, remaining_cost_usd=.15)
        self.assertEqual(wave.task_ids, ["B"])
        self.assertIn("Risk", wave.rejections["A"])
        self.assertIn("budget", wave.rejections["C"])
        self.assertEqual(scheduler.next_wave(dag, remaining_tokens=0).tasks, [])


if __name__ == "__main__":
    unittest.main()
