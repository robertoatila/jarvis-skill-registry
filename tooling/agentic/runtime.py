"""Public J.A.R.V.I.S. runtime facade with v0.2 memory observability.

The adaptive Governor implementation remains in ``runtime_adaptive_core``. This
facade preserves the public runtime import while correlating memory retrieval
receipts and sealing verified inference-memory provenance after acceptance.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace
from typing import Any, Dict, List

from .runtime_adaptive_core import *
from .runtime_adaptive_core import JarvisAgenticRuntime as _AdaptiveJarvisAgenticRuntime
from .context_governor import ContextItem
from .memory import MemoryFabric
from .model_router import InferencePolicy, InferenceRequirements
from .models import TaskNode


class JarvisAgenticRuntime(_AdaptiveJarvisAgenticRuntime):
    """Adaptive runtime extended with correlated memory receipts and provenance."""

    @staticmethod
    def _effective_inference_policy(config, policy: InferencePolicy) -> InferencePolicy:
        effective = policy
        if config.offline_only:
            effective = replace(effective, local_only=True, network_allowed=False)
        if effective.local_only:
            effective = replace(effective, network_allowed=False)
        return effective

    def _inference_memory_scope(
        self,
        *,
        mission_id: str,
        agent_id: str,
        session_id: str,
        policy: InferencePolicy,
    ) -> str:
        effective_policy = self._effective_inference_policy(self.config, policy)
        return hashlib.sha256(
            json.dumps(
                [mission_id, agent_id, session_id, asdict(effective_policy)],
                sort_keys=True,
            ).encode()
        ).hexdigest()

    def _seal_verified_inference_memory(
        self,
        result: Dict[str, Any],
        *,
        mission_id: str,
        agent_id: str,
        session_id: str,
        policy: InferencePolicy,
    ) -> None:
        trace = result.get("trace") if isinstance(result, dict) else None
        if not isinstance(trace, dict) or result.get("status") != "SUCCESS":
            return
        if trace.get("memory_writes", 0) <= 0 or not isinstance(result.get("text"), str):
            return

        accepted_attempt = None
        for attempt in reversed(trace.get("attempts", [])):
            governor = attempt.get("governor", {}) if isinstance(attempt, dict) else {}
            if attempt.get("action") == "ACCEPT" and governor.get("action") == "CONTINUE":
                accepted_attempt = attempt
                break
        if not accepted_attempt:
            return

        evidence_refs = accepted_attempt.get("evidence_refs", [])
        if (
            not isinstance(evidence_refs, list)
            or not evidence_refs
            or any(not isinstance(ref, str) or not ref for ref in evidence_refs)
        ):
            return

        scope = self._inference_memory_scope(
            mission_id=mission_id,
            agent_id=agent_id,
            session_id=session_id,
            policy=policy,
        )
        memory = MemoryFabric(storage_dir=self.config.state_dir / "inference_memory" / scope)
        if not memory.load_snapshot():
            return

        memory_key = hashlib.sha256(result["text"].encode("utf-8")).hexdigest()
        item = memory._semantic.get(memory_key)
        if item is None:
            return

        item.metadata.update({
            "verification_state": "VERIFIED",
            "evidence_refs": list(evidence_refs),
            "admission_reason": "verified_inference_result",
            "source_attempt_id": accepted_attempt.get("attempt_id"),
            "source_trace_id": accepted_attempt.get("trace_id"),
        })
        memory.save_snapshot()
        trace.setdefault("memory_admissions", []).append({
            "memory_id": item.memory_id,
            "tier": item.tier.value,
            "verification_state": "VERIFIED",
            "evidence_refs": list(evidence_refs),
            "admission_reason": "verified_inference_result",
        })

    def execute_inference(
        self,
        task: TaskNode,
        *,
        mission_id: str,
        agent_id: str,
        session_id: str,
        items: List[ContextItem],
        policy: InferencePolicy,
        requirements: InferenceRequirements,
        verifier,
        confidence_threshold: float,
        max_attempts: int = 2,
        max_output_tokens: int = 512,
        max_cost_usd: float = 0.0,
        cache_ttl: float = 0.0,
        remember: bool = False,
        retrieve_memory: bool = False,
    ) -> Dict[str, Any]:
        capture_token, captured_receipts = MemoryFabric.start_receipt_capture()
        try:
            result = super().execute_inference(
                task,
                mission_id=mission_id,
                agent_id=agent_id,
                session_id=session_id,
                items=items,
                policy=policy,
                requirements=requirements,
                verifier=verifier,
                confidence_threshold=confidence_threshold,
                max_attempts=max_attempts,
                max_output_tokens=max_output_tokens,
                max_cost_usd=max_cost_usd,
                cache_ttl=cache_ttl,
                remember=remember,
                retrieve_memory=retrieve_memory,
            )
        finally:
            MemoryFabric.stop_receipt_capture(capture_token)

        trace = result.get("trace") if isinstance(result, dict) else None
        if isinstance(trace, dict):
            trace["memory_receipts"] = list(captured_receipts)

        if remember:
            self._seal_verified_inference_memory(
                result,
                mission_id=mission_id,
                agent_id=agent_id,
                session_id=session_id,
                policy=policy,
            )
        return result
