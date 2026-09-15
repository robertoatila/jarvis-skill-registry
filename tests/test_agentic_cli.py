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

<<<<<<< HEAD
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
        self.assertEqual(code, 1)
        output = captured.getvalue()
        self.assertNotIn("MISSION CERTIFIED", output)
        self.assertIn("Tasks Verified     : 0 / 1", output)

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

    def test_05_cli_osint(self):
        """Invariant: osint command runs and produces structured dossier."""
        from tooling.agentic.cli import cmd_osint
        args = argparse.Namespace(command="osint", handle="torvalds")
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            code = cmd_osint(args, self.config)
        self.assertEqual(code, 0)
        output = captured.getvalue()
        self.assertIn("Dossiê de Inteligência OSINT", output)

    def test_06_cli_niche(self):
        """Invariant: niche command dispatches arbitrary query correctly."""
        from tooling.agentic.cli import cmd_niche
        args = argparse.Namespace(command="niche", query="@antoniaci/blackbird")
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            code = cmd_niche(args, self.config)
        self.assertEqual(code, 0)
        output = captured.getvalue()
        self.assertIn("REPO_INTEL", output)
        self.assertIn("Inteligência de Repositório", output)
=======
    def test_help_parser_exposes_public_validation_modes(self):
        parser = jarvis.build_parser()
        help_text = parser.format_help()
        self.assertIn("--doctor", help_text)
        self.assertIn("--test", help_text)
        self.assertIn("--full-test", help_text)
>>>>>>> 8f65117c4561b012121269e1afabe49cfe04c3a4


if __name__ == "__main__":
    unittest.main()
