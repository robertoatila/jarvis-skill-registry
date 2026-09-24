import json
import tempfile
import unittest
from pathlib import Path

from tooling.agentic.second_brain_graph import SecondBrainGraphBuilder


class SecondBrainGraphBuilderTests(unittest.TestCase):
    def test_builds_links_classifies_and_uses_canvas_without_scanning_ignored_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'Project Alpha.md').write_text(
                '---\\ntitle: Project Alpha\\ntype: project\\ntags: [client, active]\\n---\\n'
                '# Project Alpha\\n[[Meeting 01]]\\n[Decision](Decision.md)\\n',
                encoding='utf-8',
            )
            (root / 'Meeting 01.md').write_text('# Meeting 01\\n[[Project Alpha]]\\n', encoding='utf-8')
            (root / 'Decision.md').write_text('---\\ntype: decision\\n---\\n# Decision\\n', encoding='utf-8')
            (root / 'skills').mkdir()
            (root / 'skills' / 'Ignored.md').write_text('# Ignored\\n[[Project Alpha]]', encoding='utf-8')
            canvas = {
                'nodes': [
                    {'id': 'a', 'type': 'file', 'file': 'Project Alpha.md'},
                    {'id': 'b', 'type': 'file', 'file': 'Decision.md'},
                ],
                'edges': [{'id': 'e1', 'fromNode': 'a', 'toNode': 'b'}],
            }
            (root / 'JARVIS-Brain-Map.canvas').write_text(json.dumps(canvas), encoding='utf-8')

            graph = SecondBrainGraphBuilder(root, max_nodes=50, max_edges=50).build()

            self.assertTrue(graph['read_only'])
            ids = {node['id'] for node in graph['nodes']}
            self.assertEqual(ids, {'Project Alpha.md', 'Meeting 01.md', 'Decision.md'})
            kinds = {node['id']: node['kind'] for node in graph['nodes']}
            self.assertEqual(kinds['Project Alpha.md'], 'project')
            self.assertEqual(kinds['Meeting 01.md'], 'meeting')
            self.assertEqual(kinds['Decision.md'], 'decision')
            relations = {(edge['source'], edge['target'], edge['relation']) for edge in graph['edges']}
            self.assertIn(('Project Alpha.md', 'Meeting 01.md', 'link'), relations)
            self.assertIn(('Project Alpha.md', 'Decision.md', 'link'), relations)
            self.assertIn(('Project Alpha.md', 'Decision.md', 'canvas'), relations)
            self.assertNotIn('skills/Ignored.md', ids)


if __name__ == '__main__':
    unittest.main()
