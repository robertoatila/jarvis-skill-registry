"""Shared filesystem-safety predicates for durable remote runtime state."""

from __future__ import annotations

from pathlib import Path


def safe_state_directory(path: Path) -> bool:
    candidate = Path(path)
    if candidate.is_symlink():
        return False
    if candidate.exists():
        return candidate.is_dir()
    return True


def safe_state_file(path: Path) -> bool:
    candidate = Path(path)
    if candidate.is_symlink():
        return False
    if candidate.exists():
        return candidate.is_file()
    return True
