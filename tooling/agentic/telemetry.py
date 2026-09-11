"""
telemetry.py // J.A.R.V.I.S. Agent Telemetry, Metrics, and Spans Engine
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
Enforces:
- Structured execution spans (timing, tokens, tool calls, evidence)
- ACID append-only JSONL ledger in state/telemetry/agent_spans.jsonl
- Real-time metrics aggregation across agents and skills
"""

from __future__ import annotations
import json
import os
import threading
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Optional, Any
from datetime import datetime, timezone


REGISTRY_ROOT = Path("E:/.skill-registry").resolve()
TELEMETRY_DIR = REGISTRY_ROOT / "state" / "telemetry"
TELEMETRY_SPANS_FILE = TELEMETRY_DIR / "agent_spans.jsonl"


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def to_dict(self) -> Dict[str, int]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TokenUsage:
        return cls(
            prompt_tokens=data.get("prompt_tokens", 0),
            completion_tokens=data.get("completion_tokens", 0),
            total_tokens=data.get("total_tokens", 0)
        )


@dataclass
class Span:
    span_id: str
    mission_id: str
    task_id: str
    agent_id: str
    skill_id: str = "general"
    wave_index: int = 0
    status: str = "RUNNING"  # RUNNING, SUCCESS, FAIL, CANCELLED
    start_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    end_utc: Optional[str] = None
    duration_ms: int = 0
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    tool_calls_count: int = 0
    error_message: Optional[str] = None
    evidence_summary: Dict[str, Any] = field(default_factory=dict)
    _start_perf: float = field(default_factory=time.perf_counter, repr=False)

    def finish(
        self,
        status: str = "SUCCESS",
        token_usage: Optional[TokenUsage] = None,
        tool_calls_count: Optional[int] = None,
        error_message: Optional[str] = None,
        evidence_summary: Optional[Dict[str, Any]] = None
    ) -> Span:
        self.end_utc = datetime.now(timezone.utc).isoformat()
        self.duration_ms = int((time.perf_counter() - self._start_perf) * 1000)
        self.status = status
        if token_usage:
            self.token_usage = token_usage
        if tool_calls_count is not None:
            self.tool_calls_count = tool_calls_count
        if error_message:
            self.error_message = error_message
        if evidence_summary:
            self.evidence_summary = evidence_summary
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "span_id": self.span_id,
            "mission_id": self.mission_id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "skill_id": self.skill_id,
            "wave_index": self.wave_index,
            "status": self.status,
            "start_utc": self.start_utc,
            "end_utc": self.end_utc,
            "duration_ms": self.duration_ms,
            "token_usage": self.token_usage.to_dict(),
            "tool_calls_count": self.tool_calls_count,
            "error_message": self.error_message,
            "evidence_summary": self.evidence_summary
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Span:
        t_usage = TokenUsage.from_dict(data.get("token_usage", {}))
        return cls(
            span_id=data["span_id"],
            mission_id=data["mission_id"],
            task_id=data["task_id"],
            agent_id=data["agent_id"],
            skill_id=data.get("skill_id", "general"),
            wave_index=data.get("wave_index", 0),
            status=data.get("status", "SUCCESS"),
            start_utc=data.get("start_utc", datetime.now(timezone.utc).isoformat()),
            end_utc=data.get("end_utc"),
            duration_ms=data.get("duration_ms", 0),
            token_usage=t_usage,
            tool_calls_count=data.get("tool_calls_count", 0),
            error_message=data.get("error_message"),
            evidence_summary=data.get("evidence_summary", {})
        )


class TelemetryCollector:
    """
    Thread-safe collector and aggregator for Agent Telemetry Spans.
    Appends to state/telemetry/agent_spans.jsonl.
    """

    def __init__(self, ledger_file: Path = TELEMETRY_SPANS_FILE):
        self.ledger_file = ledger_file
        self._lock = threading.Lock()
        self._active_spans: Dict[str, Span] = {}
        self._recent_spans: List[Span] = []
        self._ensure_ledger()

    def _ensure_ledger(self) -> None:
        self.ledger_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.ledger_file.exists():
            self.ledger_file.write_text("", encoding="utf-8")

    def start_span(
        self,
        mission_id: str,
        task_id: str,
        agent_id: str,
        skill_id: str = "general",
        wave_index: int = 0
    ) -> Span:
        span_id = f"span-{int(time.time() * 1000)}-{task_id[:8]}"
        span = Span(
            span_id=span_id,
            mission_id=mission_id,
            task_id=task_id,
            agent_id=agent_id,
            skill_id=skill_id,
            wave_index=wave_index,
            status="RUNNING"
        )
        with self._lock:
            self._active_spans[span_id] = span
        return span

    def finish_span(
        self,
        span_id: str,
        status: str = "SUCCESS",
        token_usage: Optional[TokenUsage] = None,
        tool_calls_count: int = 0,
        error_message: Optional[str] = None,
        evidence_summary: Optional[Dict[str, Any]] = None
    ) -> Optional[Span]:
        with self._lock:
            span = self._active_spans.pop(span_id, None)
        if not span:
            return None

        span.finish(
            status=status,
            token_usage=token_usage,
            tool_calls_count=tool_calls_count,
            error_message=error_message,
            evidence_summary=evidence_summary
        )

        self._record_to_ledger(span)
        return span

    def _record_to_ledger(self, span: Span) -> None:
        line = json.dumps(span.to_dict(), ensure_ascii=False)
        with self._lock:
            self._recent_spans.append(span)
            if len(self._recent_spans) > 200:
                self._recent_spans.pop(0)

            try:
                with open(self.ledger_file, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except Exception as e:
                print(f"[JARVIS TELEMETRY ERROR] Failed writing span to ledger: {e}")

    def record_span(self, span: Span) -> None:
        """Directly records a completed Span to the append-only ledger."""
        self._record_to_ledger(span)

    def get_recent_spans(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            if self._recent_spans:
                return [s.to_dict() for s in reversed(self._recent_spans[-limit:])]

        # Read from file if cache is empty
        if not self.ledger_file.exists():
            return []
        try:
            lines = [l.strip() for l in self.ledger_file.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
            records = []
            for line in reversed(lines[-limit:]):
                try:
                    records.append(json.loads(line))
                except Exception:
                    continue
            return records
        except Exception:
            return []

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Calculates consolidated metrics from recorded spans."""
        spans_data = self.get_recent_spans(limit=500)

        total_spans = len(spans_data)
        if total_spans == 0:
            return {
                "total_spans": 0,
                "success_rate": 100.0,
                "avg_duration_ms": 0.0,
                "total_tokens": 0,
                "by_agent": {},
                "by_skill": {}
            }

        successes = 0
        total_duration = 0
        total_tokens = 0
        agent_counts: Dict[str, Dict[str, Any]] = {}
        skill_counts: Dict[str, Dict[str, Any]] = {}

        for s in spans_data:
            st = s.get("status")
            if st == "SUCCESS":
                successes += 1
            dur = s.get("duration_ms", 0)
            total_duration += dur
            tok = s.get("token_usage", {}).get("total_tokens", 0)
            total_tokens += tok

            # Agent aggregation
            ag = s.get("agent_id", "unknown")
            if ag not in agent_counts:
                agent_counts[ag] = {"total": 0, "success": 0, "total_duration_ms": 0}
            agent_counts[ag]["total"] += 1
            if st == "SUCCESS":
                agent_counts[ag]["success"] += 1
            agent_counts[ag]["total_duration_ms"] += dur

            # Skill aggregation
            sk = s.get("skill_id", "unknown")
            if sk not in skill_counts:
                skill_counts[sk] = {"total": 0, "success": 0, "total_duration_ms": 0}
            skill_counts[sk]["total"] += 1
            if st == "SUCCESS":
                skill_counts[sk]["success"] += 1
            skill_counts[sk]["total_duration_ms"] += dur

        return {
            "total_spans": total_spans,
            "success_rate": round((successes / total_spans) * 100.0, 2),
            "avg_duration_ms": round(total_duration / total_spans, 2),
            "total_tokens": total_tokens,
            "by_agent": agent_counts,
            "by_skill": skill_counts
        }


# Global singleton instance
TELEMETRY = TelemetryCollector()
