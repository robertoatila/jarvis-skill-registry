"""
test_agentic_federation.py // Unit and Integration Tests for Phase 16 (Multi-Node Federation)
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
"""

import unittest
from copy import deepcopy

from tooling.agentic.models import TaskNode
from tooling.agentic.federation import (
    FederationNode,
    FederationRouter,
    TrustTier,
)


class TestFederation(unittest.TestCase):

    def setUp(self):
        self.router = FederationRouter(
            exchange_secret="test-federation-exchange-secret-0123456789"
        )

    def test_primary_node_registered(self):
        nodes = self.router.list_nodes()
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].trust_tier, TrustTier.SOVEREIGN_PRIMARY)

    def test_remote_node_registration_fails_closed_without_secret(self):
        router = FederationRouter()
        peer = FederationNode(
            node_id="node-peer-no-secret",
            peer_id="peer-no-secret",
            display_name="Remote Peer",
            endpoint="https://peer.local",
            trust_tier=TrustTier.TRUSTED_PEER,
        )

        with self.assertRaises(PermissionError):
            router.register_node(peer)

    def test_unknown_trust_tier_is_rejected_on_parse(self):
        payload = {
            "node_id": "node-unknown",
            "peer_id": "peer-unknown",
            "display_name": "Unknown",
            "endpoint": "https://unknown.local",
            "trust_tier": "MAGIC_TRUST",
        }

        with self.assertRaises(ValueError):
            FederationNode.from_dict(payload)

    def test_missing_trust_tier_defaults_to_untrusted_external(self):
        payload = {
            "node_id": "node-missing-tier",
            "peer_id": "peer-missing-tier",
            "display_name": "Missing Tier",
            "endpoint": "https://missing-tier.example",
        }
        peer = FederationNode.from_dict(payload)
        self.assertEqual(peer.trust_tier, TrustTier.UNTRUSTED_EXTERNAL)

        self.router.register_node(peer)
        primary = next(
            node for node in self.router.list_nodes()
            if node.trust_tier == TrustTier.SOVEREIGN_PRIMARY
        )
        primary.active_tasks = primary.capacity
        selected, reason = self.router.resolve_node_for_task(
            TaskNode(
                task_id="missing-tier-task",
                title="Missing tier must not offload",
                agent_profile="Quantum-ReconAgent",
                read_scopes=["reports/"],
            )
        )
        self.assertIsNone(selected)
        self.assertIn("No federation node", reason)

    def test_untrusted_external_is_never_selected_for_offload(self):
        primary = self.router.list_nodes()[0]
        primary.active_tasks = primary.capacity

        peer = FederationNode(
            node_id="node-untrusted",
            peer_id="peer-untrusted",
            display_name="Untrusted Worker",
            endpoint="https://untrusted.example",
            trust_tier=TrustTier.UNTRUSTED_EXTERNAL,
            capacity=10,
        )
        self.router.register_node(peer)
        task = TaskNode(
            task_id="read-sensitive",
            title="Inspect Reports",
            agent_profile="Quantum-ReconAgent",
            read_scopes=["reports/"],
        )

        selected, reason = self.router.resolve_node_for_task(task)
        self.assertIsNone(selected)
        self.assertIn("No federation node", reason)

    def test_canonical_write_isolation(self):
        peer = FederationNode(
            node_id="node-peer-remote-01",
            peer_id="peer-123",
            display_name="Remote Peer",
            endpoint="https://peer.local",
            trust_tier=TrustTier.TRUSTED_PEER,
            capacity=10,
        )
        self.router.register_node(peer)

        write_task = TaskNode(
            task_id="write-state-task",
            title="Update State",
            agent_profile="Quantum-AuditAgent",
            write_scopes=["state/current-state.json"],
        )

        selected, _ = self.router.resolve_node_for_task(write_task)
        self.assertIsNotNone(selected)
        self.assertEqual(selected.trust_tier, TrustTier.SOVEREIGN_PRIMARY)

    def test_read_only_offload_when_primary_saturated(self):
        primary = self.router.list_nodes()[0]
        primary.active_tasks = primary.capacity

        peer = FederationNode(
            node_id="node-peer-02",
            peer_id="peer-456",
            display_name="Remote Worker",
            endpoint="https://worker.local",
            trust_tier=TrustTier.TRUSTED_PEER,
            capacity=4,
        )
        self.router.register_node(peer)

        read_task = TaskNode(
            task_id="read-report-task",
            title="Inspect Reports",
            agent_profile="Quantum-ReconAgent",
            read_scopes=["reports/"],
        )

        selected, _ = self.router.resolve_node_for_task(read_task)
        self.assertIsNotNone(selected)
        self.assertEqual(selected.node_id, "node-peer-02")

    def test_exchange_envelope_is_hmac_authenticated(self):
        peer = FederationNode(
            node_id="node-worker",
            peer_id="peer-w",
            display_name="Worker",
            endpoint="https://worker.local",
            trust_tier=TrustTier.TRUSTED_PEER,
        )
        self.router.register_node(peer)
        task = TaskNode(task_id="t-exch", title="Task Exchange")
        envelope = self.router.build_exchange_envelope(task, peer)

        self.assertIn("signature_hmac_sha256", envelope)
        self.assertNotIn("signature_sha256", envelope)
        self.assertEqual(envelope["target_node"], "node-worker")
        self.assertEqual(len(envelope["signature_hmac_sha256"]), 64)
        self.assertTrue(self.router.verify_exchange_envelope(envelope))

    def test_exchange_tampering_and_replay_fail_closed(self):
        peer = FederationNode(
            node_id="node-worker",
            peer_id="peer-w",
            display_name="Worker",
            endpoint="https://worker.local",
            trust_tier=TrustTier.TRUSTED_PEER,
        )
        self.router.register_node(peer)
        task = TaskNode(task_id="t-exch", title="Task Exchange")

        original = self.router.build_exchange_envelope(task, peer)
        tampered = deepcopy(original)
        tampered["target_node"] = "node-attacker"
        self.assertFalse(self.router.verify_exchange_envelope(tampered))

        fresh = self.router.build_exchange_envelope(task, peer)
        self.assertTrue(self.router.verify_exchange_envelope(fresh))
        self.assertFalse(self.router.verify_exchange_envelope(fresh))


if __name__ == "__main__":
    unittest.main()
