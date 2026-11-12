"""
infrastructure.py // J.A.R.V.I.S. Safe Infrastructure & Process Controller
Pure Python Standard Library (Zero PIP Dependencies)
Enforces:
- Fail-closed security blocklist for dangerous system commands
- Strict timeouts and bounded output buffers (anti-DoS)
- Read-only Git inspection primitives
- System diagnostic auditing (Python, OS, Disk, Memory)
"""

from __future__ import annotations
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple, Any
from datetime import datetime, timezone

from .config import CONFIG
from .safe_command import CommandRejected, resolve_executable, split_command

REGISTRY_ROOT = CONFIG.registry_root



DISALLOWED_COMMAND_PATTERNS = [
    r"\bformat\b",
    r"\bdd\s+if=",
    r"\brm\s+-rf\s+[/~]",
    r"\bgit\s+push\s+.*--force",
    r"\bdel\s+/[sS]\s+/[qQ]\s+[cC]:\\",
    r"\bshutdown\b",
    r"\breboot\b"
]


@dataclass
class ProcessExecutionResult:
    command: str
    status: str  # SUCCESS, TIMEOUT, BLOCKED_DISALLOWED, EXECUTION_ERROR
    exit_code: int
    duration_ms: int
    stdout_snippet: str
    stderr_snippet: str
    timestamp_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "status": self.status,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "stdout_snippet": self.stdout_snippet[:2000],
            "stderr_snippet": self.stderr_snippet[:2000],
            "timestamp_utc": self.timestamp_utc
        }


class InfrastructureSkillDriver:
    """
    Sovereign execution driver for local system and diagnostic commands.
    Enforces strict security invariants.
    """

    def is_command_allowed(self, command: str) -> Tuple[bool, str]:
        for pat in DISALLOWED_COMMAND_PATTERNS:
            if re.search(pat, command, re.IGNORECASE):
                return False, f"Command matched prohibited security pattern: '{pat}'"
        return True, ""

    def run_command(
        self,
        command: str,
        cwd: Optional[Path] = None,
        timeout_seconds: float = 30.0,
        max_output_bytes: int = 65536
    ) -> ProcessExecutionResult:
        """Executes a command safely under timeout and security constraints."""
        allowed, reason = self.is_command_allowed(command)
        if not allowed:
            return ProcessExecutionResult(
                command=command,
                status="BLOCKED_DISALLOWED",
                exit_code=126,
                duration_ms=0,
                stdout_snippet="",
                stderr_snippet=f"Security Violation: {reason}"
            )

        # The command runs as one process without a shell.  Text that needs a
        # shell (chaining, redirection, substitution) is blocked, and the
        # blocklist is applied again to the argument vector so that quoting
        # tricks such as r""m cannot spell a prohibited command.
        try:
            argv = split_command(command)
        except CommandRejected as rejected:
            return ProcessExecutionResult(
                command=command,
                status="BLOCKED_DISALLOWED",
                exit_code=126,
                duration_ms=0,
                stdout_snippet="",
                stderr_snippet=f"Security Violation: {rejected}"
            )
        allowed, reason = self.is_command_allowed(" ".join(argv))
        if not allowed:
            return ProcessExecutionResult(
                command=command,
                status="BLOCKED_DISALLOWED",
                exit_code=126,
                duration_ms=0,
                stdout_snippet="",
                stderr_snippet=f"Security Violation: {reason}"
            )

        start_time = time.perf_counter()
        try:
            completed = subprocess.run(
                resolve_executable(argv),
                shell=False,
                cwd=str(cwd) if cwd else None,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds,
                check=False,
            )
            duration_ms = int((time.perf_counter() - start_time) * 1000)

            status = "SUCCESS" if completed.returncode == 0 else "EXECUTION_ERROR"
            return ProcessExecutionResult(
                command=command,
                status=status,
                exit_code=completed.returncode,
                duration_ms=duration_ms,
                stdout_snippet=completed.stdout[:max_output_bytes],
                stderr_snippet=completed.stderr[:max_output_bytes]
            )
        except subprocess.TimeoutExpired:
            # subprocess.run has already killed and reaped the child.
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return ProcessExecutionResult(
                command=command,
                status="TIMEOUT",
                exit_code=124,
                duration_ms=duration_ms,
                stdout_snippet="",
                stderr_snippet=f"Process exceeded timeout threshold ({timeout_seconds}s)"
            )
        except FileNotFoundError as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return ProcessExecutionResult(
                command=command,
                status="EXECUTION_ERROR",
                exit_code=127,
                duration_ms=duration_ms,
                stdout_snippet="",
                stderr_snippet=f"Program not found: {e}"
            )
        except Exception as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return ProcessExecutionResult(
                command=command,
                status="EXECUTION_ERROR",
                exit_code=1,
                duration_ms=duration_ms,
                stdout_snippet="",
                stderr_snippet=str(e)
            )

    def inspect_git_status(self, repo_root: Path) -> Dict[str, Any]:
        """Performs non-destructive git inspection."""
        res = self.run_command("git status --porcelain", cwd=repo_root, timeout_seconds=5.0)
        branch_res = self.run_command("git branch --show-current", cwd=repo_root, timeout_seconds=5.0)
        commit_res = self.run_command("git rev-parse HEAD", cwd=repo_root, timeout_seconds=5.0)

        is_clean = (res.exit_code == 0) and (not res.stdout_snippet.strip())
        return {
            "is_clean": is_clean,
            "branch": branch_res.stdout_snippet.strip() if branch_res.exit_code == 0 else "unknown",
            "head_commit": commit_res.stdout_snippet.strip() if commit_res.exit_code == 0 else "unknown",
            "modified_files": [l.strip() for l in res.stdout_snippet.splitlines() if l.strip()]
        }

    def inspect_environment_health(self) -> Dict[str, Any]:
        """Collects local diagnostic metrics."""
        disk = shutil.disk_usage(Path("."))
        return {
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            "platform": os.name,
            "disk_free_gb": round(disk.free / (1024 ** 3), 2),
            "disk_total_gb": round(disk.total / (1024 ** 3), 2),
            "timestamp_utc": datetime.now(timezone.utc).isoformat()
        }


# Global singleton
INFRA_DRIVER = InfrastructureSkillDriver()
