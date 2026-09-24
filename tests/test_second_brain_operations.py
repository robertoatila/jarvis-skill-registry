import json
import tempfile
import unittest
from pathlib import Path

from tooling.agentic.second_brain_operations import SecondBrainOperationsBuilder


class SecondBrainOperationsBuilderTests(unittest.TestCase):
    def test_projects_authoritative_handoff_receipts_and_human_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missions = root / "missions"
            approvals = root / "approvals"
            receipts = root / "receipts"
            missions.mkdir()
            approvals.mkdir()
            receipts.mkdir()

            mission = {
                "schema_version": "2.0.0",
                "mission_id": "mission-1",
                "goal": "private goal is deliberately not projected",
                "status": "RUNNING",
                "created_utc": "2026-09-24T12:00:00+00:00",
                "dag": {
                    "nodes": [
                        {
                            "schema_version": "2.0.0",
                            "task_id": "observe",
                            "title": "Observe",
                            "agent_profile": "Quantum-ReconAgent",
                            "dependencies": [],
                            "status": "VERIFIED",
                            "risk_level": "R0",
                            "approval_status": "NOT_REQUIRED",
                            "verification_requirements": [
                                {"status": "VERIFIED"}
                            ],
                        },
                        {
                            "schema_version": "2.0.0",
                            "task_id": "deploy",
                            "title": "Deploy",
                            "agent_profile": "Quantum-SynthesisAgent",
                            "dependencies": ["observe"],
                            "status": "FAILED",
                            "risk_level": "R4",
                            "approval_status": "REQUESTED",
                            "execution_result": {
                                "approval_required": True,
                                "approval_id": "app-123456abcdef",
                                "executed": False,
                            },
                            "verification_requirements": [],
                        },
                    ],
                    "edges": [{"from": "observe", "to": "deploy"}],
                },
            }
            (missions / "mission-1.json").write_text(
                json.dumps(mission),
                encoding="utf-8",
            )

            approval = {
                "schema_version": "2.0.0",
                "approval_id": "app-123456abcdef",
                "task_id": "deploy",
                "agent_profile": "Quantum-SynthesisAgent",
                "action": "write",
                "tool_or_skill": "deploy",
                "resource": "production",
                "risk_level": "R4",
                "justification": "human gate",
                "context_hash": "abc",
                "signature": None,
                "action_context": {"mission_id": "mission-1"},
                "status": "PENDING_ACK",
                "requested_utc": "2026-09-24T12:01:00+00:00",
                "expires_utc": "2026-09-24T12:06:00+00:00",
                "approved_by": None,
                "decision_utc": None,
            }
            (approvals / "app-123456abcdef.json").write_text(
                json.dumps(approval),
                encoding="utf-8",
            )

            receipt_rows = [
                {
                    "receipt_id": "dec-1",
                    "schema_version": "2.0.0",
                    "mission_id": "mission-1",
                    "task_id": "observe",
                    "attempt_id": "att-1",
                    "trace_id": "trace-1",
                    "created_utc": "2026-09-24T12:00:01+00:00",
                    "decision_type": "agent_selection",
                    "candidates": ["Quantum-ReconAgent"],
                    "rejected_candidates": {},
                    "scores": {"Quantum-ReconAgent": 1.0},
                    "selected_candidate": "Quantum-ReconAgent",
                    "selection_reason": "capability match",
                    "confidence": 1.0,
                    "estimated_risk": "R0",
                },
                {
                    "receipt_id": "exec-1",
                    "schema_version": "2.0.0",
                    "mission_id": "mission-1",
                    "task_id": "observe",
                    "attempt_id": "att-1",
                    "trace_id": "trace-1",
                    "created_utc": "2026-09-24T12:00:02+00:00",
                    "adapter": "local",
                    "invocation_occurred": True,
                    "execution_state": "EXECUTED",
                    "output_reference": "artifact-1",
                    "resource_usage": {},
                },
                {
                    "receipt_id": "ver-1",
                    "schema_version": "2.0.0",
                    "mission_id": "mission-1",
                    "task_id": "observe",
                    "attempt_id": "att-1",
                    "trace_id": "trace-1",
                    "created_utc": "2026-09-24T12:00:03+00:00",
                    "execution_receipt_id": "exec-1",
                    "verification_state": "VERIFIED",
                    "evidence_ids": ["ev-1"],
                },
            ]
            (receipts / "receipts.jsonl").write_text(
                "\n".join(json.dumps(row) for row in receipt_rows) + "\n",
                encoding="utf-8",
            )

            payload = SecondBrainOperationsBuilder(
                missions,
                approvals,
                receipts,
            ).build()

            self.assertTrue(payload["read_only"])
            self.assertEqual(payload["metrics"]["active_missions"], 1)
            projected = payload["missions"][0]
            self.assertNotIn("goal", projected)
            self.assertEqual(projected["metrics"]["handoffs_total"], 1)
            self.assertEqual(projected["metrics"]["waiting_human_total"], 1)
            self.assertEqual(projected["handoffs"][0]["state"], "WAITING_HUMAN")
            gate = projected["human_gates"][0]
            self.assertEqual(gate["gate_state"], "WAITING_HUMAN")
            self.assertEqual(gate["approval_status"], "PENDING_ACK")
            observe = next(task for task in projected["tasks"] if task["task_id"] == "observe")
            self.assertEqual(observe["selected_agent"], "Quantum-ReconAgent")
            self.assertEqual(observe["execution_state"], "EXECUTED")
            self.assertEqual(observe["verification_state"], "VERIFIED")


if __name__ == "__main__":
    unittest.main()
