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
            state_path.write_text(json.dumps({'phase': 'RELEASE_V1_0_0', 'governance_status': 'SEALED_DEFINITIVE_PRODUCTION', 'total_pins': 870, 'tombstones_count': 12}), encoding='utf-8')
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

    def test_new_memory_has_no_invented_personal_facts(self):
        instance = SimpleNamespace(_load=Mock(), _sync_obsidian=Mock())
        initialize = isolated_function('__init__', {'datetime': datetime, 'timezone': timezone, 'OBSIDIAN_MEMORY_PATH': Path('memory.md')}, 'PersistentMemoryEngine')
        initialize(instance)
        self.assertEqual(instance.data['profile'], {})
        self.assertEqual(instance.data['memories'], [])
        instance._load.assert_called_once()



if __name__ == '__main__':
    unittest.main()
