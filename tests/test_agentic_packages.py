"""
test_agentic_packages.py // Unit tests for Cognitive Package Manager & Lockfiles (Phase 24)
"""

import os
import json
import unittest
import tempfile
from pathlib import Path

from tooling.agentic.package_manager import CognitivePackageManager


class TestCognitivePackageManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.work_dir = Path(self.temp_dir.name)
        self.pm = CognitivePackageManager()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_01_generate_and_verify_lockfile(self):
        lock_path = self.work_dir / ".skill-registry.lock"
        capabilities = ["systematic-code-debugging", "comprehensive-code-review"]

        lock_data = self.pm.generate_lockfile(
            workspace_root=self.work_dir,
            capabilities=capabilities,
            lockfile_path=lock_path
        )

        self.assertTrue(lock_path.exists())
        self.assertTrue(lock_data["lock_id"].startswith("slock-"))
        self.assertEqual(len(lock_data["skills"]), 2)
        self.assertTrue(lock_data["integrity"]["merkle_root"])

        # Verify lockfile
        valid, errors = self.pm.verify_lockfile(lock_path)
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)

    def test_02_detect_tampered_lockfile_fail_closed(self):
        lock_path = self.work_dir / ".skill-registry.lock"
        capabilities = ["systematic-code-debugging"]

        self.pm.generate_lockfile(
            workspace_root=self.work_dir,
            capabilities=capabilities,
            lockfile_path=lock_path
        )

        # Tamper with content hash
        tampered_data = json.loads(lock_path.read_text(encoding="utf-8"))
        tampered_data["skills"][0]["canonical_content_hash"] = "0" * 64
        lock_path.write_text(json.dumps(tampered_data), encoding="utf-8")

        # Verification must fail
        valid, errors = self.pm.verify_lockfile(lock_path)
        self.assertFalse(valid)
        self.assertGreater(len(errors), 0)
        self.assertIn("Merkle root mismatch", errors[0])

        # Installation must fail closed
        target_install = self.work_dir / "install_dest"
        with self.assertRaises(ValueError):
            self.pm.install_from_lockfile(lock_path, target_dir=target_install)

    def test_03_install_from_valid_lockfile(self):
        lock_path = self.work_dir / ".skill-registry.lock"
        capabilities = ["systematic-code-debugging"]

        self.pm.generate_lockfile(
            workspace_root=self.work_dir,
            capabilities=capabilities,
            lockfile_path=lock_path
        )

        target_install = self.work_dir / "installed"
        install_res = self.pm.install_from_lockfile(lock_path, target_dir=target_install)

        self.assertEqual(install_res["status"], "INSTALLED")
        self.assertEqual(install_res["installed_count"], 1)
        self.assertTrue((target_install / "systematic-code-debugging" / "installed.lock").exists())


if __name__ == "__main__":
    unittest.main()
