# Phase 04 — Composite skills and dependency graph

Status: PASS_WITH_WARNINGS

Inspected: CompositeSkill, SubSkillReference, SkillDependencyGraph, legacy disclosure reader, newer disclosure engine and original tests/schema.

Changed: composite.py, composite-skill.schema.json, test_agentic_composite.py.

Created: atomic/versioned composite snapshots and five regression tests. The existing disclosure test now uses a temporary fixture instead of reading a real skill payload.

Reused: ExecutionDAG, atomic JSON writer, declaration format and legacy disclosure return fields.

Deprecated: no API.

Commands Executed: `python -B -m unittest discover -s tests -p test_agentic_composite.py -v`, exit 0; exact output in phase-04-composite.json.

Results: 9 tests passed; 0 failed. Unknown endpoints and duplicate aliases fail explicitly; rejected cycles preserve the dependency graph; deterministic snapshots restore; expanded scopes do not alias original lists; traversal is rejected before reads; metadata discovery stops at the closing frontmatter delimiter.

Tests Passed: 9. Tests Failed: 0. Tests Not Executed: filesystem junction/symlink creation test (path guards inspected but not yet independently exercised); live catalog policy/activation checks; external schema validator, lint and type checker unavailable.

Compatibility Notes: existing graph tests pass. Valid legacy declarations remain supported. No execution eligibility or quarantine approval is implied by reading metadata; those checks remain mandatory in the resolver/execution path.

Known Risks: the newer disclosure implementation is still separate and needs adapter consolidation in Phase 17. File-path checks alone do not replace lifecycle/quarantine policy.

Remaining Uncertainty: live catalog integration and selected-skill execution remain unverified.

Evidence: phase-04-composite.json, source/tests and verified backup manifest.

## Phase 05 implementation plan

Objective: make the local source-validation pipeline report real work and remove fabricated source generation from its CLI bridge.

Existing Components: SoftwareEngineeringOrchestrator, SWEOrchestrationResult, AgenticOrchestrator.psm1, skillctl ascend/swarm.

Changes Required: explicit source input; append-only staging; actual compilation plus artifact hashes; required-check evidence; preserve failure exit codes; communicate limited static validation without claiming repository synthesis, functional correctness, security certification or production maturity.

Files Expected To Change: swe_orchestrator.py, AgenticOrchestrator.psm1, skillctl.ps1, test_agentic_swe.py.

Compatibility Constraints: retain function/class names and result fields. Calls without source now fail explicitly instead of producing generic code. Add optional SourceFile CLI input; a successful static check is not a promotion.

Persistence Impact: unique staging run directories and versioned DAG/evidence snapshots; original source is never overwritten.

Concurrency Impact: unique directories isolate concurrent calls. No subagents or remote jobs are started by this local validation adapter.

Security Impact: compile supplied code without importing or executing it; reject invalid target identifiers; no remote fetch, deployment, promotion or external mutation.

Test Strategy: isolated temp-root success/syntax/placeholder tests, no overwrite, real compilation evidence/hash verification, and missing-input/nonzero CLI behavior. Parse the PowerShell adapter and exercise it with temporary local input only.

Rollback/Risk Notes: Python originals were already backed up; PowerShell originals copied and hash-verified in phase-05-additional-manifest.json. Full engineering automation and real tool execution require later runtime integration.
