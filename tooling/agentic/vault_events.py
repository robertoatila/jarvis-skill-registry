"""Durable event and checkpoint primitives for the Cognitive Vault watcher."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from .vault_projection import _reject_linked_path


SCHEMA_VERSION = 1


@dataclass(frozen=True)
class VaultEvent:
    """One meaningful filesystem transition observed in the Cognitive Vault."""

    schema_version: int
    event_id: str
    path: str
    kind: str
    content_hash: str | None
    previous_hash: str | None
    observed_at: str
    source: str
    projection_receipt: str | None = None


def make_event_id(
    path: str,
    kind: str,
    previous_hash: str | None,
    content_hash: str | None,
) -> str:
    """Build a restart-safe identity independent of observation time."""

    material = json.dumps(
        {
            'path': path,
            'kind': kind,
            'previous_hash': previous_hash,
            'content_hash': content_hash,
        },
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
    ).encode('utf-8')
    return 'vault-event-' + hashlib.sha256(material).hexdigest()


class VaultCheckpointStore:
    """Atomic schema-versioned watcher checkpoint under ignored runtime state."""

    def __init__(self, state_dir: Path) -> None:
        self.state_dir = Path(state_dir).absolute()
        self.path = self.state_dir / 'obsidian' / 'vault_checkpoint.json'

    @staticmethod
    def _empty() -> dict[str, Any]:
        return {'schema_version': SCHEMA_VERSION, 'files': {}}

    @staticmethod
    def _validate(snapshot: object) -> dict[str, Any]:
        if not isinstance(snapshot, dict) or snapshot.get('schema_version') != SCHEMA_VERSION:
            raise ValueError('Unsupported vault checkpoint schema')
        files = snapshot.get('files')
        if not isinstance(files, dict):
            raise ValueError('Invalid vault checkpoint files')
        for path, record in files.items():
            if not isinstance(path, str) or not path or not isinstance(record, dict):
                raise ValueError('Invalid vault checkpoint entry')
            if not isinstance(record.get('content_hash'), str) or len(record['content_hash']) != 64:
                raise ValueError('Invalid vault checkpoint content hash')
            if not isinstance(record.get('size_bytes'), int) or record['size_bytes'] < 0:
                raise ValueError('Invalid vault checkpoint size')
            if not isinstance(record.get('modified_ns'), int) or record['modified_ns'] < 0:
                raise ValueError('Invalid vault checkpoint modification time')
            if record.get('content_kind') not in ('markdown', 'canvas'):
                raise ValueError('Invalid vault checkpoint content kind')
        return {'schema_version': SCHEMA_VERSION, 'files': dict(files)}

    def load(self) -> dict[str, Any]:
        _reject_linked_path(self.path, 'Linked Vault checkpoint paths are not supported')
        if not self.path.exists():
            return self._empty()
        try:
            snapshot = json.loads(self.path.read_text(encoding='utf-8'))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError('Invalid vault checkpoint') from exc
        return self._validate(snapshot)

    def save(self, snapshot: dict[str, Any]) -> None:
        validated = self._validate(snapshot)
        parent = self.path.parent
        _reject_linked_path(parent, 'Linked Vault checkpoint paths are not supported')
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

        fd, temporary = tempfile.mkstemp(prefix='.vault-checkpoint-', suffix='.tmp', dir=parent)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
