"""
test_agentic_hud.py // Unit and Integration Tests for Phase 07 (Runtime HUD + Agent Graph)
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
"""

import unittest
import json
from tooling.agentic.telemetry import TELEMETRY, TokenUsage
from tooling.agentic.dag import ExecutionDAG
from tooling.agentic.models import TaskNode, TaskStatus
from tooling.agentic.scheduler import WaveScheduler


class TestAgenticHUD(unittest.TestCase):

    def test_hud_telemetry_endpoint_data(self):
        # Record a span
        span = TELEMETRY.start_span("HUD-M1", "task_hud", "Quantum-VisualizerAgent", "frontend-ui-engineering")
        TELEMETRY.finish_span(
            span.span_id,
            status="SUCCESS",
            token_usage=TokenUsage(prompt_tokens=80, completion_tokens=40, total_tokens=120),
            tool_calls_count=1
        )

        metrics = TELEMETRY.get_metrics_summary()
        self.assertIn("success_rate", metrics)
        self.assertIn("avg_duration_ms", metrics)
        self.assertIn("total_spans", metrics)
        self.assertGreater(metrics["total_spans"], 0)

    def test_hud_dag_graph_structure(self):
        dag = ExecutionDAG()
        dag.add_node(TaskNode(task_id="Plan", title="Architecture Plan", agent_profile="Quantum-AuditAgent"))
        dag.add_node(TaskNode(task_id="Code", title="Synthesis", agent_profile="Quantum-SynthesisAgent", dependencies=["Plan"]))
        dag.add_node(TaskNode(task_id="Audit", title="Security Audit", agent_profile="Quantum-AuditAgent", dependencies=["Code"]))

        scheduler = WaveScheduler()
        waves = scheduler.schedule(dag)

        schedule_dict = scheduler.to_schedule_dict("HUD-MISSION-01", waves)
        self.assertEqual(schedule_dict["total_waves"], 3)
        self.assertEqual(len(schedule_dict["waves"]), 3)
        self.assertEqual(schedule_dict["waves"][0]["task_ids"], ["Plan"])
        self.assertEqual(schedule_dict["waves"][1]["task_ids"], ["Code"])
        self.assertEqual(schedule_dict["waves"][2]["task_ids"], ["Audit"])


if __name__ == "__main__":
    unittest.main()
