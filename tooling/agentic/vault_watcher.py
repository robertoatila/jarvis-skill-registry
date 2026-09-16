"""Restart-safe, loop-aware change detection for the local Obsidian vault.

The watcher is deliberately filesystem-only. It reports new or human-modified
Markdown notes and persists a cursor under ``state/obsidian``. JARVIS-owned
projection changes are recorded in the cursor but are not re-emitted, which
prevents runtime -> Obsidian -> runtime feedback loops.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Callable

from .vault_projection import END, START, _reject_linked_path


SCHEMA_VERSION = 1


@dataclass(frozen=True)
class VaultChange:
    """One new or externally modified Markdown note."""

    relative_path: str
    digest_sha256: str
    size_bytes: int
    modified_ns: int


class VaultWatcher:
    """Scan a vault without trusting Obsidian UI state or following links."""

    MAX_NOTE_BYTES = 2 * 1024 * 1024
    _IGNORED_DIRECTORIES = frozenset({'.git', '.obsidian', 'state', 'backups'})
    _IGNORED_PREFIXES = ('.projection-', '.vault-watcher-')
    _IGNORED_SUFFIXES = ('.tmp.md', '.swp.md', '.bak.md')

    def __init__(
        self,
        root: Path,
        state_dir: Path,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.root = Path(root).absolute()
        self.state_dir = Path(state_dir).absolute()
        self.state_file = self.state_dir / 'obsidian' / 'vault_watcher.json'
        self.clock = clock

    @staticmethod
    def _sha256(payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()

    @classmethod
    def _human_digest(cls, payload: bytes) -> tuple[str, bool]:
        """Return digest excluding one valid JARVIS projection, if present.

        Malformed, duplicated or reversed markers are intentionally treated as
        ordinary human-visible content. They therefore cannot suppress a
        change event merely by resembling a managed projection.
        """

        start = START.encode('utf-8')
        end = END.encode('utf-8')
        start_count = payload.count(start)
        end_count = payload.count(end)
        if start_count == 0 and end_count == 0:
            canonical = payload.rstrip(b'\r\n') + (b'\n' if payload else b'')
            return cls._sha256(canonical), False
        if start_count != 1 or end_count != 1:
            return cls._sha256(payload), False

        first = payload.find(start)
        last = payload.find(end)
        if last < first:
            return cls._sha256(payload), False

        prefix = payload[:first].rstrip(b'\r\n')
        suffix = payload[last + len(end):].lstrip(b'\r\n')
        if prefix and suffix:
            human = prefix + b'\n' + suffix
        elif prefix:
            human = prefix + b'\n'
        else:
            human = suffix
        return cls._sha256(human), True

    def _load_state(self) -> dict[str, dict[str, Any]]:
        _reject_linked_path(self.state_file, 'Linked watcher state paths are not supported')
        if not self.state_file.exists():
            return {}
        try:
            data = json.loads(self.state_file.read_text(encoding='utf-8'))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError('Invalid vault watcher state') from exc
        if not isinstance(data, dict) or data.get('schema_version') != SCHEMA_VERSION:
            raise ValueError('Unsupported vault watcher state schema')
        notes = data.get('notes')
        if not isinstance(notes, dict):
            raise ValueError('Invalid vault watcher state notes')
        for path, item in notes.items():
            if not isinstance(path, str) or not isinstance(item, dict):
                raise ValueError('Invalid vault watcher state entry')
            if not isinstance(item.get('digest_sha256'), str):
                raise ValueError('Invalid vault watcher digest')
            if not isinstance(item.get('human_digest_sha256'), str):
                raise ValueError('Invalid vault watcher human digest')
            if not isinstance(item.get('size_bytes'), int) or not isinstance(item.get('modified_ns'), int):
                raise ValueError('Invalid vault watcher metadata')
        return notes

    def _write_state(self, notes: dict[str, dict[str, Any]]) -> None:
        parent = self.state_file.parent
        _reject_linked_path(parent, 'Linked watcher state paths are not supported')
        parent.mkdir(parents=True, exist_ok=True)
        payload = (
            json.dumps(
                {'schema_version': SCHEMA_VERSION, 'notes': notes},
                ensure_ascii=False,
                sort_keys=True,
                separators=(',', ':'),
            )
            + '\n'
        ).encode('utf-8')

        fd, temporary = tempfile.mkstemp(prefix='.vault-watcher-', suffix='.tmp', dir=parent)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.state_file)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    @classmethod
    def _ignored(cls, relative: Path) -> bool:
        if any(part in cls._IGNORED_DIRECTORIES for part in relative.parts[:-1]):
            return True
        name = relative.name
        return name.startswith(cls._IGNORED_PREFIXES) or name.endswith(cls._IGNORED_SUFFIXES)

    def _read_note(self, path: Path) -> tuple[bytes, os.stat_result] | None:
        _reject_linked_path(path, 'Linked vault paths are not supported')
        try:
            before = path.stat()
            if not path.is_file() or before.st_size > self.MAX_NOTE_BYTES:
                return None
            payload = path.read_bytes()
            after = path.stat()
        except FileNotFoundError:
            return None
        if after.st_size > self.MAX_NOTE_BYTES or len(payload) != after.st_size:
            return None
        return payload, after

    def scan(self) -> list[VaultChange]:
        """Return deterministic new/human-modified notes since the last scan."""

        _reject_linked_path(self.root, 'Linked vault roots are not supported')
        previous = self._load_state()
        current: dict[str, dict[str, Any]] = {}
        changes: list[VaultChange] = []

        try:
            candidates = sorted(
                self.root.rglob('*.md'),
                key=lambda path: path.relative_to(self.root).as_posix(),
            )
        except OSError as exc:
            raise ValueError('Unable to enumerate vault') from exc

        for path in candidates:
            relative = path.relative_to(self.root)
            if self._ignored(relative):
                continue
            read = self._read_note(path)
            if read is None:
                continue
            payload, stat = read
            relative_path = relative.as_posix()
            digest = self._sha256(payload)
            human_digest, valid_projection = self._human_digest(payload)
            record = {
                'digest_sha256': digest,
                'human_digest_sha256': human_digest,
                'size_bytes': len(payload),
                'modified_ns': stat.st_mtime_ns,
            }
            current[relative_path] = record

            old = previous.get(relative_path)
            if old is None:
                changes.append(
                    VaultChange(relative_path, digest, len(payload), stat.st_mtime_ns)
                )
                continue
            if old['digest_sha256'] == digest:
                continue

            projection_only = (
                valid_projection
                and old['human_digest_sha256'] == human_digest
            )
            if not projection_only:
                changes.append(
                    VaultChange(relative_path, digest, len(payload), stat.st_mtime_ns)
                )

        if current != previous:
            self._write_state(current)
        return changes
