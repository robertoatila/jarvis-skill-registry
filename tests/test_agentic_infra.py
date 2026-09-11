"""
test_agentic_infra.py // Unit and Integration Tests for Phase 15 (Infrastructure Skills)
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
"""

import unittest
from pathlib import Path
from tooling.agentic.infrastructure import InfrastructureSkillDriver, REGISTRY_ROOT


class TestInfrastructureSkills(unittest.TestCase):

    def setUp(self):
        self.driver = InfrastructureSkillDriver()

    def test_safe_command_execution(self):
        res = self.driver.run_command("python -c \"print('JARVIS_INFRA_OK')\"")
        self.assertEqual(res.status, "SUCCESS")
        self.assertEqual(res.exit_code, 0)
        self.assertIn("JARVIS_INFRA_OK", res.stdout_snippet)
        self.assertGreater(res.duration_ms, 0)

    def test_disallowed_command_blocklist(self):
        # 1. Force push
        r1 = self.driver.run_command("git push origin main --force")
        self.assertEqual(r1.status, "BLOCKED_DISALLOWED")
        self.assertEqual(r1.exit_code, 126)
        self.assertIn("prohibited", r1.stderr_snippet)

        # 2. Dangerous rm
        r2 = self.driver.run_command("rm -rf /")
        self.assertEqual(r2.status, "BLOCKED_DISALLOWED")

    def test_timeout_enforcement(self):
        res = self.driver.run_command(
            "python -c \"import time; time.sleep(1.0)\"",
            timeout_seconds=0.1
        )
        self.assertEqual(res.status, "TIMEOUT")
        self.assertEqual(res.exit_code, 124)
        self.assertIn("timeout threshold", res.stderr_snippet)

    def test_git_inspection_read_only(self):
        info = self.driver.inspect_git_status(REGISTRY_ROOT)
        self.assertEqual(info["branch"], "main")
        self.assertEqual(len(info["head_commit"]), 40)

    def test_environment_health(self):
        health = self.driver.inspect_environment_health()
        self.assertIn("python_version", health)
        self.assertGreater(health["disk_free_gb"], 0.0)


if __name__ == "__main__":
    unittest.main()
