"""Public J.A.R.V.I.S. runtime facade with v0.2 memory observability.

The adaptive Governor implementation remains in ``runtime_adaptive_core``. This
facade preserves the public runtime import while correlating memory retrieval
receipts and sealing verified inference-memory provenance after acceptance.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace
from typing import Any, Dict, List, Optional

from .runtime_adaptive_core import *
from .runtime_adaptive_core import JarvisAgenticRuntime as _AdaptiveJarvisAgenticRuntime
from .context_governor import ContextItem
from .memory import MemoryFabric
from .model_router import InferencePolicy, InferenceRequirements
from .models import Mission, TaskNode
from .observability import ReceiptLedger


class JarvisAgenticRuntime(_AdaptiveJarvisAgenticRuntime):
    """Adaptive runtime with correlated memory and append-only receipt observability."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.observability_errors: List[Dict[str, Any]] = []
        try:
            self.receipt_ledger = ReceiptLedger(self.config.receipts_dir)
        except Exception as exc:
            self.receipt_ledger = None
            self._record_observability_error("initialize_ledger", exc)

    def _record_observability_error(
        self,
        operation: str,
        error: Exception,
        *,
        receipt_id: Optional[str] = None,
    ) -> None:
        self.observability_errors.append({
            "operation": operation,
            "error_type": type(error).__name__,
            "receipt_id": receipt_id,
        })

    def _persist_receipts(
        self,
        receipts,
        *,
        mission_id: str,
        task_id: Optional[str] = None,
    ) -> None:
        ledger = self.receipt_ledger
        if ledger is None:
            return

        for receipt in receipts:
            if not isinstance(receipt, dict):
                continue
            normalized = dict(receipt)
            receipt_id = normalized.get("receipt_id")
            if not isinstance(receipt_id, str) or not receipt_id:
                continue

            current_mission = normalized.get("mission_id")
            if current_mission is None:
                normalized["mission_id"] = mission_id
            elif current_mission != mission_id:
                self._record_observability_error(
                    "correlate_receipt",
                    ValueError("mission correlation mismatch"),
                    receipt_id=receipt_id,
                )
                continue

            if task_id is not None:
                current_task = normalized.get("task_id")
                if current_task is None:
                    normalized["task_id"] = task_id
                elif current_task != task_id:
                    self._record_observability_error(
                        "correlate_receipt",
                        ValueError("task correlation mismatch"),
                        receipt_id=receipt_id,
                    )
                    continue

            try:
                contains = getattr(ledger, "contains", None)
                if callable(contains) and contains(receipt_id):
                    continue
                ledger.append(normalized)
            except Exception as exc:
                self._record_observability_error(
                    "append_receipt",
                    exc,
                    receipt_id=receipt_id,
                )

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

        source_attempt_id = accepted_attempt.get("attempt_id")
        source_trace_id = accepted_attempt.get("trace_id")
        item.metadata.update({
            "verification_state": "VERIFIED",
            "evidence_refs": list(evidence_refs),
            "admission_reason": "verified_inference_result",
            "source_attempt_id": source_attempt_id,
            "source_trace_id": source_trace_id,
        })
        memory.save_snapshot()
        trace.setdefault("memory_admissions", []).append({
            "memory_id": item.memory_id,
            "tier": item.tier.value,
            "verification_state": "VERIFIED",
            "evidence_refs": list(evidence_refs),
            "admission_reason": "verified_inference_result",
            "source_attempt_id": source_attempt_id,
            "source_trace_id": source_trace_id,
        })

    def execute_goal(
        self,
        goal_prompt,
        required_capabilities=None,
        target_platform: str = "windows",
        budget_limits=None,
        operator_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        result = super().execute_goal(
            goal_prompt,
            required_capabilities=required_capabilities,
            target_platform=target_platform,
            budget_limits=budget_limits,
            operator_id=operator_id,
        )

        mission_id = result.get("mission_id") if isinstance(result, dict) else None
        if not isinstance(mission_id, str) or not mission_id:
            return result

        mission = goal_prompt if isinstance(goal_prompt, Mission) else self.load_mission(mission_id)
        if mission is None:
            return result

        metadata = mission.metadata if isinstance(mission.metadata, dict) else {}
        receipts = []
        for key in (
            "decision_receipts",
            "execution_receipts",
            "verification_receipts",
        ):
            values = metadata.get(key, [])
            if isinstance(values, list):
                receipts.extend(value for value in values if isinstance(value, dict))

        self._persist_receipts(receipts, mission_id=mission_id)
        return result

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
        candidate_evidence: Optional[Dict[str, Any]] = None,
        environment_fingerprint: Optional[str] = None,
        evidence_now_utc: Optional[str] = None,
        max_evidence_age_seconds: Optional[float] = None,
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
                candidate_evidence=candidate_evidence,
                environment_fingerprint=environment_fingerprint,
                evidence_now_utc=evidence_now_utc,
                max_evidence_age_seconds=max_evidence_age_seconds,
            )
        finally:
            MemoryFabric.stop_receipt_capture(capture_token)

        trace = result.get("trace") if isinstance(result, dict) else None
        if isinstance(trace, dict):
            correlated_receipts = []
            for receipt in captured_receipts:
                correlated = dict(receipt)
                if correlated.get("mission_id") is None:
                    correlated["mission_id"] = mission_id
                if correlated.get("task_id") is None:
                    correlated["task_id"] = task.task_id
                correlated_receipts.append(correlated)
            trace["memory_receipts"] = correlated_receipts

        if remember:
            self._seal_verified_inference_memory(
                result,
                mission_id=mission_id,
                agent_id=agent_id,
                session_id=session_id,
                policy=policy,
            )

        if isinstance(trace, dict):
            receipts = []
            for key in ("context", "routing"):
                value = trace.get(key)
                if isinstance(value, dict):
                    receipts.append(value)
            for attempt in trace.get("attempts", []):
                if not isinstance(attempt, dict):
                    continue
                for key in ("execution_receipt", "verification_receipt"):
                    value = attempt.get(key)
                    if isinstance(value, dict):
                        receipts.append(value)
            receipts.extend(
                receipt
                for receipt in trace.get("memory_receipts", [])
                if isinstance(receipt, dict)
            )
            self._persist_receipts(
                receipts,
                mission_id=mission_id,
                task_id=task.task_id,
            )
        return result
