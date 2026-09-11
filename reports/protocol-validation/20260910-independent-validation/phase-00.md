# Phase 00 — Independent architecture baseline

Status: PASS_WITH_WARNINGS

The working tree already contains an uncommitted implementation and reports for phases 00–28. These are inputs to this review, not evidence of their own correctness. HEAD is recorded in `baseline.json`. No existing implementation is classified as MISSING merely because its claims are not verified.

Inspected: repository status, public Python classes and entry points, the prior architecture and release reports, model/DAG/runtime/scheduler implementations, mission schema, checkpoint store and test runner, and all eight DAG tests.

Changed: no production source during reconnaissance.

Created: this baseline, `baseline.json`, and a physical backup manifest.

Reused: the existing `tooling/agentic` package, `tests`, `schemas`, `reports`, and the existing JSON/JSONL storage layout. QuantumAgentEngine and its four agent identifiers remain compatibility requirements.

Deprecated: no interface.

## Capability classification and reuse map

Classification is relative to the full protocol contract, not file presence. PARTIAL means an implementation exists but its full operational contract still requires verification or correction.

| Phase | Capability | Classification | Existing component |
|---|---|---|---|
| 00 | Architecture baseline | PARTIAL | prior phase reports, docs/ARCHITECTURE.md |
| 01 | Mission + DAG | PARTIAL | models.py, dag.py |
| 02 | Wave scheduler | PARTIAL | scheduler.py |
| 03 | Agent profiles | PARTIAL | profiles.py, jarvis_server.py:QuantumAgentEngine |
| 04 | Composite skills | PARTIAL | composite.py |
| 05 | SWE orchestrator | PARTIAL | swe_orchestrator.py, AgenticOrchestrator.psm1 |
| 06 | Telemetry | PARTIAL | telemetry.py |
| 07 | Runtime HUD | PARTIAL | ui/jarvis.js, jarvis_server.py |
| 08 | Fitness | PARTIAL | fitness.py |
| 09 | Experiments | PARTIAL | experiments.py |
| 10 | Autonomous goals | PARTIAL | goal_loop.py |
| 11 | Repository intelligence | PARTIAL | repo_intel.py |
| 12 | Learning records | PARTIAL | learning.py |
| 13 | Cognitive vault | PARTIAL | vault.py |
| 14 | n8n | PARTIAL | adapters/n8n.py |
| 15 | Infrastructure | PARTIAL | infrastructure.py |
| 16 | Federation | PARTIAL | federation.py, FederationEngine.psm1 |
| 17 | Progressive disclosure | PARTIAL | progressive_disclosure.py |
| 18 | Planner/resolver | PARTIAL | planner_resolver.py, ResolutionEngine.psm1 |
| 19 | Verification/evidence | PARTIAL | verification.py |
| 20 | End-to-end runtime | PARTIAL | runtime.py |
| 21 | Recovery | PARTIAL | resilience.py |
| 22 | Budgets | PARTIAL | budgets.py |
| 23 | Promotion lifecycle | PARTIAL | lifecycle.py, RegistryCore.psm1 |
| 24 | Package manager | PARTIAL | package_manager.py, DistributionEngine.psm1 |
| 25 | Quality review | PARTIAL | quality_review.py |
| 26 | System tests | PARTIAL | system_test_runner.py, test_agentic_*.py |
| 27 | Canonical documentation | PARTIAL | docs/AGENTIC_RUNTIME_ARCHITECTURE.md |
| 28 | Release candidate | CONFLICTING | prior reports/JARVIS_RELEASE_CANDIDATE.md claims PASS beyond demonstrated checks |

Python component paths in this table are relative to `tooling/agentic/`, PowerShell paths to `tooling/`.

## Results and evidence

Commands Executed: commands, exit codes and full repository status are in `baseline.json`. `python -B -m unittest discover -s tests -p test_agentic_dag.py -v` executed successfully: 8 tests, exit 0.

Tests Passed: the eight existing DAG tests.

Tests Failed: no existing test failed. Additional direct probes reproduced four defects: forward dependency ignored; rejected cyclic edge leaves graph cyclic; SKIPPED prerequisite releases dependent; unknown restored task status accepted. These probes are observations, not passing tests.

Tests Not Executed: full legacy and agentic suites, UI, remote adapters, lint, type checking and complete release gates. Some existing tests write shared runtime state; isolation is required before executing them.

Compatibility Notes: preserve constructor and serialization compatibility where valid; invalid states must fail explicitly. Existing reports are physically backed up before correction. No merge, tag, push, publish, deployment or external mutation is authorized.

Known Risks: runtime.py currently creates an executed result without invoking a tool and records fixed token counts; schema and type-check claims exceed the visible implementation; test loader can omit failed imports. Thus this baseline does not certify the previous RC.

Remaining Uncertainty: later-phase integration, real execution, restart safety, security gates and legacy behavior remain to be independently verified.

Evidence: `baseline.json`; backup `E:/\.skill-registry/backups/20260910-independent-validation/manifest.json` (351 files copied, source/copy SHA-256 compared before and after copying).

## Phase 01 implementation plan

Objective: correct dependency integrity, verification gating and restorable mission data before relying on the scheduler.

Existing Components: TaskNode, Mission, MissionBudget, VerificationRequirement, ExecutionDAG and their existing test suite/schema.

Changes Required: transactional graph mutations; forward-reference resolution; explicit missing references and invalid restored states; verification requirement gating; versioned deterministic serialization and atomic replacement; preserve a mission's DAG when serializing.

Files Expected To Change: models.py, dag.py, mission-model.schema.json, test_agentic_dag.py, and this evidence directory.

Compatibility Constraints: retain valid versionless legacy input and public names; reject corrupt input and unsupported schema versions rather than invent state. Quantum engine code remains untouched by Phase 01.

Persistence Impact: add schema_version 1.0.0; preserve existing valid fields; atomically replace snapshots after validation.

Concurrency Impact: unique temporary paths prevent writer collisions; failed mutations leave the prior graph intact. Multi-process mission ownership remains a later-phase concern.

Security Impact: no commands, network, catalog payloads or quarantine access in Phase 01 tests.

Test Strategy: existing tests plus adversarial dependency ordering, cyclic mutation rollback, corrupt restore, pending verification, failed file replacement and serialization/restart tests in temporary directories.

Rollback/Risk Notes: originals are verified in the backup manifest. Valid legacy input is covered by tests; callers that supplied invalid status values will now receive ValueError.
