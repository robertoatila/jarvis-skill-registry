"""
test_agentic_planner.py // Unit tests for Planner + 14-step Resolver Integration
"""

import unittest
from tooling.agentic.planner_resolver import (
    AutonomousSkillResolver,
    AutonomousMissionPlanner,
    SkillResolutionExplanation
)
from tooling.agentic.models import Mission, TaskStatus, VerificationType
from tooling.agentic.dag import ExecutionDAG


class TestPlannerResolver(unittest.TestCase):

    def setUp(self):
        self.resolver = AutonomousSkillResolver()
        self.planner = AutonomousMissionPlanner(resolver=self.resolver)

    def test_01_skill_resolver_14_step_funnel(self):
        explanation = self.resolver.resolve(
            capability_request="systematic-code-debugging",
            target_platform="windows"
        )
        self.assertIsInstance(explanation, SkillResolutionExplanation)
        self.assertTrue(explanation.resolution_id.startswith("res-"))
        self.assertIsNotNone(explanation.selected_candidate)
        self.assertIn("systematic-code-debugging", explanation.selected_candidate)
        self.assertIn("OPTIMAL_FITNESS_SCORE", explanation.selection_reason)
        
        # Verify explanation structure
        exp_dict = explanation.to_dict()
        self.assertIn("explanation", exp_dict)
        self.assertIn("candidates", exp_dict["explanation"])
        self.assertIn("scores", exp_dict["explanation"])
        self.assertIn("tie_break_rules", exp_dict["explanation"])

    def test_02_skill_resolver_cold_start_prior_invariant(self):
        # A completely unknown synthetic capability
        explanation = self.resolver.resolve(capability_request="quantum-flux-capacitor")
        # Ensure score is never 0
        cand = explanation.selected_candidate
        self.assertIsNotNone(cand)
        score = explanation.scores.get(cand, 0.0)
        self.assertGreater(score, 0.0, "Cold start score must NEVER be 0.0 (Protocol Section 10)")
        self.assertEqual(score, 0.75, "Cold start score must default to neutral prior 0.75")

    def test_03_skill_resolver_lockfile_pinning(self):
        # If a skill is explicitly pinned by registry lock
        explanation = self.resolver.resolve(
            capability_request="python-pro",
            lock_pinned_skill="fastapi-pro"
        )
        self.assertEqual(explanation.selected_candidate, "fastapi-pro")
        self.assertIn("PINNED_BY_REGISTRY_LOCK", explanation.selection_reason)

    def test_04_mission_planner_e2e_dag(self):
        mission = self.planner.plan_mission(
            goal_title="Refactor Core Service",
            goal_description="Automate AST refactoring and verification",
            required_capabilities=["systematic-code-debugging", "comprehensive-code-review"]
        )
        self.assertIsInstance(mission, Mission)
        self.assertTrue(mission.mission_id.startswith("msn-"))
        self.assertIsInstance(mission.dag, ExecutionDAG)
        
        # Verify DAG structure
        nodes = list(mission.dag.nodes.values())
        self.assertEqual(len(nodes), 2)
        
        # Check task 1
        t1 = nodes[0]
        self.assertTrue(t1.task_id.startswith("task-01"))
        self.assertTrue(len(t1.required_skills) > 0)
        self.assertTrue(len(t1.verification_requirements) > 0)
        self.assertEqual(t1.verification_requirements[0].check_type, VerificationType.COMMAND_EXIT_ZERO)
        
        # Check topological ordering
        ordered = mission.dag.topological_sort()
        self.assertEqual(len(ordered), 2)
        self.assertEqual(ordered[0], nodes[0].task_id)
        self.assertEqual(ordered[1], nodes[1].task_id)


if __name__ == "__main__":
    unittest.main()
