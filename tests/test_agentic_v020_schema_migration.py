"""v0.2.0 contracts for explicit, uncertainty-preserving durable migrations."""

from __future__ import annotations

import importlib
import unittest

from tooling.agentic.models import Artifact, ArtifactType, ExecutionAttempt, SCHEMA_VERSION


class TestV020SchemaMigration(unittest.TestCase):
    def _migrations(self):
        try:
            return importlib.import_module("tooling.agentic.schema_migrations")
        except ModuleNotFoundError as exc:
            self.fail(f"schema migration registry is missing: {exc}")

    def test_legacy_artifact_without_authoritative_identity_is_rejected(self):
        migrations = self._migrations()
        legacy = {
            "schema_version": SCHEMA_VERSION,
            "artifact_id": "art-legacy",
            "producer": "legacy",
            "path": "legacy.txt",
        }
        with self.assertRaises(migrations.LegacyIdentityMissingError):
            migrations.migrate_artifact_record(legacy)

    def test_models_do_not_synthesize_legacy_mission_or_task_ids(self):
        artifact = {
            "schema_version": SCHEMA_VERSION,
            "artifact_id": "art-legacy",
            "producer": "legacy",
        }
        attempt = {
            "schema_version": SCHEMA_VERSION,
            "attempt_id": "att-legacy",
        }
        with self.assertRaises(ValueError):
            Artifact.from_dict(artifact)
        with self.assertRaises(ValueError):
            ExecutionAttempt.from_dict(attempt)

    def test_known_older_artifact_schema_migrates_deterministically(self):
        migrations = self._migrations()
        legacy = {
            "schema_version": "0.9.0",
            "artifact_id": "art-001",
            "mission_id": "mis-001",
            "task_id": "tsk-001",
            "producer": "fixture",
            "artifact_type": "other",
            "path": "out.txt",
        }
        first = migrations.migrate_artifact_record(legacy)
        second = migrations.migrate_artifact_record(legacy)
        self.assertEqual(first, second)
        self.assertEqual(first["schema_version"], SCHEMA_VERSION)
        self.assertEqual(first["mission_id"], "mis-001")
        self.assertEqual(first["task_id"], "tsk-001")
        provenance = first.get("migration_provenance")
        self.assertIsInstance(provenance, dict)
        self.assertEqual(provenance.get("source_schema_version"), "0.9.0")
        self.assertEqual(provenance.get("target_schema_version"), SCHEMA_VERSION)
        self.assertFalse(provenance.get("legacy_identity_unknown", True))

    def test_unknown_newer_schema_is_rejected_not_guessed(self):
        migrations = self._migrations()
        payload = {
            "schema_version": "99.0.0",
            "artifact_id": "art-future",
            "mission_id": "mis-future",
            "task_id": "tsk-future",
            "producer": "future",
        }
        with self.assertRaises(migrations.UnsupportedSchemaVersionError):
            migrations.migrate_artifact_record(payload)

    def test_current_artifact_round_trip_is_stable(self):
        artifact = Artifact(
            artifact_id="art-current",
            mission_id="mis-current",
            task_id="tsk-current",
            producer="fixture",
            artifact_type=ArtifactType.OTHER,
            path="fixture.txt",
        )
        encoded = artifact.to_dict()
        restored = Artifact.from_dict(encoded)
        self.assertEqual(restored.to_dict(), encoded)

    def test_current_attempt_round_trip_is_stable(self):
        attempt = ExecutionAttempt(
            attempt_id="att-current",
            mission_id="mis-current",
            task_id="tsk-current",
        )
        encoded = attempt.to_dict()
        restored = ExecutionAttempt.from_dict(encoded)
        self.assertEqual(restored.to_dict(), encoded)


if __name__ == "__main__":
    unittest.main()
