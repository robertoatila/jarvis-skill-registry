# J.A.R.V.I.S. Documentation Map

This directory is the documentation entry point for the repository. It separates current contracts, active plans, release evidence, operational references, and historical material so that old design notes are not mistaken for validated runtime behavior.

## Canonical entry points

| Source | Purpose |
| --- | --- |
| [`../README.md`](../README.md) | Canonical human-readable current status, product position, public baseline and repository map |
| [`../evidence/current.json`](../evidence/current.json) | Machine-readable current v0.2 evidence and claim status |
| [`../AGENTS.md`](../AGENTS.md) | Cross-agent repository rules and invariants |
| [`../DESIGN.md`](../DESIGN.md) | Canonical HUD and design-system contract |
| [`../CONTRIBUTING.md`](../CONTRIBUTING.md) | Contribution workflow and validation expectations |
| [`../SECURITY.md`](../SECURITY.md) | Repository security and reporting guidance |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | General architecture reference |
| [`roadmap/JARVIS_AUTONOMOUS_INTELLIGENCE_PLAN.md`](roadmap/JARVIS_AUTONOMOUS_INTELLIGENCE_PLAN.md) | Long-horizon implementation direction |
| [`architecture/SERVER_INFERENCE_BOUNDARY.md`](architecture/SERVER_INFERENCE_BOUNDARY.md) | Server/provider trust boundary |
| [`architecture/REMOTE_TASK_CONTRACT.md`](architecture/REMOTE_TASK_CONTRACT.md) | Remote task protocol, exact plan approval, lifecycle, receipts and pending Windows acceptance |
| [`REMOTE_SECOND_BRAIN.md`](REMOTE_SECOND_BRAIN.md) | Operational runbook for bidirectional Obsidian memory, capability catalog and Remote Companion |
| [`CHATGPT_CAPABILITY_BRIDGE.md`](CHATGPT_CAPABILITY_BRIDGE.md) | Explicit ChatGPT capability-manifest contract and availability semantics |
| [`contributing/FIRST_EXTERNAL_SKILL.md`](contributing/FIRST_EXTERNAL_SKILL.md) | First external canonical-skill contribution walkthrough from fork to validated PR |
| [`ARCHITECTURE_5_LAYERS.md`](ARCHITECTURE_5_LAYERS.md) | Supported legacy distribution architecture |

Current behavior is established by executable contracts and fresh direct validation evidence. The README is the canonical human summary; `evidence/current.json` is the machine status. A design document, roadmap item, workflow badge or historical report is not proof that a feature is implemented.

## v0.2 engineering program

The active v0.2 specification and implementation plans live under [`superpowers/`](superpowers/). Plan 4 defines the current direct validation, benchmark and claim-audit architecture; final v0.2 status remains pending until its full direct gate set is executed. For deeper phase history, use:

- [`superpowers/plans/2026-09-15-v0.2.0-governor-context-memory-routing.md`](superpowers/plans/2026-09-15-v0.2.0-governor-context-memory-routing.md) — canonical phase plan.
- [`superpowers/plans/2026-09-15-v0.2.0-plan2-execution-status.md`](superpowers/plans/2026-09-15-v0.2.0-plan2-execution-status.md) — execution/evidence ledger for that plan.
- [`superpowers/README.md`](superpowers/README.md) — index for specs, plans and execution records.

## Documentation areas

| Path | Classification |
| --- | --- |
| [`architecture/`](architecture/) | Current architecture boundaries and focused technical references |
| [`roadmap/`](roadmap/) | Forward-looking implementation direction; status must be checked against tests/evidence |
| [`superpowers/specs/`](superpowers/specs/) | Approved design specifications |
| [`superpowers/plans/`](superpowers/plans/) | Implementation plans and execution-status records |
| [`launch/`](launch/) | Release, demo and launch material |
| [`assets/`](assets/) | Architecture and documentation media |
| [`plans/`](plans/) | Older or auxiliary implementation records; verify freshness before treating as active |
| [`history/`](history/) | Rules for classifying historical material without breaking existing public paths |

Other top-level documents in `docs/` remain available for compatibility and provenance. When two documents overlap, prefer the source named by `AGENTS.md`, this index, or the active plan, and verify behavior against tests before changing runtime code.

## Human cognitive vault

The numbered Markdown files at repository root and `.obsidian/` form the human-facing cognitive vault. They are intentionally kept at their existing public paths. The vault is a projection/reference surface; structured runtime state and executable contracts remain authoritative for machine behavior.

The v0.2 development branch now includes a restart-safe bidirectional Vault watcher/admission loop and the managed `20 - External Capability Matrix.md` projection. Human-authored Vault text is evidence, not execution authority, and JARVIS-authored managed projections are suppressed from self-ingestion through exact projection receipts. See [`REMOTE_SECOND_BRAIN.md`](REMOTE_SECOND_BRAIN.md) for the operational contract.

## Evidence rule

Use exact measurements and exact commit/run scope. In particular, serialized-byte benchmarks are byte measurements only unless a separate provider/token/cost experiment explicitly measures something else. Do not convert architecture intent, old reports, screenshots, or demo text into current capability claims.


## External reference analyses

- [ROWZY / JARVIS video reference — 2026-09-21](references/2026-09-21-ROWZY-JARVIS-VIDEO-REFERENCE.md) — complete technical inventory, timestamped observations, declared/inferred/proposed distinctions, source provenance and P0–P3 adaptation priorities. Supporting external reference only; not an active implementation plan or current runtime validation.
