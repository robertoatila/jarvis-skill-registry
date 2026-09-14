import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import threading

from tooling.agentic.workspace_hub import WorkspaceHub
from tooling.agentic.vault_projection import update_projection, START, END
from tooling.agentic.progressive_disclosure import ProgressiveDisclosureEngine


class ConnectedWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'index').mkdir()
        self.index = self.root / 'index/resources.jsonl'
        self.hub = WorkspaceHub(self.root, which=lambda _: None)

    def write_index(self, *records):
        self.index.write_text('\n'.join(json.dumps(record) for record in records), encoding='utf-8')

    def record(self, name='python-pro', **extra):
        return {'canonical_name': name, 'description': 'Python API', 'capabilities': ['python'],
                'lifecycle_state': 'ACTIVE', 'trust_level': 'TRUSTED', **extra}

    def test_preparation_is_deterministic_and_does_not_execute(self):
        self.write_index(self.record(), self.record('untrusted', trust_level='UNKNOWN'))
        first = self.hub.prepare('Python API')
        self.assertEqual(first, self.hub.prepare('Python API'))
        self.assertEqual([skill['id'] for skill in first['skills']], ['python-pro'])
        self.assertFalse(first['execution_started'])
        self.assertFalse((self.root / 'state').exists())
        self.assertLessEqual(first['estimated_metadata_tokens'], 700)

    def test_tombstone_overrides_earlier_and_later_active_entries(self):
        self.write_index(self.record(), self.record(lifecycle_state='QUARANTINED'), self.record())
        self.assertEqual(self.hub.prepare('Python')['skills'], [])

    def test_legacy_adapted_metadata_is_candidate_but_waiver_is_not(self):
        self.write_index(self.record(trust_level='VERIFIED_ADAPTED'),
                         self.record('python-waiver', trust_level='FLAGGED_REVIEW_WAIVER'))
        self.assertEqual([s['id'] for s in self.hub.prepare('Python')['skills']], ['python-pro'])

    def test_malformed_or_missing_index_does_not_select_candidates(self):
        for content in ('bad json', '[]', '{"canonical_name":"python-pro","capabilities":3,"lifecycle_state":"ACTIVE","trust_level":"TRUSTED"}'):
            self.index.write_text(content, encoding='utf-8')
            self.assertEqual(self.hub.prepare('Python')['skills'], [])
            self.assertIsNotNone(self.hub.catalog()[1])

    def test_oversized_goal_and_bad_budget_rejected(self):
        for goal in ('', ' ' * 10, 'x' * 2001, None):
            with self.assertRaises(ValueError):
                self.hub.prepare(goal)
        with self.assertRaises(ValueError):
            self.hub.prepare('Python', token_budget=1)

    def test_detection_is_not_session_verification(self):
        hub = WorkspaceHub(self.root, which=lambda _: 'C:/fake-command.exe')
        status = hub.snapshot()
        self.assertTrue(status['connections'][0]['command_detected'])
        self.assertTrue(all(not item['session_verified'] for item in status['connections']))
        self.assertFalse(status['autonomy']['provider_invoked'])

    def test_note_projection_preserves_human_bytes_and_is_idempotent(self):
        note = self.root / 'note.md'
        original = b'# Human\r\nKeep this.\r\n'
        note.write_bytes(original)
        self.assertTrue(update_projection(note, 'Generated'))
        self.assertTrue(note.read_bytes().startswith(original))
        backups = list((self.root / 'backups/vault-projection').glob('*.bak'))
        self.assertEqual(backups[0].read_bytes(), original)
        self.assertFalse(update_projection(note, 'Generated'))
        self.assertEqual(len(list((self.root / 'backups/vault-projection').glob('*.bak'))), 1)
        note.write_bytes(note.read_bytes() + b'\nHuman suffix')
        update_projection(note, 'Updated')
        self.assertTrue(note.read_bytes().endswith(b'Human suffix'))
        self.assertNotIn('Generated', note.read_text())

    def test_damaged_markers_do_not_modify_note(self):
        note = self.root / 'note.md'
        for text in (START, END, END + START, START + START + END):
            note.write_text(text, encoding='utf-8')
            with self.assertRaises(ValueError):
                update_projection(note, 'new')
            self.assertEqual(note.read_text(encoding='utf-8'), text)

    def test_sync_projects_metadata_without_reading_skill_payloads(self):
        self.write_index(self.record())
        result = self.hub.sync_obsidian()
        self.assertEqual(result['status'], 'SUCCESS')
        note = self.root / result['note']
        self.assertIn('[[skills/python-pro/SKILL|python-pro]]', note.read_text(encoding='utf-8'))
        self.assertFalse(self.hub.sync_obsidian()['changed'])

    def test_quarantine_blocks_directory_fallback_and_cached_execution(self):
        skills = self.root / 'skills'
        skill = skills / 'python-pro'
        skill.mkdir(parents=True)
        (skill / 'SKILL.md').write_text('---\nname: python-pro\n---\nInstructions', encoding='utf-8')
        self.write_index(self.record())
        engine = ProgressiveDisclosureEngine(skills, self.index)
        engine.disclose_execution('python-pro')
        self.write_index(self.record(lifecycle_state='QUARANTINED'))
        with patch.object(engine, '_extract_level_0_from_dir', side_effect=AssertionError('Payload accessed')):
            self.assertNotIn('python-pro', engine.load_catalog())
            with self.assertRaises(ValueError):
                engine.disclose_execution('python-pro')

    def test_skill_identifier_cannot_escape_root(self):
        engine = ProgressiveDisclosureEngine(self.root / 'skills', self.index)
        with self.assertRaises(ValueError):
            engine.disclose_manifest('../private')

    def test_invalid_index_cannot_reuse_an_older_catalog(self):
        self.write_index(self.record())
        engine = ProgressiveDisclosureEngine(self.root / 'skills', self.index)
        self.assertIn('python-pro', engine.load_catalog())
        self.index.write_text('invalid json', encoding='utf-8')
        for _ in range(2):
            with self.assertRaises(ValueError):
                engine.disclose_execution('python-pro')

    def test_lightweight_server_serves_real_ui_and_rejects_foreign_origin(self):
        from tooling.workspace_server import make_handler
        self.write_index(self.record())
        server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(self.root))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = HTTPConnection('127.0.0.1', server.server_port, timeout=3)
            client.request('GET', '/')
            response = client.getresponse()
            self.assertEqual(response.status, 200)
            self.assertIn(b'id="workspaceGoal"', response.read())
            self.assertIn("frame-ancestors 'none'", response.getheader('Content-Security-Policy'))
            client.request('GET', '/api/workspace/prepare?goal=Python')
            response = client.getresponse()
            self.assertEqual(json.loads(response.read())['skills'][0]['id'], 'python-pro')
            client.request('GET', '/api/workspace', headers={'Origin': 'https://foreign.invalid'})
            response = client.getresponse()
            self.assertEqual(response.status, 403)
            response.read()
            client.request('GET', '/state/jarvis_memory.json')
            response = client.getresponse()
            self.assertEqual(response.status, 404)
            response.read()
            client.close()
            self.assertFalse((self.root / 'state').exists())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == '__main__':
    unittest.main()
