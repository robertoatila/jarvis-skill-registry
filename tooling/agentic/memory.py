"""Public v0.2 memory facade with structured retrieval receipts.

The historical four-tier implementation remains in ``memory_core``. This module
keeps public imports stable while adding explicit considered/selected/rejected
retrieval evidence, stricter durable admission, and the persistence hardening
validated on ``main``.
"""

from __future__ import annotations

import json
import math
import os
import tempfile
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .memory_core import *
from .memory_core import MemoryFabric as _CoreMemoryFabric
from .memory_core import MemoryItem as _CoreMemoryItem
from .memory_core import MemoryReceipt as _CoreMemoryReceipt


_RECEIPT_CAPTURE: ContextVar[Optional[List[Dict[str, Any]]]] = ContextVar(
    "jarvis_memory_receipt_capture",
    default=None,
)


@dataclass
class MemoryItem(_CoreMemoryItem):
    """Public memory item with finite confidence and aware timestamps."""

    def __post_init__(self) -> None:
        self.tier = MemoryTier(self.tier)
        self.status = MemoryStatus(self.status)
        if not all(isinstance(value, str) and value.strip() for value in (self.memory_id, self.key, self.content)):
            raise ValueError("Memory requires nonempty identity, key and content")
        if not math.isfinite(self.confidence) or not 0 <= self.confidence <= 1:
            raise ValueError("Invalid confidence")
        for value in (self.created_utc, self.last_accessed_utc):
            if datetime.fromisoformat(value).tzinfo is None:
                raise ValueError("Memory timestamps require timezone")


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
    """Memory fabric with auditable retrieval and hardened persistence."""

    SNAPSHOT_SCHEMA_VERSION = "1.0.0"
    MAX_SNAPSHOT_BYTES = 16 * 1024 * 1024

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._history: Dict[str, MemoryItem] = {}

    @classmethod
    def start_receipt_capture(cls) -> Tuple[Token, List[Dict[str, Any]]]:
        bucket: List[Dict[str, Any]] = []
        return _RECEIPT_CAPTURE.set(bucket), bucket

    @classmethod
    def stop_receipt_capture(cls, token: Token) -> None:
        _RECEIPT_CAPTURE.reset(token)

    @staticmethod
    def _model_derived(item: _CoreMemoryItem) -> bool:
        provenance = str(item.provenance or "").strip().lower()
        return provenance.startswith(("model:", "inference:", "provider:", "model-output:"))

    def admit(self, item: _CoreMemoryItem, *, allow_stale: bool = False) -> MemoryAdmissionResult:
        if isinstance(item, _CoreMemoryItem) and item.tier in (MemoryTier.SEMANTIC, MemoryTier.PROCEDURAL):
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

        existing = None
        existing_snapshot = None
        if isinstance(item, _CoreMemoryItem) and item.tier == MemoryTier.SEMANTIC:
            existing = self._semantic.get(item.key)
        elif isinstance(item, _CoreMemoryItem) and item.tier == MemoryTier.PROCEDURAL:
            existing = self._procedural.get(item.key)
        if existing is not None and existing.content != item.content:
            existing_snapshot = MemoryItem.from_dict(existing.to_dict())

        result = super().admit(item, allow_stale=allow_stale)
        if result.admitted and existing_snapshot is not None and result.status != MemoryStatus.CONFLICT_DETECTED:
            existing_snapshot.status = MemoryStatus.CONFLICT_DETECTED
            existing_snapshot.contradicted_by = item.memory_id
            item.status = MemoryStatus.CONFLICT_DETECTED
            item.contradicted_by = existing_snapshot.memory_id
            self._history[existing_snapshot.memory_id] = existing_snapshot
            if item.tier == MemoryTier.SEMANTIC:
                self._semantic[item.key] = item
            else:
                self._procedural[item.key] = item
            return MemoryAdmissionResult(
                admitted=True,
                item_id=item.memory_id,
                status=MemoryStatus.CONFLICT_DETECTED,
                conflicts_detected=[existing_snapshot.memory_id],
                reason=f"CONFLICT_DETECTED: {item.tier.value} key '{item.key}' differs from existing memory {existing_snapshot.memory_id}.",
            )
        return result

    def _query_candidates(self, target_tiers: List[MemoryTier]) -> List[_CoreMemoryItem]:
        candidates: List[_CoreMemoryItem] = []
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
    ) -> Tuple[List[_CoreMemoryItem], MemoryReceipt]:
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

        strict_selected: List[_CoreMemoryItem] = []
        strict_total = 0
        for item in selected:
            item_tokens = item.estimate_tokens()
            if strict_total + item_tokens > token_budget:
                continue
            strict_selected.append(item)
            strict_total += item_tokens
        selected = strict_selected
        selected_ids_set = {item.memory_id for item in selected}
        base_receipt.matched_items = [
            match for match in base_receipt.matched_items
            if match.get("memory_id") in selected_ids_set
        ]
        base_receipt.total_tokens_estimated = strict_total

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
                elif item.estimate_tokens() > max(0, token_budget - selected_token_total):
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

    def _snapshot_target(self, filename: str) -> Path:
        if (
            not isinstance(filename, str)
            or not filename
            or any(char in filename for char in ("/", "\\", ":"))
            or filename in (".", "..")
        ):
            raise ValueError("Snapshot name must be a filename")
        target = self.storage_dir / filename
        if target.is_symlink() or target.resolve().parent != self.storage_dir:
            raise ValueError("Snapshot escapes storage")
        return target

    def save_snapshot(self, filename: str = "memory_snapshot.json") -> Path:
        target = self._snapshot_target(filename)
        data = {
            "working": [item.to_dict() for item in self._working.values()],
            "episodic": [item.to_dict() for item in self._episodic],
            "semantic": [item.to_dict() for item in self._semantic.values()],
            "procedural": [item.to_dict() for item in self._procedural.values()],
            "history": [item.to_dict() for item in self._history.values()],
            "schema_version": self.SNAPSHOT_SCHEMA_VERSION,
        }
        fd, name = tempfile.mkstemp(dir=self.storage_dir, suffix=".tmp")
        tmp_target = Path(name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(data, stream, indent=2, allow_nan=False)
                stream.flush()
                os.fsync(stream.fileno())
            tmp_target.replace(target)
        finally:
            tmp_target.unlink(missing_ok=True)
        return target

    def load_snapshot(self, filename: str = "memory_snapshot.json") -> bool:
        target = self._snapshot_target(filename)
        if not target.exists():
            return False
        try:
            with target.open("rb") as stream:
                raw = stream.read(self.MAX_SNAPSHOT_BYTES + 1)
            if len(raw) > self.MAX_SNAPSHOT_BYTES:
                raise ValueError("Snapshot too large")
            data = json.loads(raw.decode("utf-8"))
            if data.get("schema_version", self.SNAPSHOT_SCHEMA_VERSION) != self.SNAPSHOT_SCHEMA_VERSION:
                raise ValueError("Unsupported snapshot version")

            parsed: Dict[str, List[MemoryItem]] = {}
            seen_ids = set()
            for section in ("working", "episodic", "semantic", "procedural", "history"):
                items = [MemoryItem.from_dict(raw_item) for raw_item in data.get(section, [])]
                keys = set()
                for item in items:
                    if item.memory_id in seen_ids:
                        raise ValueError("Duplicate memory identity")
                    if section != "history" and item.tier.value.lower() != section:
                        raise ValueError("Memory snapshot tier mismatch")
                    if section not in ("episodic", "history") and item.key in keys:
                        raise ValueError("Duplicate memory key")
                    if self._provenance_is_unknown(item.provenance):
                        raise ValueError("Missing provenance")
                    if item.tier in (MemoryTier.SEMANTIC, MemoryTier.PROCEDURAL) and item.status == MemoryStatus.UNVERIFIED:
                        raise ValueError("Unverified durable memory in snapshot")
                    keys.add(item.key)
                    seen_ids.add(item.memory_id)
                parsed[section] = items

            if len(parsed["working"]) > self.working_capacity:
                raise ValueError("Working capacity exceeded")

            self._working = {item.key: item for item in parsed["working"]}
            self._episodic = list(parsed["episodic"])
            self._semantic = {item.key: item for item in parsed["semantic"]}
            self._procedural = {item.key: item for item in parsed["procedural"]}
            self._history = {item.memory_id: item for item in parsed["history"]}
            return True
        except Exception:
            return False

    def get_by_id(self, memory_id: str) -> Optional[_CoreMemoryItem]:
        candidates = [
            *self._working.values(),
            *self._episodic,
            *self._semantic.values(),
            *self._procedural.values(),
            *self._history.values(),
        ]
        return next((item for item in candidates if item.memory_id == memory_id), None)
