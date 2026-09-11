"""
test_agentic_goal_loop.py // Unit and Integration Tests for Phase 10 (Autonomous Goal Loop)
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
"""

import json
import unittest
import tempfile
import time
from pathlib import Path

from tooling.agentic.models import TaskNode, TaskStatus
from tooling.agentic.dag import ExecutionDAG
from tooling.agentic.goal_loop import (
    GoalDeclaration,
    GoalSafetyLimits,
    AutonomousGoalLoop
)


class TestGoalLoop(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.missions_dir = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_goal_successful_convergence(self):
        decl = GoalDeclaration(
            goal_id="goal-audit-01",
            objective="Audit repository integrity and produce laudo",
            success_criteria=["audit_completed", "evidence_verified"],
            safety_limits=GoalSafetyLimits(max_iterations=5, runtime_budget_seconds=10.0)
        )
        loop = AutonomousGoalLoop(decl, missions_dir=self.missions_dir)

        step_counter = [0]

        def mock_observe():
            step_counter[0] += 1
            if step_counter[0] == 1:
                return {"met_criteria": ["audit_completed"]}
            else:
                return {"met_criteria": ["audit_completed", "evidence_verified"]}

        def mock_plan(obs):
            dag = ExecutionDAG()
            dag.add_node(TaskNode(task_id="t1", title="Step Task"))
            return dag

        def mock_execute(task):
            return {"exit_code": 0}

        def mock_verify(task, res):
            return True

        # Step 1: satisfies audit_completed
        c1 = loop.step(mock_observe, mock_plan, mock_execute, mock_verify)
        self.assertTrue(c1)
        self.assertEqual(loop.status, "ACTIVE")

        # Step 2: satisfies evidence_verified -> all criteria satisfied -> concludes
        c2 = loop.step(mock_observe, mock_plan, mock_execute, mock_verify)
        self.assertFalse(c2)
        self.assertEqual(loop.status, "SUCCESS")

        # Invariant Section 13: Zero silent adaptations
        self.assertGreaterEqual(len(loop.adaptations_journal), 2)
        for a in loop.adaptations_journal:
            self.assertTrue(a.previous_state)
            self.assertTrue(a.observed_result)
            self.assertTrue(a.decision)
            self.assertTrue(a.change)
            self.assertTrue(a.expected_effect)

    def test_max_iterations_circuit_breaker(self):
        decl = GoalDeclaration(
            goal_id="goal-infinite",
            objective="Unattainable goal",
            success_criteria=["impossible_criterion"],
            safety_limits=GoalSafetyLimits(max_iterations=2)
        )
        loop = AutonomousGoalLoop(decl, missions_dir=self.missions_dir)

        def noop_observe(): return {}
        def noop_plan(obs):
            dag = ExecutionDAG()
            dag.add_node(TaskNode(task_id="t", title="Task"))
            return dag
        def noop_exec(t): return {}
        def noop_verif(t, r): return True

        loop.step(noop_observe, noop_plan, noop_exec, noop_verif)
        loop.step(noop_observe, noop_plan, noop_exec, noop_verif)
        # 3rd step must be blocked
        cont = loop.step(noop_observe, noop_plan, noop_exec, noop_verif)
        self.assertFalse(cont)
        self.assertEqual(loop.status, "MAX_ITERATIONS_EXCEEDED")

    def test_persistence_written(self):
        decl = GoalDeclaration(
            goal_id="goal-persist",
            objective="Check persistence",
            success_criteria=["c1"],
            safety_limits=GoalSafetyLimits(max_iterations=1)
        )
        loop = AutonomousGoalLoop(decl, missions_dir=self.missions_dir)
        loop.step(lambda: {"met_criteria": ["c1"]}, lambda o: ExecutionDAG(), lambda t: {}, lambda t, r: True)

        state_file = self.missions_dir / "goal_goal-persist.json"
        self.assertTrue(state_file.exists())
        data = json.loads(state_file.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "SUCCESS")


if __name__ == "__main__":
    unittest.main()
