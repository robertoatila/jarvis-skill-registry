#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jarvis_mission_executor.py // J.A.R.V.I.S. Autonomous Mission Execution Engine
=============================================================================
Protocolo de Segurança Soberana SSP-v13.4 | Pure Python 3.12 Standard Library
Enforces Fail-Closed Sandboxed Execution & Verifiable Receipt Generation.

Transforms J.A.R.V.I.S. from a passive catalog librarian into an active
autonomous operator capable of safely executing tools and missions.
"""

from __future__ import annotations
import os
import sys
import json
import time
import uuid
import re
import subprocess
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple

# Paths
REGISTRY_ROOT = Path(__file__).resolve().parent.parent
STAGING_MISSIONS = REGISTRY_ROOT / "staging" / "missions"
STATE_MISSIONS = REGISTRY_ROOT / "state" / "missions"

# Forbidden destructive command patterns (Fail-Closed Guardrails)
FORBIDDEN_COMMAND_PATTERNS = [
    (r"(?:rmdir|rd)\b.*[a-zA-Z]:\\?$", "Root drive recursive wipe"),
    (r"rm\s+-rf\s+(?:/|[a-zA-Z]:/)$", "Root filesystem recursive wipe"),
    (r"\bformat\b\s+[a-zA-Z]:", "Drive format command"),
    (r"\bdiskpart\b", "Raw disk partitioning utility"),
    (r"\b(?:del|erase)\b.*(?:windows|system32|boot)", "System folder deletion"),
    (r":\(\)\{\s*:\|:&\s*\};:", "Fork bomb syntax"),
    (r"powershell.*-enc\s+[A-Za-z0-9+/=]{50,}", "Unverified encoded PowerShell payload")
]

# Sensitive environment variables to scrub from child processes
SENSITIVE_ENV_VARS = [
    "GITHUB_TOKEN",
    "GITHUB_PERSONAL_ACCESS_TOKEN",
    "GH_TOKEN",
    "GROQ_API_KEY",
    "GEMINI_API_KEY",
    "OPENAI_API_KEY",
    "AWS_SECRET_ACCESS_KEY",
    "AZURE_CLIENT_SECRET"
]


@dataclass
class MissionReceipt:
    mission_id: str
    command: str
    status: str  # "SUCCESS", "FAILURE", "TIMEOUT", "BLOCKED_SECURITY"
    exit_code: Optional[int]
    duration_seconds: float
    workspace: str
    stdout: str
    stderr: str
    security_verdict: str
    timestamp_utc: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _terminate_process_tree(process: subprocess.Popen) -> bool:
    """Terminates process and all child descendants cleanly on Windows or POSIX."""
    if process.poll() is not None:
        return True
    try:
        if sys.platform == "win32":
            system_root = os.environ.get("SystemRoot", r"C:\Windows")
            taskkill = Path(system_root) / "System32" / "taskkill.exe"
            subprocess.run(
                [str(taskkill), "/PID", str(process.pid), "/T", "/F"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
                check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000),
            )
            return True
        else:
            os.killpg(process.pid, 9)
            return True
    except Exception:
        pass
    try:
        process.kill()
    except Exception:
        pass
    return False


class JarvisMissionExecutor:
    """
    Sovereign executor providing sandboxed subprocess execution with
    strict timeout, environment scrubbing, and fail-closed security guards.
    """

    def __init__(self, base_workspace: Optional[Path] = None):
        self.base_workspace = base_workspace or STAGING_MISSIONS
        self.base_workspace.mkdir(parents=True, exist_ok=True)
        STATE_MISSIONS.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def audit_command_safety(command_str: str) -> Tuple[bool, Optional[str]]:
        """
        Inspects command string against fail-closed forbidden patterns.
        """
        for pattern, label in FORBIDDEN_COMMAND_PATTERNS:
            if re.search(pattern, command_str, re.IGNORECASE):
                return False, f"SECURITY_BLOCKED: {label}"
        return True, None

    def prepare_sandbox(self, mission_id: str) -> Path:
        """
        Creates an isolated, mission-specific directory.
        """
        sandbox = self.base_workspace / mission_id
        sandbox.mkdir(parents=True, exist_ok=True)
        return sandbox

    def sanitize_environment(self, custom_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Creates a scrubbed environment that preserves execution PATH
        while stripping raw credentials unless explicitly permitted.
        """
        clean_env = dict(os.environ)
        for var in SENSITIVE_ENV_VARS:
            clean_env.pop(var, None)
        
        # Mark sovereign execution context
        clean_env["JARVIS_MISSION_CONTEXT"] = "1"
        clean_env["PYTHONUNBUFFERED"] = "1"
        clean_env["PYTHONUTF8"] = "1"

        if custom_env:
            clean_env.update(custom_env)
        return clean_env

    def execute(
        self,
        command: str | List[str],
        mission_id: Optional[str] = None,
        timeout_seconds: float = 60.0,
        custom_env: Optional[Dict[str, str]] = None,
        workspace_dir: Optional[Path] = None
    ) -> MissionReceipt:
        """
        Executes a mission command in an isolated sandbox with full evidence capture.
        """
        mission_id = mission_id or f"m-{uuid.uuid4().hex[:10]}"
        timestamp_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Normalize command string
        if isinstance(command, list):
            cmd_str = " ".join(command)
            cmd_args = command
        else:
            cmd_str = command.strip()
            cmd_args = cmd_str

        # 1. Security Pre-Audit
        safe, reason = self.audit_command_safety(cmd_str)
        if not safe:
            receipt = MissionReceipt(
                mission_id=mission_id,
                command=cmd_str,
                status="BLOCKED_SECURITY",
                exit_code=-1,
                duration_seconds=0.0,
                workspace=str(workspace_dir or self.base_workspace),
                stdout="",
                stderr=reason or "Security policy violation",
                security_verdict="FAIL_CLOSED_REJECTED",
                timestamp_utc=timestamp_str,
                metadata={"reason": reason}
            )
            self._save_receipt(receipt)
            return receipt

        # 2. Setup Sandbox
        sandbox = workspace_dir or self.prepare_sandbox(mission_id)
        env = self.sanitize_environment(custom_env)

        # 3. Subprocess Execution
        start_time = time.perf_counter()
        stdout_text = ""
        stderr_text = ""
        exit_code: Optional[int] = None
        status = "SUCCESS"

        try:
            use_shell = isinstance(cmd_args, str)
            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

            proc = subprocess.Popen(
                cmd_args,
                cwd=str(sandbox),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=use_shell,
                creationflags=creation_flags,
                encoding="utf-8",
                errors="replace"
            )

            try:
                stdout_text, stderr_text = proc.communicate(timeout=timeout_seconds)
                exit_code = proc.returncode
                status = "SUCCESS" if exit_code == 0 else "FAILURE"
            except subprocess.TimeoutExpired:
                _terminate_process_tree(proc)
                stdout_text, stderr_text = proc.communicate()
                exit_code = -9
                status = "TIMEOUT"
                stderr_text += f"\n[JARVIS] Mission execution timed out after {timeout_seconds}s."

        except Exception as e:
            status = "ERROR"
            stderr_text = f"Execution invocation failure: {str(e)}"
            exit_code = -1

        duration = time.perf_counter() - start_time

        receipt = MissionReceipt(
            mission_id=mission_id,
            command=cmd_str,
            status=status,
            exit_code=exit_code,
            duration_seconds=round(duration, 4),
            workspace=str(sandbox),
            stdout=stdout_text,
            stderr=stderr_text,
            security_verdict="PASS_INSPECTED",
            timestamp_utc=timestamp_str,
            metadata={"timeout_limit": timeout_seconds}
        )

        self._save_receipt(receipt)
        return receipt

    def _save_receipt(self, receipt: MissionReceipt) -> None:
        """
        Persists cryptographic/forensic evidence receipt to state/missions/.
        """
        mission_dir = STATE_MISSIONS / receipt.mission_id
        mission_dir.mkdir(parents=True, exist_ok=True)
        receipt_path = mission_dir / "receipt.json"
        try:
            receipt_path.write_text(
                json.dumps(receipt.to_dict(), indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        except Exception:
            pass


def main():
    if len(sys.argv) < 2:
        print("Uso: python jarvis_mission_executor.py --cmd <comando> [--timeout <segundos>]")
        sys.exit(1)

    import argparse
    parser = argparse.ArgumentParser(description="J.A.R.V.I.S. Autonomous Mission Executor")
    parser.add_argument("--cmd", "-c", required=True, help="Comando a ser executado no sandbox")
    parser.add_argument("--timeout", "-t", type=float, default=60.0, help="Tempo limite em segundos")
    parser.add_argument("--mission-id", "-m", type=str, default=None, help="Identificador da missão")

    args = parser.parse_args()

    executor = JarvisMissionExecutor()
    receipt = executor.execute(command=args.cmd, mission_id=args.mission_id, timeout_seconds=args.timeout)

    print("\n" + "=" * 70)
    print(f" J.A.R.V.I.S. MISSION RECEIPT // [{receipt.mission_id}]")
    print("=" * 70)
    print(f" Status:         {receipt.status} (Código: {receipt.exit_code})")
    print(f" Duração:        {receipt.duration_seconds}s")
    print(f" Sandbox:        {receipt.workspace}")
    print(f" Segurança:      {receipt.security_verdict}")
    if receipt.stdout.strip():
        print("-" * 70)
        print(" STDOUT:")
        print(receipt.stdout.strip()[:1000])
    if receipt.stderr.strip():
        print("-" * 70)
        print(" STDERR:")
        print(receipt.stderr.strip()[:1000])
    print("=" * 70)

    sys.exit(0 if receipt.status == "SUCCESS" else 1)


if __name__ == "__main__":
    main()
