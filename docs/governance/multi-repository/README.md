# Multi-repository engineering and security baseline

This directory is the canonical, versioned coordination point for the user's five repositories: J.A.R.V.I.S. (`jarvis-skill-registry`), TCC-DS, TCC-Markitos, Brique do Vini, and Robocode-2026. This campaign was explicitly requested against the user's Security Protocol v13.3 (nine domains, four release gates). Version alignment needs review: current J.A.R.V.I.S. `main` at `c263c2a2ffed5e7ddc50cc0584c04420df07ef5c` contains canonical v13.4, while this cross-repository plan and the active work remain scoped to requested v13.3. Do not silently relabel v13.3 as latest or substitute v13.4 during this campaign. Resolve the version baseline in a follow-up decision before starting a new cross-project phase. This document defines how the requested controls become project-specific, testable evidence; it does not replace repository instructions, domain rules, or product decisions.

## Authority and preservation

Resolve requirements in this order: the explicit current user request; applicable repository instructions; accepted product/security decisions; this cross-repository coordination contract; project-specific implementation. Record conflicts and ask for a decision when they change user-visible behavior, data, security authority, or eligibility. A common baseline adds missing controls; it never removes a valid product rule, flow, role, migration, compatibility promise, or capability. Audit before editing, search existing issues and mechanisms before proposing new ones, and use the existing owner of each concern. An UNKNOWN control is not PASS. Do not report a global audit as complete until each repository has its own inventory, threat/data-flow review, relevant negative tests, and current evidence.

## Shared engineering contract

1. Preserve each repository's actual architecture, product boundaries, domain vocabulary, release process, and existing validation policy. No blanket migrations, generic platform rewrites, or duplicated planner/registry/runtime.
2. Keep secrets and real personal data outside Git, logs, screenshots, test fixtures, and public bundles. Use synthetic fixtures and identify data owner, sensitivity, purpose, retention, and access boundaries.
3. Trust server-side authorization, not frontend redirects or caller-supplied tenant, role, owner, price, state, or identity. Map role × route/action × resource × tenant where the domain has identities/resources; test allow and deny cases. For non-authenticated software (such as a Robocode robot), explicitly mark auth, tenant, payment, and network controls N/A with the reason.
4. Critical configuration fails closed: missing/invalid `REQUIRE_AUTH` or equivalent cannot enable anonymous access; no default production passwords, weak fallback secrets, disabled TLS verification, public sensitive database ports, public `.env`/dumps/config, or internet-exposed management plane. Segment guest/client, app, data, and management networks with actual default-deny firewall/ACL controls; subnet/VLAN separation by itself is not proof.
5. Inspect and test insecure defaults, including the reachable value, sink, environment, and negative case. Use Trail of Bits `insecure-defaults` as an audit method where applicable; do not cite a scanner as proof of absence.
6. Attach evidence to exact commit, artifact digest, environment, command/tool version, UTC timestamp, expected/actual outcome, and owner. Reject stale evidence, mismatched artifacts, future timestamps, incomplete runs, or uninspected outputs. Treat SLSA 1.2 source/build provenance according to real tool support; record unavailable provenance as UNKNOWN/PENDING, never fabricated PASS.
7. Release decision is four separate gates: SECURITY, QUALITY, RELIABILITY, and PRIVACY/COMPLIANCE when applicable. Each outcome is PASS, FAIL, UNKNOWN, or justified N/A; release readiness requires every applicable gate PASS, no blocker, and evidence for the artifact being released. A checklist or successful compile alone does not pass a gate.
8. Apply accessibility appropriate to the product (WCAG 2.2 AA for new user-facing web journeys; state a justified scope for CLI/desktop/robot code), business invariants, migration/recovery, performance, telemetry with minimization, incident handling, deployment rollback and operating ownership. Do not introduce paid services, new infrastructure, or parallel systems without product need and approval.
9. Avoid GitHub Actions as a gate where a project policy excludes it. Use each repository's documented local/direct runner and provider checks only where that project already relies on them. Never infer deployment, production readiness, contest eligibility, or winning performance from documentation alone.

## Nine v13.3 domains as an applicability map

| Domain | Evidence expected when applicable |
|---|---|
| 1. Governance, architecture, secure SDLC | Owners, data/trust boundaries, decisions, dependency/source inventory, scoped changes and review trail |
| 2. Identity, authentication, authorization, sessions, anti-abuse | Fail-closed startup/config; RBAC × routes/actions × resources/tenant tests; session/rate-limit/recovery controls |
| 3. Web, API, injection, business logic | Route inventory; validation/output controls; abusive/boundary/replay/concurrency tests; server-side invariants |
| 4. Data, database, RLS, privacy, compliance | Classification, least privilege/isolation, minimization/redaction/retention, migration and restore evidence |
| 5. Cloud, infrastructure, secrets, supply chain | Private-by-default services/network, secret exclusion, dependency/build provenance and artifact integrity |
| 6. Reliability, resilience, performance, DR | Timeouts/limits, degraded behavior, measurable budgets, recovery/rollback/restore evidence |
| 7. Logging, audit, detection, incident response | Redacted useful event trails, owners/alerts, response and recovery procedures tested to relevant level |
| 8. Testing, quality engineering, accessibility | Existing test/build/lint/typecheck gates, negative/regression coverage, keyboard/screen-reader/responsive evidence where applicable |
| 9. AI, RAG, agents, MCP | Prompt/tool/output/memory trust boundaries, least authority, per-tool/resource authorization, budgets/kill switch/poisoning tests; N/A with reason otherwise |

## Four release gates

- **SECURITY:** Applicable v13.3 controls have implementation and executable negative evidence; no unresolved critical blocker, leaked active secret, insecure default, auth bypass, tenant leak, or exposed control plane.
- **QUALITY:** Business requirements and existing behavior are mapped to tests; relevant static checks, tests, build/package and compatibility checks pass.
- **RELIABILITY:** Applicable runtime/limits/failure/recovery and rollback checks pass; critical skipped work, data-loss paths, or unrecoverable migration are blockers.
- **PRIVACY/COMPLIANCE:** Data purpose, minimal exposure, retention, access, deletion/rights and legal owner are evidenced where applicable; legal questions remain PENDING LEGAL rather than silently passed.

## Ordered master prompt sequence

Execute in order; a later phase consumes the previous phase's evidence. Run the prompt in the target repository and include its `AGENTS.md` and canonical docs as context.

### P0 — Baseline and scope (all repos; read-only)

> Inspect the repository's current branch, commit, working tree, applicable instructions, product/architecture/decision/security docs, manifests, tests, CI or direct gates, deployment files, and issues. Inventory user-visible workflows, business rules, roles/routes/data, integrations, runtime boundaries, and existing validation. Read Protocol v13.3 from its existing canonical location. Label every statement OBSERVED, DECLARED, INFERRED, UNKNOWN, or PROPOSED and cite file/line or command evidence. Build a feature/rule preservation matrix and applicability matrix for all nine protocol domains. Identify only concrete, reachable gaps and overlaps with existing mechanisms. Do not edit, delete, deploy, publish, or expose secret values. Deliver prioritized findings, risks, dependencies, exact pre-change SHA, and proposed smallest changes.

**DoD:** complete tracked/untracked inventory; preservation matrix; evidence-separated nine-domain review; requirements-to-behavior map; no secret value copied into report; concrete findings mapped to existing issue/mechanism or new issue proposal; unresolved questions and evidence freshness recorded.

### P1 — Governance contract and local gates (central J.A.R.V.I.S. then target repo)

> Extend existing canonical governance, do not create parallel systems. Turn each applicable v13.3 control into an executable gate or a clearly owned pending external/legal gate. Cover missing/invalid critical configuration fail-closed behavior, RBAC × routes/resources × tenant allow/deny, insecure defaults, secret/public-file exposure, privacy minimization, artifact/commit/environment evidence freshness, exact timestamps, SLSA 1.2 provenance availability, and the four independent release gates. Include positive and negative fixtures, machine-readable result and raw references, and tests proving that missing, stale, future-dated, malformed, or mismatched evidence cannot PASS. Preserve all current project gates and product behavior. Run the repository's own documented checks; do not add GitHub Actions where excluded.

**DoD:** negative tests prove fail closed; old successful paths stay green; every applicable gate has implementation/owner/current-evidence format; N/A includes rationale; unknowns stay unresolved; reports are bound to commit+artifact+environment; no merge or deploy on missing evidence.

### P2 — Domain/repository implementation (one repository at a time; order below)

> Implement only the approved concrete gap from the P0 matrix. Before coding inspect its owner, upstream/downstream callers, current tests and issue history. State invariant and compatibility behavior. Add the smallest vertical implementation and regression/negative test, update the canonical repository documentation and cross-repository bridge, and map requirement → changed seam → test → exact evidence. Do not remove existing valid features or business rules. Do not claim categories or the whole repository audited beyond inspected evidence. Follow repository branch/issue/deployment/quota policy. Stop on ambiguous authorization, privacy/legal decisions, unsupported platform assumptions, and disclose why.

**DoD:** behavior preserved; targeted tests prove allowed and denied/boundary behavior; repository checks pass or blockers are documented; docs identify observed versus planned behavior; change has rollback/recovery note when data/state changes; current evidence is reproducible.

### P3 — Cross-repository compatibility review (after individual PRs)

> Compare the five repository bridges against this canonical baseline. Verify protocol version and canonical links, project-specific exemptions, no duplicated runtime/planner/catalog, no contradictory instructions, no private findings exposed by the public J.A.R.V.I.S. repository, and no user changes overwritten. Verify each PR's diff and base SHA independently, refresh direct checks after integration, and report unclosed findings and external actions. Do not merge or deploy.

**DoD:** five repository rows have owner/status/branch/PR/current validation/blockers; no project claims inherited from another project's PASS; every source bridge resolves; all integration evidence is fresh; any failed gate remains NOT READY.

## Repository execution order and prompts

Order: **J.A.R.V.I.S. governance → Robocode-2026 → TCC-DS → TCC-Markitos → Brique do Vini → P3 integration review.** Each repository completes P0/P1 before P2; the ordering makes the coordination contract available first, then addresses contest-specific and data-sensitive domains before broader product work. Do not bulk-apply controls to other repositories.

### J.A.R.V.I.S. / `jarvis-skill-registry`

> Use `AGENTS.md`, `docs/README.md`, `SECURITY.md`, the existing v13.3 protocol, `evidence/current.json`, and existing Superpowers/validation tooling as canonical. Preserve fail-closed mission/command/plan approvals, evidence freshness, memory provenance, current v0.2 incomplete status, immutable tags, Obsidian files, and existing runtime boundaries. Audit agent/tool/MCP authz, poisoning/rug-pull/excessive-agency, budgets/kill switch, secrets, local-first privacy, per-resource authorization, supply chain and lifecycle gates. Extend current `validate_v020_plan4.py`/direct gates rather than inventing a competing release engine. Keep user-specific/private repository findings out of public docs. Run doctor/full-test/benchmark and scoped gates relevant to the change; keep the changed user-facing route check where relevant.

**DoD:** existing v0.2 status/evidence remains truthful; new control is test-discovered; permission/poisoning/freshness failures remain fail-closed; no credential or private repo evidence enters public artifacts; Windows-only evidence is explicitly pending unless directly run.

### Robocode-2026

> Treat the official CPS 2026 regulation as the controlling tournament contract and the latest `RonaldinhoSniper.java`/`HOMOLOGACAO_FINAL_CLOUD_2026.md` freeze as a protected baseline. Inventory every tracked Java robot, dependency, runner and historical result. Preserve all existing robots and baseline. The submission is exactly one self-contained `.java`; its filename, public class and registered team name must match; header lists team/integrants and identifies AI tool, prompt and boundaries. Use CPS 800×600, five robots maximum (qualifiers), three rounds, 0.1 gun cooling, 450 inactivity; bracket groups advance two until three finalists; final is three robots, tied scores need rematch. Implement a candidate derived from the strongest proven logic, compare paired deterministic candidate vs frozen champion and representative opponents on identical legal matches, record commit/source digest, engine/Java version, seed, configs, raw scores, rank/points, survival, damage, runtime/skipped turns, and test the exact submission file. Never label champion without direct tournament-format evidence. No network/auth/data controls are applicable to the isolated robot runtime; explain that. Keep strategy explanations understandable for oral code review and honor CPS AI attribution/plagiarism rules.

**DoD:** one-file submission builds against the organizer-compatible engine/API and Java target; class/filename/team registration verified; no forbidden runtime/network dependency; qualifiers and final use exact configs; independently reproducible deterministic comparisons against frozen baseline and diverse strong bots; zero runtime/skipped-turn faults; evidence and residual risk published. Until proven, status remains CANDIDATE.

### TCC-DS

> Preserve the private-creche domain, PHP/SQLite baseline and incremental Java 21/Spring Boot + MySQL 8.4 modular-monolith direction, React/Vite frontend, no-paid-core dependency, and TCC-Markitos process reference without importing its business rules. Follow `AGENTS.md` and its mandated product/architecture/decision/backlog/roadmap docs. Keep child/guardian/health/pickup/finance PII synthetic in tests and minimized in logs. Test backend authority and role × route × resource × school-tenant negative access, startup with missing `REQUIRE_AUTH`, migration/restore compatibility, and privacy/retention. Use documented frontend/backend commands; GitHub Actions remains excluded. Preserve PHP/SQLite until each migrated vertical slice reaches parity.

**DoD:** no broad rewrite or undocumented product behavior; each migrated slice has compatibility and rollback evidence; authz negatives and synthetic PII evidence pass; WCAG 2.2 AA claims backed by journey review; release gates bind to same artifact.

### TCC-Markitos

> Preserve `AGENTS.md` issue→branch→PR discipline, current local gates, no Actions, Vercel ignore behavior, Render autoDeploy off/quota stopping, production-from-main, product rules and valid releases. Audit all auth/RBAC × routes × tenant boundaries, payment/webhook server authority if applicable, secrets, data/retention/redaction, source maps/public `.env`, UI/accessibility, and evidence timestamps/artifact freshness. Repair only reproducible gaps; tests must exercise real validation entry points and rejection paths. Never use provider deploys as iterative test runners or reopen completed work without an objective defect.

**DoD:** documented local checks pass; direct production/deployment claims stay bounded to actual provider evidence; no Actions introduced, no extra provider spend, valid historical behavior remains intact, stale/future/mismatched evidence blocks closure.

### Brique do Vini

> Inspect the existing shop/customer journey, catalog/inventory/orders/payments/shipping/admin ownership and actual routes before proposing rules. Preserve current commerce and design behavior. Make the server the authority for price/discount/tax/stock/order/payment; protect webhook signature/replay and admin actions if applicable; test auth/session/CORS/rate limits, secret/public config/source-map exposure, privacy retention/redaction, real payment callback and order failure/retry paths with synthetic fixtures. Audit mobile and accessibility against real flows. Reuse existing contract/security gates and provider quota/deploy discipline; don't invent payment, PII, or admin capabilities from assumptions.

**DoD:** concrete business invariants map to current code/routes and negative tests; local contract, build and security checks pass or blockers are recorded; no false production/payment claims; architecture docs distinguish existing behavior from recommendations; data migrations have recovery evidence.

## Per-repository status ledger

Updated 2026-10-01 to record the latest Robocode candidate head and direct-rival confirmation runs; other repository rows remain bounded to the evidence listed in each row. This is a bounded execution ledger, not a claim that all repositories have received exhaustive file-by-file audits. `UNVERIFIED` means that specific gate has not been satisfied; completion summaries must include base SHA, branch/PR, files, commands/results, blockers, and evidence date.

| Repository | P0 audit | P1 gate | P2 implementation | Release status |
|---|---|---|---|---|
| J.A.R.V.I.S. | PARTIAL (cross-repo plan only) | UNVERIFIED | Docs | BLOCKED: evidence manifest remains INCOMPLETE; the earlier 647/647 battery result is not refreshed evidence for this doc-only branch. PR #69 merged independently; PR #72 merged; Issue #71 remains open. Mainline version is v13.4, while this campaign is explicitly scoped to v13.3. No release authorization. |
| Robocode-2026 | PARTIAL (rules, source, runners, representative opponent pools) | N/A by isolated runtime boundary | Multi-format challenger experiments, direct rival runner, corrected watchdog validity gates | `RonaldinhoSniper.java` remains byte-for-byte at frozen baseline `546afb28a70b8af69ad25d75f51d5617b2b17f47`. Earlier duel-only σ=8 experiments passed 96 local 1v1 and 64 three-robot no-regression battles but were REJECTED for five-robot CPS classification in 120 battles; pattern-matcher variants were also rejected. Direct `RonaldinhoSniperBest` vs `DeepSeekV4proHigh` (32 per side): baseline 86.7% (26/30 valid), challenger 77.4% (24/31), paired delta −10.3 pp/29 pairs. σ=8 confirmation vs `RonaldinhoSniperV5` (64 per side): baseline 34.5% (20/58), challenger 44.8% (26/58), +7.5 pp/53 pairs; six invalid battles per side. σ=8 vs `DeepSeekV4proHigh` (32 per side): baseline 60.0% (18/30), challenger 53.1% (17/32), −3.3 pp/30 pairs. Six-style 1v1 matrix (8 battles per style/variant; 96 total): baseline 91.4% match wins over 35 valid vs σ=8 100% over 38 valid (+8.6 pp match, +5.8 pp rounds), but REJECT due zero-failure gate (13/48 baseline and 10/48 challenger runtime invalid; own robot fault in 12/13 and 9/10 lines respectively; only 4 baseline and 2 challenger V5 battles valid). Hence the apparent 100% is not clean evidence; duel-only specialization remains unproven. Robocode 1.11.1/OpenJDK 21.0.12.1 reports deterministic RNG unsupported, so paired local runs are exploratory and not official CPS proof. Runners reject watchdog/skipped-turn/exception-contaminated results; 21 focused tests pass. Official CPS page checked 2026-09-30 (up to five per group, top two advance, 800×600, three rounds, 0.1 cooling, 450 inactivity, submission by 2026-10-30). | PR #9 Draft at `cf1aca52015071c38dd1629e584026b5965caacc`; frozen source retained; no universal-winner claim. |
| TCC-DS | PARTIAL (release evidence path) | Partial: local evidence validator | Local validator + docs | Exact PR #159 head `1405eb39bc3cddb1dc03ddc7a9725863f6163f1f`: `npm run test:release-evidence` 21/21 pass on Node 24.18.1. NOT RELEASE AUTHORIZED; PR #159 remains Draft. |
| TCC-Markitos | PARTIAL (evidence freshness path) | Partial: repo-specific config/security validators | Local hardening + docs | Exact PR #174 head `77b39d5b2d34eb56b538a02949e22101de2e3fb2`: five focused local validators pass on Node 24. NOT RELEASE AUTHORIZED; PR #174 remains Draft. |
| Brique do Vini | PARTIAL (preflight path) | Partial: fail-closed local runner | Local runner + docs | Exact PR #25 head `de9e463c9499268516382e7befea9dfbb65c0338`: `node --test scripts/preflight.test.mjs` 3/3 pass on Node 24.18.1. Project requires Node 22.x; full supported-runtime preflight remains PENDING. NOT RELEASE AUTHORIZED; PR #25 remains Draft. |

No repository has passed all four cross-project release gates under this bounded campaign. Production deployment, production provenance/SLSA claims, full domain inventory, and any physical/device acceptance remain unverified where applicable. Local test/validator PASS results above prove only the invoked checks at the listed heads. Merged J.A.R.V.I.S. PRs #69/#72 do not satisfy or replace any cross-project release gate.
