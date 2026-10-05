"""The disposable validator copies tracked public inputs, never local extras."""
import subprocess
import tempfile
import unittest
from pathlib import Path

from tooling.validate_isolated import copy_tracked_public_sources


class IsolatedSourceManifestTests(unittest.TestCase):
    def test_untracked_local_files_never_enter_validation_sandbox(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'repo'
            sandbox = Path(temp) / 'sandbox'
            (root / '.obsidian').mkdir(parents=True)
            (root / 'ui').mkdir()
            (root / '.obsidian' / 'workspace.json').write_text('{"layout":"public"}', encoding='utf-8')
            (root / 'ui' / 'app.js').write_text('const version = 1;', encoding='utf-8')
            (root / '.env.example').write_text('JARVIS_API_KEY=placeholder\n', encoding='utf-8')

            subprocess.run(['git', 'init', str(root)], check=True, capture_output=True)
            subprocess.run(['git', '-C', str(root), 'config', 'user.name', 'Test'], check=True)
            subprocess.run(['git', '-C', str(root), 'config', 'user.email', 'test@example.invalid'], check=True)
            subprocess.run(['git', '-C', str(root), 'add', '.obsidian/workspace.json', 'ui/app.js', '.env.example'], check=True)
            subprocess.run(['git', '-C', str(root), 'commit', '-m', 'tracked public inputs'], check=True, capture_output=True)

            # A tracked working-tree change remains part of the candidate input.
            (root / 'ui' / 'app.js').write_text('const version = 2;', encoding='utf-8')
            # Simulate local Obsidian/provider configuration and an imported file.
            private_settings = root / '.obsidian' / 'plugins' / 'copilot' / 'data.json'
            private_settings.parent.mkdir(parents=True)
            private_settings.write_text('{"apiKey":"must-not-copy"}', encoding='utf-8')
            (root / 'ui' / 'untracked.js').write_text('local-only', encoding='utf-8')

            copy_tracked_public_sources(root, sandbox)

            self.assertEqual((sandbox / 'ui' / 'app.js').read_text(encoding='utf-8'), 'const version = 2;')
            self.assertEqual((sandbox / '.env.example').read_text(encoding='utf-8'), 'JARVIS_API_KEY=placeholder\n')
            self.assertTrue((sandbox / '.obsidian' / 'workspace.json').is_file())
            self.assertFalse((sandbox / '.obsidian' / 'plugins' / 'copilot' / 'data.json').exists())
            self.assertFalse((sandbox / 'ui' / 'untracked.js').exists())


if __name__ == '__main__':
    unittest.main()
