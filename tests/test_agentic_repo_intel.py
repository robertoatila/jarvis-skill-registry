"""
test_agentic_repo_intel.py // Unit and Integration Tests for Phase 11 (Repository Intelligence Graph)
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
"""

import unittest
from pathlib import Path
from tooling.agentic.repo_intel import RepositoryIntelligenceGraph, REGISTRY_ROOT


class TestRepositoryIntelligence(unittest.TestCase):

    def setUp(self):
        self.intel = RepositoryIntelligenceGraph(REGISTRY_ROOT)

    def test_scan_tree_symbols(self):
        res = self.intel.scan_tree("tooling/agentic")
        self.assertNotIn("error", res)
        self.assertGreater(res["total_files"], 5)

        symbol_names = [s["name"] for s in res["symbols"]]
        self.assertIn("ExecutionDAG", symbol_names)
        self.assertIn("WaveScheduler", symbol_names)
        self.assertIn("AgentProfileRegistry", symbol_names)
        self.assertIn("AutonomousGoalLoop", symbol_names)

    def test_scan_tree_dependencies(self):
        res = self.intel.scan_tree("tooling/agentic")
        deps = res["module_dependencies"]
        self.assertGreater(len(deps), 0)

        # Check that dag imports models
        dag_deps = [d["imported_module"] for d in deps if d["source_module"] == "dag"]
        self.assertTrue(any("models" in d for d in dag_deps))

    def test_capability_classifier(self):
        symbols = ["ExecutionDAG", "WaveScheduler", "AgentProfileRegistry"]

        # 1. Exact match -> EXISTS
        c1 = self.intel.classify_capability("execution_dag", symbols)
        self.assertEqual(c1["classification"], "EXISTS")

        # 2. Partial match -> PARTIAL
        c2 = self.intel.classify_capability("scheduler", symbols)
        self.assertEqual(c2["classification"], "PARTIAL")

        # 3. Missing -> MISSING
        c3 = self.intel.classify_capability("blockchain_quantum_warp", symbols)
        self.assertEqual(c3["classification"], "MISSING")


if __name__ == "__main__":
    unittest.main()
