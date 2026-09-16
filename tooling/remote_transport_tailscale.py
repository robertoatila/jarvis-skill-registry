"""Read-only Tailscale transport adapter for beyond-LAN Remote Companion access."""

from __future__ import annotations

import ipaddress
import json
import subprocess
import time
from typing import Callable

from tooling.remote_transport import RemoteTransport, RemoteTransportStatus, TransportState, utc_iso_from_clock

_TAILSCALE_V4 = ipaddress.ip_network("100.64.0.0/10")
_TAILSCALE_V6 = ipaddress.ip_network("fd7a:115c:a1e0::/48")


def _validate_port(port: int) -> int:
    if not isinstance(port, int) or isinstance(port, bool) or not (1 <= port <= 65535):
        raise ValueError("port is invalid")
    return port


def _is_tailnet_address(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False
    return address in (_TAILSCALE_V4 if address.version == 4 else _TAILSCALE_V6)


class TailscaleRemoteTransport(RemoteTransport):
    """Adopt an already-running tailnet without mutating global VPN state."""

    def __init__(
        self,
        *,
        port: int = 8899,
        runner: Callable = subprocess.run,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.port = _validate_port(port)
        if not callable(runner):
            raise TypeError("runner must be callable")
        self.runner = runner
        self.clock = clock
        self._status = RemoteTransportStatus(
            transport_id="tailscale",
            state=TransportState.STOPPED,
            public_or_private_endpoint=None,
            last_verified_at=None,
            detail="Tailscale transport stopped",
        )

    def _unavailable(self, detail: str) -> RemoteTransportStatus:
        self._status = RemoteTransportStatus(
            transport_id="tailscale",
            state=TransportState.UNAVAILABLE,
            public_or_private_endpoint=None,
            last_verified_at=None,
            detail=detail,
        )
        return self._status

    def start(self) -> RemoteTransportStatus:
        try:
            result = self.runner(
                ["tailscale", "status", "--json"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
        except (FileNotFoundError, OSError, subprocess.SubprocessError):
            return self._unavailable("Tailscale CLI unavailable")

        if getattr(result, "returncode", 1) != 0:
            return self._unavailable("Tailscale status command failed")

        try:
            payload = json.loads(getattr(result, "stdout", ""))
        except (TypeError, json.JSONDecodeError):
            return self._unavailable("Tailscale status output is invalid")

        if not isinstance(payload, dict) or payload.get("BackendState") != "Running":
            return self._unavailable("Tailscale backend is not running")
        self_status = payload.get("Self")
        if not isinstance(self_status, dict) or self_status.get("Online") is not True:
            return self._unavailable("Tailscale node is not online")
        addresses = self_status.get("TailscaleIPs")
        if not isinstance(addresses, list):
            return self._unavailable("Tailscale node has no verified tailnet address")

        address = next((item for item in addresses if _is_tailnet_address(item)), None)
        if address is None:
            return self._unavailable("Tailscale node has no verified tailnet address")

        endpoint_host = f"[{address}]" if ":" in address else address
        self._status = RemoteTransportStatus(
            transport_id="tailscale",
            state=TransportState.ACTIVE,
            public_or_private_endpoint=f"http://{endpoint_host}:{self.port}",
            last_verified_at=utc_iso_from_clock(self.clock),
            detail="verified active tailnet endpoint",
        )
        return self._status

    def status(self) -> RemoteTransportStatus:
        return self._status

    def stop(self) -> RemoteTransportStatus:
        # This adapter does not own the machine-wide Tailscale service and therefore
        # deliberately does not execute `tailscale down` or mutate tailnet state.
        self._status = RemoteTransportStatus(
            transport_id="tailscale",
            state=TransportState.STOPPED,
            public_or_private_endpoint=None,
            last_verified_at=None,
            detail="JARVIS Tailscale transport stopped; tailnet service left unchanged",
        )
        return self._status
