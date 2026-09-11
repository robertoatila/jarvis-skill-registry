"""
test_agentic_federation.py // Unit and Integration Tests for Phase 16 (Multi-Node Federation)
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
"""

import unittest
from tooling.agentic.models import TaskNode
from tooling.agentic.federation import (
    FederationNode,
    FederationRouter,
    TrustTier
)


class TestFederation(unittest.TestCase):

    def setUp(self):
        self.router = FederationRouter()

    def test_primary_node_registered(self):
        nodes = self.router.list_nodes()
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].trust_tier, TrustTier.SOVEREIGN_PRIMARY)

    def test_canonical_write_isolation(self):
        # Register a remote trusted peer
        peer = FederationNode(
            node_id="node-peer-remote-01",
            peer_id="peer-123",
            display_name="Remote Peer",
            endpoint="https://peer.local",
            trust_tier=TrustTier.TRUSTED_PEER,
            capacity=10
        )
        self.router.register_node(peer)

        # Task with write scope on state/
        write_task = TaskNode(
            task_id="write-state-task",
            title="Update State",
            agent_profile="Quantum-AuditAgent",
            write_scopes=["state/current-state.json"]
        )

        selected, reason = self.router.resolve_node_for_task(write_task)
        self.assertIsNotNone(selected)
        # Invariant: Must run on SOVEREIGN_PRIMARY, NOT on remote peer
        self.assertEqual(selected.trust_tier, TrustTier.SOVEREIGN_PRIMARY)

    def test_read_only_offload_when_primary_saturated(self):
        # Saturate primary node
        primary = self.router.list_nodes()[0]
        primary.active_tasks = primary.capacity  # 0 available capacity

        peer = FederationNode(
            node_id="node-peer-02",
            peer_id="peer-456",
            display_name="Remote Worker",
            endpoint="https://worker.local",
            trust_tier=TrustTier.TRUSTED_PEER,
            capacity=4
        )
        self.router.register_node(peer)

        # Read-only task
        read_task = TaskNode(
            task_id="read-report-task",
            title="Inspect Reports",
            agent_profile="Quantum-ReconAgent",
            read_scopes=["reports/"]
        )

        selected, reason = self.router.resolve_node_for_task(read_task)
        self.assertIsNotNone(selected)
        self.assertEqual(selected.node_id, "node-peer-02")

    def test_exchange_envelope_signature(self):
        peer = FederationNode(
            node_id="node-worker",
            peer_id="peer-w",
            display_name="Worker",
            endpoint="local://worker"
        )
        task = TaskNode(task_id="t-exch", title="Task Exchange")
        envelope = self.router.build_exchange_envelope(task, peer)

        self.assertIn("signature_sha256", envelope)
        self.assertEqual(envelope["target_node"], "node-worker")
        self.assertEqual(len(envelope["signature_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
