"""v0.2.0 fail-closed memory admission, restoration, retrieval and receipt contracts."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tooling.agentic.memory import (
    MemoryFabric,
    MemoryItem,
    MemoryStatus,
    MemoryTier,
)


class TestV020MemoryContracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.fabric = MemoryFabric(storage_dir=self.root)

    @staticmethod
    def _durable(
        *,
        tier: MemoryTier = MemoryTier.SEMANTIC,
        provenance: str = "operator:fixture",
        metadata: dict | None = None,
    ) -> MemoryItem:
        return MemoryItem(
            memory_id=f"mem-{tier.value.lower()}",
            tier=tier,
            key=f"key-{tier.value.lower()}",
            content="Verified durable fact",
            provenance=provenance,
            confidence=0.95,
            metadata=metadata or {},
        )

    def test_unknown_tier_and_status_are_rejected_not_defaulted(self):
        base = {
            "memory_id": "mem-invalid",
            "tier": "SEMANTIC",
            "key": "invalid",
            "content": "payload",
            "provenance": "operator:fixture",
            "status": "ACTIVE",
        }
        with self.assertRaises(ValueError):
            MemoryItem.from_dict(base | {"tier": "MYSTERY"})
        with self.assertRaises(ValueError):
            MemoryItem.from_dict(base | {"status": "MYSTERY"})

    def test_durable_memory_rejects_blank_or_unknown_provenance(self):
        for tier in (MemoryTier.SEMANTIC, MemoryTier.PROCEDURAL):
            for provenance in ("", "   ", "unknown", "UNKNOWN"):
                with self.subTest(tier=tier, provenance=provenance):
                    result = self.fabric.admit(
                        self._durable(tier=tier, provenance=provenance)
                    )
                    self.assertFalse(result.admitted)
                    self.assertIn("PROVENANCE", result.reason.upper())

    def test_stale_durable_fact_requires_explicit_stale_policy(self):
        expired = (datetime.now(timezone.utc) - timedelta(minutes=1)).timestamp()
        item = self._durable(metadata={"valid_until": expired})

        denied = self.fabric.admit(item)
        self.assertFalse(denied.admitted)
        self.assertIn("STALE", denied.reason.upper())

        explicitly_allowed = self.fabric.admit(item, allow_stale=True)
        self.assertTrue(explicitly_allowed.admitted)

    def test_unverified_model_output_cannot_become_durable_memory(self):
        for tier in (MemoryTier.SEMANTIC, MemoryTier.PROCEDURAL):
            unverified = self._durable(
                tier=tier,
                provenance="model:fixture",
                metadata={"verification_state": "UNVERIFIED"},
            )
            with self.subTest(tier=tier):
                result = self.fabric.admit(unverified)
                self.assertFalse(result.admitted)
                self.assertIn("UNVERIFIED", result.reason.upper())

            verified = self._durable(
                tier=tier,
                provenance="model:fixture",
                metadata={"verification_state": "VERIFIED"},
            )
            with self.subTest(tier=tier, verified=True):
                result = self.fabric.admit(verified)
                self.assertTrue(result.admitted)

    def test_working_and_episodic_can_hold_explicit_unverified_observations(self):
        self.assertTrue(hasattr(MemoryStatus, "UNVERIFIED"))
        for tier in (MemoryTier.WORKING, MemoryTier.EPISODIC):
            item = MemoryItem(
                memory_id=f"obs-{tier.value.lower()}",
                tier=tier,
                key=f"obs-{tier.value.lower()}",
                content="Model observation awaiting verification",
                provenance="model-observation:fixture",
                status=MemoryStatus.UNVERIFIED,
                metadata={"verification_state": "UNVERIFIED"},
            )
            with self.subTest(tier=tier):
                result = self.fabric.admit(item)
                self.assertTrue(result.admitted)
                self.assertEqual(item.status, MemoryStatus.UNVERIFIED)

    def test_query_receipt_carries_correlation_and_estimation_method(self):
        item = self._durable(metadata={"verification_state": "VERIFIED"})
        self.assertTrue(self.fabric.admit(item).admitted)

        results, receipt = self.fabric.query(
            "durable fact",
            mission_id="mis-memory",
            task_id="tsk-memory",
            attempt_id="att-memory",
            trace_id="trace-memory",
        )

        self.assertEqual([result.memory_id for result in results], [item.memory_id])
        self.assertEqual(receipt.mission_id, "mis-memory")
        self.assertEqual(receipt.task_id, "tsk-memory")
        self.assertEqual(receipt.attempt_id, "att-memory")
        self.assertEqual(receipt.trace_id, "trace-memory")
        self.assertGreater(receipt.total_tokens_estimated, 0)
        self.assertEqual(
            receipt.token_estimation_method,
            "utf8_bytes_div4_estimate_v1",
        )
        encoded = receipt.to_dict()
        self.assertEqual(encoded["token_estimation_method"], receipt.token_estimation_method)

    def test_snapshot_with_unknown_durable_contract_fails_without_partial_restore(self):
        snapshot = {
            "working": [
                {
                    "memory_id": "work-valid",
                    "tier": "WORKING",
                    "key": "work-valid",
                    "content": "scratch",
                    "provenance": "task:fixture",
                    "status": "ACTIVE",
                }
            ],
            "semantic": [
                {
                    "memory_id": "sem-invalid",
                    "tier": "UNKNOWN_TIER",
                    "key": "sem-invalid",
                    "content": "must not be coerced",
                    "provenance": "operator:fixture",
                    "status": "ACTIVE",
                }
            ],
            "episodic": [],
            "procedural": [],
        }
        (self.root / "memory_snapshot.json").write_text(
            json.dumps(snapshot), encoding="utf-8"
        )

        self.assertFalse(self.fabric.load_snapshot())
        self.assertEqual(self.fabric.get_tier_counts()["total"], 0)


if __name__ == "__main__":
    unittest.main()
