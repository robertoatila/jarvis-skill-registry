"""Durable remote companion sessions and cursor-based event journals."""

from __future__ import annotations

import copy
import json
import os
import re
import secrets
import tempfile
import threading
import time
from pathlib import Path
from typing import Callable, Optional

from tooling.remote_protocol import PROTOCOL_VERSION

SCHEMA_VERSION = 1
MAX_EVENT_LIMIT = 500
MAX_EVENT_PAYLOAD_BYTES = 256 * 1024
MAX_EVENT_JOURNAL_BYTES = 32 * 1024 * 1024
MAX_REQUESTS_PER_SESSION = 4096
_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9._:-]{1,256}$")
_REQUEST_FINGERPRINT_RE = re.compile(r"^[a-f0-9]{64}$")


class RemoteSessionError(ValueError):
    """Raised when remote session state or a requested transition is invalid."""


def _identifier(value: object, field: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER_RE.fullmatch(value):
        raise RemoteSessionError(f"{field} is invalid")
    return value


class RemoteSessionStore:
    """Schema-versioned session metadata with append-only JSONL events."""

    def __init__(
        self,
        state_dir: Path,
        clock: Callable[[], float] = time.time,
        id_factory: Optional[Callable[[], str]] = None,
        device_validator: Optional[Callable[[str], bool]] = None,
    ) -> None:
        self.state_dir = Path(state_dir)
        self.metadata_path = self.state_dir / "remote_sessions.json"
        self.events_dir = self.state_dir / "remote_events"
        self.clock = clock
        self.id_factory = id_factory or (lambda: secrets.token_hex(16))
        if device_validator is not None and not callable(device_validator):
            raise TypeError("device_validator must be callable")
        self.device_validator = device_validator
        self._lock = threading.RLock()
        self._state = self._load_state()
        self._reconcile_all_event_cursors()

    def _load_state(self) -> dict:
        if not self.metadata_path.exists():
            return {"schema_version": SCHEMA_VERSION, "sessions": {}}
        try:
            value = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise RemoteSessionError("remote session metadata is unreadable") from exc
        if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
            raise RemoteSessionError("unsupported remote session schema")
        sessions = value.get("sessions")
        if not isinstance(sessions, dict):
            raise RemoteSessionError("remote session metadata is invalid")
        for session_id, session in sessions.items():
            self._validate_loaded_session(session_id, session)
        return value

    def _validate_loaded_session(self, session_id: object, session: object) -> None:
        _identifier(session_id, "session_id")
        if not isinstance(session, dict) or session.get("session_id") != session_id:
            raise RemoteSessionError("remote session entry is invalid")
        _identifier(session.get("device_id"), "device_id")
        if session.get("status") not in {"OPEN", "DETACHED", "CLOSED"}:
            raise RemoteSessionError("remote session status is invalid")
        for field in ("next_seq", "last_ack_seq"):
            value = session.get(field)
            if not isinstance(value, int) or value < 0:
                raise RemoteSessionError(f"remote session {field} is invalid")
        if session["next_seq"] < 1:
            raise RemoteSessionError("remote session next_seq is invalid")
        requests = session.get("requests", {})
        if not isinstance(requests, dict):
            raise RemoteSessionError("remote request index is invalid")
        for request_id, record in requests.items():
            _identifier(request_id, "request_id")
            if not isinstance(record, dict) or not isinstance(record.get("result"), dict):
                raise RemoteSessionError("remote request record is invalid")
            fingerprint = record.get("request_fingerprint")
            if fingerprint is not None and (
                not isinstance(fingerprint, str)
                or not _REQUEST_FINGERPRINT_RE.fullmatch(fingerprint)
            ):
                raise RemoteSessionError("remote request fingerprint is invalid")
            created_at = record.get("created_at")
            if not isinstance(created_at, (int, float)) or isinstance(created_at, bool):
                raise RemoteSessionError("remote request created_at is invalid")
        session["requests"] = requests

    def _atomic_save(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(
            self._state,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        fd, temp_name = tempfile.mkstemp(
            prefix="remote_sessions.", suffix=".tmp", dir=str(self.state_dir)
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(encoded)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, self.metadata_path)
        except Exception:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
            raise

    def _event_path(self, session_id: str) -> Path:
        return self.events_dir / f"{_identifier(session_id, 'session_id')}.jsonl"

    def _last_event_seq(self, session_id: str) -> int:
        path = self._event_path(session_id)
        if not path.exists():
            return 0
        last_seq = 0
        try:
            with path.open("r", encoding="utf-8") as stream:
                for line in stream:
                    if not line.strip():
                        continue
                    event = json.loads(line)
                    if not isinstance(event, dict) or not isinstance(event.get("seq"), int):
                        raise RemoteSessionError("remote event journal is invalid")
                    if event["seq"] <= last_seq:
                        raise RemoteSessionError("remote event sequence is not monotonic")
                    last_seq = event["seq"]
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise RemoteSessionError("remote event journal is unreadable") from exc
        return last_seq

    def _reconcile_all_event_cursors(self) -> None:
        changed = False
        for session_id, session in self._state["sessions"].items():
            latest = self._last_event_seq(session_id)
            expected_next = latest + 1
            if session["next_seq"] < expected_next:
                session["next_seq"] = expected_next
                changed = True
            if session["last_ack_seq"] > latest:
                raise RemoteSessionError("remote acknowledgement exceeds event journal")
        if changed:
            self._atomic_save()

    def _session(self, session_id: str) -> dict:
        normalized = _identifier(session_id, "session_id")
        session = self._state["sessions"].get(normalized)
        if session is None:
            raise RemoteSessionError("remote session does not exist")
        return session

    def create_session(self, device_id: str) -> dict:
        normalized_device = _identifier(device_id, "device_id")
        if self.device_validator is not None:
            try:
                valid_device = bool(self.device_validator(normalized_device))
            except Exception as exc:
                raise RemoteSessionError("remote device is not active") from exc
            if not valid_device:
                raise RemoteSessionError("remote device is not active")
        with self._lock:
            session_id = _identifier(self.id_factory(), "session_id")
            if session_id in self._state["sessions"]:
                raise RemoteSessionError("remote session id already exists")
            now = float(self.clock())
            session = {
                "session_id": session_id,
                "device_id": normalized_device,
                "status": "OPEN",
                "created_at": now,
                "last_seen_at": now,
                "mission_id": None,
                "next_seq": 1,
                "last_ack_seq": 0,
                "requests": {},
            }
            self._state["sessions"][session_id] = session
            self._atomic_save()
            return copy.deepcopy(session)

    def get_session(self, session_id: str) -> Optional[dict]:
        normalized = _identifier(session_id, "session_id")
        with self._lock:
            session = self._state["sessions"].get(normalized)
            return copy.deepcopy(session) if session is not None else None

    def append_event(
        self,
        session_id: str,
        kind: str,
        payload: dict,
        mission_id: Optional[str] = None,
    ) -> dict:
        if not isinstance(kind, str) or not kind.strip() or len(kind) > 128:
            raise RemoteSessionError("event kind is invalid")
        if not isinstance(payload, dict):
            raise RemoteSessionError("event payload must be an object")
        if mission_id is not None:
            mission_id = _identifier(mission_id, "mission_id")
        try:
            encoded_payload = json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise RemoteSessionError("event payload must be JSON serializable") from exc
        if len(encoded_payload) > MAX_EVENT_PAYLOAD_BYTES:
            raise RemoteSessionError("remote event payload exceeds size limit")

        with self._lock:
            session = self._session(session_id)
            if session["status"] == "CLOSED":
                raise RemoteSessionError("closed session cannot accept new events")
            seq = session["next_seq"]
            now = float(self.clock())
            event = {
                "protocol": PROTOCOL_VERSION,
                "session_id": session["session_id"],
                "seq": seq,
                "kind": kind.strip(),
                "mission_id": mission_id,
                "payload": copy.deepcopy(payload),
                "created_at": now,
            }
            self.events_dir.mkdir(parents=True, exist_ok=True)
            path = self._event_path(session["session_id"])
            line = json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n"
            line_bytes = len(line.encode("utf-8"))
            try:
                current_size = path.stat().st_size if path.exists() else 0
            except OSError as exc:
                raise RemoteSessionError("remote event journal size is unavailable") from exc
            if current_size + line_bytes > MAX_EVENT_JOURNAL_BYTES:
                raise RemoteSessionError("remote event journal exceeds size limit")
            with path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(line)
                stream.flush()
                os.fsync(stream.fileno())
            session["next_seq"] = seq + 1
            session["last_seen_at"] = now
            self._atomic_save()
            return copy.deepcopy(event)

    def events_after(self, session_id: str, after: int = 0, limit: int = 100) -> list[dict]:
        if not isinstance(after, int) or after < 0:
            raise RemoteSessionError("event cursor is invalid")
        if not isinstance(limit, int) or limit < 1 or limit > MAX_EVENT_LIMIT:
            raise RemoteSessionError("event limit is invalid")
        with self._lock:
            session = self._session(session_id)
            path = self._event_path(session["session_id"])
            if not path.exists():
                return []
            events = []
            try:
                with path.open("r", encoding="utf-8") as stream:
                    for line in stream:
                        if not line.strip():
                            continue
                        event = json.loads(line)
                        if not isinstance(event, dict) or not isinstance(event.get("seq"), int):
                            raise RemoteSessionError("remote event journal is invalid")
                        if event["seq"] > after:
                            events.append(event)
                            if len(events) >= limit:
                                break
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                raise RemoteSessionError("remote event journal is unreadable") from exc
            return copy.deepcopy(events)

    def ack(self, session_id: str, seq: int) -> dict:
        if not isinstance(seq, int) or seq < 0:
            raise RemoteSessionError("acknowledgement sequence is invalid")
        with self._lock:
            session = self._session(session_id)
            latest = session["next_seq"] - 1
            if seq < session["last_ack_seq"]:
                raise RemoteSessionError("acknowledgement cannot move backwards")
            if seq > latest:
                raise RemoteSessionError("acknowledgement exceeds latest event")
            session["last_ack_seq"] = seq
            session["last_seen_at"] = float(self.clock())
            self._atomic_save()
            return copy.deepcopy(session)

    def remember_request(
        self,
        session_id: str,
        request_id: str,
        result: dict,
        *,
        request_fingerprint: str,
    ) -> tuple[dict, bool]:
        normalized_request = _identifier(request_id, "request_id")
        if (
            not isinstance(request_fingerprint, str)
            or not _REQUEST_FINGERPRINT_RE.fullmatch(request_fingerprint)
        ):
            raise RemoteSessionError("request_fingerprint is invalid")
        if not isinstance(result, dict):
            raise RemoteSessionError("request result must be an object")
        try:
            json.dumps(result, ensure_ascii=False)
        except (TypeError, ValueError) as exc:
            raise RemoteSessionError("request result must be JSON serializable") from exc

        with self._lock:
            session = self._session(session_id)
            requests = session["requests"]
            existing = requests.get(normalized_request)
            if existing is not None:
                existing_fingerprint = existing.get("request_fingerprint")
                if (
                    not isinstance(existing_fingerprint, str)
                    or not _REQUEST_FINGERPRINT_RE.fullmatch(existing_fingerprint)
                    or not secrets.compare_digest(
                        existing_fingerprint, request_fingerprint
                    )
                ):
                    raise RemoteSessionError(
                        "request_id reuse without matching fingerprint is not allowed"
                    )
                return copy.deepcopy(existing["result"]), False
            if session["status"] == "CLOSED":
                raise RemoteSessionError("closed session cannot accept new requests")
            if len(requests) >= MAX_REQUESTS_PER_SESSION:
                raise RemoteSessionError(
                    "remote request index exceeds per-session limit; open a new session"
                )
            stored = {
                "request_fingerprint": request_fingerprint,
                "result": copy.deepcopy(result),
                "created_at": float(self.clock()),
            }
            requests[normalized_request] = stored
            session["last_seen_at"] = stored["created_at"]
            self._atomic_save()
            return copy.deepcopy(stored["result"]), True

    def close_session(self, session_id: str) -> dict:
        with self._lock:
            session = self._session(session_id)
            session["status"] = "CLOSED"
            session["last_seen_at"] = float(self.clock())
            self._atomic_save()
            return copy.deepcopy(session)
