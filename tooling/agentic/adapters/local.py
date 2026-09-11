"""
local.py // J.A.R.V.I.S. Bounded Local Action Adapter
Pure Python 3.12 Standard Library (Zero External PIP Dependencies)

Implements Phase 16 Adapter Contract matching:
docs/schemas/agentic-local-action.schema.json

Guarantees:
- Hard 1 MiB (1,048,576 bytes) UTF-8 byte boundary
- Strict relative canonical path confinement within workspace root
- Traversal protection (no `../` escapes, no absolute Windows paths)
- Protected files & directories (.git, .gitignore, config/api_keys.json)
- Reparse & optimistic concurrency protection via expected_before_sha256
- Atomic write swapping (.tmp -> atomic replace)
- Formal separation of execution action from verification requirements
"""

from __future__ import annotations
import os
import re
import time
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, Tuple

SCHEMA_VERSION = "1.0.0"
MAX_PAYLOAD_BYTES = 1_048_576  # 1 MiB

PROTECTED_PATHS = {
    ".git",
    ".gitignore",
    "config/api_keys.json",
    "state/authoritative",
}


class LocalAdapterType(str, Enum):
    READ_FILE = "local.read_file"
    WRITE_TEXT = "local.write_text"


class LocalActionError(RuntimeError):
    """Raised when LocalAction validation or execution violates security invariants."""
    pass


class ConcurrencyConflictError(LocalActionError):
    """Raised when expected_before_sha256 diverges from actual file content."""
    pass


@dataclass
class LocalAction:
    adapter: LocalAdapterType | str
    path: str
    content: Optional[str] = None
    expected_before_sha256: Optional[str] = None
    approval_id: Optional[str] = None
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise LocalActionError(f"Unsupported schema_version: '{self.schema_version}'. Expected '{SCHEMA_VERSION}'.")

        if isinstance(self.adapter, str):
            try:
                self.adapter = LocalAdapterType(self.adapter)
            except ValueError:
                raise LocalActionError(f"Unsupported adapter: '{self.adapter}'. Must be one of {[a.value for a in LocalAdapterType]}")
        elif not isinstance(self.adapter, LocalAdapterType):
            raise LocalActionError(f"Unsupported adapter type: {type(self.adapter)}")

        if not isinstance(self.path, str) or not self.path.strip():
            raise LocalActionError("path must be a non-empty relative string")

        # Canonical relative path enforcement
        clean_path = self.path.replace("\\", "/").strip()
        if clean_path.startswith("/") or re.match(r"^[a-zA-Z]:", clean_path):
            raise LocalActionError(f"Path must be relative to workspace root, got absolute: '{self.path}'")

        parts = clean_path.split("/")
        if ".." in parts:
            raise LocalActionError(f"Directory traversal ('..') prohibited in path: '{self.path}'")

        # Adapter-specific schema invariants
        if self.adapter == LocalAdapterType.WRITE_TEXT:
            if self.content is None or not isinstance(self.content, str):
                raise LocalActionError("content string is strictly required for local.write_text")
            content_bytes = len(self.content.encode("utf-8"))
            if content_bytes > MAX_PAYLOAD_BYTES:
                raise LocalActionError(f"Payload size {content_bytes} bytes exceeds hard 1 MiB limit ({MAX_PAYLOAD_BYTES} bytes)")

            if self.expected_before_sha256 is not None:
                if not re.match(r"^[a-f0-9]{64}$", self.expected_before_sha256.lower()):
                    raise LocalActionError(f"Invalid expected_before_sha256 format: '{self.expected_before_sha256}'")
                self.expected_before_sha256 = self.expected_before_sha256.lower()

        elif self.adapter == LocalAdapterType.READ_FILE:
            if self.content is not None:
                raise LocalActionError("content must not be provided for local.read_file")
            if self.expected_before_sha256 is not None:
                raise LocalActionError("expected_before_sha256 must not be provided for local.read_file")

        if self.approval_id is not None:
            if not re.match(r"^app-[a-f0-9]{12}$", self.approval_id):
                raise LocalActionError(f"Invalid approval_id format: '{self.approval_id}'")

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "schema_version": self.schema_version,
            "adapter": self.adapter.value if isinstance(self.adapter, LocalAdapterType) else str(self.adapter),
            "path": self.path
        }
        if self.content is not None:
            d["content"] = self.content
        if self.expected_before_sha256 is not None:
            d["expected_before_sha256"] = self.expected_before_sha256
        if self.approval_id is not None:
            d["approval_id"] = self.approval_id
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LocalAction:
        if not isinstance(data, dict):
            raise LocalActionError("Action data must be a dictionary")
        return cls(
            adapter=data.get("adapter", ""),
            path=data.get("path", ""),
            content=data.get("content"),
            expected_before_sha256=data.get("expected_before_sha256"),
            approval_id=data.get("approval_id"),
            schema_version=data.get("schema_version", SCHEMA_VERSION)
        )


@dataclass
class LocalActionResult:
    success: bool
    adapter: str
    path: str
    exit_code: int
    bytes_transferred: int
    sha256: str
    duration_ms: float
    content: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "adapter": self.adapter,
            "path": self.path,
            "exit_code": self.exit_code,
            "bytes_transferred": self.bytes_transferred,
            "sha256": self.sha256,
            "duration_ms": self.duration_ms,
            "content_snippet": (self.content[:200] + "...") if self.content and len(self.content) > 200 else self.content,
            "error_message": self.error_message
        }


class LocalActionAdapter:
    """
    Sovereign executor for bounded local file operations.
    Enforces sandbox containment, atomic write guarantees, and concurrency checks.
    """

    def __init__(self, workspace_root: Path):
        self.root = workspace_root.resolve()

    def resolve_confined_path(self, relative_path: str) -> Path:
        """Resolves path and enforces strict confinement under workspace root."""
        clean = relative_path.replace("\\", "/").strip().lstrip("/")
        # Check protected paths
        for prot in PROTECTED_PATHS:
            if clean == prot or clean.startswith(f"{prot}/"):
                raise LocalActionError(f"Access to protected path '{clean}' is strictly prohibited")

        resolved = (self.root / clean).resolve()
        try:
            common = os.path.commonpath([str(self.root), str(resolved)])
            if common != str(self.root):
                raise LocalActionError(f"Path '{relative_path}' escapes workspace root '{self.root}'")
        except Exception as e:
            raise LocalActionError(f"Failed path confinement check: {e}")

        return resolved

    def execute(self, action: LocalAction | Dict[str, Any]) -> LocalActionResult:
        """Executes a bounded LocalAction deterministically."""
        t0 = time.perf_counter()
        if isinstance(action, dict):
            parsed_action = LocalAction.from_dict(action)
        elif isinstance(action, LocalAction):
            parsed_action = action
        else:
            raise LocalActionError("action must be a LocalAction instance or dictionary")

        target_file = self.resolve_confined_path(parsed_action.path)

        if parsed_action.adapter == LocalAdapterType.READ_FILE:
            if not target_file.exists():
                duration = round((time.perf_counter() - t0) * 1000.0, 3)
                return LocalActionResult(
                    success=False,
                    adapter=parsed_action.adapter.value,
                    path=parsed_action.path,
                    exit_code=1,
                    bytes_transferred=0,
                    sha256="",
                    duration_ms=duration,
                    error_message=f"File not found: '{parsed_action.path}'"
                )

            if not target_file.is_file():
                duration = round((time.perf_counter() - t0) * 1000.0, 3)
                return LocalActionResult(
                    success=False,
                    adapter=parsed_action.adapter.value,
                    path=parsed_action.path,
                    exit_code=1,
                    bytes_transferred=0,
                    sha256="",
                    duration_ms=duration,
                    error_message=f"Path is not a regular file: '{parsed_action.path}'"
                )

            size = target_file.stat().st_size
            if size > MAX_PAYLOAD_BYTES:
                duration = round((time.perf_counter() - t0) * 1000.0, 3)
                return LocalActionResult(
                    success=False,
                    adapter=parsed_action.adapter.value,
                    path=parsed_action.path,
                    exit_code=1,
                    bytes_transferred=size,
                    sha256="",
                    duration_ms=duration,
                    error_message=f"File size {size} bytes exceeds 1 MiB bound"
                )

            data_bytes = target_file.read_bytes()
            content_str = data_bytes.decode("utf-8", errors="replace")
            content_hash = hashlib.sha256(data_bytes).hexdigest()
            duration = round((time.perf_counter() - t0) * 1000.0, 3)

            return LocalActionResult(
                success=True,
                adapter=parsed_action.adapter.value,
                path=parsed_action.path,
                exit_code=0,
                bytes_transferred=len(data_bytes),
                sha256=content_hash,
                duration_ms=duration,
                content=content_str
            )

        elif parsed_action.adapter == LocalAdapterType.WRITE_TEXT:
            # Concurrency / optimistic check
            if parsed_action.expected_before_sha256 is not None:
                if not target_file.exists():
                    duration = round((time.perf_counter() - t0) * 1000.0, 3)
                    raise ConcurrencyConflictError(
                        f"Expected file to exist with SHA-256 {parsed_action.expected_before_sha256}, but file does not exist: '{parsed_action.path}'"
                    )
                existing_hash = hashlib.sha256(target_file.read_bytes()).hexdigest()
                if existing_hash.lower() != parsed_action.expected_before_sha256.lower():
                    duration = round((time.perf_counter() - t0) * 1000.0, 3)
                    raise ConcurrencyConflictError(
                        f"Concurrency Conflict: Target SHA-256 is {existing_hash}, expected {parsed_action.expected_before_sha256}"
                    )

            # Ensure parent directories
            target_file.parent.mkdir(parents=True, exist_ok=True)

            # Atomic write (.tmp -> replace)
            payload_bytes = parsed_action.content.encode("utf-8")
            tmp_file = target_file.with_name(f"{target_file.name}.tmp.{os.getpid()}")
            try:
                tmp_file.write_bytes(payload_bytes)
                tmp_file.replace(target_file)
            finally:
                if tmp_file.exists():
                    tmp_file.unlink(missing_ok=True)

            content_hash = hashlib.sha256(payload_bytes).hexdigest()
            duration = round((time.perf_counter() - t0) * 1000.0, 3)

            return LocalActionResult(
                success=True,
                adapter=parsed_action.adapter.value,
                path=parsed_action.path,
                exit_code=0,
                bytes_transferred=len(payload_bytes),
                sha256=content_hash,
                duration_ms=duration,
                content=parsed_action.content
            )

        raise LocalActionError(f"Unhandled adapter: {parsed_action.adapter}")
