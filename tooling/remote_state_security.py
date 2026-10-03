"""Shared filesystem-safety predicates for durable remote runtime state."""

from __future__ import annotations

import os
import stat
from pathlib import Path


_REPARSE_POINT_FLAG = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def _is_link_or_reparse(path: Path) -> bool:
    candidate = Path(path)
    try:
        info = os.lstat(candidate)
    except FileNotFoundError:
        return False
    except OSError:
        # If an existing component cannot be inspected safely, fail closed.
        return True
    if stat.S_ISLNK(info.st_mode):
        return True
    attributes = getattr(info, "st_file_attributes", 0)
    return bool(attributes & _REPARSE_POINT_FLAG)


def _has_unsafe_component(path: Path) -> bool:
    """Reject symlink/reparse points anywhere in the lexical path chain."""
    current = Path(path)
    while True:
        if _is_link_or_reparse(current):
            return True
        parent = current.parent
        if parent == current:
            return False
        current = parent


def safe_state_directory(path: Path) -> bool:
    candidate = Path(path)
    if _has_unsafe_component(candidate):
        return False
    try:
        return candidate.is_dir() if candidate.exists() else True
    except OSError:
        return False


def safe_state_file(path: Path) -> bool:
    candidate = Path(path)
    if _has_unsafe_component(candidate):
        return False
    try:
        return candidate.is_file() if candidate.exists() else True
    except OSError:
        return False


def secure_state_directory(path: Path) -> bool:
    """Create/tighten a remote state directory without traversing links/reparse points."""
    candidate = Path(path)
    if _has_unsafe_component(candidate):
        return False
    try:
        candidate.mkdir(mode=0o700, parents=True, exist_ok=True)
    except OSError:
        return False
    if not safe_state_directory(candidate):
        return False
    if os.name != "nt":
        try:
            os.chmod(candidate, 0o700)
        except OSError:
            return False
    return True
