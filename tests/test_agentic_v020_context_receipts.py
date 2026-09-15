"""v0.2.0 context measurement contracts: bytes are measured, tokens are optional estimates."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tooling.agentic.adapters.inference import InferenceResult
from tooling.agentic.context_governor import (
    ContextGovernor,
    ContextItem,
    ContextOverflowError,
    compile_context,
)
from tooling.agentic.model_router import InferencePolicy, InferenceRequirements, ModelCandidate
from tooling.agentic.models import TaskNode
from tooling.agentic.runtime import JarvisAgenticRuntime


class TestV020ContextReceipts(unittest.TestCase):
    def test_byte_budget_is_measured_without_inventing_token_count(self):
        items = [
            ContextItem("required fact", "required", required=True),
            ContextItem("optional context " * 20, "optional"),
        ]
        text, receipt = compile_context(items, 120, now=0)

        measured_bytes = len(text.encode("utf-8"))
        self.assertEqual(receipt.serialized_bytes, measured_bytes)
        self.assertLessEqual(receipt.serialized_bytes, 120)
        self.assertIsNone(receipt.token_estimate)
        self.assertIsNone(receipt.token_estimation_method)
        self.assertIsNone(receipt.estimated_tokens)
        self.assertEqual(receipt.bytes_loaded, measured_bytes)

    def test_supplied_estimator_records_estimate_and_method(self):
        estimator = lambda text: len(text.split())
        text, receipt = compile_context(
            [ContextItem("one two three", "fixture", required=True)],
            200,
            now=0,
            token_estimator=estimator,
            token_estimation_method="fixture_whitespace_v1",
        )

        self.assertEqual(receipt.token_estimate, estimator(text))
        self.assertEqual(receipt.estimated_tokens, estimator(text))
        self.assertEqual(receipt.token_estimation_method, "fixture_whitespace_v1")
        encoded = receipt.to_dict()
        self.assertEqual(encoded["serialized_bytes"], len(text.encode("utf-8")))
        self.assertEqual(encoded["token_estimate"], estimator(text))
        self.assertEqual(encoded["token_estimation_method"], "fixture_whitespace_v1")

    def test_estimator_requires_explicit_method_and_valid_result(self):
        with self.assertRaises(ValueError):
            compile_context(
                [ContextItem("fact", "fixture", required=True)],
                100,
                now=0,
                token_estimator=lambda text: 1,
            )
        with self.assertRaises(ValueError):
            compile_context(
                [ContextItem("fact", "fixture", required=True)],
                100,
                now=0,
                token_estimator=lambda text: -1,
                token_estimation_method="invalid_fixture",
            )

    def test_required_overflow_and_freshness_remain_fail_closed(self):
        with self.assertRaises(ContextOverflowError):
            compile_context([ContextItem("required", "fixture", required=True)], 1, now=0)
        with self.assertRaisesRegex(ValueError, "STALE_REQUIRED"):
            compile_context(
                [ContextItem("required", "fixture", required=True, valid_until=1)],
                100,
                now=2,
            )

        first = compile_context(
            [
                ContextItem("fresh", "fresh", required=True, valid_until=10),
                ContextItem("stale", "stale", valid_until=1),
            ],
            200,
            now=2,
        )[1]
        second = compile_context(
            [
                ContextItem("stale", "stale", valid_until=1),
                ContextItem("fresh", "fresh", required=True, valid_until=10),
            ],
            200,
            now=2,
        )[1]
        self.assertEqual(first.sources_loaded, ["fresh"])
        self.assertEqual(first.sources_loaded, second.sources_loaded)
        self.assertEqual(first.provenance["omitted_sources"], second.provenance["omitted_sources"])

    def test_file_receipts_keep_cache_deterministic_and_tokens_unknown_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "fixture.txt").write_text("context fixture", encoding="utf-8")
            governor = ContextGovernor(workspace_root=root)

            first_text, first = governor.read_with_receipt("fixture.txt")
            second_text, second = governor.read_with_receipt("fixture.txt")

            self.assertEqual(first_text, second_text)
            self.assertFalse(first.cache_hit)
            self.assertTrue(second.cache_hit)
            self.assertEqual(first.serialized_bytes, len(first_text.encode("utf-8")))
            self.assertEqual(second.serialized_bytes, len(second_text.encode("utf-8")))
            self.assertIsNone(first.token_estimate)
            self.assertIsNone(second.token_estimate)
            self.assertIsNone(first.token_estimation_method)
            self.assertIsNone(second.token_estimation_method)

    def test_runtime_does_not_understate_unknown_context_tokens_from_byte_count(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = JarvisAgenticRuntime(registry_root=Path(directory))
            runtime.inference_backends.register(
                ModelCandidate(
                    "small",
                    "fixture-backend",
                    1000,
                    0,
                    0.9,
                    is_local=True,
                ),
                lambda request: InferenceResult("ok", 0.9, ("fixture",)),
            )
            task = TaskNode("task-context-units", "Context units")

            result = runtime.execute_inference(
                task,
                mission_id="mission-context-units",
                agent_id="agent-context-units",
                session_id="session-context-units",
                items=[
                    ContextItem(
                        "verified fact",
                        "fixture",
                        required=True,
                        valid_until=9_999_999_999,
                    )
                ],
                policy=InferencePolicy(),
                requirements=InferenceRequirements(context_tokens=1500),
                verifier=lambda result: True,
                confidence_threshold=0.8,
                max_output_tokens=100,
            )

            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["trace"]["reason"], "NO_ELIGIBLE_BACKEND")


if __name__ == "__main__":
    unittest.main()
