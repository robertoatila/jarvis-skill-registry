"""
test_agentic_lifecycle.py // Unit tests for Skill Promotion Lifecycle (Phase 23)
"""

import unittest
import tempfile
from pathlib import Path

from tooling.agentic.lifecycle import (
    SkillLifecycleManager,
    LifecycleState,
    SkillLifecycleRecord
)


class TestSkillLifecycle(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_file = Path(self.temp_dir.name) / "lifecycles.json"
        self.manager = SkillLifecycleManager(state_file=self.state_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_01_canonical_progression(self):
        skill_id = "test-new-skill"
        
        # Start at DISCOVERED
        rec = self.manager.get_skill_state(skill_id)
        # Default is ACTIVE for existing skills, but let's test transition from DISCOVERED
        rec.current_state = LifecycleState.DISCOVERED
        self.manager._save_records()

        # DISCOVERED -> CANDIDATE
        rec = self.manager.transition_skill(skill_id, LifecycleState.CANDIDATE, "Candidate ingest")
        self.assertEqual(rec.current_state, LifecycleState.CANDIDATE)

        # CANDIDATE -> EVALUATED
        rec = self.manager.transition_skill(skill_id, LifecycleState.EVALUATED, "Static AST evaluated")
        self.assertEqual(rec.current_state, LifecycleState.EVALUATED)

        # EVALUATED -> VERIFIED
        rec = self.manager.transition_skill(skill_id, LifecycleState.VERIFIED, "Unit tests verified")
        self.assertEqual(rec.current_state, LifecycleState.VERIFIED)

        # VERIFIED -> ELIGIBLE
        rec = self.manager.transition_skill(skill_id, LifecycleState.ELIGIBLE, "Eligible for staging")
        self.assertEqual(rec.current_state, LifecycleState.ELIGIBLE)

        # ELIGIBLE -> STAGED
        rec = self.manager.transition_skill(skill_id, LifecycleState.STAGED, "Staged in runtime")
        self.assertEqual(rec.current_state, LifecycleState.STAGED)

        # STAGED -> ACTIVE
        rec = self.manager.transition_skill(skill_id, LifecycleState.ACTIVE, "Promoted to canonical active")
        self.assertEqual(rec.current_state, LifecycleState.ACTIVE)
        self.assertTrue(self.manager.is_execution_eligible(skill_id))

    def test_02_illegal_skip_transition_rejected(self):
        skill_id = "test-skip-skill"
        rec = self.manager.get_skill_state(skill_id)
        rec.current_state = LifecycleState.DISCOVERED
        self.manager._save_records()

        # Attempt illegal transition: DISCOVERED -> ACTIVE directly
        with self.assertRaises(ValueError):
            self.manager.transition_skill(skill_id, LifecycleState.ACTIVE, "Illegal skip attempt")

    def test_03_quarantine_precedence_and_fail_closed(self):
        skill_id = "test-active-skill"
        rec = self.manager.get_skill_state(skill_id)
        self.assertEqual(rec.current_state, LifecycleState.ACTIVE)
        self.assertTrue(self.manager.is_execution_eligible(skill_id))

        # Immediate quarantine on security violation
        quarantined = self.manager.quarantine_skill(skill_id, reason="Prohibited extension detected")
        self.assertEqual(quarantined.current_state, LifecycleState.QUARANTINED)
        self.assertFalse(self.manager.is_execution_eligible(skill_id))

        # Verify illegal transition out of quarantine directly to ACTIVE
        with self.assertRaises(ValueError):
            self.manager.transition_skill(skill_id, LifecycleState.ACTIVE, "Cannot skip evaluation")


if __name__ == "__main__":
    unittest.main()
