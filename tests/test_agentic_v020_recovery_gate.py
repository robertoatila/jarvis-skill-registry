"""Plan 4 Task 2 contracts for the named restart/recovery gate."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tooling.agentic.adapters.local import LocalActionAdapter
from tooling.run_v020_recovery_gate import (
    DUPLICATE_CONTENT,
    ORIGINAL_CONTENT,
    TARGET,
    run_recovery_gate,
)


class V020RecoveryGateTests(unittest.TestCase):
    def test_canonical_restart_gate_blocks_duplicate_effect_before_reconciliation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(
                LocalActionAdapter,
                "execute",
                side_effect=AssertionError(
                    "ambiguous mutable effect must not be dispatched on restart"
                ),
            ) as execute:
                evidence = run_recovery_gate(root)

            execute.assert_not_called()
            self.assertEqual(evidence["status"], "PASS")
            self.assertEqual(evidence["gate"], "v020-restart-recovery")
            self.assertEqual(evidence["waves_executed"], 0)
            self.assertIn(
                "RECONCILIATION_REQUIRED",
                evidence["blocked_reason"],
            )
            self.assertEqual(evidence["attempt_outcome"], "OUTCOME_UNKNOWN")
            self.assertEqual(
                (root / TARGET).read_text(encoding="utf-8"),
                ORIGINAL_CONTENT,
            )
            self.assertNotEqual(
                (root / TARGET).read_text(encoding="utf-8"),
                DUPLICATE_CONTENT,
            )

    def test_evidence_summary_is_compact_json_compatible_and_hashes_are_stable(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence = run_recovery_gate(Path(directory))

        encoded = json.dumps(evidence, sort_keys=True)

        self.assertEqual(evidence["status"], "PASS")
        self.assertEqual(
            evidence["before_effect_sha256"],
            evidence["after_effect_sha256"],
        )
        self.assertEqual(
            evidence["before_mission_sha256"],
            evidence["after_mission_sha256"],
        )
        self.assertTrue(all(evidence["checks"].values()))
        self.assertIsNone(evidence["runtime_error"])
        self.assertLess(len(encoded), 5000)


if __name__ == "__main__":
    unittest.main()
