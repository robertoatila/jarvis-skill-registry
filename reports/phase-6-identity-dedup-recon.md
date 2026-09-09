# Phase 6 Reconnaissance: Identity & Deduplication

**Skill Registry Lifecycle Platform**  
**Date**: 2026-08-31  
**Phase**: Phase 6 — Identity & Deduplication  
**Status**: `READ_ONLY_RECONNAISSANCE_COMPLETE`

---

## 1. Context & Baseline Assessment

With Phase 5 sealed in `GATE_5=PASS`, the registry possesses cryptographically immutable provenance anchoring (`index/provenance.jsonl`) and deterministic Merkle content hashes (`index/integrity-manifests.jsonl`).

Phase 6 must now implement the **Multi-Dimensional Identity & Deduplication Subsystem**, preventing the simplistic mistake of equating identity merely to `SHA-256 == SHA-256`.

---

## 2. Multi-Dimensional Equivalence Model

A skill resource possesses multiple independent identity dimensions that can converge or diverge independently:

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                    RESOURCE IDENTITY DIMENSIONS                         │
├──────────────────────┬──────────────────────────────────────────────────┤
│ 1. Content Identity  │ Merkle content_hash + manifest_hash + file tree  │
│ 2. Logical Identity  │ canonical_name + capabilities + declared schema  │
│ 3. Lineage/Origin    │ provenance_id + origin_uri + commit_sha / branch │
│ 4. Version Lineage   │ semver (MAJOR.MINOR.PATCH)                       │
└──────────────────────┴──────────────────────────────────────────────────┘

```

### 2.1 Relationship Taxonomy Matrix

| Taxonomy Classification | Name Match? | Version Match? | Content Hash Match? | Origin/Provenance Match? | Semantics / Action Required |
|---|---|---|---|---|---|
| `EXACT_MATCH` | Yes | Yes | Yes | Yes | Identical entity scanned redundantly. Deduplicate safely. |
| `MULTI_ORIGIN_MIRROR` | Yes | Yes | Yes | No | Identical content and name published from different source/repository (Mirror/Fork). Cluster under single logical identity. |
| `CONTENT_CLONE_DIFFERENT_NAME` | No | Any | Yes | Any | Boilerplate copy, template fork, or plagiarized skill with identical bytes but distinct name. |
| `VERSION_EVOLUTION` | Yes | Higher/Lower | No | Yes | Legitimate version release within the same origin lineage. Link in version chain. |
| `CONTENT_DRIFT_SAME_VERSION` | Yes | Yes | No | Yes | Uncommitted mutation / upstream drift under identical version number. Requires alert/investigation. |
| `NAME_COLLISION_DIFFERENT_CONTENT` | Yes | Any | No | No | Unrelated skills competing for the same canonical namespace across distinct sources. |
| `UNIQUE_RESOURCE` | Unique | Unique | Unique | Unique | No collisions across any dimension. |

---

## 3. Structural Gaps & Required Components

1. **JSON Schema**: `schemas/identity-cluster.schema.json` (Draft 2020-12, schema #20).
2. **Transactional Index**: `index/identity-clusters.jsonl`.
3. **Core Deduplication & Resolution Engine** (`tooling/RegistryCore.psm1`):
   - `New-RegistryIdentityClusterId`
   - `Invoke-RegistryIdentityDeduplication`
   - `Get-RegistryIdentityClusters`
   - `Compare-RegistryResourceDivergence`
   - `Resolve-RegistryCanonicalResource`
4. **CLI Domain** (`tooling/skillctl.ps1`):
   - `skillctl identity status`
   - `skillctl identity list`
   - `skillctl identity inspect <id>`
   - `skillctl identity diff <res1> <res2>`
   - `skillctl identity doctor`
5. **Test Suite**: `tests/Invoke-IdentityDeduplicationTests.ps1` with 30 synthetic test scenarios.

---

## 4. Governance & Security Invariants

- **Zero Execution**: Deduplication and clustering are pure metadata and hash comparison operations. Zero payload execution.
- **Quarantine Authority**: Quarantine link (`snapshot_id: 20260812T165347306Z-80e0f888`) takes precedence over all clustering logic. Quarantined or blocked resources cannot be selected as canonical cluster leaders.
- **Trust Level Invariance**: Trust level remains strictly unmodified during identity clustering.
- **ACID Transactions**: All cluster creation and relationship sealing are recorded in `transactions/journal.jsonl` and `audit/events.jsonl`.
