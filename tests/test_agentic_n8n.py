"""
test_agentic_n8n.py // Unit and Integration Tests for Phase 14 (n8n Adapter)
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
"""

import unittest
from tooling.agentic.adapters.n8n import N8nAdapter


class TestN8nAdapter(unittest.TestCase):

    def setUp(self):
        self.adapter = N8nAdapter(webhook_secret="test-secret-key-123")

    def test_hmac_signing_and_verification(self):
        payload = {"goal": "Run audit", "agent": "Quantum-AuditAgent"}
        sig = self.adapter.sign_payload(payload)
        self.assertTrue(self.adapter.verify_signature(payload, sig))

        # Tampered payload fails
        tampered = {"goal": "Run exploit", "agent": "Quantum-AuditAgent"}
        self.assertFalse(self.adapter.verify_signature(tampered, sig))

    def test_parse_inbound_trigger(self):
        event = {
            "event_type": "MISSION_TRIGGER",
            "mission_id": "MIS-n8n-test-01",
            "payload": {
                "goal": "Synchronize fresh repositories",
                "max_iterations": 5,
                "token_budget": 20_000
            }
        }
        sig = self.adapter.sign_payload(event["payload"])
        mission = self.adapter.parse_inbound_trigger(event, signature_hex=sig)

        self.assertEqual(mission.mission_id, "MIS-n8n-test-01")
        self.assertEqual(mission.goal, "Synchronize fresh repositories")
        self.assertEqual(mission.budget.max_iterations, 5)
        self.assertEqual(mission.budget.max_token_budget, 20_000)

    def test_outbound_notification_structure(self):
        notif = self.adapter.build_outbound_notification(
            event_type="MISSION_COMPLETED",
            mission_id="MIS-99",
            status="SUCCESS",
            goal="Verification task",
            evidence={"clean_pass": True}
        )
        self.assertEqual(notif["event_type"], "MISSION_COMPLETED")
        self.assertEqual(notif["mission_id"], "MIS-99")
        self.assertTrue(notif["signature_sha256"])
        self.assertTrue(self.adapter.verify_signature(notif["payload"], notif["signature_sha256"]))

    def test_generate_workflow_template(self):
        wf = self.adapter.generate_workflow_template("Test Pipe", "http://localhost:8899")
        self.assertEqual(wf["name"], "Test Pipe")
        self.assertEqual(len(wf["nodes"]), 2)
        node_names = [n["name"] for n in wf["nodes"]]
        self.assertIn("Webhook Trigger", node_names)
        self.assertIn("J.A.R.V.I.S. API Dispatcher", node_names)


if __name__ == "__main__":
    unittest.main()
