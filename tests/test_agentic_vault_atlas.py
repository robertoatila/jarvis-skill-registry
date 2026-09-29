import json
import os
from pathlib import Path
import tempfile
import subprocess
import unittest

from tooling.agentic.vault_atlas import VaultAtlas, apply_graph, MASTER, ARSENAL, START, END


class VaultAtlasTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.put(MASTER, '# Master\r\nHuman text\r\n')
        self.put(ARSENAL, '# Arsenal')
        config = {'schema_version': 1, 'enabled': True, 'page_size': 10,
                  'generated_root': 'JARVIS/Atlas', 'path_navigation': {'enabled': True, 'max_depth': 2}, 'hubs': [
                      {'id': 'external', 'path': '29 - External.md', 'title': 'External', 'prefixes': [], 'types': []},
                      {'id': 'docs', 'path': '25 - Docs.md', 'title': 'Docs', 'prefixes': ['docs/'], 'types': ['decision']},
                      {'id': 'relations', 'path': '32 - Relations.md', 'title': 'Relations', 'prefixes': [], 'types': []}],
                  'anchors': {}}
        self.put('config/vault/atlas.json', json.dumps(config))
        self.put('cache/starred_catalog.json', json.dumps([{'full_name': f'owner/repo{i}', 'language': 'Python',
                 'description': 'Source text [[fake]] #tag <script>bad</script>'} for i in range(23)]))
        self.put('docs/target.md', '# Target')

    def put(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text.encode())

    def test_dry_run_no_writes_and_no_truncation(self):
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        atlas = VaultAtlas(self.root)
        report = atlas.plan()
        after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(report['external_records'], 23)
        self.assertEqual(sum('/GitHub/' in p for p in atlas.outputs), 23)
        self.assertEqual(sum('/Collections/language-' in p for p in atlas.outputs), 3)
        self.assertFalse(any('[[fake]]' in body for body in atlas.outputs.values()))
        cards = [body for path, body in atlas.outputs.items() if '/GitHub/' in path]
        self.assertTrue(any('#lang-python-' in body for body in cards))

    def test_preservation_backup_receipts_and_idempotence(self):
        human = b'# Human\r\nKeep me\r\n'
        self.put('29 - External.md', human.decode())
        atlas = VaultAtlas(self.root)
        atlas.plan()
        result = atlas.apply()
        note = self.root / '29 - External.md'
        self.assertTrue(note.read_bytes().startswith(human))
        self.assertTrue(any(p.read_bytes() == human for p in (self.root / 'backups').rglob('*.bak')))
        from tooling.agentic.vault_projection_receipts import ProjectionReceiptStore
        from tooling.agentic.vault_atlas import digest
        self.assertIsNotNone(ProjectionReceiptStore(self.root / 'state').find_hash('29 - External.md', digest(note.read_bytes())))
        again = VaultAtlas(self.root)
        again.plan()
        self.assertEqual(again.apply()['changed_files'], [])
        self.assertGreater(len(result['changed_files']), 23)

    def test_malformed_target_prevents_all_writes(self):
        self.put('32 - Relations.md', START)
        with self.assertRaises(ValueError):
            VaultAtlas(self.root).plan()
        self.assertFalse((self.root / 'JARVIS').exists())

    def test_source_change_blocks_apply(self):
        atlas = VaultAtlas(self.root)
        atlas.plan()
        self.put('docs/target.md', 'Changed concurrently')
        with self.assertRaises(RuntimeError):
            atlas.apply()
        self.assertFalse((self.root / 'JARVIS').exists())

    def test_target_change_blocks_apply(self):
        atlas = VaultAtlas(self.root)
        atlas.plan()
        self.put('29 - External.md', 'New human note')
        with self.assertRaises(RuntimeError):
            atlas.apply()
        self.assertFalse((self.root / 'JARVIS').exists())

    def test_relations_require_explicit_valid_targets(self):
        relation = json.dumps([{'type': 'supported_by', 'target': 'docs/target.md'}])
        self.put('docs/source.md', f'---\ntype: decision\njarvis_relations: {relation}\n---\nSource')
        atlas = VaultAtlas(self.root)
        self.assertEqual(atlas.plan()['explicit_relations'], 1)
        self.assertIn('`supported_by`', atlas.outputs['32 - Relations.md'])
        self.put('docs/source.md', '---\njarvis_relations: [{"type":"supported_by","target":"../outside.md"}]\n---\n')
        with self.assertRaises(ValueError):
            VaultAtlas(self.root).plan()

    def test_no_keyword_relationships(self):
        self.put('docs/unrelated.md', '# Target Python repo project person evidence')
        self.assertEqual(VaultAtlas(self.root).plan()['explicit_relations'], 0)

    def test_path_navigation_connects_notes_by_containment_without_reading_or_rewriting_them(self):
        self.put('staging/provider/nested/imported.md', '# Preserve this imported payload')
        for index in range(12):
            self.put(f'staging/provider/nested/imported-{index}.md', '# Preserve this payload')
        original = (self.root / 'staging/provider/nested/imported.md').read_bytes()
        atlas = VaultAtlas(self.root)
        report = atlas.plan()
        self.assertGreaterEqual(report['navigation_notes'], 14)
        self.assertGreater(report['navigation_groups'], 0)
        self.assertGreater(report['navigation_pages'], report['navigation_groups'])
        folder_page = next(path for path, body in atlas.outputs.items()
                           if path.startswith('JARVIS/Atlas/Navigation/staging-provider') and
                           'Classificação: pertença por caminho' in body)
        note_page = next(path for path, body in atlas.outputs.items()
                         if path.startswith('JARVIS/Atlas/Navigation/Lists/') and
                         '[[staging/provider/nested/imported.md|staging/provider/nested/imported.md]]' in body)
        self.assertIn('JARVIS/Atlas/Navigation/Lists/', atlas.outputs[folder_page])
        self.assertIn('[[staging/provider/nested/imported.md|staging/provider/nested/imported.md]]', atlas.outputs[note_page])
        self.assertFalse(any('/Collections/folder-' in path for path in atlas.outputs))
        self.assertEqual((self.root / 'staging/provider/nested/imported.md').read_bytes(), original)
        self.assertTrue(any('Mapa de arquivos do Vault' in body for path, body in atlas.outputs.items()
                            if path.endswith('00 - Vault File Map.md')))

    def test_path_navigation_respects_active_obsidian_ignore_filters_without_dropping_paths(self):
        self.put('reports/backups/2026/private.md', '# Preserve and retain this note')
        self.put('.github/ISSUE_TEMPLATE/bug_report.md', '# Keep hidden dot-folder content')
        self.put('.obsidian/app.json', json.dumps({'userIgnoreFilters': ['backups/*']}))
        atlas = VaultAtlas(self.root)
        atlas.plan()
        page = next(body for path, body in atlas.outputs.items()
                    if path.startswith('JARVIS/Atlas/Navigation/reports-backups-'))
        self.assertIn('`reports/backups/2026/private.md`', page)
        self.assertNotIn('[[reports/backups/2026/private.md|', page)
        self.assertEqual((self.root / 'reports/backups/2026/private.md').read_text(),
                         '# Preserve and retain this note')
        github_page = next(body for path, body in atlas.outputs.items()
                           if path.startswith('JARVIS/Atlas/Navigation/github-') and
                           '`.github/ISSUE_TEMPLATE/bug_report.md`' in body)
        self.assertIn('`.github/ISSUE_TEMPLATE/bug_report.md`', github_page)
        self.assertNotIn('[[.github/ISSUE_TEMPLATE/bug_report.md|', github_page)

    def test_invalid_cache_fails_closed(self):
        for data in ({}, [{'full_name': '../outside'}]):
            self.put('cache/starred_catalog.json', json.dumps(data))
            with self.assertRaises(ValueError):
                VaultAtlas(self.root).plan()

    def test_duplicate_identity_preserves_all_variants(self):
        self.put('cache/starred_catalog.json', json.dumps([{'full_name': 'o/r', 'stars': 4}, {'full_name': 'O/R', 'stars': 5}]))
        atlas = VaultAtlas(self.root)
        result = atlas.plan()
        self.assertEqual(result['external_records'], 1)
        self.assertEqual(result['warnings'][0]['variants'], 2)
        body = next(body for path, body in atlas.outputs.items() if '/GitHub/' in path)
        self.assertEqual(body.count('## Registro de origem'), 2)

    def test_broken_receipts_prevent_note_changes(self):
        atlas = VaultAtlas(self.root)
        atlas.plan()
        self.put('state/obsidian/projection_receipts.json', 'broken')
        with self.assertRaises(ValueError):
            atlas.apply()
        self.assertFalse((self.root / 'JARVIS').exists())

    def test_graph_preserves_unknown_settings_and_backup(self):
        self.put('.obsidian/graph.json', '{"unknownSetting":42,"showTags":true}')
        self.put('config/vault/graph-universe.json', '{"showTags":false}')
        self.assertTrue(apply_graph(self.root, 'universe'))
        data = json.loads((self.root / '.obsidian/graph.json').read_text())
        self.assertEqual(data, {'unknownSetting': 42, 'showTags': False})
        self.assertFalse(apply_graph(self.root, 'universe'))

    def test_graph_profile_can_be_applied_from_versioned_checkout_to_another_vault(self):
        profile_root = self.root / 'profiles'
        target_root = self.root / 'target-vault'
        (profile_root / 'config/vault').mkdir(parents=True)
        (target_root / '.obsidian').mkdir(parents=True)
        (target_root / '.obsidian/graph.json').write_text('{"futureOption":true}', encoding='utf-8')
        (profile_root / 'config/vault/graph-universe.json').write_text(
            '{"scale":0.015625,"showOrphans":true}', encoding='utf-8')
        self.assertTrue(apply_graph(target_root, 'universe', profile_root=profile_root))
        graph = json.loads((target_root / '.obsidian/graph.json').read_text(encoding='utf-8'))
        self.assertEqual(graph, {'futureOption': True, 'scale': 0.015625, 'showOrphans': True})

    def test_individual_receipt_is_exact_hash_and_one_shot(self):
        from tooling.agentic.vault_projection_receipts import ProjectionReceiptStore, ProjectionReceipt
        store = ProjectionReceiptStore(self.root / 'state')
        receipt = ProjectionReceipt('projection-receipt-test123', 'note.md', 'a' * 64,
                                    '2026-09-27T12:00:00+00:00', 'atlas')
        store.record_individual(receipt)
        self.assertEqual(store.find_hash('note.md', 'a' * 64), receipt)
        self.assertIsNone(store.find_hash('note.md', 'a' * 64))
        store.record_individual(receipt)
        self.assertIsNone(store.find_hash('note.md', 'b' * 64))
        self.assertIsNone(store.find_hash('note.md', 'a' * 64))

    def test_individual_and_aggregate_receipts_replace_each_other(self):
        from tooling.agentic.vault_projection_receipts import ProjectionReceiptStore, ProjectionReceipt
        store = ProjectionReceiptStore(self.root / 'state')
        old = ProjectionReceipt('projection-receipt-old123', 'note.md', 'a' * 64,
                               '2026-09-27T12:00:00+00:00', 'atlas')
        new = ProjectionReceipt('projection-receipt-new123', 'note.md', 'b' * 64,
                               '2026-09-27T13:00:00+00:00', 'atlas')
        store.record(old)
        store.record_individual(new)
        self.assertEqual(store.find_hash('note.md', 'b' * 64), new)
        self.assertIsNone(store.find_hash('note.md', 'a' * 64))
        store.record_individual(old)
        store.record(new)
        self.assertEqual(store.find_hash('note.md', 'b' * 64), new)
        self.assertIsNone(store.find_hash('note.md', 'a' * 64))

    def test_linked_output_directory_rejected(self):
        other = self.root / 'other'
        other.mkdir()
        try:
            (self.root / 'JARVIS').symlink_to(other, target_is_directory=True)
        except OSError:
            if os.name != 'nt':
                self.skipTest('OS does not permit creating symlinks')
            subprocess.run(['cmd', '/c', 'mklink', '/J', str(self.root / 'JARVIS'), str(other)],
                           check=True, capture_output=True)
        with self.assertRaises(ValueError):
            VaultAtlas(self.root).plan()


if __name__ == '__main__':
    unittest.main()
