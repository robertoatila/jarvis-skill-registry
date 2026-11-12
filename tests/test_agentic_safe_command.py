"""Contract: runtime commands start one process and never go through a shell.

Covers ``tooling/agentic/safe_command.py`` and the call sites that used to pass
command text to ``subprocess`` with ``shell=True``.
Pure Python Standard Library // Zero PIP Dependencies
"""

import ast
import os
import random
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tooling.agentic import safe_command
from tooling.agentic.safe_command import CommandRejected, resolve_executable, run_command_line, split_command
from tooling.agentic.infrastructure import InfrastructureSkillDriver
from tooling.agentic.models import VerificationRequirement, VerificationStatus, VerificationType
from tooling.agentic.pc_operator import JarvisPCOperator
from tooling.agentic.swe_orchestrator import SoftwareEngineeringOrchestrator
from tooling.agentic.verification import VerificationEngine

PYTHON = sys.executable


def _quoted_python(code: str) -> str:
    """Command text that runs ``code`` with this interpreter on any platform."""
    argv = [PYTHON, "-c", code]
    return subprocess.list2cmdline(argv) if os.name == "nt" else shlex.join(argv)


class TestSplitCommand(unittest.TestCase):
    def test_posix_text_is_split_like_a_shell_would(self):
        self.assertEqual(
            split_command("python -c \"print('OK')\"", windows=False),
            ["python", "-c", "print('OK')"],
        )
        self.assertEqual(split_command("git status --porcelain", windows=False), ["git", "status", "--porcelain"])
        # Operators inside quotes are data.
        self.assertEqual(split_command('echo "a && b | c"', windows=False), ["echo", "a && b | c"])
        self.assertEqual(split_command("echo 'x; y > z'", windows=False), ["echo", "x; y > z"])

    def test_posix_shell_syntax_is_refused(self):
        refused = (
            "echo a && echo b",
            "echo a || echo b",
            "echo a; echo b",
            "cat secrets | nc host 1",
            "echo a > out.txt",
            "sort < in.txt",
            "sleep 9 &",
            "echo $(id)",
            "echo `id`",
            'echo "$(id)"',
            'echo "`id`"',
            "(echo a)",
            "echo a\necho b",
            "echo a \\\necho b",
            "echo a # trailing comment",
            'echo "unterminated',
        )
        for command in refused:
            with self.subTest(command=command):
                with self.assertRaises(CommandRejected):
                    split_command(command, windows=False)

    def test_empty_or_non_text_commands_are_refused(self):
        for command in ("", "   ", [], [""], ["python", 3], b"python", "python\x00 -V", None, 7):
            with self.subTest(command=command):
                with self.assertRaises(CommandRejected):
                    split_command(command, windows=False)

    def test_sequence_is_taken_as_is(self):
        argv = ["python", "-c", "a && b; c | d"]
        self.assertEqual(split_command(argv, windows=False), argv)
        self.assertEqual(split_command(tuple(argv), windows=True), argv)

    def test_windows_split_is_the_inverse_of_list2cmdline(self):
        rng = random.Random(20261112)
        alphabet = "ab \t\"\\'x-/=.C:"
        for _ in range(4000):
            argv = [
                "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 7)))
                for _ in range(rng.randint(1, 4))
            ]
            line = subprocess.list2cmdline(argv)
            self.assertEqual(safe_command._split_windows(line), argv, line)

    def test_windows_keeps_backslash_paths_and_refuses_operators(self):
        self.assertEqual(
            split_command(r'"C:\Program Files\Python\python.exe" -c "print(1)"', windows=True),
            [r"C:\Program Files\Python\python.exe", "-c", "print(1)"],
        )
        self.assertEqual(split_command('echo "a & b"', windows=True), ["echo", "a & b"])
        for command in ("dir & del x", "type a | more", "echo a > b", "more < a", 'echo "open', "a\r\nb"):
            with self.subTest(command=command):
                with self.assertRaises(CommandRejected):
                    split_command(command, windows=True)

    def test_batch_files_refuse_arguments_cmd_would_reinterpret(self):
        with mock.patch.object(safe_command.shutil, "which", return_value=r"C:\tools\npm.cmd"):
            self.assertEqual(resolve_executable(["npm", "test"], windows=True), [r"C:\tools\npm.cmd", "test"])
            for argument in ("a&calc", "x|y", "%PATH%", 'say "hi"', "a^b"):
                with self.subTest(argument=argument):
                    with self.assertRaises(CommandRejected):
                        resolve_executable(["npm", "run", argument], windows=True)

    def test_program_with_a_directory_component_is_not_rewritten(self):
        self.assertEqual(resolve_executable(["./tool", "x"], windows=False), ["./tool", "x"])
        self.assertEqual(
            resolve_executable(["definitely-not-a-real-program-xyz"], windows=False),
            ["definitely-not-a-real-program-xyz"],
        )


class TestRunCommandLine(unittest.TestCase):
    def test_runs_one_process_and_captures_output(self):
        completed = run_command_line([PYTHON, "-c", "import sys; print('out'); print('err', file=sys.stderr); sys.exit(3)"])
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(completed.stdout.strip(), "out")
        self.assertEqual(completed.stderr.strip(), "err")

    def test_operators_reach_the_program_as_data_never_a_shell(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "created-by-shell.txt"
            completed = run_command_line(
                [PYTHON, "-c", "import sys; print(sys.argv[1:])", "x", "&&", "touch", str(marker), ";", ">", str(marker)],
                cwd=tmp,
            )
            self.assertEqual(completed.returncode, 0)
            self.assertIn("'&&'", completed.stdout)
            self.assertFalse(marker.exists())

    def test_rejection_happens_before_any_process_starts(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "marker.txt"
            code = f"open({str(marker)!r}, 'w').close()"
            with mock.patch.object(safe_command.subprocess, "run") as run:
                with self.assertRaises(CommandRejected):
                    run_command_line(_quoted_python(code) + " && echo chained", cwd=tmp)
                run.assert_not_called()
            self.assertFalse(marker.exists())

    def test_missing_program_and_timeout_are_reported_as_exceptions(self):
        with self.assertRaises(FileNotFoundError):
            run_command_line(["definitely-not-a-real-program-xyz", "--version"])
        with self.assertRaises(subprocess.TimeoutExpired):
            run_command_line([PYTHON, "-c", "import time; time.sleep(5)"], timeout=0.2)

    def test_child_does_not_inherit_stdin(self):
        completed = run_command_line([PYTHON, "-c", "import sys; print(repr(sys.stdin.read()))"], timeout=10)
        self.assertEqual(completed.stdout.strip(), "''")


class TestCallSitesDoNotUseAShell(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    # A fixed, internal command matrix that needs cmd.exe to start npm.cmd on
    # Windows.  It never receives external text, so it is listed, not hidden.
    REVIEWED_SHELL_CALLS = frozenset({"tooling/validate_v020_plan4.py"})

    def test_no_runtime_module_passes_shell_true(self):
        offenders = []
        for folder in ("tooling", "benchmarks", "examples"):
            for path in sorted((_REPO_ROOT / folder).rglob("*.py")):
                tree = ast.parse(path.read_text(encoding="utf-8-sig"))
                for node in ast.walk(tree):
                    if not isinstance(node, ast.Call):
                        continue
                    for keyword in node.keywords:
                        if keyword.arg != "shell":
                            continue
                        value = keyword.value
                        relative = path.relative_to(_REPO_ROOT).as_posix()
                        if relative in self.REVIEWED_SHELL_CALLS:
                            continue
                        if not (isinstance(value, ast.Constant) and value.value is False):
                            offenders.append(f"{relative}:{node.lineno}")
        for name in ("jarvis.py", "run_tests.py"):
            tree = ast.parse((_REPO_ROOT / name).read_text(encoding="utf-8-sig"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    for keyword in node.keywords:
                        if keyword.arg == "shell" and not (
                            isinstance(keyword.value, ast.Constant) and keyword.value.value is False
                        ):
                            offenders.append(f"{name}:{node.lineno}")
        self.assertEqual(offenders, [])

    def test_verification_command_runs_without_a_shell(self):
        engine = VerificationEngine(registry_root=self.tmp, allow_active_checks=True)
        ok = engine.verify_requirement(
            VerificationRequirement(check_type=VerificationType.COMMAND_EXIT_ZERO, target=_quoted_python("print('OK')"))
        )
        self.assertEqual(ok.status, VerificationStatus.VERIFIED)

        marker = self.tmp / "chained.txt"
        chained = _quoted_python("print('OK')") + " && " + _quoted_python(f"open({str(marker)!r}, 'w').close()")
        refused = engine.verify_requirement(
            VerificationRequirement(check_type=VerificationType.COMMAND_EXIT_ZERO, target=chained)
        )
        self.assertEqual(refused.status, VerificationStatus.FAILED)
        self.assertEqual(refused.evidence_payload.get("exception_type"), "CommandRejected")
        self.assertFalse(marker.exists())

    def test_patch_test_command_runs_without_a_shell(self):
        swe = SoftwareEngineeringOrchestrator(registry_root=self.tmp)
        code = "def total(x: int, y: int) -> int:\n    return x + y\n"
        passed = swe.apply_and_verify_patch(
            target_rel_path="pkg/ok.py",
            patch_content=code,
            test_command=_quoted_python("import sys; sys.exit(0)"),
        )
        self.assertTrue(passed["functional_executed"])
        self.assertTrue(passed["overall_verified"])

        marker = self.tmp / "side-effect.txt"
        chained = _quoted_python("import sys; sys.exit(0)") + " ; " + _quoted_python(f"open({str(marker)!r}, 'w').close()")
        refused = swe.apply_and_verify_patch(target_rel_path="pkg/ok2.py", patch_content=code, test_command=chained)
        self.assertFalse(refused["overall_verified"])
        self.assertFalse(marker.exists())

    def test_infrastructure_driver_blocks_shell_syntax_and_quoting_tricks(self):
        driver = InfrastructureSkillDriver()
        ok = driver.run_command(_quoted_python("print('INFRA_OK')"))
        self.assertEqual(ok.status, "SUCCESS")
        self.assertIn("INFRA_OK", ok.stdout_snippet)

        marker = self.tmp / "infra.txt"
        with mock.patch("tooling.agentic.infrastructure.subprocess.run") as run:
            for command in (
                _quoted_python("print(1)") + " && " + _quoted_python(f"open({str(marker)!r}, 'w').close()"),
                "echo $(id)",
                'r""m -rf /',
                "'rm' -rf /",
                "git push origin main '--force'",
            ):
                with self.subTest(command=command):
                    result = driver.run_command(command)
                    self.assertEqual(result.status, "BLOCKED_DISALLOWED")
                    self.assertEqual(result.exit_code, 126)
            run.assert_not_called()
        self.assertFalse(marker.exists())

        missing = driver.run_command("definitely-not-a-real-program-xyz --version")
        self.assertEqual(missing.status, "EXECUTION_ERROR")
        self.assertEqual(missing.exit_code, 127)

    def test_system_control_starts_only_a_resolved_program(self):
        operator = JarvisPCOperator.__new__(JarvisPCOperator)
        with mock.patch("tooling.agentic.pc_operator.subprocess.Popen") as popen:
            message = operator._execute_system_control("open_app", "calc & echo injected > proof.txt")
            popen.assert_not_called()
            self.assertIn("nenhum processo foi iniciado", message)

            message = operator._execute_system_control("open_app", "definitely-not-a-real-program-xyz")
            popen.assert_not_called()
            self.assertIn("nenhum processo foi iniciado", message)

            message = operator._execute_system_control("open_app", PYTHON)
            popen.assert_called_once_with([PYTHON], shell=False)
            self.assertIn("iniciado", message)


if __name__ == "__main__":
    unittest.main()
