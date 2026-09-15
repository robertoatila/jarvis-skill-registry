"""v0.2.0 contracts for explicit, uncertainty-preserving durable migrations."""

from __future__ import annotations

import importlib
import json
import tempfile
import unittest
from pathlib import Path

from tooling.agentic.config import JarvisRuntimeConfig
from tooling.agentic.dag import ExecutionDAG
from tooling.agentic.models import Artifact, ArtifactType, ExecutionAttempt, Mission, SCHEMA_VERSION, TaskNode
from tooling.agentic.state_store import AuthoritativeStateStore


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
        with self.assertRaises((ValueError, KeyError)):
            Artifact.from_dict(artifact)
        with self.assertRaises((ValueError, KeyError)):
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

    def test_state_store_migrates_supported_nested_durable_records(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = JarvisRuntimeConfig(registry_root=root)
            config.ensure_directories()
            store = AuthoritativeStateStore(config=config)

            task = TaskNode(task_id="tsk-nested", title="Nested legacy records")
            task.artifacts.append(Artifact(
                artifact_id="art-nested",
                mission_id="mis-nested",
                task_id=task.task_id,
                producer="fixture",
                artifact_type=ArtifactType.OTHER,
                path="out.txt",
            ))
            task.record_attempt(ExecutionAttempt(
                attempt_id="att-nested",
                mission_id="mis-nested",
                task_id=task.task_id,
            ))
            dag = ExecutionDAG()
            dag.add_node(task)
            mission = Mission(mission_id="mis-nested", goal="Nested migration", dag=dag)
            legacy = mission.to_dict()
            legacy["schema_version"] = "0.9.0"
            legacy_task = legacy["dag"]["nodes"][0]
            legacy_task["artifacts"][0]["schema_version"] = "0.9.0"
            legacy_task["attempts"][0]["schema_version"] = "0.9.0"

            path = store.get_mission_path(mission.mission_id)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(legacy), encoding="utf-8")

            restored = store.load_mission(mission.mission_id)
            self.assertIsNotNone(restored)
            restored_task = restored.dag.nodes[task.task_id]
            self.assertEqual(restored_task.artifacts[0].mission_id, mission.mission_id)
            self.assertEqual(restored_task.artifacts[0].task_id, task.task_id)
            self.assertEqual(restored_task.attempts[0].mission_id, mission.mission_id)
            self.assertEqual(restored_task.attempts[0].task_id, task.task_id)

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
