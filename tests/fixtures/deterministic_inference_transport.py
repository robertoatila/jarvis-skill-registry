"""Deterministic no-network HTTP transport fixture for inference adapter tests.

The fixture patches only urllib.request.build_opener at the adapter boundary.
It records actual opener attempts and returns a scripted response/failure without
performing external I/O. Production code must not import this module.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any
import urllib.error
from unittest.mock import patch


@dataclass(frozen=True)
class TransportAttempt:
    method: str
    url: str
    headers: dict[str, str]
    body: bytes | None
    timeout: float | None


class _FixtureResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload
        self.read_sizes: list[int | None] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def read(self, size: int | None = None) -> bytes:
        self.read_sizes.append(size)
        if size is None:
            return self._payload
        return self._payload[:size]


class _FixtureOpener:
    def __init__(self, owner: "DeterministicHttpTransport") -> None:
        self.owner = owner

    def open(self, request, *, timeout=None):
        attempt = TransportAttempt(
            method=request.get_method(),
            url=request.full_url,
            headers={key: value for key, value in request.header_items()},
            body=request.data,
            timeout=timeout,
        )
        self.owner.attempts.append(attempt)

        if self.owner.mode == "timeout":
            raise TimeoutError("deterministic fixture timeout")
        if self.owner.mode == "http_error":
            raise urllib.error.HTTPError(
                request.full_url,
                self.owner.http_status,
                "deterministic fixture HTTP error",
                {},
                None,
            )
        return _FixtureResponse(self.owner.payload)


class DeterministicHttpTransport:
    """Scripted opener replacement that can never reach the network."""

    def __init__(
        self,
        *,
        mode: str,
        payload: bytes = b"",
        http_status: int | None = None,
    ) -> None:
        if mode not in {"response", "http_error", "timeout"}:
            raise ValueError("unsupported deterministic transport mode")
        if mode == "http_error" and (
            isinstance(http_status, bool)
            or not isinstance(http_status, int)
            or http_status < 100
            or http_status > 599
        ):
            raise ValueError("invalid deterministic HTTP status")
        self.mode = mode
        self.payload = bytes(payload)
        self.http_status = http_status
        self.attempts: list[TransportAttempt] = []
        self._opener = _FixtureOpener(self)

    @classmethod
    def json_response(cls, payload: Any) -> "DeterministicHttpTransport":
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return cls(mode="response", payload=encoded)

    @classmethod
    def http_error(cls, status: int) -> "DeterministicHttpTransport":
        return cls(mode="http_error", http_status=status)

    @classmethod
    def timeout(cls) -> "DeterministicHttpTransport":
        return cls(mode="timeout")

    @property
    def attempt_count(self) -> int:
        return len(self.attempts)

    def install(self):
        """Patch the stdlib opener factory used by HttpInferenceAdapter."""
        return patch("urllib.request.build_opener", return_value=self._opener)
