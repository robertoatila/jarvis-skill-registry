"""v0.2.0 contracts for correlated, uncertainty-preserving runtime receipts."""

from __future__ import annotations

import importlib
import json
import unittest

from tooling.agentic.context_governor import ContextReceipt
from tooling.agentic.decision_receipt import DecisionReceipt, DecisionType
from tooling.agentic.memory import MemoryReceipt
from tooling.agentic.resource_usage import ResourceMeasurement


CREATED = "2026-09-15T12:00:00+00:00"


class TestV020Receipts(unittest.TestCase):
    def _execution_module(self):
        try:
            return importlib.import_module("tooling.agentic.execution_receipt")
        except ModuleNotFoundError as exc:
            self.fail(f"execution receipt module is missing: {exc}")

    def _verification_receipt(self):
        try:
            module = importlib.import_module("tooling.agentic.verification")
            return module.VerificationReceipt
        except (ModuleNotFoundError, AttributeError) as exc:
            self.fail(f"verification receipt contract is missing: {exc}")

    def test_existing_receipts_expose_common_correlation_envelope(self):
        decision = DecisionReceipt(
            decision_id="dec-001",
            decision_type=DecisionType.TOOL_ROUTING,
            receipt_id="rcpt-decision-001",
            mission_id="mis-001",
            task_id="tsk-001",
            attempt_id="att-001",
            trace_id="trace-001",
            created_utc=CREATED,
        )
        context = ContextReceipt(
            receipt_id="rcpt-context-001",
            mission_id="mis-001",
            task_id="tsk-001",
            attempt_id="att-001",
            trace_id="trace-001",
            created_utc=CREATED,
        )
        memory = MemoryReceipt(
            receipt_id="rcpt-memory-001",
            query="runtime receipts",
            tier_filter=[],
            matched_items=[],
            excluded_conflicts=[],
            decay_scores={},
            total_tokens_estimated=0,
            mission_id="mis-001",
            task_id="tsk-001",
            attempt_id="att-001",
            trace_id="trace-001",
            created_utc=CREATED,
        )

        for receipt in (decision, context, memory):
            with self.subTest(receipt=type(receipt).__name__):
                encoded = receipt.to_dict()
                self.assertEqual(encoded["receipt_id"], receipt.receipt_id)
                self.assertTrue(encoded["schema_version"])
                self.assertEqual(encoded["mission_id"], "mis-001")
                self.assertEqual(encoded["task_id"], "tsk-001")
                self.assertEqual(encoded["attempt_id"], "att-001")
                self.assertEqual(encoded["trace_id"], "trace-001")
                self.assertEqual(encoded["created_utc"], CREATED)

    def test_execution_and_verification_receipts_have_distinct_ids_and_shared_correlation(self):
        execution = self._execution_module()
        VerificationReceipt = self._verification_receipt()

        execution_receipt = execution.ExecutionReceipt(
            receipt_id="exec-001",
            mission_id="mis-001",
            task_id="tsk-001",
            attempt_id="att-001",
            trace_id="trace-001",
            created_utc=CREATED,
            adapter="local",
            invocation_occurred=True,
            execution_state="FINISHED",
            resource_usage={},
        )
        verification_receipt = VerificationReceipt(
            receipt_id="verify-001",
            mission_id="mis-001",
            task_id="tsk-001",
            attempt_id="att-001",
            trace_id="trace-001",
            created_utc=CREATED,
            execution_receipt_id=execution_receipt.receipt_id,
            verification_state="VERIFIED",
            evidence_ids=["ev-001"],
        )

        self.assertNotEqual(execution_receipt.receipt_id, verification_receipt.receipt_id)
        for name in ("mission_id", "task_id", "attempt_id", "trace_id"):
            self.assertEqual(getattr(execution_receipt, name), getattr(verification_receipt, name))
        self.assertEqual(verification_receipt.execution_receipt_id, execution_receipt.receipt_id)

    def test_verification_cannot_claim_verified_execution_without_execution_receipt(self):
        VerificationReceipt = self._verification_receipt()
        with self.assertRaises(ValueError):
            VerificationReceipt(
                receipt_id="verify-orphan",
                mission_id="mis-001",
                task_id="tsk-001",
                attempt_id="att-001",
                trace_id="trace-001",
                created_utc=CREATED,
                execution_receipt_id=None,
                verification_state="VERIFIED",
                evidence_ids=["ev-001"],
            )

    def test_resource_usage_preserves_measurement_status(self):
        execution = self._execution_module()
        receipt = execution.ExecutionReceipt(
            receipt_id="exec-resources",
            mission_id="mis-001",
            task_id="tsk-001",
            attempt_id="att-001",
            trace_id="trace-001",
            created_utc=CREATED,
            adapter="inference",
            invocation_occurred=True,
            execution_state="FINISHED",
            resource_usage={
                "tokens": ResourceMeasurement.measured(42, "tokens", "provider_usage"),
                "cost_usd": ResourceMeasurement.unknown("USD"),
            },
        )
        encoded = receipt.to_dict()
        self.assertEqual(encoded["resource_usage"]["tokens"]["status"], "MEASURED")
        self.assertEqual(encoded["resource_usage"]["tokens"]["value"], 42)
        self.assertEqual(encoded["resource_usage"]["cost_usd"]["status"], "UNKNOWN")
        self.assertIsNone(encoded["resource_usage"]["cost_usd"]["value"])

    def test_receipt_serialization_is_deterministic(self):
        execution = self._execution_module()
        receipt = execution.ExecutionReceipt(
            receipt_id="exec-deterministic",
            mission_id="mis-001",
            task_id="tsk-001",
            attempt_id="att-001",
            trace_id="trace-001",
            created_utc=CREATED,
            adapter="local",
            invocation_occurred=True,
            execution_state="FINISHED",
            resource_usage={
                "cost_usd": ResourceMeasurement.unknown("USD"),
                "tokens": ResourceMeasurement.measured(5, "tokens", "fixture"),
            },
            metadata={"z": 1, "a": 2},
        )
        first = json.dumps(receipt.to_dict(), sort_keys=True, separators=(",", ":"))
        second = json.dumps(receipt.to_dict(), sort_keys=True, separators=(",", ":"))
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
