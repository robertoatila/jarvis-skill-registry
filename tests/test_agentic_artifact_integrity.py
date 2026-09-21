"""Artifact integrity and freshness regression tests."""

import tempfile
import unittest
from pathlib import Path

from tooling.agentic.config import JarvisRuntimeConfig
from tooling.agentic.dag import ExecutionDAG
from tooling.agentic.models import (
    Artifact,
    ArtifactType,
    Mission,
    RiskLevel,
    TaskNode,
    TaskStatus,
    VerificationRequirement,
    VerificationType,
)
from tooling.agentic.runtime import JarvisAgenticRuntime


class TestArtifactSealIntegrity(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.config = JarvisRuntimeConfig(registry_root=self.root)
        self.config.ensure_directories()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_compute_hash_rejects_target_outside_workspace_boundary(self):
        outside_dir = tempfile.TemporaryDirectory()
        try:
            outside = Path(outside_dir.name) / "outside.txt"
            outside.write_text("private", encoding="utf-8")
            artifact = Artifact(
                artifact_id="art-outside",
                mission_id="mis-artifact-boundary",
                task_id="tsk-artifact-boundary",
                producer="test",
                artifact_type=ArtifactType.OTHER,
                path=str(outside),
            )

            self.assertEqual(artifact.compute_hash(base_dir=self.root), "")
            self.assertEqual(artifact.sha256, "")
            self.assertFalse(artifact.seal_verification(self.root))
            self.assertEqual(artifact.verification_state, "FAILED")
        finally:
            outside_dir.cleanup()

    def test_seal_rejects_hash_or_size_drift(self):
        target = self.root / "artifact.txt"
        target.write_text("original", encoding="utf-8")
        artifact = Artifact(
            artifact_id="art-drift",
            mission_id="mis-artifact-drift",
            task_id="tsk-artifact-drift",
            producer="test",
            path="artifact.txt",
        )
        captured = artifact.compute_hash(base_dir=self.root)
        self.assertTrue(captured)

        target.write_text("tampered-after-capture", encoding="utf-8")

        self.assertFalse(artifact.seal_verification(self.root))
        self.assertEqual(artifact.sha256, captured)
        self.assertEqual(artifact.verification_state, "FAILED")

    def test_runtime_fails_task_when_artifact_changes_after_requirement_check(self):
        runtime = JarvisAgenticRuntime(config=self.config)
        target = self.root / "output.txt"

        task = TaskNode(
            task_id="tsk-artifact-seal",
            title="Artifact seal drift",
            agent_profile="Quantum-ExecutorAgent",
            risk_level=RiskLevel.R1_LOCAL_WRITE,
            write_scopes=[str(target)],
        )
        task.action = {
            "adapter": "local.write_text",
            "path": "output.txt",
            "content": "captured-by-runtime",
        }
        task.verification_requirements.append(
            VerificationRequirement(
                check_type=VerificationType.FILE_EXISTS,
                target="output.txt",
            )
        )
        mission = Mission(mission_id="mis-artifact-seal", goal="Artifact seal integrity")
        dag = ExecutionDAG()
        dag.add_node(task)
        mission.dag = dag

        original_verify = runtime.verification.verify_task

        def verify_then_tamper(task_node, base_dir=None):
            result = original_verify(task_node, base_dir=base_dir)
            if result:
                target.write_text("changed-after-verification", encoding="utf-8")
            return result

        runtime.verification.verify_task = verify_then_tamper
        result = runtime.execute_goal(mission)

        self.assertEqual(result["status"], "FAILED")
        reloaded = runtime.load_mission(mission.mission_id)
        task_out = reloaded.dag.nodes[task.task_id]
        self.assertEqual(task_out.status, TaskStatus.FAILED)
        self.assertEqual(len(task_out.artifacts), 1)
        self.assertEqual(task_out.artifacts[0].verification_state, "FAILED")
        self.assertNotEqual(
            task_out.artifacts[0].sha256,
            __import__("hashlib").sha256(target.read_bytes()).hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
