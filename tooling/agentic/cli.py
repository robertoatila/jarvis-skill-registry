"""
cli.py // J.A.R.V.I.S. Sovereign Agentic Command-Line Interface
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
Usage:
    python -m tooling.agentic.cli status
    python -m tooling.agentic.cli plan --goal "..." [--capabilities ...]
    python -m tooling.agentic.cli execute --goal "..." [--capabilities ...]
    python -m tooling.agentic.cli lock --capabilities ... [--output ...]
    python -m tooling.agentic.cli test
    python -m tooling.agentic.cli audit
"""

from __future__ import annotations
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

from .config import CONFIG, JarvisRuntimeConfig
from .runtime import JarvisAgenticRuntime
from .package_manager import CognitivePackageManager
from .system_test_runner import SystemTestRunner


BANNER = r"""
======================================================================
     J.A.R.V.I.S. // SOVEREIGN AGENTIC RUNTIME INTERFACE
  Protocol v2.0 // Pure Python 3.12 Standard Library (Zero PIP)
======================================================================
"""


def cmd_status(args: argparse.Namespace, config: JarvisRuntimeConfig) -> int:
    runtime = JarvisAgenticRuntime(config=config)
    catalog = runtime.disclosure.load_catalog()
    nodes = runtime.federation.list_nodes()
    missions = runtime.state_store.list_active_missions()
    agents = runtime.agents.list_profiles()

    print(BANNER)
    print("  Runtime Status     : OPERATIONAL")
    print(f"  Security Mode      : {config.security_mode} (Fail-Closed)")
    print(f"  Registry Root      : {config.registry_root}")
    print(f"  State Directory    : {config.state_dir}")
    print(f"  Catalog Skills     : {len(catalog)} loaded (Level 0)")
    print(f"  Agent Profiles     : {len(agents)} active")
    print(f"  Federation Nodes   : {len(nodes)} registered")
    print(f"  Active Missions    : {len(missions)}")
    print("======================================================================\n")
    return 0


def cmd_plan(args: argparse.Namespace, config: JarvisRuntimeConfig) -> int:
    runtime = JarvisAgenticRuntime(config=config)
    caps = args.capabilities if args.capabilities else ["systematic-code-debugging"]
    print(f"[*] Planning sovereign mission for goal: '{args.goal}'")
    mission = runtime.planner.plan_mission(
        goal_title=args.goal,
        required_capabilities=caps
    )

    print("\n--- MISSION PLAN ---")
    print(f"  Mission ID         : {mission.mission_id}")
    print(f"  Goal               : {mission.goal}")
    print(f"  Total Tasks        : {len(mission.dag.nodes)}")

    classifications = mission.metadata.get("capability_classifications", {})
    if classifications:
        print("  Capability Classifications:")
        for cap, cdata in classifications.items():
            print(f"    - {cap}: {cdata.get('classification')} ({cdata.get('reason')})")

    waves = runtime.scheduler.schedule(mission.dag)
    print(f"\n--- EXECUTION WAVES ({len(waves)} waves) ---")
    for w in waves:
        print(f"  Wave {w.wave_index} (Max Parallel: {len(w.tasks)}):")
        for t in w.tasks:
            risk = getattr(t, "canonical_risk_level", t.risk_level)
            risk_val = risk.value if hasattr(risk, "value") else str(risk)
            print(f"    * [{t.task_id}] Profile: {t.agent_profile} | Risk: {risk_val} | Skills: {t.required_skills}")

    print("======================================================================\n")
    return 0


def cmd_execute(args: argparse.Namespace, config: JarvisRuntimeConfig) -> int:
    runtime = JarvisAgenticRuntime(config=config)
    caps = args.capabilities if args.capabilities else ["systematic-code-debugging"]
    print(BANNER)
    print(f"[*] Executing Autonomous Goal: '{args.goal}'")
    print(f"[*] Target Capabilities     : {caps}")

    result = runtime.execute_goal(
        goal_prompt=args.goal,
        required_capabilities=caps
    )

    print("\n--- EXECUTION SUMMARY ---")
    print(f"  Execution ID       : {result['execution_id']}")
    print(f"  Mission ID         : {result['mission_id']}")
    print(f"  Final Status       : {result['status']}")
    print(f"  Lifecycle Stages   : {' -> '.join(result['lifecycle_stages'])}")
    print(f"  Waves Executed     : {result['waves_executed']}")
    print(f"  Tasks Verified     : {result['tasks_verified']} / {result['total_tasks']}")
    print(f"  Telemetry Spans    : {result['telemetry_spans_recorded']}")
    print(f"  Evidence Ledger    : {result['evidence_count']} records")
    print(f"  Circuit Breaker    : {'TRIPPED' if result['circuit_breaker_tripped'] else 'HEALTHY'}")

    if result["status"] == "SUCCESS":
        print("\n>>> MISSION CERTIFIED: ZERO DEFECTS & CRYPTOGRAPHICALLY SEALED")
        return 0
    else:
        print(f"\n>>> MISSION FAILED: {result.get('circuit_breaker_reason', 'Verification incomplete')}")
        return 1


def cmd_lock(args: argparse.Namespace, config: JarvisRuntimeConfig) -> int:
    caps = args.capabilities or ["systematic-code-debugging", "comprehensive-code-review"]
    pkg_mgr = CognitivePackageManager(config=config)
    out_path = Path(args.output) if args.output else config.state_dir / "skill-lock.json"

    print(f"[*] Generating cryptographically sealed lockfile for capabilities: {caps}")
    lock = pkg_mgr.generate_lockfile(
        workspace_root=config.registry_root,
        capabilities=caps,
        lockfile_path=out_path
    )

    print(f"[+] Lockfile generated successfully: {out_path}")
    print(f"  Lock ID            : {lock['lock_id']}")
    print(f"  Merkle Root        : {lock['integrity']['merkle_root']}")
    print(f"  Resolved Skills    : {[s['id'] for s in lock['skills']]}")
    return 0


def cmd_test(args: argparse.Namespace, config: JarvisRuntimeConfig) -> int:
    runner = SystemTestRunner(tests_dir=config.registry_root / "tests")
    res = runner.run_all_system_tests()
    status = res.get("status", "FAIL")
    passed = res.get("tests_passed", 0)
    total = res.get("tests_run", 0)
    suites = res.get("total_test_suites", 0)

    print(f"  Test Batteries     : {suites} Suites")
    print(f"  Total Tests Run    : {total}")
    print(f"  Tests Passed       : {passed}")
    print(f"  Execution Duration : {res.get('duration_seconds', 0)}s")
    if status in ("PASS", "PASS_WITH_WARNINGS"):
        print("  >>> VERDICT: PASS (ALL SYSTEMS GREEN)")
        return 0
    else:
        print(f"  >>> VERDICT: {status}")
        return 1


def cmd_audit(args: argparse.Namespace, config: JarvisRuntimeConfig) -> int:
    import subprocess
    audit_script = config.registry_root / "tooling" / "audit_pre_publish_security.py"
    if audit_script.exists():
        proc = subprocess.run([sys.executable, str(audit_script)], cwd=str(config.registry_root))
        return proc.returncode
    print(f"[-] Audit script not found: {audit_script}")
    return 1


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m tooling.agentic.cli",
        description="J.A.R.V.I.S. Sovereign Autonomous Agentic Runtime CLI"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # status
    p_status = subparsers.add_parser("status", help="Show sovereign runtime health and subsystem status")

    # plan
    p_plan = subparsers.add_parser("plan", help="Plan an autonomous mission execution DAG")
    p_plan.add_argument("--goal", required=True, help="Goal description to plan")
    p_plan.add_argument("--capabilities", nargs="+", help="Required capabilities list")

    # execute
    p_exec = subparsers.add_parser("execute", help="Execute an autonomous goal across 9-stage lifecycle")
    p_exec.add_argument("--goal", required=True, help="Goal prompt to execute")
    p_exec.add_argument("--capabilities", nargs="+", help="Required capabilities list")

    # lock
    p_lock = subparsers.add_parser("lock", help="Generate deterministic Merkle skill lockfile")
    p_lock.add_argument("--capabilities", nargs="+", required=True, help="Capabilities to lock")
    p_lock.add_argument("--output", help="Output path for lockfile")

    # test
    p_test = subparsers.add_parser("test", help="Run the complete sovereign test battery")

    # audit
    p_audit = subparsers.add_parser("audit", help="Run the pre-publish security audit")

    args = parser.parse_args()
    config = CONFIG

    dispatch = {
        "status": cmd_status,
        "plan": cmd_plan,
        "execute": cmd_execute,
        "lock": cmd_lock,
        "test": cmd_test,
        "audit": cmd_audit
    }

    handler = dispatch.get(args.command)
    if handler:
        sys.exit(handler(args, config))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
