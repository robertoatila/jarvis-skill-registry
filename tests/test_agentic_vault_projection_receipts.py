import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tooling.agentic.managed_vault_projector import ManagedVaultProjector
from tooling.agentic.vault_projection_receipts import ProjectionReceipt, ProjectionReceiptStore
from tooling.agentic.vault_watcher import VaultWatcher


class ProjectionReceiptTests(unittest.TestCase):
    def test_store_finds_exact_hash_once_and_discards_stale_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / 'state'
            store = ProjectionReceiptStore(state)
            digest = hashlib.sha256(b'generated').hexdigest()
            receipt = ProjectionReceipt(
                receipt_id='projection-receipt-test',
                path='notes/alpha.md',
                content_hash=digest,
                projected_at='2026-09-16T12:00:00+00:00',
                projection_kind='memory',
            )
            store.record(receipt)
            self.assertEqual(store.find_hash('notes/alpha.md', digest), receipt)
            self.assertIsNone(store.find_hash('notes/alpha.md', digest))

            store.record(receipt)
            other = hashlib.sha256(b'human edit').hexdigest()
            self.assertIsNone(store.find_hash('notes/alpha.md', other))
            self.assertIsNone(store.find_hash('notes/alpha.md', digest))

    def test_project_markdown_records_exact_receipt_and_watcher_attributes_self_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / 'state'
            note = root / 'notes' / 'alpha.md'
            note.parent.mkdir()
            original = b'# Human\nKeep this.\n'
            note.write_bytes(original)
            watcher = VaultWatcher(root, state)
            watcher.scan_once()
            projector = ManagedVaultProjector(root, state, clock=lambda: 1_789_500_000.0)

            receipt = projector.project_markdown(note, 'Generated', kind='memory')
            self.assertIsNotNone(receipt)
            self.assertEqual(receipt.path, 'notes/alpha.md')
            self.assertEqual(receipt.projection_kind, 'memory')
            self.assertEqual(receipt.content_hash, hashlib.sha256(note.read_bytes()).hexdigest())
            self.assertTrue(note.read_bytes().startswith(original))
            backups = list((note.parent / 'backups' / 'vault-projection').glob('*.bak'))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), original)

            events = watcher.scan_once()
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].source, 'jarvis_projection')
            self.assertEqual(events[0].projection_receipt, receipt.receipt_id)

    def test_human_edit_after_projection_is_not_inherited_as_jarvis_authorship(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / 'state'
            note = root / 'alpha.md'
            note.write_bytes(b'# Human\n')
            watcher = VaultWatcher(root, state)
            watcher.scan_once()
            projector = ManagedVaultProjector(root, state)
            projector.project_markdown(note, 'Generated', kind='memory')
            watcher.scan_once()

            note.write_bytes(note.read_bytes() + b'\nHuman suffix\n')
            event = watcher.scan_once()[0]
            self.assertEqual(event.source, 'human_or_unknown')
            self.assertIsNone(event.projection_receipt)

    def test_marker_text_without_writer_receipt_never_proves_jarvis_authorship(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / 'state'
            note = root / 'alpha.md'
            note.write_bytes(b'# Human\n')
            watcher = VaultWatcher(root, state)
            watcher.scan_once()

            note.write_bytes(
                b'# Human\n\n<!-- jarvis:projection:start -->\nPretend generated\n<!-- jarvis:projection:end -->\n'
            )
            event = watcher.scan_once()[0]
            self.assertEqual(event.source, 'human_or_unknown')
            self.assertIsNone(event.projection_receipt)

    def test_project_canvas_preserves_human_nodes_and_attributes_generated_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / 'state'
            canvas = root / 'brain.canvas'
            original = {
                'nodes': [{'id': 'human', 'type': 'text', 'text': 'Keep me'}],
                'edges': [],
                'custom': 42,
            }
            canvas.write_text(json.dumps(original), encoding='utf-8')
            watcher = VaultWatcher(root, state)
            watcher.scan_once()
            projector = ManagedVaultProjector(root, state)
            node = {'id': 'jarvis:projection:status', 'type': 'text', 'text': 'Generated'}

            receipt = projector.project_canvas(canvas, [node], [], kind='graph')
            self.assertIsNotNone(receipt)
            data = json.loads(canvas.read_text(encoding='utf-8'))
            self.assertEqual(data['nodes'][0], original['nodes'][0])
            self.assertEqual(data['custom'], 42)
            self.assertEqual(len(data['nodes']), 2)

            event = watcher.scan_once()[0]
            self.assertEqual(event.source, 'jarvis_projection')
            self.assertEqual(event.projection_receipt, receipt.receipt_id)

    def test_noop_projection_returns_no_new_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / 'state'
            note = root / 'alpha.md'
            note.write_bytes(b'# Human\n')
            projector = ManagedVaultProjector(root, state)
            first = projector.project_markdown(note, 'Generated', kind='memory')
            self.assertIsNotNone(first)
            watcher = VaultWatcher(root, state)
            watcher.scan_once()

            self.assertIsNone(projector.project_markdown(note, 'Generated', kind='memory'))
            digest = hashlib.sha256(note.read_bytes()).hexdigest()
            self.assertIsNone(ProjectionReceiptStore(state).find_hash('alpha.md', digest))


if __name__ == '__main__':
    unittest.main()
