import json
from pathlib import Path
import tempfile
import unittest

from tooling.agentic.niche_dispatcher import NicheDispatcher
from tooling.agentic.workspace_hub import WorkspaceHub


OBSIDIAN_SKILLS = (
    'obsidian-cli-controller',
    'obsidian-markdown-syntax',
    'obsidian-database-bases',
)


class ObsidianToolRoutingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'index').mkdir()
        rows = []
        for name in OBSIDIAN_SKILLS:
            folder = self.root / 'skills' / name
            folder.mkdir(parents=True)
            (folder / 'SKILL.md').write_text(
                f'---\nname: {name}\ndescription: Safe {name} instructions.\n---\n\nUse this capability.',
                encoding='utf-8',
            )
            rows.append({'canonical_name': name, 'description': f'{name} capability',
                         'capabilities': [name], 'lifecycle_state': 'ACTIVE',
                         'trust_level': 'VERIFIED_ADAPTED'})
        self.index = self.root / 'index/resources.jsonl'
        self.index.write_text('\n'.join(json.dumps(row) for row in rows), encoding='utf-8')

    def test_obsidian_intent_loads_only_registry_eligible_tools(self):
        dispatcher = NicheDispatcher(self.root, allow_network=False)
        result = dispatcher.dispatch('Configure o Graph View do Obsidian')
        self.assertEqual(result.niche, 'OBSIDIAN_TOOLS')
        self.assertTrue(result.handled)
        self.assertEqual(result.metadata['skills'], sorted(OBSIDIAN_SKILLS))
        self.assertIn('CLI executável localizado:', result.enrichment_context)
        self.assertIn('Safe obsidian-cli-controller instructions.', result.enrichment_context)
        self.assertFalse(result.metadata['session_verified'])

    def test_quarantined_skill_is_not_loaded_by_automatic_routing(self):
        rows = [json.loads(line) for line in self.index.read_text(encoding='utf-8').splitlines()]
        rows.append({'canonical_name': 'obsidian-cli-controller', 'lifecycle_state': 'QUARANTINED',
                     'trust_level': 'VERIFIED_ADAPTED', 'capabilities': []})
        self.index.write_text('\n'.join(json.dumps(row) for row in rows), encoding='utf-8')
        result = NicheDispatcher(self.root, allow_network=False).dispatch('Use Obsidian CLI')
        self.assertEqual(result.niche, 'OBSIDIAN_TOOLS')
        self.assertNotIn('obsidian-cli-controller', result.metadata['skills'])
        self.assertEqual(len(result.metadata['skills']), 2)

    def test_snapshot_lists_active_obsidian_capabilities_without_claiming_a_session(self):
        hub = WorkspaceHub(self.root, which=lambda _: 'obsidian.exe')
        status = hub.snapshot()
        obsidian = next(item for item in status['connections'] if item['id'] == 'obsidian')
        self.assertTrue(obsidian['command_detected'])
        self.assertEqual(obsidian['available_skills'], sorted(OBSIDIAN_SKILLS))
        self.assertFalse(obsidian['session_verified'])

    def test_snapshot_does_not_advertise_missing_skill_payload(self):
        (self.root / 'skills' / 'obsidian-database-bases' / 'SKILL.md').unlink()
        hub = WorkspaceHub(self.root, which=lambda _: None)
        status = hub.snapshot()
        obsidian = next(item for item in status['connections'] if item['id'] == 'obsidian')
        self.assertNotIn('obsidian-database-bases', obsidian['available_skills'])

    def test_non_obsidian_request_is_not_routed_to_obsidian_tools(self):
        result = NicheDispatcher(self.root, allow_network=False).dispatch('Organize meu trabalho')
        self.assertFalse(result.handled)
        self.assertEqual(result.niche, 'GENERAL')


if __name__ == '__main__':
    unittest.main()
