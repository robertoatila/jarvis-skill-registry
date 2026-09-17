"""Append-only correlated runtime receipt observability for J.A.R.V.I.S. v0.2.

The ledger is derived audit state. It never grants execution authority and never
mutates the authoritative mission store. Records are deterministic JSONL,
credential-bearing fields are redacted before persistence, and verification
receipts must correlate to an execution receipt from the same mission.
"""

from __future__ import annotations

import copy
import json
import os
import re
from collections.abc import Mapping
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
