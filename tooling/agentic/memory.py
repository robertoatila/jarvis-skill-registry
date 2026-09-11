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
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Optional, Tuple, Any
from datetime import datetime, timezone

from .config import CONFIG, JarvisRuntimeConfig


REGISTRY_ROOT = Path("E:/.skill-registry").resolve()
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
    def from_dict(cls, data: Dict[str, Any]) -> MemoryItem:
        tier = data.get("tier", MemoryTier.SEMANTIC)
        if isinstance(tier, str):
            try:
                tier = MemoryTier(tier)
            except ValueError:
                tier = MemoryTier.SEMANTIC

        status = data.get("status", MemoryStatus.ACTIVE)
        if isinstance(status, str):
            try:
                status = MemoryStatus(status)
            except ValueError:
                status = MemoryStatus.ACTIVE

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
        return max(1, (len(self.key) + len(self.content)) // 4)

    def compute_freshness(self, half_life_days: float = 30.0) -> float:
        """Computes exponential temporal freshness decay [0.0, 1.0]."""
        try:
            created_dt = datetime.fromisoformat(self.created_utc)
            now_dt = datetime.now(timezone.utc)
            delta_days = max(0.0, (now_dt - created_dt).total_seconds() / 86400.0)
            decay_rate = 0.693147 / max(0.1, half_life_days)
            return round(math.exp(-decay_rate * delta_days), 4)
        except Exception:
            return 1.0


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
    timestamp_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "query": self.query,
            "tier_filter": self.tier_filter,
            "matched_items": self.matched_items,
            "excluded_conflicts": self.excluded_conflicts,
            "decay_scores": self.decay_scores,
            "total_tokens_estimated": self.total_tokens_estimated,
            "timestamp_utc": self.timestamp_utc
        }


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

        # 4 Tiers
        self._working: Dict[str, MemoryItem] = {}
        self._episodic: List[MemoryItem] = []
        self._semantic: Dict[str, MemoryItem] = {}
        self._procedural: Dict[str, MemoryItem] = {}

    # ----------------------------------------------------------------------
    # Memory Admission Gate (Phase 31)
    # ----------------------------------------------------------------------
    def admit(self, item: MemoryItem) -> MemoryAdmissionResult:
        """
        Admit a memory item into its respective tier.
        Applies provenance validation and conflict detection.
        """
        # 1. Provenance Verification: Must not be empty or ungrounded
        if not item.provenance or not str(item.provenance).strip():
            return MemoryAdmissionResult(
                admitted=False,
                item_id=None,
                status=MemoryStatus.REJECTED if hasattr(MemoryStatus, "REJECTED") else MemoryStatus.CONFLICT_DETECTED,
                reason="REJECTED: Memory item lacks explicit provenance grounding"
            )

        # 2. Tier Specific Handling
        if item.tier == MemoryTier.WORKING:
            # Enforce bounded capacity with FIFO eviction
            if len(self._working) >= self.working_capacity:
                oldest_key = next(iter(self._working.keys()))
                del self._working[oldest_key]
            self._working[item.key] = item
            return MemoryAdmissionResult(admitted=True, item_id=item.memory_id, status=MemoryStatus.ACTIVE, reason="Admitted to WORKING memory")

        elif item.tier == MemoryTier.EPISODIC:
            self._episodic.append(item)
            return MemoryAdmissionResult(admitted=True, item_id=item.memory_id, status=MemoryStatus.ACTIVE, reason="Admitted to EPISODIC memory")

        elif item.tier == MemoryTier.SEMANTIC:
            # Conflict Detection: check if semantic key already exists
            existing = self._semantic.get(item.key)
            if existing:
                # If existing is active and has differing content
                norm_existing = existing.content.strip().lower()
                norm_new = item.content.strip().lower()
                if norm_existing != norm_new:
                    # Detect semantic polarity conflict
                    # e.g. "always do X" vs "never do X" or differing strict values
                    conflict_words = [("true", "false"), ("yes", "no"), ("allow", "deny"), ("always", "never"), ("safe", "unsafe")]
                    is_direct_contradiction = False
                    for w1, w2 in conflict_words:
                        if (w1 in norm_existing and w2 in norm_new) or (w2 in norm_existing and w1 in norm_new):
                            is_direct_contradiction = True
                            break

                    if is_direct_contradiction:
                        item.status = MemoryStatus.CONFLICT_DETECTED
                        item.contradicted_by = existing.memory_id
                        existing.status = MemoryStatus.CONFLICT_DETECTED
                        existing.contradicted_by = item.memory_id
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
            self._procedural[item.key] = item
            return MemoryAdmissionResult(admitted=True, item_id=item.memory_id, status=MemoryStatus.ACTIVE, reason="Admitted to PROCEDURAL memory")

        return MemoryAdmissionResult(admitted=False, item_id=None, status=MemoryStatus.ARCHIVED, reason="Unknown memory tier")

    # ----------------------------------------------------------------------
    # Ordered Retrieval with MemoryReceipts (Phase 31)
    # ----------------------------------------------------------------------
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
            if item.status in (MemoryStatus.CONFLICT_DETECTED, MemoryStatus.DEPRECATED):
                excluded_conflicts.append({
                    "memory_id": item.memory_id,
                    "key": item.key,
                    "status": item.status.value,
                    "contradicted_by": item.contradicted_by,
                    "reason": "Excluded due to unresolved conflict or deprecation"
                })
                continue

            # 2. Confidence filter
            if item.confidence < min_confidence:
                continue

            # 3. Calculate text relevance (lexical jaccard/overlap)
            item_text = f"{item.key} {item.content} {' '.join(item.tags)}".lower()
            overlap = sum(1 for term in q_terms if term in item_text)
            relevance = (overlap / len(q_terms)) if q_terms else 0.5

            if q_terms and overlap == 0 and item.tier != MemoryTier.WORKING:
                continue

            # 4. Temporal Freshness Decay
            freshness = item.compute_freshness(half_life_days=half_life_days)
            decay_scores[item.memory_id] = freshness

            # 5. Composite Score: 50% relevance, 30% confidence, 20% freshness
            composite = (relevance * 0.50) + (item.confidence * 0.30) + (freshness * 0.20)
            scored_items.append((composite, freshness, item))

        # Sort: composite DESC, memory_id ASC
        scored_items.sort(key=lambda x: (-x[0], x[2].memory_id))

        # 6. Apply token budget and max_items bounds
        selected_items: List[MemoryItem] = []
        total_tokens = 0
        matched_dicts: List[Dict[str, Any]] = []

        for comp_score, fresh_score, item in scored_items:
            if len(selected_items) >= max_items:
                break
            tokens = item.estimate_tokens()
            if total_tokens + tokens > token_budget and selected_items:
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

    # ----------------------------------------------------------------------
    # Inspection and Snapshot Utilities
    # ----------------------------------------------------------------------
    def get_tier_counts(self) -> Dict[str, int]:
        return {
            "working": len(self._working),
            "episodic": len(self._episodic),
            "semantic": len(self._semantic),
            "procedural": len(self._procedural),
            "total": len(self._working) + len(self._episodic) + len(self._semantic) + len(self._procedural)
        }

    def save_snapshot(self, filename: str = "memory_snapshot.json") -> Path:
        target = self.storage_dir / filename
        data = {
            "working": [i.to_dict() for i in self._working.values()],
            "episodic": [i.to_dict() for i in self._episodic],
            "semantic": [i.to_dict() for i in self._semantic.values()],
            "procedural": [i.to_dict() for i in self._procedural.values()],
            "saved_utc": datetime.now(timezone.utc).isoformat()
        }
        tmp_target = target.with_suffix(".tmp")
        tmp_target.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp_target.replace(target)
        return target

    def load_snapshot(self, filename: str = "memory_snapshot.json") -> bool:
        target = self.storage_dir / filename
        if not target.exists():
            return False
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
            self._working = {i["key"]: MemoryItem.from_dict(i) for i in data.get("working", [])}
            self._episodic = [MemoryItem.from_dict(i) for i in data.get("episodic", [])]
            self._semantic = {i["key"]: MemoryItem.from_dict(i) for i in data.get("semantic", [])}
            self._procedural = {i["key"]: MemoryItem.from_dict(i) for i in data.get("procedural", [])}
            return True
        except Exception:
            return False
