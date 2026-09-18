"""Plan 4 Task 1 contracts for deterministic provider evidence."""

from __future__ import annotations

import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.fixtures.v020.deterministic_provider import (
    DeterministicProvider,
    ProviderCase,
)
from tooling.agentic.context_governor import ContextItem
from tooling.agentic.model_router import (
    InferencePolicy,
    InferenceRequirements,
    ModelCandidate,
)
from tooling.agentic.models import TaskNode
from tooling.agentic.runtime import JarvisAgenticRuntime


class DeterministicProviderEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.runtime = JarvisAgenticRuntime(registry_root=self.root)

    def _register(self, model_id: str, provider: DeterministicProvider, *, capability=0.95):
        self.runtime.inference_backends.register(
            ModelCandidate(
                model_id=model_id,
                provider="deterministic-fixture",
                context_window_tokens=8192,
                cost_per_1k_tokens_usd=0.0,
                capability_rating=capability,
                is_local=True,
                tier=0,
            ),
            provider,
        )

    def _run(
        self,
        *,
        verifier=lambda result: bool(result.evidence_refs),
        max_attempts=2,
        max_output_tokens=128,
    ):
        task = TaskNode(
            task_id="tsk-provider-fixture",
            title="Deterministic provider fixture",
        )
        return self.runtime.execute_inference(
            task,
            mission_id="mis-provider-fixture",
            agent_id="agent-provider-fixture",
            session_id="session-provider-fixture",
            items=[
                ContextItem(
                    "grounded deterministic fixture fact",
                    "fixture-source",
                    required=True,
                    valid_until=9999999999,
                )
            ],
            policy=InferencePolicy(),
            requirements=InferenceRequirements(
                min_capability=0.8,
                context_tokens=1000,
            ),
            verifier=verifier,
            confidence_threshold=0.8,
            max_attempts=max_attempts,
            max_output_tokens=max_output_tokens,
        )

    def test_success_invokes_fixture_without_network_and_does_not_self_verify(self):
        provider = DeterministicProvider(
            ProviderCase.SUCCESS,
            prompt_tokens=7,
            completion_tokens=2,
        )
        self._register("a-success", provider)

        with patch.object(
            socket,
            "create_connection",
            side_effect=AssertionError("network must not be used"),
        ):
            result = self._run(verifier=lambda _: False, max_attempts=1)

        self.assertEqual(provider.invocation_count, 1)
        invocation = provider.invocations[0]
        self.assertEqual(invocation.mission_id, "mis-provider-fixture")
        self.assertEqual(invocation.task_id, "tsk-provider-fixture")

        self.assertEqual(result["status"], "BLOCKED")
        attempt = result["trace"]["attempts"][0]
        self.assertTrue(attempt["execution_receipt"]["invocation_occurred"])
        self.assertEqual(
            attempt["verification_receipt"]["verification_state"],
            "REJECTED",
        )
        self.assertFalse(
            attempt["verification_receipt"]["metadata"]["independent_verifier_passed"]
        )

    def test_provider_usage_is_measured_only_when_provider_reports_it(self):
        reported = DeterministicProvider(
            ProviderCase.SUCCESS,
            prompt_tokens=10,
            completion_tokens=5,
        )
        self._register("a-reported", reported)

        measured = self._run(max_attempts=1)
        receipt = measured["trace"]["attempts"][0]["execution_receipt"]

        self.assertEqual(measured["status"], "SUCCESS")
        self.assertEqual(
            receipt["resource_usage"]["tokens"],
            {
                "value": 15,
                "unit": "tokens",
                "status": "MEASURED",
                "method": "provider_reported",
            },
        )
        self.assertEqual(
            receipt["resource_usage"]["cost_usd"]["status"],
            "UNKNOWN",
        )
        self.assertIsNone(receipt["resource_usage"]["cost_usd"]["value"])

        second_runtime = JarvisAgenticRuntime(
            registry_root=self.root / "unknown-usage"
        )
        unreported = DeterministicProvider(ProviderCase.SUCCESS)
        second_runtime.inference_backends.register(
            ModelCandidate(
                model_id="a-unreported",
                provider="deterministic-fixture",
                context_window_tokens=8192,
                cost_per_1k_tokens_usd=0.0,
                capability_rating=0.95,
                is_local=True,
            ),
            unreported,
        )
        task = TaskNode("tsk-unreported", "Unreported provider usage")
        unknown = second_runtime.execute_inference(
            task,
            mission_id="mis-unreported",
            agent_id="agent-unreported",
            session_id="session-unreported",
            items=[
                ContextItem(
                    "fixture",
                    "fixture-source",
                    required=True,
                    valid_until=9999999999,
                )
            ],
            policy=InferencePolicy(),
            requirements=InferenceRequirements(context_tokens=1000),
            verifier=lambda result: bool(result.evidence_refs),
            confidence_threshold=0.8,
            max_attempts=1,
            max_output_tokens=128,
        )
        unknown_receipt = unknown["trace"]["attempts"][0]["execution_receipt"]

        self.assertEqual(
            unknown_receipt["resource_usage"]["tokens"]["status"],
            "UNKNOWN",
        )
        self.assertIsNone(
            unknown_receipt["resource_usage"]["tokens"]["value"],
        )

    def test_cost_is_unknown_unless_provider_explicitly_reports_measured_cost(self):
        provider = DeterministicProvider(
            ProviderCase.SUCCESS,
            prompt_tokens=4,
            completion_tokens=2,
            cost_usd=0.0042,
        )
        self._register("a-cost", provider)

        result = self._run(max_attempts=1)
        cost = result["trace"]["attempts"][0]["execution_receipt"][
            "resource_usage"
        ]["cost_usd"]

        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(
            cost,
            {
                "value": 0.0042,
                "unit": "USD",
                "status": "MEASURED",
                "method": "provider_reported",
            },
        )

    def test_policy_failure_is_terminal_and_never_invokes_fallback(self):
        policy_failure = DeterministicProvider(ProviderCase.POLICY)
        fallback = DeterministicProvider(
            ProviderCase.SUCCESS,
            prompt_tokens=1,
            completion_tokens=1,
        )
        self._register("a-policy", policy_failure)
        self._register("b-fallback", fallback)

        result = self._run(max_attempts=2)

        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["trace"]["reason"], "POLICY")
        self.assertEqual(policy_failure.invocation_count, 1)
        self.assertEqual(fallback.invocation_count, 0)
        self.assertEqual(
            result["trace"]["attempts"][0]["failure_class"],
            "POLICY",
        )

    def test_transient_failure_falls_back_but_remains_bounded_by_max_attempts(self):
        transient = DeterministicProvider(ProviderCase.TRANSIENT)
        success = DeterministicProvider(
            ProviderCase.SUCCESS,
            prompt_tokens=2,
            completion_tokens=1,
        )
        must_not_run = DeterministicProvider(
            ProviderCase.SUCCESS,
            prompt_tokens=99,
            completion_tokens=99,
        )
        self._register("a-transient", transient)
        self._register("b-success", success)
        self._register("c-out-of-bound", must_not_run)

        result = self._run(max_attempts=2)

        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(transient.invocation_count, 1)
        self.assertEqual(success.invocation_count, 1)
        self.assertEqual(must_not_run.invocation_count, 0)
        self.assertEqual(len(result["trace"]["attempts"]), 2)
        self.assertEqual(
            result["trace"]["attempts"][0]["failure_class"],
            "TRANSIENT",
        )

    def test_low_confidence_never_becomes_verified_success(self):
        provider = DeterministicProvider(
            ProviderCase.LOW_CONFIDENCE,
            prompt_tokens=3,
            completion_tokens=1,
            confidence=0.2,
        )
        self._register("a-low-confidence", provider)

        result = self._run(
            verifier=lambda result: True,
            max_attempts=1,
        )

        self.assertEqual(provider.invocation_count, 1)
        self.assertEqual(result["status"], "BLOCKED")
        attempt = result["trace"]["attempts"][0]
        self.assertLess(attempt["confidence"], 0.8)
        self.assertNotEqual(
            attempt["verification_receipt"]["verification_state"],
            "VERIFIED",
        )

    def test_malformed_and_oversized_results_fail_closed(self):
        for case in (ProviderCase.MALFORMED, ProviderCase.OVERSIZED):
            with self.subTest(case=case.value):
                runtime = JarvisAgenticRuntime(
                    registry_root=self.root / case.value.lower()
                )
                provider = DeterministicProvider(case)
                runtime.inference_backends.register(
                    ModelCandidate(
                        model_id=f"a-{case.value.lower()}",
                        provider="deterministic-fixture",
                        context_window_tokens=8192,
                        cost_per_1k_tokens_usd=0.0,
                        capability_rating=0.95,
                        is_local=True,
                    ),
                    provider,
                )
                task = TaskNode(
                    f"tsk-{case.value.lower()}",
                    f"{case.value} fixture",
                )
                result = runtime.execute_inference(
                    task,
                    mission_id=f"mis-{case.value.lower()}",
                    agent_id="agent-fixture",
                    session_id="session-fixture",
                    items=[
                        ContextItem(
                            "fixture",
                            "fixture-source",
                            required=True,
                            valid_until=9999999999,
                        )
                    ],
                    policy=InferencePolicy(),
                    requirements=InferenceRequirements(context_tokens=1000),
                    verifier=lambda _: True,
                    confidence_threshold=0.8,
                    max_attempts=1,
                    max_output_tokens=64,
                )

                self.assertEqual(provider.invocation_count, 1)
                self.assertEqual(result["status"], "BLOCKED")
                self.assertEqual(
                    result["trace"]["reason"],
                    "ELIGIBLE_ATTEMPTS_EXHAUSTED",
                )
                self.assertEqual(
                    result["trace"]["attempts"][0]["failure_class"],
                    "MALFORMED_RESULT",
                )


if __name__ == "__main__":
    unittest.main()
