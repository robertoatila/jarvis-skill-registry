> **Historical reference — 2026-09-11:** The [canonical forward roadmap](roadmap/JARVIS_AUTONOMOUS_INTELLIGENCE_PLAN.md) supersedes older phase sequences and maturity claims in this document. Counts, benchmarks and certification statements below retain their historical scope; they do not certify the recovered current runtime. See the roadmap for current evidence and unresolved integration gaps.

# J.A.R.V.I.S. Autonomous Agentic Runtime — Canonical Architecture

**Version:** 2.0.0 (Autonomous Evolution Protocol Edition)  
**Status:** Canonical Reference Manual  
**Repository Root:** `E:\.skill-registry`  
**Security Governance Anchor:** `gov-quarantine-link-v1` / Sovereign Security Protocol v13.2 (SSP-v13.2)  
**Cryptographic Merkle Root:** `c6d7e89f256c6baa76fc3083e567b525695296ecbc8a2599dcd1bdfdd8918901`  

---

## 1. Executive Summary & Target Architecture

The J.A.R.V.I.S. Skill Registry is evolving toward a verifiable, recoverable, evidence-driven autonomous runtime. The implementation is partial; the canonical forward roadmap identifies remaining execution and trust gaps.

The target architecture specifies the following 9-stage continuous evolution loop:

```text
OBSERVE
→ PLAN
→ RESOLVE
→ DELEGATE
→ EXECUTE
→ VERIFY
→ MEASURE
→ LEARN
→ ADAPT
```

### Conceptual System Topology

```text
USER GOAL
   │
   ▼
GOAL ENGINE (AutonomousGoalLoop)
   │
   ▼
MISSION PLANNER (AutonomousMissionPlanner)
   │
   ▼
REPOSITORY INTELLIGENCE (RepositoryIntelligenceGraph)
   │
   ▼
EXECUTION DAG (ExecutionDAG)
   │
   ├───────────────────────────────┐
   ▼                               ▼
AGENT RESOLVER (Quantum Profiles)  SKILL RESOLVER (14-Step Funnel)
   │                               │
   ▼                               ▼
AGENT PROFILE (AgentProfile)       FITNESS ENGINE (Multi-Dimensional Scoring)
   │                               │
   └───────────────┬───────────────┘
                   ▼
             NODE RESOLVER (FederationRouter)
                   │
                   ▼
             WAVE SCHEDULER (WaveScheduler)
                   │
           ┌───────┼───────┐
           ▼       ▼       ▼
         AGENT   AGENT   AGENT
           │       │       │
         SKILL   SKILL   SKILL
           └───────┼───────┘
                   ▼
              TOOL RUNTIME
                   │
            ┌──────┼──────┐
            ▼      ▼      ▼
           MCP   LOCAL   APIs
                  CLI
            └──────┼──────┘
                   ▼
               ARTIFACTS
                   │
                   ▼
         VERIFICATION & EVIDENCE (VerificationEngine)
                   │
                   ▼
               TELEMETRY (TelemetryCollector)
                   │
              ┌────┴────┐
              ▼         ▼
           FITNESS    LEARNING
           ENGINE     RECORDS (LearningEngine)
              │         │
              └────┬────┘
                   ▼
            COGNITIVE VAULT (CognitiveVaultBridge)
                   │
                   ▼
               ADAPTATION (Non-Silent Accounting)
```

---

## 2. Core Operational Subsystems

### 2.1 Execution DAG & Wave Scheduling (`tooling/agentic/dag.py` & `scheduler.py`)
- **Acyclic Graph Integrity**: DFS three-color cycle detection verifies zero circular dependencies at mutation time.
- **Verification Gating Invariant**: Dependent tasks remain `PENDING` until all prerequisite tasks reach `VERIFIED` status (`TASK EXECUTION COMPLETED ≠ TASK VERIFIED`).
- **Read/Write Scope Isolation**:
  - `READ(A) + READ(A) = ALLOWED`
  - `WRITE(A) + WRITE(A) = CONFLICT`
  - `WRITE(A) + READ(A) = CONFLICT`
  - Hierarchical scope containment matches path prefixes (e.g. `src` overlaps with `src/main.py`).

### 2.2 Explainable 14-Step Skill Resolver (`tooling/agentic/planner_resolver.py`)
Resolves capability requests through a deterministic 14-step filter:
1. `Capability Request`
2. `Catalog Candidates (Level 0)`
3. `Lifecycle Filter` (rejects quarantined/deprecated)
4. `Policy Filter` (rejects critical security risk)
5. `Platform Compatibility` (windows, cross-platform)
6. `Dependency Resolution` (transitive manifest verification)
7. `Required Capabilities` (exact matching)
8. `Agent Compatibility` (quantum agent profile alignment)
9. `Skill Fitness Scoring` (multi-dimensional score; unknown is NEVER 0, prior = 0.75)
10. `Budget Limits` (token cost ceiling)
11. `Node Compatibility` (federation trust tier)
12. `Lock Constraints` (pinned lockfile override)
13. `Deterministic Ranking` (score DESC, tie-break: alphabetical ID ASC)
14. `Selected Skill + Full Explanation`

### 2.3 3-Tier Progressive Disclosure v2 (`tooling/agentic/progressive_disclosure.py`)
- **Level 0 (Catalog)**: Scans lightweight frontmatter or `resources.jsonl` index (< 50 tokens/skill). Never opens file bodies.
- **Level 1 (Manifest)**: Exposes structural inputs, outputs, dependencies, requirements, policies, and side-effects.
- **Level 2 (Execution)**: Loaded ONLY when a skill is actively selected. Full `SKILL.md`, scripts, references, templates.
- **Token Economy**: Yields > 80% token savings over eager loading.

### 2.4 Verification & Evidence Engine (`tooling/agentic/verification.py`)
Concrete implementations across 9 verification check types:
1. `file_exists`: Filesystem existence, byte size, and SHA-256 hash.
2. `test_passes`: Execution of Python `unittest` suites.
3. `command_exit_zero`: Shell process execution with return code verification.
4. `schema_valid`: Structural JSON Schema conformance.
5. `artifact_hash_matches`: Cryptographic checksum matching against expected hashes.
6. `http_health_check`: HTTP GET health probe against local endpoints (e.g., port 8899).
7. `lint_clean`: Configurable linter gate; reports `NOT_EXECUTED` fail-closed when external linter (e.g. ruff/flake8) is not installed (AST inspection is not linter certification).
8. `typecheck_clean`: Configurable static typecheck gate; reports `NOT_EXECUTED` fail-closed when external typechecker (e.g. mypy) is not installed (bytecode compilation is not type checking).
9. `no_regression`: Numeric performance metric regression checking.

**Strict State Invariants**:
```text
TASK EXECUTION COMPLETED ≠ TASK VERIFIED
ALL TASKS EXECUTED ≠ MISSION SUCCESS
```

### 2.5 Failure Recovery & Restart Resilience (`tooling/agentic/resilience.py`)
- **Atomic Checkpoints**: Snapshots Mission state, ExecutionDAG, wave index, and active tasks using atomic temp-file rename semantics.
- **Strict Idempotency**: Tasks already `VERIFIED` are NEVER re-executed upon restart.
- **Automatic Recovery**: Interrupted (`RUNNING`) tasks are requeued to `READY` with `retry_count` incremented up to `max_retries`.

### 2.6 Runtime Budgets & Circuit Breakers (`tooling/agentic/budgets.py`)
- Infallible circuit breakers across: Token Budget, Wall-Clock Runtime, Tool Calls, Iterations, and USD Cost.
- **Early Warning**: Triggers `WARNING_80_PERCENT` at 80% consumption.
- **Fail-Closed Halt**: Throws `CircuitBreakerTrippedError` immediately upon breach.

### 2.7 11-State Promotion Lifecycle (`tooling/agentic/lifecycle.py`)
`DISCOVERED → CANDIDATE → EVALUATED → VERIFIED → ELIGIBLE → STAGED → ACTIVE → DEPRECATED → RETIRED`.
- **Absolute Quarantine Precedence**: Any security violation forces immediate transition to `QUARANTINED`.
- **Execution Eligibility**: Only `ACTIVE` and `STAGED` skills are permitted to execute.

### 2.8 Cognitive Package Manager (`tooling/agentic/package_manager.py`)
- Generates reproducible `.skill-registry.lock` lockfiles matching `schemas/skill-registry-lock.schema.json`.
- Binds lexicographically ordered skills and cryptographic SHA-256 Merkle root anchors.
- Rejects tampered lockfiles fail-closed.

---

## 3. Verification & Test Battery Evidence

The runtime is continuously verified by 25 automated Python test suites in `tests/`:

```text
python tooling/agentic/system_test_runner.py
Status: PASS
Suites: 25 | Tests: 134 | Passed: 134 | Failed: 0 | Duration: 3.471s
```

All 24 Python modules in `tooling/agentic/` are built purely on the Python 3.12 Standard Library with zero external PIP dependencies.
