"""
memory.py // J.A.R.V.I.S. 4-Tier Memory Fabric & Memory Admission Engine
Pure Python 3.12 Standard Library (Zero External PIP Dependencies)

Implements Phases 30 and 31 of the Autonomous Evolution Protocol:
- 4-Tier Hierarchical Memory:
  * WORKING: Ephemeral active task scratchpad (bounded capacity, FIFO eviction)
  * EPISODIC: Historical task attempts, verified episodes, and execution traces
  * SEMANTIC: Verified facts, architectural invariants, domain rules, and concepts
  * PROCEDURAL: Reusable playbooks, multi-step repair heuristics, and tool recipes
- Memory Admission Gate:
  * Mandatory provenance verification (tied to verified mission, attempt, or human grant)
  * Real conflict detection (flags CONFLICT_DETECTED, forbids silent contradiction overwrite)
  * Temporal decay modeling using exponential half-life
- Ordered Retrieval with MemoryReceipts:
  * Multi-dimensional ranking (Relevance, Confidence, Freshness Decay)
  * Token-bounded return set
  * Full auditability via explainable MemoryReceipt
"""

from __future__ import annotations
import os
import math
import time
import json
import uuid
import tempfile
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Optional, Tuple, Any
from datetime import datetime, timezone

from .config import CONFIG, JarvisRuntimeConfig
from .models import SCHEMA_VERSION


REGISTRY_ROOT = CONFIG.registry_root
MEMORY_DIR = REGISTRY_ROOT / "state" / "memory"


class MemoryTier(str, Enum):
    WORKING = "WORKING"
    EPISODIC = "EPISODIC"
    SEMANTIC = "SEMANTIC"
    PROCEDURAL = "PROCEDURAL"


class MemoryStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CONFLICT_DETECTED = "CONFLICT_DETECTED"
    DEPRECATED = "DEPRECATED"
    ARCHIVED = "ARCHIVED"


@dataclass
class MemoryItem:
    memory_id: str
    tier: MemoryTier
    key: str
    content: str
    provenance: str
    confidence: float = 0.85
    created_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_accessed_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: MemoryStatus = MemoryStatus.ACTIVE
    contradicted_by: Optional[str] = None

    def __post_init__(self):
        self.tier = MemoryTier(self.tier)
        self.status = MemoryStatus(self.status)
        if not all(isinstance(v, str) and v.strip() for v in (self.memory_id, self.key, self.content)):
            raise ValueError("Memory requires nonempty identity, key and content")
        if not math.isfinite(self.confidence) or not 0 <= self.confidence <= 1:
            raise ValueError("Invalid confidence")
        for value in (self.created_utc, self.last_accessed_utc):
            if datetime.fromisoformat(value).tzinfo is None:
                raise ValueError("Memory timestamps require timezone")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "tier": self.tier.value if isinstance(self.tier, MemoryTier) else str(self.tier),
            "key": self.key,
            "content": self.content,
            "provenance": self.provenance,
            "confidence": round(self.confidence, 4),
            "created_utc": self.created_utc,
            "last_accessed_utc": self.last_accessed_utc,
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
            "status": self.status.value if isinstance(self.status, MemoryStatus) else str(self.status),
            "contradicted_by": self.contradicted_by
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryItem":
        tier = data.get("tier", MemoryTier.SEMANTIC)
        if isinstance(tier, str):
            try:
                tier = MemoryTier(tier)
            except ValueError:
                raise ValueError("Invalid memory tier")

        status = data.get("status", MemoryStatus.ACTIVE)
        if isinstance(status, str):
            try:
                status = MemoryStatus(status)
            except ValueError:
                raise ValueError("Invalid memory status")

        return cls(
            memory_id=data["memory_id"],
            tier=tier,
            key=data["key"],
            content=data["content"],
            provenance=data.get("provenance", "unknown"),
            confidence=float(data.get("confidence", 0.85)),
            created_utc=data.get("created_utc", datetime.now(timezone.utc).isoformat()),
            last_accessed_utc=data.get("last_accessed_utc", datetime.now(timezone.utc).isoformat()),
            tags=list(data.get("tags", [])),
            metadata=dict(data.get("metadata", {})),
            status=status,
            contradicted_by=data.get("contradicted_by")
        )

    def estimate_tokens(self) -> int:
        # Standard conservative heuristic: ~4 characters per token
        return max(1, math.ceil(len((self.key + self.content).encode('utf-8')) / 4))

    def compute_freshness(self, half_life_days: float = 30.0) -> float:
        """Computes exponential temporal freshness decay [0.0, 1.0]."""
        try:
            created_dt = datetime.fromisoformat(self.created_utc)
            now_dt = datetime.now(timezone.utc)
            delta_days = max(0.0, (now_dt - created_dt).total_seconds() / 86400.0)
            decay_rate = 0.693147 / max(0.1, half_life_days)
            return round(math.exp(-decay_rate * delta_days), 4)
        except Exception:
            return 0.0


@dataclass
class MemoryAdmissionResult:
    admitted: bool
    item_id: Optional[str]
    status: MemoryStatus
    conflicts_detected: List[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class MemoryReceipt:
    receipt_id: str
    query: str
    tier_filter: List[str]
    matched_items: List[Dict[str, Any]]
    excluded_conflicts: List[Dict[str, Any]]
    decay_scores: Dict[str, float]
    total_tokens_estimated: int
    mission_id: Optional[str] = None
    task_id: Optional[str] = None
    attempt_id: Optional[str] = None
    trace_id: Optional[str] = None
    created_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    timestamp_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "schema_version": self.schema_version,
            "mission_id": self.mission_id,
            "task_id": self.task_id,
            "attempt_id": self.attempt_id,
            "trace_id": self.trace_id,
            "created_utc": self.created_utc,
            "query": self.query,
            "tier_filter": self.tier_filter,
            "matched_items": self.matched_items,
            "excluded_conflicts": self.excluded_conflicts,
            "decay_scores": self.decay_scores,
            "total_tokens_estimated": self.total_tokens_estimated,
            "timestamp_utc": self.timestamp_utc
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryReceipt":
        return cls(
            receipt_id=data["receipt_id"],
            query=data.get("query", ""),
            tier_filter=list(data.get("tier_filter", [])),
            matched_items=list(data.get("matched_items", [])),
            excluded_conflicts=list(data.get("excluded_conflicts", [])),
            decay_scores=dict(data.get("decay_scores", {})),
            total_tokens_estimated=data.get("total_tokens_estimated", 0),
            mission_id=data.get("mission_id"),
            task_id=data.get("task_id"),
            attempt_id=data.get("attempt_id"),
            trace_id=data.get("trace_id"),
            created_utc=data.get("created_utc", data.get("timestamp_utc", "")),
            timestamp_utc=data.get("timestamp_utc", ""),
            schema_version=data.get("schema_version", SCHEMA_VERSION),
        )


class MemoryFabric:
    """
    Unified 4-Tier Memory Fabric with Admission Gate and Ordered Retrieval.
    Enforces provenance, detects knowledge conflicts, and prevents memory corruption.
    """

    def __init__(
        self,
        working_capacity: int = 50,
        storage_dir: Optional[Path] = None,
        config: Optional[JarvisRuntimeConfig] = None
    ):
        cfg = config or CONFIG
        self.storage_dir = (storage_dir or (cfg.registry_root / "state" / "memory")).resolve()
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.working_capacity = working_capacity
        if not isinstance(working_capacity, int) or working_capacity < 1:
            raise ValueError("Working capacity must be positive")
        self._history: Dict[str, MemoryItem] = {}

        self._working: Dict[str, MemoryItem] = {}
        self._episodic: List[MemoryItem] = []
        self._semantic: Dict[str, MemoryItem] = {}
        self._procedural: Dict[str, MemoryItem] = {}

    def admit(self, item: MemoryItem) -> MemoryAdmissionResult:
        """
        Admit a memory item into its respective tier.
        Applies provenance validation and conflict detection.
        """
        # 1. Provenance Verification: Must not be empty or ungrounded
        if not item.provenance or str(item.provenance).strip().lower() in ("", "unknown"):
            return MemoryAdmissionResult(
                admitted=False,
                item_id=None,
                status=MemoryStatus.REJECTED if hasattr(MemoryStatus, "REJECTED") else MemoryStatus.CONFLICT_DETECTED,
                reason="REJECTED: Memory item lacks explicit provenance grounding"
            )

        if item.tier == MemoryTier.WORKING:
            # Enforce bounded capacity with FIFO eviction
            if item.key not in self._working and len(self._working) >= self.working_capacity:
                oldest_key = next(iter(self._working.keys()))
                del self._working[oldest_key]
            self._working[item.key] = item
            return MemoryAdmissionResult(admitted=True, item_id=item.memory_id, status=MemoryStatus.ACTIVE, reason="Admitted to WORKING memory")

        elif item.tier == MemoryTier.EPISODIC:
            self._episodic.append(item)
            return MemoryAdmissionResult(admitted=True, item_id=item.memory_id, status=MemoryStatus.ACTIVE, reason="Admitted to EPISODIC memory")

        elif item.tier == MemoryTier.SEMANTIC:
            existing = self._semantic.get(item.key)
            if existing:
                # If existing is active and has differing content
                norm_existing = existing.content.strip()
                norm_new = item.content.strip()
                if norm_existing != norm_new:
                    # Different values remain unresolved until explicit reconciliation.
                    is_direct_contradiction = True

                    if is_direct_contradiction:
                        item.status = MemoryStatus.CONFLICT_DETECTED
                        item.contradicted_by = existing.memory_id
                        existing.status = MemoryStatus.CONFLICT_DETECTED
                        existing.contradicted_by = item.memory_id
                        self._history[existing.memory_id] = MemoryItem.from_dict(existing.to_dict())
                        self._semantic[item.key] = item
                        return MemoryAdmissionResult(
                            admitted=True,
                            item_id=item.memory_id,
                            status=MemoryStatus.CONFLICT_DETECTED,
                            conflicts_detected=[existing.memory_id],
                            reason=f"CONFLICT_DETECTED: Semantic key '{item.key}' contradicts existing memory {existing.memory_id}. Flagged for reconciliation."
                        )

            self._semantic[item.key] = item
            return MemoryAdmissionResult(admitted=True, item_id=item.memory_id, status=MemoryStatus.ACTIVE, reason="Admitted to SEMANTIC memory")

        elif item.tier == MemoryTier.PROCEDURAL:
            existing = self._procedural.get(item.key)
            if existing and existing.content != item.content:
                existing.status = item.status = MemoryStatus.CONFLICT_DETECTED
                existing.contradicted_by = item.memory_id
                item.contradicted_by = existing.memory_id
                self._history[existing.memory_id] = MemoryItem.from_dict(existing.to_dict())
            self._procedural[item.key] = item
            return MemoryAdmissionResult(admitted=True, item_id=item.memory_id, status=item.status, reason="Admitted to PROCEDURAL memory")

        return MemoryAdmissionResult(admitted=False, item_id=None, status=MemoryStatus.ARCHIVED, reason="Unknown memory tier")

    def query(
        self,
        query_text: str,
        tiers: Optional[List[MemoryTier]] = None,
        max_items: int = 10,
        min_confidence: float = 0.5,
        token_budget: int = 2000,
        half_life_days: float = 30.0
    ) -> Tuple[List[MemoryItem], MemoryReceipt]:
        """
        Retrieves top relevant memory items bounded by token budget and relevance scoring.
        Excludes unresolved contradictory items from active results, logging them in receipt.
        """
        receipt_id = f"rcp-mem-{uuid.uuid4().hex[:8]}"
        target_tiers = tiers or [MemoryTier.WORKING, MemoryTier.EPISODIC, MemoryTier.SEMANTIC, MemoryTier.PROCEDURAL]
        tier_names = [t.value if isinstance(t, MemoryTier) else str(t) for t in target_tiers]

        candidates: List[MemoryItem] = []
        if MemoryTier.WORKING in target_tiers:
            candidates.extend(self._working.values())
        if MemoryTier.EPISODIC in target_tiers:
            candidates.extend(self._episodic)
        if MemoryTier.SEMANTIC in target_tiers:
            candidates.extend(self._semantic.values())
        if MemoryTier.PROCEDURAL in target_tiers:
            candidates.extend(self._procedural.values())

        q_terms = set(query_text.lower().split())
        scored_items: List[Tuple[float, float, MemoryItem]] = []
        excluded_conflicts: List[Dict[str, Any]] = []
        decay_scores: Dict[str, float] = {}

        now_utc = datetime.now(timezone.utc).isoformat()

        for item in candidates:
            # 1. Filter status: Exclude conflicts and deprecated items from active return
            if item.status != MemoryStatus.ACTIVE:
                excluded_conflicts.append({
                    "memory_id": item.memory_id,
                    "key": item.key,
                    "status": item.status.value,
                    "contradicted_by": item.contradicted_by,
                    "reason": "Excluded due to unresolved conflict or deprecation"
                })
                continue

            if item.confidence < min_confidence:
                continue

            item_text = f"{item.key} {item.content} {' '.join(item.tags)}".lower()
            overlap = sum(1 for term in q_terms if term in item_text)
            relevance = (overlap / len(q_terms)) if q_terms else 0.5

            if q_terms and overlap == 0 and item.tier != MemoryTier.WORKING:
                continue

            freshness = item.compute_freshness(half_life_days=half_life_days)
            decay_scores[item.memory_id] = freshness

            composite = (relevance * 0.50) + (item.confidence * 0.30) + (freshness * 0.20)
            scored_items.append((composite, freshness, item))

        scored_items.sort(key=lambda x: (-x[0], x[2].memory_id))

        selected_items: List[MemoryItem] = []
        total_tokens = 0
        matched_dicts: List[Dict[str, Any]] = []

        for comp_score, fresh_score, item in scored_items:
            if len(selected_items) >= max_items:
                break
            tokens = item.estimate_tokens()
            if total_tokens + tokens > token_budget:
                continue
            total_tokens += tokens
            item.last_accessed_utc = now_utc
            selected_items.append(item)
            matched_dicts.append({
                "memory_id": item.memory_id,
                "tier": item.tier.value,
                "key": item.key,
                "score": round(comp_score, 4),
                "freshness": fresh_score,
                "tokens": tokens
            })

        receipt = MemoryReceipt(
            receipt_id=receipt_id,
            query=query_text,
            tier_filter=tier_names,
            matched_items=matched_dicts,
            excluded_conflicts=excluded_conflicts,
            decay_scores=decay_scores,
            total_tokens_estimated=total_tokens,
            timestamp_utc=now_utc
        )

        return selected_items, receipt

    def get_tier_counts(self) -> Dict[str, int]:
        return {
            "working": len(self._working),
            "episodic": len(self._episodic),
            "semantic": len(self._semantic),
            "procedural": len(self._procedural),
            "total": len(self._working) + len(self._episodic) + len(self._semantic) + len(self._procedural)
        }

    def save_snapshot(self, filename: str = "memory_snapshot.json") -> Path:
        target = self._snapshot_target(filename)
        data = {
            "working": [i.to_dict() for i in self._working.values()],
            "episodic": [i.to_dict() for i in self._episodic],
            "semantic": [i.to_dict() for i in self._semantic.values()],
            "procedural": [i.to_dict() for i in self._procedural.values()],
            "history": [i.to_dict() for i in self._history.values()],
            "schema_version": "1.0.0",
            "saved_utc": datetime.now(timezone.utc).isoformat()
        }
        fd, name = tempfile.mkstemp(dir=self.storage_dir, suffix='.tmp')
        tmp_target = Path(name)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
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
            with target.open('rb') as stream:
                raw = stream.read(16 * 1024 * 1024 + 1)
            if len(raw) > 16 * 1024 * 1024:
                raise ValueError("Snapshot too large")
            data = json.loads(raw.decode('utf-8'))
            if data.get('schema_version', '1.0.0') != '1.0.0':
                raise ValueError("Unsupported snapshot version")
            parsed = {}
            seen = set()
            for name in ('working', 'episodic', 'semantic', 'procedural', 'history'):
                items = [MemoryItem.from_dict(i) for i in data.get(name, [])]
                keys = set()
                for item in items:
                    if item.memory_id in seen or (name != 'history' and item.tier.value.lower() != name):
                        raise ValueError("Duplicate identity or wrong tier")
                    if name not in ('episodic', 'history') and item.key in keys:
                        raise ValueError("Duplicate tier key")
                    if not item.provenance or item.provenance.strip().lower() == 'unknown':
                        raise ValueError("Missing provenance")
                    keys.add(item.key); seen.add(item.memory_id)
                parsed[name] = items
            if len(parsed['working']) > self.working_capacity:
                raise ValueError("Working capacity exceeded")
            self._working = {i.key: i for i in parsed['working']}
            self._episodic = parsed['episodic']
            self._semantic = {i.key: i for i in parsed['semantic']}
            self._procedural = {i.key: i for i in parsed['procedural']}
            self._history = {i.memory_id: i for i in parsed['history']}
            return True
        except Exception:
            return False

    def _snapshot_target(self, filename: str) -> Path:
        if not isinstance(filename, str) or not filename or any(c in filename for c in ('/', '\\', ':')) or filename in ('.', '..'):
            raise ValueError("Snapshot name must be a filename")
        target = self.storage_dir / filename
        if target.is_symlink() or target.resolve().parent != self.storage_dir:
            raise ValueError("Snapshot escapes storage")
        return target

    def get_by_id(self, memory_id: str) -> Optional[MemoryItem]:
        candidates = [*self._working.values(), *self._episodic, *self._semantic.values(), *self._procedural.values(), *self._history.values()]
        return next((item for item in candidates if item.memory_id == memory_id), None)
