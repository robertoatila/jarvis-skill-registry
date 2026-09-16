"""Persistent provenance-aware catalog for capabilities outside the local JARVIS runtime.

Cataloged capability metadata is not execution authority. Provider/user manifests
may only introduce KNOWN/UNVERIFIED records. Executable availability is a
separate, time-bounded verification state established by trusted runtime code.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
import time
from typing import Any, Callable


SCHEMA_VERSION = 1
DEFAULT_VERIFICATION_TTL_SECONDS = 15 * 60
MAX_CAPABILITIES_PER_MANIFEST = 512
MAX_STATE_BYTES = 4 * 1024 * 1024

_ID_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$')
_KIND_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$')
_ALLOWED_MANIFEST_FIELDS = {
    'schema_version',
    'source_id',
    'observed_at',
    'source_provenance',
    'capabilities',
}
_ALLOWED_CAPABILITY_FIELDS = {
    'capability_id',
    'name',
    'provider',
    'kind',
    'capabilities',
    'availability',
}
_SECRET_FIELDS = {
    'cookie',
    'cookies',
    'access_token',
    'refresh_token',
    'session_token',
    'api_key',
    'apikey',
    'password',
    'authorization',
    'client_secret',
}


class CapabilityAvailability(str, Enum):
    KNOWN = 'KNOWN'
    UNVERIFIED = 'UNVERIFIED'
    AVAILABLE_LOCAL = 'AVAILABLE_LOCAL'
    AVAILABLE_DELEGATED = 'AVAILABLE_DELEGATED'
    UNAVAILABLE = 'UNAVAILABLE'
    REVOKED = 'REVOKED'


@dataclass(frozen=True)
class ExternalCapability:
    schema_version: int
    source_id: str
    capability_id: str
    name: str
    provider: str
    kind: str
    provenance: str
    capabilities: list[str]
    availability_state: CapabilityAvailability
    invocation_mode: str
    last_observed_at: str
    last_verified_at: str | None
    metadata_hash: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data['availability_state'] = self.availability_state.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'ExternalCapability':
        if not isinstance(data, dict):
            raise ValueError('Invalid external capability record')
        try:
            state = CapabilityAvailability(data['availability_state'])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError('Invalid external capability availability') from exc
        item = cls(
            schema_version=data.get('schema_version'),
            source_id=data.get('source_id'),
            capability_id=data.get('capability_id'),
            name=data.get('name'),
            provider=data.get('provider'),
            kind=data.get('kind'),
            provenance=data.get('provenance'),
            capabilities=list(data.get('capabilities', [])),
            availability_state=state,
            invocation_mode=data.get('invocation_mode'),
            last_observed_at=data.get('last_observed_at'),
            last_verified_at=data.get('last_verified_at'),
            metadata_hash=data.get('metadata_hash'),
        )
        _validate_external_capability(item)
        return item


def _reject_linked_path(path: Path) -> None:
    for part in (path, *path.parents):
        try:
            linked = part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction())
        except OSError as exc:
            raise ValueError('Unable to validate external capability state path') from exc
        if linked:
            raise ValueError('Linked external capability state paths are not supported')


def _require_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise ValueError(f'Invalid {label}')
    return value


def _require_text(value: Any, label: str, *, max_chars: int = 256) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > max_chars:
        raise ValueError(f'Invalid {label}')
    if any(char in value for char in ('\x00', '\r', '\n')):
        raise ValueError(f'Invalid {label}')
    return value.strip()


def _parse_timestamp(value: Any, label: str) -> tuple[str, float]:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'Invalid {label}')
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValueError(f'Invalid {label}') from exc
    if parsed.tzinfo is None:
        raise ValueError(f'{label} requires timezone')
    timestamp = parsed.timestamp()
    if not math.isfinite(timestamp):
        raise ValueError(f'Invalid {label}')
    return value, timestamp


def _metadata_hash(
    *,
    source_id: str,
    capability_id: str,
    name: str,
    provider: str,
    kind: str,
    provenance: str,
    capabilities: list[str],
    observed_at: str,
) -> str:
    payload = json.dumps(
        {
            'source_id': source_id,
            'capability_id': capability_id,
            'name': name,
            'provider': provider,
            'kind': kind,
            'provenance': provenance,
            'capabilities': capabilities,
            'observed_at': observed_at,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
    ).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def _validate_external_capability(item: ExternalCapability) -> None:
    if item.schema_version != SCHEMA_VERSION:
        raise ValueError('Unsupported external capability schema')
    _require_id(item.source_id, 'source_id')
    _require_id(item.capability_id, 'capability_id')
    _require_text(item.name, 'capability name')
    _require_text(item.provider, 'provider', max_chars=128)
    if not isinstance(item.kind, str) or not _KIND_RE.fullmatch(item.kind):
        raise ValueError('Invalid capability kind')
    _require_text(item.provenance, 'provenance', max_chars=256)
    if not isinstance(item.capabilities, list) or len(item.capabilities) > 128:
        raise ValueError('Invalid capability list')
    for capability in item.capabilities:
        _require_text(capability, 'capability value', max_chars=128)
    if len(set(item.capabilities)) != len(item.capabilities):
        raise ValueError('Duplicate capability values')
    _parse_timestamp(item.last_observed_at, 'last_observed_at')
    if item.last_verified_at is not None:
        _parse_timestamp(item.last_verified_at, 'last_verified_at')
    if not isinstance(item.metadata_hash, str) or not re.fullmatch(r'[0-9a-f]{64}', item.metadata_hash):
        raise ValueError('Invalid external capability metadata hash')
    valid_modes = {'catalog_only', 'local_adapter', 'delegated', 'disabled'}
    if item.invocation_mode not in valid_modes:
        raise ValueError('Invalid invocation mode')


class ExternalCapabilityCatalog:
    """Atomic catalog of external capabilities with time-bounded availability proof."""

    def __init__(
        self,
        state_dir: Path,
        *,
        clock: Callable[[], float] | None = None,
        verification_ttl_seconds: float = DEFAULT_VERIFICATION_TTL_SECONDS,
    ) -> None:
        self.state_dir = Path(state_dir).absolute()
        self.path = self.state_dir / 'external_capabilities' / 'catalog.json'
        self.clock = clock or time.time
        if isinstance(verification_ttl_seconds, bool) or not isinstance(verification_ttl_seconds, (int, float)):
            raise ValueError('Invalid verification TTL')
        self.verification_ttl_seconds = float(verification_ttl_seconds)
        if not math.isfinite(self.verification_ttl_seconds) or self.verification_ttl_seconds <= 0:
            raise ValueError('Invalid verification TTL')

    @staticmethod
    def _empty() -> dict[str, Any]:
        return {'schema_version': SCHEMA_VERSION, 'entries': {}}

    @staticmethod
    def _key(source_id: str, capability_id: str) -> str:
        return f'{source_id}::{capability_id}'

    @classmethod
    def _validate_snapshot(cls, snapshot: object) -> dict[str, Any]:
        if not isinstance(snapshot, dict) or snapshot.get('schema_version') != SCHEMA_VERSION:
            raise ValueError('Unsupported external capability catalog schema')
        entries = snapshot.get('entries')
        if not isinstance(entries, dict):
            raise ValueError('Invalid external capability catalog entries')
        validated: dict[str, dict[str, Any]] = {}
        for key, raw in entries.items():
            item = ExternalCapability.from_dict(raw)
            expected = cls._key(item.source_id, item.capability_id)
            if key != expected:
                raise ValueError('External capability catalog key mismatch')
            validated[key] = item.to_dict()
        return {'schema_version': SCHEMA_VERSION, 'entries': validated}

    def _load(self) -> dict[str, Any]:
        _reject_linked_path(self.path)
        if not self.path.exists():
            return self._empty()
        try:
            with self.path.open('rb') as stream:
                raw = stream.read(MAX_STATE_BYTES + 1)
        except OSError as exc:
            raise ValueError('Unable to read external capability catalog') from exc
        if len(raw) > MAX_STATE_BYTES:
            raise ValueError('External capability catalog exceeds size limit')
        try:
            snapshot = json.loads(raw.decode('utf-8'))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError('Invalid external capability catalog JSON') from exc
        return self._validate_snapshot(snapshot)

    def _save(self, snapshot: dict[str, Any]) -> None:
        validated = self._validate_snapshot(snapshot)
        parent = self.path.parent
        _reject_linked_path(parent)
        parent.mkdir(parents=True, exist_ok=True)
        payload = (
            json.dumps(validated, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
        ).encode('utf-8')
        if len(payload) > MAX_STATE_BYTES:
            raise ValueError('External capability catalog exceeds size limit')
        fd, temporary = tempfile.mkstemp(prefix='.external-capabilities-', suffix='.tmp', dir=parent)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    @staticmethod
    def _validate_manifest_fields(manifest: dict[str, Any]) -> None:
        unknown = set(manifest) - _ALLOWED_MANIFEST_FIELDS
        if unknown:
            if unknown & _SECRET_FIELDS:
                raise ValueError('External capability manifest contains secret fields')
            raise ValueError(f'External capability manifest contains unknown field: {sorted(unknown)[0]}')

    @staticmethod
    def _validate_capability_fields(raw: dict[str, Any]) -> None:
        unknown = set(raw) - _ALLOWED_CAPABILITY_FIELDS
        if unknown:
            if unknown & _SECRET_FIELDS:
                raise ValueError('External capability manifest contains secret fields')
            raise ValueError(f'External capability manifest contains unknown field: {sorted(unknown)[0]}')

    def _normalize_manifest(self, manifest: dict[str, Any]) -> tuple[str, str, str, list[dict[str, Any]]]:
        if not isinstance(manifest, dict):
            raise TypeError('External capability manifest must be an object')
        self._validate_manifest_fields(manifest)
        if manifest.get('schema_version') != SCHEMA_VERSION:
            raise ValueError('Unsupported external capability manifest schema')
        source_id = _require_id(manifest.get('source_id'), 'source_id')
        observed_at, _ = _parse_timestamp(manifest.get('observed_at'), 'observed_at')
        provenance = _require_text(manifest.get('source_provenance'), 'source provenance', max_chars=256)
        raw_capabilities = manifest.get('capabilities')
        if not isinstance(raw_capabilities, list) or len(raw_capabilities) > MAX_CAPABILITIES_PER_MANIFEST:
            raise ValueError('Invalid external capability manifest capabilities')

        normalized: list[dict[str, Any]] = []
        seen: set[str] = set()
        for raw in raw_capabilities:
            if not isinstance(raw, dict):
                raise ValueError('Invalid external capability manifest entry')
            self._validate_capability_fields(raw)
            capability_id = _require_id(raw.get('capability_id'), 'capability_id')
            if capability_id in seen:
                raise ValueError('Duplicate capability_id in external capability manifest')
            seen.add(capability_id)
            name = _require_text(raw.get('name'), 'capability name')
            provider = _require_text(raw.get('provider'), 'provider', max_chars=128)
            kind = raw.get('kind')
            if not isinstance(kind, str) or not _KIND_RE.fullmatch(kind):
                raise ValueError('Invalid capability kind')
            capabilities = raw.get('capabilities')
            if not isinstance(capabilities, list) or len(capabilities) > 128:
                raise ValueError('Invalid capability list')
            normalized_capabilities: list[str] = []
            for value in capabilities:
                normalized_capabilities.append(_require_text(value, 'capability value', max_chars=128))
            if len(set(normalized_capabilities)) != len(normalized_capabilities):
                raise ValueError('Duplicate capability values')
            try:
                availability = CapabilityAvailability(raw.get('availability', 'UNVERIFIED'))
            except (TypeError, ValueError) as exc:
                raise ValueError('Invalid manifest availability') from exc
            if availability not in {CapabilityAvailability.KNOWN, CapabilityAvailability.UNVERIFIED}:
                raise ValueError('Manifest availability cannot claim executable capability')
            normalized.append({
                'capability_id': capability_id,
                'name': name,
                'provider': provider,
                'kind': kind,
                'capabilities': normalized_capabilities,
                'availability': availability,
            })
        return source_id, observed_at, provenance, normalized

    def import_manifest(self, manifest: dict[str, Any]) -> dict[str, int]:
        source_id, observed_at, provenance, capabilities = self._normalize_manifest(manifest)
        snapshot = self._load()
        inserted = 0
        updated = 0
        unchanged = 0

        for raw in capabilities:
            key = self._key(source_id, raw['capability_id'])
            existing_raw = snapshot['entries'].get(key)
            existing = ExternalCapability.from_dict(existing_raw) if existing_raw is not None else None

            imported_state = raw['availability']
            state = existing.availability_state if existing is not None and existing.availability_state == CapabilityAvailability.REVOKED else imported_state
            verified_at = existing.last_verified_at if existing is not None and state in {
                CapabilityAvailability.REVOKED,
                CapabilityAvailability.AVAILABLE_LOCAL,
                CapabilityAvailability.AVAILABLE_DELEGATED,
            } else None
            if state == CapabilityAvailability.AVAILABLE_LOCAL:
                invocation_mode = 'local_adapter'
            elif state == CapabilityAvailability.AVAILABLE_DELEGATED:
                invocation_mode = 'delegated'
            elif state == CapabilityAvailability.REVOKED:
                invocation_mode = 'disabled'
            else:
                invocation_mode = 'catalog_only'

            metadata_hash = _metadata_hash(
                source_id=source_id,
                capability_id=raw['capability_id'],
                name=raw['name'],
                provider=raw['provider'],
                kind=raw['kind'],
                provenance=provenance,
                capabilities=raw['capabilities'],
                observed_at=observed_at,
            )
            item = ExternalCapability(
                schema_version=SCHEMA_VERSION,
                source_id=source_id,
                capability_id=raw['capability_id'],
                name=raw['name'],
                provider=raw['provider'],
                kind=raw['kind'],
                provenance=provenance,
                capabilities=list(raw['capabilities']),
                availability_state=state,
                invocation_mode=invocation_mode,
                last_observed_at=observed_at,
                last_verified_at=verified_at,
                metadata_hash=metadata_hash,
            )
            _validate_external_capability(item)
            serialized = item.to_dict()
            if existing_raw is None:
                inserted += 1
                snapshot['entries'][key] = serialized
            elif existing_raw == serialized:
                unchanged += 1
            else:
                updated += 1
                snapshot['entries'][key] = serialized

        if inserted or updated:
            self._save(snapshot)
        return {'inserted': inserted, 'updated': updated, 'unchanged': unchanged}

    def _effective(self, item: ExternalCapability) -> ExternalCapability:
        if item.availability_state not in {
            CapabilityAvailability.AVAILABLE_LOCAL,
            CapabilityAvailability.AVAILABLE_DELEGATED,
        }:
            return item
        if item.last_verified_at is None:
            return replace(item, availability_state=CapabilityAvailability.UNVERIFIED, invocation_mode='catalog_only')
        _, verified_ts = _parse_timestamp(item.last_verified_at, 'last_verified_at')
        age = float(self.clock()) - verified_ts
        if age < -60 or age > self.verification_ttl_seconds:
            return replace(item, availability_state=CapabilityAvailability.UNVERIFIED, invocation_mode='catalog_only')
        return item

    def list(self, *, source_id: str | None = None) -> list[ExternalCapability]:
        if source_id is not None:
            source_id = _require_id(source_id, 'source_id')
        snapshot = self._load()
        items = [ExternalCapability.from_dict(raw) for raw in snapshot['entries'].values()]
        if source_id is not None:
            items = [item for item in items if item.source_id == source_id]
        return [self._effective(item) for item in sorted(items, key=lambda item: (item.source_id, item.capability_id))]

    def get(self, source_id: str, capability_id: str) -> ExternalCapability | None:
        source_id = _require_id(source_id, 'source_id')
        capability_id = _require_id(capability_id, 'capability_id')
        snapshot = self._load()
        raw = snapshot['entries'].get(self._key(source_id, capability_id))
        if raw is None:
            return None
        return self._effective(ExternalCapability.from_dict(raw))

    def mark_availability(
        self,
        source_id: str,
        capability_id: str,
        state: CapabilityAvailability,
        *,
        verified_at: str | None,
    ) -> None:
        source_id = _require_id(source_id, 'source_id')
        capability_id = _require_id(capability_id, 'capability_id')
        if not isinstance(state, CapabilityAvailability):
            try:
                state = CapabilityAvailability(state)
            except (TypeError, ValueError) as exc:
                raise ValueError('Invalid capability availability') from exc

        snapshot = self._load()
        key = self._key(source_id, capability_id)
        raw = snapshot['entries'].get(key)
        if raw is None:
            raise KeyError(f'Unknown external capability: {source_id}/{capability_id}')
        item = ExternalCapability.from_dict(raw)

        availability_requires_proof = state in {
            CapabilityAvailability.AVAILABLE_LOCAL,
            CapabilityAvailability.AVAILABLE_DELEGATED,
        }
        normalized_verified_at = verified_at
        if availability_requires_proof:
            if verified_at is None:
                raise ValueError('verified_at is required for executable availability')
            normalized_verified_at, verified_ts = _parse_timestamp(verified_at, 'verified_at')
            age = float(self.clock()) - verified_ts
            if age < -60:
                raise ValueError('verified_at cannot be materially in the future')
            if age > self.verification_ttl_seconds:
                raise ValueError('verified_at is stale')
        elif verified_at is not None:
            normalized_verified_at, _ = _parse_timestamp(verified_at, 'verified_at')
        elif state in {CapabilityAvailability.KNOWN, CapabilityAvailability.UNVERIFIED}:
            normalized_verified_at = item.last_verified_at
        elif state in {CapabilityAvailability.UNAVAILABLE, CapabilityAvailability.REVOKED}:
            normalized_verified_at = item.last_verified_at

        invocation_mode = {
            CapabilityAvailability.AVAILABLE_LOCAL: 'local_adapter',
            CapabilityAvailability.AVAILABLE_DELEGATED: 'delegated',
            CapabilityAvailability.UNAVAILABLE: 'disabled',
            CapabilityAvailability.REVOKED: 'disabled',
            CapabilityAvailability.KNOWN: 'catalog_only',
            CapabilityAvailability.UNVERIFIED: 'catalog_only',
        }[state]
        updated = replace(
            item,
            availability_state=state,
            invocation_mode=invocation_mode,
            last_verified_at=normalized_verified_at,
        )
        _validate_external_capability(updated)
        snapshot['entries'][key] = updated.to_dict()
        self._save(snapshot)
