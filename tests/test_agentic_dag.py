"""
test_agentic_dag.py // Unit and Integration Tests for Phase 01 (Mission Model + Execution DAG)
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
"""

import os
import json
import unittest
import tempfile
import itertools
import subprocess
import sys
from unittest.mock import patch
from pathlib import Path

from tooling.agentic.models import (
    TaskNode,
    TaskStatus,
    VerificationStatus,
    VerificationType,
    VerificationRequirement,
    Mission,
    MissionStatus,
    MissionBudget
)
from tooling.agentic.dag import ExecutionDAG, CycleDetectedError


class TestExecutionDAG(unittest.TestCase):

    def test_node_creation_and_serialization(self):
        vreq = VerificationRequirement(
            check_type=VerificationType.FILE_EXISTS,
            target="reports/summary.json",
            expected=True
        )
        node = TaskNode(
            task_id="task-01",
            title="Initial Audit",
            description="Performs security audit on code",
            agent_profile="Quantum-AuditAgent",
            required_skills=["security-research-audit"],
            read_scopes=["src/"],
            write_scopes=["reports/"],
            verification_requirements=[vreq]
        )
        data = node.to_dict()
        self.assertEqual(data["task_id"], "task-01")
        self.assertEqual(data["agent_profile"], "Quantum-AuditAgent")
        self.assertEqual(data["status"], "PENDING")
        self.assertEqual(len(data["verification_requirements"]), 1)

        # Deserialization
        reconstructed = TaskNode.from_dict(data)
        self.assertEqual(reconstructed.task_id, node.task_id)
        self.assertEqual(reconstructed.verification_requirements[0].check_type, VerificationType.FILE_EXISTS)

    def test_linear_dag_topological_sort(self):
        dag = ExecutionDAG()
        n1 = TaskNode(task_id="step-1", title="Step 1")
        n2 = TaskNode(task_id="step-2", title="Step 2")
        n3 = TaskNode(task_id="step-3", title="Step 3")
        dag.add_node(n1)
        dag.add_node(n2)
        dag.add_node(n3)

        dag.add_dependency("step-1", "step-2")
        dag.add_dependency("step-2", "step-3")

        order = dag.topological_sort()
        self.assertEqual(order, ["step-1", "step-2", "step-3"])

    def test_diamond_dag_determinism(self):
        dag = ExecutionDAG()
        for name in ["D", "B", "C", "A"]:  # Deliberately inserted out of order
            dag.add_node(TaskNode(task_id=name, title=f"Task {name}"))

        dag.add_dependency("A", "B")
        dag.add_dependency("A", "C")
        dag.add_dependency("B", "D")
        dag.add_dependency("C", "D")

        order = dag.topological_sort()
        # Alphabetical tie-breaking guarantees A -> B -> C -> D
        self.assertEqual(order, ["A", "B", "C", "D"])

    def test_cycle_detection(self):
        dag = ExecutionDAG()
        dag.add_node(TaskNode(task_id="A", title="A"))
        dag.add_node(TaskNode(task_id="B", title="B"))
        dag.add_node(TaskNode(task_id="C", title="C"))

        dag.add_dependency("A", "B")
        dag.add_dependency("B", "C")

        with self.assertRaises(CycleDetectedError) as ctx:
            dag.add_dependency("C", "A")

        self.assertIn("A", ctx.exception.cycle_path)
        self.assertIn("B", ctx.exception.cycle_path)
        self.assertIn("C", ctx.exception.cycle_path)

    def test_self_cycle_detection(self):
        dag = ExecutionDAG()
        dag.add_node(TaskNode(task_id="SelfNode", title="Self Node"))
        with self.assertRaises(CycleDetectedError):
            dag.add_dependency("SelfNode", "SelfNode")

    def test_verification_gating_invariant(self):
        """
        Critical Invariant:
        TASK EXECUTION COMPLETED != TASK VERIFIED
        A dependent task must NEVER become READY while prerequisites are only EXECUTED.
        Prerequisites must be explicitly VERIFIED.
        """
        dag = ExecutionDAG()
        task_a = TaskNode(
            task_id="task_A",
            title="Generate Artifact",
            verification_requirements=[
                VerificationRequirement(check_type=VerificationType.FILE_EXISTS, target="out.json")
            ]
        )
        task_b = TaskNode(
            task_id="task_B",
            title="Consume Artifact",
            dependencies=["task_A"]
        )

        dag.add_node(task_a)
        dag.add_node(task_b)

        # 1. Initial State: Only A is ready
        ready = dag.get_ready_tasks()
        self.assertEqual([t.task_id for t in ready], ["task_A"])

        # 2. Task A executes but is NOT yet verified
        dag.mark_task_status("task_A", TaskStatus.EXECUTED)
        ready_after_exec = dag.get_ready_tasks()
        # Task B must NOT be ready!
        self.assertEqual(ready_after_exec, [], "Dependent task must not be ready when prerequisite is merely EXECUTED")

        # 3. Task A is formally verified
        with self.assertRaises(ValueError):
            dag.mark_task_status("task_A", TaskStatus.VERIFIED)
        task_a.verification_requirements[0].status = VerificationStatus.VERIFIED
        dag.mark_task_status("task_A", TaskStatus.VERIFIED)
        ready_after_verif = dag.get_ready_tasks()
        self.assertEqual([t.task_id for t in ready_after_verif], ["task_B"])

    def test_dag_persistence_roundtrip(self):
        dag = ExecutionDAG()
        dag.add_node(TaskNode(task_id="t1", title="Task 1", read_scopes=["a.txt"]))
        dag.add_node(TaskNode(task_id="t2", title="Task 2", write_scopes=["b.txt"]))
        dag.add_dependency("t1", "t2")

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "test_dag.json"
            dag.save(save_path)

            loaded_dag = ExecutionDAG.load(save_path)
            self.assertEqual(len(loaded_dag.nodes), 2)
            self.assertEqual(loaded_dag.topological_sort(), ["t1", "t2"])
            self.assertEqual(loaded_dag.nodes["t1"].read_scopes, ["a.txt"])
            self.assertEqual(loaded_dag.nodes["t2"].write_scopes, ["b.txt"])

    def test_mission_container_serialization(self):
        dag = ExecutionDAG()
        dag.add_node(TaskNode(task_id="m_t1", title="Mission Task 1"))
        mission = Mission(
            mission_id="MIS-20260910-001",
            goal="Test Autonomous Mission Workflow",
            budget=MissionBudget(max_iterations=10, max_token_budget=50_000)
        )
        data = mission.to_dict()
        data["dag"] = dag.to_dict()

        self.assertEqual(data["mission_id"], "MIS-20260910-001")
        self.assertEqual(data["budget"]["max_iterations"], 10)
        self.assertEqual(len(data["dag"]["nodes"]), 1)

    def test_forward_dependencies_resolve_for_every_insertion_order(self):
        serialized = []
        for order in itertools.permutations("ABC"):
            dag = ExecutionDAG()
            for name in order:
                dag.add_node(TaskNode(name, name, dependencies={"A": [], "B": ["A"], "C": ["B"]}[name]))
            self.assertEqual(dag.topological_sort(), ["A", "B", "C"])
            self.assertEqual([n.task_id for n in dag.get_ready_tasks()], ["A"])
            serialized.append(json.dumps(dag.to_dict(), sort_keys=True))
        self.assertEqual(len(set(serialized)), 1)

    def test_cycle_rejection_does_not_mutate_graph(self):
        dag = ExecutionDAG()
        dag.add_node(TaskNode("A", "A"))
        dag.add_node(TaskNode("B", "B", dependencies=["A"]))
        before = dag.to_dict()
        with self.assertRaises(CycleDetectedError):
            dag.add_dependency("B", "A")
        self.assertEqual(dag.to_dict(), before)
        self.assertEqual(dag.topological_sort(), ["A", "B"])

    def test_forward_cycle_node_rejection_is_atomic(self):
        dag = ExecutionDAG()
        dag.add_node(TaskNode("A", "A", dependencies=["B"]))
        with self.assertRaises(CycleDetectedError):
            dag.add_node(TaskNode("B", "B", dependencies=["A"]))
        self.assertNotIn("B", dag.nodes)
        dag.add_node(TaskNode("B", "B"))
        self.assertEqual(dag.topological_sort(), ["B", "A"])

    def test_missing_prerequisite_fails_before_execution_or_save(self):
        dag = ExecutionDAG()
        dag.add_node(TaskNode("B", "B", dependencies=["missing"]))
        for operation in (dag.get_ready_tasks, dag.topological_sort, dag.to_dict):
            with self.assertRaises(ValueError):
                operation()

    def test_skipped_prerequisite_does_not_release_required_task(self):
        dag = ExecutionDAG()
        dag.add_node(TaskNode("A", "A", status=TaskStatus.SKIPPED))
        dag.add_node(TaskNode("B", "B", dependencies=["A"]))
        self.assertEqual(dag.get_ready_tasks(), [])
        self.assertFalse(dag.is_complete())

    def test_restore_rejects_unknown_states_versions_and_invalid_bounds(self):
        invalid = [
            {"status": "TYPO"}, {"schema_version": "99.0"}, {"dependencies": "A"},
            {"retry_count": -1}, {"max_retries": True}, {"timeout_seconds": float("nan")},
            {"timeout_seconds": 0}, {"verification_requirements": ["bad"]},
            {"verification_requirements": [{"check_type": "unknown"}]},
            {"verification_requirements": [{"check_type": "file_exists", "status": "TYPO"}]},
        ]
        for fields in invalid:
            with self.subTest(fields=fields), self.assertRaises((ValueError, TypeError)):
                TaskNode.from_dict({"task_id": "A", "title": "A", **fields})
        with self.assertRaises(ValueError):
            Mission.from_dict({"mission_id": "M", "goal": "G", "status": "TYPO"})
        with self.assertRaises(ValueError):
            MissionBudget(max_iterations=0)

    def test_restore_rejects_missing_edges_and_false_verified_state(self):
        for data in (
            {"nodes": [], "edges": [{"from": "missing", "to": "also-missing"}]},
            {"nodes": [{"task_id": "A", "dependencies": ["missing"]}]},
            {"nodes": [{"task_id": "A", "status": "VERIFIED", "verification_requirements": [{"check_type": "file_exists"}]}]},
            {"nodes": [{"task_id": "A"}, {"task_id": "A"}]},
            {"schema_version": "2", "nodes": []},
        ):
            with self.subTest(data=data), self.assertRaises((ValueError, KeyError)):
                ExecutionDAG.from_dict(data)

    def test_atomic_save_failure_preserves_last_valid_snapshot(self):
        dag = ExecutionDAG()
        dag.add_node(TaskNode("A", "A"))
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "dag.json"
            dag.save(target)
            old = target.read_bytes()
            dag.add_node(TaskNode("B", "B"))
            with patch("tooling.agentic.dag.os.replace", side_effect=OSError("injected storage failure")):
                with self.assertRaises(OSError):
                    dag.save(target)
            self.assertEqual(target.read_bytes(), old)
            self.assertEqual(list(Path(td).glob("*.tmp")), [])

    def test_mission_roundtrip_preserves_dag_budget_and_evidence_after_restart(self):
        dag = ExecutionDAG()
        dag.add_node(TaskNode("A", "A", status=TaskStatus.EXECUTED, retry_count=1,
                              execution_result={"exit_code": 0}, artifacts=["out.json"]))
        mission = Mission("msn-restart", "Recover", budget=MissionBudget(max_iterations=7),
                          evidence_ledger=[{"producer": "task-A"}], dag=dag)
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "mission.json"
            target.write_text(json.dumps(mission.to_dict()), encoding="utf-8")
            code = "import json,sys;from tooling.agentic.models import Mission;print(json.dumps(Mission.from_dict(json.load(open(sys.argv[1],encoding='utf-8'))).to_dict(),sort_keys=True))"
            result = subprocess.run([sys.executable, "-B", "-c", code, str(target)],
                                    cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), mission.to_dict())

    def test_versionless_legacy_snapshot_remains_readable(self):
        old = {"nodes": [{"task_id": "A", "title": "A"}, {"task_id": "B", "title": "B"}],
               "edges": [{"from": "A", "to": "B"}]}
        dag = ExecutionDAG.from_dict(old)
        self.assertEqual(dag.topological_sort(), ["A", "B"])
        self.assertEqual(dag.to_dict()["schema_version"], "1.0.0")


if __name__ == "__main__":
    unittest.main()
