#!/usr/bin/env python3
"""Portable deterministic transport evidence for the inference boundary."""

from __future__ import annotations

import json
import unittest

from fixtures.deterministic_inference_transport import DeterministicHttpTransport
from tooling.agentic.adapters.http_inference import HttpInferenceAdapter
from tooling.agentic.adapters.inference import InferenceFailure, InferenceRequest
from tooling.agentic.model_router import InferencePolicy
from tooling.agentic.models import FailureClass


class DeterministicInferenceTransportTests(unittest.TestCase):
    @staticmethod
    def request(*, allowed_models=("openai:fixture-model",), local_only=False, network_allowed=True):
        return InferenceRequest(
            mission_id="mission-fixture",
            task_id="task-fixture",
            agent_id="agent-fixture",
            session_id="session-fixture",
            context="bounded fixture context",
            policy=InferencePolicy(
                local_only=local_only,
                network_allowed=network_allowed,
                allowed_models=allowed_models,
            ),
            max_output_tokens=64,
        )

    def test_success_proves_real_adapter_attempt_without_implying_verification(self):
        transport = DeterministicHttpTransport.json_response(
            {
                "choices": [{"message": {"content": "deterministic reply"}}],
                "usage": {"prompt_tokens": 7, "completion_tokens": 2},
            }
        )

        with transport.install():
            result = HttpInferenceAdapter(
                "openai",
                "fixture-model",
                "fixture-credential",
            )(self.request())

        self.assertEqual(transport.attempt_count, 1)
        attempt = transport.attempts[0]
        self.assertEqual(attempt.method, "POST")
        self.assertEqual(attempt.timeout, 20.0)
        self.assertEqual(json.loads(attempt.body)["model"], "fixture-model")
        self.assertEqual(result.text, "deterministic reply")
        self.assertEqual((result.prompt_tokens, result.completion_tokens), (7, 2))

        # Transport success is not independent verification/evidence.
        self.assertIsNone(result.confidence)
        self.assertEqual(result.evidence_refs, ())
        self.assertIsNone(result.invocation_id)

    def test_policy_and_model_authorization_block_before_transport_attempt(self):
        for request, expected_class, expected_reason in (
            (
                self.request(local_only=True, network_allowed=False),
                FailureClass.POLICY,
                "NETWORK_DENIED",
            ),
            (
                self.request(allowed_models=("openai:other-model",)),
                FailureClass.AUTHORIZATION,
                "MODEL_NOT_AUTHORIZED",
            ),
        ):
            with self.subTest(reason=expected_reason):
                transport = DeterministicHttpTransport.json_response(
                    {"choices": [{"message": {"content": "must not execute"}}]}
                )
                with transport.install():
                    with self.assertRaises(InferenceFailure) as raised:
                        HttpInferenceAdapter(
                            "openai",
                            "fixture-model",
                            "fixture-credential",
                        )(request)

                self.assertEqual(raised.exception.failure_class, expected_class)
                self.assertEqual(str(raised.exception), expected_reason)
                self.assertEqual(transport.attempt_count, 0)

    def test_deterministic_provider_failure_is_typed_and_not_retried(self):
        transport = DeterministicHttpTransport.http_error(429)

        with transport.install():
            with self.assertRaises(InferenceFailure) as raised:
                HttpInferenceAdapter(
                    "openai",
                    "fixture-model",
                    "fixture-credential",
                )(self.request())

        self.assertEqual(raised.exception.failure_class, FailureClass.TRANSIENT)
        self.assertEqual(str(raised.exception), "PROVIDER_HTTP_429")
        self.assertEqual(transport.attempt_count, 1)

    def test_deterministic_timeout_is_unknown_outcome_and_not_retried(self):
        transport = DeterministicHttpTransport.timeout()

        with transport.install():
            with self.assertRaises(InferenceFailure) as raised:
                HttpInferenceAdapter(
                    "openai",
                    "fixture-model",
                    "fixture-credential",
                )(self.request())

        self.assertEqual(raised.exception.failure_class, FailureClass.TIMEOUT)
        self.assertEqual(str(raised.exception), "PROVIDER_TIMEOUT_OUTCOME_UNKNOWN")
        self.assertEqual(transport.attempt_count, 1)


if __name__ == "__main__":
    unittest.main()
