# Phase 01 — Mission model and execution DAG

Status: PASS_WITH_WARNINGS

Inspected: models.py, dag.py, scheduler consumers, checkpoint serialization, mission schema and the original eight DAG tests.

Changed: `tooling/agentic/models.py`, `tooling/agentic/dag.py`, `schemas/mission-model.schema.json`, `tests/test_agentic_dag.py`.

Created: ten regression tests and the independent command record `phase-01-dag.json`.

Reused: existing model classes, graph API, schema, filesystem snapshots and unittest suite.

Deprecated: no public class or method; invalid status values, missing prerequisites and false VERIFIED transitions are now rejected.

Commands Executed: `python -B -m unittest discover -s tests -p test_agentic_dag.py -v` (exit 0; exact captured output in phase-01-dag.json).

Results: forward declarations resolve in all six insertion orders; rejected cycles do not corrupt the graph; skipped tasks cannot release required dependents; invalid restored data fails explicitly; unique temporary files and atomic replacement preserve the previous snapshot on replacement failure; a fresh Python process restores the complete mission, DAG, retry count, budget and evidence.

Tests Passed: 18. Tests Failed: 0.

Tests Not Executed: lint, static type checking and an external JSON Schema validator are NOT_EXECUTED because those tools are absent in the available Python installations. Runtime validation, JSON serialization, invalid-input checks and restart tests were executed. Full legacy/server execution belongs to subsequent compatibility checks; no end-to-end runtime success is claimed here.

Compatibility Notes: valid versionless DAG snapshots remain accepted; new records carry schema_version 1.0.0. Mission serialization now includes its DAG. Mission IDs accept the existing MIS-, QMIS- and msn- families through a nonempty string contract. Callers that previously marked unchecked requirements VERIFIED need to supply verification results; later-phase orchestrators are subject to that gate.

Known Risks: Python callers can still mutate dataclass fields directly, so graph operations revalidate them. Snapshot replacement is atomic, but multi-process ownership and whole-runtime checkpoint accounting still require Phase 21.

Remaining Uncertainty: scheduler dispatch and later consumers have not yet been certified. This result approves the corrected Phase 01 contract only.

Evidence: phase-01-before.txt, phase-01-dag.json, modified source and the verified backup manifest. No production server, autonomous scheduler, remote service or third-party skill was executed.

## Phase 02 implementation plan

Objective: separate a deterministic schedule plan from permission to dispatch a wave and enforce current dependencies, active locks and capacity at dispatch time.

Existing Components: WaveScheduler, Wave, TaskNode, has_concurrency_conflict, agent profiles.

Changes Required: normalize dot path aliases; validate capacities; track per-agent/per-node capacity; add a current-state wave selector with explicit cancellation, deadline, risk and remaining-budget rejection reasons. A planned earlier wave never implies a verified prerequisite.

Files Expected To Change: scheduler.py, models.py, mission schema, test_agentic_scheduler.py.

Compatibility Constraints: preserve schedule() as a planning API and the existing default four-task limit. Add next_wave() for dispatch; callers must use it immediately before execution.

Persistence Impact: add optional placement/risk/estimate fields with explicit unknown values; keep legacy defaults readable.

Concurrency Impact: active tasks participate in lock and capacity checks. Read/read sharing remains allowed.

Security Impact: constrained dispatch rejects unknown risk/cost estimates. No tasks are actually executed by scheduling.

Test Strategy: old scheduling tests plus alias conflicts, missing nodes, occupied capacity, failed prerequisites, cancelled missions, expired deadlines and exhausted budgets.

Rollback/Risk Notes: source and tests are in the verified backup. Node dispatch and process termination remain integration responsibilities of later phases.
