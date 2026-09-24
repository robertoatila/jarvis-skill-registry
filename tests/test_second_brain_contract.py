import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "ui"
SERVER = ROOT / "tooling" / "jarvis_server.py"


class SecondBrainContractTests(unittest.TestCase):
    def test_second_brain_assets_are_loaded_and_cached(self):
        index = (UI / "index.html").read_text(encoding="utf-8")
        service_worker = (UI / "service-worker.js").read_text(encoding="utf-8")

        self.assertIn('href="second-brain.css"', index)
        self.assertIn('src="second-brain.js"', index)
        self.assertIn("'/second-brain.css'", service_worker)
        self.assertIn("'/second-brain.js'", service_worker)
        self.assertIn("jarvis-mark-liv-shell-v6", service_worker)

    def test_server_exposes_only_real_second_brain_runtime_projections(self):
        server = SERVER.read_text(encoding="utf-8")

        self.assertIn('path == "/api/second-brain/graph"', server)
        self.assertIn('path == "/api/second-brain/operations"', server)
        self.assertIn('path == "/api/agentic/dag/active"', server)
        self.assertIn("NO_ACTIVE_MISSION", server)
        self.assertIn("AUTHORITATIVE_DAG_INCONSISTENT", server)

        self.assertNotIn("MISSION-ACTIVE-DAG", server)
        self.assertNotIn("Observe Workspace Environment", server)
        self.assertNotIn("Plan Autonomous Mission", server)

    def test_ui_distinguishes_observed_context_and_human_gates(self):
        source = (UI / "second-brain.js").read_text(encoding="utf-8")

        self.assertIn("CTX SHARED", source)
        self.assertIn("CTX NÃO OBSERVADO", source)
        self.assertIn("WAITING_HUMAN", source)
        self.assertIn("DECISÃO HUMANA", source)
        self.assertIn("/api/second-brain/operations", source)
        self.assertIn("/api/second-brain/graph", source)

    def test_operation_projection_is_read_only_and_does_not_expose_goal(self):
        source = (
            ROOT / "tooling" / "agentic" / "second_brain_operations.py"
        ).read_text(encoding="utf-8")

        self.assertIn('"read_only": True', source)
        self.assertIn('"persisted_approval_requests"', source)
        self.assertIn('"receipt_ledger"', source)
        self.assertNotIn('"goal": record.get', source)
        self.assertNotIn('"signature":', source)
        self.assertNotIn('"approved_by":', source)


if __name__ == "__main__":
    unittest.main()
