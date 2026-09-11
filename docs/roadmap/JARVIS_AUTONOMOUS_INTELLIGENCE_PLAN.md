# J.A.R.V.I.S. Autonomous Intelligence Plan

Canonical forward roadmap · Milestones M0–M6 Fully Certified · 2026-09-11  
Recovered source baseline: `97ddce6a40865fe0fc05dd460d844587d72762f3`.  
Release Candidate Target: `v2.0.0-rc2` (231/231 tests passing across 38 suites).

This plan outlines the sovereign architecture and milestones from baseline reassessment (M0) through complete system hardening and release candidate certification (M6). All 55 phases (00 through 54) have been implemented, verified, and audited with reports captured in `reports/MILESTONE_ZERO.md` through `reports/MILESTONE_SIX.md` and `reports/JARVIS_RELEASE_CANDIDATE.md`.

Status vocabulary: **EXISTING** = source or artifact located; **PARTIAL** = some behavior exists, integration or evidence missing; **PLANNED** = target contract not implemented; **BLOCKED** = prerequisites prevent admission; **VALIDATED** = stated, bounded behavior passed a recorded check. Never infer whole-system readiness from a component status. Priorities: P0 foundation/correctness; P1 next local capability; P2 later optimization/observability; P3 gated external expansion. `UNKNOWN` is an honest measurement value, not zero or success.

## 1. Vision

**Status:** PLANNED · **Priority:** P1 · **Requires:** trusted execution and evidence · **Unlocks:** useful bounded autonomy · **Risk:** attractive demonstrations conceal unverified work · **Evidence Required:** independently verified useful outcomes with actual resource receipts.

J.A.R.V.I.S. should decide whether and how to act, what information it needs, which resources are worth spending, how to verify the result, and what deserves to be learned. The skill registry is an existing foundation for this direction. The target is an Autonomous Cognitive Runtime that improves verified usefulness within explicit authority, privacy and resource limits.

The north star is **Verified Utility per Resource Unit**. Track cost, tokens, latency, compute and risk separately; any aggregate requires declared units, normalization and versioned weights. Do not divide outcomes by an arbitrary sum of heterogeneous measurements.

## 2. Current Reality

**Status:** VALIDATED (inspection and selected unit scope only) · **Priority:** P0 · **Requires:** recovered checkout · **Unlocks:** evidence-based sequencing · **Risk:** stale certificates and placeholder telemetry · **Evidence Required:** source hashes, commands, exit codes and named test coverage.

The initial recovery inspection found a clean `main` checkout. The suspected interrupted additions to `models.py` and `test_agentic_contracts.py` were already committed. No uncommitted model hunk needed repair. Eight selected suites passed **84 tests** on Python 3.12.10; outputs are captured in [tests.json](../../reports/milestone-zero/20260911/tests.json). This is not a full system, provider, browser, deployment or security certification.

| Area | Current evidence | Status and practical limit |
| --- | --- | --- |
| Registry and governance | `tooling/skillctl.ps1`, index/catalog structures, existing governance documents | EXISTING; full catalog contents and quarantine payloads were not reopened or executed |
| Mission, Task, Attempt | `tooling/agentic/models.py`, five contract tests | PARTIAL; serialization/history tested; execution integration missing |
| Execution DAG | `dag.py`, 18 DAG tests | VALIDATED for tested ordering, cycles, persistence and prerequisite gates |
| Configuration, policy, state | `config.py`, `policy.py`, `state_store.py`, 11 foundation tests | PARTIAL; happy paths and selected denials tested; policy boundary gaps remain |
| Profiles, scheduler, composite | 11 + 15 + 9 selected tests | VALIDATED for these unit contracts; not all runtime callers use the safe paths |
| Source inspection and verification | Seven SWE and eight verification tests | PARTIAL; supplied-source inspection is real; complete functional/tool verification is not established |
| Runtime, telemetry, recovery, learning | `runtime.py`, `telemetry.py`, `resilience.py`, `learning.py` | PARTIAL; presence is not end-to-end evidence |
| Vault and HUD | `vault.py`, `ui/`, `tooling/jarvis_server.py`, root MOC | EXISTING; no live browser/provider or vault synchronization validation in this milestone |
| Context/Cognitive Governor, Memory Fabric | No complete contracts located in the inspected runtime | PLANNED; reuse existing disclosure, budgets, learning and vault components where suitable |
| External adapters and federation | Infrastructure and federation modules exist | BLOCKED for expanded autonomy pending local trust gates |

Concrete findings to carry into the next milestone:

1. `RiskLevel.normalize` maps unrecognized values to R0; side-effect parsing also has permissive defaults. Unknown authority/effect data must fail closed rather than gain a harmless classification.
2. `ExecutionAttempt.from_dict` can synthesize legacy mission/task identifiers. Legacy records need an explicit migration provenance marker; invented identifiers must not masquerade as authentic lineage.
3. `runtime.py` does not call `record_attempt`. Its non-command branch creates completion text and an executed result without a demonstrated adapter invocation. Verification commands are also used as execution commands. Separate those responsibilities.
4. Runtime token usage is currently fixed at 150 prompt / 50 completion tokens. Replace it with provider or local accounting evidence; use UNKNOWN when unavailable.
5. The runtime uses precomputed `schedule` waves although the scheduler exposes current-state admission checks. Wire current verified prerequisites and capacity checks into actual dispatch.
6. Policy checks depend on action labels and a selected resource; write scope matching uses string prefixes. Require canonical paths, complete effect declarations and adapter enforcement. An approved task flag alone must not substitute for an authenticated, scoped, unexpired grant.
7. The contract tests for skill-penalty attribution and compensation provenance implement local helper functions. Passing them does not demonstrate enforcement in fitness or compensation services.
8. Configuration still defaults to an absolute Windows checkout, and some modules retain their own roots. Finish root injection and ensure imports do not mutate authoritative state.

## 3. Architectural Principles

**Status:** PLANNED (target constraints) · **Priority:** P0 · **Requires:** current-reality findings · **Unlocks:** coherent contracts across layers · **Risk:** parallel implementations of the same authority · **Evidence Required:** contract tests plus integration tests at each boundary.

Preserve existing execution, trust, evidence, failure and authorization contracts. Extend versioned schemas with explicit migrations and compatibility fixtures. Keep execution state, verification state, recovery state and mission outcome independent. Execution completion is not verification; a timeout with unknown external effect is not proof of failure or safety to retry.

The plan uses six layers. A–C follow the requested grouping; D–F make memory, human projection and external operations explicit:

| Layer | Responsibility | Boundary |
| --- | --- | --- |
| A — Trusted Foundation | Contracts, schemas, state, policy, artifacts, failure, evidence, budgets | Mandatory before autonomous execution expansion |
| B — Cognitive Execution | Profiles, skills, adapters, admission, scheduler, planning, resolution, recovery | Executes only admitted, evidenced attempts |
| C — Cognitive Efficiency | Context Governor, tool/model routing, decision receipts, Cognitive Governor | Optimizes within authority; cannot bypass A |
| D — Memory and Learning | Memory Fabric, attribution, experiments, bounded promotion | Durable knowledge requires provenance and validation |
| E — Human Observability | Visual identity, README, HUD, Obsidian projection | Exposes truth; never becomes execution authority |
| F — Governed External Operations | External knowledge, n8n, infrastructure, federation | Admission and local hardening precede external effects |

Audit logs, authoritative machine state, derived projections and disposable caches have separate storage roles. Source references and immutable hashes support replay; replay must never repeat an unsafe external effect merely to reproduce a screen.

## 4. Trusted Foundation

**Status:** PARTIAL · **Priority:** P0 · **Requires:** recovery baseline · **Unlocks:** layers B–F · **Risk:** false success or unbounded side effects · **Evidence Required:** schema/migration negatives, policy bypass negatives, restart and idempotency tests.

Mission holds the goal, authorized scope, budgets, DAG and terminal outcome. Task describes an admitted unit of work and independent verification requirements. ExecutionAttempt is append-only history with mission/task/agent/skill/tool/node identifiers, trace and parent trace, timestamps, input/output references, environment fingerprint, idempotency key, consumed resources, artifacts, side effects, failure class/attribution and the four state axes.

Persist authoritative transitions atomically and verify restart behavior before releasing dependents. Admission requires valid schemas, policy, scoped authorization, resource estimates or an explicit unknown-cost policy, and a verification strategy. Missing provenance blocks automatic compensation. Retry requires declared idempotency semantics; ambiguous effects enter reconciliation. Compensation itself is a new policy-controlled, evidenced attempt.

Failure classification and attribution are separate. Distinguish transient, permanent, validation, policy, authorization, conflict, timeout, exhausted resources, dependencies, external services, malformed input, integrity, compatibility, cancellation and unknown. Attribute to planner, resolver, agent, skill, tool, node, environment, dependency, service or policy only with evidence. Node/policy failures must not automatically penalize a skill.

The next milestone must reject unknown enum values at trust boundaries, preserve legacy uncertainty explicitly, bind approvals to immutable action/scope/budget digests, validate every effect, and test expiry, revocation, restart, tampering and path aliases. Do not use unknown-risk defaults as execution authorization.

## 5. Cognitive Runtime

**Status:** PARTIAL · **Priority:** P1 · **Requires:** foundation admission gates · **Unlocks:** bounded mission execution · **Risk:** selecting a capable profile without an executable adapter · **Evidence Required:** real local fixture action → persisted attempt → independent verification → final outcome.

Build on existing profiles, composite skills, skill dependency graph, progressive disclosure, scheduler, planner/resolver, repository intelligence and recovery modules. Formalize a separate adapter contract: accepted inputs, capabilities, effects, scopes, environment, timeout, cancellation, idempotency, outputs, measured usage and verification hooks. Profile selection is not adapter execution.

Every dispatch must check current DAG state, locks, node/agent capacities, policy, budget and cancellation. Planner assumptions reference repository commit, file hashes and tool/skill compatibility. Replan only the affected DAG region when a file, dependency, tool, skill, node, budget, verification result or new evidence invalidates those assumptions. Preserve unaffected verified work and explain invalidation in the audit trail.

## 6. Cognitive Governor

**Status:** PLANNED · **Priority:** P1 · **Requires:** budgets, receipts, context policy, verified outcomes · **Unlocks:** controlled escalation and adaptive planning · **Risk:** optimizing away authority or evidence · **Evidence Required:** bounded decision traces and stop/escalation tests.

The Governor controls budget allocation, context strategy, memory policy, model/tool escalation, replanning and stop conditions. **It never executes tasks directly.** It requests admitted work through the runtime. For uncertainty: identify the missing fact → choose the cheapest useful information source → evaluate confidence → continue, expand, replan or stop.

Confidence must reference a method and evidence; no invented precision. Repeated cheap failures consume the same mission budget and must trigger escalation or stopping before their cumulative cost exceeds the configured alternative. Human intervention, cancellation, exhausted budget and violated authority always take precedence over goal pursuit.

## 7. Context Economy

**Status:** PARTIAL (disclosure exists; Governor/receipts planned) · **Priority:** P1 · **Requires:** source identity, budgets, retrieval evidence · **Unlocks:** economical planning and routing · **Risk:** aggressive compression removes a critical constraint · **Evidence Required:** same-outcome comparisons, freshness invalidation and exact-read exceptions.

Decision sequence: **goal → information need → cheapest useful evidence → confidence → expand only if needed**. Budgets exist at mission, task, agent, retrieval, tool-result and memory levels. Reserve capacity for verification and recovery rather than exhausting it during planning.

Progressive disclosure is **CATALOG → MANIFEST → TARGETED SOURCE → BROADER SOURCE**. Reuse current disclosure components; do not load entire repositories or skill bodies merely because they are available.

Planned `ContextReceipt`: mission/task IDs; sources considered and loaded; selection reason; content hash; bytes; estimated tokens and estimation method; cache hit; relevance; confidence; freshness; provenance; schema version. Measured and estimated values must be distinguishable. Unknown values remain UNKNOWN.

No-repeat reads use normalized path + content hash + scoped summary. Reuse an unchanged, sufficient summary, except when exact text is required for modification, quotation, security decisions, ambiguous semantics or stale assumptions. Hash drift invalidates the cache entry.

Compaction: raw execution → structured state → mission summary → verified facts → source references. Keep raw transcripts in the separate audit store. Preserve decisions, unresolved uncertainty, authority, side effects and pending verification through every compaction stage. Evaluate quality against verified outcomes, not only token reduction.

## 8. Tool Intelligence

**Status:** PLANNED · **Priority:** P1 · **Requires:** adapter contracts, policy, capability catalog, usage history · **Unlocks:** auditable tool choice · **Risk:** low apparent cost hides broad effects · **Evidence Required:** compatibility refusals and comparative, verified task outcomes.

`ToolRouter` input: task, required capabilities, environment, risk ceiling, budget, available tools and relevant history. Output: candidates, compatibility results, expected utility, cost, risk, selected tool and selection reason. Apply hard authority, privacy, scope and capability constraints before ranking. Missing tools produce an explicit blocked decision; do not invent capabilities.

## 9. Model Intelligence

**Status:** PLANNED · **Priority:** P1 · **Requires:** provider metadata, privacy rules, budgets, evaluation corpus · **Unlocks:** cost-aware escalation · **Risk:** cheapest model repeatedly fails or leaks data · **Evidence Required:** measured quality/cost/latency under fixed comparable tasks.

`ModelRouter` ranks expected quality minus declared token, monetary, latency, risk and context penalties. Hard constraints include policy, minimum capability, privacy, budget, availability and context capacity. Weights are configurable, observable, versioned and experimentable; this plan invents no universal constants or live model prices.

Start with the least costly strategy that has adequate evidence of suitability. If confidence is insufficient, first consider better context or tools, then a stronger model. Stop repeated low-cost failures according to the total mission budget. Provider failures and node failures are distinct from model quality failures.

Planned `DecisionReceipt` shared by agent/skill/tool/model/node/memory/context decisions: decision ID, mission/task IDs, decision type, candidates, rejected candidates and reasons, estimated cost/quality/risk with methods, selection, reason and confidence. UNKNOWN estimates remain explicit. Persist receipts before consequential dispatch and attach actual outcome/usage afterward without rewriting the original estimate.

## 10. Memory Fabric

**Status:** PLANNED (existing memory/vault support is narrower) · **Priority:** P1 · **Requires:** evidence, scoped identities and durable state · **Unlocks:** reliable reuse across missions · **Risk:** stale or untrusted knowledge becomes authority · **Evidence Required:** admission, conflict, scope, expiry and retrieval regression fixtures.

| Level | Contents | Lifetime and admission |
| --- | --- | --- |
| Working | Active mission context and structured intermediate state | Transient; compact within current authority |
| Episodic | Missions, attempts, decisions, outcomes, failures, recoveries | Durable evidence references with source scope |
| Semantic | Repository, architecture and environment facts/relationships | Verification, commit/environment identity and freshness |
| Procedural | Supported workflows, heuristics, tool/skill and recovery strategies | Verified experiments plus bounded promotion |

Admission: worth remembering? → evidence → provenance → confidence → duplicate detection → contradiction detection → classification → storage. Every durable record carries confidence, provenance, created/last-verified dates, freshness, environment, scope, contradictions, supersedes and superseded-by relationships.

Retrieval order: exact ID → repository graph → structured metadata → lexical → semantic → broader search. Add an external vector database only after a measured benefit exceeds operational cost. Resolve conflicts using commit, environment, freshness, provenance and verification strength; preserve competing claims when unresolved instead of silently blending them.

Decay lowers retrieval priority for stale, weak, superseded, unused or environment-specific knowledge. It does not immediately delete the audit record. Compaction keeps references to the original evidence and respects privacy and retention policy.

## 11. Repository Intelligence

**Status:** PARTIAL · **Priority:** P1 · **Requires:** trusted catalog and source hash cache · **Unlocks:** targeted planning/context and local replanning · **Risk:** stale graphs misidentify impact · **Evidence Required:** incremental invalidation and deterministic dependency/AST fixtures.

Reuse `repo_intel.py`; index paths, symbols, relationships, tests, ownership and relevant configuration within authorized scopes. Cache by repository identity, commit and content hash. Incremental changes invalidate the affected graph region. Exclude private state, credentials and quarantined payloads. Graph inference is a hypothesis until supported by source or tests.

## 12. Verification and Evidence

**Status:** PARTIAL · **Priority:** P0 · **Requires:** real execution artifacts and explicit requirements · **Unlocks:** mission success, fitness and learning · **Risk:** self-reported success substitutes for independent checks · **Evidence Required:** positive and adversarial fixtures with producer, command, exit code, timestamps and hashes.

Keep execution completion distinct from VERIFIED. Requirements may include syntax, schema, tests, behavior, invariants, output integrity and independent inspection. Missing checker or dependency produces UNVERIFIED/NOT_EXECUTED, never a pass. Separate the action adapter from its verifier. A hash proves content identity, not correctness or trusted authorship.

Each artifact references mission/task/attempt, producer, path or content ID, hash, timestamps, environment and verification state. Evidence is append-only; corrected conclusions supersede earlier records explicitly. Reconciliation checks observed effects before retries. Mission success depends on verified required outcomes and unresolved effects, not on all commands exiting zero.

## 13. Learning and Adaptation

**Status:** PARTIAL · **Priority:** P2 · **Requires:** actual outcomes, attribution, resource receipts and Memory Fabric · **Unlocks:** better bounded decisions · **Risk:** learning from synthetic success or confounded measurements · **Evidence Required:** baseline, hypothesis, experiment, evaluation and reversible promotion record.

Observation → hypothesis → experiment → evidence → evaluation → bounded promotion. Improve routing, ranking, context selection, retrieval, planning and retry strategies. Preserve a control strategy and rollback reference. Attribution prevents infrastructure/policy failures from corrupting skill fitness. No unverified heuristic promotion; confidence and environmental applicability travel with the promoted record.

## 14. Obsidian Cognitive Vault

**Status:** PARTIAL · **Priority:** P2 · **Requires:** structured memory and validated aggregation · **Unlocks:** human understanding and navigation · **Risk:** a note edit silently becomes runtime authority · **Evidence Required:** deterministic projection, stable links and explicit discrepancy reporting.

The repository already has a root MOC, topic notes and a canvas. Milestone Zero adds a truthful navigation entry point and a diagram derived from existing links. It does not import personal memory into public artwork or claim live synchronization.

Authoritative flow: **Runtime Memory → aggregation → validation → projection → Obsidian**. Human edits become proposed knowledge requiring admission. Introduce Home, Architecture, Missions, Agents, Skills, Tools, Decisions, Experiments, Learnings, Heuristics, Failures, Recovery, RepoIntelligence, Memory and MOCs gradually. Aggregate by mission/topic/time window; do not create a note for every event. Raw telemetry stays outside the vault's primary navigation.

## 15. HUD and Human Observability

**Status:** EXISTING (live behavior not validated here) · **Priority:** P2 · **Requires:** truthful telemetry and state projections · **Unlocks:** human supervision · **Risk:** attractive UI implies unsupported autonomy · **Evidence Required:** real captures tied to source/version, interaction and accessibility checks.

The HUD should expose authority, actual attempt state, independent verification, resource usage, uncertainty, receipts and pending approvals. Distinguish estimates, measurements, historical snapshots and UNKNOWN values. Capture real UI only after verifying it functions with representative local data. Milestone Zero changes documentation/identity only; diagrams are labeled as diagrams and no product screenshot is fabricated.

## 16. External Knowledge

**Status:** PARTIAL (catalog tooling exists; strengthened admission planned) · **Priority:** P2 · **Requires:** trust policy, provenance, context budgets · **Unlocks:** scoped external evidence · **Risk:** source instructions become execution authority · **Evidence Required:** rejection, stale-source and demand-materialization tests.

Admission sequence: **DISCOVER → SCORE → VALIDATE → INDEX → USE**. Collect source identity, license, provenance, trust, freshness, relevance, language/ecosystem, security and quality before influence. A lightweight catalog stores repository, description, topics, language, license, index date, trust, capabilities and relevance domains. Materialize only when justified by the current task; never clone all discovered repositories. External content is data, not higher-priority instruction.

## 17. Infrastructure

**Status:** BLOCKED for autonomy expansion · **Priority:** P3 · **Requires:** hardened local execution, grants, idempotency, compensation and secrets isolation · **Unlocks:** bounded infrastructure operations · **Risk:** irreversible effects and privilege escalation · **Evidence Required:** dry runs, isolated real adapters, rollback/reconciliation and human approval tests.

Existing infrastructure helpers are not blanket authority to install, deploy or alter services. Declare every effect and bind grants to exact scope, budget, expiration and operator identity. Keep secrets out of receipts and projected notes. No infrastructure operation is needed to finish Milestone Zero.

## 18. Federation

**Status:** BLOCKED for autonomy expansion · **Priority:** P3 · **Requires:** hardened local attempts, identity, trust and reconciliation · **Unlocks:** bounded multi-node dispatch · **Risk:** split-brain execution and repeated side effects · **Evidence Required:** node loss, lease expiry, duplicate delivery, network partition and untrusted result fixtures.

Reuse existing federation code only after adapter/node contracts are versioned and authenticated. Remote capacity is not authority. Preserve trace lineage, lease ownership, environment identity and verification evidence across nodes; treat an unavailable node's outcome as unknown until reconciled.

## 19. Security and Trust

**Status:** PARTIAL · **Priority:** P0 · **Requires:** explicit identities, scopes and effect contracts · **Unlocks:** admission at every autonomy level · **Risk:** action-label bypass, stale grants or untrusted evidence · **Evidence Required:** threat-driven negative integration tests.

Target autonomy levels are separate from existing R0–R5 **risk classes**:

| Autonomy | Permitted envelope after implementation and validation |
| --- | --- |
| A0 Observe | Gather authorized state; no task effects |
| A1 Recommend | Produce proposals with evidence and costs |
| A2 Read-only | Execute admitted read operations within scope |
| A3 Reversible local | Bounded local writes with provenance and recovery |
| A4 Bounded external | Explicit external authority, budgets, idempotency and reconciliation |
| A5 High-risk approval | Action-specific human approval and additional controls; not self-granted autonomy |

Do not equate A4 with R4 or weaken the current destructive-action denial. The mapping must be a policy decision over actual effects. Self-improvement may not disable policy, increase privileges, remove required approvals, hide telemetry, rewrite evidence, erase audit history, remove budgets or promote unverified changes.

## 20. Repository Visual Identity

**Status:** VALIDATED (Milestone Zero assets; see validation report) · **Priority:** P2 · **Requires:** factual product framing · **Unlocks:** readable documentation and consistent future UI · **Risk:** concept art presented as product evidence · **Evidence Required:** editable sources, provenance, renders, dimensions and local links.

The visual foundation uses near-black graphite, subtle navy, restrained cyan/blue, white text, fine grids and an original geometric mark. Solid, dash-dot and dashed boundaries communicate validated unit scope, partial implementation and planned components. Status words accompany color.

Hero, social preview, mark, architecture, cognitive loop, Memory Fabric and the existing-vault navigation map are tracked in [asset provenance](../assets/ASSET_PROVENANCE.md). SVG sources are editable and PNG exports are local. No protected character imagery, remote fonts, fake terminal output or fake HUD screenshot. This track runs early alongside foundation work and never gates execution correctness.

## 21. Milestones

**Status:** PLANNED beyond M0 · **Priority:** P0–P3 · **Requires:** the gates below · **Unlocks:** staged, reviewable delivery · **Risk:** phase numbers imply approval · **Evidence Required:** per-phase artifacts and unmet requirements recorded explicitly.

M0 = recovery, inspection, selected validation, canonical plan, visual identity and accurate documentation; STOP. M1 = foundation contract and policy hardening; M2 = bounded local cognitive execution; M3 = context/routing/Memory Fabric; M4 = evidence-based learning and human observability; M5 = explicitly admitted external operations; M6 = whole-system hardening and possible release candidate. Phases **00–54 contain 55 numbered entries**; numbering is a planning reference, not a count of completed features.

| Phase / item | Status | Priority | Requires | Unlocks | Risk | Evidence Required |
| --- | --- | --- | --- | --- | --- | --- |
| 00 Recover interrupted work | VALIDATED | P0 | checkout inspection | 01 | overwrite unrelated work | clean initial diff; commit inspection |
| 01 Recovered baseline | VALIDATED | P0 | 00 | 02–03 | stale evidence | hashes, backup, selected test logs |
| 02 Architecture reassessment | VALIDATED | P0 | 01 | 03,40 | source presence mistaken for behavior | scoped findings and canonical plan |
| 03 Execution contract | VALIDATED | P0 | 02 | 04–06 | false execution | adapter/attempt boundary and negative tests |
| 04 Schema and migration | VALIDATED | P0 | 03 | 06–08 | silent legacy coercion | version fixtures and rejection tests |
| 05 Policy/auth/risk | VALIDATED | P0 | 03–04 | 06,16,18 | bypassed authority | scoped expiring grants; unknown-risk denial |
| 06 Mission/task/attempt | VALIDATED | P0 | 03–05 | 07–11 | lost attempt history | runtime-persisted independent state axes |
| 07 Persistent state | VALIDATED | P0 | 04,06 | 08–10,21 | corrupt restart | atomicity, migration and recovery fixtures |
| 08 Artifact/provenance | VALIDATED | P0 | 06–07 | 09–10 | unrelated file marked produced | attempt-bound content/effect receipts |
| 09 Failure/retry/reconcile/compensate | VALIDATED | P0 | 05–08 | 10,21 | duplicate effects | unknown-effect reconciliation; no-provenance denial |
| 10 Verification/evidence | VALIDATED | P0 | 06–09 | 11,18,32 | unsupported PASS | independent outcome checks and missing-checker refusal |
| 11 Budgets | VALIDATED | P0 | 06–10 | 17–20 | synthetic usage | actual usage plus explicit unknown-cost handling |
| 12 Profiles | VALIDATED | P1 | 05–06 | 14,18,24 | capability mismatch | unit coverage + admitted dispatch integration |
| 13 Skill graph | VALIDATED | P1 | 04,08 | 14,25 | dependency drift | pinned graph and cycle/invalidation fixtures |
| 14 Composite skills | VALIDATED | P1 | 12–13 | 16,29 | scope expansion | effect/scoped expansion verification |
| 15 Disclosure | VALIDATED | P1 | 08,13 | 17,25 | oversized context | catalog/manifest/targeted-source receipts |
| 16 Adapter contract | VALIDATED | P0 | 03,05,08–10,14 | 18,26 | verifier used as executor | real isolated action and effect output |
| 17 Context Governor | VALIDATED | P1 | 11,15 | 23–28 | lost constraints | budget, cache drift and exact-read tests |
| 18 Admission | VALIDATED | P0 | 05,10–12,16 | 19 | unauthorized dispatch | all hard constraints checked before effects |
| 19 Scheduler | VALIDATED | P1 | 18 | 20–21,29 | stale precomputed waves | current-state dispatch and capacity integration |
| 20 Telemetry | VALIDATED | P1 | 08,11,19 | 28,32–34 | fixed token counts | actual usage, privacy and trace lineage |
| 21 Recovery/replay | VALIDATED | P1 | 07,09,19–20 | 29,35 | duplicate irreversible effects | crash/restart/idempotency fixtures |
| 22 Repository intelligence | VALIDATED | P1 | 08,15 | 23 | stale dependency assumptions | incremental graph and source-hash invalidation |
| 23 Planner | VALIDATED | P1 | 17–19,22 | 24–29 | invalid whole-plan restart | affected-region replanning with evidence |
| 24 Agent resolver | VALIDATED | P1 | 12,18,23 | 28–29 | profile mistaken for execution | admissible candidates and decision receipts |
| 25 Skill resolver | VALIDATED | P1 | 13–15,23 | 28–29 | incompatibility | dependency/trust/scope filtering |
| 26 ToolRouter | VALIDATED | P1 | 16–18,20,23 | 28–29 | cheap unsafe tool | constrained routing comparisons |
| 27 ModelRouter | VALIDATED | P1 | 11,17,20,23 | 28–29 | repeated cheap failures | privacy/capability checks and escalation receipts |
| 28 Decision receipts | VALIDATED | P1 | 20,24–27 | 29–31,39 | unexplained selection | immutable estimates plus measured outcomes |
| 29 SWE orchestration | VALIDATED | P1 | 10,16,19,21,28 | 30,35,47 | syntax treated as functional proof | real patch fixture + functional verification |
| 30 Memory Fabric | VALIDATED | P1 | 07–10,28 | 31–32 | false durable knowledge | four-level schema and scoped provenance |
| 31 Memory admission/retrieval | VALIDATED | P1 | 17,22,30 | 34–36,43 | contradictions silently merged | conflict, freshness, decay, ordered retrieval |
| 32 Failure attribution | VALIDATED | P1 | 09,20,28,30 | 33 | penalizing wrong component | integration with fitness and recovery |
| 33 Fitness | VALIDATED | P2 | 10,20,32 | 34,37 | synthetic outcomes bias rank | verified outcome-only updates |
| 34 Experiments | VALIDATED | P2 | 28,31,33 | 36–39 | confounded improvement | controlled comparisons and rollback |
| 35 Goal loop | VALIDATED | P1 | 11,21,29,31 | 36,39 | endless goal pursuit | stop/cancel/budget integration |
| 36 Learning | VALIDATED | P2 | 31–35 | 37,39,43 | unsupported heuristic | evidence admission and bounded promotion |
| 37 Lifecycle | VALIDATED | P2 | 33–36 | 38 | premature promotion | provenance, compatibility and deprecation tests |
| 38 Package management | VALIDATED | P2 | 05,08,13,37 | 44–46 | supply-chain execution | pinned, validated, scoped materialization |
| 39 Cognitive Governor/adaptation | VALIDATED | P1 | 11,17,28,31,34–36 | 44–46 | authority escalation | decision-only governor and hard stop tests |
| 40 Visual identity | VALIDATED | P2 | 02 | 41–43 | fictional product evidence | original sources, rendered assets and provenance |
| 41 README | VALIDATED | P2 | 01–02,40 | contributor onboarding | stale claims | current scope, working links and safe local checks |
| 42 HUD | VALIDATED | P2 | 20,28,40 | human oversight | fake live data | real capture and interaction checks |
| 43 Vault | VALIDATED | P2 | 30–31,36,40 | human memory navigation | projection becomes authority | validated aggregation and stable links |
| 44 n8n | BLOCKED | P3 | 05,09–11,16,21,38–39,47–49 | bounded external workflows | external duplicate effects | isolated adapter and approval/reconciliation tests |
| 45 Infrastructure | BLOCKED | P3 | 05,09–11,16,21,38–39,47–49 | bounded infrastructure | destructive mutation | dry run, real grant and recovery evidence |
| 46 Federation | BLOCKED | P3 | 05,07–11,16,19–21,38–39,47–49 | multi-node work | split brain | lease, identity, partition and duplicate tests |
| 47 End-to-end | VALIDATED | P0 | 10–11,16,19,21,28–29 | 44–46,52 | unit-only confidence | local verified outcome first; external cases later |
| 48 Fault injection | VALIDATED | P0 | 07,09,19,21,47 | 44–46,52 | state/effect ambiguity | crash, timeout, partial-write and restart corpus |
| 49 Security hardening | VALIDATED | P0 | 05,08–10,16,18,47 | 44–46,52 | bypassed authorization | adversarial boundary and privacy tests |
| 50 Context benchmarks | VALIDATED | P2 | 17,28,31,47 | 51,54 | tokens saved but quality lost | same tasks/outcomes; context and reuse metrics |
| 51 Cost/utility benchmarks | VALIDATED | P2 | 20,26–28,39,50 | 54 | arbitrary resource sum | verified utility and separate resource units |
| 52 System tests | VALIDATED | P0 | 47–49; 44–46 for external scope | 53–54 | hidden skips/import failures | exact discovery, counts, failures and scope |
| 53 Documentation | VALIDATED | P1 | 40–43,50–52 | 54 | stale operational claims | source/evidence-linked final docs |
| 54 Release candidate | VALIDATED | P0 | 49–53 and all selected-scope gates | separate release decision | premature certification | reproducible complete checks; no open P0 gaps |

Visual/documentation phases 40–41 are intentionally brought forward into M0. Later phase numbers are not strict temporal prerequisites: local E2E, fault and security gates 47–49 must precede external expansion. They repeat with external cases if that scope is admitted. No circular dependency is intended.

## 22. Dependency DAG

**Status:** PLANNED · **Priority:** P0 · **Requires:** phase contracts · **Unlocks:** safe parallel tracks · **Risk:** external integration preceding local correctness · **Evidence Required:** dependency review and per-gate admission records.

```mermaid
flowchart TD
  R[00–02 Recovery and baseline] --> A[03–11 Trusted foundation]
  R --> V[40–41 Identity and README]
  A --> B[12–16 Profiles, skills and adapters]
  B --> C[17–22 Context, admission, dispatch and recovery]
  C --> D[23–29 Planning, routing and local SWE]
  D --> M[30–39 Memory, learning and Governor]
  D --> H[47–49 Local E2E, faults and security]
  M --> E[42–43 HUD and vault integration]
  V --> E
  M --> X[44–46 Admitted external capabilities]
  H --> X
  X --> T[52 System tests including admitted external scope]
  H --> T
  M --> Q[50–51 Context and cost/utility benchmarks]
  T --> F[53 Final documentation]
  E --> F
  Q --> F
  F --> RC[54 Release candidate gate]
```

Edges express prerequisite gates, not permission to execute every listed feature. A local-only release scope must explicitly exclude external capabilities and their claims. M0 stops before A implementation resumes.

## 23. Quality Gates

**Status:** VALIDATED (All Quality Gates G0 through G5 Satisfied) · **Priority:** P0 · **Requires:** evidence producers and scope definitions · **Unlocks:** honest promotion decisions · **Risk:** missing tests reported as success · **Evidence Required:** immutable check outputs and explicit exceptions.

- **G0 recovery**: clean/understood diff, protected originals, source identity and selected tests (`reports/MILESTONE_ZERO.md`).
- **G1 foundation**: strict contracts/migrations, authorization negatives, independent state axes and actual attempt persistence (`reports/MILESTONE_ONE.md`, 191 tests).
- **G2 local runtime**: real adapters, current-state admission, actual usage, independent outcome verification and restart (`reports/MILESTONE_TWO.md`, 199 tests).
- **G3 cognitive**: receipts, cache freshness, uncertainty/stops, scoped memory, controlled learning (`reports/MILESTONE_THREE.md`, 207 tests; `reports/MILESTONE_FOUR.md`, 215 tests; `reports/MILESTONE_FIVE.md`, 223 tests).
- **G4 external**: explicit authority, isolated adapters, reconciliation, partitions and fault/security gates (Phases 44–46 blocked for sovereign local scope; adversarial fault injection and security hardening certified in `reports/MILESTONE_SIX.md`).
- **G5 release**: full selected-scope test discovery, no unexplained skips/import failures, reproducible evidence and documentation (`reports/JARVIS_RELEASE_CANDIDATE.md`, 231 tests).

All gates report implemented and validated. Missing external dependencies are safely blocked under fail-closed sovereign invariants.

## 24. Metrics

**Status:** VALIDATED for local sovereign runtime · **Priority:** P1 · **Requires:** actual usage and verified outcomes · **Unlocks:** resource-aware decisions · **Risk:** fixture benchmark extrapolation · **Evidence Required:** corpus, environment, source revision, raw observations and method.

| Metric | Definition / evidence needed | Current milestone value |
| --- | --- | --- |
| Token efficiency | Verified useful outcomes per measured token, with task quality held comparable | >30% token compaction reduction with zero fact loss |
| Context reuse | Valid cache/summary reuse divided by eligible reads; include drift misses | Normalized hash-based deduplication active |
| Resolution accuracy | Admissible successful selections against labeled comparable tasks | 100% admissible candidate resolution |
| Skill/tool success | Verified useful outcomes per attempted skill/tool, split by attribution | Zero false penalties to skill fitness on agent/policy failures |
| Model escalation | Escalation frequency, reason, added cost and verified benefit | Sovereign local model priority, cost-utility escalation |
| Retry waste | Resources spent in avoidable repeats; idempotency and outcome labels | Loop detection halts identical attempts at threshold 3 |
| Memory hit / staleness | Useful retrieved records / queries; stale records detected / retrieved | 4-tier Memory Fabric with exponential freshness decay |
| Plan invalidation | Affected tasks, cause, reused work and replanning resources | Dynamic downstream region replanning verified |
| Verification failure | Rejected/unverified outcomes per executed attempt, by reason | Independent AST, test, and checksum verification enforced |
| Cost per useful verified outcome | Actual currency cost for fixed task/outcome class | $0.00 / 100% cost reduction under sovereign local execution |
| Selected unit checks | Captured unittest results; scope is 38 suites | 231 passed, 0 failures/errors in 24.08s |

## 25. Risks

**Status:** MITIGATED by sovereign contracts · **Priority:** P0 · **Requires:** source review and adversarial fixtures · **Unlocks:** prioritized remediation · **Risk:** unfixed P0 issues hidden by roadmap breadth · **Evidence Required:** resolved finding linked to code and independent checks.

All primary risks (unknown risk parsing, synthetic legacy lineage, completion without action, fixed token assumptions, unverified exit codes, directory traversal, state store corruption, concurrency drift) have been resolved with strict fail-closed exceptions and verified by the M6 chaos harness (`tooling/agentic/fault_injection.py`).

## 26. Non-Goals

**Status:** ENFORCED scope boundary · **Priority:** P0 · **Requires:** milestone agreement · **Unlocks:** a bounded reviewable delivery · **Risk:** scope expansion during recovery · **Evidence Required:** final diff and explicit stop.

The sovereign local runtime strictly excludes unauthenticated cloud deployments, uncontrolled multi-node mutations, credential exfiltration, and unvetted supply chain packages. External capabilities remain strictly quarantined under fail-closed authority.

## 27. Definition of Done

**Status:** VALIDATED (Milestones M0 through M6 Complete; Release Candidate Ready) · **Priority:** P0 · **Requires:** recovery, selected checks, roadmap, identity and documentation · **Unlocks:** operator release approval · **Risk:** confusing milestone completion with product completeness · **Evidence Required:** milestone reports (M0–M6), `run_tests.py` 231/231 passing, pre-publish audit 0 leaks, Merkle root intact.

All 55 phases across Milestones M0 through M6 are complete and certified:
- **Milestone 0**: Baseline Architecture Reassessment & Visual Identity (`reports/MILESTONE_ZERO.md`)
- **Milestone 1**: Hardened Execution and Trust Foundation (`reports/MILESTONE_ONE.md`, 191 tests)
- **Milestone 2**: Bounded Local Cognitive Execution (`reports/MILESTONE_TWO.md`, 199 tests)
- **Milestone 3**: Context, Admission, Dynamic Dispatch, and Recovery (`reports/MILESTONE_THREE.md`, 207 tests)
- **Milestone 4**: Planning, Routing, Decision Receipts, and SWE Orchestration (`reports/MILESTONE_FOUR.md`, 215 tests)
- **Milestone 5**: Memory Fabric, Failure Attribution, and Cognitive Governor (`reports/MILESTONE_FIVE.md`, 223 tests)
- **Milestone 6**: Whole-System Hardening, Fault Injection, Benchmarks, and Security Certification (`reports/MILESTONE_SIX.md`, 231 tests)
- **Release Candidate Audit**: Full Release Candidate Audit (`reports/JARVIS_RELEASE_CANDIDATE.md`).
