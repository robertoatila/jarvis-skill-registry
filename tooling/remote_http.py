"""Versioned HTTP surface for the J.A.R.V.I.S. Remote Companion.

The handler subclasses the existing desktop HTTP handler and intercepts only
``/api/remote/v1``. Every other route delegates to the established server, so
this module is additive and does not create a parallel desktop API stack.
"""

from __future__ import annotations

import re
import urllib.parse
from typing import Callable, Optional

from tooling.http_security import (
    read_json_request,
    validate_authorized_request,
    validate_local_request,
    validate_pairing_offer_source,
)
from tooling.jarvis_server import JarvisHttpHandler, ThreadingJarvisServer
from tooling.remote_devices import RemoteDeviceError, RemoteDeviceRegistry
from tooling.remote_runtime_bridge import RemoteRuntimeBridge, RemoteRuntimeBridgeError
from tooling.remote_sessions import RemoteSessionError, RemoteSessionStore
from tooling.remote_transport import RemoteTransport

REMOTE_API_PREFIX = "/api/remote/v1"
_SESSION_PATH_RE = re.compile(r"^/api/remote/v1/sessions/([A-Za-z0-9._:-]{1,256})$")
_EVENTS_PATH_RE = re.compile(r"^/api/remote/v1/sessions/([A-Za-z0-9._:-]{1,256})/events$")
_MESSAGES_PATH_RE = re.compile(r"^/api/remote/v1/sessions/([A-Za-z0-9._:-]{1,256})/messages$")
_ACK_PATH_RE = re.compile(r"^/api/remote/v1/sessions/([A-Za-z0-9._:-]{1,256})/ack$")
_CLOSE_PATH_RE = re.compile(r"^/api/remote/v1/sessions/([A-Za-z0-9._:-]{1,256})/close$")
_PAIRING_OFFERS_PATH = f"{REMOTE_API_PREFIX}/pairing/offers"
_PAIRING_COMPLETE_PATH = f"{REMOTE_API_PREFIX}/pairing/complete"


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
        device_registry: RemoteDeviceRegistry | None = None,
        remote_transport: RemoteTransport | None = None,
    ) -> None:
        if not isinstance(session_store, RemoteSessionStore):
            raise TypeError("session_store must be RemoteSessionStore")
        if not isinstance(runtime_bridge, RemoteRuntimeBridge):
            raise TypeError("runtime_bridge must be RemoteRuntimeBridge")
        if not callable(host_status_provider):
            raise TypeError("host_status_provider must be callable")
        if device_registry is not None and not isinstance(device_registry, RemoteDeviceRegistry):
            raise TypeError("device_registry must be RemoteDeviceRegistry")
        if remote_transport is not None and not isinstance(remote_transport, RemoteTransport):
            raise TypeError("remote_transport must be RemoteTransport")
        self.session_store = session_store
        self.runtime_bridge = runtime_bridge
        self.host_status_provider = host_status_provider
        self.remote_auth = remote_auth
        self.device_registry = device_registry
        self.remote_transport = remote_transport
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

    def _device_credential_header(self) -> str:
        value = self.headers.get("X-Jarvis-Device-Credential", "")
        return value.strip() if isinstance(value, str) else ""

    def _request_security_context(self) -> tuple[str, str, str, int, str]:
        return (
            self.client_address[0],
            self.headers.get("Host", ""),
            self.headers.get("Origin", ""),
            self.server.server_port,
            self.headers.get("Sec-Fetch-Site", ""),
        )

    def _transport_networks(self) -> tuple[str, ...]:
        transport = getattr(self.server, "remote_transport", None)
        if transport is None:
            return ()
        networks = getattr(transport, "trusted_source_networks", ())
        return tuple(networks) if networks else ()

    def _is_local_request(self) -> bool:
        return validate_local_request(*self._request_security_context())

    def _guard_remote_request(self) -> bool:
        """Use per-device proof when configured; otherwise preserve legacy guard."""
        self._authenticated_device_id = None
        if self._is_local_request():
            return True

        registry = getattr(self.server, "device_registry", None)
        if registry is None:
            return self.guard_local_request()

        device_id = self._device_header()
        credential = self._device_credential_header()
        if not device_id or not credential:
            self._remote_error(403, "REMOTE_DEVICE_CREDENTIAL_REQUIRED")
            return False

        client_ip, host, origin, port, fetch_site = self._request_security_context()
        if not validate_authorized_request(
            client_ip,
            host,
            origin,
            port,
            fetch_site,
            token=credential,
            expected_token=credential,
            allowed_networks=self._transport_networks(),
        ):
            self._remote_error(403, "REMOTE_DEVICE_TRANSPORT_REJECTED")
            return False
        if not registry.authenticate(device_id, {"credential": credential}):
            self._remote_error(403, "REMOTE_DEVICE_NOT_AUTHORIZED")
            return False
        self._authenticated_device_id = device_id
        return True

    def _guard_pairing_offer(self) -> bool:
        if self._is_local_request():
            return True
        pairing_endpoint = self._verified_pairing_endpoint()
        if pairing_endpoint and validate_pairing_offer_source(
            self.client_address[0], pairing_endpoint
        ):
            return True
        self._remote_error(403, "PAIRING_OFFER_LOCAL_ONLY")
        return False

    def _verified_pairing_endpoint(self) -> str | None:
        """Return a verified transport origin suitable for a remote pairing link."""
        try:
            host_status = self.server.host_status_provider()
        except Exception:
            return None
        if not isinstance(host_status, dict):
            return None
        transport = host_status.get("transport_status")
        if not isinstance(transport, dict):
            return None
        if transport.get("state") != "ACTIVE" or not transport.get("last_verified_at"):
            return None
        endpoint = transport.get("public_or_private_endpoint")
        if not isinstance(endpoint, str) or not endpoint.strip():
            return None
        try:
            parsed = urllib.parse.urlsplit(endpoint.strip())
        except (TypeError, ValueError):
            return None
        if (
            parsed.scheme not in {"http", "https"}
            or parsed.username
            or parsed.password
            or not parsed.hostname
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            return None
        return f"{parsed.scheme}://{parsed.netloc}"

    def _guard_pairing_completion(self, pairing_secret: object) -> bool:
        if self._is_local_request():
            return True
        if not isinstance(pairing_secret, str) or not pairing_secret:
            self._remote_error(403, "PAIRING_TRANSPORT_REJECTED")
            return False
        client_ip, host, origin, port, fetch_site = self._request_security_context()
        if validate_authorized_request(
            client_ip,
            host,
            origin,
            port,
            fetch_site,
            token=pairing_secret,
            expected_token=pairing_secret,
            allowed_networks=self._transport_networks(),
        ):
            return True
        self._remote_error(403, "PAIRING_TRANSPORT_REJECTED")
        return False

    def _owned_session(self, session_id: str, device_id: str):
        session = self.server.session_store.get_session(session_id)
        if session is None:
            self._remote_error(404, "REMOTE_SESSION_NOT_FOUND")
            return None
        if not device_id or session.get("device_id") != device_id:
            self._remote_error(403, "REMOTE_SESSION_DEVICE_MISMATCH")
            return None
        registry = getattr(self.server, "device_registry", None)
        if registry is not None and not registry.is_active(device_id):
            self._remote_error(403, "REMOTE_DEVICE_NOT_AUTHORIZED")
            return None
        authenticated = getattr(self, "_authenticated_device_id", None)
        if authenticated is not None and authenticated != device_id:
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

        if path == _PAIRING_OFFERS_PATH:
            if not self._guard_pairing_offer():
                return
            registry = getattr(self.server, "device_registry", None)
            if registry is None:
                self._remote_error(404, "PAIRING_NOT_CONFIGURED")
                return
            body = self._read_remote_body()
            if body is None:
                return
            label_hint = body.get("label_hint")
            if label_hint is not None and not isinstance(label_hint, str):
                self._remote_error(400, "INVALID_PAIRING_LABEL")
                return
            try:
                offer = registry.create_pairing_offer(label_hint=label_hint)
            except RemoteDeviceError:
                self._remote_error(400, "INVALID_PAIRING_OFFER")
                return
            pairing_endpoint = self._verified_pairing_endpoint()
            if pairing_endpoint is not None:
                offer["pairing_endpoint"] = pairing_endpoint
            self.send_json(offer, 201)
            return

        if path == _PAIRING_COMPLETE_PATH:
            registry = getattr(self.server, "device_registry", None)
            if registry is None:
                self._remote_error(404, "PAIRING_NOT_CONFIGURED")
                return
            body = self._read_remote_body()
            if body is None:
                return
            if not self._guard_pairing_completion(body.get("pairing_secret")):
                return
            offer_id = body.get("offer_id")
            if not isinstance(offer_id, str):
                self._remote_error(400, "INVALID_PAIRING_OFFER")
                return
            try:
                device = registry.complete_pairing(offer_id, body)
            except RemoteDeviceError as exc:
                reason = str(exc).lower()
                status = 409 if "expired" in reason or "consumed" in reason else 400
                self._remote_error(status, "PAIRING_REJECTED")
                return
            self.send_json(RemoteDeviceRegistry.as_dict(device), 201)
            return

        if path == f"{REMOTE_API_PREFIX}/sessions":
            body = self._read_remote_body()
            if body is None:
                return
            device_id = body.get("device_id")
            if not isinstance(device_id, str) or not device_id.strip():
                self._remote_error(400, "INVALID_DEVICE_ID")
                return
            device_id = device_id.strip()
            registry = getattr(self.server, "device_registry", None)
            if registry is not None:
                if not registry.is_active(device_id):
                    self._remote_error(403, "REMOTE_DEVICE_NOT_AUTHORIZED")
                    return
                authenticated = getattr(self, "_authenticated_device_id", None)
                if authenticated is not None and authenticated != device_id:
                    self._remote_error(403, "REMOTE_SESSION_DEVICE_MISMATCH")
                    return
            try:
                session = self.server.session_store.create_session(device_id)
            except RemoteSessionError as exc:
                if "device" in str(exc).lower():
                    self._remote_error(403, "REMOTE_DEVICE_NOT_AUTHORIZED")
                else:
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
            registry = getattr(self.server, "device_registry", None)
            if registry is not None:
                device_id = body.get("device_id")
                if not isinstance(device_id, str) or self._owned_session(session_id, device_id.strip()) is None:
                    if not isinstance(device_id, str):
                        self._remote_error(400, "INVALID_DEVICE_ID")
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
            if not self._guard_remote_request():
                return
            self._handle_remote_get()
            return
        super().do_GET()

    def do_POST(self):
        path = self._parsed_remote_path().path
        if path.startswith(REMOTE_API_PREFIX):
            if path in {_PAIRING_OFFERS_PATH, _PAIRING_COMPLETE_PATH}:
                self._handle_remote_post()
                return
            if not self._guard_remote_request():
                return
            self._handle_remote_post()
            return
        super().do_POST()
