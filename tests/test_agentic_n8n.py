"""
test_agentic_n8n.py // Unit and Integration Tests for Phase 14 (n8n Adapter)
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
"""

import unittest
from datetime import datetime, timedelta, timezone

from tooling.agentic.adapters.n8n import N8nAdapter


class TestN8nAdapter(unittest.TestCase):

    def setUp(self):
        self.adapter = N8nAdapter(webhook_secret="test-secret-key-123")

    def signed_event(self, *, nonce="nonce-0123456789abcdef", timestamp_utc=None):
        event = {
            "event_type": "MISSION_TRIGGER",
            "mission_id": "MIS-n8n-test-01",
            "timestamp_utc": timestamp_utc or datetime.now(timezone.utc).isoformat(),
            "nonce": nonce,
            "payload": {
                "goal": "Synchronize fresh repositories",
                "max_iterations": 5,
                "token_budget": 20_000,
            },
        }
        return event, self.adapter.sign_event(event)

    def test_rejects_missing_or_legacy_default_secret(self):
        with self.assertRaises(ValueError):
            N8nAdapter(webhook_secret="")
        with self.assertRaises(ValueError):
            N8nAdapter(webhook_secret=N8nAdapter.LEGACY_DEFAULT_SECRET)

    def test_hmac_signing_and_verification(self):
        payload = {"goal": "Run audit", "agent": "Quantum-AuditAgent"}
        sig = self.adapter.sign_payload(payload)
        self.assertTrue(self.adapter.verify_signature(payload, sig))

        tampered = {"goal": "Run exploit", "agent": "Quantum-AuditAgent"}
        self.assertFalse(self.adapter.verify_signature(tampered, sig))

    def test_parse_inbound_trigger_requires_signed_fresh_envelope(self):
        event, sig = self.signed_event()
        mission = self.adapter.parse_inbound_trigger(event, signature_hex=sig)

        self.assertEqual(mission.mission_id, "MIS-n8n-test-01")
        self.assertEqual(mission.goal, "Synchronize fresh repositories")
        self.assertEqual(mission.budget.max_iterations, 5)
        self.assertEqual(mission.budget.max_token_budget, 20_000)

    def test_unsigned_inbound_trigger_fails_closed(self):
        event, _ = self.signed_event()

        with self.assertRaises(PermissionError):
            self.adapter.parse_inbound_trigger(event)

    def test_signature_binds_mission_and_event_metadata(self):
        event, sig = self.signed_event()
        event["mission_id"] = "MIS-attacker"

        with self.assertRaises(PermissionError):
            self.adapter.parse_inbound_trigger(event, signature_hex=sig)

    def test_replay_nonce_is_rejected(self):
        event, sig = self.signed_event()
        self.adapter.parse_inbound_trigger(event, signature_hex=sig)

        with self.assertRaisesRegex(PermissionError, "Replay"):
            self.adapter.parse_inbound_trigger(event, signature_hex=sig)

    def test_stale_timestamp_is_rejected(self):
        stale = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        event, sig = self.signed_event(nonce="nonce-stale-0123456789", timestamp_utc=stale)

        with self.assertRaisesRegex(PermissionError, "Stale"):
            self.adapter.parse_inbound_trigger(event, signature_hex=sig)

    def test_outbound_notification_structure(self):
        notif = self.adapter.build_outbound_notification(
            event_type="MISSION_COMPLETED",
            mission_id="MIS-99",
            status="SUCCESS",
            goal="Verification task",
            evidence={"clean_pass": True},
        )
        self.assertEqual(notif["event_type"], "MISSION_COMPLETED")
        self.assertEqual(notif["mission_id"], "MIS-99")
        self.assertTrue(notif["nonce"])
        self.assertTrue(notif["timestamp_utc"])
        self.assertTrue(notif["signature_sha256"])
        self.assertTrue(
            self.adapter.verify_event_signature(notif, notif["signature_sha256"])
        )

    def test_generate_workflow_template(self):
        wf = self.adapter.generate_workflow_template("Test Pipe", "http://localhost:8899")
        self.assertEqual(wf["name"], "Test Pipe")
        self.assertEqual(len(wf["nodes"]), 2)
        node_names = [n["name"] for n in wf["nodes"]]
        self.assertIn("Webhook Trigger", node_names)
        self.assertIn("J.A.R.V.I.S. API Dispatcher", node_names)


if __name__ == "__main__":
    unittest.main()
