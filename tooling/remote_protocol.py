"""Versioned protocol primitives for J.A.R.V.I.S. remote companion clients."""

from __future__ import annotations

import json
from typing import Any

PROTOCOL_VERSION = "jarvis-remote/1"
ALLOWED_CLIENT_KINDS = {
    "message",
    "resume_mission",
    "cancel_request",
    "approve_action",
    "ping",
}
MAX_TEXT_CHARS = 32_768
MAX_PAYLOAD_BYTES = 64 * 1024


class RemoteProtocolError(ValueError):
    """Raised when a remote protocol envelope violates the public contract."""


def _require_identifier(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise RemoteProtocolError(f"{field} must be a string")
    normalized = value.strip()
    if not normalized or len(normalized) > 256 or "\r" in normalized or "\n" in normalized:
        raise RemoteProtocolError(f"{field} is invalid")
    return normalized


def parse_client_envelope(value: object) -> dict:
    """Validate and normalize one client-to-host protocol envelope."""
    if not isinstance(value, dict):
        raise RemoteProtocolError("request must be an object")

    protocol = value.get("protocol")
    if protocol != PROTOCOL_VERSION:
        raise RemoteProtocolError("unsupported remote protocol")

    session_id = _require_identifier(value.get("session_id"), "session_id")
    device_id = _require_identifier(value.get("device_id"), "device_id")
    request_id = _require_identifier(value.get("request_id"), "request_id")

    kind = value.get("kind")
    if not isinstance(kind, str) or kind not in ALLOWED_CLIENT_KINDS:
        raise RemoteProtocolError("unsupported request kind")

    payload = value.get("payload")
    if not isinstance(payload, dict):
        raise RemoteProtocolError("payload must be an object")

    if kind == "message":
        text = payload.get("text")
        if not isinstance(text, str) or not text.strip():
            raise RemoteProtocolError("message payload requires non-empty text")
        if len(text) > MAX_TEXT_CHARS:
            raise RemoteProtocolError("message text exceeds maximum length")

    try:
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise RemoteProtocolError("payload must be JSON serializable") from exc
    if len(encoded) > MAX_PAYLOAD_BYTES:
        raise RemoteProtocolError("payload exceeds maximum encoded size")

    return {
        "protocol": PROTOCOL_VERSION,
        "session_id": session_id,
        "device_id": device_id,
        "request_id": request_id,
        "kind": kind,
        "payload": dict(payload),
    }
