import tempfile
import unittest
from pathlib import Path

from tooling.agentic.adapters.local import LocalAction, LocalAdapterType
from tooling.agentic.context_governor import ContextGovernor
from tooling.agentic.dag import ExecutionDAG
from tooling.agentic.models import (
    Mission,
    RiskLevel,
    TaskNode,
    TaskStatus,
    VerificationRequirement,
    VerificationType,
)
from tooling.agentic.runtime import JarvisAgenticRuntime
from tooling.agentic.tool_router import ToolCandidate


class TestCognitiveContractClosure(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name).resolve()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _mission(self, mission_id, task):
        dag = ExecutionDAG()
        dag.add_node(task)
        return Mission(mission_id=mission_id, goal=mission_id, dag=dag)

    def test_context_governor_rejects_escape_and_supports_bounded_reuse(self):
        (self.root / "note.txt").write_text("important verified content", encoding="utf-8")
        governor = ContextGovernor(self.root)

        with self.assertRaises(ValueError):
            governor.read_with_receipt("../outside.txt")

        full, first = governor.read_with_receipt("note.txt")
        reference, second = governor.read_with_receipt("note.txt", delivery_mode="reference")
        self.assertEqual(full, "important verified content")
        self.assertTrue(second.cache_hit)
        self.assertEqual(second.delivery_mode, "reference")
        self.assertTrue(reference.startswith("sha256:"))
        self.assertEqual(first.provenance["source"], "workspace")

    def test_governor_state_is_isolated_per_mission(self):
        runtime = JarvisAgenticRuntime(registry_root=self.root)
        runtime.cognitive_governor.max_consecutive_repeats = 2

        def command_task(task_id):
            action = LocalAction(
                adapter=LocalAdapterType.WRITE_TEXT,
                path=f"output_{task_id}.txt",
                content="ok",
            )
            return TaskNode(
                task_id=task_id,
                title="Same action",
                agent_profile="Quantum-ExecutorAgent",
                required_skills=["general"],
                action=action.to_dict(),
                risk_level=RiskLevel.R1_LOCAL_WRITE,
                write_scopes=[f"output_{task_id}.txt"],
                verification_requirements=[
                    VerificationRequirement(
                        check_type=VerificationType.FILE_EXISTS,
                        target=f"output_{task_id}.txt",
                    )
                ],
            )

        first = runtime.execute_goal(self._mission("msn-isolation-1", command_task("tsk-one")))
        second = runtime.execute_goal(self._mission("msn-isolation-2", command_task("tsk-two")))
        self.assertEqual(first["status"], "SUCCESS")
        self.assertEqual(second["status"], "SUCCESS")

    def test_missing_executor_fails_closed(self):
        runtime = JarvisAgenticRuntime(registry_root=self.root)
        task = TaskNode(
            task_id="tsk-unbound",
            title="No concrete action",
            agent_profile="Quantum-ExecutorAgent",
            required_skills=["general-execution"],
        )
        mission = self._mission("msn-unbound", task)

        result = runtime.execute_goal(mission)

        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(task.status, TaskStatus.FAILED)
        self.assertFalse(task.execution_result["executed"])
        self.assertEqual(task.execution_result["exit_code"], 127)
        self.assertEqual(task.execution_result["execution_binding"]["status"], "UNBOUND")

    def test_routed_tool_is_bound_to_actual_executor_and_attempt(self):
        runtime = JarvisAgenticRuntime(registry_root=self.root)
        action = LocalAction(
            adapter=LocalAdapterType.WRITE_TEXT,
            path="output.txt",
            content="verified",
        )
        task = TaskNode(
            task_id="tsk-bound",
            title="Bound write",
            agent_profile="Quantum-ExecutorAgent",
            required_skills=["general"],
            action=action.to_dict(),
            risk_level=RiskLevel.R1_LOCAL_WRITE,
            write_scopes=["output.txt"],
            verification_requirements=[
                VerificationRequirement(
                    check_type=VerificationType.FILE_EXISTS,
                    target="output.txt",
                )
            ],
        )
        mission = self._mission("msn-bound", task)

        result = runtime.execute_goal(mission)

        self.assertEqual(result["status"], "SUCCESS")
        binding = task.execution_result["execution_binding"]
        self.assertEqual(binding["status"], "BOUND")
        self.assertEqual(binding["tool_id"], "local.write_text")
        self.assertEqual(task.attempts[0].tool_id, binding["tool_id"])
        self.assertEqual(task.attempts[0].budget_consumed["tokens"], 0)
        self.assertEqual(
            task.attempts[0].budget_consumed["token_measurement"],
            "MEASURED_NO_MODEL_INVOCATION",
        )

    def test_tool_candidate_requires_every_capability(self):
        tool = ToolCandidate(
            tool_id="example",
            name="Example",
            capabilities=["read_file"],
        )
        self.assertFalse(tool.matches_capabilities(["read_file", "write_file"]))


if __name__ == "__main__":
    unittest.main()
