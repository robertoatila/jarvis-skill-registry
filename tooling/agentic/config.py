"""
config.py // J.A.R.V.I.S. Canonical Runtime Configuration
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
"""

from __future__ import annotations
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

DEFAULT_ROOT = Path("E:/.skill-registry").resolve()


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
    learning_dir: Path = field(init=False)
    corrupted_dir: Path = field(init=False)
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
        self.learning_dir = self.state_dir / "learning"
        self.corrupted_dir = self.state_dir / "corrupted"
        self.cache_dir = self.registry_root / "cache"
        self.config_dir = self.registry_root / "config"
        self.reports_dir = self.registry_root / "reports"

    def ensure_directories(self) -> None:
        for path in (
            self.state_dir,
            self.missions_dir,
            self.checkpoints_dir,
            self.telemetry_dir,
            self.learning_dir,
            self.corrupted_dir,
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


def load_config(root_override: Optional[Path] = None) -> JarvisRuntimeConfig:
    env_root = os.environ.get("JARVIS_REGISTRY_ROOT")
    if root_override:
        root_path = Path(root_override)
    elif env_root:
        root_path = Path(env_root)
    else:
        root_path = DEFAULT_ROOT

    config = JarvisRuntimeConfig(registry_root=root_path)
    config.ensure_directories()
    return config


CONFIG = load_config()
