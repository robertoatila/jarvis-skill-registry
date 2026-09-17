"""Append-only correlated runtime receipt observability for J.A.R.V.I.S. v0.2.

The ledger is derived audit state. It never grants execution authority and never
mutates the authoritative mission store. Records are deterministic JSONL,
credential-bearing fields are redacted before persistence, and verification
receipts must correlate to an execution receipt from the same mission.
"""

from __future__ import annotations

import copy
import json
import math
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any


_REDACTED = "[REDACTED]"
_SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "access_token",
    "refresh_token",
    "client_secret",
    "password",
    "secret",
}
_BEARER_PATTERN = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")


class ReceiptLedgerError(ValueError):
    """Raised when receipt persistence would violate ledger integrity."""


class TimelineProjectionError(ValueError):
    """Raised when receipt data cannot be projected safely into a timeline."""


@dataclass(frozen=True)
class TimelineEvent:
    receipt_id: str
    event_type: str
    created_utc: str
    task_id: str | None
    attempt_id: str | None
    trace_id: str | None
    data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "event_type": self.event_type,
            "created_utc": self.created_utc,
            "task_id": self.task_id,
            "attempt_id": self.attempt_id,
            "trace_id": self.trace_id,
            "data": copy.deepcopy(self.data),
        }


@dataclass(frozen=True)
class MissionTimeline:
    mission_id: str
    events: tuple[TimelineEvent, ...]
    resource_summary: dict[str, Any]
    verification_summary: dict[str, Any]
    unknown_fields: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "events": [event.to_dict() for event in self.events],
            "resource_summary": copy.deepcopy(self.resource_summary),
            "verification_summary": copy.deepcopy(self.verification_summary),
            "unknown_fields": list(self.unknown_fields),
        }


class ReceiptLedger:
    """Durable append-only JSONL ledger for correlated runtime receipts."""

    def __init__(self, receipts_dir: Path):
        self.receipts_dir = Path(receipts_dir)
        self.path = self.receipts_dir / "receipts.jsonl"
        self._lock = RLock()
        self._records: list[dict[str, Any]] = []
        self._by_id: dict[str, dict[str, Any]] = {}
        self._load_existing()

    @staticmethod
    def _redact(value: Any, *, key: str | None = None) -> Any:
        normalized_key = key.casefold().replace("-", "_") if isinstance(key, str) else None
        if normalized_key in _SENSITIVE_KEYS:
            return _REDACTED

        if isinstance(value, Mapping):
            return {
                str(child_key): ReceiptLedger._redact(child_value, key=str(child_key))
                for child_key, child_value in value.items()
            }
        if isinstance(value, list):
            return [ReceiptLedger._redact(item) for item in value]
        if isinstance(value, tuple):
            return [ReceiptLedger._redact(item) for item in value]
        if isinstance(value, str):
            return _BEARER_PATTERN.sub("Bearer " + _REDACTED, value)
        if value is None or isinstance(value, (bool, int, float)):
            return value
        raise ReceiptLedgerError(
            f"receipt contains unsupported value type: {type(value).__name__}"
        )

    @staticmethod
    def _require_identifier(record: Mapping[str, Any], field: str) -> str:
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ReceiptLedgerError(f"{field} must be a non-empty string")
        return value

    @staticmethod
    def _validate_optional_identifier(record: Mapping[str, Any], field: str) -> None:
        value = record.get(field)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ReceiptLedgerError(f"{field} must be null or a non-empty string")

    def _validate(self, record: Mapping[str, Any]) -> None:
        if not isinstance(record, Mapping):
            raise ReceiptLedgerError("receipt must be a mapping")

        receipt_id = self._require_identifier(record, "receipt_id")
        self._require_identifier(record, "schema_version")
        self._require_identifier(record, "mission_id")
        self._require_identifier(record, "created_utc")
        for field in ("task_id", "attempt_id", "trace_id"):
            self._validate_optional_identifier(record, field)

        if receipt_id in self._by_id:
            raise ReceiptLedgerError(f"duplicate receipt_id: {receipt_id}")

        execution_receipt_id = record.get("execution_receipt_id")
        if execution_receipt_id is not None:
            if not isinstance(execution_receipt_id, str) or not execution_receipt_id.strip():
                raise ReceiptLedgerError(
                    "execution_receipt_id must be null or a non-empty string"
                )
            execution = self._by_id.get(execution_receipt_id)
            if execution is None:
                raise ReceiptLedgerError(
                    f"verification references unknown execution receipt: {execution_receipt_id}"
                )
            if execution.get("mission_id") != record.get("mission_id"):
                raise ReceiptLedgerError(
                    "verification/execution correlation crosses mission boundary"
                )
            for field in ("task_id", "attempt_id", "trace_id"):
                current = record.get(field)
                prior = execution.get(field)
                if current is not None and prior is not None and current != prior:
                    raise ReceiptLedgerError(
                        f"verification/execution correlation mismatch: {field}"
                    )

    def _accept_loaded(self, record: dict[str, Any]) -> None:
        self._validate(record)
        stored = copy.deepcopy(record)
        self._records.append(stored)
        self._by_id[stored["receipt_id"]] = stored

    def _load_existing(self) -> None:
        if not self.path.exists():
            return
        if not self.path.is_file():
            raise ReceiptLedgerError("receipt ledger path is not a regular file")

        with self.path.open("r", encoding="utf-8") as stream:
            for line_number, raw in enumerate(stream, start=1):
                line = raw.strip()
                if not line:
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ReceiptLedgerError(
                        f"invalid receipt JSONL at line {line_number}"
                    ) from exc
                if not isinstance(value, dict):
                    raise ReceiptLedgerError(
                        f"receipt JSONL line {line_number} is not an object"
                    )
                self._accept_loaded(value)

    def contains(self, receipt_id: str) -> bool:
        with self._lock:
            return receipt_id in self._by_id

    def append(self, receipt: Mapping[str, Any]) -> None:
        """Redact, validate, fsync and append exactly one receipt."""
        with self._lock:
            redacted = self._redact(receipt)
            if not isinstance(redacted, dict):
                raise ReceiptLedgerError("redacted receipt must remain an object")
            self._validate(redacted)

            try:
                encoded = json.dumps(
                    redacted,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                    allow_nan=False,
                )
            except (TypeError, ValueError) as exc:
                raise ReceiptLedgerError("receipt is not deterministic JSON data") from exc

            self.receipts_dir.mkdir(parents=True, exist_ok=True)
            if self.path.exists() and not self.path.is_file():
                raise ReceiptLedgerError("receipt ledger path is not a regular file")

            with self.path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(encoded + "\n")
                stream.flush()
                os.fsync(stream.fileno())

            stored = copy.deepcopy(redacted)
            self._records.append(stored)
            self._by_id[stored["receipt_id"]] = stored

    def _query(self, predicate) -> list[dict[str, Any]]:
        with self._lock:
            return [copy.deepcopy(item) for item in self._records if predicate(item)]

    def for_mission(self, mission_id: str) -> list[dict[str, Any]]:
        return self._query(lambda item: item.get("mission_id") == mission_id)

    def for_task(self, mission_id: str, task_id: str) -> list[dict[str, Any]]:
        return self._query(
            lambda item: item.get("mission_id") == mission_id
            and item.get("task_id") == task_id
        )

    def for_attempt(self, attempt_id: str) -> list[dict[str, Any]]:
        return self._query(lambda item: item.get("attempt_id") == attempt_id)

    def for_trace(self, trace_id: str) -> list[dict[str, Any]]:
        return self._query(lambda item: item.get("trace_id") == trace_id)


_STRUCTURED_EVENT_FIELDS: dict[str, tuple[str, ...]] = {
    "ADMISSION": (
        "admitted",
        "admission_decision",
        "rejection_reasons",
        "risk_level",
        "rule_violations",
    ),
    "CONTEXT": (
        "sources_loaded",
        "sources_considered",
        "serialized_bytes",
        "bytes_loaded",
        "token_estimate",
        "token_estimation_method",
        "selection_reason",
        "delivery_mode",
        "content_hash",
        "provenance",
    ),
    "DECISION": (
        "decision_type",
        "candidates",
        "rejected_candidates",
        "scores",
        "selected_candidate",
        "selection_reason",
        "confidence",
        "estimated_tokens",
        "estimated_cost_usd",
        "estimated_risk",
        "actual_tokens",
        "actual_cost_usd",
        "actual_outcome",
    ),
    "EXECUTION": (
        "adapter",
        "invocation_occurred",
        "execution_state",
        "output_reference",
        "resource_usage",
    ),
    "EFFECT": (
        "side_effect_id",
        "side_effect_type",
        "target",
        "expected_change",
        "observed_change",
        "idempotency",
        "rollback_target",
        "compensation_action",
        "verification_requirement_id",
        "provenance_hash",
        "side_effects",
    ),
    "RECOVERY": (
        "recovery_state",
        "failure_class",
        "failure_attribution",
        "retryable",
        "side_effects",
    ),
    "VERIFICATION": (
        "execution_receipt_id",
        "verification_state",
        "evidence_ids",
    ),
    "MEMORY": (
        "query",
        "tier_filter",
        "matched_items",
        "excluded_conflicts",
        "decay_scores",
        "total_tokens_estimated",
        "memory_id",
        "tier",
        "verification_state",
        "evidence_refs",
        "admission_reason",
        "source_attempt_id",
        "source_trace_id",
    ),
    "GOVERNOR": (
        "governor_action",
        "action",
        "reason_code",
        "observation",
    ),
}

_PRIVATE_EVENT_KEYS = {
    "chain_of_thought",
    "reasoning",
    "private_reasoning",
    "thoughts",
    "prompt",
    "raw_prompt",
    "raw_output",
    "text",
    "content",
}

_RESOURCE_METRICS: dict[str, tuple[tuple[str, ...], str]] = {
    "tokens": (("tokens",), "tokens"),
    "cost_usd": (("cost_usd",), "USD"),
    "latency_ms": (("latency_ms", "duration_ms"), "ms"),
}


def _parse_timeline_timestamp(value: Any) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise TimelineProjectionError("created_utc must be a non-empty timestamp")
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise TimelineProjectionError(f"invalid created_utc timestamp: {value}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise TimelineProjectionError("created_utc must include an explicit timezone")
    return parsed


def _classify_timeline_receipt(receipt: Mapping[str, Any]) -> str | None:
    explicit = receipt.get("event_type")
    if isinstance(explicit, str):
        normalized = explicit.strip().upper()
        if normalized in _STRUCTURED_EVENT_FIELDS:
            return normalized

    if "admission_decision" in receipt or "admitted" in receipt:
        return "ADMISSION"
    if "sources_loaded" in receipt or "serialized_bytes" in receipt:
        return "CONTEXT"
    if "decision_type" in receipt:
        return "DECISION"
    if "invocation_occurred" in receipt or (
        "adapter" in receipt and "execution_state" in receipt
    ):
        return "EXECUTION"
    if (
        "side_effect_id" in receipt
        or "side_effect_type" in receipt
        or "side_effects" in receipt
    ):
        return "EFFECT"
    if "recovery_state" in receipt:
        return "RECOVERY"
    if "execution_receipt_id" in receipt and "verification_state" in receipt:
        return "VERIFICATION"
    if (
        "matched_items" in receipt
        or "tier_filter" in receipt
        or "memory_id" in receipt
    ):
        return "MEMORY"
    if "governor_action" in receipt or (
        "reason_code" in receipt
        and "observation" in receipt
        and "action" in receipt
    ):
        return "GOVERNOR"
    return None


def _strip_private_event_data(value: Any) -> Any:
    if isinstance(value, Mapping):
        cleaned = {}
        for key, child in value.items():
            normalized = str(key).casefold().replace("-", "_")
            if normalized in _PRIVATE_EVENT_KEYS:
                continue
            cleaned[str(key)] = _strip_private_event_data(child)
        return cleaned
    if isinstance(value, (list, tuple)):
        return [_strip_private_event_data(item) for item in value]
    return copy.deepcopy(value)


def _event_from_receipt(
    receipt: Mapping[str, Any],
    event_type: str,
) -> TimelineEvent:
    data = {
        field: _strip_private_event_data(receipt[field])
        for field in _STRUCTURED_EVENT_FIELDS[event_type]
        if field in receipt
    }
    return TimelineEvent(
        receipt_id=str(receipt["receipt_id"]),
        event_type=event_type,
        created_utc=str(receipt["created_utc"]),
        task_id=receipt.get("task_id"),
        attempt_id=receipt.get("attempt_id"),
        trace_id=receipt.get("trace_id"),
        data=data,
    )


def _measurement_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value):
        return None
    return float(value)


def _aggregate_resource_metric(
    receipts: list[Mapping[str, Any]],
    aliases: tuple[str, ...],
    unit: str,
) -> dict[str, Any]:
    measurements: list[Mapping[str, Any]] = []
    for receipt in receipts:
        usage = receipt.get("resource_usage")
        if not isinstance(usage, Mapping):
            continue
        for alias in aliases:
            candidate = usage.get(alias)
            if isinstance(candidate, Mapping):
                measurements.append(candidate)
                break

    if not measurements:
        return {"status": "UNKNOWN", "value": None, "unit": unit}

    statuses = []
    measured_values: list[float] = []
    estimated_values: list[float] = []
    invalid_or_unknown = False

    for measurement in measurements:
        status = str(measurement.get("status", "UNKNOWN")).upper()
        statuses.append(status)
        reported_unit = measurement.get("unit")
        if reported_unit not in (None, unit):
            invalid_or_unknown = True
            continue

        number = _measurement_number(measurement.get("value"))
        if status == "MEASURED":
            if number is None:
                invalid_or_unknown = True
            else:
                measured_values.append(number)
        elif status == "ESTIMATED":
            if number is None:
                invalid_or_unknown = True
            else:
                estimated_values.append(number)
        elif status not in ("NOT_APPLICABLE", "UNKNOWN"):
            invalid_or_unknown = True

    if measured_values:
        incomplete = (
            invalid_or_unknown
            or any(status in ("UNKNOWN", "ESTIMATED") for status in statuses)
        )
        return {
            "status": "PARTIAL" if incomplete else "MEASURED",
            "value": float(sum(measured_values)),
            "unit": unit,
        }

    if estimated_values and not invalid_or_unknown and all(
        status in ("ESTIMATED", "NOT_APPLICABLE") for status in statuses
    ):
        return {
            "status": "ESTIMATED",
            "value": float(sum(estimated_values)),
            "unit": unit,
        }

    if statuses and all(status == "NOT_APPLICABLE" for status in statuses):
        return {"status": "NOT_APPLICABLE", "value": None, "unit": unit}

    return {"status": "UNKNOWN", "value": None, "unit": unit}


def project_mission_timeline(
    mission_id: str,
    receipts,
) -> MissionTimeline:
    """Project correlated receipts into a read-only, reasoning-free mission timeline."""
    if not isinstance(mission_id, str) or not mission_id.strip():
        raise TimelineProjectionError("mission_id must be a non-empty string")
    if not isinstance(receipts, (list, tuple)):
        raise TimelineProjectionError("receipts must be a list or tuple")

    prepared: list[tuple[datetime, str, Mapping[str, Any]]] = []
    receipt_list: list[Mapping[str, Any]] = []
    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            raise TimelineProjectionError("timeline receipts must be mappings")
        receipt_id = receipt.get("receipt_id")
        if not isinstance(receipt_id, str) or not receipt_id.strip():
            raise TimelineProjectionError("timeline receipt_id must be a non-empty string")
        if receipt.get("mission_id") != mission_id:
            raise TimelineProjectionError("timeline receipt crosses mission boundary")
        created_utc = receipt.get("created_utc")
        parsed = _parse_timeline_timestamp(created_utc)
        prepared.append((parsed, receipt_id, receipt))
        receipt_list.append(receipt)

    prepared.sort(key=lambda item: (item[0], item[1]))

    events = []
    for _, _, receipt in prepared:
        event_type = _classify_timeline_receipt(receipt)
        if event_type is None:
            continue
        events.append(_event_from_receipt(receipt, event_type))

    attempt_ids = {
        receipt.get("attempt_id")
        for receipt in receipt_list
        if isinstance(receipt.get("attempt_id"), str) and receipt.get("attempt_id")
    }

    resource_summary: dict[str, Any] = {"attempt_count": len(attempt_ids)}
    unknown_fields: set[str] = set()
    for metric, (aliases, unit) in _RESOURCE_METRICS.items():
        summary = _aggregate_resource_metric(receipt_list, aliases, unit)
        resource_summary[metric] = summary
        if summary["status"] in ("UNKNOWN", "PARTIAL"):
            unknown_fields.add(f"resources.{metric}")

    verification_states = []
    for receipt in receipt_list:
        if _classify_timeline_receipt(receipt) != "VERIFICATION":
            continue
        state = receipt.get("verification_state")
        verification_states.append(
            state.upper() if isinstance(state, str) and state else "UNKNOWN"
        )

    by_state: dict[str, int] = {}
    for state in verification_states:
        by_state[state] = by_state.get(state, 0) + 1
    by_state = dict(sorted(by_state.items()))

    verification_count = len(verification_states)
    verified_count = by_state.get("VERIFIED", 0)
    verification_rate = (
        verified_count / verification_count if verification_count else None
    )
    verification_summary = {
        "count": verification_count,
        "by_state": by_state,
        "verification_rate": verification_rate,
        "verification_rate_status": (
            "MEASURED" if verification_count else "NO_DATA"
        ),
    }
    if verification_count == 0:
        unknown_fields.add("verification.rate")

    return MissionTimeline(
        mission_id=mission_id,
        events=tuple(events),
        resource_summary=resource_summary,
        verification_summary=verification_summary,
        unknown_fields=tuple(sorted(unknown_fields)),
    )
