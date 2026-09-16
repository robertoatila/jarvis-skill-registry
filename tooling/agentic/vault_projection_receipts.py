"""Durable one-shot authorship receipts for J.A.R.V.I.S. Vault projections.

Marker-shaped text is not proof of authorship. A projection is attributable to
J.A.R.V.I.S. only when its exact resulting content hash matches a durable
receipt recorded by the writer. Successful or stale matches are consumed so a
future human edit cannot inherit old writer authority.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from typing import Any

from .vault_projection import _reject_linked_path


SCHEMA_VERSION = 1
_SHA256_RE = re.compile(r'^[0-9a-f]{64}$')


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


def _receipt_id(relative_path: str, content_hash: str) -> str:
    material = json.dumps(
        {'path': relative_path, 'content_hash': content_hash},
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
    ).encode('utf-8')
    return 'projection-receipt-' + hashlib.sha256(material).hexdigest()


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
        for raw_path, record in receipts.items():
            relative_path = _normalize_relative_path(raw_path)
            if not isinstance(record, dict):
                raise ValueError('Invalid projection receipt entry')
            content_hash = _validate_hash(record.get('content_hash'))
            receipt_id = record.get('receipt_id')
            expected_id = _receipt_id(relative_path, content_hash)
            if receipt_id != expected_id:
                raise ValueError('Invalid projection receipt identity')
            validated[relative_path] = {
                'content_hash': content_hash,
                'receipt_id': receipt_id,
            }
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
            json.dumps(
                validated,
                ensure_ascii=False,
                sort_keys=True,
                separators=(',', ':'),
            )
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

    def record(self, relative_path: str, content_hash: str) -> str:
        relative_path = _normalize_relative_path(relative_path)
        content_hash = _validate_hash(content_hash)
        receipt_id = _receipt_id(relative_path, content_hash)
        snapshot = self._load()
        snapshot['receipts'][relative_path] = {
            'content_hash': content_hash,
            'receipt_id': receipt_id,
        }
        self._save(snapshot)
        return receipt_id

    def match(self, relative_path: str, content_hash: str) -> str | None:
        """Consume a path receipt, returning it only for an exact content hash."""

        relative_path = _normalize_relative_path(relative_path)
        content_hash = _validate_hash(content_hash)
        snapshot = self._load()
        record = snapshot['receipts'].pop(relative_path, None)
        if record is None:
            return None
        self._save(snapshot)
        if record['content_hash'] != content_hash:
            return None
        return str(record['receipt_id'])
