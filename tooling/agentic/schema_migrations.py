"""Explicit durable-record migrations for J.A.R.V.I.S. runtime state.

Migrations preserve source uncertainty. They never synthesize authoritative
mission/task identities that were absent from the persisted record.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable

from .models import SCHEMA_VERSION


KNOWN_LEGACY_SCHEMA_VERSIONS = frozenset({"0.9.0"})


class SchemaMigrationError(ValueError):
    """Base class for deterministic durable-record migration failures."""


class UnsupportedSchemaVersionError(SchemaMigrationError):
    """Raised when a record version has no declared migration path."""


class LegacyIdentityMissingError(SchemaMigrationError):
    """Raised when a durable record lacks an identity migration cannot recover."""


def _require_object(record: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(record, dict):
        raise SchemaMigrationError("DURABLE_RECORD_MUST_BE_OBJECT")
    return deepcopy(record)


def _require_identity(record: Dict[str, Any], fields: Iterable[str]) -> None:
    missing = [
        name for name in fields
        if not isinstance(record.get(name), str) or not record.get(name, "").strip()
    ]
    if missing:
        raise LegacyIdentityMissingError(
            "LEGACY_IDENTITY_MISSING:" + ",".join(sorted(missing))
        )


def _source_version(record: Dict[str, Any]) -> str:
    value = record.get("schema_version")
    if not isinstance(value, str) or not value.strip():
        raise UnsupportedSchemaVersionError("MISSING_SCHEMA_VERSION")
    return value.strip()


def _migrate_version(record: Dict[str, Any]) -> Dict[str, Any]:
    source = _source_version(record)
    if source == SCHEMA_VERSION:
        return record
    if source not in KNOWN_LEGACY_SCHEMA_VERSIONS:
        raise UnsupportedSchemaVersionError(
            f"UNSUPPORTED_SCHEMA_VERSION:{source}"
        )
    record["schema_version"] = SCHEMA_VERSION
    record["migration_provenance"] = {
        "source_schema_version": source,
        "target_schema_version": SCHEMA_VERSION,
        "legacy_identity_unknown": False,
        "migration_method": "declared_field_preserving_upgrade",
    }
    return record


def migrate_artifact_record(record: Dict[str, Any]) -> Dict[str, Any]:
    migrated = _require_object(record)
    _require_identity(migrated, ("artifact_id", "mission_id", "task_id", "producer"))
    return _migrate_version(migrated)


def migrate_execution_attempt_record(record: Dict[str, Any]) -> Dict[str, Any]:
    migrated = _require_object(record)
    _require_identity(migrated, ("attempt_id", "mission_id", "task_id"))
    return _migrate_version(migrated)


def migrate_mission_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate a top-level mission envelope before authoritative loading.

    Nested durable objects keep their own migration contracts. This function
    intentionally does not rewrite arbitrary nested ``schema_version`` keys.
    """
    migrated = _require_object(record)
    _require_identity(migrated, ("mission_id",))
    return _migrate_version(migrated)
