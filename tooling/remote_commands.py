"""Durable, approval-bound remote command execution for the J.A.R.V.I.S. PC host.

Remote reachability is not execution authority. A command request is normalized,
persisted as PENDING, and bound to a canonical SHA-256 digest. Execution happens
only after an explicit approval for that exact action digest.

The executor intentionally uses subprocess with shell=False. It is a development
runner, not a shell proxy: only a bounded set of executable families is accepted,
the working directory is confined to the repository, and inline-code shell
wrappers are rejected.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Callable, Optional

SCHEMA_VERSION = 1
MAX_ARGS = 64
MAX_ARG_CHARS = 4096
MAX_TOTAL_ARG_CHARS = 16_384
MAX_OUTPUT_CHARS = 64 * 1024
MAX_TIMEOUT_SECONDS = 900
_ALLOWED_EXECUTABLES = {
    "python",
    "python3",
    "py",
    "git",
    "node",
    "npm",
    "npm.cmd",
    "npx",
    "npx.cmd",
    "powershell",
    "powershell.exe",
    "pwsh",
    "pwsh.exe",
}
_ACTION_ID_RE = re.compile(r"^rcmd-[a-f0-9]{24}$")
_DIGEST_RE = re.compile(r"^[a-f0-9]{64}$")


class RemoteCommandError(ValueError):
    """Raised when a remote command request or transition is invalid."""


def _canonical_digest(value: dict) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _bounded_text(value: object, field: str, *, max_chars: int = MAX_ARG_CHARS) -> str:
    if not isinstance(value, str):
        raise RemoteCommandError(f"{field} must be a string")
    if not value or len(value) > max_chars or "\x00" in value or "\r" in value or "\n" in value:
        raise RemoteCommandError(f"{field} is invalid")
    return value


def normalize_command_payload(payload: object) -> dict:
    """Normalize one structured command request without executing it."""
    if not isinstance(payload, dict):
        raise RemoteCommandError("command payload must be an object")
    unknown = set(payload) - {"argv", "cwd", "timeout_seconds"}
    if unknown:
        raise RemoteCommandError("command payload contains unsupported fields")

    argv = payload.get("argv")
    if not isinstance(argv, list) or not argv or len(argv) > MAX_ARGS:
        raise RemoteCommandError("argv must be a non-empty bounded list")

    normalized_argv = [
        _bounded_text(arg, f"argv[{index}]")
        for index, arg in enumerate(argv)
    ]
    if sum(len(arg) for arg in normalized_argv) > MAX_TOTAL_ARG_CHARS:
        raise RemoteCommandError("argv exceeds total size limit")

    executable = Path(normalized_argv[0]).name.casefold()
    if executable not in _ALLOWED_EXECUTABLES:
        raise RemoteCommandError("executable is not allowed for remote PC execution")

    lowered = [arg.casefold() for arg in normalized_argv[1:]]
    if executable in {"python", "python3", "py"} and "-c" in lowered:
        raise RemoteCommandError("inline Python code is not allowed remotely")
    if executable == "node" and any(flag in lowered for flag in {"-e", "--eval", "-p", "--print"}):
        raise RemoteCommandError("inline Node.js code is not allowed remotely")
    if executable in {"powershell", "powershell.exe", "pwsh", "pwsh.exe"}:
        if any(flag in lowered for flag in {"-command", "-c", "-encodedcommand", "-enc"}):
            raise RemoteCommandError("inline PowerShell commands are not allowed remotely")
        if "-file" not in lowered:
            raise RemoteCommandError("remote PowerShell execution requires -File")

    cwd = payload.get("cwd", ".")
    if not isinstance(cwd, str):
        raise RemoteCommandError("cwd must be a string")
    cwd = cwd.replace("\\", "/").strip() or "."
    if cwd.startswith("/") or re.match(r"^[A-Za-z]:", cwd):
        raise RemoteCommandError("cwd must be repository-relative")
    if ".." in cwd.split("/"):
        raise RemoteCommandError("cwd traversal is not allowed")
    if "\r" in cwd or "\n" in cwd or "\x00" in cwd or len(cwd) > 1024:
        raise RemoteCommandError("cwd is invalid")

    timeout = payload.get("timeout_seconds", 120)
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool):
        raise RemoteCommandError("timeout_seconds must be numeric")
    timeout = int(timeout)
    if timeout < 1 or timeout > MAX_TIMEOUT_SECONDS:
        raise RemoteCommandError("timeout_seconds is outside the allowed range")

    return {
        "argv": normalized_argv,
        "cwd": cwd,
        "timeout_seconds": timeout,
    }


class RemoteCommandController:
    """Persist pending actions and execute only digest-bound approvals."""

    def __init__(
        self,
        state_dir: Path,
        *,
        workspace_root: Path,
        clock: Callable[[], float] = time.time,
        id_factory: Optional[Callable[[], str]] = None,
    ) -> None:
        self.state_dir = Path(state_dir)
        self.state_path = self.state_dir / "remote_commands.json"
        self.workspace_root = Path(workspace_root).resolve()
        self.clock = clock
        self.id_factory = id_factory or (lambda: f"rcmd-{secrets.token_hex(12)}")
        self._lock = threading.RLock()
        self._state = self._load()

    @staticmethod
    def _empty() -> dict:
        return {"schema_version": SCHEMA_VERSION, "actions": {}}

    def _load(self) -> dict:
        if not self.state_path.exists():
            return self._empty()
        try:
            value = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise RemoteCommandError("remote command state is unreadable") from exc
        if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
            raise RemoteCommandError("unsupported remote command state schema")
        actions = value.get("actions")
        if not isinstance(actions, dict):
            raise RemoteCommandError("remote command state is invalid")

        changed = False
        for action_id, record in actions.items():
            self._validate_record(action_id, record)
            if record["status"] == "RUNNING":
                record["status"] = "UNKNOWN"
                record["unknown_reason"] = "HOST_RESTARTED_DURING_EXECUTION"
                changed = True
        if changed:
            self._state = value
            self._save()
        return value

    @staticmethod
    def _validate_record(action_id: object, record: object) -> None:
        if not isinstance(action_id, str) or not _ACTION_ID_RE.fullmatch(action_id):
            raise RemoteCommandError("remote command action id is invalid")
        if not isinstance(record, dict) or record.get("action_id") != action_id:
            raise RemoteCommandError("remote command record is invalid")
        if record.get("status") not in {"PENDING", "RUNNING", "COMPLETED", "UNKNOWN"}:
            raise RemoteCommandError("remote command status is invalid")
        digest = record.get("action_digest")
        if not isinstance(digest, str) or not _DIGEST_RE.fullmatch(digest):
            raise RemoteCommandError("remote command digest is invalid")
        normalize_command_payload(record.get("command"))
        for field in ("session_id", "device_id", "request_id"):
            _bounded_text(record.get(field), field, max_chars=256)

    def _save(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(self._state, ensure_ascii=False, indent=2, sort_keys=True)
        fd, temp_name = tempfile.mkstemp(
            prefix="remote_commands.", suffix=".tmp", dir=str(self.state_dir)
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(encoded)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, self.state_path)
        except Exception:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
            raise

    def _resolve_cwd(self, relative: str) -> Path:
        normalized = normalize_command_payload(
            {"argv": ["python"], "cwd": relative, "timeout_seconds": 1}
        )["cwd"]
        candidate = (self.workspace_root / normalized).resolve()
        try:
            candidate.relative_to(self.workspace_root)
        except ValueError as exc:
            raise RemoteCommandError("cwd escapes workspace root") from exc
        if not candidate.exists() or not candidate.is_dir():
            raise RemoteCommandError("cwd does not exist or is not a directory")
        for component in [candidate, *candidate.parents]:
            if component == self.workspace_root:
                break
            if component.is_symlink() or (
                component.exists()
                and getattr(component.lstat(), "st_file_attributes", 0) & 0x400
            ):
                raise RemoteCommandError("cwd cannot traverse a symlink/reparse point")
        return candidate

    @staticmethod
    def _resolve_executable(argv0: str) -> str:
        name = Path(argv0).name.casefold()
        if name in {"python", "python3"}:
            return sys.executable
        resolved = shutil.which(argv0)
        if not resolved:
            raise RemoteCommandError(f"executable is unavailable on this PC: {argv0}")
        return resolved

    def prepare(
        self,
        payload: object,
        *,
        session_id: str,
        device_id: str,
        request_id: str,
    ) -> dict:
        command = normalize_command_payload(payload)
        session_id = _bounded_text(session_id, "session_id", max_chars=256)
        device_id = _bounded_text(device_id, "device_id", max_chars=256)
        request_id = _bounded_text(request_id, "request_id", max_chars=256)
        action_material = {
            "command": command,
            "session_id": session_id,
            "device_id": device_id,
            "request_id": request_id,
        }
        digest = _canonical_digest(action_material)
        action_id = self.id_factory()
        if not isinstance(action_id, str) or not _ACTION_ID_RE.fullmatch(action_id):
            raise RemoteCommandError("generated remote command action id is invalid")

        with self._lock:
            if action_id in self._state["actions"]:
                raise RemoteCommandError("remote command action id collision")
            now = float(self.clock())
            record = {
                "action_id": action_id,
                "action_digest": digest,
                "status": "PENDING",
                "session_id": session_id,
                "device_id": device_id,
                "request_id": request_id,
                "command": command,
                "created_at": now,
                "updated_at": now,
                "result": None,
            }
            self._state["actions"][action_id] = record
            self._save()
            return json.loads(json.dumps(record))

    def get(self, action_id: str) -> Optional[dict]:
        with self._lock:
            record = self._state["actions"].get(action_id)
            return json.loads(json.dumps(record)) if isinstance(record, dict) else None

    def approve_and_execute(
        self,
        *,
        action_id: str,
        action_digest: str,
        session_id: str,
        device_id: str,
    ) -> dict:
        if not isinstance(action_id, str) or not _ACTION_ID_RE.fullmatch(action_id):
            raise RemoteCommandError("action_id is invalid")
        if not isinstance(action_digest, str) or not _DIGEST_RE.fullmatch(action_digest):
            raise RemoteCommandError("action_digest is invalid")

        with self._lock:
            record = self._state["actions"].get(action_id)
            if record is None:
                raise RemoteCommandError("remote command action does not exist")
            if record["session_id"] != session_id or record["device_id"] != device_id:
                raise RemoteCommandError("remote command approval ownership mismatch")
            if not secrets.compare_digest(record["action_digest"], action_digest):
                raise RemoteCommandError("remote command approval digest mismatch")
            if record["status"] == "COMPLETED":
                return json.loads(json.dumps(record["result"]))
            if record["status"] == "UNKNOWN":
                raise RemoteCommandError("remote command outcome is unknown and will not be replayed")
            if record["status"] != "PENDING":
                raise RemoteCommandError("remote command action is not pending")

            record["status"] = "RUNNING"
            record["updated_at"] = float(self.clock())
            self._save()
            command = json.loads(json.dumps(record["command"]))

        result = self._execute(command, action_id=action_id, action_digest=action_digest)

        with self._lock:
            record = self._state["actions"][action_id]
            record["status"] = "COMPLETED"
            record["updated_at"] = float(self.clock())
            record["result"] = result
            self._save()
            return json.loads(json.dumps(result))

    def _execute(self, command: dict, *, action_id: str, action_digest: str) -> dict:
        normalized = normalize_command_payload(command)
        started_at = float(self.clock())
        t0 = time.perf_counter()
        env = dict(os.environ)
        env.setdefault("PYTHONUTF8", "1")
        env.setdefault("PYTHONUNBUFFERED", "1")

        status = "ERROR"
        exit_code = None
        stdout = ""
        stderr = ""
        reason = None
        try:
            cwd = self._resolve_cwd(normalized["cwd"])
            executable = self._resolve_executable(normalized["argv"][0])
            argv = [executable, *normalized["argv"][1:]]
            completed = subprocess.run(
                argv,
                cwd=str(cwd),
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=normalized["timeout_seconds"],
                shell=False,
                check=False,
            )
            exit_code = int(completed.returncode)
            stdout = completed.stdout or ""
            stderr = completed.stderr or ""
            status = "PASS" if exit_code == 0 else "FAIL"
        except subprocess.TimeoutExpired as exc:
            status = "TIMEOUT"
            reason = "COMMAND_TIMEOUT"
            stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
        except Exception as exc:
            status = "ERROR"
            reason = f"{type(exc).__name__}: {exc}"

        duration_ms = round((time.perf_counter() - t0) * 1000.0, 3)
        return {
            "schema_version": SCHEMA_VERSION,
            "action_id": action_id,
            "action_digest": action_digest,
            "status": status,
            "exit_code": exit_code,
            "cwd": normalized["cwd"],
            "argv": normalized["argv"],
            "started_at": started_at,
            "finished_at": float(self.clock()),
            "duration_ms": duration_ms,
            "stdout": stdout[:MAX_OUTPUT_CHARS],
            "stderr": stderr[:MAX_OUTPUT_CHARS],
            "stdout_truncated": len(stdout) > MAX_OUTPUT_CHARS,
            "stderr_truncated": len(stderr) > MAX_OUTPUT_CHARS,
            "reason": reason,
        }
