"""HTTPS Tailscale Serve transport for the J.A.R.V.I.S. Remote Companion.

The JARVIS HTTP server stays loopback-only. Tailscale Serve terminates HTTPS on
its tailnet DNS name and proxies to the local backend. Device credentials remain
mandatory at the JARVIS remote API even though the backend connection itself is
loopback.

This adapter refuses to overwrite an unrelated existing Serve handler on the
selected HTTPS port.
"""

from __future__ import annotations

import ipaddress
import json
import re
import subprocess
import time
from typing import Callable

from tooling.remote_transport import (
    RemoteTransport,
    RemoteTransportStatus,
    TransportState,
    utc_iso_from_clock,
)

_TAILSCALE_V4 = ipaddress.ip_network("100.64.0.0/10")
_TAILSCALE_V6 = ipaddress.ip_network("fd7a:115c:a1e0::/48")
_DNS_NAME_RE = re.compile(
    r"^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$"
)


def _valid_port(value: int, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not (1 <= value <= 65535):
        raise ValueError(f"{field} is invalid")
    return value


def _is_tailnet_address(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False
    return address in (_TAILSCALE_V4 if address.version == 4 else _TAILSCALE_V6)


def _dns_name(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().rstrip(".")
    if not normalized or not _DNS_NAME_RE.fullmatch(normalized):
        return None
    return normalized.lower()


class TailscaleServeRemoteTransport(RemoteTransport):
    """Expose the loopback-only JARVIS host through Tailscale Serve HTTPS."""

    def __init__(
        self,
        *,
        backend_port: int = 8899,
        https_port: int = 443,
        runner: Callable = subprocess.run,
        clock: Callable[[], float] = time.time,
        adopt_only: bool = False,
    ) -> None:
        self.backend_port = _valid_port(backend_port, "backend_port")
        self.https_port = _valid_port(https_port, "https_port")
        if not callable(runner):
            raise TypeError("runner must be callable")
        if not isinstance(adopt_only, bool):
            raise TypeError("adopt_only must be boolean")
        self.runner = runner
        self.clock = clock
        self.adopt_only = adopt_only
        self._configured_by_instance = False
        self._status = RemoteTransportStatus(
            transport_id="tailscale-serve",
            state=TransportState.STOPPED,
            public_or_private_endpoint=None,
            last_verified_at=None,
            detail="Tailscale Serve transport stopped",
        )

    @property
    def trusted_source_networks(self) -> tuple[str, ...]:
        # The backend accepts only the loopback reverse-proxy connection.
        return ()

    @property
    def trusted_reverse_proxy_endpoint(self) -> str | None:
        if self._status.state is not TransportState.ACTIVE:
            return None
        return self._status.public_or_private_endpoint

    @property
    def requires_device_auth_on_loopback(self) -> bool:
        return True

    @property
    def target(self) -> str:
        return f"http://127.0.0.1:{self.backend_port}"

    def _run(self, args: list[str], *, timeout: float = 5.0):
        try:
            return self.runner(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except (FileNotFoundError, OSError, subprocess.SubprocessError):
            return None

    def _unavailable(self, detail: str) -> RemoteTransportStatus:
        self._status = RemoteTransportStatus(
            transport_id="tailscale-serve",
            state=TransportState.UNAVAILABLE,
            public_or_private_endpoint=None,
            last_verified_at=None,
            detail=detail[:512],
        )
        return self._status

    def _tailscale_identity(self) -> tuple[str, str] | None:
        result = self._run(["tailscale", "status", "--json"], timeout=3.0)
        if result is None or getattr(result, "returncode", 1) != 0:
            return None
        try:
            payload = json.loads(getattr(result, "stdout", ""))
        except (TypeError, json.JSONDecodeError):
            return None
        if not isinstance(payload, dict) or payload.get("BackendState") != "Running":
            return None
        self_status = payload.get("Self")
        if not isinstance(self_status, dict) or self_status.get("Online") is not True:
            return None
        addresses = self_status.get("TailscaleIPs")
        if not isinstance(addresses, list):
            return None
        tailnet_ip = next((item for item in addresses if _is_tailnet_address(item)), None)
        dns_name = _dns_name(self_status.get("DNSName"))
        if tailnet_ip is None or dns_name is None:
            return None
        return dns_name, tailnet_ip

    def _serve_config(self) -> dict | None:
        result = self._run(["tailscale", "serve", "status", "--json"], timeout=5.0)
        if result is None or getattr(result, "returncode", 1) != 0:
            return None
        raw = getattr(result, "stdout", "")
        try:
            payload = json.loads(raw or "{}")
        except (TypeError, json.JSONDecodeError):
            return None
        return payload if isinstance(payload, dict) else None

    def _expected_handler(self, config: dict, dns_name: str) -> bool:
        tcp = config.get("TCP")
        web = config.get("Web")
        if not isinstance(tcp, dict) or not isinstance(web, dict):
            return False

        tcp_record = tcp.get(str(self.https_port))
        if not isinstance(tcp_record, dict) or tcp_record.get("HTTPS") is not True:
            return False

        host_key = f"{dns_name}:{self.https_port}"
        web_record = web.get(host_key)
        if not isinstance(web_record, dict):
            return False
        handlers = web_record.get("Handlers")
        if not isinstance(handlers, dict):
            return False
        root_handler = handlers.get("/")
        return isinstance(root_handler, dict) and root_handler.get("Proxy") == self.target

    def _port_has_other_config(self, config: dict, dns_name: str) -> bool:
        tcp = config.get("TCP")
        web = config.get("Web")
        tcp = tcp if isinstance(tcp, dict) else {}
        web = web if isinstance(web, dict) else {}
        if str(self.https_port) in tcp:
            return True
        return f"{dns_name}:{self.https_port}" in web

    def _endpoint(self, dns_name: str) -> str:
        suffix = "" if self.https_port == 443 else f":{self.https_port}"
        return f"https://{dns_name}{suffix}"

    def start(self) -> RemoteTransportStatus:
        identity = self._tailscale_identity()
        if identity is None:
            return self._unavailable("Tailscale node/DNS identity is unavailable")
        dns_name, _tailnet_ip = identity

        current = self._serve_config()
        if current is None:
            return self._unavailable("Tailscale Serve status is unavailable")

        if self._expected_handler(current, dns_name):
            # Preserve ownership if this same process created the mapping during an
            # earlier idempotent start() call.
            endpoint = self._endpoint(dns_name)
            self._status = RemoteTransportStatus(
                transport_id="tailscale-serve",
                state=TransportState.ACTIVE,
                public_or_private_endpoint=endpoint,
                last_verified_at=utc_iso_from_clock(self.clock),
                detail=f"verified HTTPS reverse proxy to {self.target}",
            )
            return self._status

        if self._port_has_other_config(current, dns_name):
            return self._unavailable(
                f"Tailscale Serve HTTPS port {self.https_port} already has unrelated configuration"
            )

        if self.adopt_only:
            return self._unavailable(
                "JARVIS Tailscale Serve mapping is not provisioned; "
                "run 'python jarvis.py remote-serve provision' from an elevated Windows terminal"
            )

        configure = self._run(
            [
                "tailscale",
                "serve",
                "--bg",
                "--yes",
                f"--https={self.https_port}",
                self.target,
            ],
            timeout=15.0,
        )
        if configure is None or getattr(configure, "returncode", 1) != 0:
            detail = ""
            if configure is not None:
                detail = (getattr(configure, "stderr", "") or getattr(configure, "stdout", "") or "").strip()
            return self._unavailable(
                "Tailscale Serve configuration failed"
                + (f": {detail[:300]}" if detail else "")
            )
        self._configured_by_instance = True

        verified = self._serve_config()
        if verified is None or not self._expected_handler(verified, dns_name):
            return self._unavailable("Tailscale Serve did not verify the requested JARVIS proxy")

        endpoint = self._endpoint(dns_name)
        self._status = RemoteTransportStatus(
            transport_id="tailscale-serve",
            state=TransportState.ACTIVE,
            public_or_private_endpoint=endpoint,
            last_verified_at=utc_iso_from_clock(self.clock),
            detail=f"verified HTTPS reverse proxy to {self.target}",
        )
        return self._status

    def status(self) -> RemoteTransportStatus:
        return self._status

    def stop(self) -> RemoteTransportStatus:
        detail = "JARVIS Tailscale Serve transport stopped"
        if self._configured_by_instance:
            result = self._run(
                [
                    "tailscale",
                    "serve",
                    "--bg",
                    "--yes",
                    f"--https={self.https_port}",
                    "off",
                ],
                timeout=10.0,
            )
            if result is None or getattr(result, "returncode", 1) != 0:
                self._status = RemoteTransportStatus(
                    transport_id="tailscale-serve",
                    state=TransportState.ERROR,
                    public_or_private_endpoint=self._status.public_or_private_endpoint,
                    last_verified_at=self._status.last_verified_at,
                    detail="failed to remove JARVIS-owned Tailscale Serve mapping",
                )
                return self._status
            detail += "; JARVIS-owned Serve mapping removed"
            self._configured_by_instance = False
        else:
            detail += "; pre-existing matching Serve mapping left unchanged"

        self._status = RemoteTransportStatus(
            transport_id="tailscale-serve",
            state=TransportState.STOPPED,
            public_or_private_endpoint=None,
            last_verified_at=None,
            detail=detail,
        )
        return self._status
