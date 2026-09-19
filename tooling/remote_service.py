"""Per-user resident-host service management for J.A.R.V.I.S.

Windows is the first concrete backend because the primary Remote Companion host
is a Windows PC. Registration uses a per-user Scheduled Task at logon and a
generated .pyw launcher that restores the repository as cwd/sys.path before
starting tooling.remote_host. No administrator privilege is requested.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional

TASK_NAME = "JARVIS Remote Host"
SERVICE_DIR_NAME = "remote_service"
LAUNCHER_NAME = "jarvis_remote_host.pyw"
METADATA_NAME = "service.json"


class RemoteServiceError(RuntimeError):
    """Raised when resident-host service registration cannot be completed."""


def _quote_py(value: str) -> str:
    return repr(str(value))


def build_windows_launcher(
    *,
    registry_root: Path,
    port: int,
    transport: str,
) -> str:
    root = Path(registry_root).resolve()
    if not isinstance(port, int) or isinstance(port, bool) or not (1 <= port <= 65535):
        raise RemoteServiceError("port is invalid")
    if transport not in {"local", "lan", "tailscale", "tailscale-serve"}:
        raise RemoteServiceError("transport is invalid")
    args = ["--port", str(port), "--transport", transport]
    return (
        "from pathlib import Path\n"
        "import os\n"
        "import sys\n"
        f"ROOT = Path({_quote_py(str(root))}).resolve()\n"
        "os.chdir(ROOT)\n"
        "sys.path.insert(0, str(ROOT))\n"
        "from tooling.remote_host import main\n"
        f"raise SystemExit(main({args!r}))\n"
    )


def _pythonw(platform_name: str = os.name) -> Path:
    current = Path(sys.executable).resolve()
    if platform_name == "nt":
        candidate = current.with_name("pythonw.exe")
        if candidate.exists():
            return candidate
    return current


class WindowsRemoteService:
    """Manage one per-user Windows Scheduled Task for the resident PC host."""

    def __init__(
        self,
        registry_root: Path,
        state_dir: Path,
        *,
        runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
        platform_name: str = os.name,
    ) -> None:
        self.registry_root = Path(registry_root).resolve()
        self.state_dir = Path(state_dir).resolve()
        self.service_dir = self.state_dir / SERVICE_DIR_NAME
        self.launcher_path = self.service_dir / LAUNCHER_NAME
        self.metadata_path = self.service_dir / METADATA_NAME
        self.runner = runner
        self.platform_name = platform_name

    def _require_windows(self) -> None:
        if self.platform_name != "nt":
            raise RemoteServiceError("Windows Scheduled Task service is only available on Windows")

    def _run(self, args: list[str], *, check: bool = False) -> subprocess.CompletedProcess:
        try:
            return self.runner(
                args,
                cwd=str(self.registry_root),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                shell=False,
                check=check,
            )
        except FileNotFoundError as exc:
            raise RemoteServiceError("schtasks.exe is unavailable on this Windows host") from exc
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or "").strip()
            raise RemoteServiceError(detail or "Windows service command failed") from exc

    def install(self, *, port: int = 8899, transport: str = "local") -> dict:
        self._require_windows()
        launcher = build_windows_launcher(
            registry_root=self.registry_root,
            port=port,
            transport=transport,
        )
        self.service_dir.mkdir(parents=True, exist_ok=True)
        self.launcher_path.write_text(launcher, encoding="utf-8", newline="\n")
        pythonw = _pythonw(self.platform_name)
        task_command = subprocess.list2cmdline([str(pythonw), str(self.launcher_path)])
        result = self._run(
            [
                "schtasks.exe",
                "/Create",
                "/TN",
                TASK_NAME,
                "/SC",
                "ONLOGON",
                "/TR",
                task_command,
                "/RL",
                "LIMITED",
                "/F",
            ]
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise RemoteServiceError(detail or "failed to register Windows Scheduled Task")

        metadata = {
            "schema_version": 1,
            "platform": "windows",
            "task_name": TASK_NAME,
            "registry_root": str(self.registry_root),
            "launcher": str(self.launcher_path),
            "python": str(pythonw),
            "port": port,
            "transport": transport,
        }
        self.metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return metadata

    def start(self) -> dict:
        self._require_windows()
        result = self._run(["schtasks.exe", "/Run", "/TN", TASK_NAME])
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise RemoteServiceError(detail or "failed to start Windows Scheduled Task")
        return {"status": "START_REQUESTED", "task_name": TASK_NAME}

    def stop(self) -> dict:
        self._require_windows()
        result = self._run(["schtasks.exe", "/End", "/TN", TASK_NAME])
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise RemoteServiceError(detail or "failed to stop Windows Scheduled Task")
        return {"status": "STOP_REQUESTED", "task_name": TASK_NAME}

    def status(self) -> dict:
        self._require_windows()
        result = self._run(
            ["schtasks.exe", "/Query", "/TN", TASK_NAME, "/FO", "LIST", "/V"]
        )
        installed = result.returncode == 0
        metadata = None
        if self.metadata_path.exists():
            try:
                value = json.loads(self.metadata_path.read_text(encoding="utf-8"))
                metadata = value if isinstance(value, dict) else None
            except (OSError, UnicodeError, json.JSONDecodeError):
                metadata = None
        return {
            "installed": installed,
            "task_name": TASK_NAME,
            "detail": (result.stdout or result.stderr or "").strip(),
            "metadata": metadata,
        }

    def uninstall(self) -> dict:
        self._require_windows()
        result = self._run(["schtasks.exe", "/Delete", "/TN", TASK_NAME, "/F"])
        if result.returncode not in {0, 1}:
            detail = (result.stderr or result.stdout or "").strip()
            raise RemoteServiceError(detail or "failed to delete Windows Scheduled Task")
        for path in (self.launcher_path, self.metadata_path):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        try:
            self.service_dir.rmdir()
        except OSError:
            pass
        return {"status": "UNINSTALLED", "task_name": TASK_NAME}


def manage_windows_service(
    action: str,
    *,
    registry_root: Path,
    state_dir: Path,
    port: int = 8899,
    transport: str = "local",
) -> dict:
    manager = WindowsRemoteService(registry_root, state_dir)
    if action == "install":
        return manager.install(port=port, transport=transport)
    if action == "start":
        return manager.start()
    if action == "stop":
        return manager.stop()
    if action == "status":
        return manager.status()
    if action == "uninstall":
        return manager.uninstall()
    raise RemoteServiceError("unsupported service action")
