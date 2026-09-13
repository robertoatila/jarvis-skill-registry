"""Tests for the zero-dependency public launcher."""

import io
import unittest

import jarvis


class TestJarvisPublicLauncher(unittest.TestCase):
    def test_doctor_passes_for_repository_checkout(self):
        output = io.StringIO()
        self.assertEqual(jarvis.doctor(output), 0)
        text = output.getvalue()
        self.assertIn("Doctor passed", text)
        self.assertIn("tooling/jarvis_server.py", text)

    def test_server_command_uses_current_interpreter_and_requested_port(self):
        command = jarvis.build_server_command(8899)
        self.assertEqual(command[0], jarvis.sys.executable)
        self.assertEqual(command[1], str(jarvis.SERVER))
        self.assertEqual(command[-2:], ["--port", "8899"])

    def test_invalid_port_fails_without_starting_server(self):
        self.assertEqual(jarvis.main(["--port", "0", "--no-browser"]), 2)
        self.assertEqual(jarvis.main(["--port", "65536", "--no-browser"]), 2)

    def test_help_parser_exposes_public_validation_modes(self):
        parser = jarvis.build_parser()
        help_text = parser.format_help()
        self.assertIn("--doctor", help_text)
        self.assertIn("--test", help_text)
        self.assertIn("--full-test", help_text)


if __name__ == "__main__":
    unittest.main()
