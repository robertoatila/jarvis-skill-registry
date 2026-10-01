import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tooling import jarvis_server


class MemoryPrivacyProjectionTests(unittest.TestCase):
    def test_private_memory_stays_local_when_projecting_to_obsidian(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            state_dir = root / "state"
            state_dir.mkdir()
            local_memory = state_dir / "jarvis_memory.local.json"
            legacy_memory = state_dir / "jarvis_memory.json"
            note = root / "19 - Memoria Persistente e Conhecimento Episodico.md"
            private_fact = "PRIVATE_SENTINEL_ONLY_FOR_TEST"
            legacy_memory.write_text(json.dumps({
                "version": "1.0.0",
                "profile": {"user_name": private_fact, "primary_stack": "private-stack"},
                "memories": [{"id": "local-1", "category": "fact", "fact": private_fact}],
            }), encoding="utf-8")

            with patch.multiple(
                jarvis_server,
                STATE_DIR=state_dir,
                MEMORY_PATH=local_memory,
                LEGACY_MEMORY_PATH=legacy_memory,
                OBSIDIAN_MEMORY_PATH=note,
            ):
                memory = jarvis_server.PersistentMemoryEngine()
                self.assertEqual(memory.data["profile"]["user_name"], private_fact)
                self.assertTrue(memory.add_memory(private_fact + "-new", source="explicit-test"))

            projected = note.read_text(encoding="utf-8")
            self.assertTrue(local_memory.exists())
            self.assertIn(private_fact, local_memory.read_text(encoding="utf-8"))
            self.assertNotIn(private_fact, projected)
            self.assertNotIn("private-stack", projected)
            self.assertEqual(memory.obsidian_projection["privacy_mode"], "PRIVATE_RECORDS_OMITTED")


if __name__ == "__main__":
    unittest.main()
