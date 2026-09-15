#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for J.A.R.V.I.S. Remote Mobile Companion Access & QR Code Generator."""

import unittest
import tempfile
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from tooling.qr_terminal import QRCode, generate_qr_terminal, generate_qr_ascii, generate_qr_svg
from tooling.remote_auth import RemoteAuthManager, detect_local_ip
from tooling.http_security import validate_local_request, validate_authorized_request, LocalRequestGuard


class TestRemoteCompanion(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.token_file = Path(self.tmp.name) / "test_token.json"
        self.auth = RemoteAuthManager(token_file=self.token_file)

    def tearDown(self):
        self.tmp.cleanup()

    def test_qr_generation(self):
        url = "http://192.168.1.100:8899/?token=0123456789abcdef"
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
        self.assertGreaterEqual(len(token), 16)
        self.assertTrue(self.token_file.exists())

        # Validates correctly
        self.assertTrue(self.auth.validate_token(token))
        self.assertFalse(self.auth.validate_token("wrong_token"))
        self.assertFalse(self.auth.validate_token(None))
        self.assertFalse(self.auth.validate_token(""))

        # URL contains IP and token
        url = self.auth.get_companion_url(host_ip="192.168.1.50", port=8899)
        self.assertIn("192.168.1.50:8899", url)
        self.assertIn(token, url)

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


if __name__ == "__main__":
    unittest.main()
