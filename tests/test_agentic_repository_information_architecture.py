"""Repository information-architecture contracts.

These checks keep documentation discoverable without moving public paths or
turning historical material into current validation claims.
"""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestRepositoryInformationArchitecture(unittest.TestCase):
    def test_documentation_entry_points_exist(self):
        required = (
            ROOT / "docs" / "README.md",
            ROOT / "docs" / "history" / "README.md",
            ROOT / "docs" / "superpowers" / "README.md",
            ROOT / "docs" / "superpowers" / "plans" / "2026-09-15-v0.2.0-plan2-execution-status.md",
        )
        for path in required:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertTrue(path.is_file(), f"Missing repository documentation entry point: {path}")

    def test_docs_index_names_canonical_sources(self):
        docs_index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
        canonical_refs = (
            "../README.md",
            "../AGENTS.md",
            "../DESIGN.md",
            "../CONTRIBUTING.md",
            "../SECURITY.md",
            "ARCHITECTURE.md",
            "roadmap/JARVIS_AUTONOMOUS_INTELLIGENCE_PLAN.md",
            "superpowers/plans/2026-09-15-v0.2.0-governor-context-memory-routing.md",
        )
        for ref in canonical_refs:
            with self.subTest(ref=ref):
                self.assertIn(ref, docs_index)

    def test_history_index_marks_historical_material_as_non_authoritative(self):
        history = (ROOT / "docs" / "history" / "README.md").read_text(encoding="utf-8").lower()
        self.assertIn("historical", history)
        self.assertIn("not current validation evidence", history)
        self.assertIn("do not infer current runtime behavior", history)

    def test_superpowers_index_separates_specs_plans_and_execution_status(self):
        index = (ROOT / "docs" / "superpowers" / "README.md").read_text(encoding="utf-8")
        self.assertIn("specs/", index)
        self.assertIn("plans/", index)
        self.assertIn("2026-09-15-v0.2.0-plan2-execution-status.md", index)
        self.assertIn("2026-09-15-v0.2.0-governor-context-memory-routing.md", index)

    def test_human_vault_public_paths_are_preserved(self):
        self.assertTrue((ROOT / "00 - J.A.R.V.I.S. Cognitive Vault.md").is_file())
        self.assertTrue((ROOT / ".obsidian").is_dir())
        self.assertTrue((ROOT / "06 - GitHub Starred Repositories.md").is_file())


if __name__ == "__main__":
    unittest.main()
