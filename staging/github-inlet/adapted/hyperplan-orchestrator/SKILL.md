---
name: hyperplan-orchestrator
description: "Structure complex, multi-phase technical projects into deterministic, file-backed implementation plans with explicit verification criteria and rollback safeguards. Triggers: hyperplan, plan project, multi-phase plan, plan architecture, implementation plan, orchestrate plan."
---

# Hyperplan Orchestrator

Design, decompose, and orchestrate complex technical changes across multiple subsystems.
Generates persistent, file-backed engineering blueprints designed to survive agent context loss
and ensure verifiable incremental delivery.

## Core Architectural Invariants

1. **Persistent File State**: Plans must be written to disk (`task_plan.md` or `docs/plans/<plan-name>.md`), never left solely in transient agent conversation context.
2. **Phase Decoupling**: Each phase must be independently testable with binary pass/fail verification criteria.
3. **Rollback Pre-Planning**: Every mutating step must define an explicit rollback action.
4. **Zero Unreviewed Execution**: Planning is decoupled from implementation. Execution occurs only after explicit human approval.

## Planning Workflow & Schema

- **Executive Summary**: Core objective, business/technical drivers, scope boundaries.
- **Architecture Overview**: System diagrams, component relationships, data flow.
- **Phase Breakdown**:
  - Phase 1: Foundation & Schemas (Non-breaking).
  - Phase 2: Core Logic & Internal Services.
  - Phase 3: Public API / Interfaces / Adapters.
  - Phase 4: Verification, Security Scanning, and Acceptance.
- **Risk & Mitigation Matrix**: Pre-mortem failure scenarios and guardrails.