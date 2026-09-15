import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

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

    def test_tombstone_overrides_earlier_and_later_active_entries(self):
        self.write_index(self.record(), self.record(lifecycle_state='QUARANTINED'), self.record())
        self.assertEqual(self.hub.catalog()[0], [])

    def test_legacy_adapted_metadata_is_candidate_but_waiver_is_not(self):
        self.write_index(self.record(trust_level='VERIFIED_ADAPTED'),
                         self.record('python-waiver', trust_level='FLAGGED_REVIEW_WAIVER'))
        self.assertEqual([s['id'] for s in self.hub.catalog()[0]], ['python-pro'])

    def test_malformed_or_missing_index_does_not_select_candidates(self):
        for content in ('bad json', '[]', '{"canonical_name":"python-pro","capabilities":3,"lifecycle_state":"ACTIVE","trust_level":"TRUSTED"}'):
            self.index.write_text(content, encoding='utf-8')
            self.assertEqual(self.hub.catalog()[0], [])
            self.assertIsNotNone(self.hub.catalog()[1])

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
        note = self.root / '01 - Arsenal Map of Content.md'
        self.assertIn('[[skills/python-pro/SKILL|python-pro]]', note.read_text(encoding='utf-8'))
        self.assertEqual(self.hub.sync_obsidian()['changed_files'], [])

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

    def test_handoff_reuses_exact_existing_plan_without_resolving_again(self):
        from tooling.agentic.planner_resolver import AutonomousMissionPlanner
        from tooling.agentic.models import Mission, TaskNode
        from tooling.agentic.dag import ExecutionDAG
        planner = AutonomousMissionPlanner.__new__(AutonomousMissionPlanner)
        planner.root = self.root
        from unittest.mock import Mock
        planner.resolver = Mock()
        mission = Mission(mission_id='test-existing-plan', goal='Existing goal')
        mission.dag = ExecutionDAG()
        mission.dag.add_node(TaskNode(task_id='existing-task', title='Existing task', required_skills=['already-chosen']))
        output = planner.format_handoff(mission)
        self.assertIn('already-chosen', output)
        self.assertIn('test-existing-plan', output)
        self.assertIn('Existing goal', output)
        planner.resolver.resolve.assert_not_called()

    def test_existing_arsenal_map_is_not_duplicated(self):
        self.write_index(self.record())
        path = self.root / '01 - Arsenal Map of Content.md'
        original = '# Existing map\n[[skills/python-pro/SKILL|python-pro]]\n'
        path.write_text(original, encoding='utf-8')
        self.hub.sync_obsidian()
        text = path.read_text(encoding='utf-8')
        self.assertTrue(text.startswith(original))
        self.assertEqual(text.count('[[skills/python-pro/SKILL|python-pro]]'), 1)

    def test_canvas_preserves_human_nodes_and_extra_fields(self):
        from tooling.agentic.vault_projection import update_canvas_projection
        path = self.root / 'map.canvas'
        original = {'nodes': [{'id': 'human', 'type': 'text', 'text': 'Keep me'}], 'edges': [], 'custom': 42}
        path.write_text(json.dumps(original), encoding='utf-8')
        node = {'id': 'jarvis:projection:status', 'type': 'text', 'text': 'Generated'}
        update_canvas_projection(path, [node], [])
        self.assertFalse(update_canvas_projection(path, [node], []))
        data = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(data['nodes'][0], original['nodes'][0])
        self.assertEqual(data['custom'], 42)
        self.assertEqual(len(data['nodes']), 2)
        path.write_text('broken', encoding='utf-8')
        with self.assertRaises(ValueError):
            update_canvas_projection(path, [node], [])
        self.assertEqual(path.read_text(), 'broken')

    def test_ui_has_one_goal_input_and_no_parallel_prepare_endpoint(self):
        root = Path(__file__).resolve().parents[1]
        html = (root / 'ui/index.html').read_text(encoding='utf-8')
        self.assertEqual(html.count('id="inputAgenticGoal"'), 1)
        self.assertNotIn('id="workspaceGoal"', html)
        self.assertLess(html.index('id="tabObsidian"'), html.index('id="workspaceHub"'))
        server = (root / 'tooling/jarvis_server.py').read_text(encoding='utf-8')
        self.assertNotIn('/api/workspace/prepare', server)
        self.assertIn('rt.planner.format_handoff(mission)', server)
        self.assertFalse((root / 'tooling/workspace_server.py').exists())


if __name__ == '__main__':
    unittest.main()
