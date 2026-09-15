"""v0.2.0 deterministic end-to-end cognitive runtime evidence-chain contract."""

from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path

from tooling.agentic.adapters.inference import InferenceResult
from tooling.agentic.context_governor import ContextItem
from tooling.agentic.decision_receipt import CandidateEvidence
from tooling.agentic.memory import MemoryFabric, MemoryItem, MemoryStatus, MemoryTier
from tooling.agentic.model_router import InferencePolicy, InferenceRequirements, ModelCandidate
from tooling.agentic.models import TaskNode
from tooling.agentic.runtime import JarvisAgenticRuntime


class TestV020CognitiveIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.runtime = JarvisAgenticRuntime(registry_root=self.root)
        self.task = TaskNode("tsk-cognitive-e2e", "Verify router contract")
        self.mission_id = "mis-cognitive-e2e"
        self.agent_id = "agent-cognitive-e2e"
        self.session_id = "session-cognitive-e2e"
        self.policy = InferencePolicy(local_only=True, network_allowed=False)

    def _register(self, model_id, callback, *, local=True):
        self.runtime.inference_backends.register(
            ModelCandidate(
                model_id=model_id,
                provider=f"provider-{model_id}",
                context_window_tokens=8000,
                cost_per_1k_tokens_usd=0.0,
                capability_rating=0.9,
                is_local=local,
            ),
            callback,
        )

    @staticmethod
    def _evidence(rate: float, *, env: str = "linux-py312-e2e") -> CandidateEvidence:
        return CandidateEvidence(
            sample_count=20,
            verified_success_rate=rate,
            median_latency_ms=20.0,
            measured_cost_usd=0.0,
            environment_fingerprint=env,
            freshness_utc="2026-09-15T20:00:00+00:00",
        )

    def _seed_memory(self):
        scope = self.runtime._inference_memory_scope(
            mission_id=self.mission_id,
            agent_id=self.agent_id,
            session_id=self.session_id,
            policy=self.policy,
        )
        memory = MemoryFabric(storage_dir=self.root / "state" / "inference_memory" / scope)
        now = time.time()
        verified = MemoryItem(
            memory_id="mem-router-verified",
            tier=MemoryTier.SEMANTIC,
            key="router-contract",
            content="Verify router contract using independent evidence",
            provenance="evidence:seed",
            confidence=0.95,
            metadata={
                "verification_state": "VERIFIED",
                "evidence_refs": ["evidence:seed"],
                "admission_reason": "verified_fixture",
                "valid_until": now + 3600,
            },
        )
        weak = MemoryItem(
            memory_id="mem-router-weak",
            tier=MemoryTier.EPISODIC,
            key="router-contract-observation",
            content="Verify router contract speculative observation",
            provenance="model-observation:fixture",
            confidence=0.2,
            status=MemoryStatus.UNVERIFIED,
            metadata={
                "verification_state": "UNVERIFIED",
                "evidence_refs": [],
                "admission_reason": "retain_observation_only",
            },
        )
        self.assertTrue(memory.admit(verified).admitted)
        self.assertTrue(memory.admit(weak).admitted)
        memory.save_snapshot()
        return verified, weak

    def test_context_memory_empirical_routing_verification_and_admission_form_one_evidence_chain(self):
        verified_memory, weak_memory = self._seed_memory()
        calls = []
        self._register(
            "a-weak",
            lambda request: calls.append("a-weak") or InferenceResult(
                "uncertain answer",
                0.4,
                ("evidence:weak",),
                prompt_tokens=40,
                completion_tokens=10,
            ),
        )
        self._register(
            "z-strong",
            lambda request: calls.append("z-strong") or InferenceResult(
                "verified answer",
                0.95,
                ("evidence:strong",),
                prompt_tokens=45,
                completion_tokens=12,
            ),
        )
        self._register(
            "zz-cloud-denied",
            lambda request: calls.append("zz-cloud-denied") or InferenceResult(
                "must not run",
                0.99,
                ("evidence:cloud",),
            ),
            local=False,
        )

        candidate_evidence = {
            "a-weak": self._evidence(0.98),
            "z-strong": self._evidence(0.90),
            "zz-cloud-denied": self._evidence(1.0),
        }
        expires = time.time() + 3600
        result = self.runtime.execute_inference(
            self.task,
            mission_id=self.mission_id,
            agent_id=self.agent_id,
            session_id=self.session_id,
            items=[
                ContextItem(
                    "required router invariant",
                    "source:required",
                    required=True,
                    valid_until=expires,
                ),
                ContextItem(
                    "optional supporting detail",
                    "source:optional",
                    priority=5,
                    valid_until=expires,
                ),
            ],
            policy=self.policy,
            requirements=InferenceRequirements(min_capability=0.8, context_tokens=1600),
            verifier=lambda response: response.text == "verified answer" and response.evidence_refs == ("evidence:strong",),
            confidence_threshold=0.8,
            max_attempts=2,
            max_output_tokens=128,
            max_cost_usd=0.0,
            remember=True,
            retrieve_memory=True,
            candidate_evidence=candidate_evidence,
            environment_fingerprint="linux-py312-e2e",
            evidence_now_utc="2026-09-15T20:05:00+00:00",
            max_evidence_age_seconds=3600,
        )

        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["text"], "verified answer")
        self.assertEqual(calls, ["a-weak", "z-strong"])

        trace = result["trace"]
        self.assertEqual(trace["mission_id"], self.mission_id)
        self.assertEqual(trace["task_id"], self.task.task_id)

        context = trace["context"]
        self.assertEqual(context["mission_id"], self.mission_id)
        self.assertEqual(context["task_id"], self.task.task_id)
        self.assertIn("source:required", context["sources_loaded"])
        self.assertIn("source:optional", context["sources_loaded"])
        self.assertIn(verified_memory.provenance, context["sources_loaded"])

        routing = trace["routing"]
        self.assertEqual(routing["mission_id"], self.mission_id)
        self.assertEqual(routing["task_id"], self.task.task_id)
        self.assertEqual(routing["selected_candidate"], "a-weak")
        self.assertEqual(routing["metadata"]["ranking_mode"], "qualified_empirical_then_prior")
        self.assertEqual(routing["metadata"]["eligible_order"][:2], ["a-weak", "z-strong"])
        self.assertEqual(routing["rejected_candidates"]["zz-cloud-denied"], "LOCAL_ONLY")
        self.assertEqual(routing["metadata"]["evidence_status"]["zz-cloud-denied"], "HARD_REJECTED")

        self.assertEqual(len(trace["attempts"]), 2)
        first, second = trace["attempts"]
        self.assertEqual(first["model_id"], "a-weak")
        self.assertEqual(first["governor"]["action"], "ESCALATE_CAPABILITY")
        self.assertEqual(first["verification_receipt"]["verification_state"], "REJECTED")
        self.assertFalse(first["verification_receipt"]["metadata"]["independent_verifier_passed"])
        self.assertEqual(second["model_id"], "z-strong")
        self.assertEqual(second["governor"]["action"], "CONTINUE")
        self.assertEqual(second["verification_receipt"]["verification_state"], "VERIFIED")
        self.assertTrue(second["verification_receipt"]["metadata"]["independent_verifier_passed"])

        for attempt in (first, second):
            execution = attempt["execution_receipt"]
            verification = attempt["verification_receipt"]
            self.assertEqual(execution["mission_id"], self.mission_id)
            self.assertEqual(execution["task_id"], self.task.task_id)
            self.assertEqual(execution["attempt_id"], attempt["attempt_id"])
            self.assertEqual(execution["trace_id"], attempt["trace_id"])
            self.assertEqual(verification["mission_id"], self.mission_id)
            self.assertEqual(verification["task_id"], self.task.task_id)
            self.assertEqual(verification["attempt_id"], attempt["attempt_id"])
            self.assertEqual(verification["trace_id"], attempt["trace_id"])
            self.assertEqual(verification["execution_receipt_id"], execution["receipt_id"])

        self.assertEqual(
            [entry["attempt_id"] for entry in trace["governor_decisions"]],
            [first["attempt_id"], second["attempt_id"]],
        )

        self.assertEqual(len(trace["memory_receipts"]), 1)
        memory_receipt = trace["memory_receipts"][0]
        self.assertEqual(memory_receipt["mission_id"], self.mission_id)
        self.assertEqual(memory_receipt["task_id"], self.task.task_id)
        self.assertIn(verified_memory.memory_id, memory_receipt["selected_item_ids"])
        self.assertEqual(
            memory_receipt["rejected_items"][weak_memory.memory_id]["reason_code"],
            "LOW_CONFIDENCE",
        )

        self.assertEqual(trace["memory_writes"], 1)
        self.assertEqual(len(trace["memory_admissions"]), 1)
        admission = trace["memory_admissions"][0]
        self.assertEqual(admission["verification_state"], "VERIFIED")
        self.assertEqual(admission["evidence_refs"], ["evidence:strong"])
        self.assertEqual(admission["source_attempt_id"], second["attempt_id"])
        self.assertEqual(admission["source_trace_id"], second["trace_id"])

        encoded = json.dumps(trace, sort_keys=True).lower()
        self.assertNotIn("chain_of_thought", encoded)
        self.assertNotIn('"reasoning"', encoded)
        self.assertNotIn('"thoughts"', encoded)


if __name__ == "__main__":
    unittest.main()
