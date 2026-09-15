"""Durable, context-bound authorization grants for the agentic runtime."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from .config import CONFIG, JarvisRuntimeConfig
from .dag import save_json_atomic
from .models import SCHEMA_VERSION

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class AuthorizationDeniedError(RuntimeError):
    """Raised when an authorization grant cannot authorize the requested action."""


@dataclass(frozen=True)
class AuthorizationDecision:
    valid: bool
    reason: str


def canonical_digest(value: Any) -> str:
    """Return SHA-256 over canonical JSON without guessing non-JSON values."""
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _parse_utc(value: str, field_name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise AuthorizationDeniedError(f"INVALID_{field_name.upper()}") from exc
    if parsed.tzinfo is None:
        raise AuthorizationDeniedError(f"INVALID_{field_name.upper()}")
    return parsed.astimezone(timezone.utc)


def _is_autonomous_identity(identity: str, subject: str) -> bool:
    candidate = identity.strip().lower()
    subject_norm = subject.strip().lower()
    return (
        not candidate
        or candidate == subject_norm
        or candidate == f"agent:{subject_norm}"
        or candidate.startswith("agent:")
        or candidate.startswith("quantum-")
        or candidate.startswith("runtime:")
        or "autonomous" in candidate
    )


def _canonical_scopes(scopes: Iterable[str], registry_root: Path) -> list[str]:
    root = Path(registry_root).resolve()
    canonical: list[str] = []
    for raw_scope in scopes:
        if not isinstance(raw_scope, str) or not raw_scope.strip():
            raise AuthorizationDeniedError("INVALID_SCOPE")
        path = Path(raw_scope)
        resolved = path.resolve() if path.is_absolute() else (root / path).resolve()
        try:
            relative = resolved.relative_to(root)
        except ValueError as exc:
            raise AuthorizationDeniedError("SCOPE_OUTSIDE_REGISTRY") from exc
        canonical.append(relative.as_posix())
    return sorted(set(canonical))


@dataclass
class AuthorizationGrant:
    grant_id: str
    task_id: str
    subject: str
    action: str
    scope_digest: str
    budget_digest: str
    approved_by: str
    issued_utc: str
    expires_utc: str
    revoked_utc: Optional[str] = None
    schema_version: str = SCHEMA_VERSION

    @classmethod
    def issue(
        cls,
        *,
        task_id: str,
        subject: str,
        action: str,
        scopes: Iterable[str],
        budget: Dict[str, Any],
        approved_by: str,
        issued_utc: str,
        expires_utc: str,
        registry_root: str | Path,
        grant_id: Optional[str] = None,
    ) -> "AuthorizationGrant":
        for name, value in (("task_id", task_id), ("subject", subject), ("action", action)):
            if not isinstance(value, str) or not value.strip():
                raise AuthorizationDeniedError(f"INVALID_{name.upper()}")
        if _is_autonomous_identity(approved_by, subject):
            raise AuthorizationDeniedError("SELF_APPROVAL_PROHIBITED")
        if not isinstance(budget, dict):
            raise AuthorizationDeniedError("INVALID_BUDGET")

        _parse_utc(issued_utc, "issued_utc")
        _parse_utc(expires_utc, "expires_utc")
        canonical_scopes = _canonical_scopes(scopes, Path(registry_root))

        return cls(
            grant_id=grant_id or f"grant-{uuid.uuid4().hex[:16]}",
            task_id=task_id.strip(),
            subject=subject.strip(),
            action=action.strip().lower(),
            scope_digest=canonical_digest(canonical_scopes),
            budget_digest=canonical_digest(budget),
            approved_by=approved_by.strip(),
            issued_utc=issued_utc,
            expires_utc=expires_utc,
        )

    def revoke(self, revoked_utc: str) -> None:
        _parse_utc(revoked_utc, "revoked_utc")
        self.revoked_utc = revoked_utc

    def verify(
        self,
        *,
        task_id: str,
        subject: str,
        action: str,
        scopes: Iterable[str],
        budget: Dict[str, Any],
        registry_root: str | Path,
        now_utc: Optional[datetime] = None,
    ) -> AuthorizationDecision:
        if self.schema_version != SCHEMA_VERSION:
            raise AuthorizationDeniedError("UNSUPPORTED_SCHEMA_VERSION")
        if not _SHA256_RE.fullmatch(self.scope_digest or "") or not _SHA256_RE.fullmatch(self.budget_digest or ""):
            raise AuthorizationDeniedError("MALFORMED_DIGEST")
        if self.revoked_utc is not None:
            raise AuthorizationDeniedError("GRANT_REVOKED")

        now = now_utc or datetime.now(timezone.utc)
        if now.tzinfo is None:
            raise AuthorizationDeniedError("INVALID_NOW_UTC")
        now = now.astimezone(timezone.utc)
        if now > _parse_utc(self.expires_utc, "expires_utc"):
            raise AuthorizationDeniedError("GRANT_EXPIRED")

        if task_id != self.task_id:
            raise AuthorizationDeniedError("TASK_MISMATCH")
        if subject != self.subject:
            raise AuthorizationDeniedError("SUBJECT_MISMATCH")
        if not isinstance(action, str) or action.strip().lower() != self.action:
            raise AuthorizationDeniedError("ACTION_MISMATCH")
        if not isinstance(budget, dict):
            raise AuthorizationDeniedError("INVALID_BUDGET")

        scope_digest = canonical_digest(_canonical_scopes(scopes, Path(registry_root)))
        if scope_digest != self.scope_digest:
            raise AuthorizationDeniedError("SCOPE_MISMATCH")
        if canonical_digest(budget) != self.budget_digest:
            raise AuthorizationDeniedError("BUDGET_MISMATCH")

        return AuthorizationDecision(valid=True, reason="AUTHORIZED")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "grant_id": self.grant_id,
            "task_id": self.task_id,
            "subject": self.subject,
            "action": self.action,
            "scope_digest": self.scope_digest,
            "budget_digest": self.budget_digest,
            "approved_by": self.approved_by,
            "issued_utc": self.issued_utc,
            "expires_utc": self.expires_utc,
            "revoked_utc": self.revoked_utc,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuthorizationGrant":
        if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
            raise AuthorizationDeniedError("UNSUPPORTED_SCHEMA_VERSION")
        required = (
            "grant_id", "task_id", "subject", "action", "scope_digest",
            "budget_digest", "approved_by", "issued_utc", "expires_utc",
        )
        if any(not isinstance(data.get(name), str) or not data[name].strip() for name in required):
            raise AuthorizationDeniedError("MALFORMED_GRANT")
        return cls(
            grant_id=data["grant_id"],
            task_id=data["task_id"],
            subject=data["subject"],
            action=data["action"],
            scope_digest=data["scope_digest"],
            budget_digest=data["budget_digest"],
            approved_by=data["approved_by"],
            issued_utc=data["issued_utc"],
            expires_utc=data["expires_utc"],
            revoked_utc=data.get("revoked_utc"),
            schema_version=data["schema_version"],
        )


class AuthorizationGrantStore:
    def __init__(self, config: Optional[JarvisRuntimeConfig] = None):
        self.config = config or CONFIG
        self.directory = self.config.authorizations_dir
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, grant_id: str) -> Path:
        if not isinstance(grant_id, str) or not grant_id.strip():
            raise AuthorizationDeniedError("INVALID_GRANT_ID")
        safe = "".join(ch for ch in grant_id if ch.isalnum() or ch in "-_")
        if safe != grant_id:
            raise AuthorizationDeniedError("INVALID_GRANT_ID")
        return self.directory / f"{safe}.json"

    def save(self, grant: AuthorizationGrant) -> Path:
        if not isinstance(grant, AuthorizationGrant):
            raise TypeError("grant must be an AuthorizationGrant")
        target = self._path(grant.grant_id)
        save_json_atomic(target, grant.to_dict())
        return target

    def load(self, grant_id: str) -> Optional[AuthorizationGrant]:
        target = self._path(grant_id)
        if not target.exists():
            return None
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise AuthorizationDeniedError("MALFORMED_GRANT") from exc
        return AuthorizationGrant.from_dict(data)
