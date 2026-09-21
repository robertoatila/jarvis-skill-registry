"""Fail-closed regression tests for unknown side-effect classification."""

import unittest

from tooling.agentic.models import (
    ExecutionAttempt,
    IdempotencySemantics,
    SideEffectRecord,
    SideEffectType,
    TaskNode,
)
from tooling.agentic.resilience import CheckpointManager, ReplayEngine


class TestUnknownSideEffectFailClosed(unittest.TestCase):
    def test_missing_side_effect_type_remains_unknown(self):
        record = SideEffectRecord(side_effect_id="se-missing")
        self.assertEqual(record.side_effect_type, SideEffectType.UNKNOWN)
        self.assertEqual(record.idempotency, IdempotencySemantics.UNSAFE_TO_RETRY)

        restored = SideEffectRecord.from_dict({
            "side_effect_id": "se-legacy",
            "idempotency": "IDEMPOTENT",
        })
        self.assertEqual(restored.side_effect_type, SideEffectType.UNKNOWN)
        self.assertEqual(restored.idempotency, IdempotencySemantics.IDEMPOTENT)

    def test_explicit_pure_effect_remains_pure(self):
        record = SideEffectRecord(
            side_effect_id="se-pure",
            side_effect_type=SideEffectType.PURE,
            idempotency=IdempotencySemantics.IDEMPOTENT,
        )
        self.assertEqual(record.side_effect_type, SideEffectType.PURE)

    def test_unknown_effect_blocks_replay_even_when_marked_idempotent(self):
        effect = SideEffectRecord(
            side_effect_id="se-unknown",
            side_effect_type=SideEffectType.UNKNOWN,
            idempotency=IdempotencySemantics.IDEMPOTENT,
        )
        attempt = ExecutionAttempt(
            attempt_id="att-unknown",
            mission_id="mis-unknown",
            task_id="tsk-unknown",
            side_effects=[effect],
        )
        task = TaskNode(
            task_id="tsk-unknown",
            title="Unknown effect replay",
            attempts=[attempt],
            max_retries=3,
        )

        allowed, reason = ReplayEngine().can_replay_task(task)
        self.assertFalse(allowed)
        self.assertIn("UNKNOWN side-effect classification", reason)

    def test_unknown_effect_cannot_be_auto_compensated(self):
        unknown = SideEffectRecord(
            side_effect_id="se-unknown-comp",
            provenance_hash="abc123",
            compensation_action="undo",
        )
        known = SideEffectRecord(
            side_effect_id="se-known-comp",
            side_effect_type=SideEffectType.LOCAL_WRITE,
            provenance_hash="abc123",
            compensation_action="undo",
        )

        self.assertFalse(CheckpointManager.can_automatically_compensate(unknown))
        self.assertTrue(CheckpointManager.can_automatically_compensate(known))

    def test_legacy_dict_without_effect_type_cannot_be_auto_compensated(self):
        legacy = {
            "side_effect_id": "se-legacy-dict",
            "provenance_hash": "abc123",
            "compensation_action": "undo",
        }
        self.assertFalse(CheckpointManager.can_automatically_compensate(legacy))


if __name__ == "__main__":
    unittest.main()
