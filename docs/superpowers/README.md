# Superpowers Design and Implementation Index

This subtree contains the structured v0.2 design/implementation workflow. It is separated from general documentation so approved architecture, executable plans and execution evidence do not blur together.

## Structure

- [`specs/`](specs/) — approved architectural/design specifications. A spec defines the intended contract; it is not proof that the implementation exists.
- [`plans/`](plans/) — sequenced implementation plans and execution-status records. Plans may contain future work; check status/evidence before treating a task as complete.

## Active v0.2 plans

- [`plans/2026-09-15-jarvis-v0.2.0-master-plan.md`](plans/2026-09-15-jarvis-v0.2.0-master-plan.md) — umbrella implementation sequence.
- [`plans/2026-09-15-v0.2.0-trusted-runtime-receipts.md`](plans/2026-09-15-v0.2.0-trusted-runtime-receipts.md) — trusted runtime/receipt hardening.
- [`plans/2026-09-15-v0.2.0-governor-context-memory-routing.md`](plans/2026-09-15-v0.2.0-governor-context-memory-routing.md) — adaptive Governor, context, memory and routing phase.
- [`plans/2026-09-15-v0.2.0-plan2-execution-status.md`](plans/2026-09-15-v0.2.0-plan2-execution-status.md) — current evidence/status ledger for the Governor/Context/Memory/Routing plan.
- [`plans/2026-09-15-v0.2.0-operational-hud-observability.md`](plans/2026-09-15-v0.2.0-operational-hud-observability.md) — operational HUD/observability phase.
- [`plans/2026-09-15-v0.2.0-ci-benchmarks-docs.md`](plans/2026-09-15-v0.2.0-ci-benchmarks-docs.md) — direct validation, benchmark and documentation phase.
- [`plans/2026-09-18-v0.2.0-plan4-execution-status.md`](plans/2026-09-18-v0.2.0-plan4-execution-status.md) — exact Plan 4 implementation/Task 8 evidence ledger; currently blocked pending direct execution.
- [`plans/2026-09-15-v0.2.0-release-productization.md`](plans/2026-09-15-v0.2.0-release-productization.md) — release/productization phase.

## Status semantics

Use evidence rather than prose completion claims:

- **PLANNED** — described but not yet implemented.
- **RED** — executable contract exists and is intentionally failing against the previous implementation.
- **GREEN** — implementation satisfies focused tests.
- **VALIDATED** — the relevant full matrix has passed on the exact stated commit.
- **RELEASED** — included in an immutable published release.

A later integrated validation can prove cumulative compatibility of earlier tasks, but it does not rewrite the historical commit at which each task was developed.

For repository-wide documentation navigation, return to [`../README.md`](../README.md).
