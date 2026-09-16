"""Provider-neutral transport contracts for J.A.R.V.I.S. Remote Companion."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable


class TransportState(str, Enum):
    STOPPED = "STOPPED"
    ACTIVE = "ACTIVE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


def utc_iso_from_clock(clock: Callable[[], float]) -> str:
    value = float(clock())
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class RemoteTransportStatus:
    transport_id: str
    state: TransportState
    public_or_private_endpoint: str | None
    last_verified_at: str | None
    detail: str

    def __post_init__(self) -> None:
        if not isinstance(self.transport_id, str) or not self.transport_id.strip():
            raise ValueError("transport_id is invalid")
        if not isinstance(self.state, TransportState):
            raise TypeError("state must be TransportState")
        if self.public_or_private_endpoint is not None and not isinstance(
            self.public_or_private_endpoint, str
        ):
            raise TypeError("endpoint must be a string or None")
        if self.last_verified_at is not None and not isinstance(self.last_verified_at, str):
            raise TypeError("last_verified_at must be a string or None")
        if not isinstance(self.detail, str):
            raise TypeError("detail must be a string")

    def to_dict(self) -> dict:
        return {
            "transport_id": self.transport_id,
            "state": self.state.value,
            "public_or_private_endpoint": self.public_or_private_endpoint,
            "last_verified_at": self.last_verified_at,
            "detail": self.detail,
        }


class RemoteTransport(ABC):
    """Replaceable reachability layer. Reachability never grants execution authority."""

    @abstractmethod
    def start(self) -> RemoteTransportStatus:
        raise NotImplementedError

    @abstractmethod
    def status(self) -> RemoteTransportStatus:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> RemoteTransportStatus:
        raise NotImplementedError
