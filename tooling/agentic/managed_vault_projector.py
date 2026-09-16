"""Managed, receipt-bearing writes into the J.A.R.V.I.S. Cognitive Vault."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from typing import Callable

from .vault_projection import update_canvas_projection, update_projection
from .vault_projection_receipts import ProjectionReceipt, ProjectionReceiptStore


class ManagedVaultProjector:
    """Wrap safe Vault projection primitives and record exact resulting hashes."""

    def __init__(
        self,
        root: Path,
        state_dir: Path,
        clock: Callable[[], float] | None = None,
        receipt_store: ProjectionReceiptStore | None = None,
    ) -> None:
        self.root = Path(root).absolute()
        self.state_dir = Path(state_dir).absolute()
        self.clock = clock or time.time
        self.receipts = receipt_store or ProjectionReceiptStore(self.state_dir)

    def _relative(self, path: Path) -> tuple[Path, str]:
        target = Path(path).absolute()
        try:
            relative = target.relative_to(self.root).as_posix()
        except ValueError as exc:
            raise ValueError('Managed projection target must stay within the Vault') from exc
        if not relative or relative == '.':
            raise ValueError('Managed projection target must be a file')
        return target, relative

    def _projected_at(self) -> str:
        return datetime.fromtimestamp(float(self.clock()), timezone.utc).isoformat()

    @staticmethod
    def _receipt_id(
        path: str,
        content_hash: str,
        projected_at: str,
        projection_kind: str,
    ) -> str:
        material = json.dumps(
            {
                'path': path,
                'content_hash': content_hash,
                'projected_at': projected_at,
                'projection_kind': projection_kind,
            },
            sort_keys=True,
            separators=(',', ':'),
            ensure_ascii=False,
        ).encode('utf-8')
        return 'projection-receipt-' + hashlib.sha256(material).hexdigest()

    def _record(self, target: Path, relative: str, kind: str) -> ProjectionReceipt:
        content_hash = hashlib.sha256(target.read_bytes()).hexdigest()
        projected_at = self._projected_at()
        receipt = ProjectionReceipt(
            receipt_id=self._receipt_id(relative, content_hash, projected_at, kind),
            path=relative,
            content_hash=content_hash,
            projected_at=projected_at,
            projection_kind=kind,
        )
        self.receipts.record(receipt)
        return receipt

    def project_markdown(self, path: Path, body: str, *, kind: str) -> ProjectionReceipt | None:
        target, relative = self._relative(path)
        changed = update_projection(target, body)
        if not changed:
            return None
        return self._record(target, relative, kind)

    def project_canvas(
        self,
        path: Path,
        nodes: list,
        edges: list,
        *,
        kind: str,
    ) -> ProjectionReceipt | None:
        target, relative = self._relative(path)
        changed = update_canvas_projection(target, nodes, edges)
        if not changed:
            return None
        return self._record(target, relative, kind)
