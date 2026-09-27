#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. Remote Mobile Companion Authentication & Network Discovery
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
"""

from __future__ import annotations
import json
import os
import secrets
import socket
import stat
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

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
        self.token_file = token_file
        self.active_token: Optional[str] = None
        self.created_at: float = 0
        self._load_or_create_token()

    def _load_or_create_token(self) -> str:
        if self.token_file.exists():
            try:
                if self.token_file.is_symlink() or not self.token_file.is_file():
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
        try:
            self.token_file.parent.mkdir(parents=True, exist_ok=True)
            if self.token_file.exists() and (
                self.token_file.is_symlink() or not self.token_file.is_file()
            ):
                raise ValueError("remote auth token path must be a regular file")

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
        except Exception as e:
            print(f"[JARVIS REMOTE AUTH WARN] Could not persist token: {e}", file=sys.stderr)
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
        return f"http://{ip}:{port}/#token={self.active_token}"


# Global instance
REMOTE_AUTH = RemoteAuthManager()


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
