"""v0.2.0 runtime integration contracts for adaptive Governor strategy."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tooling.agentic.adapters.inference import InferenceResult
from tooling.agentic.context_governor import ContextItem
from tooling.agentic.dag import ExecutionDAG
from tooling.agentic.model_router import InferencePolicy, InferenceRequirements, ModelCandidate
from tooling.agentic.models import (
    ExecutionAttempt,
    ExecutionState,
    IdempotencySemantics,
    Mission,
    MissionOutcome,
    MissionStatus,
    RecoveryState,
    SideEffectRecord,
    SideEffectType,
    TaskNode,
    TaskStatus,
    VerificationState,
)
from tooling.agentic.runtime import JarvisAgenticRuntime


class TestV020GovernorRuntimeIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.runtime = JarvisAgenticRuntime(registry_root=Path(self.tmp.name))
        self.task = TaskNode("tsk-governor-runtime", "Governor runtime fixture")

    def _register(self, model_id, callback, *, local=True, cost=0.0):
        self.runtime.inference_backends.register(
            ModelCandidate(
                model_id,
                f"provider-{model_id}",
                4000,
                cost,
                0.9,
                is_local=local,
            ),
            callback,
        )

    def _run(self, *, items, policy=None, context_tokens=1000, max_cost_usd=0.0):
        return self.runtime.execute_inference(
            self.task,
            mission_id="mis-governor-runtime",
            agent_id="agent-governor-runtime",
            session_id="session-governor-runtime",
            items=items,
            policy=policy or InferencePolicy(),
            requirements=InferenceRequirements(context_tokens=context_tokens),
            verifier=lambda result: bool(result.evidence_refs),
            confidence_threshold=0.8,
            max_attempts=2,
            max_output_tokens=100,
            max_cost_usd=max_cost_usd,
        )

    def test_low_confidence_with_available_omitted_context_expands_before_model_escalation(self):
        calls = []
        self._register(
            "a-weak",
            lambda request: calls.append("a-weak") or InferenceResult("uncertain", 0.2, ("required",)),
        )
        self._register(
            "b-next",
            lambda request: calls.append("b-next") or InferenceResult("should-not-run", 0.95, ("required",)),
        )

        result = self._run(
            context_tokens=350,
            items=[
                ContextItem("required fact", "required", required=True, valid_until=9_999_999_999),
                ContextItem("optional context " * 500, "optional-large"),
            ],
        )

        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["trace"]["reason"], "GOVERNOR_EXPAND_CONTEXT_REQUIRED")
        self.assertEqual(calls, ["a-weak"])
        first = result["trace"]["attempts"][0]
        self.assertEqual(first["governor"]["action"], "EXPAND_CONTEXT")
        self.assertIn("optional-large", result["trace"]["context"]["provenance"]["omitted_sources"])

    def test_exhausted_context_escalates_to_next_eligible_model(self):
        calls = []
        self._register(
            "a-weak",
            lambda request: calls.append("a-weak") or InferenceResult("uncertain", 0.2, ("required",)),
        )
        self._register(
            "b-next",
            lambda request: calls.append("b-next") or InferenceResult("verified", 0.95, ("required",)),
        )

        result = self._run(
            items=[ContextItem("required fact", "required", required=True, valid_until=9_999_999_999)],
        )

        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(calls, ["a-weak", "b-next"])
        self.assertEqual(result["trace"]["attempts"][0]["governor"]["action"], "ESCALATE_CAPABILITY")
        self.assertEqual(result["trace"]["attempts"][1]["governor"]["action"], "CONTINUE")

    def test_policy_exclusion_never_becomes_governor_escalation_bypass(self):
        calls = []
        self._register(
            "a-local",
            lambda request: calls.append("a-local") or InferenceResult("uncertain", 0.2, ("required",)),
        )
        self._register(
            "b-cloud",
            lambda request: calls.append("b-cloud") or InferenceResult("cloud", 0.99, ("required",)),
            local=False,
        )

        result = self._run(
            items=[ContextItem("required fact", "required", required=True, valid_until=9_999_999_999)],
            policy=InferencePolicy(local_only=True, network_allowed=False),
        )

        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["trace"]["reason"], "GOVERNOR_REQUIRE_HUMAN")
        self.assertEqual(calls, ["a-local"])
        self.assertEqual(result["trace"]["routing"]["rejected_candidates"]["b-cloud"], "LOCAL_ONLY")
        self.assertEqual(result["trace"]["attempts"][0]["governor"]["action"], "REQUIRE_HUMAN")

    def test_hard_cost_budget_blocks_before_adapter_invocation(self):
        calls = []
        self._register(
            "expensive",
            lambda request: calls.append("expensive") or InferenceResult("should-not-run", 0.99, ("required",)),
            cost=1.0,
        )

        result = self._run(
            items=[ContextItem("required fact", "required", required=True, valid_until=9_999_999_999)],
            max_cost_usd=0.01,
        )

        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["trace"]["reason"], "NO_ELIGIBLE_BACKEND")
        self.assertEqual(calls, [])
        self.assertIn("headroom", result["trace"]["routing"]["rejected_candidates"]["expensive"].lower())

    def test_unknown_mutable_effect_remains_reconciliation_blocked_before_runtime_replay(self):
        task = TaskNode(
            task_id="tsk-ambiguous-effect",
            title="Ambiguous mutation",
            status=TaskStatus.RUNNING,
        )
        task.record_attempt(
            ExecutionAttempt(
                attempt_id="att-ambiguous-effect",
                mission_id="mis-ambiguous-effect",
                task_id=task.task_id,
                attempt_number=1,
                execution_state=ExecutionState.RUNNING,
                verification_state=VerificationState.UNVERIFIED,
                recovery_state=RecoveryState.NOT_REQUIRED,
                outcome=MissionOutcome.OUTCOME_UNKNOWN,
                side_effects=[
                    SideEffectRecord(
                        side_effect_id="effect-ambiguous",
                        side_effect_type=SideEffectType.LOCAL_WRITE,
                        target="state.txt",
                        observed_change="effect may have occurred",
                        idempotency=IdempotencySemantics.RECONCILIATION_REQUIRED,
                        provenance_hash="a" * 64,
                    )
                ],
            )
        )
        dag = ExecutionDAG()
        dag.add_node(task)
        mission = Mission(
            mission_id="mis-ambiguous-effect",
            goal="ambiguous effect",
            dag=dag,
            status=MissionStatus.RUNNING,
        )

        blocked = self.runtime._recovery_blocked_result(mission)
        self.assertIsNotNone(blocked)
        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertIn("RECONCILIATION_REQUIRED", blocked["blocked_tasks"][0]["reason"])

    def test_governor_metadata_is_structured_and_contains_no_private_reasoning_field(self):
        self._register(
            "a-only",
            lambda request: InferenceResult("verified", 0.95, ("required",)),
        )
        result = self._run(
            items=[ContextItem("required fact", "required", required=True, valid_until=9_999_999_999)],
        )

        governor = result["trace"]["attempts"][0]["governor"]
        self.assertEqual(governor["action"], "CONTINUE")
        self.assertIsInstance(governor["observation"], dict)
        self.assertIn("reason_code", governor)
        self.assertNotIn("chain_of_thought", governor)
        self.assertNotIn("reasoning", governor)
        self.assertNotIn("thoughts", governor)


if __name__ == "__main__":
    unittest.main()
