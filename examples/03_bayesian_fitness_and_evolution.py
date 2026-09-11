"""
examples/03_bayesian_fitness_and_evolution.py
=============================================
J.A.R.V.I.S. Autonomous Agentic Runtime // Protocol v2.0
Zero PIP Dependencies // Pure Python 3.12 Standard Library

This example demonstrates:
  1. The Bayesian Cold-Start Prior (Section 10: Unknown is NEVER 0; prior = 0.75).
  2. Telemetry tracking & dynamic multi-dimensional skill fitness scoring.
  3. Controlled A/B experimentation with deterministic context-hashing.
  4. The 3-Tier Promotion Lifecycle: OBSERVATION -> PATTERN -> VALIDATED_HEURISTIC.
  5. Anti-Hasty Generalization: Strict rejection of single-execution promotions.
"""

from __future__ import annotations
import sys
from pathlib import Path

# Ensure repository root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tooling.agentic.config import JarvisRuntimeConfig
from tooling.agentic.fitness import SkillFitnessEngine, COLD_START_PRIOR
from tooling.agentic.experiments import ExperimentEngine, SkillExperiment, ExperimentVariant
from tooling.agentic.learning import LearningEngine, LearningTier
from tooling.agentic.telemetry import TelemetryCollector


def main():
    print("=" * 70)
    print("  J.A.R.V.I.S. // EXAMPLE 03: BAYESIAN FITNESS & EVOLUTION")
    print("=" * 70)

    config = JarvisRuntimeConfig(registry_root=_REPO_ROOT)
    telemetry = TelemetryCollector(ledger_file=config.telemetry_dir / "example_telemetry.jsonl")
    fitness_engine = SkillFitnessEngine(telemetry_collector=telemetry, config=config)
    exp_engine = ExperimentEngine(config=config)
    learning_engine = LearningEngine(config=config)

    # -----------------------------------------------------------------
    # Section 1: Bayesian Cold-Start Prior
    # -----------------------------------------------------------------
    print("\n[*] Section 1: Bayesian Cold-Start Prior Verification")
    unseen_skill = "novel-quantum-algorithm"
    cold_report = fitness_engine.evaluate_skill(unseen_skill)
    print(f"    - Unseen Skill       : '{unseen_skill}'")
    print(f"    - Is Cold Start      : {cold_report.is_cold_start}")
    print(f"    - Cold-Start Score   : {cold_report.fitness_score}")
    print(f"    - Dimension Scores   : {cold_report.dimension_scores}")
    assert cold_report.is_cold_start is True
    assert cold_report.fitness_score == COLD_START_PRIOR, "Cold start score must equal 0.75"
    print("    >>> Invariant 10 Verified: Unknown skills are initialized to 0.75 (never penalized to 0.0)!")

    # -----------------------------------------------------------------
    # Section 2: Controlled A/B Variant Assignment
    # -----------------------------------------------------------------
    print("\n[*] Section 2: Controlled A/B Experiment Assignment")
    exp = SkillExperiment(
        experiment_id="exp-debug-01",
        capability="systematic-code-debugging",
        variants=[
            ExperimentVariant(variant_id="var-A", skill_id="systematic-code-debugging", weight=1.0),
            ExperimentVariant(variant_id="var-B", skill_id="systematic-debugging", weight=1.0),
        ],
        min_samples_per_variant=3
    )

    # Deterministic assignment based on SHA-256 context hash
    ctx_1 = "mission-auth-fix-42"
    ctx_2 = "mission-auth-fix-42"
    ctx_3 = "mission-db-leak-99"

    var_1 = exp.assign_variant(ctx_1)
    var_2 = exp.assign_variant(ctx_2)
    var_3 = exp.assign_variant(ctx_3)
    print(f"    - Context '{ctx_1}' -> Assigned: {var_1.variant_id} ({var_1.skill_id})")
    print(f"    - Context '{ctx_2}' -> Assigned: {var_2.variant_id} ({var_2.skill_id})")
    print(f"    - Context '{ctx_3}' -> Assigned: {var_3.variant_id} ({var_3.skill_id})")
    assert var_1.variant_id == var_2.variant_id, "Assignment must be deterministic for identical context!"
    print("    >>> Section 8 Verified: Deterministic hash assignment guarantees reproducible experimentation.")

    # -----------------------------------------------------------------
    # Section 3: 3-Tier Knowledge Promotion Lifecycle
    # -----------------------------------------------------------------
    print("\n[*] Section 3: 3-Tier Promotion Lifecycle & Anti-Hasty Generalization")
    
    # 1. Record single observation
    obs = learning_engine.record_observation(
        skill="systematic-code-debugging",
        agent_profile="Quantum-AuditAgent",
        approach="Trace root cause via deterministic AST syntax tree analysis",
        expected_result="Zero syntax regression",
        actual_result="Zero syntax regression verified",
        evidence={"ast_nodes_scanned": 120, "defects_found": 0},
        provenance="mission-debug-01"
    )
    print(f"    - Recorded Observation : ID={obs.record_id} | Tier={obs.tier.value} | Confidence={obs.confidence}")

    # 2. Attempt premature promotion (Single Execution -> Pattern)
    promoted, msg = learning_engine.promote_candidate(
        record=obs,
        new_observations_count=0,
        corroborating_evidence=[]
    )
    print(f"    - Premature Promotion Attempt: Allowed={promoted} | Reason='{msg}'")
    assert promoted is False, "Single execution must NEVER be promoted to pattern or rule!"
    print("    >>> Section 14 Verified: Single-run hasty generalization strictly blocked fail-closed.")

    # 3. Simulate multiple corroborating observations (Tier 1 -> Tier 2: PATTERN)
    promoted_pattern, msg_pattern = learning_engine.promote_candidate(
        record=obs,
        new_observations_count=2,  # total 1 + 2 = 3
        corroborating_evidence=[{"run": 2, "verified": True}, {"run": 3, "verified": True}]
    )
    print(f"    - 3-Run Promotion to PATTERN : Allowed={promoted_pattern} | New Tier={obs.tier.value} | Confidence={obs.confidence}")
    assert promoted_pattern is True
    assert obs.tier == LearningTier.PATTERN

    # 4. Simulate further validation to Tier 3: VALIDATED_HEURISTIC
    promoted_heuristic, msg_heuristic = learning_engine.promote_candidate(
        record=obs,
        new_observations_count=3,  # total 3 + 3 = 6
        corroborating_evidence=[{"run": 4, "verified": True}, {"run": 5, "verified": True}, {"run": 6, "verified": True}]
    )
    print(f"    - 6-Run Promotion to HEURISTIC: Allowed={promoted_heuristic} | New Tier={obs.tier.value} | Confidence={obs.confidence}")
    assert promoted_heuristic is True
    assert obs.tier == LearningTier.VALIDATED_HEURISTIC
    print("    >>> 3-Tier Promotion Complete: OBSERVATION -> PATTERN -> VALIDATED_HEURISTIC successfully achieved.")

    print("\n" + "=" * 70)
    print(">>> SUCCESS: Bayesian Fitness & Closed-Loop Evolution Verified Deterministically!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
