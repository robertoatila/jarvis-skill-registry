# Phase 05 — Local software source-validation adapter

Status: PASS_WITH_WARNINGS

Inspected: full Python orchestrator, PowerShell bridge, skillctl ascend/swarm consumers, existing tests and staging effects.

Changed: swe_orchestrator.py, AgenticOrchestrator.psm1, skillctl.ps1, test_agentic_swe.py, runtime.py, verification.py, system_test_runner.py.

Created: four regression tests, real source input in both CLI interfaces, append-only staging runs and per-artifact evidence.

Reused: existing public class/function names, result fields, DAG, atomic snapshot writer and local compiler.

Deprecated: implicit generation of generic SUCCESS source and unverified production-maturity claims. SourceFile/--source is now required at the CLI boundary.

Commands Executed: `python -B -m unittest discover -s tests -p test_agentic_swe.py -v`, exit 0; phase-05-swe.json contains full evidence. PowerShell ParseFile on AgenticOrchestrator.psm1 and skillctl.ps1 reported zero parse errors (exit 0).

Results: supplied source is staged in a unique run directory; syntax is parsed and compiled without executing the source; file hashes, DAG and evidence are saved; prior runs are preserved; CLI failures return a nonzero code. Static validation explicitly reports functional tests, type checking and security certification as NOT_EXECUTED.

Tests Passed: 7 source-adapter tests, 8 verification-guard tests, 4 test-runner accounting tests, and an independent PowerShell bridge check using temporary source and destination. All tests pass with exit code 0.

Tests Not Executed: real dynamic source synthesis, remote model/agent delegation, and functional-test commands for generated products. Lint/typecheck adapters are not configured. JSON Schema validator is absent. Refusing to approve unavailable checks is tested and verified; executing those checks successfully is not claimed.

Compatibility Notes: valid execute_pipeline(target, source_code) callers retain the interface. The bridge no longer certifies a maturity level from a static scan. Legacy calls lacking source fail explicitly; this is intentional removal of fabricated execution.

Known Risks: the implementation is bounded as a local source-validation adapter with static AST and bytecode inspection. Dynamic code generation requires user-provided source. Command execution is delegated to InfrastructureSkillDriver with explicit security filtering and timeouts.

Remaining Uncertainty: live external model generation and third-party remote services remain outside the sovereign local runtime boundary.

Evidence: phase-05-swe.json, phase-05-powershell.json, phase-05-prerequisites.json, phase-05-prerequisites-after.json, phase-05-verification-guards.json, corrected-components-final.json, source/tests, physical backup and phase-05-additional-manifest.json.

Gate: Phase 05 is approved as PASS_WITH_WARNINGS with explicit static source validation boundaries. Dependent phases may advance.

