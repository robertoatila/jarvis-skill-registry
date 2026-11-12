"""
config.py // J.A.R.V.I.S. Canonical Runtime Configuration
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
"""

from __future__ import annotations
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Mapping, Optional, Dict, Any

DEFAULT_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Locations outside the checkout.
#
# Every path that is not inside the registry is resolved here, from an
# environment variable first, so no module carries a drive letter of its own.
# ---------------------------------------------------------------------------
ARSENAL_HOME_ENV = "JARVIS_ARSENAL_HOME"
GEMINI_ROOT_ENV = "GEMINI_ROOT"
# Where the arsenal lived before it became configurable.  It stays the Windows
# default so an existing installation keeps working without new settings.
LEGACY_WINDOWS_ARSENAL_HOME = "D:/Program Files/jarvis-arsenal"
DEFAULT_POSIX_ARSENAL_DIRNAME = ".jarvis-arsenal"


def _is_windows(windows: Optional[bool]) -> bool:
    return (os.name == "nt") if windows is None else bool(windows)


def external_arsenal_home(
    environ: Optional[Mapping[str, str]] = None, *, windows: Optional[bool] = None
) -> Path:
    """Directory of the optional arsenal kept outside the checkout.

    Order: ``JARVIS_ARSENAL_HOME``; the legacy location on Windows;
    ``~/.jarvis-arsenal`` elsewhere.  The directory is optional and is never
    created by this function; callers check for existence.
    """
    env = os.environ if environ is None else environ
    configured = (env.get(ARSENAL_HOME_ENV) or "").strip()
    if configured:
        return Path(configured).expanduser()
    if _is_windows(windows):
        return Path(LEGACY_WINDOWS_ARSENAL_HOME)
    return Path.home() / DEFAULT_POSIX_ARSENAL_DIRNAME


def external_arsenal_db_path(
    environ: Optional[Mapping[str, str]] = None, *, windows: Optional[bool] = None
) -> Path:
    """Path of the optional external arsenal database (it may not exist)."""
    return external_arsenal_home(environ, windows=windows) / "data" / "arsenal_library.sqlite"


def external_rf_model_path(
    environ: Optional[Mapping[str, str]] = None, *, windows: Optional[bool] = None
) -> Path:
    """Path of the optional external classifier model (it may not exist)."""
    return external_arsenal_home(environ, windows=windows) / "models" / "random_forest_model.json"


def external_arsenal_mirror_enabled(
    environ: Optional[Mapping[str, str]] = None, *, windows: Optional[bool] = None
) -> bool:
    """Whether a tool may write a mirror into the external arsenal.

    True only when the operator named the location explicitly or the directory
    already exists, so no tool creates a directory tree on a machine that
    never had one.
    """
    env = os.environ if environ is None else environ
    if (env.get(ARSENAL_HOME_ENV) or "").strip():
        return True
    try:
        return external_arsenal_home(environ, windows=windows).is_dir()
    except OSError:
        return False


def gemini_root(environ: Optional[Mapping[str, str]] = None) -> Path:
    """Root of the optional IDE configuration tree (``GEMINI_ROOT`` or ``~/.gemini``)."""
    env = os.environ if environ is None else environ
    configured = (env.get(GEMINI_ROOT_ENV) or "").strip()
    return Path(configured).expanduser() if configured else Path.home() / ".gemini"


@dataclass
class JarvisRuntimeConfig:
    registry_root: Path = field(default_factory=lambda: DEFAULT_ROOT)
    security_mode: str = "FAIL_CLOSED"
    default_timeout_seconds: float = 60.0
    max_parallel_tasks: int = 4
    approval_timeout_seconds: float = 300.0
    offline_only: bool = True

    # Derived path directories
    skills_dir: Path = field(init=False)
    state_dir: Path = field(init=False)
    missions_dir: Path = field(init=False)
    checkpoints_dir: Path = field(init=False)
    telemetry_dir: Path = field(init=False)
    receipts_dir: Path = field(init=False)
    learning_dir: Path = field(init=False)
    corrupted_dir: Path = field(init=False)
    authorizations_dir: Path = field(init=False)
    cache_dir: Path = field(init=False)
    config_dir: Path = field(init=False)
    reports_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        self.registry_root = self.registry_root.resolve()
        self.skills_dir = self.registry_root / "skills"
        self.state_dir = self.registry_root / "state"
        self.missions_dir = self.state_dir / "missions"
        self.checkpoints_dir = self.state_dir / "checkpoints"
        self.telemetry_dir = self.state_dir / "telemetry"
        self.receipts_dir = self.state_dir / "receipts"
        self.learning_dir = self.state_dir / "learning"
        self.corrupted_dir = self.state_dir / "corrupted"
        self.authorizations_dir = self.state_dir / "authorizations"
        self.cache_dir = self.registry_root / "cache"
        self.config_dir = self.registry_root / "config"
        self.reports_dir = self.registry_root / "reports"

    def ensure_directories(self) -> None:
        for path in (
            self.state_dir,
            self.missions_dir,
            self.checkpoints_dir,
            self.telemetry_dir,
            self.receipts_dir,
            self.learning_dir,
            self.corrupted_dir,
            self.authorizations_dir,
            self.cache_dir
        ):
            path.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "registry_root": str(self.registry_root),
            "security_mode": self.security_mode,
            "default_timeout_seconds": self.default_timeout_seconds,
            "max_parallel_tasks": self.max_parallel_tasks,
            "approval_timeout_seconds": self.approval_timeout_seconds,
            "offline_only": self.offline_only
        }


def load_config(root_override: Optional[Path] = None, ensure_dirs: bool = False) -> JarvisRuntimeConfig:
    env_root = os.environ.get("JARVIS_REGISTRY_ROOT")
    if root_override:
        root_path = Path(root_override)
    elif env_root:
        root_path = Path(env_root)
    else:
        root_path = DEFAULT_ROOT

    config = JarvisRuntimeConfig(registry_root=root_path)
    if ensure_dirs:
        config.ensure_directories()
    return config


CONFIG = load_config(ensure_dirs=False)