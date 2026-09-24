"""Operational projection for the J.A.R.V.I.S. second-brain cockpit.

This module reads authoritative mission state, persisted approval requests and the
existing receipt ledger. It exposes only a bounded, reasoning-free projection
for visualization. It never mutates mission state and never grants authority.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from .observability import (
    ReceiptLedger,
    ReceiptLedgerError,
    TimelineProjectionError,
    project_mission_timeline,
)

_ACTIVE_MISSION_STATUSES = {"PENDING", "PLANNING", "SCHEDULED", "RUNNING", "VERIFYING"}
_TERMINAL_TASK_STATUSES = {"VERIFIED", "FAILED", "CANCELLED", "SKIPPED"}
_WAITING_APPROVAL_STATUSES = {"REQUESTED", "PENDING_ACK"}
_BLOCKED_APPROVAL_STATUSES = {"DENIED", "EXPIRED"}
_RESOLVED_APPROVAL_STATUSES = {"APPROVED", "EXECUTED"}


def _as_text(value: Any, fallback: str = "") -> str:
    if isinstance(value, str):
        value = value.strip()
        if value:
            return value
    return fallback


def _safe_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _iso_sort_key(value: Any) -> Tuple[int, str]:
    text = _as_text(value)
    if not text:
        return (0, "")
    try:
        normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            return (0, text)
        return (1, parsed.astimezone(timezone.utc).isoformat())
    except ValueError:
        return (0, text)


def _latest_approval(
    approvals: Iterable[Mapping[str, Any]],
    mission_id: str,
    task_id: str,
) -> Optional[Mapping[str, Any]]:
    matches = []
    for item in approvals:
        if _as_text(item.get("task_id")) != task_id:
            continue
        context = item.get("action_context")
        if not isinstance(context, Mapping) or _as_text(context.get("mission_id")) != mission_id:
            continue
        matches.append(item)
    if not matches:
        return None
    return max(matches, key=lambda item: _iso_sort_key(item.get("requested_utc")))


def _effective_approval_status(
    task: Mapping[str, Any],
    approval: Optional[Mapping[str, Any]],
) -> str:
    status = _as_text(
        approval.get("status") if approval else None,
        _as_text(task.get("approval_status"), "NOT_REQUIRED"),
    ).upper()
    if approval is not None and status in _WAITING_APPROVAL_STATUSES:
        expires_utc = _as_text(approval.get("expires_utc"))
        if expires_utc:
            try:
                normalized = (
                    expires_utc[:-1] + "+00:00"
                    if expires_utc.endswith("Z")
                    else expires_utc
                )
                expires = datetime.fromisoformat(normalized)
                if expires.tzinfo is not None and expires.utcoffset() is not None:
                    if datetime.now(timezone.utc) > expires.astimezone(timezone.utc):
                        return "EXPIRED"
            except ValueError:
                return "EXPIRED"
    return status


def _gate_state(
    task: Mapping[str, Any],
    approval: Optional[Mapping[str, Any]],
    approval_status: Optional[str] = None,
) -> str:
    approval_status = approval_status or _effective_approval_status(task, approval)
    result = task.get("execution_result")
    approval_required = isinstance(result, Mapping) and result.get("approval_required") is True

    if approval_status in _WAITING_APPROVAL_STATUSES or (
        approval_required
        and approval_status not in _RESOLVED_APPROVAL_STATUSES
        and approval_status not in _BLOCKED_APPROVAL_STATUSES
    ):
        return "WAITING_HUMAN"
    if approval_status in _BLOCKED_APPROVAL_STATUSES:
        return "BLOCKED"
    if approval_status in _RESOLVED_APPROVAL_STATUSES:
        return "RESOLVED"
    return "NONE"


def _handoff_state(source: Mapping[str, Any], target: Mapping[str, Any], target_gate: str) -> str:
    source_status = _as_text(source.get("status"), "UNKNOWN").upper()
    target_status = _as_text(target.get("status"), "UNKNOWN").upper()
    if target_gate == "WAITING_HUMAN":
        return "WAITING_HUMAN"
    if target_gate == "BLOCKED":
        return "BLOCKED"
    if target_status == "VERIFIED":
        return "COMPLETED"
    if target_status in {"RUNNING", "EXECUTED"}:
        return "ACTIVE"
    if source_status == "VERIFIED" and target_status in {"PENDING", "READY"}:
        return "READY"
    if source_status in {"FAILED", "CANCELLED", "SKIPPED"}:
        return "BLOCKED"
    return "PLANNED"


class SecondBrainOperationsBuilder:
    """Build a read-only operational graph from persisted runtime evidence."""

    def __init__(
        self,
        missions_dir: Path,
        approvals_dir: Path,
        receipts_dir: Path,
        *,
        max_missions: int = 8,
    ):
        self.missions_dir = Path(missions_dir)
        self.approvals_dir = Path(approvals_dir)
        self.receipts_dir = Path(receipts_dir)
        self.max_missions = max(1, min(int(max_missions), 20))

    def _approvals(self) -> List[Dict[str, Any]]:
        if not self.approvals_dir.exists():
            return []
        approvals: List[Dict[str, Any]] = []
        for path in sorted(self.approvals_dir.glob("app-*.json")):
            item = _safe_json(path)
            if item is not None:
                approvals.append(item)
        return approvals

    def _active_mission_records(self) -> List[Dict[str, Any]]:
        if not self.missions_dir.exists():
            return []
        records: List[Dict[str, Any]] = []
        for path in sorted(self.missions_dir.glob("*.json")):
            record = _safe_json(path)
            if record is None:
                continue
            status = _as_text(record.get("status")).upper()
            if status not in _ACTIVE_MISSION_STATUSES:
                continue
            mission_id = _as_text(record.get("mission_id"), path.stem)
            if not mission_id:
                continue
            records.append(record)
        records.sort(
            key=lambda item: _iso_sort_key(item.get("created_utc")),
            reverse=True,
        )
        return records[: self.max_missions]

    @staticmethod
    def _event_projection(timeline) -> Dict[str, Any]:
        counts: Counter[str] = Counter()
        by_task: Dict[str, Dict[str, Any]] = defaultdict(dict)
        last_event_utc = None

        for event in timeline.events:
            counts[event.event_type] += 1
            last_event_utc = event.created_utc
            if not event.task_id:
                continue
            task_state = by_task[event.task_id]
            if event.event_type == "DECISION":
                dtype = _as_text(event.data.get("decision_type")).lower()
                selected = _as_text(event.data.get("selected_candidate"))
                if dtype == "agent_selection" and selected:
                    task_state["selected_agent"] = selected
            elif event.event_type == "EXECUTION":
                task_state["execution_state"] = _as_text(
                    event.data.get("execution_state"),
                    "UNKNOWN",
                )
            elif event.event_type == "VERIFICATION":
                task_state["verification_state"] = _as_text(
                    event.data.get("verification_state"),
                    "UNKNOWN",
                )
            elif event.event_type == "RECOVERY":
                task_state["recovery_state"] = _as_text(
                    event.data.get("recovery_state"),
                    "UNKNOWN",
                )
            task_state["last_event_utc"] = event.created_utc

        return {
            "event_count": len(timeline.events),
            "event_types": dict(sorted(counts.items())),
            "last_event_utc": last_event_utc,
            "task_state": dict(by_task),
            "verification_summary": timeline.verification_summary,
            "unknown_fields": list(timeline.unknown_fields),
        }

    def _receipt_index(self) -> Tuple[Optional[ReceiptLedger], Optional[str]]:
        try:
            return ReceiptLedger(self.receipts_dir), None
        except ReceiptLedgerError:
            return None, "RECEIPT_LEDGER_UNAVAILABLE"

    def _mission_projection(
        self,
        record: Mapping[str, Any],
        approvals: List[Dict[str, Any]],
        ledger: Optional[ReceiptLedger],
    ) -> Dict[str, Any]:
        mission_id = _as_text(record.get("mission_id"))
        dag = record.get("dag")
        dag = dag if isinstance(dag, Mapping) else {}
        raw_nodes = dag.get("nodes")
        raw_nodes = raw_nodes if isinstance(raw_nodes, list) else []
        raw_edges = dag.get("edges")
        raw_edges = raw_edges if isinstance(raw_edges, list) else []

        receipt_projection: Dict[str, Any] = {
            "event_count": 0,
            "event_types": {},
            "last_event_utc": None,
            "task_state": {},
            "verification_summary": {
                "count": 0,
                "by_state": {},
                "verification_rate": None,
                "verification_rate_status": "NO_DATA",
            },
            "unknown_fields": ["verification.rate"],
        }
        if ledger is not None:
            try:
                receipts = ledger.for_mission(mission_id)
                receipt_projection = self._event_projection(
                    project_mission_timeline(mission_id, receipts)
                )
            except (ReceiptLedgerError, TimelineProjectionError):
                receipt_projection["projection_error"] = "TIMELINE_UNAVAILABLE"

        task_map: Dict[str, Dict[str, Any]] = {}
        gates: List[Dict[str, Any]] = []

        for raw in raw_nodes:
            if not isinstance(raw, Mapping):
                continue
            task_id = _as_text(raw.get("task_id"))
            if not task_id:
                continue
            approval = _latest_approval(approvals, mission_id, task_id)
            approval_status = _effective_approval_status(raw, approval)
            gate = _gate_state(raw, approval, approval_status)
            observed = receipt_projection["task_state"].get(task_id, {})
            planned_agent = _as_text(raw.get("agent_profile"), "UNKNOWN")
            selected_agent = _as_text(observed.get("selected_agent"))
            attempts = raw.get("attempts")
            attempts = attempts if isinstance(attempts, list) else []
            latest_attempt_agent = ""
            for attempt in reversed(attempts):
                if not isinstance(attempt, Mapping):
                    continue
                latest_attempt_agent = _as_text(attempt.get("agent_id"))
                if latest_attempt_agent:
                    break
            effective_agent = selected_agent or latest_attempt_agent or planned_agent
            verification_requirements = raw.get("verification_requirements")
            verification_requirements = (
                verification_requirements
                if isinstance(verification_requirements, list)
                else []
            )
            verification_counts: Counter[str] = Counter()
            for requirement in verification_requirements:
                if isinstance(requirement, Mapping):
                    verification_counts[
                        _as_text(requirement.get("status"), "UNVERIFIED").upper()
                    ] += 1

            item = {
                "task_id": task_id,
                "title": _as_text(raw.get("title"), task_id)[:180],
                "status": _as_text(raw.get("status"), "UNKNOWN").upper(),
                "planned_agent": planned_agent,
                "selected_agent": effective_agent if effective_agent != planned_agent else None,
                "agent_source": (
                    "receipt"
                    if selected_agent
                    else ("attempt_state" if latest_attempt_agent else "mission_state")
                ),
                "dependencies": sorted({
                    str(value)
                    for value in raw.get("dependencies", [])
                    if isinstance(value, str) and value
                }),
                "risk_level": _as_text(raw.get("risk_level"), "UNKNOWN").upper(),
                "approval_status": approval_status,
                "gate_state": gate,
                "start_utc": raw.get("start_utc"),
                "end_utc": raw.get("end_utc"),
                "execution_state": observed.get("execution_state"),
                "verification_state": observed.get("verification_state"),
                "recovery_state": observed.get("recovery_state"),
                "last_event_utc": observed.get("last_event_utc"),
                "verification_requirements": dict(sorted(verification_counts.items())),
            }
            task_map[task_id] = item

            if gate != "NONE":
                gates.append({
                    "task_id": task_id,
                    "title": item["title"],
                    "agent": effective_agent,
                    "gate_state": gate,
                    "approval_status": item["approval_status"],
                    "risk_level": item["risk_level"],
                    "approval_id": (
                        _as_text(approval.get("approval_id"))
                        if approval is not None
                        else None
                    ),
                    "requested_utc": approval.get("requested_utc") if approval else None,
                    "expires_utc": approval.get("expires_utc") if approval else None,
                })

        edges: List[Dict[str, Any]] = []
        seen_edges: set[Tuple[str, str]] = set()
        for raw in raw_edges:
            if not isinstance(raw, Mapping):
                continue
            source_id = _as_text(raw.get("from"))
            target_id = _as_text(raw.get("to"))
            if not source_id or not target_id or source_id not in task_map or target_id not in task_map:
                continue
            key = (source_id, target_id)
            if key in seen_edges:
                continue
            seen_edges.add(key)
            source = task_map[source_id]
            target = task_map[target_id]
            source_agent = source.get("selected_agent") or source["planned_agent"]
            target_agent = target.get("selected_agent") or target["planned_agent"]
            edges.append({
                "from": source_id,
                "to": target_id,
                "handoff": source_agent != target_agent,
                "from_agent": source_agent,
                "to_agent": target_agent,
                "state": _handoff_state(source, target, target["gate_state"]),
            })

        # Older mission records may only carry per-task dependency lists.
        for target_id, target in task_map.items():
            for source_id in target["dependencies"]:
                if source_id not in task_map or (source_id, target_id) in seen_edges:
                    continue
                seen_edges.add((source_id, target_id))
                source = task_map[source_id]
                source_agent = source.get("selected_agent") or source["planned_agent"]
                target_agent = target.get("selected_agent") or target["planned_agent"]
                edges.append({
                    "from": source_id,
                    "to": target_id,
                    "handoff": source_agent != target_agent,
                    "from_agent": source_agent,
                    "to_agent": target_agent,
                    "state": _handoff_state(source, target, target["gate_state"]),
                })

        status_counts = Counter(task["status"] for task in task_map.values())
        handoffs = [edge for edge in edges if edge["handoff"]]
        return {
            "mission_id": mission_id,
            "status": _as_text(record.get("status"), "UNKNOWN").upper(),
            "created_utc": record.get("created_utc"),
            "tasks": list(task_map.values()),
            "edges": edges,
            "handoffs": handoffs,
            "human_gates": gates,
            "receipts": {
                key: value
                for key, value in receipt_projection.items()
                if key != "task_state"
            },
            "metrics": {
                "tasks_total": len(task_map),
                "task_status_counts": dict(sorted(status_counts.items())),
                "handoffs_total": len(handoffs),
                "human_gates_total": len(gates),
                "waiting_human_total": sum(
                    1 for gate in gates if gate["gate_state"] == "WAITING_HUMAN"
                ),
            },
        }

    def build(self) -> Dict[str, Any]:
        approvals = self._approvals()
        ledger, ledger_error = self._receipt_index()
        missions = [
            self._mission_projection(record, approvals, ledger)
            for record in self._active_mission_records()
        ]
        return {
            "status": "SUCCESS",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": [
                "authoritative_mission_state",
                "persisted_approval_requests",
                "receipt_ledger",
            ],
            "read_only": True,
            "receipt_status": "AVAILABLE" if ledger is not None else ledger_error,
            "missions": missions,
            "metrics": {
                "active_missions": len(missions),
                "tasks_total": sum(m["metrics"]["tasks_total"] for m in missions),
                "handoffs_total": sum(m["metrics"]["handoffs_total"] for m in missions),
                "waiting_human_total": sum(
                    m["metrics"]["waiting_human_total"] for m in missions
                ),
            },
        }
