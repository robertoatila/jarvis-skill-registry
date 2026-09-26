"""Per-device identity, one-time pairing and selective revocation for Remote Companion."""

from __future__ import annotations

import copy
import hashlib
import hmac
import json
import os
import re
import secrets
import tempfile
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

SCHEMA_VERSION = 1
DEFAULT_PAIRING_TTL_SECONDS = 120
LAST_SEEN_PERSIST_INTERVAL_SECONDS = 60
_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9._:-]{1,256}$")


class RemoteDeviceError(ValueError):
    """Raised when pairing/device state or a transition is invalid."""


def _identifier(value: object, field: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER_RE.fullmatch(value):
        raise RemoteDeviceError(f"{field} is invalid")
    return value


def _text(value: object, field: str, *, max_length: int = 128) -> str:
    if not isinstance(value, str):
        raise RemoteDeviceError(f"{field} must be a string")
    normalized = value.strip()
    if not normalized or len(normalized) > max_length or "\r" in normalized or "\n" in normalized:
        raise RemoteDeviceError(f"{field} is invalid")
    return normalized


def _utc_iso(timestamp: float) -> str:
    return datetime.fromtimestamp(float(timestamp), timezone.utc).isoformat()


def _secret_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RemoteDevice:
    device_id: str
    label: str
    status: str
    paired_at: str
    last_seen_at: str | None
    credential_fingerprint: str


class RemoteDeviceRegistry:
    """Atomic device registry; raw pairing/device credentials are never persisted."""

    def __init__(
        self,
        state_dir: Path,
        *,
        clock: Callable[[], float] = time.time,
        id_factory: Optional[Callable[[], str]] = None,
        pairing_ttl_seconds: float = DEFAULT_PAIRING_TTL_SECONDS,
    ) -> None:
        self.state_dir = Path(state_dir)
        self.state_path = self.state_dir / "remote_devices.json"
        self.clock = clock
        self.id_factory = id_factory or (lambda: secrets.token_hex(16))
        try:
            ttl = float(pairing_ttl_seconds)
        except (TypeError, ValueError) as exc:
            raise RemoteDeviceError("pairing TTL is invalid") from exc
        if ttl <= 0 or ttl > 3600:
            raise RemoteDeviceError("pairing TTL is invalid")
        self.pairing_ttl_seconds = ttl
        self._lock = threading.RLock()
        self._state = self._load()

    @staticmethod
    def _empty() -> dict:
        return {"schema_version": SCHEMA_VERSION, "devices": {}, "offers": {}}

    def _expire_and_prune_offers_locked(self, now: float) -> bool:
        offers = self._state["offers"]
        changed = False
        for record in offers.values():
            if (
                record.get("status") == "PENDING"
                and now > float(record.get("expires_at", 0.0))
            ):
                record["status"] = "EXPIRED"
                changed = True

        terminal = sorted(
            (
                (offer_id, record)
                for offer_id, record in offers.items()
                if record.get("status") != "PENDING"
            ),
            key=lambda item: (
                float(
                    item[1].get("consumed_at")
                    or item[1].get("expires_at")
                    or item[1].get("created_at")
                    or 0.0
                ),
                item[0],
            ),
        )
        for offer_id, _record in terminal:
            if len(offers) < MAX_PAIRING_OFFERS:
                break
            offers.pop(offer_id, None)
            changed = True
        return changed

    def _prune_revoked_devices_locked(self) -> bool:
        devices = self._state["devices"]
        changed = False
        revoked = sorted(
            (
                (device_id, record)
                for device_id, record in devices.items()
                if record.get("status") == "REVOKED"
            ),
            key=lambda item: (str(item[1].get("paired_at", "")), item[0]),
        )
        for device_id, _record in revoked:
            if len(devices) < MAX_DEVICE_RECORDS:
                break
            devices.pop(device_id, None)
            changed = True
        return changed

    def _load(self) -> dict:
        if not self.state_path.exists():
            return self._empty()
        try:
            value = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise RemoteDeviceError("remote device registry is unreadable") from exc
        if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
            raise RemoteDeviceError("unsupported remote device schema")
        devices = value.get("devices")
        offers = value.get("offers")
        if not isinstance(devices, dict) or not isinstance(offers, dict):
            raise RemoteDeviceError("remote device registry is invalid")
        for device_id, record in devices.items():
            self._validate_device_record(device_id, record)
        for offer_id, record in offers.items():
            self._validate_offer_record(offer_id, record)
        return value

    @staticmethod
    def _validate_device_record(device_id: object, record: object) -> None:
        _identifier(device_id, "device_id")
        if not isinstance(record, dict) or record.get("device_id") != device_id:
            raise RemoteDeviceError("remote device entry is invalid")
        _text(record.get("label"), "device label")
        if record.get("status") not in {"ACTIVE", "REVOKED"}:
            raise RemoteDeviceError("remote device status is invalid")
        if not isinstance(record.get("paired_at"), str):
            raise RemoteDeviceError("remote device paired_at is invalid")
        if record.get("last_seen_at") is not None and not isinstance(record.get("last_seen_at"), str):
            raise RemoteDeviceError("remote device last_seen_at is invalid")
        fingerprint = record.get("credential_fingerprint")
        if not isinstance(fingerprint, str) or not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
            raise RemoteDeviceError("remote device fingerprint is invalid")

    @staticmethod
    def _validate_offer_record(offer_id: object, record: object) -> None:
        _identifier(offer_id, "offer_id")
        if not isinstance(record, dict) or record.get("offer_id") != offer_id:
            raise RemoteDeviceError("pairing offer entry is invalid")
        secret_hash = record.get("pairing_secret_hash")
        if not isinstance(secret_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", secret_hash):
            raise RemoteDeviceError("pairing offer secret hash is invalid")
        if record.get("status") not in {"PENDING", "CONSUMED", "EXPIRED"}:
            raise RemoteDeviceError("pairing offer status is invalid")
        for field in ("created_at", "expires_at"):
            value = record.get(field)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise RemoteDeviceError(f"pairing offer {field} is invalid")
        label_hint = record.get("label_hint")
        if label_hint is not None:
            _text(label_hint, "label_hint")

    def _save(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(self._state, ensure_ascii=False, indent=2, sort_keys=True)
        fd, temporary = tempfile.mkstemp(prefix="remote_devices.", suffix=".tmp", dir=str(self.state_dir))
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(encoded)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.state_path)
        except Exception:
            try:
                os.unlink(temporary)
            except OSError:
                pass
            raise

    def _new_id(self, field: str) -> str:
        value = _identifier(self.id_factory(), field)
        return value

    @staticmethod
    def _public_device(record: dict) -> RemoteDevice:
        return RemoteDevice(
            device_id=record["device_id"],
            label=record["label"],
            status=record["status"],
            paired_at=record["paired_at"],
            last_seen_at=record.get("last_seen_at"),
            credential_fingerprint=record["credential_fingerprint"],
        )

    def create_pairing_offer(self, *, label_hint: str | None = None) -> dict:
        normalized_hint = _text(label_hint, "label_hint") if label_hint is not None else None
        with self._lock:
            now = float(self.clock())
            changed = self._expire_and_prune_offers_locked(now)
            pending = sum(
                1
                for record in self._state["offers"].values()
                if record.get("status") == "PENDING"
            )
            if pending >= MAX_PENDING_PAIRING_OFFERS:
                if changed:
                    self._save()
                raise RemoteDeviceError("too many pending pairing offers")
            if len(self._state["offers"]) >= MAX_PAIRING_OFFERS:
                if changed:
                    self._save()
                raise RemoteDeviceError("pairing offer registry is at capacity")
            offer_id = self._new_id("offer_id")
            if offer_id in self._state["offers"]:
                raise RemoteDeviceError("pairing offer id already exists")
            pairing_secret = secrets.token_urlsafe(32)
            expires_at = now + self.pairing_ttl_seconds
            self._state["offers"][offer_id] = {
                "offer_id": offer_id,
                "label_hint": normalized_hint,
                "pairing_secret_hash": _secret_hash(pairing_secret),
                "status": "PENDING",
                "created_at": now,
                "expires_at": expires_at,
                "consumed_at": None,
                "device_id": None,
            }
            self._save()
            return {
                "schema_version": SCHEMA_VERSION,
                "offer_id": offer_id,
                "label_hint": normalized_hint,
                "pairing_secret": pairing_secret,
                "created_at": now,
                "expires_at": expires_at,
            }

    def complete_pairing(self, offer_id: str, proof: dict) -> RemoteDevice:
        normalized_offer = _identifier(offer_id, "offer_id")
        if not isinstance(proof, dict):
            raise RemoteDeviceError("pairing proof must be an object")
        pairing_secret = proof.get("pairing_secret")
        credential = proof.get("credential")
        if not isinstance(pairing_secret, str) or len(pairing_secret) < 32 or len(pairing_secret) > 512:
            raise RemoteDeviceError("pairing proof is invalid")
        if not isinstance(credential, str) or len(credential) < 32 or len(credential) > 512:
            raise RemoteDeviceError("device credential is invalid")

        with self._lock:
            offer = self._state["offers"].get(normalized_offer)
            if offer is None:
                raise RemoteDeviceError("pairing offer does not exist")
            if offer["status"] == "CONSUMED":
                raise RemoteDeviceError("pairing offer has already been consumed")
            now = float(self.clock())
            if offer["status"] == "EXPIRED" or now > float(offer["expires_at"]):
                offer["status"] = "EXPIRED"
                self._save()
                raise RemoteDeviceError("pairing offer expired")
            expected = offer["pairing_secret_hash"]
            if not hmac.compare_digest(_secret_hash(pairing_secret), expected):
                raise RemoteDeviceError("pairing proof is invalid")

            label_value = proof.get("label") or offer.get("label_hint")
            label = _text(label_value, "device label")
            active_devices = sum(
                1
                for record in self._state["devices"].values()
                if record.get("status") == "ACTIVE"
            )
            if active_devices >= MAX_ACTIVE_DEVICES:
                raise RemoteDeviceError("too many active remote devices")
            changed = self._prune_revoked_devices_locked()
            if len(self._state["devices"]) >= MAX_DEVICE_RECORDS:
                if changed:
                    self._save()
                raise RemoteDeviceError("remote device registry is at capacity")
            device_id = self._new_id("device_id")
            if device_id in self._state["devices"]:
                raise RemoteDeviceError("device id already exists")
            fingerprint = _secret_hash(credential)
            paired_at = _utc_iso(now)
            record = {
                "device_id": device_id,
                "label": label,
                "status": "ACTIVE",
                "paired_at": paired_at,
                "last_seen_at": None,
                "credential_fingerprint": fingerprint,
            }
            self._state["devices"][device_id] = record
            offer["status"] = "CONSUMED"
            offer["consumed_at"] = now
            offer["device_id"] = device_id
            self._save()
            return self._public_device(record)

    def authenticate(self, device_id: str, proof: dict) -> bool:
        try:
            normalized_device = _identifier(device_id, "device_id")
        except RemoteDeviceError:
            return False
        if not isinstance(proof, dict):
            return False
        credential = proof.get("credential")
        if not isinstance(credential, str) or len(credential) < 32 or len(credential) > 512:
            return False

        with self._lock:
            record = self._state["devices"].get(normalized_device)
            if record is None or record.get("status") != "ACTIVE":
                return False
            if not hmac.compare_digest(_secret_hash(credential), record["credential_fingerprint"]):
                return False
            now = float(self.clock())
            persist_seen = True
            previous_seen = record.get("last_seen_at")
            if isinstance(previous_seen, str):
                try:
                    previous_ts = datetime.fromisoformat(previous_seen).timestamp()
                    persist_seen = (
                        now < previous_ts
                        or now - previous_ts >= LAST_SEEN_PERSIST_INTERVAL_SECONDS
                    )
                except (TypeError, ValueError, OverflowError):
                    persist_seen = True
            if persist_seen:
                record["last_seen_at"] = _utc_iso(now)
                self._save()
            return True

    def is_active(self, device_id: str) -> bool:
        try:
            normalized_device = _identifier(device_id, "device_id")
        except RemoteDeviceError:
            return False
        with self._lock:
            record = self._state["devices"].get(normalized_device)
            return bool(record and record.get("status") == "ACTIVE")

    def get(self, device_id: str) -> RemoteDevice | None:
        normalized_device = _identifier(device_id, "device_id")
        with self._lock:
            record = self._state["devices"].get(normalized_device)
            return self._public_device(record) if record is not None else None

    def list_devices(self) -> list[RemoteDevice]:
        with self._lock:
            return [
                self._public_device(self._state["devices"][device_id])
                for device_id in sorted(self._state["devices"])
            ]

    def revoke(self, device_id: str) -> RemoteDevice:
        normalized_device = _identifier(device_id, "device_id")
        with self._lock:
            record = self._state["devices"].get(normalized_device)
            if record is None:
                raise RemoteDeviceError("remote device does not exist")
            record["status"] = "REVOKED"
            self._save()
            return self._public_device(record)

    @staticmethod
    def as_dict(device: RemoteDevice) -> dict:
        return asdict(device)
