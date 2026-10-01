# Public J.A.R.V.I.S. system reassessment — 2026-10-01

## Scope and evidence boundary

This is a bounded source audit of the public J.A.R.V.I.S. repository at `main@55406f4212ffb64abf68a7be0f2d41017240018a`, the exact mainline snapshot reviewed before this change. It covers the tracked source tree, local direct test harnesses, Obsidian configuration structure, and remote repository/PR metadata. It is not a line-by-line proof of every runtime path, an audit of every repository accessible to the account, or a release certification.

Repository facts, local-machine observations, remote metadata, and unknown external behavior are kept separate. Private Vault/plugin payloads, credential values, personal memory, and names of private repositories are intentionally excluded from this public report. No user-owned dirty checkout data was staged or copied into the candidate. No GitHub Actions were created or used.

## Measured repository inventory

The tracked snapshot contains 1,888 files: 895 Markdown files, 524 `SKILL.md` files across canonical and staged content, 445 JSON files, and 38 JSONL files with 64,192 nonempty records. All JSONL records parsed. Among the skill files, 520 have YAML frontmatter, 520 declare `name`, and 519 declare `description`; four tracked `SKILL.md` files have no opening frontmatter block.

Sixteen tracked files under `exports/` have a `.json` extension but do not parse as JSON. Inspection identifies them as historical text-marker export artifacts, not structured bundles. They are preserved as legacy history; they are not silently repaired or promoted to trusted data. No database file (`.db`, `.sqlite`, `.sqlite3`, `.duckdb`, `.mdb`, or `.realm`) is tracked in this snapshot. The repository contains serialized JSON/JSONL state; live provider stores and remote databases were not queried.

## Confirmed findings

1. **Memory crossed a public boundary.** The tracked memory note and JSON previously contained personal profile/fact data, and runtime projections could write private records into a tracked note. The candidate replaces the tracked JSON with an empty compatibility template, moves new local writes to an ignored `state/jarvis_memory.local.json`, and projects instructions/status only. A synthetic canary test checks that private memory does not enter the public note. Earlier public Git blobs remain unchanged; this work does not rewrite repository history.
2. **Export labels overstated the bytes and trust.** The previous export path could write a text marker under JSON/archive extensions, describe a concatenated digest as a canonical Merkle root, and return a verified result from a mutable local ledger without authenticating a publisher. The candidate emits parseable metadata-only JSON, defines its exact inventory-fingerprint scope, prevents overwrite, and fails closed for OCI/tar formats and cryptographic-authenticity claims.
3. **OCI verification was not cryptographic verification.** The prior distribution path could manufacture an unsigned payload, accept a forged `VALID` label, and mark intake clean without checking a trusted signature. The candidate disables OCI creation and pull intake until a real packer and trusted-key verifier exist. Hash consistency is reported separately from signer identity and quarantine clearance.
4. **The saved canonical skill digest is stale.** `state/canonical-merkle.json` says it was generated on 2026-09-07 and lists 145 leaves. In the reviewed tracked snapshot, zero leaf content hashes match raw `SKILL.md` bytes; two match only after newline normalization; 143 do not match. The root was not regenerated or blessed. The pre-publish scanner loads this anchor but does not recompute it.
5. **The release manifest remains incomplete.** `evidence/current.json` still marks release, portable-runtime, legacy-governance, and browser-smoke status as `DIRECT_VALIDATION_REQUIRED`. Passing local tests does not clear cross-platform, provider, browser/device, or release evidence that was not directly produced.
6. **Export health output also overstated its checks.** The earlier diagnostic labeled a schema conformant after comparing only title and version, and called a present ledger/storage healthy without validating contents. The candidate changes these labels to header match, present-but-unvalidated, and counts-match-without-authentication; full JSON Schema validation remains explicitly unrun.

## Changes in this candidate

- Separated local memory writes from public Markdown/JSON projections and added privacy regression coverage.
- Replaced the false export marker with a scoped, metadata-only JSON contract; unsupported archive formats now stop before writing.
- Disabled misleading OCI signing/verification/intake paths and rewrote examples, schemas, CLI output, ADR, and trust-boundary documentation to match actual behavior.
- Replaced the prior weak export/OCI checks with isolated temporary-directory tests for parseability, no-overwrite, tampering, forged signature labels, and no-write failure behavior.
- Reworked export health output so it reports only the checks actually performed and never emits schema-conformance or healthy-storage PASS from presence checks.
- Added the E0–E5 evolution prompts for source inventory, memory/export provenance, working chat/voice/data paths, incremental repair, Obsidian Graph/animation, and exact-head publication.
- Updated the public README and documentation map to make the local-memory boundary and follow-on audit materials discoverable.

## Remaining gaps and next work

- The accessible-account repository list was inspected as metadata only. Source code outside this J.A.R.V.I.S. repository, including private repositories, was not cloned or audited.
- The actual Obsidian UI was not launched for a fresh Graph View test in this audit. Local Graph configuration and a committed 23,897-node animation asset exist, but this report does not re-assert its current rendered frame count, playback duration, or behavior on the installed Obsidian version. User-local Graph/plugin changes are not part of this public candidate.
- Chat and voice were not validated against a live model provider, microphone, speech-recognition browser, or TTS backend. UI/control tests and API fixtures do not prove those live paths work.
- External GitHub search freshness, external databases, deployment state, and account data beyond returned metadata remain unverified.
- The exact candidate SHA must pass its direct validation set before merge. The evidence manifest and any missing platform/UI proof remain explicit blockers; this document is not a substitute for those gates.

## Success criteria for follow-up

Complete E0–E5 in [`JARVIS_EVOLUTION_PROMPTS.md`](../../docs/governance/multi-repository/JARVIS_EVOLUTION_PROMPTS.md), preserving local human Vault work and imported content. Publish no skill copy with unknown redistribution rights, add no link without direct evidence, show data freshness/provenance at its point of use, and merge only after current exact-head validation and remote mergeability are confirmed.
