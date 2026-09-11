"""
test_agentic_disclosure.py // Unit tests for Progressive Disclosure v2 Engine
"""

import unittest
from pathlib import Path
from tooling.agentic.progressive_disclosure import (
    ProgressiveDisclosureEngine,
    SkillCatalogEntry,
    SkillManifestEntry,
    SkillExecutionPackage
)


class TestProgressiveDisclosure(unittest.TestCase):

    def setUp(self):
        self.engine = ProgressiveDisclosureEngine()

    def test_01_catalog_level_0_loading(self):
        catalog = self.engine.load_catalog()
        self.assertGreater(len(catalog), 10, "Catalog should discover skills in registry")
        
        # Verify an entry has level 0 structure
        sample_key = next(iter(catalog))
        entry = catalog[sample_key]
        self.assertIsInstance(entry, SkillCatalogEntry)
        self.assertEqual(entry.disclosure_level, 0)
        self.assertTrue(entry.id)
        self.assertTrue(entry.name)
        # Verify token economy of L0 entry
        self.assertLess(entry.estimated_tokens, 150, "Level 0 catalog entry should be ultra-compact")

    def test_02_manifest_level_1_on_demand(self):
        catalog = self.engine.load_catalog()
        sample_id = next(iter(catalog))
        
        # Initially manifest should not be in cache
        self.assertNotIn(sample_id, self.engine._manifest_cache)
        
        # Disclose manifest
        manifest = self.engine.disclose_manifest(sample_id)
        self.assertIsInstance(manifest, SkillManifestEntry)
        self.assertEqual(manifest.disclosure_level, 1)
        self.assertIn("fail-closed", manifest.policies)
        self.assertIn(sample_id, self.engine._manifest_cache)
        self.assertGreaterEqual(manifest.estimated_tokens, manifest.catalog.estimated_tokens)

    def test_03_execution_level_2_lazy_loading(self):
        catalog = self.engine.load_catalog()
        sample_id = next(iter(catalog))
        
        # Initially execution package should not be in cache
        self.assertNotIn(sample_id, self.engine._execution_cache)
        
        # Disclose execution package
        pkg = self.engine.disclose_execution(sample_id)
        self.assertIsInstance(pkg, SkillExecutionPackage)
        self.assertEqual(pkg.disclosure_level, 2)
        self.assertIn(sample_id, self.engine._execution_cache)
        
        # Dict representation check
        d = pkg.to_dict()
        self.assertEqual(d["disclosure_level"], 2)
        self.assertIn("execution", d)
        self.assertIn("instructions", d["execution"])

    def test_04_token_economy_audit(self):
        metrics = self.engine.audit_token_economy(sample_size=15)
        self.assertGreater(metrics["skills_sampled"], 0)
        self.assertGreater(metrics["level_2_execution_tokens"], metrics["level_0_catalog_tokens"])
        self.assertGreater(metrics["token_savings_percent"], 50.0, "Progressive disclosure should yield massive token savings")


if __name__ == "__main__":
    unittest.main()
