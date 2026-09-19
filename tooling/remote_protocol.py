"""Versioned protocol primitives for J.A.R.V.I.S. remote companion clients."""

from __future__ import annotations

import json
from typing import Any

PROTOCOL_VERSION = "jarvis-remote/1"
ALLOWED_CLIENT_KINDS = {
    "message",
    "command",
    "task",
    "resume_mission",
    "cancel_request",
    "approve_action",
    "approve_plan",
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
    elif kind == "command":
        try:
            from tooling.remote_commands import normalize_command_payload
            payload = normalize_command_payload(payload)
        except (TypeError, ValueError) as exc:
            raise RemoteProtocolError(str(exc)) from exc
    elif kind == "task":
        goal = payload.get("goal")
        if not isinstance(goal, str) or not goal.strip():
            raise RemoteProtocolError("task payload requires non-empty goal")
        if len(goal) > 6000:
            raise RemoteProtocolError("task goal exceeds maximum length")
        payload = {"goal": goal.strip()}
    elif kind == "approve_action":
        action_id = payload.get("action_id")
        action_digest = payload.get("action_digest")
        if (
            not isinstance(action_id, str)
            or not action_id.startswith("rcmd-")
            or len(action_id) != 29
        ):
            raise RemoteProtocolError("approve_action requires a valid action_id")
        if (
            not isinstance(action_digest, str)
            or len(action_digest) != 64
            or any(ch not in "0123456789abcdef" for ch in action_digest)
        ):
            raise RemoteProtocolError("approve_action requires a valid action_digest")
        payload = {"action_id": action_id, "action_digest": action_digest}
    elif kind == "approve_plan":
        task_id = payload.get("task_id")
        plan_digest = payload.get("plan_digest")
        if (
            not isinstance(task_id, str)
            or not task_id.startswith("rtask-")
            or len(task_id) != 30
        ):
            raise RemoteProtocolError("approve_plan requires a valid task_id")
        if (
            not isinstance(plan_digest, str)
            or len(plan_digest) != 64
            or any(ch not in "0123456789abcdef" for ch in plan_digest)
        ):
            raise RemoteProtocolError("approve_plan requires a valid plan_digest")
        payload = {"task_id": task_id, "plan_digest": plan_digest}

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
