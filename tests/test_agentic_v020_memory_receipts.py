"""v0.2.0 memory receipt, provenance, freshness and runtime integration contracts."""

from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path

from tooling.agentic.adapters.inference import InferenceResult
from tooling.agentic.context_governor import ContextItem
from tooling.agentic.memory import MemoryFabric, MemoryItem, MemoryStatus, MemoryTier
from tooling.agentic.model_router import InferencePolicy, InferenceRequirements, ModelCandidate
from tooling.agentic.models import TaskNode
from tooling.agentic.runtime import JarvisAgenticRuntime


class TestV020MemoryReceipts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    @staticmethod
    def _verified_semantic(memory_id: str, key: str, content: str, *, valid_until: float) -> MemoryItem:
        return MemoryItem(
            memory_id=memory_id,
            tier=MemoryTier.SEMANTIC,
            key=key,
            content=content,
            provenance=f"evidence:{memory_id}",
            confidence=0.95,
            metadata={
                "verification_state": "VERIFIED",
                "evidence_refs": [f"evidence:{memory_id}"],
                "valid_until": valid_until,
                "admission_reason": "verified_fixture",
            },
        )

    def test_retrieval_receipt_records_considered_selected_and_rejected_reasons(self):
        memory = MemoryFabric(storage_dir=self.root / "memory")
        now = time.time()
        selected = self._verified_semantic(
            "mem-selected",
            "router-contract",
            "router contract requires explicit evidence",
            valid_until=now + 3600,
        )
        stale = self._verified_semantic(
            "mem-stale",
            "router-contract-stale",
            "router contract stale observation",
            valid_until=now - 1,
        )
        irrelevant = self._verified_semantic(
            "mem-irrelevant",
            "database-note",
            "database migration note",
            valid_until=now + 3600,
        )
        low_confidence = MemoryItem(
            memory_id="mem-low",
            tier=MemoryTier.EPISODIC,
            key="router-contract-low",
            content="router contract low confidence observation",
            provenance="attempt:low",
            confidence=0.2,
            status=MemoryStatus.UNVERIFIED,
            metadata={"verification_state": "UNVERIFIED"},
        )

        self.assertTrue(memory.admit(selected).admitted)
        self.assertTrue(memory.admit(stale, allow_stale=True).admitted)
        self.assertTrue(memory.admit(irrelevant).admitted)
        self.assertTrue(memory.admit(low_confidence).admitted)

        items, receipt = memory.query(
            "router contract",
            min_confidence=0.5,
            token_budget=1000,
            mission_id="mis-memory",
            task_id="tsk-memory",
            attempt_id="att-memory",
            trace_id="trc-memory",
        )

        self.assertEqual([item.memory_id for item in items], ["mem-selected"])
        self.assertEqual(
            set(receipt.considered_item_ids),
            {"mem-selected", "mem-stale", "mem-irrelevant", "mem-low"},
        )
        self.assertEqual(receipt.selected_item_ids, ["mem-selected"])
        self.assertEqual(receipt.rejected_items["mem-stale"]["reason_code"], "STALE_MEMORY")
        self.assertEqual(receipt.rejected_items["mem-low"]["reason_code"], "LOW_CONFIDENCE")
        self.assertEqual(receipt.rejected_items["mem-irrelevant"]["reason_code"], "NO_QUERY_MATCH")
        self.assertEqual(receipt.mission_id, "mis-memory")
        self.assertEqual(receipt.task_id, "tsk-memory")
        self.assertEqual(receipt.attempt_id, "att-memory")
        self.assertEqual(receipt.trace_id, "trc-memory")

        serialized = receipt.to_dict()
        self.assertEqual(serialized["selected_item_ids"], ["mem-selected"])
        self.assertEqual(serialized["rejected_items"]["mem-stale"]["reason_code"], "STALE_MEMORY")

    def test_unverified_model_observation_can_be_episodic_but_not_semantic(self):
        memory = MemoryFabric(storage_dir=self.root / "memory")
        episode = MemoryItem(
            memory_id="mem-episode",
            tier=MemoryTier.EPISODIC,
            key="observation",
            content="provider returned an unverified observation",
            provenance="model:test-model",
            confidence=0.7,
            status=MemoryStatus.UNVERIFIED,
            metadata={
                "verification_state": "UNVERIFIED",
                "evidence_refs": [],
                "admission_reason": "retain_observation_only",
            },
        )
        semantic = MemoryItem(
            memory_id="mem-semantic-unverified",
            tier=MemoryTier.SEMANTIC,
            key="observation",
            content="provider returned an unverified observation",
            provenance="model:test-model",
            confidence=0.7,
            status=MemoryStatus.UNVERIFIED,
            metadata={
                "verification_state": "UNVERIFIED",
                "evidence_refs": [],
                "admission_reason": "invalid_promotion_attempt",
            },
        )

        self.assertTrue(memory.admit(episode).admitted)
        rejected = memory.admit(semantic)
        self.assertFalse(rejected.admitted)
        self.assertIn("UNVERIFIED", rejected.reason)

    def test_model_derived_semantic_memory_requires_verified_evidence_refs(self):
        memory = MemoryFabric(storage_dir=self.root / "memory")
        missing_evidence = MemoryItem(
            memory_id="mem-no-evidence",
            tier=MemoryTier.SEMANTIC,
            key="verified-claim",
            content="claim says verified but cites no evidence",
            provenance="model:test-model",
            confidence=0.99,
            metadata={
                "verification_state": "VERIFIED",
                "evidence_refs": [],
                "admission_reason": "promotion",
                "valid_until": time.time() + 3600,
            },
        )

        result = memory.admit(missing_evidence)
        self.assertFalse(result.admitted)
        self.assertIn("EVIDENCE", result.reason)

    def test_verified_semantic_snapshot_preserves_provenance_and_evidence_refs(self):
        memory = MemoryFabric(storage_dir=self.root / "memory")
        item = MemoryItem(
            memory_id="mem-promoted",
            tier=MemoryTier.SEMANTIC,
            key="verified-fact",
            content="verified fact",
            provenance="model:test-model",
            confidence=0.99,
            metadata={
                "verification_state": "VERIFIED",
                "evidence_refs": ["evidence:one", "evidence:two"],
                "admission_reason": "verified_promotion",
                "valid_until": time.time() + 3600,
            },
        )
        self.assertTrue(memory.admit(item).admitted)
        memory.save_snapshot()

        reloaded = MemoryFabric(storage_dir=self.root / "memory")
        self.assertTrue(reloaded.load_snapshot())
        restored = reloaded._semantic["verified-fact"]
        self.assertEqual(restored.provenance, "model:test-model")
        self.assertEqual(restored.metadata["evidence_refs"], ["evidence:one", "evidence:two"])
        self.assertEqual(restored.metadata["verification_state"], "VERIFIED")
        self.assertEqual(restored.metadata["admission_reason"], "verified_promotion")

    def test_runtime_emits_memory_receipt_and_persists_verified_inference_evidence(self):
        runtime = JarvisAgenticRuntime(registry_root=self.root)
        task = TaskNode("tsk-memory-runtime", "Memory runtime fixture")
        runtime.inference_backends.register(
            ModelCandidate(
                "memory-model",
                "provider-memory",
                4000,
                0.0,
                0.95,
                is_local=True,
            ),
            lambda request: InferenceResult(
                "Memory runtime fixture verified fact",
                0.95,
                ("evidence:runtime",),
            ),
        )
        policy = InferencePolicy()
        requirements = InferenceRequirements(context_tokens=1200)
        items = [
            ContextItem(
                "authoritative runtime evidence",
                "source:runtime",
                required=True,
                valid_until=time.time() + 3600,
            )
        ]

        first = runtime.execute_inference(
            task,
            mission_id="mis-memory-runtime",
            agent_id="agent-memory-runtime",
            session_id="session-memory-runtime",
            items=items,
            policy=policy,
            requirements=requirements,
            verifier=lambda result: result.evidence_refs == ("evidence:runtime",),
            confidence_threshold=0.8,
            max_attempts=1,
            max_output_tokens=128,
            max_cost_usd=0.0,
            remember=True,
        )
        self.assertEqual(first["status"], "SUCCESS")
        self.assertEqual(first["trace"]["memory_writes"], 1)

        snapshots = list((self.root / "state" / "inference_memory").glob("*/memory_snapshot.json"))
        self.assertEqual(len(snapshots), 1)
        snapshot = json.loads(snapshots[0].read_text(encoding="utf-8"))
        self.assertEqual(len(snapshot["semantic"]), 1)
        saved = snapshot["semantic"][0]
        self.assertEqual(saved["metadata"]["verification_state"], "VERIFIED")
        self.assertEqual(saved["metadata"]["evidence_refs"], ["evidence:runtime"])
        self.assertEqual(saved["metadata"]["admission_reason"], "verified_inference_result")

        second = runtime.execute_inference(
            task,
            mission_id="mis-memory-runtime",
            agent_id="agent-memory-runtime",
            session_id="session-memory-runtime",
            items=items,
            policy=policy,
            requirements=requirements,
            verifier=lambda result: result.evidence_refs == ("evidence:runtime",),
            confidence_threshold=0.8,
            max_attempts=1,
            max_output_tokens=128,
            max_cost_usd=0.0,
            retrieve_memory=True,
        )
        self.assertEqual(second["status"], "SUCCESS")
        self.assertEqual(len(second["trace"]["memory_receipts"]), 1)
        memory_receipt = second["trace"]["memory_receipts"][0]
        self.assertEqual(memory_receipt["mission_id"], "mis-memory-runtime")
        self.assertEqual(memory_receipt["task_id"], "tsk-memory-runtime")
        self.assertEqual(len(memory_receipt["selected_item_ids"]), 1)
        self.assertEqual(memory_receipt["selected_item_ids"], [saved["memory_id"]])
        self.assertNotIn("chain_of_thought", memory_receipt)
        self.assertNotIn("reasoning", memory_receipt)


if __name__ == "__main__":
    unittest.main()
