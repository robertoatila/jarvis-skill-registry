# Phase 02 — Wave scheduler

Status: PASS_WITH_WARNINGS

Inspected: WaveScheduler, Wave, scope normalization, task model, agent capacity declarations and existing scheduling tests.

Changed: models.py, scheduler.py, mission-model.schema.json, test_agentic_scheduler.py.

Created: next_wave() dispatch selector and seven dispatch regression tests.

Reused: existing scheduler, DAG, task states and read/write conflict semantics.

Deprecated: no API. schedule() remains a deterministic planning API; a plan does not authorize execution.

Commands Executed: `python -B -m unittest discover -s tests -p test_agentic_scheduler.py -v`, exit 0 (captured in phase-02-scheduler.json).

Results: 15 tests passed, 0 failed. Current-state dispatch blocks failed prerequisites, excludes completed tasks, respects occupied locks, enforces node/agent capacities and refuses unknown nodes. Read/read sharing is preserved. Dot path aliases conflict. Cancellation, deadline, constrained risk and unknown/insufficient cost/token estimates block selection.

Tests Passed: 15. Tests Failed: 0. Tests Not Executed: real parallel tool execution and process timeout termination; these belong to the execution integration phases. Lint and static type checker unavailable.

Compatibility Notes: existing valid planning tests still pass. Optional placement/estimate fields restore from legacy defaults. Unknown estimates remain null. Other callers must adopt next_wave immediately before dispatch; this report does not certify the old runtime's use of a precomputed plan.

Known Risks: scope normalization does not provide a filesystem sandbox or detect every filesystem alias; concrete tool paths must also be confined at execution. Persistent multi-process locks and node dispatch still require later integration.

Remaining Uncertainty: later runtime integration and cross-process execution are not verified.

Evidence: phase-02-scheduler.json and modified source/tests. Originals are in the verified backup manifest.

## Phase 03 implementation plan

Objective: require an agent to satisfy every requested capability/skill and constraint, and preserve its profile across restart.

Existing Components: AgentProfile, AgentConstraints, AgentBudgetLimits, AgentProfileRegistry and the four Quantum identifiers.

Changes Required: strict validation, reject offline/unqualified profiles, evaluate tool/write/network/capacity and task-budget requirements, retain deterministic ranking and explanations, version profile snapshots.

Files Expected To Change: profiles.py, dag.py (reuse its atomic JSON writer), tests/test_agentic_profiles.py and agent-profile.schema.json.

Compatibility Constraints: preserve identifiers and valid constructors. Previously selected profiles missing mandatory capabilities will correctly produce no selection.

Persistence Impact: opt-in profile save/load with version checking. No autonomous global config writes.

Concurrency Impact: explicit capacity on profiles feeds the existing scheduler; profiles do not claim to enforce a process sandbox.

Security Impact: constraints are authorization inputs, not claims that a sandbox exists. Remove unverified audit percentages from profile badges.

Test Strategy: existing six tests plus no-match/partial-match/offline/write/network/tool/budget/capacity rejection and save/load corruption checks in temporary directories.

Rollback/Risk Notes: verified backup retained. Legacy server is inspected without importing it, since its module initialization starts background behavior.
