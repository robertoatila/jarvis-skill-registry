"""
benchmarks/benchmark_runtime_latency.py
=======================================
J.A.R.V.I.S. Latency & Performance Micro-Benchmark
Measures sub-millisecond execution overhead of the sovereign runtime.
Pure Python 3.12 Standard Library // Zero PIP Dependencies
"""

from __future__ import annotations
import argparse
import sys
import time
import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tooling.agentic.config import JarvisRuntimeConfig
from tooling.agentic.runtime import JarvisAgenticRuntime
from tooling.agentic.policy import PolicyEngine
from tooling.agentic.profiles import AgentProfile, AgentConstraints
from tooling.agentic.models import RiskLevel
from tooling.agentic.package_manager import CognitivePackageManager


DEFAULT_REPORT_PATH = _REPO_ROOT / "benchmarks" / "runtime_latency_report.json"


def benchmark(output: Path | None = DEFAULT_REPORT_PATH):
    """Run the micro-benchmark; write the report to ``output`` unless it is None."""
    config = JarvisRuntimeConfig(registry_root=_REPO_ROOT)
    runtime = JarvisAgenticRuntime(config=config)
    policy_engine = PolicyEngine(config=config)
    pkg_mgr = CognitivePackageManager(config=config)

    agent = AgentProfile(
        agent_id="Quantum-AuditAgent",
        name="Audit Agent",
        domain="Security",
        skills=["systematic-code-debugging"],
        allowed_tools=["*"],
        constraints=AgentConstraints(read_only=True, network_access=False)
    )

    results = {}
    iterations = 50

    # 1. Benchmark Policy Engine Authorization Check
    start = time.perf_counter()
    for _ in range(iterations):
        policy_engine.evaluate_policy(
            agent_profile=agent,
            action="read_file",
            tool_or_skill="code-review",
            resource=str(_REPO_ROOT / "state"),
            risk_level=RiskLevel.R0_READ_ONLY
        )
    dur_policy = (time.perf_counter() - start) / iterations * 1000.0
    results["policy_evaluation_latency_ms"] = round(dur_policy, 4)

    # 2. Benchmark Mission Planning & DAG Generation
    start = time.perf_counter()
    for _ in range(iterations):
        runtime.planner.plan_mission(
            goal_title="Benchmark Mission",
            required_capabilities=["systematic-code-debugging"]
        )
    dur_plan = (time.perf_counter() - start) / iterations * 1000.0
    results["mission_planning_latency_ms"] = round(dur_plan, 4)

    # 3. Benchmark Wave Scheduling (Conflict Checking)
    mission = runtime.planner.plan_mission(
        goal_title="Benchmark Mission",
        required_capabilities=["systematic-code-debugging", "comprehensive-code-review"]
    )
    start = time.perf_counter()
    for _ in range(iterations):
        runtime.scheduler.schedule(mission.dag)
    dur_sched = (time.perf_counter() - start) / iterations * 1000.0
    results["wave_scheduling_latency_ms"] = round(dur_sched, 4)

    # 4. Benchmark Merkle Lockfile Generation
    start = time.perf_counter()
    for _ in range(iterations):
        pkg_mgr.generate_lockfile(
            workspace_root=_REPO_ROOT,
            capabilities=["systematic-code-debugging", "comprehensive-code-review"]
        )
    dur_lock = (time.perf_counter() - start) / iterations * 1000.0
    results["merkle_lockfile_latency_ms"] = round(dur_lock, 4)

    # 5. Benchmark End-to-End Mission Execution
    start = time.perf_counter()
    res = runtime.execute_goal(
        goal_prompt="Benchmark Goal",
        required_capabilities=["systematic-code-debugging"]
    )
    dur_exec = (time.perf_counter() - start) * 1000.0
    results["e2e_goal_execution_latency_ms"] = round(dur_exec, 4)
    results["mission_status"] = res["status"]
    results["measurement_scope"] = "local planning and fail-closed execution; no model calls"

    print("=" * 70)
    print("  J.A.R.V.I.S. // RUNTIME LATENCY & OVERHEAD BENCHMARK")
    print("=" * 70)
    print(f"  Iterations per Benchmark : {iterations}")
    print(f"  Policy Auth Evaluation   : {results['policy_evaluation_latency_ms']:.3f} ms / check")
    print(f"  Mission DAG Planning     : {results['mission_planning_latency_ms']:.3f} ms / plan")
    print(f"  Wave Conflict Scheduling : {results['wave_scheduling_latency_ms']:.3f} ms / schedule")
    print(f"  Merkle Lock Generation   : {results['merkle_lockfile_latency_ms']:.3f} ms / lock")
    print(f"  End-to-End Goal Run      : {results['e2e_goal_execution_latency_ms']:.3f} ms (9-stage loop)")
    print("=" * 70)
    print(">>> Measurements recorded; latency does not certify mission success\n")

    if output is None:
        print("[+] Report not written (--no-write)")
    else:
        report_path = Path(output)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"[+] Saved report to: {report_path}")
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local runtime latency micro-benchmark (no model calls).")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help="Report path (default: the tracked benchmarks/runtime_latency_report.json)",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Print measurements without writing a report; timings are machine-specific",
    )
    return parser


if __name__ == "__main__":
    _args = build_parser().parse_args()
    benchmark(None if _args.no_write else _args.output)
