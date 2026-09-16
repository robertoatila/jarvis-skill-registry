"""Restart-safe filesystem watcher for the J.A.R.V.I.S. Cognitive Vault.

This module observes Markdown and Obsidian Canvas files without requiring the
Obsidian desktop application. It emits deterministic durable events from
content hashes and checkpoints the last observed filesystem state atomically.
JARVIS authorship is recognized only through exact one-shot projection receipts;
marker-shaped text alone never grants trusted authorship.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
import time
from typing import Callable

from .vault_events import (
    SCHEMA_VERSION,
    VaultCheckpointStore,
    VaultEvent,
    make_event_id,
)
from .vault_projection import _reject_linked_path
from .vault_projection_receipts import ProjectionReceiptStore


class VaultWatcher:
    """Detect meaningful create/modify/delete transitions in a local Vault."""

    MAX_NOTE_BYTES = 2 * 1024 * 1024
    _IGNORED_DIRECTORIES = frozenset({'.git', '.obsidian', 'state', 'backups'})
    _IGNORED_PREFIXES = ('.projection-', '.vault-checkpoint-', '.vault-watcher-')
    _IGNORED_SUFFIXES = (
        '.tmp.md',
        '.swp.md',
        '.bak.md',
        '.tmp.canvas',
        '.swp.canvas',
        '.bak.canvas',
    )

    def __init__(
        self,
        root: Path,
        state_dir: Path,
        clock: Callable[[], float] | None = None,
        projection_receipts: ProjectionReceiptStore | None = None,
    ) -> None:
        self.root = Path(root).absolute()
        self.state_dir = Path(state_dir).absolute()
        self.clock = clock or time.time
        self.checkpoints = VaultCheckpointStore(self.state_dir)
        self.projection_receipts = projection_receipts or ProjectionReceiptStore(self.state_dir)

    @staticmethod
    def _sha256(payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()

    @classmethod
    def _ignored(cls, relative: Path) -> bool:
        if any(part in cls._IGNORED_DIRECTORIES for part in relative.parts[:-1]):
            return True
        name = relative.name
        return name.startswith(cls._IGNORED_PREFIXES) or name.endswith(cls._IGNORED_SUFFIXES)

    def _read_content(self, path: Path) -> tuple[bytes, os.stat_result] | None:
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

    def _candidates(self) -> list[Path]:
        _reject_linked_path(self.root, 'Linked vault roots are not supported')
        candidates: set[Path] = set()
        try:
            for pattern in ('*.md', '*.canvas'):
                candidates.update(self.root.rglob(pattern))
            return sorted(
                candidates,
                key=lambda path: path.relative_to(self.root).as_posix(),
            )
        except OSError as exc:
            raise ValueError('Unable to enumerate vault') from exc

    def _observed_at(self) -> str:
        return datetime.fromtimestamp(float(self.clock()), timezone.utc).isoformat()

    def _authorship(self, relative_path: str, content_hash: str) -> tuple[str, str | None]:
        receipt = self.projection_receipts.find_hash(relative_path, content_hash)
        if receipt is None:
            return 'human_or_unknown', None
        return 'jarvis_projection', receipt.receipt_id

    def _event(
        self,
        *,
        path: str,
        kind: str,
        previous_hash: str | None,
        content_hash: str | None,
        observed_at: str,
        source: str = 'human_or_unknown',
        projection_receipt: str | None = None,
    ) -> VaultEvent:
        return VaultEvent(
            schema_version=SCHEMA_VERSION,
            event_id=make_event_id(path, kind, previous_hash, content_hash),
            path=path,
            kind=kind,
            content_hash=content_hash,
            previous_hash=previous_hash,
            observed_at=observed_at,
            source=source,
            projection_receipt=projection_receipt,
        )

    def scan_once(self) -> list[VaultEvent]:
        """Emit each meaningful content transition once and advance checkpoint."""

        snapshot = self.checkpoints.load()
        previous = snapshot['files']
        current: dict[str, dict[str, object]] = {}
        events: list[VaultEvent] = []
        observed_at = self._observed_at()

        for path in self._candidates():
            relative = path.relative_to(self.root)
            if self._ignored(relative):
                continue
            read = self._read_content(path)
            if read is None:
                continue
            payload, stat = read
            relative_path = relative.as_posix()
            content_hash = self._sha256(payload)
            content_kind = 'canvas' if path.suffix.casefold() == '.canvas' else 'markdown'
            record = {
                'content_hash': content_hash,
                'size_bytes': len(payload),
                'modified_ns': stat.st_mtime_ns,
                'content_kind': content_kind,
            }
            current[relative_path] = record

            old = previous.get(relative_path)
            if old is None:
                source, receipt = self._authorship(relative_path, content_hash)
                events.append(
                    self._event(
                        path=relative_path,
                        kind='created',
                        previous_hash=None,
                        content_hash=content_hash,
                        observed_at=observed_at,
                        source=source,
                        projection_receipt=receipt,
                    )
                )
            elif old['content_hash'] != content_hash:
                source, receipt = self._authorship(relative_path, content_hash)
                events.append(
                    self._event(
                        path=relative_path,
                        kind='modified',
                        previous_hash=str(old['content_hash']),
                        content_hash=content_hash,
                        observed_at=observed_at,
                        source=source,
                        projection_receipt=receipt,
                    )
                )

        for relative_path in sorted(set(previous) - set(current)):
            old = previous[relative_path]
            events.append(
                self._event(
                    path=relative_path,
                    kind='deleted',
                    previous_hash=str(old['content_hash']),
                    content_hash=None,
                    observed_at=observed_at,
                )
            )

        if current != previous:
            self.checkpoints.save({'schema_version': SCHEMA_VERSION, 'files': current})
        return events
