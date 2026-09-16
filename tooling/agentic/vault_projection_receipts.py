"""Durable one-shot authorship receipts for J.A.R.V.I.S. Vault projections."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from typing import Any

from .vault_projection import _reject_linked_path


SCHEMA_VERSION = 1
_SHA256_RE = re.compile(r'^[0-9a-f]{64}$')
_RECEIPT_ID_RE = re.compile(r'^projection-receipt-[A-Za-z0-9_-]{4,128}$')
_KIND_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$')


def _normalize_relative_path(value: str) -> str:
    if not isinstance(value, str) or not value.strip() or '\\' in value:
        raise ValueError('Projection receipt requires a normalized relative path')
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or '.' in path.parts:
        raise ValueError('Projection receipt path must stay within the vault')
    normalized = path.as_posix()
    if normalized != value or normalized.startswith('/'):
        raise ValueError('Projection receipt path must be canonical')
    return normalized


def _validate_hash(value: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise ValueError('Projection receipt requires a lowercase SHA-256 digest')
    return value


def _validate_timestamp(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Projection receipt requires projected_at')
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError('Projection receipt projected_at must be ISO-8601') from exc
    if parsed.tzinfo is None:
        raise ValueError('Projection receipt projected_at requires timezone')
    return value


@dataclass(frozen=True)
class ProjectionReceipt:
    receipt_id: str
    path: str
    content_hash: str
    projected_at: str
    projection_kind: str

    def __post_init__(self) -> None:
        if not isinstance(self.receipt_id, str) or not _RECEIPT_ID_RE.fullmatch(self.receipt_id):
            raise ValueError('Invalid projection receipt identity')
        _normalize_relative_path(self.path)
        _validate_hash(self.content_hash)
        _validate_timestamp(self.projected_at)
        if not isinstance(self.projection_kind, str) or not _KIND_RE.fullmatch(self.projection_kind):
            raise ValueError('Invalid projection kind')

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'ProjectionReceipt':
        if not isinstance(data, dict):
            raise ValueError('Invalid projection receipt entry')
        return cls(
            receipt_id=data.get('receipt_id'),
            path=data.get('path'),
            content_hash=data.get('content_hash'),
            projected_at=data.get('projected_at'),
            projection_kind=data.get('projection_kind'),
        )

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class ProjectionReceiptStore:
    """Persist the latest unconsumed projection receipt for each Vault path."""

    def __init__(self, state_dir: Path) -> None:
        self.state_dir = Path(state_dir).absolute()
        self.path = self.state_dir / 'obsidian' / 'projection_receipts.json'

    @staticmethod
    def _empty() -> dict[str, Any]:
        return {'schema_version': SCHEMA_VERSION, 'receipts': {}}

    @classmethod
    def _validate_snapshot(cls, snapshot: object) -> dict[str, Any]:
        if not isinstance(snapshot, dict) or snapshot.get('schema_version') != SCHEMA_VERSION:
            raise ValueError('Unsupported projection receipt schema')
        receipts = snapshot.get('receipts')
        if not isinstance(receipts, dict):
            raise ValueError('Invalid projection receipt collection')
        validated: dict[str, dict[str, str]] = {}
        for raw_path, raw_receipt in receipts.items():
            relative_path = _normalize_relative_path(raw_path)
            receipt = ProjectionReceipt.from_dict(raw_receipt)
            if receipt.path != relative_path:
                raise ValueError('Projection receipt path key mismatch')
            validated[relative_path] = receipt.to_dict()
        return {'schema_version': SCHEMA_VERSION, 'receipts': validated}

    def _load(self) -> dict[str, Any]:
        _reject_linked_path(self.path, 'Linked projection receipt paths are not supported')
        if not self.path.exists():
            return self._empty()
        try:
            snapshot = json.loads(self.path.read_text(encoding='utf-8'))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError('Invalid projection receipt state') from exc
        return self._validate_snapshot(snapshot)

    def _save(self, snapshot: dict[str, Any]) -> None:
        validated = self._validate_snapshot(snapshot)
        parent = self.path.parent
        _reject_linked_path(parent, 'Linked projection receipt paths are not supported')
        parent.mkdir(parents=True, exist_ok=True)
        payload = (
            json.dumps(validated, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
            + '\n'
        ).encode('utf-8')
        fd, temporary = tempfile.mkstemp(prefix='.projection-receipt-', suffix='.tmp', dir=parent)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def record(self, receipt: ProjectionReceipt) -> None:
        if not isinstance(receipt, ProjectionReceipt):
            raise TypeError('ProjectionReceiptStore.record requires ProjectionReceipt')
        snapshot = self._load()
        snapshot['receipts'][receipt.path] = receipt.to_dict()
        self._save(snapshot)

    def find_hash(self, path: str, content_hash: str) -> ProjectionReceipt | None:
        """Consume the path receipt and return it only when the exact hash matches."""
        relative_path = _normalize_relative_path(path)
        content_hash = _validate_hash(content_hash)
        snapshot = self._load()
        raw = snapshot['receipts'].pop(relative_path, None)
        if raw is None:
            return None
        self._save(snapshot)
        receipt = ProjectionReceipt.from_dict(raw)
        if receipt.content_hash != content_hash:
            return None
        return receipt
