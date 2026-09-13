"""Executable acceptance tests for the capability-driven software upgrade."""
import unittest
import tempfile
from pathlib import Path
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from tooling.agentic.runtime import JarvisAgenticRuntime
from tooling.agentic.adapters.inference import InferenceResult, InferenceFailure
from tooling.agentic.models import FailureClass

from tooling.agentic.model_router import ModelCandidate, ModelRouter, InferencePolicy, InferenceRequirements
from tooling.agentic.models import TaskNode
from tooling.agentic.context_governor import ContextItem, compile_context, ContextOverflowError, InferenceCache
from tooling.agentic.tool_router import ToolCandidate, ToolRouter


class TestSoftwareContext(unittest.TestCase):
    def test_mandatory_priority_overflow_and_provenance(self):
        required = ContextItem("policy", "runtime", required=True)
        optional = ContextItem("noise" * 1000, "tool-result")
        text, receipt = compile_context([optional, required], 100, now=0)
        self.assertLessEqual(receipt.estimated_tokens, 100)
        self.assertIn("runtime", text)
        self.assertEqual(receipt.provenance["omitted_sources"], ["tool-result"])
        self.assertEqual(text, compile_context([required, optional], 100, now=0)[0])
        with self.assertRaises(ContextOverflowError):
            compile_context([required], 1, now=0)

    def test_dedup_and_stale_mandatory_evidence(self):
        text, _ = compile_context([ContextItem("same", "a"), ContextItem("same", "b")], 100, now=0)
        self.assertEqual(text.count("same"), 1)
        self.assertIn('"a","b"', text)
        with self.assertRaisesRegex(ValueError, "STALE_REQUIRED"):
            compile_context([ContextItem("evidence", "source", required=True, valid_until=1)], 100, now=2)

    def test_cache_expiry_and_copy_isolation(self):
        clock = [0]
        cache = InferenceCache(clock=lambda: clock[0])
        cache.put("scope-policy-version-hash", {"answer": []}, 5)
        value, state = cache.get("scope-policy-version-hash")
        self.assertEqual(state, "HIT")
        value["answer"].append("private")
        self.assertEqual(cache.get("scope-policy-version-hash")[0], {"answer": []})
        clock[0] = 5
        self.assertEqual(cache.get("scope-policy-version-hash")[1], "INVALIDATED_STALE")


class TestSoftwareRouting(unittest.TestCase):
    def test_tool_permission_and_network_precede_score(self):
        local = ToolCandidate("local", "Local", ["read"])
        cloud = ToolCandidate("external", "External", ["read"], requires_network=True)
        wrong = ToolCandidate("wrong", "Wrong", ["bread"])
        task = TaskNode("task", "Task")
        selected, receipt = ToolRouter([cloud, wrong, local]).route_tool(task,
            required_capabilities=["read"], policy=InferencePolicy(allowed_tools=("local", "external", "wrong")))
        self.assertEqual(selected.tool_id, "local")
        self.assertEqual(receipt.rejected_candidates["external"], "NETWORK_DENIED")
        self.assertIn("wrong", receipt.rejected_candidates)
        self.assertIsNone(ToolRouter([local]).route_tool(task, policy=InferencePolicy())[0])

    def test_invalid_manifest_and_request(self):
        with self.assertRaises(ValueError):
            ModelCandidate("x", "backend", 0, 0, 0.8)
        with self.assertRaises(ValueError):
            InferenceRequirements(context_tokens=-1)
        with self.assertRaises(ValueError):
            InferencePolicy(local_only="false")

    def test_empty_catalog_fails_closed(self):
        model, receipt = ModelRouter([]).route_model(TaskNode("task", "Task"), policy=InferencePolicy())
        self.assertIsNone(model)
        self.assertEqual(receipt.candidates, [])

    def test_constraints_and_stable_tie_break(self):
        local = ModelCandidate("a", "one", 8000, 0, 0.8, is_local=True, supports_tools=True)
        tie = ModelCandidate("b", "two", 8000, 0, 0.8, is_local=True, supports_tools=True)
        cloud = ModelCandidate("cloud", "three", 8000, 0, 1.0)
        network = ModelCandidate("lan", "four", 8000, 0, 1.0, is_local=True, requires_network=True)
        for candidates in ([tie, local, cloud, network], [network, cloud, local, tie]):
            model, receipt = ModelRouter(candidates).route_model(TaskNode("task", "Task"),
                policy=InferencePolicy(), requirements=InferenceRequirements(requires_tools=True))
            self.assertEqual(model.model_id, "a")
            self.assertEqual(receipt.metadata["eligible_order"], ["a", "b"])
            self.assertEqual(receipt.rejected_candidates["cloud"], "LOCAL_ONLY")
            self.assertEqual(receipt.rejected_candidates["lan"], "NETWORK_DENIED")


class TestSoftwareInference(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.runtime = JarvisAgenticRuntime(registry_root=Path(self.directory.name))
        self.args = dict(mission_id="mission", agent_id="agent", session_id="session",
            items=[ContextItem("fact", "source", required=True, valid_until=9999999999)],
            policy=InferencePolicy(), requirements=InferenceRequirements(context_tokens=1000),
            verifier=lambda result: result.evidence_refs == ("source",), confidence_threshold=0.8)
        self.task = TaskNode("task", "fact")

    def register(self, name, callback, **kwargs):
        manifest = ModelCandidate(name, "backend-" + name, 8000, 0, 0.9, is_local=True, **kwargs)
        self.runtime.inference_backends.register(manifest, callback)

    def run_request(self, **kwargs):
        return self.runtime.execute_inference(self.task, **(self.args | kwargs))

    def test_swappable_backend_and_shared_request_isolation(self):
        seen = []
        def backend(request):
            seen.append(request)
            return InferenceResult(request.session_id, 0.9, ("source",))
        self.register("one", backend)
        first = self.run_request()
        self.assertEqual(self.task.attempts[-1].attempt_id, first["trace"]["attempts"][-1]["attempt_id"])
        self.assertEqual(self.task.attempts[-1].outcome.value, "SUCCEEDED")
        second = self.run_request(agent_id="other-agent", session_id="other-session")
        self.assertEqual((first["text"], second["text"]), ("session", "other-session"))
        self.assertEqual(seen[0].agent_id, "agent")
        self.assertEqual(seen[1].agent_id, "other-agent")
        self.register("two", lambda request: InferenceResult("replacement", 0.9, ("source",)))
        result = self.run_request(policy=InferencePolicy(allowed_models=("two",)))
        self.assertEqual(result["text"], "replacement")

    def test_transient_fallback_is_bounded_and_never_uses_cloud(self):
        calls = []
        def fail(request):
            calls.append("a")
            raise InferenceFailure(FailureClass.TRANSIENT, "private error payload")
        self.register("a", fail)
        self.register("b", lambda request: InferenceResult("ok", 0.9, ("source",)))
        cloud = ModelCandidate("cloud", "remote", 8000, 0, 1.0)
        self.runtime.inference_backends.register(cloud, lambda request: self.fail("cloud invoked"))
        result = self.run_request(max_attempts=2)
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual([a["model_id"] for a in result["trace"]["attempts"]], ["a", "b"])
        self.assertNotIn("private error payload", str(result["trace"]))
        result = self.run_request(max_attempts=1)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(len(result["trace"]["attempts"]), 1)

    def test_policy_denial_is_terminal(self):
        def denied(request):
            raise InferenceFailure(FailureClass.POLICY, "denied")
        self.register("a", denied)
        self.register("b", lambda request: self.fail("policy bypass"))
        result = self.run_request()
        self.assertEqual(result["trace"]["reason"], "POLICY")
        self.assertEqual(len(result["trace"]["attempts"]), 1)

    def test_cloud_optional_requires_explicit_network_and_same_policy_on_fallback(self):
        self.runtime.config.offline_only = False
        def fail(request):
            raise InferenceFailure(FailureClass.EXTERNAL_SERVICE, "unavailable")
        self.register("a", fail)
        cloud_calls = []
        def cloud(request):
            cloud_calls.append(request.policy)
            return InferenceResult("allowed", 0.9, ("source",))
        self.runtime.inference_backends.register(ModelCandidate("cloud", "remote-adapter", 8000, 0, 0.9), cloud)
        denied = InferencePolicy(local_only=False, network_allowed=False)
        self.assertEqual(self.run_request(policy=denied)["status"], "BLOCKED")
        self.assertEqual(cloud_calls, [])
        allowed = InferencePolicy(local_only=False, network_allowed=True, allowed_models=("a", "cloud"))
        self.assertEqual(self.run_request(policy=allowed)["text"], "allowed")
        self.assertEqual(cloud_calls, [allowed])

    def test_low_confidence_changes_flow_and_unverified_result_stops(self):
        self.register("a", lambda request: InferenceResult("unsure", 0.2, ("source",)))
        self.register("b", lambda request: InferenceResult("verified", 0.9, ("source",)))
        result = self.run_request()
        self.assertEqual(result["text"], "verified")
        self.assertEqual(result["trace"]["attempts"][0]["action"], "TRY_ELIGIBLE_ALTERNATIVE")
        result = self.run_request(verifier=lambda result: False)
        self.assertEqual(result["status"], "BLOCKED")

    def test_overflow_fails_before_backend_invocation(self):
        self.register("a", lambda request: self.fail("overflow invoked backend"))
        result = self.run_request(requirements=InferenceRequirements(context_tokens=5))
        self.assertEqual(result["trace"]["reason"], "CONTEXT_OVERFLOW")
        self.assertEqual(result["trace"]["attempts"], [])

    def test_local_only_without_backend_fails_closed(self):
        result = self.run_request()
        self.assertEqual(result["trace"]["reason"], "NO_ELIGIBLE_BACKEND")

    def test_provider_reported_usage_reaches_attempt_without_inventing_cost(self):
        self.register("a", lambda request: InferenceResult("ok", 0.9, ("source",), 20, 4))
        result = self.run_request()
        budget = self.task.attempts[-1].budget_consumed
        self.assertEqual(budget["token_measurement"], "PROVIDER_REPORTED")
        self.assertEqual((budget["prompt_tokens"], budget["completion_tokens"]), (20, 4))
        self.assertEqual(budget["cost_measurement"], "UNKNOWN")
        self.assertEqual(result["trace"]["attempts"][0]["token_usage"]["prompt_tokens"], 20)
        self.run_request(cache_ttl=30)
        self.run_request(cache_ttl=30)
        budget = self.task.attempts[-1].budget_consumed
        self.assertEqual(budget["token_measurement"], "MEASURED_NO_MODEL_INVOCATION")
        self.assertEqual((budget["prompt_tokens"], budget["completion_tokens"]), (0, 0))

    def test_cache_policy_scope_and_revalidation(self):
        calls = []
        def backend(request):
            calls.append(request.session_id)
            return InferenceResult("ok", 0.9, ("source",))
        self.register("a", backend)
        self.assertEqual(self.run_request(cache_ttl=30)["trace"]["cache"], "MISS")
        self.assertEqual(self.run_request(cache_ttl=30)["trace"]["cache"], "HIT")
        self.assertEqual(len(calls), 1)
        self.run_request(cache_ttl=30, session_id="other")
        self.assertEqual(len(calls), 2)
        result = self.run_request(cache_ttl=30, verifier=lambda result: False)
        self.assertEqual(result["status"], "BLOCKED")
        result = self.run_request(cache_ttl=30, policy=InferencePolicy(allowed_models=()))
        self.assertEqual(result["trace"]["reason"], "NO_ELIGIBLE_BACKEND")

    def test_selective_persistent_memory_dedup(self):
        self.register("a", lambda request: InferenceResult("fact", 0.9, ("source",)))
        self.assertEqual(self.run_request()["trace"]["memory_writes"], 0)
        self.assertEqual(self.run_request(remember=True)["trace"]["memory_writes"], 1)
        self.assertEqual(self.run_request(remember=True)["trace"]["memory_writes"], 0)
        self.assertEqual(self.run_request(remember=True, verifier=lambda result: False)["trace"]["memory_writes"], 0)

    def test_concurrent_agents_share_backend_without_request_state_leak(self):
        self.register("shared", lambda request: InferenceResult(request.session_id, 0.9, ("source",)))
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda identity: self.run_request(agent_id=identity, session_id=identity), ["one", "two"]))
        self.assertEqual([r["text"] for r in results], ["one", "two"])

    def test_backend_replacement_invalidates_cached_result(self):
        self.register("a", lambda request: InferenceResult("old", 0.9, ("source",)))
        self.run_request(cache_ttl=30)
        self.register("a", lambda request: InferenceResult("new", 0.9, ("source",)))
        result = self.run_request(cache_ttl=30)
        self.assertEqual(result["text"], "new")
        self.assertEqual(result["trace"]["cache"], "MISS")

    def test_unknown_failure_does_not_retry_and_large_output_is_rejected(self):
        def unknown(request):
            raise RuntimeError("sensitive detail")
        self.register("a", unknown)
        self.register("b", lambda request: self.fail("blind retry"))
        result = self.run_request()
        self.assertEqual(result["trace"]["reason"], "UNKNOWN_BACKEND_OR_VERIFIER_FAILURE")
        self.assertNotIn("sensitive detail", str(result))
        self.runtime.inference_backends.register(ModelCandidate("a", "adapter", 8000, 0, 0.9, is_local=True),
            lambda request: InferenceResult("x" * 1000, 1.0, ("source",)))
        result = self.run_request(max_attempts=1, max_output_tokens=10)
        self.assertEqual(result["trace"]["attempts"][0]["failure_class"], "MALFORMED_RESULT")

    def test_confidence_unknown_and_memory_without_freshness_are_not_facts(self):
        self.register("a", lambda request: InferenceResult("unknown", None, ("source",)))
        result = self.run_request(remember=True)
        self.assertEqual(result["trace"]["attempts"][0]["action"], "GATHER_EVIDENCE")
        self.assertEqual(result["trace"]["memory_writes"], 0)
        self.register("a", lambda request: InferenceResult("known", 0.9, ("source",)))
        result = self.run_request(remember=True, items=[ContextItem("fact", "source")])
        self.assertEqual(result["trace"]["memory_writes"], 0)

    def test_memory_retrieval_is_session_scoped(self):
        self.register("a", lambda request: InferenceResult("remembered-fact", 0.9, ("source",)))
        self.run_request(remember=True)
        result = self.run_request(retrieve_memory=True, items=[])
        self.assertIn("source", result["trace"]["context"]["sources_loaded"])
        other = self.run_request(retrieve_memory=True, items=[], session_id="other")
        self.assertNotIn("source", other["trace"]["context"]["sources_loaded"])


if __name__ == "__main__":
    unittest.main()
