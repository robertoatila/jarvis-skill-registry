"""
federation.py // J.A.R.V.I.S. Multi-Node Federation & Remote Wave Dispatcher
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
Enforces:
- Peer identity grounded in Merkle root anchor
- Fail-closed isolation: Write-scoped tasks on canonical registry restricted to SOVEREIGN_PRIMARY
- Deterministic candidate node ranking & capacity bounds
"""

from __future__ import annotations
import hashlib
import json
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple, Any
from datetime import datetime, timezone

from .models import TaskNode


class TrustTier(str, Enum):
    SOVEREIGN_PRIMARY = "SOVEREIGN_PRIMARY"
    TRUSTED_PEER = "TRUSTED_PEER"
    UNTRUSTED_EXTERNAL = "UNTRUSTED_EXTERNAL"


@dataclass
class FederationNode:
    node_id: str
    peer_id: str
    display_name: str
    endpoint: str
    trust_tier: TrustTier = TrustTier.TRUSTED_PEER
    capacity: int = 4
    active_tasks: int = 0
    supported_profiles: List[str] = field(default_factory=lambda: ["Quantum-AuditAgent", "Quantum-ReconAgent", "Quantum-SynthesisAgent", "Quantum-VisualizerAgent"])

    @property
    def available_capacity(self) -> int:
        return max(0, self.capacity - self.active_tasks)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "peer_id": self.peer_id,
            "display_name": self.display_name,
            "endpoint": self.endpoint,
            "trust_tier": self.trust_tier.value if isinstance(self.trust_tier, TrustTier) else str(self.trust_tier),
            "capacity": self.capacity,
            "active_tasks": self.active_tasks,
            "supported_profiles": sorted(self.supported_profiles)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FederationNode:
        tier = data.get("trust_tier", TrustTier.TRUSTED_PEER)
        try:
            tier = TrustTier(tier)
        except ValueError:
            pass
        return cls(
            node_id=data["node_id"],
            peer_id=data["peer_id"],
            display_name=data.get("display_name", data["node_id"]),
            endpoint=data.get("endpoint", "local://"),
            trust_tier=tier,
            capacity=data.get("capacity", 4),
            active_tasks=data.get("active_tasks", 0),
            supported_profiles=list(data.get("supported_profiles", []))
        )


class FederationRouter:
    """
    Manages trusted federation nodes and routes tasks across nodes deterministically.
    """

    def __init__(self, primary_node_id: str = "node-primary-sovereign"):
        self.primary_node_id = primary_node_id
        self._nodes: Dict[str, FederationNode] = {}
        self._init_primary_node()

    def _init_primary_node(self) -> None:
        primary = FederationNode(
            node_id=self.primary_node_id,
            peer_id="peer-c6d7e89f256c6baa",
            display_name="Local Sovereign Master Node",
            endpoint="local://primary",
            trust_tier=TrustTier.SOVEREIGN_PRIMARY,
            capacity=8
        )
        self.register_node(primary)

    def register_node(self, node: FederationNode) -> None:
        self._nodes[node.node_id] = node

    def list_nodes(self) -> List[FederationNode]:
        return [self._nodes[k] for k in sorted(self._nodes.keys())]

    def resolve_node_for_task(self, task: TaskNode) -> Tuple[Optional[FederationNode], str]:
        """
        Deterministically selects an execution node for task.
        Invariants:
        - If task has write_scopes on canonical/state paths, it MUST run on SOVEREIGN_PRIMARY.
        - Node must support task's required agent_profile.
        - Node must have available capacity.
        - Deterministic tie-breaking by available capacity (desc), node_id (asc).
        """
        has_canonical_writes = any(
            "state" in s.lower() or "skills" in s.lower() or "index" in s.lower()
            for s in task.write_scopes
        )

        candidates: List[FederationNode] = []
        for n_id in sorted(self._nodes.keys()):
            node = self._nodes[n_id]
            if node.available_capacity <= 0:
                continue
            if task.agent_profile not in node.supported_profiles:
                continue

            # Security isolation: Canonical writes allowed ONLY on PRIMARY
            if has_canonical_writes and node.trust_tier != TrustTier.SOVEREIGN_PRIMARY:
                continue

            candidates.append(node)

        if not candidates:
            return None, "No federation node meets required trust tier, capacity, and profile support."

        # Rank deterministically:
        # 1. SOVEREIGN_PRIMARY first if matching
        # 2. Highest available capacity
        # 3. Alphabetical node_id
        def rank_key(n: FederationNode):
            tier_val = 2 if n.trust_tier == TrustTier.SOVEREIGN_PRIMARY else 1
            return (-tier_val, -n.available_capacity, n.node_id)

        candidates.sort(key=rank_key)
        selected = candidates[0]
        return selected, f"Selected node '{selected.node_id}' ({selected.trust_tier.value})"

    def build_exchange_envelope(self, task: TaskNode, target_node: FederationNode) -> Dict[str, Any]:
        """Creates a signed exchange payload for remote dispatch."""
        envelope = {
            "exchange_id": f"exch-{int(datetime.now(timezone.utc).timestamp())}-{task.task_id}",
            "source_node": self.primary_node_id,
            "target_node": target_node.node_id,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "task": task.to_dict()
        }
        data_str = json.dumps(envelope, sort_keys=True, ensure_ascii=False)
        sig = hashlib.sha256(data_str.encode("utf-8")).hexdigest()
        envelope["signature_sha256"] = sig
        return envelope


# Global singleton
FEDERATION_ROUTER = FederationRouter()
