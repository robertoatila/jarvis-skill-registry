"""v0.2.0 fail-closed skill resolution contracts."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tooling.agentic.planner_resolver import (
    AutonomousMissionPlanner,
    AutonomousSkillResolver,
    SkillResolutionExplanation,
)
from tooling.agentic.progressive_disclosure import SkillCatalogEntry, SkillManifestEntry


class _DisclosureFixture:
    def __init__(self, entries):
        self.entries = {entry.id: entry for entry in entries}

    def load_catalog(self):
        return dict(self.entries)

    def disclose_manifest(self, skill_id):
        entry = self.entries.get(skill_id)
        if entry is None:
            # Deliberately permissive fixture: production must reject identities
            # that do not exist in the catalog rather than relying on load failure.
            entry = SkillCatalogEntry(
                id=skill_id,
                name=f"synthetic-{skill_id}",
                capabilities=[skill_id],
            )
        return SkillManifestEntry(catalog=entry, cost_hints={"token_estimate": 10})


class _FitnessFixture:
    def __init__(self, scores=None):
        self.scores = scores or {}

    def evaluate_skill(self, skill_id):
        return SimpleNamespace(fitness_score=self.scores.get(skill_id, 0.75))


class _AgentsFixture:
    def get(self, _agent_id):
        return None

    def resolve_agent(self, required_capabilities):
        return {"selected_agent": None, "required_capabilities": list(required_capabilities)}


class _FederationFixture:
    def __init__(self):
        self._nodes = {}


class _ExperimentsFixture:
    def get_experiment_for_capability(self, _capability):
        return None


class _RepoIntelFixture:
    def get_known_symbols(self):
        return set()

    def classify_capability(self, capability, _known_symbols):
        return {"classification": "MISSING", "capability": capability}


class _UnresolvedResolverFixture:
    def __init__(self):
        self.agents = _AgentsFixture()

    def resolve(self, capability_request, target_platform="windows"):
        return SkillResolutionExplanation(
            resolution_id="res-unresolved",
            capability_request=capability_request,
            candidates=[],
            selected_candidate=None,
            selection_reason="NO_CANDIDATE_AVAILABLE",
        )


class TestV020SkillResolution(unittest.TestCase):
    def _resolver(self, entries=(), scores=None):
        return AutonomousSkillResolver(
            disclosure_engine=_DisclosureFixture(entries),
            fitness_engine=_FitnessFixture(scores),
            agent_registry=_AgentsFixture(),
            federation_router=_FederationFixture(),
            experiment_engine=_ExperimentsFixture(),
        )

    @staticmethod
    def _entry(skill_id, capability="python-pro", *, risk="LOW", lifecycle=None):
        entry = SkillCatalogEntry(
            id=skill_id,
            name=skill_id,
            capabilities=[capability],
            description=f"Handles {capability}",
            risk=risk,
        )
        if lifecycle is not None:
            entry.lifecycle_state = lifecycle
        return entry

    def test_empty_catalog_has_no_synthetic_winner(self):
        winner, receipt = self._resolver().resolve_with_decision_receipt("missing-capability")

        self.assertIsNone(winner)
        self.assertEqual(receipt.selected_candidate, "")
        self.assertTrue(receipt.metadata["requires_intervention"])
        self.assertEqual(receipt.metadata["unresolved_capability"], "missing-capability")

    def test_all_policy_excluded_candidates_have_no_winner(self):
        resolver = self._resolver([
            self._entry("critical-a", risk="CRITICAL"),
            self._entry("critical-b", risk="CRITICAL"),
        ])

        winner, receipt = resolver.resolve_with_decision_receipt("python-pro")

        self.assertIsNone(winner)
        self.assertEqual(receipt.selected_candidate, "")
        self.assertEqual(receipt.rejected_candidates["critical-a"], "REJECTED_POLICY_CRITICAL_RISK")
        self.assertEqual(receipt.rejected_candidates["critical-b"], "REJECTED_POLICY_CRITICAL_RISK")

    def test_missing_pinned_candidate_blocks_instead_of_becoming_candidate(self):
        resolver = self._resolver([self._entry("real-python")])

        winner, receipt = resolver.resolve_with_decision_receipt(
            "python-pro",
            lock_pinned_skill="missing-pinned-skill",
        )

        self.assertIsNone(winner)
        self.assertEqual(receipt.selected_candidate, "")
        self.assertEqual(
            receipt.rejected_candidates["missing-pinned-skill"],
            "PINNED_SKILL_NOT_FOUND",
        )
        self.assertTrue(receipt.metadata["requires_intervention"])

    def test_quarantined_broken_and_disabled_candidates_remain_excluded(self):
        entries = [
            self._entry("quarantined", lifecycle="QUARANTINED"),
            self._entry("broken", lifecycle="BROKEN"),
            self._entry("disabled", lifecycle="DISABLED"),
        ]
        resolver = self._resolver(entries)

        winner, receipt = resolver.resolve_with_decision_receipt("python-pro")

        self.assertIsNone(winner)
        self.assertEqual(receipt.selected_candidate, "")
        self.assertIn("LIFECYCLE", receipt.rejected_candidates["quarantined"])
        self.assertIn("LIFECYCLE", receipt.rejected_candidates["broken"])
        self.assertIn("LIFECYCLE", receipt.rejected_candidates["disabled"])

    def test_admissible_candidates_choose_deterministic_real_winner(self):
        resolver = self._resolver(
            [self._entry("alpha-python"), self._entry("beta-python")],
            scores={"alpha-python": 0.91, "beta-python": 0.91},
        )

        winner, receipt = resolver.resolve_with_decision_receipt("python-pro")

        self.assertEqual(winner, "alpha-python")
        self.assertEqual(receipt.selected_candidate, "alpha-python")
        self.assertFalse(receipt.metadata["requires_intervention"])
        self.assertIn("DETERMINISTIC", receipt.selection_reason)

    def test_planner_refuses_mission_with_unresolved_capability(self):
        with tempfile.TemporaryDirectory() as tmp:
            planner = AutonomousMissionPlanner(
                resolver=_UnresolvedResolverFixture(),
                registry_root=Path(tmp),
                repo_intel=_RepoIntelFixture(),
            )

            with self.assertRaisesRegex(ValueError, "UNRESOLVED_CAPABILITY: missing-capability"):
                planner.plan_mission(
                    goal_title="Fail closed",
                    required_capabilities=["missing-capability"],
                )


if __name__ == "__main__":
    unittest.main()
