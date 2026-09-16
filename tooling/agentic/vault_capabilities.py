"""Managed Obsidian projection for evidence-bound external capability state.

This module renders only selected, non-secret catalog fields. It never turns
catalog knowledge into execution authority and relies on ``ExternalCapabilityCatalog``
for effective availability (including verification staleness).
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Iterable

from .external_capabilities import (
    CapabilityAvailability,
    ExternalCapability,
    ExternalCapabilityCatalog,
)
from .vault_projection import update_projection


DEFAULT_NOTE = Path('20 - External Capability Matrix.md')

_STATE_LABELS = {
    CapabilityAvailability.AVAILABLE_LOCAL: 'LOCAL EXECUTABLE',
    CapabilityAvailability.AVAILABLE_DELEGATED: 'DELEGATED / PROVIDER VERIFIED',
    CapabilityAvailability.KNOWN: 'KNOWN ONLY',
    CapabilityAvailability.UNVERIFIED: 'UNVERIFIED / STALE',
    CapabilityAvailability.UNAVAILABLE: 'REVOKED / UNAVAILABLE',
    CapabilityAvailability.REVOKED: 'REVOKED / UNAVAILABLE',
}


def _cell(value: object) -> str:
    """Render one Markdown table cell without leaking structure or new lines."""
    if value is None:
        return '—'
    text = str(value).replace('\r', ' ').replace('\n', ' ').replace('|', '\\|').strip()
    return text or '—'


class VaultCapabilityProjector:
    """Project current external capability evidence into one managed Vault note."""

    def __init__(
        self,
        root: Path,
        *,
        catalog: ExternalCapabilityCatalog | None = None,
        note_path: Path = DEFAULT_NOTE,
    ) -> None:
        self.root = Path(root).absolute()
        note_path = Path(note_path)
        if note_path.is_absolute() or '..' in note_path.parts:
            raise ValueError('Capability projection note must stay inside the Vault')
        self.note_path = self.root / note_path
        self.catalog = catalog or ExternalCapabilityCatalog(self.root / 'state')

    @staticmethod
    def _render(items: Iterable[ExternalCapability]) -> tuple[str, dict[str, int]]:
        materialized = list(items)
        counts = Counter(_STATE_LABELS[item.availability_state] for item in materialized)

        lines = [
            '# J.A.R.V.I.S. // External Capability Matrix',
            '',
            '> [!NOTE] Evidence-bound capability inventory',
            '> Catalog knowledge is not execution authority. Local/delegated availability is shown only while separately verified; stale proof is rendered as UNVERIFIED / STALE.',
            '',
            '| State | Name | Provider | Source | Kind | Capabilities | Last observed | Last verified |',
            '| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |',
        ]

        for item in materialized:
            capabilities = ', '.join(item.capabilities) if item.capabilities else '—'
            lines.append(
                '| '
                + ' | '.join(
                    [
                        _cell(_STATE_LABELS[item.availability_state]),
                        _cell(item.name),
                        _cell(item.provider),
                        _cell(item.source_id),
                        _cell(item.kind),
                        _cell(capabilities),
                        _cell(item.last_observed_at),
                        _cell(item.last_verified_at),
                    ]
                )
                + ' |'
            )

        if not materialized:
            lines.append('| KNOWN ONLY | — | — | — | — | No external capabilities cataloged. | — | — |')

        lines.extend(
            [
                '',
                '## State summary',
                f"- LOCAL EXECUTABLE: **{counts.get('LOCAL EXECUTABLE', 0)}**",
                f"- DELEGATED / PROVIDER VERIFIED: **{counts.get('DELEGATED / PROVIDER VERIFIED', 0)}**",
                f"- KNOWN ONLY: **{counts.get('KNOWN ONLY', 0)}**",
                f"- UNVERIFIED / STALE: **{counts.get('UNVERIFIED / STALE', 0)}**",
                f"- REVOKED / UNAVAILABLE: **{counts.get('REVOKED / UNAVAILABLE', 0)}**",
                '',
                '*This managed projection exposes selected catalog metadata only. Credentials, cookies, provider sessions, metadata hashes and raw runtime state are not projected.*',
                '',
                'Navegação: [[00 - J.A.R.V.I.S. Cognitive Vault]] · [[19 - Memoria Persistente e Conhecimento Episodico]]',
            ]
        )
        return '\n'.join(lines), dict(counts)

    def sync(self) -> dict[str, object]:
        items = self.catalog.list()
        body, counts = self._render(items)
        changed = update_projection(self.note_path, body)
        return {
            'status': 'SUCCESS',
            'changed': changed,
            'note': self.note_path.name,
            'capabilities': len(items),
            'states': counts,
        }
