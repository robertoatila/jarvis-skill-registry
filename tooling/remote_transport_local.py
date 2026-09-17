"""Local and LAN transport adapters for Remote Companion compatibility."""

from __future__ import annotations

import ipaddress
import time
from typing import Callable

from tooling.remote_transport import RemoteTransport, RemoteTransportStatus, TransportState, utc_iso_from_clock


def _validate_port(port: int) -> int:
    if not isinstance(port, int) or isinstance(port, bool) or not (1 <= port <= 65535):
        raise ValueError("port is invalid")
    return port


class LocalRemoteTransport(RemoteTransport):
    def __init__(self, *, port: int = 8899, clock: Callable[[], float] = time.time) -> None:
        self.port = _validate_port(port)
        self.clock = clock
        self._status = RemoteTransportStatus(
            transport_id="local",
            state=TransportState.STOPPED,
            public_or_private_endpoint=None,
            last_verified_at=None,
            detail="local transport stopped",
        )

    def start(self) -> RemoteTransportStatus:
        self._status = RemoteTransportStatus(
            transport_id="local",
            state=TransportState.ACTIVE,
            public_or_private_endpoint=f"http://127.0.0.1:{self.port}",
            last_verified_at=utc_iso_from_clock(self.clock),
            detail="loopback endpoint verified by configuration",
        )
        return self._status

    def status(self) -> RemoteTransportStatus:
        return self._status

    def stop(self) -> RemoteTransportStatus:
        self._status = RemoteTransportStatus(
            transport_id="local",
            state=TransportState.STOPPED,
            public_or_private_endpoint=None,
            last_verified_at=None,
            detail="local transport stopped",
        )
        return self._status


class LanRemoteTransport(RemoteTransport):
    def __init__(
        self,
        *,
        host: str,
        port: int = 8899,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.port = _validate_port(port)
        self.clock = clock
        try:
            address = ipaddress.ip_address(host)
        except ValueError as exc:
            raise ValueError("LAN host is invalid") from exc
        if address.is_loopback or address.is_multicast or address.is_unspecified:
            raise ValueError("LAN host must be a non-loopback private address")
        if not (address.is_private or address.is_link_local):
            raise ValueError("LAN transport does not accept public addresses")
        self.host = str(address)
        self._status = RemoteTransportStatus(
            transport_id="lan",
            state=TransportState.STOPPED,
            public_or_private_endpoint=None,
            last_verified_at=None,
            detail="LAN transport stopped",
        )

    def start(self) -> RemoteTransportStatus:
        endpoint_host = f"[{self.host}]" if ":" in self.host else self.host
        self._status = RemoteTransportStatus(
            transport_id="lan",
            state=TransportState.ACTIVE,
            public_or_private_endpoint=f"http://{endpoint_host}:{self.port}",
            last_verified_at=utc_iso_from_clock(self.clock),
            detail="private LAN endpoint selected",
        )
        return self._status

    def status(self) -> RemoteTransportStatus:
        return self._status

    def stop(self) -> RemoteTransportStatus:
        self._status = RemoteTransportStatus(
            transport_id="lan",
            state=TransportState.STOPPED,
            public_or_private_endpoint=None,
            last_verified_at=None,
            detail="LAN transport stopped",
        )
        return self._status
