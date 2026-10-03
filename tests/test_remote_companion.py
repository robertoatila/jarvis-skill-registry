#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for J.A.R.V.I.S. Remote Mobile Companion Access & QR Code Generator."""

import unittest
import tempfile
from unittest.mock import patch
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from tooling.qr_terminal import QRCode, generate_qr_terminal, generate_qr_ascii, generate_qr_svg
from tooling.remote_auth import RemoteAuthManager, companion_url_for_mode, detect_local_ip
from tooling.http_security import validate_local_request, validate_authorized_request, LocalRequestGuard


class TestRemoteCompanion(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.token_file = Path(self.tmp.name) / "test_token.json"
        self.auth = RemoteAuthManager(token_file=self.token_file)

    def tearDown(self):
        self.tmp.cleanup()

    def test_qr_generation(self):
        url = "http://192.168.1.100:8899/#token=0123456789abcdef"
        qr = QRCode(url)
        self.assertGreater(qr.size, 20)

        terminal_out = generate_qr_terminal(url)
        self.assertIn("█", terminal_out)

        ascii_out = generate_qr_ascii(url)
        self.assertIn("##", ascii_out)

        svg_out = generate_qr_svg(url)
        self.assertTrue(svg_out.startswith("<svg"))
        self.assertTrue(svg_out.endswith("</svg>"))

    def test_remote_auth_manager(self):
        token = self.auth.active_token
        self.assertIsNotNone(token)
        self.assertEqual(len(token), 64)
        self.assertRegex(token, r"^[0-9a-f]{64}$")
        self.assertTrue(self.token_file.exists())
        self.assertEqual(list(self.token_file.parent.glob("remote_auth_token.*.tmp")), [])

        # Validates correctly
        self.assertTrue(self.auth.validate_token(token))
        self.assertFalse(self.auth.validate_token("wrong_token"))
        self.assertFalse(self.auth.validate_token(None))
        self.assertFalse(self.auth.validate_token(""))

        # URL contains IP and token only in the client-side fragment.
        url = self.auth.get_companion_url(host_ip="192.168.1.50", port=8899)
        self.assertIn("192.168.1.50:8899", url)
        self.assertIn("#token=", url)
        self.assertNotIn("?token=", url)
        self.assertIn(token, url)

    def test_remote_auth_persistence_does_not_follow_symlink(self):
        target = Path(self.tmp.name) / "target.txt"
        target.write_text("do-not-overwrite", encoding="utf-8")
        link = Path(self.tmp.name) / "linked-token.json"
        try:
            link.symlink_to(target)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")

        with patch("sys.stderr"):
            manager = RemoteAuthManager(token_file=link)

        self.assertEqual(target.read_text(encoding="utf-8"), "do-not-overwrite")
        self.assertEqual(len(manager.active_token), 64)
        self.assertTrue(link.is_symlink())

    def test_query_string_token_is_not_accepted_by_local_request_guard(self):
        class _RemoteAuth:
            active_token = self.auth.active_token

        class _Transport:
            trusted_source_networks = ("192.168.1.0/24",)

        class _Server:
            server_port = 8899
            remote_auth = _RemoteAuth()
            remote_transport = _Transport()

        class _Headers(dict):
            def get(self, key, default=None):
                return super().get(key, default)

        class _Request(LocalRequestGuard):
            client_address = ("192.168.1.55", 12345)
            path = f"/?token={self.auth.active_token}"
            headers = _Headers({
                "Host": "192.168.1.50:8899",
                "Origin": "",
                "Sec-Fetch-Site": "same-origin",
            })
            server = _Server()

            def __init__(self):
                self.error = None

            def send_error(self, status, message):
                self.error = (status, message)

        request = _Request()
        self.assertFalse(request.guard_local_request())
        self.assertEqual(request.error[0], 403)

    def test_frontend_bootstrap_uses_fragment_and_session_storage_only(self):
        source = (Path(__file__).resolve().parents[1] / "ui" / "jarvis.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("window.location.hash", source)
        self.assertIn("sessionStorage.setItem('jarvis_token'", source)
        self.assertNotIn("localStorage.setItem('jarvis_token'", source)
        self.assertNotIn("urlParams.get('token')", source)
        self.assertIn("/api/remote/v1/pairing/offers", source)
        self.assertIn("data.pairing_url || data.url", source)
        self.assertNotIn("fetch('/api/remote/qr')", source)

    def test_authorized_request_guard(self):
        expected_token = self.auth.active_token

        # Loopback is always allowed
        self.assertTrue(validate_authorized_request(
            "127.0.0.1", "localhost:8899", "", 8899
        ))

        # Private LAN with valid token is allowed
        self.assertTrue(validate_authorized_request(
            "192.168.1.55", "192.168.1.50:8899", "", 8899,
            token=expected_token, expected_token=expected_token
        ))

        # Private LAN with invalid token is rejected
        self.assertFalse(validate_authorized_request(
            "192.168.1.55", "192.168.1.50:8899", "", 8899,
            token="invalid_token", expected_token=expected_token
        ))

        # Private LAN without token is rejected
        self.assertFalse(validate_authorized_request(
            "192.168.1.55", "192.168.1.50:8899", "", 8899,
            token="", expected_token=expected_token
        ))

        # Public non-private IP is rejected even with token (fail-closed security)
        self.assertFalse(validate_authorized_request(
            "8.8.8.8", "my-public-ip:8899", "", 8899,
            token=expected_token, expected_token=expected_token
        ))

    def test_ip_detection(self):
        ip = detect_local_ip()
        self.assertIsInstance(ip, str)
        self.assertGreater(len(ip), 6)

    def test_local_mode_skips_lan_discovery(self):
        with patch(
            "tooling.remote_auth.detect_local_ip",
            side_effect=AssertionError("local startup must not discover LAN interfaces"),
        ):
            url = companion_url_for_mode(
                remote=False,
                port=8899,
                auth_manager=self.auth,
            )
        self.assertIsNone(url)

    def test_remote_mode_still_discovers_lan_address(self):
        with patch("tooling.remote_auth.detect_local_ip", return_value="192.168.1.50") as probe:
            url = companion_url_for_mode(
                remote=True,
                port=8899,
                auth_manager=self.auth,
            )
        probe.assert_called_once_with()
        self.assertIn("192.168.1.50:8899", url)
        self.assertIn("#token=", url)
        self.assertNotIn("?token=", url)
        self.assertIn(self.auth.active_token, url)


if __name__ == "__main__":
    unittest.main()
