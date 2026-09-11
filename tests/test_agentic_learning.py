"""
test_agentic_learning.py // Unit and Integration Tests for Phase 12 (Learning Records)
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
"""

import unittest
import tempfile
from pathlib import Path

from tooling.agentic.learning import (
    LearningEngine,
    LearningRecord,
    LearningTier
)


class TestLearningRecords(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.ledger_file = Path(self.tmp_dir.name) / "test_learning.jsonl"
        self.heuristics_file = Path(self.tmp_dir.name) / "test_heuristics.json"
        self.engine = LearningEngine(
            ledger_file=self.ledger_file,
            heuristics_file=self.heuristics_file
        )

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_record_observation_lifecycle(self):
        rec = self.engine.record_observation(
            skill="fastapi-pro",
            agent_profile="Quantum-SynthesisAgent",
            approach="Async connection pooling with SQLAlchemy 2.0",
            expected_result="Latency under 50ms",
            actual_result="Latency observed: 32ms",
            evidence={"latency_ms": 32, "verified": True},
            provenance="QMIS-1001:task-01:sha256"
        )

        self.assertEqual(rec.tier, LearningTier.OBSERVATION)
        self.assertEqual(rec.confidence, 0.50)
        self.assertEqual(rec.observation_count, 1)
        self.assertTrue(self.ledger_file.exists())

    def test_single_execution_cannot_promote_to_heuristic(self):
        """Invariant: Section 14 - A single execution NEVER promotes automatically to global rule."""
        rec = self.engine.record_observation(
            skill="single-run-skill",
            agent_profile="Quantum-AuditAgent",
            approach="Test approach",
            expected_result="Ok",
            actual_result="Ok",
            evidence={"ok": True},
            provenance="QMIS-1002"
        )

        # Trying to promote with zero extra observations must fail
        promoted, reason = self.engine.promote_candidate(rec, new_observations_count=0, corroborating_evidence=[])
        self.assertFalse(promoted)
        self.assertIn("requires >= 3 observations", reason)
        self.assertEqual(rec.tier, LearningTier.OBSERVATION)

    def test_promotion_lifecycle_to_validated_heuristic(self):
        rec = self.engine.record_observation(
            skill="comprehensive-code-review",
            agent_profile="Quantum-AuditAgent",
            approach="AST AST-based static threat inspection",
            expected_result="Detect unhandled CVEs and placeholders",
            actual_result="100% detection rate in benchmarks",
            evidence={"pass_rate": 1.0},
            provenance="QMIS-1003"
        )

        # 1. Promote to PATTERN with 2 additional observations (total 3)
        promoted_pattern, _ = self.engine.promote_candidate(rec, new_observations_count=2, corroborating_evidence=[])
        self.assertTrue(promoted_pattern)
        self.assertEqual(rec.tier, LearningTier.PATTERN)
        self.assertEqual(rec.observation_count, 3)

        # 2. Promote to VALIDATED_HEURISTIC with 2 more observations (total 5) + 2 evidence sets
        promoted_heuristic, _ = self.engine.promote_candidate(
            rec,
            new_observations_count=2,
            corroborating_evidence=[{"env": "win"}, {"env": "linux"}]
        )
        self.assertTrue(promoted_heuristic)
        self.assertEqual(rec.tier, LearningTier.VALIDATED_HEURISTIC)
        self.assertGreaterEqual(rec.confidence, 0.90)

        # Check that it is saved in heuristics cache
        heuristics = self.engine.get_validated_heuristics()
        self.assertIn(rec.record_id, heuristics)


if __name__ == "__main__":
    unittest.main()
