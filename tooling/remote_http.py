"""Versioned HTTP surface for the J.A.R.V.I.S. Remote Companion.

The handler subclasses the existing desktop HTTP handler and intercepts only
``/api/remote/v1``. Every other route delegates to the established server, so
this module is additive and does not create a parallel desktop API stack.
"""

from __future__ import annotations

import re
import urllib.parse
from typing import Callable, Optional

from tooling.http_security import read_json_request
from tooling.jarvis_server import JarvisHttpHandler, ThreadingJarvisServer
from tooling.remote_runtime_bridge import RemoteRuntimeBridge, RemoteRuntimeBridgeError
from tooling.remote_sessions import RemoteSessionError, RemoteSessionStore

REMOTE_API_PREFIX = "/api/remote/v1"
_SESSION_PATH_RE = re.compile(r"^/api/remote/v1/sessions/([A-Za-z0-9._:-]{1,256})$")
_EVENTS_PATH_RE = re.compile(r"^/api/remote/v1/sessions/([A-Za-z0-9._:-]{1,256})/events$")
_MESSAGES_PATH_RE = re.compile(r"^/api/remote/v1/sessions/([A-Za-z0-9._:-]{1,256})/messages$")
_ACK_PATH_RE = re.compile(r"^/api/remote/v1/sessions/([A-Za-z0-9._:-]{1,256})/ack$")
_CLOSE_PATH_RE = re.compile(r"^/api/remote/v1/sessions/([A-Za-z0-9._:-]{1,256})/close$")


class RemoteJarvisServer(ThreadingJarvisServer):
    """Existing threaded J.A.R.V.I.S. server with remote-session dependencies."""

    def __init__(
        self,
        server_address,
        RequestHandlerClass=None,
        *,
        session_store: RemoteSessionStore,
        runtime_bridge: RemoteRuntimeBridge,
        host_status_provider: Callable[[], dict],
        remote_auth=None,
    ) -> None:
        if not isinstance(session_store, RemoteSessionStore):
            raise TypeError("session_store must be RemoteSessionStore")
        if not isinstance(runtime_bridge, RemoteRuntimeBridge):
            raise TypeError("runtime_bridge must be RemoteRuntimeBridge")
        if not callable(host_status_provider):
            raise TypeError("host_status_provider must be callable")
        self.session_store = session_store
        self.runtime_bridge = runtime_bridge
        self.host_status_provider = host_status_provider
        self.remote_auth = remote_auth
        super().__init__(server_address, RequestHandlerClass or RemoteJarvisHttpHandler)


class RemoteJarvisHttpHandler(JarvisHttpHandler):
    """Add `/api/remote/v1` while preserving the established handler as fallback."""

    def _parsed_remote_path(self):
        return urllib.parse.urlsplit(self.path)

    def _remote_error(self, status: int, reason: str) -> None:
        self.send_json({"status": "ERROR", "reason": reason}, status)

    def _read_remote_body(self) -> Optional[dict]:
        try:
            return read_json_request(self.headers, self.rfile)
        except (ValueError, TypeError, UnicodeError):
            self._remote_error(400, "INVALID_JSON_REQUEST")
            return None

    def _device_header(self) -> str:
        value = self.headers.get("X-Jarvis-Device-ID", "")
        return value.strip() if isinstance(value, str) else ""

    def _owned_session(self, session_id: str, device_id: str):
        session = self.server.session_store.get_session(session_id)
        if session is None:
            self._remote_error(404, "REMOTE_SESSION_NOT_FOUND")
            return None
        if not device_id or session.get("device_id") != device_id:
            self._remote_error(403, "REMOTE_SESSION_DEVICE_MISMATCH")
            return None
        return session

    @staticmethod
    def _bridge_http_status(exc: RemoteRuntimeBridgeError) -> int:
        reason = str(exc)
        if reason == "REMOTE_SESSION_NOT_FOUND":
            return 404
        if reason == "REMOTE_SESSION_DEVICE_MISMATCH":
            return 403
        if reason == "REMOTE_SESSION_CLOSED":
            return 409
        return 400

    def _handle_remote_get(self) -> None:
        parsed = self._parsed_remote_path()
        path = parsed.path

        if path == f"{REMOTE_API_PREFIX}/host":
            try:
                status = self.server.host_status_provider()
            except Exception:
                self._remote_error(503, "REMOTE_HOST_STATUS_UNAVAILABLE")
                return
            if not isinstance(status, dict):
                self._remote_error(503, "REMOTE_HOST_STATUS_UNAVAILABLE")
                return
            self.send_json(status, 200)
            return

        match = _EVENTS_PATH_RE.fullmatch(path)
        if match:
            session_id = match.group(1)
            if self._owned_session(session_id, self._device_header()) is None:
                return
            try:
                query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
                after_values = query.get("after", ["0"])
                limit_values = query.get("limit", ["100"])
                if len(after_values) != 1 or len(limit_values) != 1:
                    raise ValueError
                after = int(after_values[0])
                limit = int(limit_values[0])
                events = self.server.session_store.events_after(
                    session_id, after=after, limit=limit
                )
            except (ValueError, RemoteSessionError):
                self._remote_error(400, "INVALID_EVENT_CURSOR")
                return
            self.send_json(
                {"session_id": session_id, "after": after, "events": events}, 200
            )
            return

        match = _SESSION_PATH_RE.fullmatch(path)
        if match:
            session_id = match.group(1)
            session = self._owned_session(session_id, self._device_header())
            if session is None:
                return
            self.send_json(session, 200)
            return

        self._remote_error(404, "REMOTE_ROUTE_NOT_FOUND")

    def _handle_remote_post(self) -> None:
        parsed = self._parsed_remote_path()
        path = parsed.path

        if path == f"{REMOTE_API_PREFIX}/sessions":
            body = self._read_remote_body()
            if body is None:
                return
            device_id = body.get("device_id")
            if not isinstance(device_id, str) or not device_id.strip():
                self._remote_error(400, "INVALID_DEVICE_ID")
                return
            try:
                session = self.server.session_store.create_session(device_id.strip())
            except RemoteSessionError:
                self._remote_error(400, "INVALID_REMOTE_SESSION")
                return
            self.send_json(session, 201)
            return

        match = _MESSAGES_PATH_RE.fullmatch(path)
        if match:
            body = self._read_remote_body()
            if body is None:
                return
            session_id = match.group(1)
            if body.get("session_id") != session_id:
                self._remote_error(400, "REMOTE_SESSION_PATH_MISMATCH")
                return
            try:
                result = self.server.runtime_bridge.handle(body)
            except RemoteRuntimeBridgeError as exc:
                self._remote_error(self._bridge_http_status(exc), str(exc))
                return
            self.send_json(result, 202)
            return

        match = _ACK_PATH_RE.fullmatch(path)
        if match:
            body = self._read_remote_body()
            if body is None:
                return
            session_id = match.group(1)
            device_id = body.get("device_id")
            if not isinstance(device_id, str):
                self._remote_error(400, "INVALID_DEVICE_ID")
                return
            if self._owned_session(session_id, device_id.strip()) is None:
                return
            try:
                session = self.server.session_store.ack(session_id, body.get("seq"))
            except RemoteSessionError:
                self._remote_error(400, "INVALID_ACKNOWLEDGEMENT")
                return
            self.send_json(session, 200)
            return

        match = _CLOSE_PATH_RE.fullmatch(path)
        if match:
            body = self._read_remote_body()
            if body is None:
                return
            session_id = match.group(1)
            device_id = body.get("device_id")
            if not isinstance(device_id, str):
                self._remote_error(400, "INVALID_DEVICE_ID")
                return
            if self._owned_session(session_id, device_id.strip()) is None:
                return
            try:
                session = self.server.session_store.close_session(session_id)
            except RemoteSessionError:
                self._remote_error(400, "INVALID_REMOTE_SESSION")
                return
            self.send_json(session, 200)
            return

        self._remote_error(404, "REMOTE_ROUTE_NOT_FOUND")

    def do_GET(self):
        if self._parsed_remote_path().path.startswith(REMOTE_API_PREFIX):
            if not self.guard_local_request():
                return
            self._handle_remote_get()
            return
        super().do_GET()

    def do_POST(self):
        if self._parsed_remote_path().path.startswith(REMOTE_API_PREFIX):
            if not self.guard_local_request():
                return
            self._handle_remote_post()
            return
        super().do_POST()
