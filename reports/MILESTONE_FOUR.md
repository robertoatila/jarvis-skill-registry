# Milestone 4 Certification: Planning, Routing, Decision Receipts, and Local SWE Orchestration
**J.A.R.V.I.S. Autonomous Evolution Protocol v2.0**
**Date**: September 11, 2026 | **Workspace**: `E:\.skill-registry` | **Platform**: Windows / Pure Python 3.12 Standard Library

---

## 1. Executive Summary

Milestone 4 (**Phases 23–29**) integrates the autonomous cognitive control loop with deterministic, explainable routing, immutable decision audit trails, dynamic graph replanning, and local software engineering patch orchestration.

With zero external pip dependencies, J.A.R.V.I.S. now enforces:
1. **Dynamic Graph Replanning**: Targeted invalidation and downstream replanning (`replan_affected_region`) in `AutonomousMissionPlanner`, resetting affected tasks while preserving verified upstream work and emitting formal decision receipts.
2. **Unified Decision Receipts Architecture**: The `DecisionReceipt` dataclass strictly decouples pre-execution estimates (`estimated_cost_usd`, `estimated_tokens`, `confidence`) from terminal outcomes (`actual_cost_usd`, `actual_tokens`, `actual_outcome`). Pre-execution estimates are immutable and never mutated post-hoc.
3. **Constrained Autonomous Tool Routing**: `ToolRouter` evaluates hard authority, scope, and capability constraints before ranking. Rejects missing capabilities with an explicit `BLOCKED` receipt (fail-closed, never hallucinates or invents tools), and scores survivors by risk and cost trade-offs.
4. **Cost-Aware Privacy-First Model Routing**: `ModelRouter` enforces sovereign local execution for sensitive scopes/keys, validates context window token limits, respects budget headroom, and follows a tiered cost escalation sequence.
5. **Explainable Profile & Skill Resolution**: `AutonomousSkillResolver` and `AgentProfileRegistry` emit unified `DecisionReceipt`s providing mathematical justification and rejected candidate logs for skill and agent dispatch.
6. **Local Software Engineering Orchestration**: `SoftwareEngineeringOrchestrator.apply_and_verify_patch` uses `LocalActionAdapter` for atomic file writes and optimistic concurrency, with strict separation between static AST syntax verification and functional test execution.

---

## 2. Architecture & Subsystem Implementations

### Phase 23: Dynamic Region Replanning (`tooling/agentic/planner_resolver.py`)
- **`AutonomousMissionPlanner.replan_affected_region(mission, invalidated_task_ids, invalidation_reason)`**:
  - Traverses the task DAG iteratively from the invalidated root tasks down through all direct and transitive dependents.
  - Resets all downstream affected tasks to `READY` status, increments retry counts, and clears stale execution results.
  - Strictly preserves verified upstream nodes and independent tasks, leaving their state untouched.
  - Emits an auditable `DecisionReceipt` of type `REPLANNING` and records the replan event into `mission.metadata["replan_history"]`.

### Phase 24 & 25: Explainable Agent & Skill Resolution (`tooling/agentic/profiles.py`, `planner_resolver.py`)
- **`AgentProfileRegistry.resolve_agent_with_decision_receipt`**:
  - Resolves optimal agent candidates against required capabilities, tools, and constraints.
  - Returns a unified `DecisionReceipt` (type `AGENT_SELECTION`) capturing candidate scores, rejected agent rationale, and confidence.
- **`AutonomousSkillResolver.resolve_with_decision_receipt`**:
  - Resolves required skill capabilities against disclosure catalogs, fitness scores, and platform compatibility.
  - Emits an immutable `DecisionReceipt` (type `SKILL_SELECTION`) detailing selection reason and candidate rankings.

### Phase 26: Constrained Autonomous Tool Router (`tooling/agentic/tool_router.py`)
- **`ToolRouter`**:
  - *Hard Constraint Filtering*: Matches required task capabilities against tool catalogs. Rejects missing capabilities with an explicit `BLOCKED` decision (fail-closed, zero hallucination).
  - *Risk Ceiling Enforcement*: Enforces task-assigned risk ceilings (`R0_READ_ONLY` through `R5_DESTRUCTIVE`), filtering out tools that exceed policy boundaries.
  - *Deterministic Utility Ranking*: Scores admissible survivors based on risk minimization and invocation cost (`Score = 100 - (Risk_Tier * 10) - (Cost_USD * 50)`).
  - *DecisionReceipt Emission*: Logs all evaluated, rejected, and winning tools with selection rationale.

### Phase 27: Cost-Aware Privacy-First Model Router (`tooling/agentic/model_router.py`)
- **`ModelRouter`**:
  - *Privacy Enforcement*: Enforces mandatory local sovereign execution (`sovereign-local-deepseek-8b`) whenever tasks touch sensitive scopes (keys, tokens, credentials, vault). Rejects cloud models immediately.
  - *Context Window Capacity*: Verifies candidate model context windows against required prompt and token lengths (e.g. 1M token window for Gemini 2.0 Flash).
  - *Budget Headroom & Escalation*: Starts with zero-cost local sovereign models, escalating to economy cloud and frontier models only when capabilities or context demand it.
  - *DecisionReceipt Emission*: Generates formal audit receipts for model selection.

### Phase 28: Unified Decision Receipts Subsystem (`tooling/agentic/decision_receipt.py`)
- **`DecisionReceipt`**:
  - Canonical data structure capturing `decision_id`, `decision_type` (`TOOL_ROUTING`, `MODEL_ROUTING`, `AGENT_SELECTION`, `SKILL_SELECTION`, `REPLANNING`, etc.), `candidates`, `rejected_candidates`, `scores`, `selected_candidate`, `selection_reason`, `confidence`, `estimated_cost_usd`, and `estimated_tokens`.
  - **Immutable Estimates Invariant**: Pre-execution estimates are locked. `attach_actual_outcome(actual_cost_usd, actual_tokens, actual_outcome)` records actual terminal metrics into dedicated fields without altering the pre-decision estimates.

### Phase 29: Local SWE Orchestration (`tooling/agentic/swe_orchestrator.py`)
- **`SoftwareEngineeringOrchestrator.apply_and_verify_patch`**:
  - Executes patches atomically within the workspace boundary via `LocalActionAdapter` (`local.write_text`).
  - Implements optimistic concurrency protection via `expected_before_sha256`.
  - Enforces strict two-stage verification:
    1. *Stage 1*: Static AST inspection and compilation (`py_compile`), validating syntax and detecting placeholders/TODOs.
    2. *Stage 2*: Functional test command execution in subprocess.
  - Strictly adheres to the core sovereign axiom: **Syntax Clean ≠ Functionally Verified**. Functional execution is bypassed if syntax is broken, preventing unsafe execution.

---

## 3. End-to-End Runtime Integration (`tooling/agentic/runtime.py`)

The `JarvisAgenticRuntime` has been updated to wire all Milestone 4 capabilities into the complete 9-stage evolution lifecycle:
- `ToolRouter` and `ModelRouter` are initialized and invoked per-task during Stage 5 (EXECUTE).
- Generated `DecisionReceipt`s are attached to mission metadata and evidence ledgers.
- Upon task completion or verification, actual tokens, cost, and execution outcomes are attached to the receipts.
- `SoftwareEngineeringOrchestrator` is integrated as an authoritative local code modification and verification service.

---

## 4. Verification & Testing Evidence

### Master Test Battery (`run_tests.py`)
```
======================================================================
     J.A.R.V.I.S. // AUTONOMOUS AGENTIC RUNTIME TEST BATTERY
  Sovereign Evolution Protocol v2.0 // Pure Python 3.12 Stdlib
======================================================================

  Target Workspace   : E:\.skill-registry
  Test Batteries     : 36 Suites
  Total Tests Run    : 215
  Tests Passed       : 215
  Tests Failed       : 0
  Tests Errored      : 0
  Execution Duration : 45.141s
----------------------------------------------------------------------
  >>> VERDICT: PASS (ALL SYSTEMS GREEN)
======================================================================
```

### Dedicated Milestone 4 Test Suite (`tests/test_agentic_m4_adaptation_learning.py`)
- `test_decision_receipt_immutability_and_outcome`: PASSED.
- `test_tool_router_capability_filtering`: PASSED.
- `test_tool_router_deterministic_ranking`: PASSED.
- `test_model_router_privacy_enforcement`: PASSED.
- `test_model_router_context_capacity_and_cost`: PASSED.
- `test_planner_replan_affected_region`: PASSED.
- `test_resolver_and_profile_decision_receipts`: PASSED.
- `test_swe_orchestrator_apply_and_verify_patch`: PASSED.

### Sovereign Pre-Publish Security Audit (`tooling/audit_pre_publish_security.py`)
```
================================================================================
J.A.R.V.I.S. // PROTOCOLO DE SEGURANCA SOBERANA v13 (SSP-v13)
AUDITORIA DETERMINISTICA PRE-PUBLICACAO DO REPOSITORIO
================================================================================
[*] Regras de exclusao .gitignore carregadas: 70 regras ativas
[+] Verificacao de Custodia: 'config/api_keys.json' devidamente blindado pelo .gitignore (FAIL-CLOSED)
[+] Protocolo v13.2 Homologado: 14 Invariantes ativas (Merkle: c6d7e89f256c6baa...)
[*] Iniciando varredura profunda de arquivos publicaveis...
[*] Varredura concluida: 1520 arquivos elegiveis inspecionados (68,525,716 bytes)

================================================================================
VEREDITO SOBERANO: APROVADO PARA PUBLICACAO (100% SEGURO & ZERO LEAKS)
- Nenhuma chave ativa exposta em arquivos rastreaveis.
- .gitignore cobre credenciais, browser sessions, backups e mídias pessoais.
- Protocolo de Seguranca Soberana v13.2: 14/14 Invariantes Ativas.
- Merkle Root Imutavel SHA-256 Verificada.
================================================================================
```

---

## 5. Certification Sign-Off

- **Milestone Status**: CERTIFIED & SEALED.
- **Architectural Conformance**: 100% compliant with `JARVIS_AUTONOMOUS_INTELLIGENCE_PLAN.md`.
- **Dependencies**: Pure Python 3.12 Standard Library (Zero PIP dependencies).
- **Security Invariants**: 14/14 active; Merkle Root verified; 0 credential leaks.
- **Next Milestone**: **Milestone 5 (Phases 30–39): Memory Fabric, Failure Attribution, and Cognitive Governor**.
