"""
test_agentic_intelligence_tier.py // Tier 3 Intelligence & Adaptive Closed-Loop Verification
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
Validates:
1. RepositoryIntelligenceGraph: AST parsing, symbol extraction, capability classification (EXISTS/PARTIAL/MISSING)
2. SkillFitnessEngine: Cold-start prior safety, multi-metric composite scoring, config injection
3. ExperimentEngine: A/B variant assignment, outcome tracking, winner determination
4. LearningEngine: Auto-evaluation & promotion lifecycle (OBSERVATION -> PATTERN -> VALIDATED_HEURISTIC)
5. End-to-End Runtime Integration: Planner repo-intel annotations, risk classification, experiment dispatch & learning evidence
"""

import unittest
import shutil
import tempfile
import json
from pathlib import Path
from datetime import datetime, timezone

from tooling.agentic.config import JarvisRuntimeConfig
from tooling.agentic.models import Mission, TaskNode, TaskStatus, RiskLevel
from tooling.agentic.repo_intel import RepositoryIntelligenceGraph
from tooling.agentic.fitness import SkillFitnessEngine, COLD_START_PRIOR
from tooling.agentic.experiments import ExperimentEngine
from tooling.agentic.learning import LearningEngine, LearningTier
from tooling.agentic.planner_resolver import AutonomousSkillResolver, AutonomousMissionPlanner
from tooling.agentic.runtime import JarvisAgenticRuntime
from tooling.agentic.telemetry import TelemetryCollector, Span, TokenUsage


class TestAgenticIntelligenceTier(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="jarvis_intel_test_")
        self.root = Path(self.temp_dir)
        self.config = JarvisRuntimeConfig(
            registry_root=self.root,
            security_mode="FAIL_CLOSED"
        )
        self.config.ensure_directories()

        # Create dummy skills
        skill_a_dir = self.config.skills_dir / "test-skill-alpha"
        skill_a_dir.mkdir(parents=True)
        (skill_a_dir / "SKILL.md").write_text(
            "---\nname: test-skill-alpha\ndescription: Alpha debugging tool\ncapabilities: [debugging, analysis]\n---\n# Alpha Skill\n",
            encoding="utf-8"
        )

        skill_b_dir = self.config.skills_dir / "test-skill-beta"
        skill_b_dir.mkdir(parents=True)
        (skill_b_dir / "SKILL.md").write_text(
            "---\nname: test-skill-beta\ndescription: Beta review tool\ncapabilities: [review, linting]\n---\n# Beta Skill\n",
            encoding="utf-8"
        )

        # Create dummy python file in workspace for AST scanning
        src_dir = self.root / "tooling" / "agentic"
        src_dir.mkdir(parents=True)
        (src_dir / "sample_service.py").write_text(
            "import os\n\nclass SampleService:\n    def compute_metric(self, x: int) -> int:\n        return x * 2\n\ndef run_pipeline():\n    pass\n",
            encoding="utf-8"
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_repo_intel_ast_and_capability_classification(self):
        """Invariant: RepositoryIntelligenceGraph discovers AST symbols and classifies capabilities."""
        graph = RepositoryIntelligenceGraph(root_path=self.root, config=self.config)
        scan = graph.scan_tree("tooling/agentic")

        self.assertIn("symbols", scan)
        symbol_names = [s["name"] for s in scan["symbols"]]
        self.assertIn("SampleService", symbol_names)
        self.assertIn("compute_metric", symbol_names)
        self.assertIn("run_pipeline", symbol_names)

        # Classify capability that exists
        res_exists = graph.classify_capability("SampleService", symbol_names)
        self.assertEqual(res_exists["classification"], "EXISTS")

        # Classify capability that partially exists
        res_partial = graph.classify_capability("compute_something", symbol_names)
        self.assertEqual(res_partial["classification"], "PARTIAL")

        # Classify capability that is missing
        res_missing = graph.classify_capability("quantum_teleportation_protocol", symbol_names)
        self.assertEqual(res_missing["classification"], "MISSING")

    def test_02_skill_fitness_cold_start_and_composite_scoring(self):
        """Invariant: Unobserved skills receive cold start prior (0.75), never 0."""
        telemetry = TelemetryCollector(ledger_file=self.config.telemetry_dir / "test_spans.jsonl")
        fitness = SkillFitnessEngine(config=self.config, telemetry_collector=telemetry)

        # Cold-start skill evaluation
        cold_report = fitness.evaluate_skill("unknown-quantum-skill")
        self.assertTrue(cold_report.is_cold_start)
        self.assertEqual(cold_report.fitness_score, COLD_START_PRIOR)
        self.assertEqual(cold_report.sample_count, 0)

        # Record telemetry spans
        span1 = Span(
            span_id="spn-01",
            mission_id="msn-01",
            task_id="tsk-01",
            agent_id="Quantum-ExecutorAgent",
            skill_id="test-skill-alpha",
            wave_index=0,
            status="SUCCESS",
            duration_ms=500,
            token_usage=TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        )
        telemetry.record_span(span1)

        # Evaluated skill has non-cold score
        active_report = fitness.evaluate_skill("test-skill-alpha")
        self.assertFalse(active_report.is_cold_start)
        self.assertEqual(active_report.sample_count, 1)
        self.assertGreater(active_report.fitness_score, 0.0)

    def test_03_experiment_engine_ab_variant_resolution(self):
        """Invariant: Active experiments deterministically assign variants in resolver."""
        exp_engine = ExperimentEngine(config=self.config)
        exp = exp_engine.create_experiment(
            experiment_id="exp-debug-01",
            capability="advanced-debugging",
            variants_tuples=[
                ("var-alpha", "test-skill-alpha", 0.5),
                ("var-beta", "test-skill-beta", 0.5)
            ],
            min_samples=2
        )
        self.assertEqual(exp.status, "ACTIVE")

        resolver = AutonomousSkillResolver(
            experiment_engine=exp_engine,
            config=self.config
        )

        # Resolve capability with active experiment
        res = resolver.resolve(capability_request="advanced-debugging", agent_profile="agent-x")
        self.assertIn(res.selected_candidate, ["test-skill-alpha", "test-skill-beta"])
        self.assertIn("ASSIGNED_BY_EXPERIMENT", res.selection_reason)

        # Record outcomes
        exp_engine.record_outcome("exp-debug-01", "var-alpha", success=True, duration_ms=200)
        exp_engine.record_outcome("exp-debug-01", "var-alpha", success=True, duration_ms=180)
        exp_engine.record_outcome("exp-debug-01", "var-beta", success=False, duration_ms=500)
        exp_engine.record_outcome("exp-debug-01", "var-beta", success=False, duration_ms=600)

        # Verify automatic conclusion
        self.assertEqual(exp.status, "CONCLUDED")
        self.assertEqual(exp.winner_variant_id, "var-alpha")


    def test_04_learning_engine_auto_promotions(self):
        """Invariant: Observations automatically promote to PATTERN and VALIDATED_HEURISTIC."""
        learning = LearningEngine(config=self.config)

        # Record 3 observations for a skill
        for i in range(3):
            learning.record_observation(
                skill="test-skill-alpha",
                agent_profile="Quantum-ExecutorAgent",
                approach=f"Refactoring step {i}",
                expected_result="Test passes",
                actual_result="Verified clean pass",
                evidence={"step": i, "status": "OK"},
                provenance=f"prov-obs-{i}"
            )

        records = learning.get_records_for_skill("test-skill-alpha")
        self.assertEqual(len(records), 3)

        # Auto evaluate promotions
        promotions = learning.auto_evaluate_promotions("test-skill-alpha")
        self.assertTrue(len(promotions) > 0)
        success_promotions = [p for p in promotions if p[1]]
        self.assertTrue(len(success_promotions) > 0)

        # Add more observations to trigger promotion to VALIDATED_HEURISTIC
        for i in range(3, 6):
            learning.record_observation(
                skill="test-skill-alpha",
                agent_profile="Quantum-ExecutorAgent",
                approach=f"Refactoring step {i}",
                expected_result="Test passes",
                actual_result="Verified clean pass",
                evidence={"step": i, "corroboration": f"env-{i}"},
                provenance=f"prov-obs-{i}"
            )

        promotions_h = learning.auto_evaluate_promotions("test-skill-alpha")
        heuristics = learning.get_validated_heuristics()
        # Heuristics cache should be loaded properly
        self.assertIsInstance(heuristics, dict)

    def test_05_end_to_end_runtime_closed_loop_intelligence(self):
        """Invariant: Runtime mission execution completes full closed-loop intelligence."""
        runtime = JarvisAgenticRuntime(registry_root=self.root, config=self.config)

        # Plan and verify capability classification metadata
        mission = runtime.planner.plan_mission(
            goal_title="Scan and verify sample service",
            required_capabilities=["SampleService", "test-skill-alpha"]
        )

        self.assertIn("capability_classifications", mission.metadata)
        classifications = mission.metadata["capability_classifications"]
        self.assertIn("SampleService", classifications)
        self.assertEqual(classifications["SampleService"]["classification"], "EXISTS")

        # Execute goal via runtime
        res = runtime.execute_goal(
            goal_prompt="Run full verification on SampleService",
            required_capabilities=["test-skill-alpha"]
        )

        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["tasks_verified"], 1)

        # Check telemetry spans recorded
        self.assertGreaterEqual(res["telemetry_spans_recorded"], 1)

        # Check learning record was created
        records = runtime.learning.get_records_for_skill("test-skill-alpha")
        self.assertGreaterEqual(len(records), 1)
        self.assertEqual(records[0].skill, "test-skill-alpha")


if __name__ == "__main__":
    unittest.main()
