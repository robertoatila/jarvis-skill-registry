"""Bridge durable remote companion sessions into one existing J.A.R.V.I.S. runtime.

This module intentionally owns no planner, Governor, memory fabric, model router,
tool router, or authorization plane.  A caller injects the already-authoritative
PC-side runtime adapter.  The bridge only validates session ownership, preserves
correlation/idempotency, delegates once, and journals explicit user-visible
remote events.
"""

from __future__ import annotations

import copy
import threading
from typing import Callable

from tooling.remote_protocol import RemoteProtocolError, parse_client_envelope
from tooling.remote_sessions import RemoteSessionError, RemoteSessionStore


class RemoteRuntimeBridgeError(ValueError):
    """Raised when a remote request cannot be safely bridged to the host runtime."""


class RemoteRuntimeBridge:
    """Translate remote protocol messages into calls to an injected host runtime."""

    def __init__(
        self,
        session_store: RemoteSessionStore,
        *,
        runtime_adapter: Callable[[dict], dict],
    ) -> None:
        if not isinstance(session_store, RemoteSessionStore):
            raise TypeError("session_store must be RemoteSessionStore")
        if not callable(runtime_adapter):
            raise TypeError("runtime_adapter must be callable")
        self.session_store = session_store
        self.runtime_adapter = runtime_adapter
        # Serializes request-id check -> delegate -> durable result publication
        # within one host process. Durable completed results remain idempotent
        # across restart through RemoteSessionStore.
        self._dispatch_lock = threading.RLock()

    @staticmethod
    def _existing_request_result(session: dict, request_id: str):
        requests = session.get("requests")
        if not isinstance(requests, dict):
            return None
        record = requests.get(request_id)
        if not isinstance(record, dict):
            return None
        result = record.get("result")
        return copy.deepcopy(result) if isinstance(result, dict) else None

    def _owned_open_session(self, session_id: str, device_id: str) -> dict:
        session = self.session_store.get_session(session_id)
        if session is None:
            raise RemoteRuntimeBridgeError("REMOTE_SESSION_NOT_FOUND")
        if session.get("device_id") != device_id:
            raise RemoteRuntimeBridgeError("REMOTE_SESSION_DEVICE_MISMATCH")
        if session.get("status") == "CLOSED":
            raise RemoteRuntimeBridgeError("REMOTE_SESSION_CLOSED")
        return session

    def _record_error(self, envelope: dict, reason: str) -> dict:
        event = self.session_store.append_event(
            envelope["session_id"],
            "error",
            {
                "request_id": envelope["request_id"],
                "reason": reason,
            },
        )
        result = {
            "status": "ERROR",
            "reason": reason,
            "session_id": envelope["session_id"],
            "request_id": envelope["request_id"],
            "mission_id": None,
            "event_seq": event["seq"],
        }
        remembered, _ = self.session_store.remember_request(
            envelope["session_id"], envelope["request_id"], result
        )
        return remembered

    def handle(self, raw_envelope: object) -> dict:
        """Validate, correlate, delegate, journal, and return one remote request.

        Task 2 initially supports the `message` operation. Other protocol kinds
        remain defined at the wire layer but are rejected here until their
        runtime authority semantics are implemented explicitly.
        """
        try:
            envelope = parse_client_envelope(raw_envelope)
        except RemoteProtocolError as exc:
            raise RemoteRuntimeBridgeError(str(exc)) from exc

        with self._dispatch_lock:
            session = self._owned_open_session(
                envelope["session_id"], envelope["device_id"]
            )
            existing = self._existing_request_result(session, envelope["request_id"])
            if existing is not None:
                return existing

            if envelope["kind"] != "message":
                raise RemoteRuntimeBridgeError("REMOTE_REQUEST_KIND_NOT_IMPLEMENTED")

            text = envelope["payload"]["text"]
            accepted = self.session_store.append_event(
                envelope["session_id"],
                "user_message_accepted",
                {
                    "request_id": envelope["request_id"],
                    "text": text,
                },
            )

            runtime_request = {
                "protocol": envelope["protocol"],
                "session_id": envelope["session_id"],
                "device_id": envelope["device_id"],
                "request_id": envelope["request_id"],
                "kind": envelope["kind"],
                "text": text,
                "payload": copy.deepcopy(envelope["payload"]),
                "accepted_event_seq": accepted["seq"],
            }

            try:
                runtime_result = self.runtime_adapter(runtime_request)
            except Exception:
                return self._record_error(envelope, "RUNTIME_ADAPTER_FAILED")

            if not isinstance(runtime_result, dict):
                return self._record_error(envelope, "RUNTIME_ADAPTER_MALFORMED_RESULT")

            status = runtime_result.get("status")
            if not isinstance(status, str) or not status.strip():
                return self._record_error(envelope, "RUNTIME_ADAPTER_MALFORMED_RESULT")
            status = status.strip()

            mission_id = runtime_result.get("mission_id")
            if mission_id is not None and (
                not isinstance(mission_id, str) or not mission_id.strip()
            ):
                return self._record_error(envelope, "RUNTIME_ADAPTER_MALFORMED_RESULT")
            if isinstance(mission_id, str):
                mission_id = mission_id.strip()

            reply = runtime_result.get("reply", runtime_result.get("text"))
            if not isinstance(reply, str):
                return self._record_error(envelope, "RUNTIME_ADAPTER_MALFORMED_RESULT")

            payload = {
                "request_id": envelope["request_id"],
                "status": status,
                "text": reply,
            }
            receipt = runtime_result.get("receipt")
            if isinstance(receipt, dict):
                payload["receipt"] = copy.deepcopy(receipt)

            try:
                response_event = self.session_store.append_event(
                    envelope["session_id"],
                    "assistant_message",
                    payload,
                    mission_id=mission_id,
                )
            except RemoteSessionError:
                return self._record_error(envelope, "RUNTIME_CORRELATION_INVALID")

            result = {
                "status": status,
                "session_id": envelope["session_id"],
                "request_id": envelope["request_id"],
                "mission_id": mission_id,
                "event_seq": response_event["seq"],
            }
            remembered, created = self.session_store.remember_request(
                envelope["session_id"], envelope["request_id"], result
            )
            if not created:
                return remembered
            return result
