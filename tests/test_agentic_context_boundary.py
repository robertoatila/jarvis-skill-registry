"""Security regression tests for ContextGovernor local source admission."""

import tempfile
import unittest
from pathlib import Path

from tooling.agentic.adapters.local import MAX_PAYLOAD_BYTES
from tooling.agentic.context_governor import ContextGovernor


class TestContextProtectedPathBoundary(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.governor = ContextGovernor(workspace_root=self.root)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_regular_workspace_file_is_readable(self):
        (self.root / "docs").mkdir()
        (self.root / "docs" / "note.txt").write_text("bounded context", encoding="utf-8")

        content, receipt = self.governor.read_with_receipt("docs/note.txt")

        self.assertEqual(content, "bounded context")
        self.assertEqual(receipt.sources_loaded, ["docs/note.txt"])

    def test_protected_sources_are_rejected_before_read(self):
        protected = {
            ".env": "SECRET=do-not-ingest",
            "config/provider.json": '{"token":"secret"}',
            "state/session.json": '{"credential":"secret"}',
            "backups/old.env": "SECRET=old",
            ".git/config": "[remote \"origin\"]",
        }
        for relative, body in protected.items():
            with self.subTest(path=relative):
                target = self.root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(body, encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.governor.read_with_receipt(relative)

    def test_env_suffix_names_are_rejected(self):
        target = self.root / "nested" / ".env.local"
        target.parent.mkdir(parents=True)
        target.write_text("TOKEN=secret", encoding="utf-8")

        with self.assertRaises(ValueError):
            self.governor.read_with_receipt("nested/.env.local")

    def test_context_source_cannot_exceed_local_read_limit(self):
        target = self.root / "large.txt"
        target.write_bytes(b"x" * (MAX_PAYLOAD_BYTES + 1))

        with self.assertRaises(ValueError):
            self.governor.read_with_receipt("large.txt")


if __name__ == "__main__":
    unittest.main()
