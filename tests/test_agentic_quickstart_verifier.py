#!/usr/bin/env python3
"""Portable quickstart verifier contracts."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

from tooling.quickstart_verifier import (
    build_quickstart_commands,
    environment_record,
)


ROOT = Path(__file__).resolve().parents[1]


class QuickstartVerifierTests(unittest.TestCase):
    def test_commands_match_public_quickstart_without_provider_credentials(self):
        commands = build_quickstart_commands(43123)

        self.assertEqual(
            commands["doctor"],
            [sys.executable, str(ROOT / "jarvis.py"), "--doctor"],
        )
        self.assertEqual(
            commands["test"],
            [sys.executable, str(ROOT / "jarvis.py"), "--test"],
        )
        self.assertEqual(
            commands["launch"],
            [
                sys.executable,
                str(ROOT / "jarvis.py"),
                "--no-browser",
                "--port",
                "43123",
            ],
        )
        serialized = repr(commands).lower()
        self.assertNotIn("api_key", serialized)
        self.assertNotIn("token", serialized)
        self.assertNotIn("credential", serialized)

    def test_environment_record_exposes_platform_and_python_not_secrets(self):
        record = environment_record(commit_sha="exact-sha")

        self.assertEqual(record["commit_sha"], "exact-sha")
        self.assertTrue(record["os"])
        self.assertTrue(record["os_release"])
        self.assertTrue(record["python_version"])
        self.assertEqual(record["python_executable"], sys.executable)
        self.assertNotIn("environment", record)
        self.assertNotIn("api_keys", record)
        self.assertNotIn("token", record)


if __name__ == "__main__":
    unittest.main()
