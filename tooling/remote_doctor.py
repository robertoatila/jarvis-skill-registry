"""Read-only readiness checks for using a Windows PC as the J.A.R.V.I.S. remote host."""

from __future__ import annotations

import json
import os
import platform
import socket
import subprocess
import sys
from pathlib import Path
from typing import Callable

from tooling.remote_host import RemoteHostController


def _run(runner: Callable, args: list[str], timeout: float = 5.0):
    try:
        return runner(
            args,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=False,
            check=False,
        )
    except (FileNotFoundError, OSError, subprocess.SubprocessError):
        return None


def _check_loopback_port(port: int) -> dict:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        probe.bind(("127.0.0.1", port))
    except OSError as exc:
        return {"state": "IN_USE", "detail": str(exc)}
    finally:
        probe.close()
    return {"state": "AVAILABLE", "detail": "loopback port is available"}


def remote_doctor(
    registry_root: Path,
    state_dir: Path,
    *,
    port: int = 8899,
    runner: Callable = subprocess.run,
) -> dict:
    root = Path(registry_root).resolve()
    state_dir = Path(state_dir).resolve()
    checks: dict[str, dict] = {}

    checks["platform"] = {
        "state": "PASS" if os.name == "nt" else "INFO",
        "system": platform.system(),
        "release": platform.release(),
        "target": "Windows",
    }
    checks["python"] = {
        "state": "PASS" if sys.version_info >= (3, 12) else "FAIL",
        "version": platform.python_version(),
        "executable": sys.executable,
    }
    checks["repository"] = {
        "state": "PASS" if (root / "jarvis.py").is_file() and (root / "tooling").is_dir() else "FAIL",
        "path": str(root),
    }

    host_status = RemoteHostController(state_dir).status()
    checks["resident_host"] = {
        "state": "ONLINE" if host_status.get("status") == "ONLINE" else "OFFLINE",
        "detail": host_status,
    }
    if host_status.get("status") == "ONLINE" and host_status.get("port") == port:
        checks["port"] = {
            "state": "PASS",
            "detail": f"port {port} is owned by the recorded live JARVIS host",
        }
    else:
        port_probe = _check_loopback_port(port)
        checks["port"] = {
            "state": "PASS" if port_probe["state"] == "AVAILABLE" else "WARN",
            **port_probe,
        }

    version = _run(runner, ["tailscale", "version"], timeout=3.0)
    checks["tailscale_cli"] = {
        "state": "PASS" if version is not None and version.returncode == 0 else "FAIL",
        "detail": (
            (version.stdout or version.stderr or "").strip().splitlines()[0]
            if version is not None and (version.stdout or version.stderr)
            else "Tailscale CLI unavailable"
        ),
    }

    status_result = _run(runner, ["tailscale", "status", "--json"], timeout=5.0)
    tailscale_payload = None
    if status_result is not None and status_result.returncode == 0:
        try:
            value = json.loads(status_result.stdout or "")
            tailscale_payload = value if isinstance(value, dict) else None
        except (TypeError, json.JSONDecodeError):
            tailscale_payload = None

    self_status = tailscale_payload.get("Self") if isinstance(tailscale_payload, dict) else None
    running = bool(
        isinstance(tailscale_payload, dict)
        and tailscale_payload.get("BackendState") == "Running"
        and isinstance(self_status, dict)
        and self_status.get("Online") is True
    )
    dns_name = self_status.get("DNSName") if isinstance(self_status, dict) else None
    ips = self_status.get("TailscaleIPs") if isinstance(self_status, dict) else None
    checks["tailscale_node"] = {
        "state": "PASS" if running else "FAIL",
        "backend_state": tailscale_payload.get("BackendState") if isinstance(tailscale_payload, dict) else None,
        "online": self_status.get("Online") if isinstance(self_status, dict) else None,
        "dns_name": dns_name,
        "tailscale_ips": ips if isinstance(ips, list) else [],
    }
    checks["tailnet_dns"] = {
        "state": "PASS" if isinstance(dns_name, str) and dns_name.strip() else "FAIL",
        "dns_name": dns_name,
    }

    serve = _run(runner, ["tailscale", "serve", "status", "--json"], timeout=5.0)
    serve_payload = None
    if serve is not None and serve.returncode == 0:
        try:
            parsed = json.loads(serve.stdout or "{}")
            serve_payload = parsed if isinstance(parsed, dict) else None
        except (TypeError, json.JSONDecodeError):
            serve_payload = None
    checks["tailscale_serve"] = {
        "state": "PASS" if serve_payload is not None else "WARN",
        "configured": bool(serve_payload),
        "detail": "Serve CLI/status available" if serve_payload is not None else "Serve status unavailable; first-time HTTPS consent may still be required",
    }

    if os.name == "nt":
        from tooling.remote_service import WindowsRemoteService

        try:
            service_status = WindowsRemoteService(root, state_dir, runner=runner).status()
        except Exception as exc:
            service_status = {"installed": False, "detail": f"{type(exc).__name__}: {exc}"}
        checks["windows_autostart"] = {
            "state": "PASS" if service_status.get("installed") else "WARN",
            **service_status,
        }
    else:
        checks["windows_autostart"] = {
            "state": "INFO",
            "installed": False,
            "detail": "Windows Scheduled Task check skipped on this platform",
        }

    hard_failures = [
        name
        for name in ("python", "repository", "tailscale_cli", "tailscale_node", "tailnet_dns")
        if checks[name]["state"] == "FAIL"
    ]
    return {
        "schema_version": 1,
        "status": "READY" if not hard_failures else "NOT_READY",
        "target": "windows-pc-remote-host",
        "port": port,
        "checks": checks,
        "hard_failures": hard_failures,
        "next_command": (
            "python jarvis.py service install --transport tailscale-serve"
            if not hard_failures
            else None
        ),
    }
