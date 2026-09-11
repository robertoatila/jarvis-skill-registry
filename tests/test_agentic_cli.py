"""
test_agentic_cli.py // J.A.R.V.I.S. Sovereign CLI Test Suite
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
Validates CLI operations: status, plan, execute, lock, test
"""

import io
import sys
import unittest
import shutil
import tempfile
import json
from pathlib import Path
from unittest.mock import patch

from tooling.agentic.config import JarvisRuntimeConfig
from tooling.agentic.cli import cmd_status, cmd_plan, cmd_execute, cmd_lock, cmd_test
import argparse


class TestAgenticCLI(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="jarvis_cli_test_")
        self.root = Path(self.temp_dir)
        self.config = JarvisRuntimeConfig(
            registry_root=self.root,
            security_mode="FAIL_CLOSED"
        )
        self.config.ensure_directories()

        # Add a dummy skill
        skill_dir = self.config.skills_dir / "systematic-code-debugging"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: systematic-code-debugging\ndescription: Debugging skill\ncapabilities: [debugging]\n---\n",
            encoding="utf-8"
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_cli_status(self):
        """Invariant: status command runs and returns exit code 0."""
        args = argparse.Namespace(command="status")
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            code = cmd_status(args, self.config)
        self.assertEqual(code, 0)
        output = captured.getvalue()
        self.assertIn("Runtime Status", output)
        self.assertIn("FAIL_CLOSED", output)

    def test_02_cli_plan(self):
        """Invariant: plan command outputs DAG and capability classifications."""
        args = argparse.Namespace(
            command="plan",
            goal="Test audit goal",
            capabilities=["systematic-code-debugging"]
        )
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            code = cmd_plan(args, self.config)
        self.assertEqual(code, 0)
        output = captured.getvalue()
        self.assertIn("MISSION PLAN", output)
        self.assertIn("Wave 0", output)

    def test_03_cli_execute(self):
        """Invariant: execute command executes complete 9-stage lifecycle."""
        args = argparse.Namespace(
            command="execute",
            goal="Execute audit goal",
            capabilities=["systematic-code-debugging"]
        )
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            code = cmd_execute(args, self.config)
        self.assertEqual(code, 0)
        output = captured.getvalue()
        self.assertIn("MISSION CERTIFIED", output)
        self.assertIn("Tasks Verified     : 1 / 1", output)

    def test_04_cli_lock(self):
        """Invariant: lock command generates verifiable lockfile."""
        lock_out = self.config.state_dir / "test-lock.json"
        args = argparse.Namespace(
            command="lock",
            capabilities=["systematic-code-debugging"],
            output=str(lock_out)
        )
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            code = cmd_lock(args, self.config)
        self.assertEqual(code, 0)
        self.assertTrue(lock_out.exists())
        data = json.loads(lock_out.read_text(encoding="utf-8"))
        self.assertIn("integrity", data)
        self.assertIn("merkle_root", data["integrity"])


if __name__ == "__main__":
    unittest.main()
