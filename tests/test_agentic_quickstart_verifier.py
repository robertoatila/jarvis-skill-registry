#!/usr/bin/env python3
"""Portable quickstart verifier contracts."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from tooling.quickstart_verifier import (
    _probe_local_http,
    build_quickstart_commands,
    environment_record,
    resolve_commit_sha,
)
from tooling.jarvis_server import JarvisHttpHandler, ThreadingJarvisServer


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

    def test_commit_identity_comes_from_git_not_github_sha_environment(self):
        checkout_sha = "b" * 40
        misleading_environment_sha = "a" * 40
        completed = subprocess.CompletedProcess(
            ["git", "rev-parse", "HEAD"],
            0,
            stdout=checkout_sha + "\n",
            stderr="",
        )

        with (
            patch.dict(
                "tooling.quickstart_verifier.os.environ",
                {"GITHUB_SHA": misleading_environment_sha},
                clear=False,
            ),
            patch(
                "tooling.quickstart_verifier.subprocess.run",
                return_value=completed,
            ),
        ):
            observed = resolve_commit_sha()

        self.assertEqual(observed, checkout_sha)
        self.assertNotEqual(observed, misleading_environment_sha)

    def test_commit_identity_fails_closed_on_malformed_git_output(self):
        completed = subprocess.CompletedProcess(
            ["git", "rev-parse", "HEAD"],
            0,
            stdout="not-a-commit\n",
            stderr="",
        )
        with patch(
            "tooling.quickstart_verifier.subprocess.run",
            return_value=completed,
        ):
            self.assertEqual(resolve_commit_sha(), "UNKNOWN")

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

    def test_http_probe_is_direct_loopback_without_proxy_discovery(self):
        calls = []

        class FakeResponse:
            status = 200

            def read(self, limit):
                self.limit = limit
                return b"hud"

        class FakeConnection:
            def __init__(self, host, port, timeout):
                calls.append(("connect", host, port, timeout))

            def request(self, method, path):
                calls.append(("request", method, path))

            def getresponse(self):
                return FakeResponse()

            def close(self):
                calls.append(("close",))

        with patch("tooling.quickstart_verifier.http.client.HTTPConnection", FakeConnection):
            status, response_bytes = _probe_local_http(43123, timeout=0.75)

        self.assertEqual(status, 200)
        self.assertEqual(response_bytes, 3)
        self.assertEqual(calls[0], ("connect", "127.0.0.1", 43123, 0.75))
        self.assertEqual(calls[1], ("request", "GET", "/"))
        self.assertEqual(calls[-1], ("close",))

    def test_hud_bind_does_not_depend_on_reverse_dns(self):
        with patch("socket.getfqdn", side_effect=AssertionError("reverse DNS must not run")):
            server = ThreadingJarvisServer(("127.0.0.1", 0), JarvisHttpHandler)
        try:
            self.assertEqual(server.server_name, "127.0.0.1")
            self.assertGreater(server.server_port, 0)
        finally:
            server.server_close()


if __name__ == "__main__":
    unittest.main()
