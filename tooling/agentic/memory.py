"""Public v0.2 memory facade with structured retrieval receipts.

The historical four-tier implementation remains in ``memory_core``. This module
keeps public imports stable while adding explicit considered/selected/rejected
retrieval evidence and stricter durable admission for model-derived facts.
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .memory_core import *
from .memory_core import MemoryFabric as _CoreMemoryFabric
from .memory_core import MemoryReceipt as _CoreMemoryReceipt


_RECEIPT_CAPTURE: ContextVar[Optional[List[Dict[str, Any]]]] = ContextVar(
    "jarvis_memory_receipt_capture",
    default=None,
)


@dataclass
class MemoryReceipt(_CoreMemoryReceipt):
    """Backward-compatible receipt with explicit retrieval disposition fields."""

    considered_item_ids: List[str] = field(default_factory=list)
    selected_item_ids: List[str] = field(default_factory=list)
    rejected_items: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "considered_item_ids": list(self.considered_item_ids),
            "selected_item_ids": list(self.selected_item_ids),
            "rejected_items": {
                memory_id: dict(details)
                for memory_id, details in self.rejected_items.items()
            },
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryReceipt":
        resolved = _CoreMemoryReceipt.from_dict(data)
        return cls(
            receipt_id=resolved.receipt_id,
            query=resolved.query,
            tier_filter=list(resolved.tier_filter),
            matched_items=list(resolved.matched_items),
            excluded_conflicts=list(resolved.excluded_conflicts),
            decay_scores=dict(resolved.decay_scores),
            total_tokens_estimated=resolved.total_tokens_estimated,
            token_estimation_method=resolved.token_estimation_method,
            mission_id=resolved.mission_id,
            task_id=resolved.task_id,
            attempt_id=resolved.attempt_id,
            trace_id=resolved.trace_id,
            created_utc=resolved.created_utc,
            timestamp_utc=resolved.timestamp_utc,
            schema_version=resolved.schema_version,
            considered_item_ids=list(data.get("considered_item_ids", [])),
            selected_item_ids=list(data.get("selected_item_ids", [])),
            rejected_items={
                str(memory_id): dict(details)
                for memory_id, details in data.get("rejected_items", {}).items()
            },
        )


class MemoryFabric(_CoreMemoryFabric):
    """Memory fabric with auditable retrieval and provenance-gated durable facts."""

    @classmethod
    def start_receipt_capture(cls) -> Tuple[Token, List[Dict[str, Any]]]:
        bucket: List[Dict[str, Any]] = []
        return _RECEIPT_CAPTURE.set(bucket), bucket

    @classmethod
    def stop_receipt_capture(cls, token: Token) -> None:
        _RECEIPT_CAPTURE.reset(token)

    @staticmethod
    def _model_derived(item: MemoryItem) -> bool:
        provenance = str(item.provenance or "").strip().lower()
        return provenance.startswith(("model:", "inference:", "provider:", "model-output:"))

    def admit(self, item: MemoryItem, *, allow_stale: bool = False) -> MemoryAdmissionResult:
        if isinstance(item, MemoryItem) and item.tier in (MemoryTier.SEMANTIC, MemoryTier.PROCEDURAL):
            if self._model_derived(item):
                verification_state = str(item.metadata.get("verification_state", "")).strip().upper()
                evidence_refs = item.metadata.get("evidence_refs")
                admission_reason = item.metadata.get("admission_reason")
                if verification_state != "VERIFIED":
                    return MemoryAdmissionResult(
                        admitted=False,
                        item_id=None,
                        status=MemoryStatus.ARCHIVED,
                        reason="REJECTED: UNVERIFIED_MODEL_OUTPUT_CANNOT_BECOME_DURABLE_MEMORY",
                    )
                if (
                    not isinstance(evidence_refs, list)
                    or not evidence_refs
                    or any(not isinstance(ref, str) or not ref.strip() for ref in evidence_refs)
                ):
                    return MemoryAdmissionResult(
                        admitted=False,
                        item_id=None,
                        status=MemoryStatus.ARCHIVED,
                        reason="REJECTED: VERIFIED_DURABLE_MODEL_MEMORY_REQUIRES_EVIDENCE_REFS",
                    )
                if not isinstance(admission_reason, str) or not admission_reason.strip():
                    return MemoryAdmissionResult(
                        admitted=False,
                        item_id=None,
                        status=MemoryStatus.ARCHIVED,
                        reason="REJECTED: DURABLE_MODEL_MEMORY_REQUIRES_ADMISSION_REASON",
                    )
        return super().admit(item, allow_stale=allow_stale)

    def _query_candidates(self, target_tiers: List[MemoryTier]) -> List[MemoryItem]:
        candidates: List[MemoryItem] = []
        if MemoryTier.WORKING in target_tiers:
            candidates.extend(self._working.values())
        if MemoryTier.EPISODIC in target_tiers:
            candidates.extend(self._episodic)
        if MemoryTier.SEMANTIC in target_tiers:
            candidates.extend(self._semantic.values())
        if MemoryTier.PROCEDURAL in target_tiers:
            candidates.extend(self._procedural.values())
        return candidates

    def query(
        self,
        query_text: str,
        tiers: Optional[List[MemoryTier]] = None,
        max_items: int = 10,
        min_confidence: float = 0.5,
        token_budget: int = 2000,
        half_life_days: float = 30.0,
        mission_id: Optional[str] = None,
        task_id: Optional[str] = None,
        attempt_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> Tuple[List[MemoryItem], MemoryReceipt]:
        selected, base_receipt = super().query(
            query_text,
            tiers=tiers,
            max_items=max_items,
            min_confidence=min_confidence,
            token_budget=token_budget,
            half_life_days=half_life_days,
            mission_id=mission_id,
            task_id=task_id,
            attempt_id=attempt_id,
            trace_id=trace_id,
        )

        target_tiers = tiers or [
            MemoryTier.WORKING,
            MemoryTier.EPISODIC,
            MemoryTier.SEMANTIC,
            MemoryTier.PROCEDURAL,
        ]
        candidates = self._query_candidates(target_tiers)
        selected_ids = [item.memory_id for item in selected]
        selected_set = set(selected_ids)
        considered_ids = [item.memory_id for item in candidates]
        rejected: Dict[str, Dict[str, Any]] = {}
        q_terms = set(query_text.lower().split())
        selected_token_total = sum(item.estimate_tokens() for item in selected)

        for item in candidates:
            if item.memory_id in selected_set:
                continue
            reason_code = "RANKED_OUT"
            reason = "Candidate was eligible but ranked below selected items"

            if item.tier in (MemoryTier.SEMANTIC, MemoryTier.PROCEDURAL):
                try:
                    if self._is_stale(item):
                        reason_code = "STALE_MEMORY"
                        reason = "Durable memory is stale at retrieval time"
                except ValueError:
                    reason_code = "INVALID_FRESHNESS"
                    reason = "Memory freshness metadata is invalid"

            if reason_code == "RANKED_OUT" and item.status in (
                MemoryStatus.CONFLICT_DETECTED,
                MemoryStatus.DEPRECATED,
                MemoryStatus.ARCHIVED,
            ):
                reason_code = "STATUS_EXCLUDED"
                reason = f"Memory status {item.status.value} is not retrievable"
            elif reason_code == "RANKED_OUT" and item.confidence < min_confidence:
                reason_code = "LOW_CONFIDENCE"
                reason = "Memory confidence is below retrieval threshold"
            elif reason_code == "RANKED_OUT":
                item_text = f"{item.key} {item.content} {' '.join(item.tags)}".lower()
                overlap = sum(1 for term in q_terms if term in item_text)
                if q_terms and overlap == 0 and item.tier != MemoryTier.WORKING:
                    reason_code = "NO_QUERY_MATCH"
                    reason = "Memory has no query-term overlap"
                elif len(selected) >= max_items:
                    reason_code = "MAX_ITEMS_LIMIT"
                    reason = "Retrieval max_items bound excluded this candidate"
                elif selected and selected_token_total + item.estimate_tokens() > token_budget:
                    reason_code = "TOKEN_BUDGET"
                    reason = "Retrieval token budget excluded this candidate"

            rejected[item.memory_id] = {
                "reason_code": reason_code,
                "reason": reason,
                "tier": item.tier.value,
                "key": item.key,
                "status": item.status.value,
            }

        receipt = MemoryReceipt(
            receipt_id=base_receipt.receipt_id,
            query=base_receipt.query,
            tier_filter=list(base_receipt.tier_filter),
            matched_items=list(base_receipt.matched_items),
            excluded_conflicts=list(base_receipt.excluded_conflicts),
            decay_scores=dict(base_receipt.decay_scores),
            total_tokens_estimated=base_receipt.total_tokens_estimated,
            token_estimation_method=base_receipt.token_estimation_method,
            mission_id=base_receipt.mission_id,
            task_id=base_receipt.task_id,
            attempt_id=base_receipt.attempt_id,
            trace_id=base_receipt.trace_id,
            created_utc=base_receipt.created_utc,
            timestamp_utc=base_receipt.timestamp_utc,
            schema_version=base_receipt.schema_version,
            considered_item_ids=considered_ids,
            selected_item_ids=selected_ids,
            rejected_items=rejected,
        )

        capture = _RECEIPT_CAPTURE.get()
        if capture is not None:
            capture.append(receipt.to_dict())
        return selected, receipt
