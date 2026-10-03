"""Host-owned background context for one authoritative resident J.A.R.V.I.S.

The context coordinates an already-existing runtime adapter, one bidirectional
Obsidian bridge / MemoryFabric, and one optional remote transport.  It does not
construct per-device runtimes or memories.  Reconciliation failures degrade the
Vault subsystem without terminating the resident host.
"""

from __future__ import annotations

import copy
import threading
from pathlib import Path
from typing import Callable

from tooling.remote_transport import RemoteTransport, TransportState


class ResidentHostContextError(ValueError):
    """Raised when resident context construction violates its contract."""


class ResidentHostContext:
    """Own one process-level runtime/memory context and background reconcile loop."""

    def __init__(
        self,
        root: Path,
        *,
        runtime_adapter: Callable[[dict], dict],
        vault_bridge=None,
        remote_transport: RemoteTransport | None = None,
        state_dir: Path | None = None,
        reconcile_interval_seconds: float = 30.0,
    ) -> None:
        root = Path(root).resolve()
        if not root.exists() or not root.is_dir():
            raise ResidentHostContextError("root must be an existing directory")
        if not callable(runtime_adapter):
            raise TypeError("runtime_adapter must be callable")
        try:
            interval = float(reconcile_interval_seconds)
        except (TypeError, ValueError) as exc:
            raise ResidentHostContextError("reconcile interval is invalid") from exc
        if interval <= 0:
            raise ResidentHostContextError("reconcile interval must be positive")
        if remote_transport is not None and not isinstance(remote_transport, RemoteTransport):
            raise TypeError("remote_transport must be RemoteTransport or None")

        if vault_bridge is None:
            from tooling.agentic.bidirectional_vault import BidirectionalVaultBridge

            vault_bridge = BidirectionalVaultBridge(
                root,
                state_dir=Path(state_dir) if state_dir is not None else root / "state",
            )
        if not callable(getattr(vault_bridge, "reconcile_once", None)):
            raise TypeError("vault_bridge must expose reconcile_once()")
        if not callable(getattr(vault_bridge, "status", None)):
            raise TypeError("vault_bridge must expose status()")
        if not hasattr(vault_bridge, "memory_fabric"):
            raise TypeError("vault_bridge must expose memory_fabric")

        self.root = root
        self.runtime_adapter = runtime_adapter
        self.vault_bridge = vault_bridge
        self.memory_fabric = vault_bridge.memory_fabric
        self.remote_transport = remote_transport
        self.reconcile_interval_seconds = interval

        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._running = False
        self._transport_started = False
        self._transport_error: str | None = None
        self._reconciliation_status = "STOPPED"
        self._last_success: dict | None = None
        self._last_error: str | None = None

    @staticmethod
    def _error_text(exc: BaseException) -> str:
        return f"{type(exc).__name__}: {exc}"

    def _ensure_transport_active(self):
        """Retry a configured transport until it becomes active."""
        if self.remote_transport is None:
            return None
        try:
            current = self.remote_transport.status()
        except Exception:
            current = None
        if current is not None and getattr(current, "state", None) is TransportState.ACTIVE:
            with self._lock:
                self._transport_started = True
                self._transport_error = None
            return current
        try:
            started = self.remote_transport.start()
        except Exception as exc:
            with self._lock:
                self._transport_started = False
                self._transport_error = self._error_text(exc)
            return None
        active = getattr(started, "state", None) is TransportState.ACTIVE
        with self._lock:
            self._transport_started = active
            self._transport_error = None if active else getattr(started, "detail", "transport unavailable")
        return started

    def reconcile_once(self) -> dict:
        """Run one bounded reconcile attempt without allowing a fault to escape."""
        try:
            result = self.vault_bridge.reconcile_once()
            if not isinstance(result, dict):
                raise TypeError("vault reconciliation returned invalid result")
        except Exception as exc:
            error = self._error_text(exc)
            with self._lock:
                self._reconciliation_status = "DEGRADED"
                self._last_error = error
            return {"status": "DEGRADED", "error": error}

        normalized = copy.deepcopy(result)
        with self._lock:
            self._last_success = copy.deepcopy(normalized)
            if normalized.get("status") == "SUCCESS":
                self._reconciliation_status = "ACTIVE"
                self._last_error = None
            else:
                self._reconciliation_status = "DEGRADED"
                detail = normalized.get("error") or normalized.get("errors")
                self._last_error = str(detail) if detail else "reconciliation returned non-success status"
        return normalized

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            self._ensure_transport_active()
            self.reconcile_once()
            if self._stop_event.wait(self.reconcile_interval_seconds):
                break

    def start(self) -> dict:
        """Start transport and one daemon reconciliation loop, idempotently."""
        with self._lock:
            if self._running:
                return self.status()

            self._stop_event = threading.Event()
            self._transport_error = None
            self._transport_started = False

            self._running = True
            self._reconciliation_status = "STARTING"
            self._ensure_transport_active()
            self._thread = threading.Thread(
                target=self._run_loop,
                name="jarvis-vault-reconcile",
                daemon=True,
            )
            self._thread.start()
            return self.status()

    def stop(self) -> dict:
        """Stop the loop and configured transport exactly once per active start."""
        with self._lock:
            if not self._running:
                return self.status()
            self._running = False
            self._stop_event.set()
            thread = self._thread
            self._thread = None
            should_stop_transport = self._transport_started
            self._transport_started = False

        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=max(1.0, min(self.reconcile_interval_seconds + 1.0, 5.0)))

        if should_stop_transport and self.remote_transport is not None:
            try:
                self.remote_transport.stop()
            except Exception as exc:
                with self._lock:
                    self._transport_error = self._error_text(exc)

        with self._lock:
            self._reconciliation_status = "STOPPED"
            return self.status()

    def _transport_status(self):
        if self.remote_transport is None:
            return None
        try:
            current = self.remote_transport.status()
            payload = current.to_dict()
            if getattr(current, "state", None) is TransportState.ACTIVE:
                # Publish one coherent snapshot: an observed ACTIVE transport
                # must not retain a stale error from an earlier startup attempt.
                self._transport_started = True
                self._transport_error = None
            return payload
        except Exception as exc:
            return {
                "state": "ERROR",
                "detail": self._error_text(exc),
            }

    def _vault_status(self) -> dict:
        try:
            value = self.vault_bridge.status()
            return copy.deepcopy(value) if isinstance(value, dict) else {"status": "UNKNOWN"}
        except Exception as exc:
            return {"status": "DEGRADED", "error": self._error_text(exc)}

    def status(self) -> dict:
        """Return bounded operational status without exposing runtime/memory contents."""
        with self._lock:
            return {
                "running": self._running,
                "reconcile_interval_seconds": self.reconcile_interval_seconds,
                "reconciliation": {
                    "status": self._reconciliation_status,
                    "last_success": copy.deepcopy(self._last_success),
                    "last_error": self._last_error,
                },
                "transport": self._transport_status(),
                "transport_error": self._transport_error,
                "vault": self._vault_status(),
            }
