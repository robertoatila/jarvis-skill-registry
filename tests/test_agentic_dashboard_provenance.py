import ast
import json
import re
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
TREE = ast.parse((ROOT / 'tooling/jarvis_server.py').read_text(encoding='utf-8'))


def isolated_function(name, namespace, class_name=None):
    nodes = TREE.body
    if class_name:
        nodes = next(node for node in nodes if isinstance(node, ast.ClassDef) and node.name == class_name).body
    node = next(node for node in nodes if isinstance(node, ast.FunctionDef) and node.name == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<isolated-server-function>', 'exec'), namespace)
    return namespace[name]


class DashboardProvenanceTests(unittest.TestCase):
    def test_historical_release_and_counts_never_become_current_facts(self):
        with tempfile.TemporaryDirectory() as temp:
            state_path = Path(temp) / 'current-state.json'
            state_path.write_text(json.dumps({'phase': 'RELEASE_V1_0_0', 'governance_status': 'SEALED_DEFINITIVE_PRODUCTION', 'total_pins': 870, 'tombstones_count': 12, 'canonical_merkle_root': 'a' * 64, 'canonical_active_skills_count': 1}), encoding='utf-8')
            namespace = {'json': json, 're': re, 'SKILLS_CACHE': {'current': {'security_status': 'PASS'}}, 'SKILLS_DIR': Path(temp) / 'skills', 'CURRENT_STATE_PATH': state_path, 'MANIFEST_110_PATH': Path(temp) / 'missing.json'}
            status = isolated_function('get_current_catalog_status', namespace)()
        self.assertEqual(status['phase'], 'UNKNOWN')
        self.assertEqual(status['governance_status'], 'UNKNOWN')
        self.assertEqual(status['snapshot_phase'], 'RELEASE_V1_0_0')
        self.assertEqual(status['snapshot_governance_status'], 'SEALED_DEFINITIVE_PRODUCTION')
        self.assertEqual(status['snapshot_status'], 'UNVERIFIED_FOR_CURRENT_SOURCE')
        self.assertIsNone(status['total_pins'])
        self.assertIsNone(status['tombstones_count'])
        self.assertEqual(status['snapshot_total_pins'], 870)
        self.assertEqual(status['canonical_active_skills_count'], 1)
        self.assertIsNone(status['canonical_merkle_root'])
        self.assertEqual(status['canonical_merkle_status'], 'UNKNOWN_OR_STALE')
        self.assertEqual(status['snapshot_merkle_root'], 'a' * 64)
        self.assertEqual(status['snapshot_merkle_status'], 'UNVERIFIED_FOR_CURRENT_SOURCE')

    def test_skill_metadata_without_frontmatter_stays_unknown(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill_dir = root / 'skills' / 'example-skill'
            skill_dir.mkdir(parents=True)
            (skill_dir / 'SKILL.md').write_text('# Example\nNo structured metadata.\n', encoding='utf-8')
            cache = {}
            load_skills = isolated_function('load_canonical_skills', {
                'SKILLS_CACHE': cache,
                'SKILLS_DIR': root / 'skills',
                'REGISTRY_ROOT': root,
                're': re,
            })
            skills = load_skills()
        self.assertEqual(len(skills), 1)
        self.assertEqual(skills[0]['description'], '')
        self.assertEqual(skills[0]['capabilities'], [])
        self.assertIsNone(skills[0]['version'])
        self.assertEqual(skills[0]['security_status'], 'UNKNOWN')
        self.assertIsNone(skills[0]['lockfiles_count'])
        self.assertEqual(skills[0]['metadata_sources']['security_status'], 'missing')

    def test_skill_path_resolution_rejects_parent_and_nested_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            skills = Path(temp) / 'skills'
            skill_md = skills / 'safe-skill' / 'SKILL.md'
            skill_md.parent.mkdir(parents=True)
            skill_md.write_text('# Safe', encoding='utf-8')
            resolve_skill = isolated_function('resolve_canonical_skill', {
                'SKILLS_DIR': skills,
                'Path': Path,
                're': re,
            })
            self.assertEqual(resolve_skill('safe-skill'), skill_md.resolve())
            for invalid in ('../state', 'safe-skill/../../state', 'safe-skill\\nested', '..'):
                self.assertIsNone(resolve_skill(invalid))

    def test_json_response_treats_disconnected_browser_as_normal_teardown(self):
        send_json = isolated_function('send_json', {'json': json}, 'JarvisHttpHandler')
        handler = SimpleNamespace(
            send_response=Mock(),
            send_header=Mock(),
            end_headers=Mock(),
            wfile=SimpleNamespace(write=Mock(side_effect=ConnectionAbortedError())),
        )
        send_json(handler, {'status': 'fixture'})
        handler.send_response.assert_called_once_with(200)
        handler.wfile.write.assert_called_once()

    def test_file_response_does_not_write_a_second_response_after_disconnect(self):
        send_file = isolated_function('send_file', {'Path': Path}, 'JarvisHttpHandler')
        with tempfile.TemporaryDirectory() as temp:
            asset = Path(temp) / 'asset.js'
            asset.write_text('fixture', encoding='utf-8')
            handler = SimpleNamespace(
                send_response=Mock(),
                send_header=Mock(),
                end_headers=Mock(),
                send_error=Mock(),
                wfile=SimpleNamespace(write=Mock(side_effect=ConnectionAbortedError())),
            )
            send_file(handler, asset, 'application/javascript')
        handler.send_response.assert_called_once_with(200)
        handler.wfile.write.assert_called_once()
        handler.send_error.assert_not_called()

    def test_new_memory_has_no_invented_personal_facts(self):
        instance = SimpleNamespace(_load=Mock(), _sync_obsidian=Mock())
        initialize = isolated_function('__init__', {'datetime': datetime, 'timezone': timezone, 'OBSIDIAN_MEMORY_PATH': Path('memory.md')}, 'PersistentMemoryEngine')
        initialize(instance)
        self.assertEqual(instance.data['profile'], {})
        self.assertEqual(instance.data['memories'], [])
        instance._load.assert_called_once()



if __name__ == '__main__':
    unittest.main()
