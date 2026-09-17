#!/usr/bin/env python3
"""Portable evidence runner for the public J.A.R.V.I.S. quickstart.

Runs the documented doctor/self-test commands, launches the real HUD through
`jarvis.py --no-browser`, confirms a loopback HTTP response, and terminates the
whole process tree. No provider credential or live provider call is required.
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import platform
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
JARVIS = ROOT / "jarvis.py"
CLAIM_BOUNDARY = (
    "local startup only; does not certify provider connectivity or browser rendering"
)


def build_quickstart_commands(port: int) -> dict[str, list[str]]:
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("port must be between 1 and 65535")
    return {
        "doctor": [sys.executable, str(JARVIS), "--doctor"],
        "test": [sys.executable, str(JARVIS), "--test"],
        "launch": [
            sys.executable,
            str(JARVIS),
            "--no-browser",
            "--port",
            str(port),
        ],
    }


def resolve_commit_sha() -> str:
    github_sha = os.environ.get("GITHUB_SHA", "").strip()
    if len(github_sha) == 40 and all(ch in "0123456789abcdefABCDEF" for ch in github_sha):
        return github_sha.lower()
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return "UNKNOWN"
    value = completed.stdout.strip()
    return value or "UNKNOWN"


def environment_record(*, commit_sha: str | None = None) -> dict[str, str]:
    return {
        "commit_sha": commit_sha or resolve_commit_sha(),
        "os": platform.system() or "UNKNOWN",
        "os_release": platform.release() or "UNKNOWN",
        "os_version": platform.version() or "UNKNOWN",
        "machine": platform.machine() or "UNKNOWN",
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
    }


def choose_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return int(sock.getsockname()[1])


def _command_result(command: list[str], *, timeout: float = 120.0) -> dict:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "FAIL",
            "reason": "COMMAND_TIMEOUT",
            "command": command,
            "exit_code": None,
            "duration_seconds": round(time.monotonic() - started, 3),
            "output_tail": ((exc.stdout or "") + "\n" + (exc.stderr or ""))[-2000:],
        }
    output = ((completed.stdout or "") + "\n" + (completed.stderr or "")).strip()
    return {
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "reason": None if completed.returncode == 0 else "NONZERO_EXIT",
        "command": command,
        "exit_code": completed.returncode,
        "duration_seconds": round(time.monotonic() - started, 3),
        "output_tail": output[-2000:] if completed.returncode != 0 else "",
    }


def _probe_local_http(port: int, *, timeout: float = 1.0) -> tuple[int, int]:
    """Probe the HUD over a direct loopback connection without proxy discovery."""
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    try:
        connection.request("GET", "/")
        response = connection.getresponse()
        payload = response.read(1024 * 1024)
        return response.status, len(payload)
    finally:
        connection.close()


def _stop_process_tree(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        return

    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=5)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def _launch_result(command: list[str], port: int, *, startup_timeout: float = 20.0) -> dict:
    url = f"http://127.0.0.1:{port}/"
    started = time.monotonic()
    creationflags = 0
    kwargs = {}
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    else:
        kwargs["start_new_session"] = True

    with tempfile.TemporaryFile(mode="w+b") as output:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=output,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
            **kwargs,
        )
        http_status = None
        response_bytes = 0
        reason = "HUD_STARTUP_TIMEOUT"
        try:
            deadline = time.monotonic() + startup_timeout
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    reason = "HUD_PROCESS_EXITED"
                    break
                try:
                    http_status, response_bytes = _probe_local_http(port, timeout=1.0)
                    if http_status == 200 and response_bytes > 0:
                        reason = None
                        break
                except (OSError, TimeoutError, http.client.HTTPException):
                    time.sleep(0.2)
        finally:
            _stop_process_tree(process)
            output.flush()
            output.seek(0)
            captured = output.read().decode("utf-8", errors="replace")

    passed = reason is None and http_status == 200 and response_bytes > 0
    return {
        "status": "PASS" if passed else "FAIL",
        "reason": reason,
        "command": command,
        "url": url,
        "http_status": http_status,
        "response_bytes": response_bytes,
        "provider_key_required": False,
        "duration_seconds": round(time.monotonic() - started, 3),
        "output_tail": "" if passed else captured[-4000:],
    }


def verify_quickstart(*, port: int | None = None) -> dict:
    selected_port = port or choose_free_port()
    commands = build_quickstart_commands(selected_port)
    result = {
        **environment_record(),
        "claim_boundary": CLAIM_BOUNDARY,
        "provider_key_required": False,
        "checks": {},
    }

    result["checks"]["doctor"] = _command_result(commands["doctor"])
    if result["checks"]["doctor"]["status"] != "PASS":
        result["status"] = "FAIL"
        return result

    result["checks"]["test"] = _command_result(commands["test"])
    if result["checks"]["test"]["status"] != "PASS":
        result["status"] = "FAIL"
        return result

    result["checks"]["launch"] = _launch_result(commands["launch"], selected_port)
    result["status"] = (
        "PASS"
        if all(check["status"] == "PASS" for check in result["checks"].values())
        else "FAIL"
    )
    return result


def _write_json(path: Path, result: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify the public J.A.R.V.I.S. local quickstart without provider credentials."
    )
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--json-output", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = verify_quickstart(port=args.port)
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.json_output is not None:
        _write_json(args.json_output, result)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
