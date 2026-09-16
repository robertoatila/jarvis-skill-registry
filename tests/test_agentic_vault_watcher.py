import json
import tempfile
import time
import unittest
from pathlib import Path

from tooling.agentic.vault_watcher import VaultWatcher


START = '<!-- jarvis:projection:start -->'
END = '<!-- jarvis:projection:end -->'


class VaultWatcherTests(unittest.TestCase):
    def test_discovers_new_and_modified_markdown_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / 'state'
            note = root / 'notes' / 'alpha.md'
            note.parent.mkdir()
            note.write_text('# Alpha\n', encoding='utf-8')

            watcher = VaultWatcher(root, state)
            first = watcher.scan()
            self.assertEqual([change.relative_path for change in first], ['notes/alpha.md'])
            self.assertEqual(watcher.scan(), [])

            time.sleep(0.01)
            note.write_text('# Alpha\nchanged\n', encoding='utf-8')
            second = watcher.scan()
            self.assertEqual([change.relative_path for change in second], ['notes/alpha.md'])
            self.assertEqual(watcher.scan(), [])

    def test_restart_does_not_reemit_unchanged_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / 'state'
            note = root / 'alpha.md'
            note.write_text('# Alpha\n', encoding='utf-8')

            VaultWatcher(root, state).scan()
            restarted = VaultWatcher(root, state)
            self.assertEqual(restarted.scan(), [])

    def test_projection_only_update_is_suppressed_but_human_update_emits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / 'state'
            note = root / 'alpha.md'
            note.write_text('# Alpha\n', encoding='utf-8')
            watcher = VaultWatcher(root, state)
            watcher.scan()

            note.write_text(
                '# Alpha\n\n'
                f'{START}\nmanaged v1\n{END}\n',
                encoding='utf-8',
            )
            self.assertEqual(watcher.scan(), [])

            note.write_text(
                '# Alpha changed by user\n\n'
                f'{START}\nmanaged v2\n{END}\n',
                encoding='utf-8',
            )
            changes = watcher.scan()
            self.assertEqual([change.relative_path for change in changes], ['alpha.md'])

    def test_malformed_projection_markers_are_not_treated_as_jarvis_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / 'state'
            note = root / 'alpha.md'
            note.write_text('# Alpha\n', encoding='utf-8')
            watcher = VaultWatcher(root, state)
            watcher.scan()

            note.write_text(f'# Alpha\n{START}\nmanaged without end\n', encoding='utf-8')
            changes = watcher.scan()
            self.assertEqual([change.relative_path for change in changes], ['alpha.md'])

    def test_ignores_internal_temp_and_oversized_notes(self):
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
            changes = watcher.scan()
            self.assertEqual([change.relative_path for change in changes], ['valid.md'])

    def test_deleted_note_recreated_with_same_content_is_new_again(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / 'state'
            note = root / 'alpha.md'
            note.write_text('# Alpha\n', encoding='utf-8')
            watcher = VaultWatcher(root, state)
            watcher.scan()

            note.unlink()
            self.assertEqual(watcher.scan(), [])
            note.write_text('# Alpha\n', encoding='utf-8')
            changes = watcher.scan()
            self.assertEqual([change.relative_path for change in changes], ['alpha.md'])

    def test_future_state_schema_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / 'state'
            state_file = state / 'obsidian' / 'vault_watcher.json'
            state_file.parent.mkdir(parents=True)
            state_file.write_text(
                json.dumps({'schema_version': 999, 'notes': {}}),
                encoding='utf-8',
            )

            with self.assertRaisesRegex(ValueError, 'schema'):
                VaultWatcher(root, state).scan()


if __name__ == '__main__':
    unittest.main()
