"""Public fail-closed planner/resolver facade for J.A.R.V.I.S. v0.2.

The historical implementation remains in ``planner_resolver_core``. This facade
preserves public imports while preventing synthetic skill identities and
synthetic verification commands from crossing the planning boundary.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import List, Optional, Tuple

from .decision_receipt import DecisionReceipt, DecisionType
from .fitness import COLD_START_PRIOR
from .planner_resolver_core import *
from .planner_resolver_core import (
    AutonomousMissionPlanner as _CoreAutonomousMissionPlanner,
    AutonomousSkillResolver as _CoreAutonomousSkillResolver,
)


_BLOCKED_LIFECYCLE_STATES = {"QUARANTINED", "BROKEN", "DISABLED"}


class AutonomousSkillResolver(_CoreAutonomousSkillResolver):
    """Resolve only catalog-backed, admitted skills; never fabricate winners."""

    @staticmethod
    def _empty_explanation(capability_request: str) -> SkillResolutionExplanation:
        return SkillResolutionExplanation(
            resolution_id=f"res-{uuid.uuid4().hex[:12]}",
            capability_request=capability_request,
            tie_break_rules=[
                "Score DESC",
                "ColdStart Prior (0.75) if unmeasured",
                "Alphabetical Skill ID ASC",
            ],
        )

    @staticmethod
    def _matching_catalog_ids(catalog, capability_request: str) -> List[str]:
        normalized_req = capability_request.lower().replace("_", "-")
        candidate_ids: List[str] = []
        for sid, entry in catalog.items():
            caps_norm = [cap.lower().replace("_", "-") for cap in entry.capabilities]
            tags_norm = [tag.lower().replace("_", "-") for tag in entry.tags]
            if (
                normalized_req in sid.lower()
                or normalized_req in caps_norm
                or normalized_req in tags_norm
                or normalized_req in entry.description.lower()
            ):
                candidate_ids.append(sid)
        if not candidate_ids:
            for sid in catalog:
                if "python" in normalized_req and "python" in sid:
                    candidate_ids.append(sid)
                elif "test" in normalized_req and "test" in sid:
                    candidate_ids.append(sid)
                elif "audit" in normalized_req and "audit" in sid:
                    candidate_ids.append(sid)
        return sorted(set(candidate_ids))

    def resolve(
        self,
        capability_request: str,
        target_platform: str = "windows",
        agent_profile: Optional[str] = None,
        max_cost_tokens: int = 50000,
        target_node_id: Optional[str] = None,
        lock_pinned_skill: Optional[str] = None,
    ) -> SkillResolutionExplanation:
        catalog = self.disclosure.load_catalog()

        if lock_pinned_skill and lock_pinned_skill not in catalog:
            explanation = self._empty_explanation(capability_request)
            explanation.candidates = self._matching_catalog_ids(catalog, capability_request)
            explanation.rejected_candidates[lock_pinned_skill] = "PINNED_SKILL_NOT_FOUND"
            explanation.selection_reason = "PINNED_SKILL_NOT_FOUND"
            return explanation

        if self.experiments and not lock_pinned_skill:
            active_exp = self.experiments.get_experiment_for_capability(capability_request)
            if active_exp and active_exp.status == "ACTIVE":
                explanation = super().resolve(
                    capability_request=capability_request,
                    target_platform=target_platform,
                    agent_profile=agent_profile,
                    max_cost_tokens=max_cost_tokens,
                    target_node_id=target_node_id,
                    lock_pinned_skill=lock_pinned_skill,
                )
                selected = explanation.selected_candidate
                entry = catalog.get(selected) if selected else None
                lifecycle = getattr(entry, "lifecycle_state", None) if entry else None
                if entry is None or lifecycle in _BLOCKED_LIFECYCLE_STATES:
                    if selected:
                        explanation.rejected_candidates[selected] = (
                            "REJECTED_NOT_IN_CATALOG"
                            if entry is None
                            else f"REJECTED_LIFECYCLE_{lifecycle}"
                        )
                    explanation.selected_candidate = None
                    explanation.selection_reason = "NO_CANDIDATE_AVAILABLE"
                return explanation

        if not self._matching_catalog_ids(catalog, capability_request) and not lock_pinned_skill:
            explanation = self._empty_explanation(capability_request)
            explanation.selection_reason = "NO_CANDIDATE_AVAILABLE"
            return explanation

        explanation = super().resolve(
            capability_request=capability_request,
            target_platform=target_platform,
            agent_profile=agent_profile,
            max_cost_tokens=max_cost_tokens,
            target_node_id=target_node_id,
            lock_pinned_skill=lock_pinned_skill,
        )

        for sid in list(explanation.candidates):
            entry = catalog.get(sid)
            if entry is None:
                explanation.rejected_candidates.setdefault(sid, "REJECTED_NOT_IN_CATALOG")
                continue
            lifecycle = getattr(entry, "lifecycle_state", None)
            if lifecycle in _BLOCKED_LIFECYCLE_STATES:
                explanation.rejected_candidates[sid] = f"REJECTED_LIFECYCLE_{lifecycle}"

        selected = explanation.selected_candidate
        if selected and selected in catalog and selected not in explanation.rejected_candidates:
            return explanation

        eligible = [
            sid
            for sid in explanation.scores
            if sid in catalog and sid not in explanation.rejected_candidates
        ]
        if eligible:
            ranked = sorted(
                eligible,
                key=lambda sid: (-explanation.scores.get(sid, COLD_START_PRIOR), sid),
            )
            winner = ranked[0]
            score = explanation.scores.get(winner, COLD_START_PRIOR)
            explanation.selected_candidate = winner
            explanation.selection_reason = (
                f"OPTIMAL_FITNESS_SCORE ({score}) WITH DETERMINISTIC_TIE_BREAK"
            )
            return explanation

        explanation.selected_candidate = None
        explanation.selection_reason = "NO_CANDIDATE_AVAILABLE"
        return explanation

    def resolve_with_decision_receipt(
        self,
        capability_request: str,
        target_platform: str = "windows",
        lock_pinned_skill: Optional[str] = None,
    ) -> Tuple[Optional[str], DecisionReceipt]:
        explanation = self.resolve(
            capability_request=capability_request,
            target_platform=target_platform,
            lock_pinned_skill=lock_pinned_skill,
        )
        winner = explanation.selected_candidate
        score = explanation.scores.get(winner, COLD_START_PRIOR) if winner else 0.0
        receipt = DecisionReceipt(
            decision_id=f"dec-skill-{uuid.uuid4().hex[:8]}",
            decision_type=DecisionType.SKILL_SELECTION,
            candidates=list(explanation.candidates),
            rejected_candidates=dict(explanation.rejected_candidates),
            scores=dict(explanation.scores),
            selected_candidate=winner or "",
            selection_reason=explanation.selection_reason,
            confidence=round(score, 2),
            metadata={
                "capability_request": capability_request,
                "tie_break_rules": explanation.tie_break_rules,
                "requires_intervention": winner is None,
                "unresolved_capability": capability_request if winner is None else None,
            },
        )
        return winner, receipt


class AutonomousMissionPlanner(_CoreAutonomousMissionPlanner):
    """Mission planner that refuses unresolved or unbound execution authority."""

    def __init__(
        self,
        resolver: Optional[AutonomousSkillResolver] = None,
        registry_root: Optional[Path] = None,
        repo_intel: Optional[RepositoryIntelligenceGraph] = None,
        config: Optional[JarvisRuntimeConfig] = None,
    ):
        super().__init__(
            resolver=resolver or AutonomousSkillResolver(config=config),
            registry_root=registry_root,
            repo_intel=repo_intel,
            config=config,
        )

    def plan_mission(
        self,
        goal_title: str,
        goal_description: str = "",
        required_capabilities: Optional[List[str]] = None,
        target_platform: str = "windows",
    ) -> Mission:
        capabilities = required_capabilities or ["systematic-code-debugging"]
        for capability in capabilities:
            resolution = self.resolver.resolve(
                capability_request=capability,
                target_platform=target_platform,
            )
            if resolution.selected_candidate is None:
                raise ValueError(f"UNRESOLVED_CAPABILITY: {capability}")

        mission = super().plan_mission(
            goal_title=goal_title,
            goal_description=goal_description,
            required_capabilities=capabilities,
            target_platform=target_platform,
        )

        # The legacy core synthesized COMMAND_EXIT_ZERO requirements even when
        # it produced no executable action. Verification is evidence about an
        # execution, never authority to create or substitute that execution.
        for task in mission.dag.nodes.values():
            if task.action is None:
                task.verification_requirements = []
        return mission
