# Milestone Zero — recovery, direction and visual foundation

Date: 2026-09-11 · Repository: J.A.R.V.I.S. Skill Registry  
Recovered baseline: `97ddce6a40865fe0fc05dd460d844587d72762f3` on `main`.

This report certifies the bounded Milestone Zero deliverables listed here, not the full autonomous runtime. The execution stops after recovery, selected tests, roadmap, identity and documentation.

## Interrupted work recovered

Initial `git status --short`, `git diff` and `git diff --stat` were empty. The suspected interrupted changes had already been committed in `97ddce6`; no pending model hunk required reconstruction. The commit's model and test changes were inspected and preserved. Its benchmark update was inspected separately and not promoted into a performance claim.

| Recovered item | Classification | Evidence and limit |
| --- | --- | --- |
| `tooling/agentic/models.py` | PARTIAL | Attempt/state/side-effect structures and serialization exist; five contract tests pass. Real runtime attempt integration, strict trust-boundary parsing and migration provenance remain incomplete |
| `tests/test_agentic_contracts.py` | COMPLETE for its five unit cases; PARTIAL as runtime coverage | All five pass. Attribution/compensation checks use test-local helpers, so production enforcement is not established |
| `benchmarks/runtime_latency_report.json` | UNRELATED to contract recovery | Committed generated timing update; untouched in M0 and not used as a runtime maturity or performance certificate |
| Pending uncommitted interrupted files | None | Initial checkout was clean. No BROKEN syntax/test item was found in the recovered selected scope |

Recovery preserved existing work. No runtime, model, test, private memory or benchmark implementation was changed in M0. New helper code only generates artwork or records this milestone's checks.

## Repository state

The [baseline manifest](milestone-zero/20260911/baseline.json) records HEAD, branch, source hashes, the captured diff and backup verification. Its capture occurs after adding the evidence helper; the initial clean inspection is recorded explicitly. Six existing documents were physically copied under local ignored `backups/milestone-zero-20260911/` and their SHA-256 hashes matched before any rewrite.

The final changes consist of README, root vault navigation, historical-document status notices, the new canonical plan, original visual assets, their generation sources and this evidence/report set. Runtime and selected test source hashes are checked against the recovered baseline. No commit, push, tag, release, deployment, hosting-setting change or provider request was performed by this Milestone Zero execution.

## Tests executed

Windows / Python 3.12.10. Selected suites ran using `python -B -m unittest discover -s tests -p <suite-file> -v`; the capture harness supplies a temporary `JARVIS_REGISTRY_ROOT` and tests use local fixtures. Exact commands, per-suite exit codes, output paths and hashes are in [tests.json](milestone-zero/20260911/tests.json).

| Suite | Tests | Result |
| --- | ---: | --- |
| Contracts | 5 | PASS |
| Foundation: policy, artifacts and state | 11 | PASS |
| Execution DAG | 18 | PASS |
| Agent profiles | 11 | PASS |
| Scheduler | 15 | PASS |
| Composite skills / disclosure | 9 | PASS |
| Supplied-source SWE inspection | 7 | PASS |
| Verification | 8 | PASS |
| **Total selected scope** | **84** | **0 failures, 0 errors** |

The two initial recovery commands also passed five contract and 18 DAG tests. The later captured eight-suite run is the canonical count; repeat runs are not counted as additional unique tests. One earlier combined inspection/test command failed PowerShell parsing before executing tests; it contributes no test result. A document-update helper subsequently encountered a Windows text-decoding error; it was completed using explicit UTF-8, and final document checks cover the resulting files.

Full-system, live HUD, Obsidian synchronization, external models/tools, infrastructure, federation, lint/type-checking and full schema-engine validation were not executed in M0. Selected green unit tests do not certify these surfaces or close the runtime integration findings.

## Roadmap created/updated

[JARVIS_AUTONOMOUS_INTELLIGENCE_PLAN.md](../docs/roadmap/JARVIS_AUTONOMOUS_INTELLIGENCE_PLAN.md) is the canonical forward plan. It has all **27 required sections**, six architectural layers and phases **00–54 (55 numbered entries)**. Each major section and each phase records Status, Priority, Requires, Unlocks, Risk and Evidence Required.

The old architecture reassessment's 33-phase sequence is retained as historical material and points to the new plan. Local E2E, fault and security gates precede external autonomy even though their phase numbers are later. Visual identity and README run early alongside foundation work. M0 does not automatically advance into implementation.

## Architecture improvements discovered

- Unknown risk and some side-effect data receive permissive defaults; trust-boundary deserialization needs explicit refusal and migration semantics.
- Legacy attempt restoration can generate placeholder mission/task identifiers. Preserve uncertainty rather than implying authentic lineage.
- Runtime dispatch does not persist the new attempt history; its non-command branch can emit successful completion without a demonstrated adapter action.
- Verification commands and execution commands need separate responsibilities and independent evidence.
- Runtime usage currently records fixed token values; budgets and optimization need measured usage or explicit UNKNOWN values.
- Actual dispatch should use current-state admission rather than only precomputed waves.
- Policy enforcement needs canonical path boundaries, complete effects and action-bound authenticated approvals; flags and action-name checks are insufficient foundations for expanded autonomy.
- Fitness and compensation rules need production integration tests, beyond the test-local rule helpers.
- Root configuration and import-side effects need further isolation.

These are prioritized P0/P1 findings, not silently implemented in a documentation milestone.

## Visual assets created

Every listed source has a same-basename PNG beside it, at the same dimensions. All are original programmatic compositions with editable source in `tooling/design/generate_assets.py`. PNG exports use the available local Sharp renderer. No remote images, external fonts or proprietary character artwork were used.

| Path | Format / dimensions | Purpose | Source/provenance |
| --- | --- | --- | --- |
| [.github/assets/jarvis-hero.svg](../.github/assets/jarvis-hero.svg) | SVG + PNG / 1400 × 560 | README hero | Original geometry, core graph, requested project text |
| [.github/assets/jarvis-social-preview.svg](../.github/assets/jarvis-social-preview.svg) | SVG + PNG / 1200 × 630 | Social preview ready for hosting configuration | Original simplified identity; development label |
| [.github/assets/jarvis-mark.svg](../.github/assets/jarvis-mark.svg) | SVG + PNG / 32 × 32 | Cyan mark for dark surfaces | Original open-J/hexagon geometry |
| [.github/assets/jarvis-mark-mono.svg](../.github/assets/jarvis-mark-mono.svg) | SVG + PNG / 32 × 32 | Monochrome mark for light surfaces | Same original geometry, single graphite color |
| [docs/assets/jarvis-runtime-architecture.svg](../docs/assets/jarvis-runtime-architecture.svg) | SVG + PNG / 1200 × 900 | Maturity-aware architecture | Current source evidence and planned contracts |
| [docs/assets/jarvis-cognitive-loop.svg](../docs/assets/jarvis-cognitive-loop.svg) | SVG + PNG / 1200 × 740 | Target nine-stage lifecycle | Explicitly labeled target, not live telemetry |
| [docs/assets/jarvis-memory-fabric.svg](../docs/assets/jarvis-memory-fabric.svg) | SVG + PNG / 1200 × 870 | Four-level memory architecture | Requested planned memory contract |
| [docs/assets/jarvis-cognitive-vault.svg](../docs/assets/jarvis-cognitive-vault.svg) | SVG + PNG / 1200 × 840 | Faithful existing-vault navigation diagram | Ten verified root MOC links; filenames recorded separately |

See [ASSET_PROVENANCE.md](../docs/assets/ASSET_PROVENANCE.md) for methods, palette, reproduction and usage. The [artifact validation](milestone-zero/20260911/artifact-validation.json) records hashes, dimensions, source preservation, backup verification, roadmap structure and local document-link checks. Render review includes the hero at reduced width and both 32-pixel marks; an overflowing memory-card label and vault connectors were corrected before final validation. No image is represented as a real HUD or Obsidian screenshot.

## README changes

The English README now opens with the local hero, explains the project and its direction, shows current versus planned capabilities, provides two inspected local test commands, and links directly to recovery evidence and the canonical plan. It includes architecture, cognitive loop, memory and existing-vault diagrams with descriptive alt text. Unsupported whole-runtime certification, conflicting test counts, generic token-saving percentages and unverified accessibility claims were removed from the README. Licensing distinguishes project code from third-party catalog entries.

## Obsidian changes

The root MOC now links to current implementation status, recovery evidence, the navigation map and planned memory architecture. Its frontmatter no longer presents historical counts/hashes as current authority, and the old telemetry section is labeled a static historical snapshot. Existing topic notes and the canvas remain intact. The diagram uses ten existing MOC links; it does not read or expose personal-memory note contents.

The target architecture is a validated, aggregated projection from structured runtime memory. A complete Memory Fabric, conflict-aware admission and live synchronization are not claimed as implemented.

## HUD changes

No live HUD code or behavior was changed. The visual foundation is available for a later UI milestone. No live HUD capture was taken; the README states that limitation and uses explicitly labeled architecture diagrams.

## Token/context optimization plan

Context Governor: information need → cheapest useful evidence → confidence → expansion only when needed. It applies budgets at mission/task/agent/retrieval/tool-result/memory levels, progresses from catalog to manifest to targeted/broader source, and records ContextReceipts. No-repeat reads use path/hash/sufficient summary with exact-read exceptions. Compaction preserves authority, unresolved uncertainty, verified facts and references; raw transcripts remain in a separate audit store.

## Memory architecture plan

Four levels: working, episodic, semantic and procedural. Admission checks value, evidence, provenance, confidence, duplicates and contradictions before classification/storage. Retrieval progresses from exact IDs and repository graphs through metadata, lexical and semantic search. Freshness, scope, environment, conflict and supersession metadata travel with each record. Decay lowers retrieval priority without silently deleting audit history. Obsidian receives aggregated validated projections.

## Tool/model routing plan

ToolRouter filters compatibility and authority before cost/utility ranking. ModelRouter enforces policy, minimum capability, privacy, availability and budget before comparing expected quality and resource costs. Both produce decision receipts with candidates, rejections, reasons and explicit UNKNOWN estimates. Escalation considers context and tool improvements as well as a stronger model; repeated cheap failures consume the same bounded budget. Weights and thresholds require measured experiments, not invented constants.

## Autonomy safety boundaries

A0 observe, A1 recommend, A2 read-only, A3 reversible local, A4 bounded external and A5 high-risk human approval are target autonomy envelopes, distinct from R0–R5 risk classes. Cognitive Governor makes bounded decisions and never directly executes tasks. Self-improvement cannot expand privileges, disable policy, erase evidence/audit, remove budgets or required approvals, hide telemetry or promote unverified changes. Existing destructive-action denial is not weakened.

## Remaining blockers

No blocker remains for the bounded M0 documentation/identity/recovery deliverables once the linked artifact checks pass. The P0 findings above block a claim of fully verified autonomous execution and gate expanded autonomy. Production resource efficiency is UNKNOWN; existing fixture benchmarks are not re-certified. Live UI, synchronization, providers and external effects remain outside this validation scope.

## Next recommended milestone

**M1 — harden the execution and trust foundation.** Complete phases 03–11 and the minimal adapter boundary needed to validate them: strict schema/migrations, fail-closed risk/effect parsing, action-bound approvals, real persisted attempts, execution/verifier separation, measured usage, enforced idempotency/reconciliation/compensation and isolated restart/fault integration tests. Preserve current identifiers and evidence. This recommendation is documented; implementation does not begin in M0.

Final artifact validation passed: 27 roadmap sections, 55 phase entries, an acyclic dependency diagram, 47 local document links, eight SVG sources with eight matching PNG exports, six reverified backups and 65 unchanged runtime/test source files. All checked primary text/panel combinations exceeded a 4.5:1 contrast ratio. This is not an accessibility certification of the HUD.

Milestone completion is backed by the selected test outputs and the final artifact-validation manifest. **STOP after Milestone Zero.**

**MILESTONE ZERO COMPLETE**
