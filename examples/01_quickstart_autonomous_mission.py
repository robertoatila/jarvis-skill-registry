"""
examples/01_quickstart_autonomous_mission.py
============================================
J.A.R.V.I.S. Autonomous Agentic Runtime // Protocol v2.0
Zero PIP Dependencies // Pure Python 3.12 Standard Library

This example demonstrates:
  1. Initializing the sovereign runtime with fail-closed security.
  2. Planning a goal into a deterministic execution DAG.
  3. Scheduling conflict-free execution waves (Read/Write scope isolation).
  4. Executing and cryptographically verifying every task.
  5. Recording telemetry and state without external dependencies.
"""

from __future__ import annotations
import sys
from pathlib import Path

# Ensure repository root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tooling.agentic.config import JarvisRuntimeConfig
from tooling.agentic.runtime import JarvisAgenticRuntime


def main():
    print("=" * 70)
    print("  J.A.R.V.I.S. // EXAMPLE 01: QUICKSTART AUTONOMOUS MISSION")
    print("=" * 70)

    # 1. Initialize Sovereign Runtime
    config = JarvisRuntimeConfig(
        registry_root=_REPO_ROOT,
        security_mode="FAIL_CLOSED"
    )
    runtime = JarvisAgenticRuntime(config=config)
    print(f"[+] Runtime initialized in FAIL_CLOSED mode at: {config.registry_root}")

    # 2. Define Goal
    goal = "Execute deterministic code audit and systematic debugging verification"
    capabilities = ["systematic-code-debugging", "comprehensive-code-review"]
    print(f"[*] Goal: '{goal}'")
    print(f"[*] Capabilities requested: {capabilities}\n")

    # 3. Plan the Mission DAG
    print("[*] Stage 1: Planning Mission DAG...")
    mission = runtime.planner.plan_mission(goal_title=goal, required_capabilities=capabilities)
    print(f"    - Mission ID  : {mission.mission_id}")
    print(f"    - Total Tasks : {len(mission.dag.nodes)}")

    # 4. Schedule into Waves (Conflict-Free Concurrency)
    print("[*] Stage 2: Scheduling Execution Waves...")
    waves = runtime.scheduler.schedule(mission.dag)
    print(f"    - Execution Waves: {len(waves)}")
    for wave in waves:
        print(f"      * Wave {wave.wave_index}: {len(wave.tasks)} tasks | Agents: {[t.agent_profile for t in wave.tasks]}")

    # 5. Execute Across the 9-Stage Autonomous Closed Loop
    print("\n[*] Stage 3: Executing Closed Loop (OBSERVE -> PLAN -> RESOLVE -> DELEGATE -> EXECUTE -> VERIFY -> MEASURE -> LEARN -> ADAPT)...")
    result = runtime.execute_goal(goal_prompt=goal, required_capabilities=capabilities)

    # 6. Verify Deterministic Output & Cryptographic Evidence
    print("\n" + "=" * 70)
    print("  MISSION EXECUTION OUTCOME")
    print("=" * 70)
    print(f"  Execution ID    : {result['execution_id']}")
    print(f"  Status          : {result['status']}")
    print(f"  Waves Executed  : {result['waves_executed']}")
    print(f"  Tasks Verified  : {result['tasks_verified']} / {result['total_tasks']}")
    print(f"  Telemetry Spans : {result['telemetry_spans_recorded']}")
    print(f"  Evidence Count  : {result['evidence_count']}")
    print(f"  Circuit Breaker : {'HEALTHY' if not result['circuit_breaker_tripped'] else 'TRIPPED'}")
    print("=" * 70)
    print(">>> SUCCESS: Mission planned, executed, and verified with zero external dependencies!\n")


if __name__ == "__main__":
    main()
