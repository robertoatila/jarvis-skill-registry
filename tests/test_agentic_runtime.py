"""
test_agentic_runtime.py // Unit tests for Runtime End-to-End Orchestration (Phase 20)
"""

import unittest
import tempfile
from pathlib import Path

from tooling.agentic.runtime import JarvisAgenticRuntime
from tooling.agentic.models import TaskStatus, MissionStatus


class TestJarvisAgenticRuntime(unittest.TestCase):

    def setUp(self):
        self.runtime = JarvisAgenticRuntime()

    def test_01_end_to_end_goal_execution_9_stages(self):
        result = self.runtime.execute_goal(
            goal_prompt="Run Diagnostic Health Verification",
            required_capabilities=["systematic-code-debugging", "comprehensive-code-review"],
            target_platform="windows"
        )

        self.assertEqual(result["status"], "SUCCESS")
        self.assertTrue(result["execution_id"].startswith("exec-"))
        self.assertTrue(result["mission_id"].startswith("msn-"))

        # Verify all 9 mandatory lifecycle stages
        expected_stages = [
            "OBSERVE",
            "PLAN",
            "RESOLVE",
            "DELEGATE",
            "EXECUTE",
            "VERIFY",
            "MEASURE",
            "LEARN",
            "ADAPT"
        ]
        self.assertEqual(result["lifecycle_stages"], expected_stages)

        # Verify execution and verification metrics
        self.assertGreaterEqual(result["waves_executed"], 1)
        self.assertEqual(result["total_tasks"], 2)
        self.assertEqual(result["tasks_verified"], 2)
        self.assertEqual(result["telemetry_spans_recorded"], 2)
        self.assertGreater(result["evidence_count"], 0)

        # Verify observation state
        obs = result["observation_state"]
        self.assertGreater(obs["catalog_skills_observed"], 0)
        self.assertGreaterEqual(obs["federation_nodes_online"], 1)

    def test_02_failure_triggers_non_silent_adaptation(self):
        # Pass a task that deliberately fails verification
        result = self.runtime.execute_goal(
            goal_prompt="Run Failing Test",
            required_capabilities=["ast-grep-search"]
        )
        # Verify result contains adaptation structure and records
        self.assertIn("adaptation_count", result)
        self.assertIn("lifecycle_stages", result)
        self.assertIn("ADAPT", result["lifecycle_stages"])


if __name__ == "__main__":
    unittest.main()
