"""Per-user Windows resident-host autostart for J.A.R.V.I.S.

The resident process does not require administrator elevation. Windows autostart
is registered in the current user's HKCU Run key, which launches a generated
.pyw wrapper at logon. Tailscale Serve provisioning is intentionally separate
and may require a one-time Admin terminal; this module only starts the already
configured JARVIS host.

Immediate stop is requested through the loopback-only resident HTTP control
endpoint so we never terminate an unverified/recycled PID.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable, Optional

from tooling.remote_state_security import safe_state_directory, safe_state_file, secure_state_directory

RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE_NAME = "JARVIS Remote Host"
SERVICE_DIR_NAME = "remote_service"
LAUNCHER_NAME = "jarvis_remote_host.pyw"
METADATA_NAME = "service.json"
MAX_RUN_COMMAND_CHARS = 260


class RemoteServiceError(RuntimeError):
    """Raised when resident-host autostart registration cannot be completed."""


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


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(
        prefix=f"{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


class WindowsRemoteService:
    """Manage one current-user HKCU Run entry for the resident PC host."""

    def __init__(
        self,
        registry_root: Path,
        state_dir: Path,
        *,
        platform_name: str = os.name,
        registry_module=None,
        popen_factory: Callable = subprocess.Popen,
        urlopen: Callable = urllib.request.urlopen,
    ) -> None:
        self.registry_root = Path(registry_root).resolve()
        raw_state_dir = Path(state_dir)
        if not secure_state_directory(raw_state_dir):
            raise RemoteServiceError("resident host state directory is unsafe")
        self.state_dir = raw_state_dir.absolute()
        self.service_dir = self.state_dir / SERVICE_DIR_NAME
        self.launcher_path = self.service_dir / LAUNCHER_NAME
        self.metadata_path = self.service_dir / METADATA_NAME
        self.platform_name = platform_name
        self.registry_module = registry_module
        self.popen_factory = popen_factory
        self.urlopen = urlopen

    def _require_windows(self) -> None:
        if self.platform_name != "nt":
            raise RemoteServiceError("Windows HKCU Run autostart is only available on Windows")

    def _registry(self):
        if self.registry_module is not None:
            return self.registry_module
        try:
            import winreg
        except ImportError as exc:
            raise RemoteServiceError("winreg is unavailable on this Windows host") from exc
        return winreg

    def _read_metadata(self) -> Optional[dict]:
        if not self.metadata_path.exists():
            return None
        if not safe_state_file(self.metadata_path) or not self.metadata_path.is_file():
            return None
        try:
            value = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return None
        return value if isinstance(value, dict) else None

    def _validated_installation(self) -> dict:
        metadata = self._read_metadata()
        if not metadata:
            raise RemoteServiceError("resident host autostart is not installed")
        if metadata.get("schema_version") != 2:
            raise RemoteServiceError("resident host metadata schema is invalid")
        if Path(str(metadata.get("registry_root", ""))).resolve() != self.registry_root:
            raise RemoteServiceError("resident host metadata registry root mismatch")

        port = metadata.get("port")
        transport = metadata.get("transport")
        if not isinstance(port, int) or isinstance(port, bool) or not (1 <= port <= 65535):
            raise RemoteServiceError("resident host metadata contains invalid port")
        if transport not in {"local", "lan", "tailscale", "tailscale-serve"}:
            raise RemoteServiceError("resident host metadata contains invalid transport")

        expected_launcher_path = self.launcher_path.resolve()
        declared_launcher = Path(str(metadata.get("launcher", ""))).resolve()
        if declared_launcher != expected_launcher_path:
            raise RemoteServiceError("resident host metadata launcher path mismatch")
        if not safe_state_file(self.launcher_path) or not self.launcher_path.is_file():
            raise RemoteServiceError("resident host launcher is missing or unsafe")

        expected_launcher = build_windows_launcher(
            registry_root=self.registry_root,
            port=port,
            transport=transport,
        )
        try:
            actual_launcher = self.launcher_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise RemoteServiceError("resident host launcher is unreadable") from exc
        if actual_launcher != expected_launcher:
            raise RemoteServiceError("resident host launcher content mismatch")

        expected_python = _pythonw(self.platform_name).resolve()
        declared_python = Path(str(metadata.get("python", ""))).resolve()
        if declared_python != expected_python or not expected_python.is_file():
            raise RemoteServiceError("resident host Python executable mismatch")

        expected_command = subprocess.list2cmdline(
            [str(expected_python), str(expected_launcher_path)]
        )
        if metadata.get("command") != expected_command:
            raise RemoteServiceError("resident host metadata command mismatch")

        result = dict(metadata)
        result["port"] = port
        result["transport"] = transport
        result["launcher"] = str(expected_launcher_path)
        result["python"] = str(expected_python)
        result["command"] = expected_command
        return result

    def _read_run_value(self) -> Optional[str]:
        reg = self._registry()
        try:
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, RUN_KEY_PATH)
        except OSError:
            return None
        try:
            value, _kind = reg.QueryValueEx(key, RUN_VALUE_NAME)
        except OSError:
            return None
        finally:
            reg.CloseKey(key)
        return value if isinstance(value, str) else None

    def _write_run_value(self, command: str) -> None:
        reg = self._registry()
        key = reg.CreateKey(reg.HKEY_CURRENT_USER, RUN_KEY_PATH)
        try:
            reg.SetValueEx(key, RUN_VALUE_NAME, 0, reg.REG_SZ, command)
        finally:
            reg.CloseKey(key)

    def _delete_run_value(self) -> None:
        reg = self._registry()
        try:
            key = reg.OpenKey(
                reg.HKEY_CURRENT_USER,
                RUN_KEY_PATH,
                0,
                getattr(reg, "KEY_SET_VALUE", 0),
            )
        except OSError:
            return
        try:
            try:
                reg.DeleteValue(key, RUN_VALUE_NAME)
            except OSError:
                pass
        finally:
            reg.CloseKey(key)

    def install(self, *, port: int = 8899, transport: str = "local") -> dict:
        self._require_windows()
        launcher = build_windows_launcher(
            registry_root=self.registry_root,
            port=port,
            transport=transport,
        )
        pythonw = _pythonw(self.platform_name).resolve()
        command = subprocess.list2cmdline([str(pythonw), str(self.launcher_path)])
        if len(command) > MAX_RUN_COMMAND_CHARS:
            raise RemoteServiceError(
                f"HKCU Run command is {len(command)} characters; maximum supported is "
                f"{MAX_RUN_COMMAND_CHARS}. Move the checkout to a shorter path."
            )

        self.service_dir.mkdir(parents=True, exist_ok=True)
        if not safe_state_directory(self.service_dir) or not self.service_dir.is_dir():
            raise RemoteServiceError("resident host service directory is unsafe")

        previous_files = {}
        for path in (self.launcher_path, self.metadata_path):
            if path.exists():
                if not safe_state_file(path) or not path.is_file():
                    raise RemoteServiceError("resident host generated file path is unsafe")
                try:
                    previous_files[path] = path.read_text(encoding="utf-8")
                except (OSError, UnicodeError) as exc:
                    raise RemoteServiceError("resident host generated file is unreadable") from exc
            else:
                previous_files[path] = None
        previous_run_value = self._read_run_value()

        metadata = {
            "schema_version": 2,
            "platform": "windows",
            "autostart": "HKCU_RUN",
            "run_key": RUN_KEY_PATH,
            "run_value": RUN_VALUE_NAME,
            "registry_root": str(self.registry_root),
            "launcher": str(self.launcher_path),
            "python": str(pythonw),
            "command": command,
            "port": port,
            "transport": transport,
        }

        try:
            _atomic_write_text(self.launcher_path, launcher)
            _atomic_write_text(
                self.metadata_path,
                json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            )
            self._write_run_value(command)
        except Exception as exc:
            for path, previous in previous_files.items():
                try:
                    if previous is None:
                        path.unlink(missing_ok=True)
                    else:
                        _atomic_write_text(path, previous)
                except Exception:
                    pass
            try:
                if previous_run_value is None:
                    self._delete_run_value()
                else:
                    self._write_run_value(previous_run_value)
            except Exception:
                pass
            raise RemoteServiceError(
                f"failed to install resident host autostart: {exc}"
            ) from exc
        return metadata

    def start(self) -> dict:
        self._require_windows()
        metadata = self._validated_installation()
        launcher = Path(metadata["launcher"])
        python_path = Path(metadata["python"])
        try:
            process = self.popen_factory(
                [str(python_path), str(launcher)],
                cwd=str(self.registry_root),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=False,
                close_fds=True,
            )
        except OSError as exc:
            raise RemoteServiceError(f"failed to start resident host: {exc}") from exc
        return {
            "status": "START_REQUESTED",
            "autostart": "HKCU_RUN",
            "pid": getattr(process, "pid", None),
        }

    def stop(self) -> dict:
        self._require_windows()
        metadata = self._validated_installation()
        port = metadata["port"]
        request = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/remote/v1/admin/stop",
            data=b"",
            method="POST",
        )
        try:
            with self.urlopen(request, timeout=5) as response:
                status_code = getattr(response, "status", 0)
                raw = response.read()
        except urllib.error.HTTPError as exc:
            raise RemoteServiceError(f"resident host stop rejected with HTTP {exc.code}") from exc
        except (OSError, urllib.error.URLError) as exc:
            return {
                "status": "ALREADY_STOPPED_OR_UNREACHABLE",
                "autostart": "HKCU_RUN",
                "detail": str(exc),
            }
        if status_code != 202:
            raise RemoteServiceError(f"resident host stop returned HTTP {status_code}")
        try:
            body = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeError, json.JSONDecodeError):
            body = {}
        return {
            "status": body.get("status", "STOPPING"),
            "autostart": "HKCU_RUN",
        }

    def status(self) -> dict:
        self._require_windows()
        command = self._read_run_value()
        raw_metadata = self._read_metadata()
        try:
            metadata = self._validated_installation()
            validation_error = None
        except RemoteServiceError as exc:
            metadata = raw_metadata
            validation_error = str(exc)
        expected = metadata.get("command") if isinstance(metadata, dict) and validation_error is None else None
        installed = command is not None
        matches_metadata = bool(installed and expected and command == expected)

        try:
            from tooling.remote_host import RemoteHostController

            host = RemoteHostController(self.state_dir).status()
        except Exception as exc:
            host = {
                "status": "OFFLINE",
                "reason": "STATE_ERROR",
                "detail": f"{type(exc).__name__}: {exc}",
            }

        return {
            "installed": installed,
            "matches_metadata": matches_metadata,
            "autostart": "HKCU_RUN",
            "run_key": RUN_KEY_PATH,
            "run_value": RUN_VALUE_NAME,
            "command": command,
            "metadata": metadata,
            "validation_error": validation_error,
            "host": host,
        }

    def uninstall(self) -> dict:
        self._require_windows()
        self._delete_run_value()
        if not safe_state_directory(self.service_dir):
            raise RemoteServiceError(
                "autostart disabled but resident host service directory is unsafe"
            )
        for path in (self.launcher_path, self.metadata_path):
            if not safe_state_file(path):
                raise RemoteServiceError(
                    "autostart disabled but resident host generated file path is unsafe"
                )
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        try:
            self.service_dir.rmdir()
        except OSError:
            pass
        return {
            "status": "UNINSTALLED",
            "autostart": "HKCU_RUN",
            "run_value": RUN_VALUE_NAME,
        }


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
