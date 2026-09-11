"""
test_agentic_experiments.py // Unit and Integration Tests for Phase 09 (Skill Experiment Engine)
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
"""

import unittest
import tempfile
from pathlib import Path

from tooling.agentic.experiments import (
    SkillExperiment,
    ExperimentVariant,
    ExperimentEngine
)


class TestSkillExperiments(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.state_file = Path(self.tmp_dir.name) / "test_exp.json"
        self.engine = ExperimentEngine(state_file=self.state_file)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_deterministic_variant_assignment(self):
        """Invariant: Section 8 - Deterministic assignment across identical contexts."""
        exp = self.engine.create_experiment(
            experiment_id="exp-ast-check",
            capability="code-review",
            variants_tuples=[
                ("var-A", "comprehensive-code-review", 1.0),
                ("var-B", "security-research-audit", 1.0)
            ],
            min_samples=5
        )

        # Exact same context must yield exact same variant
        v1 = exp.assign_variant("mission-alpha-task-01")
        v2 = exp.assign_variant("mission-alpha-task-01")
        self.assertEqual(v1.variant_id, v2.variant_id)

    def test_sample_threshold_and_conclusion(self):
        """Invariant: Section 14 - A single execution never promotes automatically."""
        exp = self.engine.create_experiment(
            experiment_id="exp-speed",
            capability="data-plotting",
            variants_tuples=[
                ("A", "academic-scientific-plotting", 1.0),
                ("B", "deckgl-geospatial-visualization", 1.0)
            ],
            min_samples=3
        )

        # 2 runs for A, 2 runs for B (below min_samples 3)
        exp.record_result("A", success=True, duration_ms=100)
        exp.record_result("A", success=True, duration_ms=110)
        exp.record_result("B", success=False, duration_ms=200)
        exp.record_result("B", success=True, duration_ms=190)

        self.assertEqual(exp.status, "ACTIVE")
        self.assertIsNone(exp.winner_variant_id)

        # 3rd run for both
        exp.record_result("A", success=True, duration_ms=105)
        exp.record_result("B", success=False, duration_ms=210)

        # Both reached 3 samples, A had 100% success vs B 33.3%
        self.assertEqual(exp.status, "CONCLUDED")
        self.assertEqual(exp.winner_variant_id, "A")
        self.assertIsNotNone(exp.concluded_utc)

    def test_persistence_roundtrip(self):
        exp = self.engine.create_experiment(
            experiment_id="exp-persist",
            capability="persistence-check",
            variants_tuples=[("v1", "s1", 1.0)],
            min_samples=2
        )
        self.engine.save()

        # New engine instance loading from same file
        engine2 = ExperimentEngine(state_file=self.state_file)
        loaded = engine2.get_experiment("exp-persist")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.capability, "persistence-check")


if __name__ == "__main__":
    unittest.main()
