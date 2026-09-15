"""Exercise the actual browser formatting functions using Node's standard library."""
import shutil
import subprocess
import unittest
from pathlib import Path


class TestUiSecurity(unittest.TestCase):
    def test_html_and_markdown_cannot_break_quoted_attributes(self):
        node = shutil.which('node')
        if not node:
            self.skipTest('Node is required to validate JavaScript behavior')
        source = (Path(__file__).resolve().parents[1]/'ui/jarvis.js').read_text(encoding='utf-8')
        functions = []
        for name in ('escapeHtml', 'renderMarkdown'):
            start = source.index('  function '+name+'(')
            end = source.index('\n  }', start) + len('\n  }')
            functions.append(source[start:end])
        script = '\n'.join(functions) + r'''
const assert = require('node:assert/strict');
assert.equal(escapeHtml(0), '0');
assert.equal(escapeHtml('"<svg onload=alert(1)>\''), '&quot;&lt;svg onload=alert(1)&gt;&#39;');
const html = renderMarkdown('[link](https://example.invalid/" onmouseover="alert)');
assert.ok(!html.includes(' onmouseover="'));
assert.ok(!renderMarkdown('<script>alert(1)</script>').includes('<script>'));
'''
        result = subprocess.run([node, '-e', script], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
