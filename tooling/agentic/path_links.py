"""Link detection that behaves the same on every supported Python version.

``Path.is_junction()`` exists only on Python 3.12+.  Guarding the call with
``hasattr`` keeps older interpreters from crashing, but it also means that on
Windows with Python 3.10/3.11 a directory junction is not detected at all, so
a confinement check that refuses "linked" paths silently lets a junction
through.  :func:`is_junction` reads the reparse tag directly, which is what
the 3.12 implementation does, and therefore gives the same answer on 3.10+.

Scope: a junction is a Windows concept; on other platforms the function
returns False.  The Windows branch is exercised here through a substituted
``os.lstat`` result, not on a Windows host.

Pure Python standard library.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Union

__all__ = ["IO_REPARSE_TAG_MOUNT_POINT", "is_junction", "is_link"]

# Reparse tag of a directory junction (winnt.h); ``stat.IO_REPARSE_TAG_MOUNT_POINT``
# carries the same value but is only defined on Windows builds.
IO_REPARSE_TAG_MOUNT_POINT = 0xA0000003

PathLike = Union[str, "os.PathLike[str]", Path]


def is_junction(path: PathLike) -> bool:
    """True when ``path`` is a Windows directory junction (never raises)."""
    try:
        status = os.lstat(path)
    except (OSError, ValueError, TypeError):
        return False
    return getattr(status, "st_reparse_tag", 0) == IO_REPARSE_TAG_MOUNT_POINT


def is_link(path: PathLike) -> bool:
    """True when ``path`` is a symbolic link or a directory junction."""
    try:
        if os.path.islink(path):
            return True
    except (OSError, ValueError, TypeError):
        return False
    return is_junction(path)
