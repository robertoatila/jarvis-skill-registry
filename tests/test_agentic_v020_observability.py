"""v0.2.0 Plan 3 Task 1 contracts for append-only receipt observability."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tooling.agentic.adapters.inference import InferenceResult
from tooling.agentic.adapters.local import LocalAction, LocalAdapterType
from tooling.agentic.context_governor import ContextItem
from tooling.agentic.dag import ExecutionDAG
from tooling.agentic.model_router import InferencePolicy, InferenceRequirements, ModelCandidate
from tooling.agentic.models import (
    Mission,
    MissionStatus,
    RiskLevel,
    TaskNode,
    TaskStatus,
    VerificationRequirement,
    VerificationType,
)
from tooling.agentic.observability import ReceiptLedger, ReceiptLedgerError
from tooling.agentic.runtime import JarvisAgenticRuntime


CREATED = "2026-09-17T23:40:00+00:00"


def _receipt(
    receipt_id: str,
    *,
    mission_id: str = "mis-ledger",
    task_id: str | None = "tsk-ledger",
    attempt_id: str | None = "att-ledger",
    trace_id: str | None = "trc-ledger",
    **extra,
):
    value = {
        "schema_version": "1.0.0",
        "receipt_id": receipt_id,
        "mission_id": mission_id,
        "task_id": task_id,
        "attempt_id": attempt_id,
        "trace_id": trace_id,
        "created_utc": CREATED,
    }
    value.update(extra)
    return value


class TestReceiptLedger(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.receipts_dir = Path(self.tmp.name) / "state" / "receipts"

    def test_append_order_queries_and_restart_preserve_exact_history(self):
        ledger = ReceiptLedger(self.receipts_dir)
        first = _receipt("rcp-001", decision_type="tool_routing", selected_candidate="local.read_file")
        second = _receipt(
            "rcp-002",
            adapter="local.read_file",
            invocation_occurred=True,
            execution_state="FINISHED",
        )
        third = _receipt(
            "rcp-003",
            execution_receipt_id="rcp-002",
            verification_state="VERIFIED",
            evidence_ids=["ev-001"],
        )

        for receipt in (first, second, third):
            ledger.append(receipt)

        self.assertEqual(
            [item["receipt_id"] for item in ledger.for_mission("mis-ledger")],
            ["rcp-001", "rcp-002", "rcp-003"],
        )
        self.assertEqual(
            [item["receipt_id"] for item in ledger.for_task("mis-ledger", "tsk-ledger")],
            ["rcp-001", "rcp-002", "rcp-003"],
        )
        self.assertEqual(
            [item["receipt_id"] for item in ledger.for_attempt("att-ledger")],
            ["rcp-001", "rcp-002", "rcp-003"],
        )
        self.assertEqual(
            [item["receipt_id"] for item in ledger.for_trace("trc-ledger")],
            ["rcp-001", "rcp-002", "rcp-003"],
        )

        restarted = ReceiptLedger(self.receipts_dir)
        self.assertEqual(restarted.for_mission("mis-ledger"), ledger.for_mission("mis-ledger"))

    def test_malformed_duplicate_and_cross_mission_correlation_fail_closed(self):
        ledger = ReceiptLedger(self.receipts_dir)
        with self.assertRaises(ReceiptLedgerError):
            ledger.append({"mission_id": "mis-ledger"})

        execution = _receipt(
            "rcp-exec-a",
            adapter="local.read_file",
            invocation_occurred=True,
            execution_state="FINISHED",
        )
        ledger.append(execution)

        with self.assertRaises(ReceiptLedgerError):
            ledger.append(dict(execution))

        cross_mission_verification = _receipt(
            "rcp-ver-b",
            mission_id="mis-other",
            execution_receipt_id="rcp-exec-a",
            verification_state="VERIFIED",
            evidence_ids=["ev-001"],
        )
        with self.assertRaises(ReceiptLedgerError):
            ledger.append(cross_mission_verification)

    def test_credentials_are_redacted_without_destroying_resource_token_measurements(self):
        ledger = ReceiptLedger(self.receipts_dir)
        ledger.append(
            _receipt(
                "rcp-secret",
                metadata={
                    "api_key": "sk-test-super-secret",
                    "authorization": "Bearer bearer-super-secret",
                    "nested": {"access_token": "oauth-super-secret"},
                },
                resource_usage={
                    "tokens": {
                        "status": "MEASURED",
                        "value": 41,
                        "unit": "tokens",
                        "method": "provider_reported",
                    }
                },
                note="Authorization: Bearer inline-secret-value",
            )
        )

        raw = ledger.path.read_text(encoding="utf-8")
        for secret in (
            "sk-test-super-secret",
            "bearer-super-secret",
            "oauth-super-secret",
            "inline-secret-value",
        ):
            self.assertNotIn(secret, raw)
        self.assertIn("[REDACTED]", raw)

        stored = ledger.for_mission("mis-ledger")[0]
        self.assertEqual(stored["resource_usage"]["tokens"]["value"], 41)
        self.assertEqual(stored["resource_usage"]["tokens"]["status"], "MEASURED")

    def test_inference_runtime_persists_context_decision_execution_and_verification_receipts(self):
        root = Path(self.tmp.name)
        runtime = JarvisAgenticRuntime(registry_root=root)
        runtime.inference_backends.register(
            ModelCandidate(
                "local-observability-fixture",
                "fixture",
                8000,
                0.0,
                0.95,
                is_local=True,
            ),
            lambda request: InferenceResult(
                "verified",
                0.95,
                ("fixture-source",),
                12,
                5,
            ),
        )
        task = TaskNode("tsk-inference-ledger", "Inference ledger fixture")

        result = runtime.execute_inference(
            task,
            mission_id="mis-inference-ledger",
            agent_id="agent-ledger",
            session_id="session-ledger",
            items=[
                ContextItem(
                    "grounded fact",
                    "fixture-source",
                    required=True,
                    valid_until=9_999_999_999,
                )
            ],
            policy=InferencePolicy(local_only=True, network_allowed=False),
            requirements=InferenceRequirements(context_tokens=1000),
            verifier=lambda candidate: candidate.evidence_refs == ("fixture-source",),
            confidence_threshold=0.8,
            max_attempts=1,
        )

        self.assertEqual(result["status"], "SUCCESS")
        receipts = runtime.receipt_ledger.for_mission("mis-inference-ledger")
        self.assertEqual(len(receipts), 4)
        self.assertTrue(any(item.get("sources_loaded") for item in receipts))
        self.assertTrue(any(item.get("decision_type") == "model_routing" for item in receipts))
        self.assertTrue(any(item.get("invocation_occurred") is True for item in receipts))
        self.assertTrue(any(item.get("verification_state") == "VERIFIED" for item in receipts))

    def test_goal_runtime_persists_actual_local_execution_and_verification_receipts(self):
        root = Path(self.tmp.name)
        (root / "fixture.txt").write_text("observable fixture\n", encoding="utf-8")
        runtime = JarvisAgenticRuntime(registry_root=root)
        task = TaskNode(
            task_id="tsk-goal-ledger",
            title="Read observable fixture",
            agent_profile="Quantum-ExecutorAgent",
            required_skills=["general"],
            action=LocalAction(
                adapter=LocalAdapterType.READ_FILE,
                path="fixture.txt",
            ).to_dict(),
            risk_level=RiskLevel.R0_READ_ONLY,
            read_scopes=["fixture.txt"],
            verification_requirements=[
                VerificationRequirement(
                    check_type=VerificationType.FILE_EXISTS,
                    target="fixture.txt",
                )
            ],
        )
        dag = ExecutionDAG()
        dag.add_node(task)
        mission = Mission(
            mission_id="mis-goal-ledger",
            goal="Read observable fixture",
            dag=dag,
        )

        result = runtime.execute_goal(mission)

        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(task.status, TaskStatus.VERIFIED)
        receipts = runtime.receipt_ledger.for_mission(mission.mission_id)
        self.assertTrue(any(item.get("adapter") == "local.read_file" for item in receipts))
        self.assertTrue(any(item.get("verification_state") == "VERIFIED" for item in receipts))

    def test_ledger_failure_never_changes_authoritative_mission_outcome(self):
        class BrokenLedger:
            def append(self, _receipt):
                raise OSError("simulated observability storage failure")

        root = Path(self.tmp.name)
        (root / "fixture.txt").write_text("authoritative state wins\n", encoding="utf-8")
        runtime = JarvisAgenticRuntime(registry_root=root)
        runtime.receipt_ledger = BrokenLedger()

        task = TaskNode(
            task_id="tsk-ledger-failure",
            title="Read despite observability failure",
            agent_profile="Quantum-ExecutorAgent",
            required_skills=["general"],
            action=LocalAction(
                adapter=LocalAdapterType.READ_FILE,
                path="fixture.txt",
            ).to_dict(),
            risk_level=RiskLevel.R0_READ_ONLY,
            read_scopes=["fixture.txt"],
            verification_requirements=[
                VerificationRequirement(
                    check_type=VerificationType.FILE_EXISTS,
                    target="fixture.txt",
                )
            ],
        )
        dag = ExecutionDAG()
        dag.add_node(task)
        mission = Mission(
            mission_id="mis-ledger-failure",
            goal="Observability must not become execution authority",
            dag=dag,
        )

        result = runtime.execute_goal(mission)
        restored = runtime.load_mission(mission.mission_id)

        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(task.status, TaskStatus.VERIFIED)
        self.assertIsNotNone(restored)
        self.assertEqual(restored.status, MissionStatus.SUCCEEDED)
        self.assertTrue(runtime.observability_errors)


if __name__ == "__main__":
    unittest.main()
