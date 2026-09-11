"""
test_agentic_vault.py // Unit and Integration Tests for Phase 13 (Cognitive Vault Integration)
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
"""

import unittest
import tempfile
import json
from pathlib import Path

from tooling.agentic.vault import CognitiveVaultBridge
from tooling.agentic.learning import LearningEngine, LearningRecord, LearningTier


class TestCognitiveVault(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.mem_file = Path(self.tmp_dir.name) / "test_mem.json"
        self.note_file = Path(self.tmp_dir.name) / "test_note_19.md"
        self.heuristics_file = Path(self.tmp_dir.name) / "test_heuristics.json"

        # Mock initial memory
        initial_data = {
            "version": "1.0.0",
            "profile": {
                "user_name": "Ad",
                "primary_stack": "Java, Spring Boot, Python",
                "operational_rules": ["Soberania absoluta: zero dependências externas", "Nunca usar Tailwind sem permissão"]
            },
            "memories": [
                {"id": "mem-01", "category": "project", "fact": "Markitos ERP", "importance": "HIGH"}
            ]
        }
        self.mem_file.write_text(json.dumps(initial_data), encoding="utf-8")

        # Mock heuristics
        heuristics_data = {
            "heur-01": {
                "skill": "fastapi-pro",
                "approach": "Async pool tuning",
                "actual_result": "30ms latency",
                "confidence": 0.95
            }
        }
        self.heuristics_file.write_text(json.dumps(heuristics_data), encoding="utf-8")

        learning_eng = LearningEngine(heuristics_file=self.heuristics_file)
        self.vault = CognitiveVaultBridge(
            memory_file=self.mem_file,
            note_19_file=self.note_file,
            learning_engine=learning_eng
        )

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_load_profile_and_memories(self):
        prof = self.vault.get_user_profile()
        self.assertEqual(prof["user_name"], "Ad")
        self.assertIn("Java", prof["primary_stack"])

        mems = self.vault.get_memories()
        self.assertEqual(len(mems), 1)
        self.assertEqual(mems[0]["id"], "mem-01")

    def test_build_agent_context(self):
        ctx = self.vault.build_agent_context("backend")
        self.assertIn("User: Ad", ctx)
        self.assertIn("Soberania absoluta", ctx)
        self.assertIn("Nunca usar Tailwind", ctx)
        self.assertIn("fastapi-pro", ctx)
        self.assertIn("Async pool tuning", ctx)

    def test_sync_to_obsidian_note(self):
        synced = self.vault.sync_to_obsidian()
        self.assertTrue(synced)
        self.assertTrue(self.note_file.exists())

        content = self.note_file.read_text(encoding="utf-8")
        self.assertIn("Memória Persistente de Longo Prazo", content)
        self.assertIn("Markitos ERP", content)
        self.assertIn("Heurísticas Validadas em Runtime", content)
        self.assertIn("fastapi-pro", content)


if __name__ == "__main__":
    unittest.main()
