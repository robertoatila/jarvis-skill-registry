#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_agentic_mission_executor.py // J.A.R.V.I.S. Mission Executor Contract Tests
================================================================================
Pure Python 3.12 unittest verifying sandboxed subprocess execution,
bounded timeouts, fail-closed security invariants, and MCP gateway integration.
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tooling.jarvis_mission_executor import JarvisMissionExecutor, MissionReceipt
import tooling.jarvis_mcp_server as mcp_server


class TestAgenticMissionExecutor(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="jarvis_test_missions_")
        self.executor = JarvisMissionExecutor(base_workspace=Path(self.test_dir))

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_successful_execution_and_receipt(self):
        """Verifies clean command execution, exit code 0, and receipt persistence."""
        receipt = self.executor.execute(command=[sys.executable, "-V"], mission_id="test-succ-01")
        self.assertEqual(receipt.status, "SUCCESS")
        self.assertEqual(receipt.exit_code, 0)
        self.assertIn("Python", receipt.stdout + receipt.stderr)
        self.assertEqual(receipt.security_verdict, "PASS_INSPECTED")
        self.assertTrue(Path(receipt.workspace).exists())

    def test_02_fail_closed_security_blocklist(self):
        """Verifies destructive commands are rejected without spawning a subprocess."""
        blocked_commands = [
            "format C:",
            "rmdir /s /q C:\\",
            "diskpart",
            "del /f /s /q C:\\Windows\\System32\\test.dll"
        ]
        for cmd in blocked_commands:
            receipt = self.executor.execute(command=cmd, mission_id="test-block-01")
            self.assertEqual(receipt.status, "BLOCKED_SECURITY")
            self.assertEqual(receipt.exit_code, -1)
            self.assertEqual(receipt.security_verdict, "FAIL_CLOSED_REJECTED")
            self.assertIn("SECURITY_BLOCKED", receipt.stderr)

    def test_03_bounded_timeout_enforcement(self):
        """Verifies process exceeding timeout is terminated cleanly with status TIMEOUT."""
        sleep_cmd = [sys.executable, "-c", "import time; time.sleep(10)"]
        receipt = self.executor.execute(command=sleep_cmd, timeout_seconds=1.0, mission_id="test-timeout-01")
        self.assertEqual(receipt.status, "TIMEOUT")
        self.assertEqual(receipt.exit_code, -9)
        self.assertIn("timed out", receipt.stderr)

    def test_04_sensitive_environment_scrubbing(self):
        """Verifies API keys and credentials are stripped from child processes."""
        os.environ["GITHUB_TOKEN"] = "mock_secret_gh_token_12345"
        os.environ["GROQ_API_KEY"] = "mock_secret_groq_key_abcde"
        try:
            check_cmd = [sys.executable, "-c", "import os; print('GH:' + os.environ.get('GITHUB_TOKEN', 'CLEAN'))"]
            receipt = self.executor.execute(command=check_cmd, mission_id="test-env-01")
            self.assertEqual(receipt.status, "SUCCESS")
            self.assertIn("GH:CLEAN", receipt.stdout)
            self.assertNotIn("mock_secret_gh_token_12345", receipt.stdout)
        finally:
            os.environ.pop("GITHUB_TOKEN", None)
            os.environ.pop("GROQ_API_KEY", None)

    def test_05_mcp_gateway_integration(self):
        """Verifies MCP tool_execute_mission dispatches through executor."""
        result = mcp_server.tool_execute_mission({
            "command": f'"{sys.executable}" -V',
            "timeout_seconds": 10.0
        })
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["security_verdict"], "PASS_INSPECTED")
        self.assertIn("mission_id", result)


if __name__ == "__main__":
    unittest.main()
