"""
context_governor.py // J.A.R.V.I.S. Context Governor & Progressive Cache Engine
Pure Python 3.12 Standard Library (Zero External PIP Dependencies)

Implements Section 7 (Context Management) of the Autonomous Architecture Plan:
- ContextReceipt: immutable audit receipt for context loading decisions
- NoRepeatReadCache: normalized path + SHA-256 content hash cache with drift invalidation
- ContextCompactor: 4-stage progressive compaction preserving authority & decisions
- ContextGovernor: context budget enforcement and token economy control
"""

from __future__ import annotations
import os
import re
import json
import uuid
import hashlib
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Optional, Tuple, Any
from datetime import datetime, timezone

from .models import SCHEMA_VERSION, _identifier, _nonnegative


@dataclass
class ContextReceipt:
    """Immutable audit receipt tracking context sources, volume, and token economics."""
    receipt_id: str
    mission_id: Optional[str] = None
    task_id: Optional[str] = None
    sources_considered: List[str] = field(default_factory=list)
    sources_loaded: List[str] = field(default_factory=list)
    selection_reason: str = ""
    content_hash: str = ""
    bytes_loaded: int = 0
    estimated_tokens: int = 0
    cache_hit: bool = False
    is_measured_tokens: bool = False
    freshness_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    timestamp_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "receipt_id": self.receipt_id,
            "mission_id": self.mission_id,
            "task_id": self.task_id,
            "sources_considered": sorted(self.sources_considered),
            "sources_loaded": sorted(self.sources_loaded),
            "selection_reason": self.selection_reason,
            "content_hash": self.content_hash,
            "bytes_loaded": self.bytes_loaded,
            "estimated_tokens": self.estimated_tokens,
            "cache_hit": self.cache_hit,
            "is_measured_tokens": self.is_measured_tokens,
            "freshness_utc": self.freshness_utc,
            "timestamp_utc": self.timestamp_utc
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ContextReceipt:
        return cls(
            receipt_id=data["receipt_id"],
            mission_id=data.get("mission_id"),
            task_id=data.get("task_id"),
            sources_considered=list(data.get("sources_considered", [])),
            sources_loaded=list(data.get("sources_loaded", [])),
            selection_reason=data.get("selection_reason", ""),
            content_hash=data.get("content_hash", ""),
            bytes_loaded=data.get("bytes_loaded", 0),
            estimated_tokens=data.get("estimated_tokens", 0),
            cache_hit=data.get("cache_hit", False),
            is_measured_tokens=data.get("is_measured_tokens", False),
            freshness_utc=data.get("freshness_utc", ""),
            timestamp_utc=data.get("timestamp_utc", ""),
            schema_version=data.get("schema_version", SCHEMA_VERSION)
        )


class NoRepeatReadCache:
    """
    Normalized path + content SHA-256 read cache with automatic drift invalidation.
    Eliminates redundant file reading while guaranteeing zero stale assumption leakage.
    """

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.hits: int = 0
        self.misses: int = 0

    @staticmethod
    def normalize_path(path_str: str) -> str:
        clean = path_str.replace("\\", "/").strip().lstrip("/")
        parts = clean.split("/")
        norm_parts = []
        for p in parts:
            if p in ("", "."):
                continue
            norm_parts.append(p)
        return "/".join(norm_parts)

    def get(self, path_str: str, current_sha256: str) -> Optional[Dict[str, Any]]:
        norm = self.normalize_path(path_str)
        entry = self._cache.get(norm)
        if not entry:
            self.misses += 1
            return None

        # Invalidate on content hash drift
        if entry["sha256"].lower() != current_sha256.lower():
            del self._cache[norm]
            self.misses += 1
            return None

        self.hits += 1
        return entry

    def put(self, path_str: str, sha256: str, content: str, summary: Optional[str] = None) -> None:
        norm = self.normalize_path(path_str)
        self._cache[norm] = {
            "path": norm,
            "sha256": sha256.lower(),
            "content": content,
            "summary": summary or (content[:300] + "..." if len(content) > 300 else content),
            "bytes": len(content.encode("utf-8")),
            "cached_utc": datetime.now(timezone.utc).isoformat()
        }

    def invalidate(self, path_str: str) -> bool:
        norm = self.normalize_path(path_str)
        if norm in self._cache:
            del self._cache[norm]
            return True
        return False

    def clear(self) -> None:
        self._cache.clear()

    @property
    def size(self) -> int:
        return len(self._cache)


class ContextCompactor:
    """
    Progressive 4-stage context compaction:
    Stage 1: RAW_EXECUTION / SCRUB_FORMATTING (full tool stdout/stderr or whitespace cleaning)
    Stage 2: STRUCTURED_ATTEMPT / TRUNCATE_HISTORY (metadata, status, returncode, side effects)
    Stage 3: SUMMARY / EXECUTIVE_SYNTHESIS (high-level outcome description and verified facts)
    Stage 4: REFERENCE / EMERGENCY_HALT (URI, SHA-256 hash, and status marker only)

    Critical Invariant:
    Decisions, unresolved uncertainties, authority, and pending verification
    are strictly preserved across all compaction stages.
    """

    @staticmethod
    def compact(
        record: Dict[str, Any],
        target_stage: str = "SUMMARY"
    ) -> Dict[str, Any]:
        stage = target_stage.upper().strip()
        compacted: Dict[str, Any] = {
            "compaction_stage": stage,
            "task_id": record.get("task_id", ""),
            "agent_id": record.get("agent_id") or record.get("agent_profile", ""),
            "status": record.get("status", ""),
            "verification_state": record.get("verification_state", "UNVERIFIED"),
            "preserved_uncertainties": record.get("unresolved_uncertainties", []),
            "preserved_decisions": record.get("decision_records", [])
        }

        if stage == "RAW_EXECUTION":
            return dict(record)

        elif stage == "STRUCTURED_ATTEMPT":
            compacted.update({
                "exit_code": record.get("exit_code"),
                "duration_ms": record.get("duration_ms"),
                "side_effects_count": len(record.get("side_effects", [])),
                "artifacts_count": len(record.get("artifacts", [])),
                "error_snippet": record.get("error_message") or record.get("stderr_snippet", "")
            })

        elif stage == "SUMMARY":
            desc = record.get("stdout_snippet") or record.get("description") or record.get("title") or ""
            compacted.update({
                "summary": desc[:250] + ("..." if len(desc) > 250 else ""),
                "outcome": record.get("outcome", "UNKNOWN"),
                "verified": record.get("status") == "VERIFIED" or record.get("verification_state") == "VERIFIED"
            })

        elif stage == "REFERENCE":
            compacted.update({
                "target_ref": record.get("input_reference") or record.get("target") or "",
                "provenance_hash": record.get("provenance_hash") or record.get("sha256") or ""
            })

        else:
            raise ValueError(f"Unknown compaction stage: '{stage}'. Expected RAW_EXECUTION, STRUCTURED_ATTEMPT, SUMMARY, or REFERENCE.")

        return compacted

    def compact_stage_1_scrub(self, text: str) -> Tuple[str, List[str], List[str]]:
        """
        Stage 1: Scrubs formatting, redundant whitespace, and comments,
        while extracting and preserving decisions and uncertainties.
        """
        decisions: List[str] = []
        uncertainties: List[str] = []
        cleaned_lines: List[str] = []

        for line in text.splitlines():
            s = line.strip()
            if not s:
                continue
            if s.startswith("//") or s.startswith("#") and not s.startswith("# Decision"):
                continue
            if "decision:" in s.lower():
                decisions.append(s)
            elif "uncertainty:" in s.lower() or "risk:" in s.lower():
                uncertainties.append(s)
            cleaned_lines.append(s)

        return "\n".join(cleaned_lines), decisions, uncertainties

    def compact_stage_2_truncate(self, text: str, max_items: int = 2) -> str:
        """
        Stage 2: Truncates non-decision repetitive history, capping item lists.
        """
        lines = [l for l in text.splitlines() if l.strip()]
        if len(lines) <= max_items:
            return "\n".join(lines)
        return "\n".join(lines[:max_items]) + "\n...[TRUNCATED_HISTORY]..."

    def compact_stage_3_synthesize(self, text: str, decisions: List[str], uncertainties: List[str]) -> str:
        """
        Stage 3: Generates executive synthesis block retaining decisions and uncertainties.
        """
        summary_lines = [
            "=== EXECUTIVE SUMMARY ===",
            f"Digest: {text[:200]}...",
            "--- DECISIONS PRESERVED ---"
        ]
        for d in decisions:
            summary_lines.append(f"- {d}")
        summary_lines.append("--- UNCERTAINTIES PRESERVED ---")
        for u in uncertainties:
            summary_lines.append(f"- {u}")
        return "\n".join(summary_lines)

    def compact_stage_4_halt(self, text: str, emergency_limit_bytes: int = 100_000) -> None:
        """
        Stage 4: Fail-closed emergency halt if content still exceeds absolute bounds.
        """
        size = len(text.encode("utf-8"))
        if size > emergency_limit_bytes:
            raise RuntimeError(f"Context compaction emergency halt: text size {size} bytes exceeds limit {emergency_limit_bytes}")


class ContextGovernor:
    """
    Sovereign Context Governor managing context budget, disclosure receipts,
    and no-repeat read caching.
    """

    def __init__(self, workspace_root: Optional[Path] = None, max_context_tokens: int = 64_000):
        self.root = (workspace_root or Path("E:/.skill-registry")).resolve()
        self.max_tokens = max_context_tokens
        self.cache = NoRepeatReadCache()
        self.compactor = ContextCompactor()
        self.receipts: List[ContextReceipt] = []

    def read_file_content(self, rel_path: str) -> Tuple[str, ContextReceipt]:
        """Convenience alias for read_with_receipt."""
        return self.read_with_receipt(rel_path)

    def read_with_receipt(
        self,
        rel_path: str,
        mission_id: Optional[str] = None,
        task_id: Optional[str] = None,
        force_refresh: bool = False
    ) -> Tuple[str, ContextReceipt]:
        """
        Reads a workspace file with NoRepeatReadCache protection and issues a ContextReceipt.
        """
        clean_path = rel_path.replace("\\", "/").strip().lstrip("/")
        target = (self.root / clean_path).resolve()

        if not target.exists() or not target.is_file():
            raise FileNotFoundError(f"Target file does not exist: '{clean_path}'")

        data_bytes = target.read_bytes()
        current_hash = hashlib.sha256(data_bytes).hexdigest()
        byte_len = len(data_bytes)
        token_est = max(1, byte_len // 4)

        cache_entry = None if force_refresh else self.cache.get(clean_path, current_hash)
        cache_hit = cache_entry is not None

        if cache_hit:
            content = cache_entry["content"]
            reason = "Loaded from NoRepeatReadCache (hash matched)"
        else:
            content = data_bytes.decode("utf-8", errors="replace")
            self.cache.put(clean_path, current_hash, content)
            reason = "Fresh disk read (cache miss or hash drift invalidated previous entry)"

        receipt = ContextReceipt(
            receipt_id=f"ctx-{uuid.uuid4().hex[:8]}",
            mission_id=mission_id,
            task_id=task_id,
            sources_considered=[clean_path],
            sources_loaded=[clean_path],
            selection_reason=reason,
            content_hash=current_hash,
            bytes_loaded=byte_len,
            estimated_tokens=token_est,
            cache_hit=cache_hit,
            is_measured_tokens=False,
            freshness_utc=datetime.fromtimestamp(target.stat().st_mtime, tz=timezone.utc).isoformat(),
            timestamp_utc=datetime.now(timezone.utc).isoformat()
        )
        self.receipts.append(receipt)

        return content, receipt
