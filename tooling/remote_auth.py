#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. Remote Mobile Companion Authentication & Network Discovery
Pure Python 3.10+ Standard Library (Zero PIP Dependencies)
"""

from __future__ import annotations
import json
import os
import secrets
import socket
import stat
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Optional

from tooling.remote_state_security import safe_state_directory, safe_state_file, secure_state_directory

REGISTRY_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = REGISTRY_ROOT / "state"
TOKEN_FILE = STATE_DIR / "remote_auth_token.json"


def detect_local_ip() -> str:
    """Detect the best non-loopback local network IPv4 address (LAN / Wi-Fi / Tailscale)."""
    try:
        # Create UDP socket towards non-routable address to probe default route interface
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("10.255.255.255", 1))
        local_ip = s.getsockname()[0]
        s.close()
        if local_ip and not local_ip.startswith("127."):
            return local_ip
    except Exception:
        pass

    # Fallback to gethostbyname_ex
    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if not ip.startswith("127.") and not ip.startswith("169.254."):
                return ip
    except Exception:
        pass

    return "127.0.0.1"


class RemoteAuthManager:
    """Manages ephemeral sovereign tokens for secure mobile companion access."""

    def __init__(self, token_file: Path = TOKEN_FILE):
        self.token_file = Path(token_file)
        self.active_token: Optional[str] = None
        self.created_at: float = 0
        self._assert_safe_token_path()
        self._load_or_create_token()

    def _assert_safe_token_path(self) -> None:
        if not secure_state_directory(self.token_file.parent):
            raise ValueError("remote auth token directory is unsafe")
        if not safe_state_file(self.token_file):
            raise ValueError("remote auth token path must be a regular safe file")

    def _load_or_create_token(self) -> str:
        if self.token_file.exists():
            try:
                self._assert_safe_token_path()
                if not self.token_file.is_file():
                    raise ValueError("remote auth token path must be a regular file")
                data = json.loads(self.token_file.read_text(encoding="utf-8"))
                token = data.get("token")
                created = data.get("created_at", 0)
                # Keep a sufficiently strong token if valid and under 7 days old.
                if (
                    token
                    and isinstance(token, str)
                    and len(token) >= 32
                    and isinstance(created, (int, float))
                    and not isinstance(created, bool)
                    and 0 <= time.time() - float(created) < 7 * 86400
                ):
                    self.active_token = token
                    self.created_at = float(created)
                    return token
            except Exception:
                pass

        # Generate a 256-bit cryptographically secure token.
        token = secrets.token_hex(32)
        self.active_token = token
        self.created_at = time.time()
        self._save()
        return token

    def regenerate_token(self) -> str:
        self.active_token = secrets.token_hex(32)
        self.created_at = time.time()
        self._save()
        return self.active_token

    def _save(self):
        temporary = None
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        self._assert_safe_token_path()
        try:
            payload = {
                "token": self.active_token,
                "created_at": self.created_at,
                "created_utc": time.strftime(
                    "%Y-%m-%d %H:%M:%S UTC",
                    time.gmtime(self.created_at),
                ),
                "purpose": "JARVIS Mobile Companion Sovereign Access Token",
            }
            encoded = json.dumps(payload, indent=2) + "\n"
            fd, temporary = tempfile.mkstemp(
                prefix="remote_auth_token.",
                suffix=".tmp",
                dir=str(self.token_file.parent),
            )
            try:
                try:
                    os.fchmod(fd, stat.S_IRUSR | stat.S_IWUSR)
                except (AttributeError, OSError):
                    pass
                with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                    stream.write(encoded)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, self.token_file)
                temporary = None
                try:
                    os.chmod(self.token_file, stat.S_IRUSR | stat.S_IWUSR)
                except OSError:
                    pass
            except Exception:
                try:
                    os.close(fd)
                except OSError:
                    pass
                raise
        except Exception as exc:
            raise RuntimeError("could not persist remote auth token safely") from exc
        finally:
            if temporary:
                try:
                    os.unlink(temporary)
                except OSError:
                    pass

    def validate_token(self, candidate: Optional[str]) -> bool:
        if not candidate or not self.active_token:
            return False
        # Constant-time comparison to prevent timing attacks
        return secrets.compare_digest(candidate.strip(), self.active_token)

    def get_companion_url(self, host_ip: Optional[str] = None, port: int = 8899) -> str:
        ip = host_ip or detect_local_ip()
        return f"http://{ip}:{port}/?legacy_remote=1#token={self.active_token}"


class _LazyRemoteAuth:
    """Create the legacy token manager only when legacy remote auth is actually used."""

    def __init__(self) -> None:
        self._manager: RemoteAuthManager | None = None
        self._lock = threading.Lock()

    def _get(self) -> RemoteAuthManager:
        if self._manager is None:
            with self._lock:
                if self._manager is None:
                    self._manager = RemoteAuthManager()
        return self._manager

    def __getattr__(self, name: str):
        return getattr(self._get(), name)


# Compatibility surface for the standalone legacy --remote server.
# Importing this module no longer creates or persists a token by itself.
REMOTE_AUTH = _LazyRemoteAuth()


def companion_url_for_mode(
    *,
    remote: bool,
    port: int,
    auth_manager: RemoteAuthManager | None = None,
) -> Optional[str]:
    """Resolve the LAN companion URL only when remote access is enabled."""
    if not remote:
        return None
    manager = auth_manager or REMOTE_AUTH
    return manager.get_companion_url(host_ip=detect_local_ip(), port=port)
