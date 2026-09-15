"""v0.2.0 end-to-end contracts for receipts emitted by real adapter execution."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tooling.agentic.adapters.inference import InferenceResult
from tooling.agentic.adapters.local import LocalAction, LocalAdapterType
from tooling.agentic.context_governor import ContextItem
from tooling.agentic.dag import ExecutionDAG
from tooling.agentic.model_router import ModelCandidate, InferencePolicy, InferenceRequirements
from tooling.agentic.models import (
    Mission,
    RiskLevel,
    TaskNode,
    TaskStatus,
    VerificationRequirement,
    VerificationType,
)
from tooling.agentic.runtime import JarvisAgenticRuntime


class TestV020RuntimeReceiptIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.runtime = JarvisAgenticRuntime(registry_root=self.root)

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def _mission(mission_id: str, task: TaskNode) -> Mission:
        dag = ExecutionDAG()
        dag.add_node(task)
        return Mission(mission_id=mission_id, goal=mission_id, dag=dag)

    def test_local_write_actual_invocation_emits_correlated_execution_and_verification_receipts(self):
        action = LocalAction(
            adapter=LocalAdapterType.WRITE_TEXT,
            path="receipt-output.txt",
            content="verified receipt evidence",
        )
        task = TaskNode(
            task_id="tsk-local-receipt",
            title="Write deterministic evidence",
            agent_profile="Quantum-ExecutorAgent",
            required_skills=["general"],
            action=action.to_dict(),
            risk_level=RiskLevel.R1_LOCAL_WRITE,
            write_scopes=["receipt-output.txt"],
            verification_requirements=[
                VerificationRequirement(
                    check_type=VerificationType.FILE_EXISTS,
                    target="receipt-output.txt",
                )
            ],
        )
        mission = self._mission("mis-local-receipt", task)

        result = self.runtime.execute_goal(mission)

        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual((self.root / "receipt-output.txt").read_text(encoding="utf-8"), "verified receipt evidence")
        self.assertEqual(task.status, TaskStatus.VERIFIED)
        self.assertEqual(len(task.attempts), 1)

        execution_receipts = mission.metadata.get("execution_receipts", [])
        verification_receipts = mission.metadata.get("verification_receipts", [])
        self.assertEqual(len(execution_receipts), 1)
        self.assertEqual(len(verification_receipts), 1)

        attempt = task.attempts[0]
        execution = execution_receipts[0]
        verification = verification_receipts[0]
        self.assertTrue(execution["invocation_occurred"])
        self.assertEqual(execution["adapter"], "local.write_text")
        self.assertTrue(execution["metadata"]["adapter_invocation_id"].startswith("inv-"))
        self.assertEqual(execution["attempt_id"], attempt.attempt_id)
        self.assertEqual(execution["trace_id"], attempt.trace_id)
        self.assertEqual(verification["attempt_id"], attempt.attempt_id)
        self.assertEqual(verification["trace_id"], attempt.trace_id)
        self.assertEqual(verification["execution_receipt_id"], execution["receipt_id"])
        self.assertEqual(verification["verification_state"], "VERIFIED")
        self.assertEqual(execution["resource_usage"]["tokens"]["status"], "NOT_APPLICABLE")
        self.assertEqual(execution["resource_usage"]["cost_usd"]["status"], "NOT_APPLICABLE")

    def test_missing_executor_never_creates_positive_adapter_receipt(self):
        task = TaskNode(
            task_id="tsk-no-executor-receipt",
            title="No executor",
            agent_profile="Quantum-ExecutorAgent",
            required_skills=["general-execution"],
        )
        mission = self._mission("mis-no-executor-receipt", task)

        result = self.runtime.execute_goal(mission)

        self.assertEqual(result["status"], "FAILED")
        self.assertFalse(task.execution_result["executed"])
        self.assertEqual(mission.metadata.get("execution_receipts", []), [])
        self.assertEqual(mission.metadata.get("verification_receipts", []), [])

    def _register_inference_backend(self, callback) -> None:
        self.runtime.inference_backends.register(
            ModelCandidate("local-fixture", "fixture", 8000, 0, 0.9, is_local=True),
            callback,
        )

    def _run_inference(self, task: TaskNode, verifier):
        return self.runtime.execute_inference(
            task,
            mission_id="mis-inference-receipt",
            agent_id="agent-fixture",
            session_id="session-fixture",
            items=[ContextItem("grounded fact", "fixture-source", required=True, valid_until=9999999999)],
            policy=InferencePolicy(),
            requirements=InferenceRequirements(context_tokens=1000),
            verifier=verifier,
            confidence_threshold=0.8,
            max_attempts=1,
        )

    def test_provider_transport_success_remains_unverified_when_independent_verifier_rejects(self):
        calls = []

        def backend(request):
            calls.append(request.task_id)
            return InferenceResult("candidate answer", 0.95, ("fixture-source",), 20, 4)

        self._register_inference_backend(backend)
        task = TaskNode("tsk-inference-rejected", "Inference receipt rejection")

        result = self._run_inference(task, verifier=lambda _: False)

        self.assertEqual(calls, [task.task_id])
        self.assertEqual(result["status"], "BLOCKED")
        attempt_trace = result["trace"]["attempts"][0]
        execution = attempt_trace["execution_receipt"]
        verification = attempt_trace["verification_receipt"]
        self.assertTrue(execution["invocation_occurred"])
        self.assertTrue(execution["metadata"]["adapter_invocation_id"].startswith("inv-"))
        self.assertNotEqual(verification["verification_state"], "VERIFIED")
        self.assertEqual(verification["execution_receipt_id"], execution["receipt_id"])
        self.assertEqual(execution["attempt_id"], verification["attempt_id"])
        self.assertEqual(execution["trace_id"], verification["trace_id"])
        self.assertNotEqual(task.attempts[-1].verification_state.value, "VERIFIED")

    def test_inference_receipt_preserves_measured_tokens_and_unknown_cost(self):
        self._register_inference_backend(
            lambda request: InferenceResult("verified", 0.95, ("fixture-source",), 20, 4)
        )
        task = TaskNode("tsk-inference-usage", "Inference usage receipt")

        result = self._run_inference(task, verifier=lambda result: result.evidence_refs == ("fixture-source",))

        self.assertEqual(result["status"], "SUCCESS")
        execution = result["trace"]["attempts"][0]["execution_receipt"]
        verification = result["trace"]["attempts"][0]["verification_receipt"]
        self.assertEqual(execution["resource_usage"]["tokens"]["status"], "MEASURED")
        self.assertEqual(execution["resource_usage"]["tokens"]["value"], 24.0)
        self.assertEqual(execution["resource_usage"]["cost_usd"]["status"], "UNKNOWN")
        self.assertIsNone(execution["resource_usage"]["cost_usd"]["value"])
        self.assertEqual(verification["verification_state"], "VERIFIED")


if __name__ == "__main__":
    unittest.main()
