"""Bridge durable remote companion sessions into one existing J.A.R.V.I.S. runtime.

The bridge owns correlation/idempotency only. Chat requests delegate to the
injected PC-side runtime. Structured command requests delegate to the optional
RemoteCommandController and require an explicit digest-bound approval before
execution.
"""

from __future__ import annotations

import copy
import hashlib
import json
import secrets
import threading
from typing import Callable

from tooling.remote_protocol import RemoteProtocolError, parse_client_envelope
from tooling.remote_sessions import RemoteSessionError, RemoteSessionStore

try:
    from tooling.remote_commands import RemoteCommandController, RemoteCommandError
except ImportError:  # pragma: no cover - compatibility during partial checkout upgrades
    RemoteCommandController = None

    class RemoteCommandError(ValueError):
        pass

try:
    from tooling.remote_tasks import RemoteTaskError, public_plan_view
except ImportError:  # pragma: no cover - compatibility during partial checkout upgrades
    class RemoteTaskError(ValueError):
        pass

    def public_plan_view(plan):
        return {"summary": plan.get("summary"), "actions": []}


class RemoteRuntimeBridgeError(ValueError):
    """Raised when a remote request cannot be safely bridged to the host runtime."""


class RemoteRuntimeBridge:
    """Translate remote protocol messages into the authoritative PC-side runtime."""

    def __init__(
        self,
        session_store: RemoteSessionStore,
        *,
        runtime_adapter: Callable[[dict], dict],
        command_controller=None,
        task_controller=None,
    ) -> None:
        if not isinstance(session_store, RemoteSessionStore):
            raise TypeError("session_store must be RemoteSessionStore")
        if not callable(runtime_adapter):
            raise TypeError("runtime_adapter must be callable")
        if command_controller is not None:
            required = ("prepare", "approve_and_execute")
            if any(not callable(getattr(command_controller, name, None)) for name in required):
                raise TypeError("command_controller must expose prepare() and approve_and_execute()")
        if task_controller is not None:
            required = ("prepare", "approve_and_execute")
            if any(not callable(getattr(task_controller, name, None)) for name in required):
                raise TypeError("task_controller must expose prepare() and approve_and_execute()")
        self.session_store = session_store
        self.runtime_adapter = runtime_adapter
        self.command_controller = command_controller
        self.task_controller = task_controller
        self._dispatch_lock = threading.RLock()

    @staticmethod
    def _request_fingerprint(envelope: dict) -> str:
        material = {
            "protocol": envelope["protocol"],
            "session_id": envelope["session_id"],
            "device_id": envelope["device_id"],
            "request_id": envelope["request_id"],
            "kind": envelope["kind"],
            "payload": envelope["payload"],
        }
        raw = json.dumps(
            material,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @classmethod
    def _existing_request_result(cls, session: dict, envelope: dict):
        requests = session.get("requests")
        if not isinstance(requests, dict):
            return None
        record = requests.get(envelope["request_id"])
        if not isinstance(record, dict):
            return None
        stored_fingerprint = record.get("request_fingerprint")
        expected_fingerprint = cls._request_fingerprint(envelope)
        if (
            not isinstance(stored_fingerprint, str)
            or not secrets.compare_digest(stored_fingerprint, expected_fingerprint)
        ):
            raise RemoteRuntimeBridgeError("REMOTE_REQUEST_ID_REUSE_MISMATCH")
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

    def _remember(self, envelope: dict, result: dict) -> dict:
        remembered, created = self.session_store.remember_request(
            envelope["session_id"],
            envelope["request_id"],
            result,
            request_fingerprint=self._request_fingerprint(envelope),
        )
        return result if created else remembered

    def _record_error(self, envelope: dict, reason: str, *, detail: str | None = None) -> dict:
        payload = {
            "request_id": envelope["request_id"],
            "reason": reason,
        }
        if detail:
            payload["detail"] = detail[:512]
        event = self.session_store.append_event(
            envelope["session_id"],
            "error",
            payload,
        )
        result = {
            "status": "ERROR",
            "reason": reason,
            "session_id": envelope["session_id"],
            "request_id": envelope["request_id"],
            "mission_id": None,
            "event_seq": event["seq"],
        }
        if detail:
            result["detail"] = detail[:512]
        return self._remember(envelope, result)

    def _handle_message(self, envelope: dict) -> dict:
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

        return self._remember(
            envelope,
            {
                "status": status,
                "session_id": envelope["session_id"],
                "request_id": envelope["request_id"],
                "mission_id": mission_id,
                "event_seq": response_event["seq"],
            },
        )

    def _handle_command(self, envelope: dict) -> dict:
        if self.command_controller is None:
            return self._record_error(envelope, "REMOTE_COMMAND_EXECUTOR_UNAVAILABLE")

        requested = self.session_store.append_event(
            envelope["session_id"],
            "command_requested",
            {
                "request_id": envelope["request_id"],
                "command": copy.deepcopy(envelope["payload"]),
            },
        )
        try:
            action = self.command_controller.prepare(
                envelope["payload"],
                session_id=envelope["session_id"],
                device_id=envelope["device_id"],
                request_id=envelope["request_id"],
            )
        except (RemoteCommandError, ValueError, TypeError) as exc:
            return self._record_error(
                envelope,
                "REMOTE_COMMAND_REJECTED",
                detail=str(exc),
            )

        approval_event = self.session_store.append_event(
            envelope["session_id"],
            "approval_required",
            {
                "request_id": envelope["request_id"],
                "action_id": action["action_id"],
                "action_digest": action["action_digest"],
                "command": copy.deepcopy(action["command"]),
                "execution_binding": copy.deepcopy(action.get("execution_binding")),
                "requested_event_seq": requested["seq"],
            },
        )
        return self._remember(
            envelope,
            {
                "status": "APPROVAL_REQUIRED",
                "session_id": envelope["session_id"],
                "request_id": envelope["request_id"],
                "mission_id": None,
                "action_id": action["action_id"],
                "action_digest": action["action_digest"],
                "event_seq": approval_event["seq"],
            },
        )

    def _handle_approval(self, envelope: dict) -> dict:
        if self.command_controller is None:
            return self._record_error(envelope, "REMOTE_COMMAND_EXECUTOR_UNAVAILABLE")

        action_id = envelope["payload"]["action_id"]
        action_digest = envelope["payload"]["action_digest"]
        submitted = self.session_store.append_event(
            envelope["session_id"],
            "approval_submitted",
            {
                "request_id": envelope["request_id"],
                "action_id": action_id,
                "action_digest": action_digest,
            },
        )
        try:
            receipt = self.command_controller.approve_and_execute(
                action_id=action_id,
                action_digest=action_digest,
                session_id=envelope["session_id"],
                device_id=envelope["device_id"],
            )
        except (RemoteCommandError, ValueError, TypeError) as exc:
            return self._record_error(
                envelope,
                "REMOTE_COMMAND_APPROVAL_REJECTED",
                detail=str(exc),
            )

        event = self.session_store.append_event(
            envelope["session_id"],
            "action_receipt",
            {
                "request_id": envelope["request_id"],
                "action_id": action_id,
                "action_digest": action_digest,
                "approval_event_seq": submitted["seq"],
                "receipt": copy.deepcopy(receipt),
            },
        )
        return self._remember(
            envelope,
            {
                "status": receipt.get("status", "ERROR"),
                "session_id": envelope["session_id"],
                "request_id": envelope["request_id"],
                "mission_id": None,
                "action_id": action_id,
                "action_digest": action_digest,
                "exit_code": receipt.get("exit_code"),
                "event_seq": event["seq"],
            },
        )

    def _handle_task(self, envelope: dict) -> dict:
        if self.task_controller is None:
            return self._record_error(envelope, "REMOTE_TASK_PLANNER_UNAVAILABLE")

        requested = self.session_store.append_event(
            envelope["session_id"],
            "task_requested",
            {
                "request_id": envelope["request_id"],
                "goal": envelope["payload"]["goal"],
            },
        )
        try:
            task = self.task_controller.prepare(
                envelope["payload"]["goal"],
                session_id=envelope["session_id"],
                device_id=envelope["device_id"],
                request_id=envelope["request_id"],
            )
        except (RemoteTaskError, ValueError, TypeError) as exc:
            return self._record_error(
                envelope,
                "REMOTE_TASK_PLANNING_REJECTED",
                detail=str(exc),
            )

        plan_event = self.session_store.append_event(
            envelope["session_id"],
            "task_plan_required",
            {
                "request_id": envelope["request_id"],
                "task_id": task["task_id"],
                "plan_digest": task["plan_digest"],
                "plan": public_plan_view(task["plan"]),
                "requested_event_seq": requested["seq"],
            },
        )
        return self._remember(
            envelope,
            {
                "status": "PLAN_APPROVAL_REQUIRED",
                "session_id": envelope["session_id"],
                "request_id": envelope["request_id"],
                "mission_id": None,
                "task_id": task["task_id"],
                "plan_digest": task["plan_digest"],
                "event_seq": plan_event["seq"],
            },
        )

    def _handle_plan_approval(self, envelope: dict) -> dict:
        if self.task_controller is None:
            return self._record_error(envelope, "REMOTE_TASK_PLANNER_UNAVAILABLE")

        task_id = envelope["payload"]["task_id"]
        plan_digest = envelope["payload"]["plan_digest"]
        submitted = self.session_store.append_event(
            envelope["session_id"],
            "task_plan_approval_submitted",
            {
                "request_id": envelope["request_id"],
                "task_id": task_id,
                "plan_digest": plan_digest,
            },
        )
        try:
            receipt = self.task_controller.approve_and_execute(
                task_id=task_id,
                plan_digest=plan_digest,
                session_id=envelope["session_id"],
                device_id=envelope["device_id"],
            )
        except (RemoteTaskError, ValueError, TypeError) as exc:
            return self._record_error(
                envelope,
                "REMOTE_TASK_PLAN_APPROVAL_REJECTED",
                detail=str(exc),
            )

        event = self.session_store.append_event(
            envelope["session_id"],
            "task_receipt",
            {
                "request_id": envelope["request_id"],
                "task_id": task_id,
                "plan_digest": plan_digest,
                "approval_event_seq": submitted["seq"],
                "receipt": copy.deepcopy(receipt),
            },
        )
        return self._remember(
            envelope,
            {
                "status": receipt.get("status", "FAILED"),
                "session_id": envelope["session_id"],
                "request_id": envelope["request_id"],
                "mission_id": None,
                "task_id": task_id,
                "plan_digest": plan_digest,
                "event_seq": event["seq"],
            },
        )

    def handle(self, raw_envelope: object) -> dict:
        """Validate, correlate and dispatch one durable remote request."""
        try:
            envelope = parse_client_envelope(raw_envelope)
        except RemoteProtocolError as exc:
            raise RemoteRuntimeBridgeError(str(exc)) from exc

        with self._dispatch_lock:
            session = self._owned_open_session(
                envelope["session_id"], envelope["device_id"]
            )
            existing = self._existing_request_result(session, envelope)
            if existing is not None:
                return existing

            kind = envelope["kind"]
            if kind == "message":
                return self._handle_message(envelope)
            if kind == "command":
                return self._handle_command(envelope)
            if kind == "task":
                return self._handle_task(envelope)
            if kind == "approve_action":
                return self._handle_approval(envelope)
            if kind == "approve_plan":
                return self._handle_plan_approval(envelope)
            raise RemoteRuntimeBridgeError("REMOTE_REQUEST_KIND_NOT_IMPLEMENTED")
