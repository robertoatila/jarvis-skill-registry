"""
test_agentic_profiles.py // Unit and Integration Tests for Phase 03 (Agent Profiles)
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
"""

import unittest
import tempfile
import json
import ast
from pathlib import Path
from tooling.agentic.profiles import (
    AgentProfile,
    AgentConstraints,
    AgentBudgetLimits,
    AgentProfileRegistry
)


class TestAgentProfiles(unittest.TestCase):

    def setUp(self):
        self.registry = AgentProfileRegistry()

    def test_default_quantum_agents_present(self):
        profiles = self.registry.list_profiles()
        self.assertEqual(len(profiles), 4)

        audit_agent = self.registry.get("Quantum-AuditAgent")
        self.assertIsNotNone(audit_agent)
        self.assertIn("security-audit", audit_agent.capabilities)
        self.assertTrue(audit_agent.constraints.read_only)
        self.assertFalse(audit_agent.constraints.network_access)

        recon_agent = self.registry.get("Quantum-ReconAgent")
        self.assertIsNotNone(recon_agent)
        self.assertIn("osint-recon", recon_agent.capabilities)

        synth_agent = self.registry.get("Quantum-SynthesisAgent")
        self.assertIsNotNone(synth_agent)
        self.assertIn("ai-routing", synth_agent.capabilities)

        vis_agent = self.registry.get("Quantum-VisualizerAgent")
        self.assertIsNotNone(vis_agent)
        self.assertIn("wcag-audit", vis_agent.capabilities)

    def test_resolve_agent_by_capability(self):
        res = self.registry.resolve_agent(required_capabilities=["security-audit", "integrity-verification"])
        self.assertIsNotNone(res["selected_agent"])
        self.assertEqual(res["selected_agent"].agent_id, "Quantum-AuditAgent")
        self.assertGreater(res["score"], 0.0)

    def test_resolve_agent_by_skill(self):
        res = self.registry.resolve_agent(required_skills=["deckgl-geospatial-visualization"])
        self.assertIsNotNone(res["selected_agent"])
        self.assertEqual(res["selected_agent"].agent_id, "Quantum-VisualizerAgent")

    def test_constraint_filtering_offline(self):
        # Even if ReconAgent has repo-mining, require_offline must reject it because it has network access
        res = self.registry.resolve_agent(
            required_capabilities=["repo-mining"],
            constraints_filter={"require_offline": True}
        )
        candidates = {c["agent_id"]: c for c in res["candidates_evaluated"]}
        self.assertFalse(candidates["Quantum-ReconAgent"]["accepted"])
        self.assertIn("offline", candidates["Quantum-ReconAgent"]["reason"])

    def test_deterministic_tie_breaking(self):
        # Register two agents with identical capability match
        p1 = AgentProfile(agent_id="Agent-Beta", name="Beta", domain="Test", capabilities=["common-cap"])
        p2 = AgentProfile(agent_id="Agent-Alpha", name="Alpha", domain="Test", capabilities=["common-cap"])
        self.registry.register(p1)
        self.registry.register(p2)

        res = self.registry.resolve_agent(required_capabilities=["common-cap"])
        # Both match score 1.0, tie-breaker must pick Agent-Alpha alphabetically
        self.assertEqual(res["selected_agent"].agent_id, "Agent-Alpha")

    def test_profile_serialization_roundtrip(self):
        prof = self.registry.get("Quantum-AuditAgent")
        data = prof.to_dict()

        reconstructed = AgentProfile.from_dict(data)
        self.assertEqual(reconstructed.agent_id, prof.agent_id)
        self.assertEqual(reconstructed.badge, prof.badge)
        self.assertEqual(reconstructed.constraints.read_only, True)

    def test_every_requested_capability_and_skill_is_mandatory(self):
        for kwargs in ({"required_capabilities": ["unknown"]},
                       {"required_capabilities": ["security-audit", "unknown"]},
                       {"required_skills": ["security-research-audit", "unknown"]}):
            result = self.registry.resolve_agent(**kwargs)
            self.assertIsNone(result["selected_agent"])
            self.assertTrue(all(not c["accepted"] for c in result["candidates_evaluated"]))

    def test_write_network_tool_budget_and_capacity_constraints(self):
        for constraints in ({"requires_write": True}, {"requires_network": True},
                            {"required_tools": ["unapproved:tool"]}, {"estimated_tokens": 999999},
                            {"timeout_seconds": 999}, {"tool_calls": 999},
                            {"active_tasks": {"Quantum-AuditAgent": 1}}):
            with self.subTest(constraints=constraints):
                result = self.registry.resolve_agent(required_capabilities=["security-audit"], constraints_filter=constraints)
                self.assertIsNone(result["selected_agent"])

    def test_offline_agent_and_invalid_profiles_are_rejected(self):
        self.registry.get("Quantum-AuditAgent").status = "OFFLINE"
        self.assertIsNone(self.registry.resolve_agent(required_capabilities=["security-audit"])["selected_agent"])
        for field in ({"capacity": 0}, {"status": "TYPO"}, {"capabilities": "wrong"}, {"schema_version": "99"},
                      {"constraints": {"read_only": "false"}}, {"budget_limits": {"max_runtime_seconds": float("inf")}}):
            data = self.registry.get("Quantum-AuditAgent").to_dict()
            with self.subTest(field=field), self.assertRaises(ValueError):
                AgentProfile.from_dict({**data, **field})

    def test_profile_snapshot_roundtrip_and_duplicate_rejection(self):
        self.registry.register(AgentProfile("custom", "Custom", "testing", capabilities=["test"], capacity=2))
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "profiles.json"
            self.registry.save(target)
            restored = AgentProfileRegistry.load(target)
            self.assertEqual([p.to_dict() for p in restored.list_profiles()], [p.to_dict() for p in self.registry.list_profiles()])
            data = json.loads(target.read_text())
            data["profiles"].append(data["profiles"][0])
            target.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                AgentProfileRegistry.load(target)

    def test_legacy_quantum_identifiers_are_preserved_without_importing_server(self):
        server = Path(__file__).resolve().parents[1] / "tooling" / "jarvis_server.py"
        module = ast.parse(server.read_text(encoding="utf-8-sig"))
        engine = next(n for n in module.body if isinstance(n, ast.ClassDef) and n.name == "QuantumAgentEngine")
        strings = {n.value for n in ast.walk(engine) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        for profile in self.registry.list_profiles():
            self.assertIn(profile.agent_id, strings)


if __name__ == "__main__":
    unittest.main()
