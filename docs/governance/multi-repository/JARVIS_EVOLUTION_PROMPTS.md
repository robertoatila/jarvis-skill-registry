# J.A.R.V.I.S. evolution prompts

This prompt set is a continuation of the canonical [multi-repository baseline](README.md) and its P0–P3 sequence. It is based on the bounded 2026-10-01 review of the public J.A.R.V.I.S. mainline. Run one phase at a time on the named exact checkout; carry forward the source SHA, evidence, and unresolved limits. A prompt is an instruction for future work, not proof that the work is complete.

## E0 — Whole-system evidence inventory

> On this exact checkout and commit, inventory tracked and untracked files, Git remotes/branches/PRs, application entry points, routes, UI controls, API integrations, providers, databases and data files, Obsidian configuration/notes/Canvas, skills and their frontmatter/resources, schemas, JSON/JSONL records, scripts, tests, and generated artifacts. Respect `.gitignore`; do not read or print secret values. Measure parsable/invalid JSON and JSONL, duplicate or stale records, skill-to-index coverage, internal links/backlinks, and database presence; distinguish repository facts from local/remote facts. Label every conclusion OBSERVED, DECLARED, INFERRED, UNKNOWN, or PROPOSED and give path/line or reproducible command evidence. Do not edit or migrate during this phase. Produce an inventory matrix, risk-ranked findings, preservation requirements, and the smallest ordered remediation plan. Do not claim the whole repository passed without enumerating what was inspected.

**Done when:** exact SHA and clean/dirty boundary are recorded; local-only and remote-only evidence are separated; every requested data class has a finding or an explicit access gap; secrets and personal data are absent from the report; no automated migration occurred.

## E1 — Data privacy, provenance, and export trust

> Audit every path that reads, writes, projects, logs, exports, indexes, or publishes memory and repository data. Trace source → transform → store → user/remote sink. Keep personal memory local and ignored by default; use synthetic canaries to prove it never reaches a tracked Obsidian note, public report, audit log, export, or unauthorized UI response. For artifact distribution inspect actual bytes, MIME/media type, source-file binding, digest scope, signature verifier, and trusted-key source. SHA-256 consistency is not identity, signature, quarantine clearance, or a Merkle proof. Compare every declared integrity leaf with current bytes and report drift; never recompute and bless an unexplained root. Fail closed where a real implementation or trusted evidence is absent. Preserve old records as untrusted history rather than rewriting them to look valid.

**Done when:** no private fixture reaches a tracked/public sink; payload bytes match their extensions and media types; unkeyed/fake signatures cannot pass; stale leaf manifests remain blocked; negative tests cover malformed, changed, unsigned, untrusted, missing, and stale inputs.

## E2 — Working product paths: chat, voice, data freshness, and Obsidian

> Trace each visible HUD control to a real backend action and current data source. With a fresh local profile and synthetic data, exercise chat send/response/error/loading/cancel; settings, provider connectivity, and route failures; browser microphone permission, speech recognition, unsupported-browser state, dictation insertion, and explicit send; TTS availability and playback; memory create/read/update/delete; GitHub/source search freshness and provenance; and Obsidian Graph/MOC links, filters, projection, and preservation of human content. Use browser E2E for user-visible paths and unit tests only for internal logic. Do not claim live voice, model connectivity, GitHub freshness, or Obsidian application behavior from static controls or mocked responses. Make unsupported provider/browser/platform cases visible and actionable; never substitute stale fixtures as current results.

**Done when:** every visible primary action has success and failure coverage, current-source provenance, and an accessible disabled/error state; no default send or unauthorized memory write occurs; Obsidian links resolve and sync preserves unmanaged human content; verified browser/device scope is stated.

## E3 — Data quality and incremental repair

> Use the E0 inventory and existing canonical indexers, Atlas/MOCs, resolvers, and sync machinery. Classify stale, duplicate, malformed, inaccurate, orphaned, externally imported, and human-authored records without deleting any source. For imported skills, retain upstream URL, source revision or digest, attribution, and license evidence; do not publish copied skill content when redistribution rights are unknown. Produce a dry-run manifest with stable record ID, before/after digest, evidence for every proposed relation, destination, and rollback path. Add only links supported by explicit metadata or direct source evidence; do not connect items only because they share a folder, language, or tag. Apply migrations in small resumable batches, preserve every original, and report unresolved cases instead of guessing.

**Done when:** dry-run is reproducible; each changed record has source evidence and rollback; no invented links or destructive pruning occur; repeated runs are idempotent; post-migration link, schema, count, and orphan measurements match stated criteria.

## E4 — Exact-head publication and merge review

> Review the complete diff against the stated base, inspect public data exposure and all changed tests, run the repository’s documented direct gates on the exact candidate SHA, then refresh provider/PR checks and mergeability. Preserve unrelated local work and keep unrelated PRs separate. Do not create GitHub Actions where policy excludes them. Do not merge while a required check, privacy decision, fresh exact-SHA evidence, protected baseline, or external acceptance is unresolved. After an authorized merge, verify the remote target SHA, PR state, resulting tests, and remaining release blockers. Report merge, deployment, and release as separate states.

**Done when:** the diff is reviewed; validation is bound to the exact SHA; no private Vault facts are in the public tree; every required check is current and passing; PR/base/head identities are verified; remote post-merge state is directly observed; remaining release blockers are named.

## E5 — Obsidian Graph, filters, and native animation

> Work from a disposable copy of the Vault. First record the exact hashes of `.obsidian/graph.json` and relevant workspace state; never overwrite a dirty user copy or plugin data. Measure notes, explicit links, connected components, unresolved links, and orphans before changing the view. Compare the native global and local Graph Views, and distinguish real wikilinks from visible relationships introduced by shared tags. Improve presentation with native color groups, filters, node/link forces, and a focused default view; keep all notes, GitHub-starred knowledge, attachments, and archives indexed and searchable. Test one variable at a time so a denser picture is not mistaken for new semantic links. Verify the native **Animate** behavior in Obsidian itself: use a clean test copy, confirm the actual note-creation order and empty-start behavior on the installed version, and capture the real application output. Do not synthesize or retime a substitute video and do not claim multiple saved profiles unless the installed core/plugin actually supports them.

**Done when:** no note or attachment was removed; graph counts and link provenance are reproducible; all native filters and color groups work in the installed Obsidian UI; the focused view is visibly clearer while the audit view retains the full corpus; and the delivered video is a direct capture of Obsidian's own animation with its duration and limits recorded.

## E6 — Canonical sources, protocol versions, and freshness

> Trace every time-sensitive product claim and imported record to its authoritative source: protocol specifications (including the exact SSP version used), upstream skill repositories, provider/model documentation, package registries, GitHub metadata, and other external APIs. For each source record its canonical URL or repository, immutable version/commit where available, retrieval time, content digest, license/attribution, freshness policy, and the consumer that displays it. Compare the checked-in protocol with the newest authoritative release; if the upstream source cannot be established, report the version as unverified instead of guessing. Distinguish live, cached, stale, synthetic, and user-authored data at the point of use. Refresh through existing canonical adapters, preserve snapshots and provenance, and never turn a failed fetch into a current-looking fallback.

**Done when:** every mutable claim has a cited source and an observable retrieval/version marker; stale and unavailable sources are surfaced honestly; updates are reproducible and license-aware; and no data is relabeled current merely because a refresh job ran.

## E7 — Database and structured-record integrity

> Inventory database drivers, connection configuration names, migration files, schema definitions, embedded stores, JSON/JSONL state, and remote database declarations. Never print credentials or query an external host without an explicitly authorized, read-only connection path. Separate “no database file in this checkout” from “no remote database exists.” In an isolated copy or approved read-only session, inspect schema/version, row counts, constraints, referential integrity, duplicate keys, null/invalid fields, retention, and data lineage. Identify which source is canonical for each record and trace the path into caches, indexes, exports, Obsidian, reports, and UI. Propose corrections as dry-run manifests with backups, stable IDs, before/after digests, rollback, and resumable batches; do not delete or rewrite the source to make validation pass.

**Done when:** every discovered store is classified as local, remote, generated, or declared-only; schema and record checks have direct evidence; privacy boundaries and lineage are documented; and any proposed migration is repeatable, reversible, and verified against the exact source snapshot.

## E8 — Authorized multi-repository audit

> Re-enumerate repositories reachable through the configured GitHub connection and record only the metadata needed for scope: visibility, default branch, current head, archival state, and likely relationship to J.A.R.V.I.S. Do not place private repository names or contents in a public report. Inspect source only for repositories inside the user's authorized scope, using a read-only checkout at an exact SHA and each repository's own policy. Map shared packages, protocols, skills, APIs, and deployment artifacts to one canonical owner; identify duplicate, stale, or conflicting copies with file-level evidence. Do not change another repository, push, open a PR, or copy code/skills across repositories as a side effect of the audit. Record inaccessible repositories and missing permissions as explicit gaps.

**Done when:** the discovered repository set and exact audited SHAs are recorded privately; public reporting is redacted; cross-repository relationships cite source evidence; and each repository is clearly marked source-audited, metadata-only, or inaccessible.

## E9 — Tool, provider, and automation reality check

> Build a capability map from every user-visible control to its implementation: UI action → command/API/MCP adapter → provider or local tool → data source → observable result. Include chat, voice input/output, Obsidian integration, GitHub/source search, file and shell tools, scheduled jobs, and recovery paths. For each capability record installation/version, required permissions, real-versus-mocked mode, supported platforms, timeout/cancellation behavior, rate limits, error handling, and freshness. Exercise success, denial, offline, stale, malformed, and timeout cases with synthetic data. Confirm that mutations require the declared authorization, secrets stay out of logs, and a missing integration never returns a fabricated success. Extend existing connectors and canonical services rather than creating duplicate planners or adapters.

**Done when:** all primary controls have a traceable implementation and real success/error evidence; unsupported capabilities are labeled clearly; authorization and cancellation work; and mocks cannot be mistaken for live provider evidence.

## E10 — Next-step prompt generator

> Read the newest bounded audit report, exact checkout SHA, dirty-worktree boundary, open PR/base/head state, direct checks, and unresolved evidence. Generate a prioritized set of no more than seven next prompts. Each prompt must name one outcome, exact repository/scope, required read-only discovery, allowed mutations, preservation/privacy constraints, source evidence, validation commands, success criteria, and stop conditions. Group work by dependency so source inventory precedes migration, migration precedes publication, and publication follows fresh exact-head validation. Reuse existing canonical systems and open PRs where appropriate; do not create duplicate tools or prompt phases. Mark every unknown and access gap instead of converting it into a task assumption.

**Done when:** every prompt maps to an observed unresolved finding, contains measurable acceptance and a safe rollback or stop condition, has no duplicated scope, and makes no claim that its future work has already been completed.
