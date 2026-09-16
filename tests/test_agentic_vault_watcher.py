import hashlib
import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from tooling.agentic.vault_events import VaultCheckpointStore, VaultEvent
from tooling.agentic.vault_watcher import VaultWatcher


class VaultWatcherTests(unittest.TestCase):
    def test_create_modify_delete_emit_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / 'state'
            note = root / 'notes' / 'alpha.md'
            note.parent.mkdir()
            watcher = VaultWatcher(root, state, clock=lambda: 1_789_500_000.0)

            note.write_bytes(b'# Alpha\n')
            created = watcher.scan_once()
            self.assertEqual(len(created), 1)
            self.assertIsInstance(created[0], VaultEvent)
            self.assertEqual(created[0].kind, 'created')
            self.assertEqual(created[0].path, 'notes/alpha.md')
            self.assertIsNone(created[0].previous_hash)
            first_hash = hashlib.sha256(b'# Alpha\n').hexdigest()
            self.assertEqual(created[0].content_hash, first_hash)
            self.assertEqual(created[0].source, 'human_or_unknown')
            self.assertIsNotNone(datetime.fromisoformat(created[0].observed_at).tzinfo)
            self.assertEqual(watcher.scan_once(), [])

            note.write_bytes(b'# Alpha\nchanged\n')
            modified = watcher.scan_once()
            self.assertEqual([event.kind for event in modified], ['modified'])
            self.assertEqual(modified[0].previous_hash, first_hash)
            second_hash = hashlib.sha256(b'# Alpha\nchanged\n').hexdigest()
            self.assertEqual(modified[0].content_hash, second_hash)
            self.assertEqual(watcher.scan_once(), [])

            note.unlink()
            deleted = watcher.scan_once()
            self.assertEqual([event.kind for event in deleted], ['deleted'])
            self.assertEqual(deleted[0].previous_hash, second_hash)
            self.assertIsNone(deleted[0].content_hash)
            self.assertEqual(watcher.scan_once(), [])

    def test_markdown_and_canvas_are_observed_deterministically(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / 'state'
            (root / 'zeta.md').write_text('zeta\n', encoding='utf-8')
            (root / 'brain.canvas').write_text('{"nodes":[],"edges":[]}\n', encoding='utf-8')

            events = VaultWatcher(root, state).scan_once()
            self.assertEqual([event.path for event in events], ['brain.canvas', 'zeta.md'])
            self.assertEqual([event.kind for event in events], ['created', 'created'])

    def test_restart_from_checkpoint_does_not_reemit_old_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / 'state'
            (root / 'alpha.md').write_text('# Alpha\n', encoding='utf-8')

            first = VaultWatcher(root, state).scan_once()
            self.assertEqual(len(first), 1)
            restarted = VaultWatcher(root, state)
            self.assertEqual(restarted.scan_once(), [])

    def test_mtime_only_change_without_hash_change_emits_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / 'state'
            note = root / 'alpha.md'
            note.write_text('# Alpha\n', encoding='utf-8')
            watcher = VaultWatcher(root, state)
            watcher.scan_once()

            stat = note.stat()
            os.utime(note, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
            self.assertEqual(watcher.scan_once(), [])

    def test_event_identity_is_deterministic_across_independent_checkpoints(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            note = root / 'alpha.md'
            note.write_text('# Alpha\n', encoding='utf-8')

            first = VaultWatcher(root, root / 'state-a', clock=lambda: 100.0).scan_once()[0]
            second = VaultWatcher(root, root / 'state-b', clock=lambda: 999.0).scan_once()[0]
            self.assertEqual(first.event_id, second.event_id)

    def test_ignored_temp_internal_and_oversized_paths_do_not_emit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / 'state'
            for directory in ('.git', '.obsidian', 'state', 'backups'):
                path = root / directory / 'ignored.md'
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('ignored\n', encoding='utf-8')
            (root / '.projection-scratch.md').write_text('temporary\n', encoding='utf-8')
            (root / 'draft.tmp.md').write_text('temporary\n', encoding='utf-8')
            (root / 'valid.md').write_text('ok\n', encoding='utf-8')
            (root / 'large.md').write_text('0123456789\n', encoding='utf-8')

            watcher = VaultWatcher(root, state)
            watcher.MAX_NOTE_BYTES = 4
            events = watcher.scan_once()
            self.assertEqual([event.path for event in events], ['valid.md'])

    def test_recreated_deleted_file_emits_created_again(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / 'state'
            note = root / 'alpha.md'
            note.write_text('# Alpha\n', encoding='utf-8')
            watcher = VaultWatcher(root, state)
            watcher.scan_once()
            note.unlink()
            watcher.scan_once()

            note.write_text('# Alpha\n', encoding='utf-8')
            events = watcher.scan_once()
            self.assertEqual([event.kind for event in events], ['created'])

    def test_future_checkpoint_schema_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / 'state'
            store = VaultCheckpointStore(state)
            store.path.parent.mkdir(parents=True)
            store.path.write_text(
                json.dumps({'schema_version': 999, 'files': {}}),
                encoding='utf-8',
            )

            with self.assertRaisesRegex(ValueError, 'schema'):
                VaultWatcher(root, state).scan_once()


if __name__ == '__main__':
    unittest.main()
