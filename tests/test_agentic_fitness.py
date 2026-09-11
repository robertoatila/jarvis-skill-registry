"""
test_agentic_fitness.py // Unit and Integration Tests for Phase 08 (Skill Fitness)
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
"""

import unittest
import tempfile
from pathlib import Path

from tooling.agentic.telemetry import TelemetryCollector, TokenUsage
from tooling.agentic.fitness import SkillFitnessEngine, COLD_START_PRIOR


class TestSkillFitness(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.ledger_file = Path(self.tmp_dir.name) / "test_spans.jsonl"
        self.state_file = Path(self.tmp_dir.name) / "test_fitness.json"
        self.collector = TelemetryCollector(ledger_file=self.ledger_file)
        self.engine = SkillFitnessEngine(telemetry_collector=self.collector, state_file=self.state_file)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_cold_start_prior_never_zero(self):
        """Invariant: Section 10 - unknown is NEVER converted to 0."""
        report = self.engine.evaluate_skill("unobserved-new-skill")
        self.assertTrue(report.is_cold_start)
        self.assertEqual(report.sample_count, 0)
        self.assertEqual(report.fitness_score, COLD_START_PRIOR)
        self.assertGreater(report.fitness_score, 0.0)
        self.assertEqual(report.recommendation, "EVALUATING")

    def test_observed_successful_skill(self):
        # Record 5 successful spans
        for i in range(5):
            s = self.collector.start_span("M1", f"t_{i}", "Agent1", skill_id="fastapi-pro")
            self.collector.finish_span(
                s.span_id,
                status="SUCCESS",
                token_usage=TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
            )

        report = self.engine.evaluate_skill("fastapi-pro")
        self.assertFalse(report.is_cold_start)
        self.assertEqual(report.sample_count, 5)
        self.assertEqual(report.dimension_scores["success_rate"], 1.0)
        self.assertGreaterEqual(report.fitness_score, 0.85)
        self.assertEqual(report.recommendation, "HIGHLY_RECOMMENDED")

    def test_degraded_skill(self):
        # Record 4 failures and 1 success
        for i in range(4):
            s = self.collector.start_span("M1", f"fail_{i}", "Agent1", skill_id="failing-skill")
            self.collector.finish_span(s.span_id, status="FAIL", error_message="Crash")

        s = self.collector.start_span("M1", "succ_0", "Agent1", skill_id="failing-skill")
        self.collector.finish_span(s.span_id, status="SUCCESS")

        report = self.engine.evaluate_skill("failing-skill")
        self.assertFalse(report.is_cold_start)
        self.assertEqual(report.sample_count, 5)
        self.assertLess(report.dimension_scores["success_rate"], 0.3)
        self.assertIn(report.recommendation, ["EVALUATING", "DEGRADED"])

    def test_deterministic_ranking(self):
        # 3 skills: one great, two unobserved
        s = self.collector.start_span("M1", "t1", "Agent1", skill_id="skill-star")
        self.collector.finish_span(s.span_id, status="SUCCESS")

        candidates = ["skill-zebra", "skill-star", "skill-alpha"]
        ranked = self.engine.rank_skills(candidates)

        self.assertEqual(len(ranked), 3)
        # skill-star is #1 because it has empirical success
        self.assertEqual(ranked[0].skill_id, "skill-star")
        # skill-alpha and skill-zebra both have cold start prior (0.75), tie broken alphabetically
        self.assertEqual(ranked[1].skill_id, "skill-alpha")
        self.assertEqual(ranked[2].skill_id, "skill-zebra")

    def test_fitness_cache_persistence(self):
        report = self.engine.evaluate_skill("fastapi-pro")
        self.engine.save_cache([report])
        self.assertTrue(self.state_file.exists())


if __name__ == "__main__":
    unittest.main()
