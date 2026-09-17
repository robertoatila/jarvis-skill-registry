"""Truthful resident-host lifecycle state for J.A.R.V.I.S. Remote Companion.

The persisted file is only a last-known host declaration. It is never treated
as proof of liveness: an ONLINE record is projected as ONLINE only when its PID
can still be probed successfully. This module also assembles the versioned
remote HTTP server around the existing J.A.R.V.I.S. server/runtime surface.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import socket
import tempfile
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable, Optional

SCHEMA_VERSION = 1
ALLOWED_TRANSPORTS = {"none", "local", "lan", "overlay", "relay"}


class RemoteHostError(ValueError):
    """Raised when resident-host lifecycle state violates the public contract."""


def _nonempty_string(value: object, field: str, *, max_length: int = 256) -> str:
    if not isinstance(value, str):
        raise RemoteHostError(f"{field} must be a string")
    normalized = value.strip()
    if (
        not normalized
        or len(normalized) > max_length
        or "\r" in normalized
        or "\n" in normalized
    ):
        raise RemoteHostError(f"{field} is invalid")
    return normalized


def _default_pid_probe(pid: int) -> bool:
    """Return whether a process id appears alive without modifying the process."""
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        # The process exists but the current user cannot signal it.
        return True
    except (ProcessLookupError, OSError, ValueError):
        return False


class RemoteHostController:
    """Persist and truthfully project home-PC host availability."""

    def __init__(
        self,
        state_dir: Path,
        *,
        clock: Callable[[], float] = time.time,
        pid_probe: Optional[Callable[[int], bool]] = None,
    ) -> None:
        self.state_dir = Path(state_dir)
        self.state_path = self.state_dir / "remote_host.json"
        self.clock = clock
        self.pid_probe = pid_probe or _default_pid_probe
        self._lock = threading.RLock()

    def _read_persisted(self) -> Optional[dict]:
        if not self.state_path.exists():
            return None
        try:
            value = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise RemoteHostError("remote host state is unreadable") from exc
        if not isinstance(value, dict):
            raise RemoteHostError("remote host state must be an object")
        if value.get("schema_version") != SCHEMA_VERSION:
            raise RemoteHostError("unsupported remote host schema")
        status = value.get("status")
        if status not in {"ONLINE", "OFFLINE"}:
            raise RemoteHostError("remote host status is invalid")
        return value

    def _atomic_write(self, value: dict) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
        fd, temp_name = tempfile.mkstemp(
            prefix="remote_host.", suffix=".tmp", dir=str(self.state_dir)
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(encoded)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, self.state_path)
        except Exception:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
            raise

    @staticmethod
    def _validate_online_state(value: dict) -> None:
        _nonempty_string(value.get("host_id"), "host_id")
        pid = value.get("pid")
        if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
            raise RemoteHostError("pid is invalid")
        port = value.get("port")
        if not isinstance(port, int) or isinstance(port, bool) or not (1 <= port <= 65535):
            raise RemoteHostError("port is invalid")
        if not isinstance(value.get("remote_enabled"), bool):
            raise RemoteHostError("remote_enabled must be boolean")
        if value.get("transport") not in ALLOWED_TRANSPORTS:
            raise RemoteHostError("transport is invalid")
        started_at = value.get("started_at")
        if not isinstance(started_at, (int, float)) or isinstance(started_at, bool):
            raise RemoteHostError("started_at is invalid")

    def publish_online(
        self,
        *,
        host_id: str,
        pid: int,
        port: int,
        remote_enabled: bool,
        transport: str,
    ) -> dict:
        """Persist an ONLINE declaration for the currently starting host process."""
        normalized_host = _nonempty_string(host_id, "host_id")
        if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
            raise RemoteHostError("pid is invalid")
        if not isinstance(port, int) or isinstance(port, bool) or not (1 <= port <= 65535):
            raise RemoteHostError("port is invalid")
        if not isinstance(remote_enabled, bool):
            raise RemoteHostError("remote_enabled must be boolean")
        if transport not in ALLOWED_TRANSPORTS:
            raise RemoteHostError("transport is invalid")

        now = float(self.clock())
        value = {
            "schema_version": SCHEMA_VERSION,
            "host_id": normalized_host,
            "status": "ONLINE",
            "pid": pid,
            "started_at": now,
            "updated_at": now,
            "port": port,
            "remote_enabled": remote_enabled,
            "transport": transport,
        }
        with self._lock:
            self._atomic_write(value)
        return copy.deepcopy(value)

    def publish_offline(self, reason: str = "STOPPED") -> dict:
        """Persist an explicit OFFLINE state while retaining useful host metadata."""
        normalized_reason = _nonempty_string(reason, "reason", max_length=128)
        with self._lock:
            previous = self._read_persisted()
            now = float(self.clock())
            value = {
                "schema_version": SCHEMA_VERSION,
                "status": "OFFLINE",
                "reason": normalized_reason,
                "updated_at": now,
            }
            if previous:
                for field in (
                    "host_id",
                    "started_at",
                    "port",
                    "remote_enabled",
                    "transport",
                ):
                    if field in previous:
                        value[field] = previous[field]
                if isinstance(previous.get("pid"), int):
                    value["last_known_pid"] = previous["pid"]
            self._atomic_write(value)
            return copy.deepcopy(value)

    def status(self) -> dict:
        """Return current host availability, verifying liveness for ONLINE records."""
        with self._lock:
            persisted = self._read_persisted()
            checked_at = float(self.clock())
            if persisted is None:
                return {
                    "schema_version": SCHEMA_VERSION,
                    "status": "OFFLINE",
                    "reason": "NOT_STARTED",
                    "checked_at": checked_at,
                }

            if persisted["status"] == "OFFLINE":
                result = copy.deepcopy(persisted)
                result["checked_at"] = checked_at
                result.pop("pid", None)
                return result

            self._validate_online_state(persisted)
            pid = persisted["pid"]
            try:
                alive = bool(self.pid_probe(pid))
            except Exception:
                alive = False

            if alive:
                result = copy.deepcopy(persisted)
                result["checked_at"] = checked_at
                return result

            result = {
                "schema_version": SCHEMA_VERSION,
                "status": "OFFLINE",
                "reason": "STALE_PID",
                "last_known_pid": pid,
                "checked_at": checked_at,
            }
            for field in (
                "host_id",
                "started_at",
                "updated_at",
                "port",
                "remote_enabled",
                "transport",
            ):
                if field in persisted:
                    result[field] = persisted[field]
            return result

    def start_foreground(
        self,
        server,
        *,
        host_id: str,
        pid: int,
        port: int,
        remote_enabled: bool,
        transport: str,
        resident_context=None,
    ) -> None:
        """Publish liveness around one HTTP server and optional host-owned context."""
        if resident_context is not None:
            if not callable(getattr(resident_context, "start", None)):
                raise TypeError("resident_context must expose start()")
            if not callable(getattr(resident_context, "stop", None)):
                raise TypeError("resident_context must expose stop()")

        self.publish_online(
            host_id=host_id,
            pid=pid,
            port=port,
            remote_enabled=remote_enabled,
            transport=transport,
        )
        context_started = False
        try:
            if resident_context is not None:
                resident_context.start()
                context_started = True
            server.serve_forever()
        finally:
            try:
                if context_started:
                    resident_context.stop()
            finally:
                try:
                    self.publish_offline("STOPPED")
                finally:
                    server.server_close()


def build_transport_status_provider(base_provider: Callable[[], dict], remote_transport):
    """Decorate truthful host status with the currently verified transport state."""
    from tooling.remote_transport import RemoteTransport

    if not callable(base_provider):
        raise TypeError("base_provider must be callable")
    if not isinstance(remote_transport, RemoteTransport):
        raise TypeError("remote_transport must be RemoteTransport")

    def provider() -> dict:
        base = base_provider()
        if not isinstance(base, dict):
            raise RemoteHostError("host status provider returned invalid data")
        result = copy.deepcopy(base)
        result["transport_status"] = remote_transport.status().to_dict()
        return result

    return provider


def bind_host_for_transport(status) -> str:
    """Extract a bindable host only from an explicitly verified ACTIVE endpoint."""
    from tooling.remote_transport import RemoteTransportStatus, TransportState

    if not isinstance(status, RemoteTransportStatus):
        raise TypeError("status must be RemoteTransportStatus")
    if status.state is not TransportState.ACTIVE:
        raise RemoteHostError("remote transport is not active")
    if not status.public_or_private_endpoint or not status.last_verified_at:
        raise RemoteHostError("remote transport endpoint is not verified")

    parsed = urllib.parse.urlsplit(status.public_or_private_endpoint)
    if (
        parsed.scheme not in {"http", "https"}
        or parsed.username
        or parsed.password
        or not parsed.hostname
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise RemoteHostError("remote transport endpoint is invalid")
    return parsed.hostname


def build_loopback_runtime_adapter(port: int, host: str = "127.0.0.1") -> Callable[[dict], dict]:
    """Reuse the established local `/api/chat` runtime without accepting phone secrets."""
    if not isinstance(port, int) or isinstance(port, bool) or not (1 <= port <= 65535):
        raise RemoteHostError("port is invalid")
    normalized_host = _nonempty_string(host, "host", max_length=255)
    url = f"http://{normalized_host}:{port}/api/chat"

    def adapter(runtime_request: dict) -> dict:
        if not isinstance(runtime_request, dict):
            raise ValueError("runtime request must be an object")
        text = runtime_request.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("runtime request text is invalid")
        payload = runtime_request.get("payload")
        payload = payload if isinstance(payload, dict) else {}
        provider = payload.get("provider", "")
        model = payload.get("model", "")
        provider = provider.strip() if isinstance(provider, str) else ""
        model = model.strip() if isinstance(model, str) else ""
        body = json.dumps(
            {
                "message": text,
                "provider": provider,
                "model": model,
                # Provider credentials stay PC-side. Remote payload secrets are ignored.
                "apiKey": "",
            },
            ensure_ascii=False,
        ).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
        if not isinstance(result, dict):
            raise ValueError("local runtime returned a malformed result")
        return result

    return adapter


def build_default_remote_transport(*, port: int, remote_enabled: bool):
    """Choose a truthful default local/LAN transport for the resident launcher."""
    from tooling.remote_auth import detect_local_ip
    from tooling.remote_transport_local import LanRemoteTransport, LocalRemoteTransport

    if not isinstance(remote_enabled, bool):
        raise TypeError("remote_enabled must be boolean")
    if not remote_enabled:
        return LocalRemoteTransport(port=port)

    detected_ip = detect_local_ip()
    try:
        return LanRemoteTransport(host=detected_ip, port=port)
    except (TypeError, ValueError) as exc:
        raise RemoteHostError("remote LAN mode requires a detected private non-loopback address") from exc


def create_remote_server(
    server_address,
    *,
    state_dir: Path,
    runtime_adapter: Callable[[dict], dict] | None = None,
    host_controller: RemoteHostController | None = None,
    remote_auth=None,
    device_registry=None,
    remote_transport=None,
    resident_context=None,
):
    """Assemble the remote API around one existing resident J.A.R.V.I.S. runtime."""
    from tooling.remote_http import RemoteJarvisHttpHandler, RemoteJarvisServer
    from tooling.remote_runtime_bridge import RemoteRuntimeBridge
    from tooling.remote_sessions import RemoteSessionStore
    from tooling.resident_host_context import ResidentHostContext

    if resident_context is not None:
        if not isinstance(resident_context, ResidentHostContext):
            raise TypeError("resident_context must be ResidentHostContext")
        if runtime_adapter is not None and runtime_adapter is not resident_context.runtime_adapter:
            raise RemoteHostError("runtime_adapter must match resident_context")
        if (
            remote_transport is not None
            and resident_context.remote_transport is not None
            and remote_transport is not resident_context.remote_transport
        ):
            raise RemoteHostError("remote_transport must match resident_context")
        runtime_adapter = resident_context.runtime_adapter
        if remote_transport is None:
            remote_transport = resident_context.remote_transport

    if not callable(runtime_adapter):
        raise TypeError("runtime_adapter must be callable")

    state_dir = Path(state_dir)
    controller = host_controller or RemoteHostController(state_dir)
    validator = device_registry.is_active if device_registry is not None else None
    store = RemoteSessionStore(state_dir, device_validator=validator)
    bridge = RemoteRuntimeBridge(store, runtime_adapter=runtime_adapter)
    status_provider = (
        build_transport_status_provider(controller.status, remote_transport)
        if remote_transport is not None
        else controller.status
    )
    server = RemoteJarvisServer(
        server_address,
        RemoteJarvisHttpHandler,
        session_store=store,
        runtime_bridge=bridge,
        host_status_provider=status_provider,
        remote_auth=remote_auth,
        device_registry=device_registry,
        remote_transport=remote_transport,
    )
    server.resident_context = resident_context
    return server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the resident J.A.R.V.I.S. remote host")
    parser.add_argument("--port", type=int, default=8899, help="Host port (default: 8899)")
    parser.add_argument("--host", type=str, default=None, help="Explicit bind host")
    parser.add_argument("--remote", action="store_true", help="Allow authenticated LAN/private remote access")
    parser.add_argument(
        "--transport",
        choices=("local", "lan", "tailscale"),
        default=None,
        help="Explicit remote transport; --remote remains an alias for LAN mode",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.port < 1 or args.port > 65535:
        print("Port must be between 1 and 65535.")
        return 2

    from tooling import jarvis_server
    from tooling.remote_devices import RemoteDeviceRegistry
    from tooling.resident_host_context import ResidentHostContext

    transport_mode = args.transport or ("lan" if args.remote else "local")
    if args.remote and transport_mode == "local":
        raise RemoteHostError("--remote cannot be combined with local transport")

    remote_enabled = transport_mode != "local"
    if transport_mode == "tailscale":
        from tooling.remote_transport_tailscale import TailscaleRemoteTransport

        remote_transport = TailscaleRemoteTransport(port=args.port)
        verified_status = remote_transport.start()
        verified_bind_host = bind_host_for_transport(verified_status)
        if args.host is not None and args.host != verified_bind_host:
            raise RemoteHostError("--host must match the verified Tailscale endpoint")
        bind_host = verified_bind_host
        host_transport = "overlay"
    else:
        remote_transport = build_default_remote_transport(
            port=args.port,
            remote_enabled=remote_enabled,
        )
        bind_host = args.host or ("0.0.0.0" if remote_enabled else "127.0.0.1")
        host_transport = "lan" if remote_enabled else "local"

    jarvis_server.load_starred_catalog()
    jarvis_server.load_canonical_skills()

    controller = RemoteHostController(jarvis_server.STATE_DIR)
    device_registry = RemoteDeviceRegistry(jarvis_server.STATE_DIR)
    runtime_adapter = build_loopback_runtime_adapter(args.port)
    resident_context = ResidentHostContext(
        jarvis_server.REGISTRY_ROOT,
        state_dir=jarvis_server.STATE_DIR,
        runtime_adapter=runtime_adapter,
        remote_transport=remote_transport,
    )
    server = create_remote_server(
        (bind_host, args.port),
        state_dir=jarvis_server.STATE_DIR,
        resident_context=resident_context,
        host_controller=controller,
        remote_auth=jarvis_server.REMOTE_AUTH if remote_enabled else None,
        device_registry=device_registry,
    )
    host_id = socket.gethostname().strip() or "home-pc"

    print("J.A.R.V.I.S. resident host starting")
    print(f"  Bind: {bind_host}:{args.port}")
    print(f"  Remote: {'enabled' if remote_enabled else 'local only'}")
    try:
        controller.start_foreground(
            server,
            host_id=host_id,
            pid=os.getpid(),
            port=args.port,
            remote_enabled=remote_enabled,
            transport=host_transport,
            resident_context=resident_context,
        )
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
