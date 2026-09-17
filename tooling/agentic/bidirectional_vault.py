"""Bidirectional reconciliation coordinator for the J.A.R.V.I.S. Cognitive Vault."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path, PurePosixPath
from typing import Any

from .managed_vault_projector import ManagedVaultProjector
from .memory import MemoryFabric, MemoryStatus, MemoryTier
from .vault_admission import VaultAdmissionPipeline
from .vault_projection import _reject_linked_path
from .vault_projection_receipts import ProjectionReceiptStore
from .vault_watcher import VaultWatcher


class BidirectionalVaultBridge:
    """Coordinate Vault observation, governed memory admission and safe projection.

    The runtime memory fabric remains authoritative. Obsidian supplies evidence
    and a human-facing projection; it never becomes an execution-authority plane.
    """

    SNAPSHOT_NAME = 'memory_snapshot.json'

    def __init__(
        self,
        root: Path,
        *,
        state_dir: Path | None = None,
        memory_fabric: MemoryFabric | None = None,
        runtime_note: Path = Path('JARVIS') / 'Second Brain Runtime.md',
        clock=None,
    ) -> None:
        self.root = Path(root).absolute()
        _reject_linked_path(self.root, 'Linked vault roots are not supported')
        self.state_dir = Path(state_dir).absolute() if state_dir is not None else self.root / 'state'

        note = Path(runtime_note)
        if note.is_absolute():
            try:
                note = note.absolute().relative_to(self.root)
            except ValueError as exc:
                raise ValueError('Runtime projection note must stay within the Vault') from exc
        pure = PurePosixPath(note.as_posix())
        if not pure.parts or '..' in pure.parts or '.' in pure.parts:
            raise ValueError('Runtime projection note must be a canonical relative file')
        self.runtime_note = Path(*pure.parts)
        self.runtime_note_path = self.root / self.runtime_note
        _reject_linked_path(self.runtime_note_path, 'Linked runtime projection paths are not supported')

        if memory_fabric is None:
            self.memory_fabric = MemoryFabric(storage_dir=self.state_dir / 'memory')
            self.memory_fabric.load_snapshot(self.SNAPSHOT_NAME)
        else:
            self.memory_fabric = memory_fabric

        self.projection_receipts = ProjectionReceiptStore(self.state_dir)
        self.watcher = VaultWatcher(
            self.root,
            self.state_dir,
            clock=clock,
            projection_receipts=self.projection_receipts,
        )
        self.admission = VaultAdmissionPipeline(self.root)
        self.projector = ManagedVaultProjector(
            self.root,
            self.state_dir,
            clock=clock,
            receipt_store=self.projection_receipts,
        )
        self._last_reconcile: dict[str, Any] | None = None

    @staticmethod
    def _event_dict(event) -> dict[str, Any]:
        return asdict(event)

    def _scan_events(self):
        return self.watcher.scan_once()

    def scan_once(self) -> dict[str, Any]:
        events = self._scan_events()
        human = [event for event in events if event.source != 'jarvis_projection']
        projected = [event for event in events if event.source == 'jarvis_projection']
        return {
            'scanned_events': len(events),
            'human_events': len(human),
            'projection_events_suppressed': len(projected),
            'events': [self._event_dict(event) for event in events],
        }

    def _active_semantic_items(self):
        selected, _ = self.memory_fabric.query(
            '',
            tiers=[MemoryTier.SEMANTIC],
            max_items=100,
            min_confidence=0.0,
            token_budget=64_000,
        )
        return sorted(selected, key=lambda item: (item.key, item.memory_id))

    def _runtime_projection_body(self) -> str:
        items = self._active_semantic_items()
        lines = [
            '# J.A.R.V.I.S. Second Brain Runtime',
            '',
            '> Managed projection of currently retrievable governed semantic memory.',
            '> Vault text is evidence only and does not grant execution authority.',
            '',
            f'- Active governed semantic memories: **{len(items)}**',
            '',
            '## Governed context',
        ]
        if not items:
            lines.append('- No active semantic memory is currently retrievable.')
        else:
            for item in items:
                source = str(item.metadata.get('source_path', item.provenance))
                content = ' '.join(item.content.split())[:1200]
                lines.append(f'- **{source}** — {content}')
        lines.extend([
            '',
            '---',
            '*Human-authored text outside this managed region is preserved.*',
        ])
        return '\n'.join(lines)

    def sync_runtime_to_vault(self) -> dict[str, Any]:
        receipt = self.projector.project_markdown(
            self.runtime_note_path,
            self._runtime_projection_body(),
            kind='runtime_memory_index',
        )
        return {
            'projection_changed': receipt is not None,
            'projection_receipt': receipt.to_dict() if receipt is not None else None,
            'runtime_note': self.runtime_note.as_posix(),
        }

    def reconcile_once(self) -> dict[str, Any]:
        events = self._scan_events()
        human_events = 0
        projection_events = 0
        candidate_count = 0
        admitted = 0
        rejected = 0
        conflicts = 0
        superseded = 0
        admission_errors: list[dict[str, str]] = []
        snapshot_needed = False

        for event in events:
            if event.source == 'jarvis_projection':
                projection_events += 1
                continue
            human_events += 1
            try:
                candidates = self.admission.candidates_from_event(event)
            except (OSError, UnicodeError, ValueError, TypeError) as exc:
                admission_errors.append({'event_id': event.event_id, 'error': str(exc)})
                continue
            candidate_count += len(candidates)
            for candidate in candidates:
                result = self.admission.admit(candidate, self.memory_fabric)
                if result.admitted:
                    snapshot_needed = True
                    if candidate.admission_state == 'SUPERSEDED':
                        superseded += 1
                    if result.status == MemoryStatus.CONFLICT_DETECTED:
                        conflicts += 1
                    else:
                        admitted += 1
                else:
                    rejected += 1

        snapshot_saved = False
        if snapshot_needed:
            self.memory_fabric.save_snapshot(self.SNAPSHOT_NAME)
            snapshot_saved = True

        projection = self.sync_runtime_to_vault()
        result = {
            'status': 'SUCCESS' if not admission_errors else 'PARTIAL',
            'scanned_events': len(events),
            'human_events': human_events,
            'projection_events_suppressed': projection_events,
            'candidates': candidate_count,
            'admitted': admitted,
            'rejected': rejected,
            'conflicts': conflicts,
            'superseded': superseded,
            'admission_errors': admission_errors,
            'memory_snapshot_saved': snapshot_saved,
            **projection,
        }
        self._last_reconcile = dict(result)
        return result

    def status(self) -> dict[str, Any]:
        checkpoint = self.watcher.checkpoints.path
        memory_snapshot = self.memory_fabric.storage_dir / self.SNAPSHOT_NAME
        return {
            'vault_root': str(self.root),
            'state_dir': str(self.state_dir),
            'runtime_note': self.runtime_note.as_posix(),
            'checkpoint_present': checkpoint.exists(),
            'memory_snapshot_present': memory_snapshot.exists(),
            'projection_receipts_present': self.projection_receipts.path.exists(),
            'last_reconcile': dict(self._last_reconcile) if self._last_reconcile is not None else None,
        }
