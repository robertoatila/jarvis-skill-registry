# Skill Registry CLI (`skillctl`) — Operational Reference Manual

**Binary / Script Entrypoint:** `E:\.skill-registry\tooling\skillctl.ps1` (and `skillctl.cmd`)  
**Version:** 1.0.0 (Phase 24 / Gate 24 Edition)  
**Total Functional Domains:** 23  

---

## 1. Syntax & Global Parameters

```powershell
skillctl <domain> <command> [<target>] [-Json] [-DryRun] [-Force]

```

### Global Switches

- `-Json`: Emits pure machine-readable JSON output to stdout. All formatting headers and ANSI colors are suppressed.
- `-DryRun`: Simulates state-mutating commands (e.g. deployments, promotions, compactions) without committing transactions to ledgers.
- `-Force`: Bypasses non-critical safety confirmation prompts (cannot bypass sovereign quarantine or fail-closed invariants).

### Standard Exit Codes

- `0`: Operation completed successfully / Diagnostic state is `HEALTHY`.
- `1`: Operation failed / Diagnostic errors detected / Invariant violation.

---

## 2. Complete Domain Matrix (23 Domains)

| Domain | Available Commands | Mutation Type | Purpose |
| :--- | :--- | :--- | :--- |
| **`registry`** | `status`, `doctor` | READ-ONLY | Global health, configuration, and schema validation |
| **`source`** | `status`, `list`, `inspect <id>`, `validate`, `doctor` | READ-ONLY | Source repository inspection and boundary verification |
| **`discovery`** | `status`, `list`, `inspect <id>`, `validate`, `doctor` | READ-ONLY | Frontmatter extraction and discovered candidate listings |
| **`structure`** | `status`, `list`, `inspect <id>`, `validate`, `doctor` | READ-ONLY | Structural analysis, packaging archetypes, risk levels |
| **`provenance`**| `status`, `list`, `inspect <id>`, `doctor` | READ-ONLY | Origin lineage, commit SHAs, acquisition history |
| **`integrity`** | `status`, `list`, `inspect <id>`, `verify <id>`, `doctor` | READ-ONLY | Merkle tree verification, file hash checks, tamper detection |
| **`identity`**  | `status`, `list`, `inspect <id>`, `diff <res1,res2>`, `doctor` | READ-ONLY | Deduplication clusters, content divergence, canonical leaders |
| **`capability`**| `status`, `list`, `inspect <id>`, `search <tag>`, `doctor` | READ-ONLY | Capability taxonomy search and semantic profile maps |
| **`compatibility`**| `status`, `list`, `inspect <id>`, `matrix`, `doctor` | READ-ONLY | 5-adapter provider compatibility matrix (Gemini, Claude, Codex, OpenAI, Generic) |
| **`security`**  | `status`, `list`, `inspect <id>`, `scan <id>`, `doctor` | READ-ONLY | Static security audit reports and threat classification |
| **`quality`**   | `status`, `list`, `inspect <id>`, `evaluate <id>`, `doctor` | READ-ONLY | 5-dimensional quality, maintainability, and token scores |
| **`conflict`**  | `status`, `list`, `inspect <id>`, `resolve`, `doctor` | READ-ONLY | Namespace clashes, capability competition, shadowing records |
| **`curation`**  | `status`, `list`, `inspect <id>`, `compile <set>`, `doctor` | MUTATOR | Curated set compilation and token budget resolution |
| **`materialize`**| `status`, `list`, `inspect <id>`, `build <set,prov>`, `doctor` | MUTATOR | Intermediate provider adaptation into `staging/` |
| **`profile`**   | `status`, `list`, `inspect <id>`, `apply <id,prof>`, `doctor` | READ-ONLY | Sandboxing profiles and containment policies |
| **`deploy`**    | `status`, `list`, `inspect <id>`, `apply <set>`, `rollback <dep>`, `deactivate <dep>`, `doctor` | MUTATOR | Atomic live mounting, health probing, safe rollback |
| **`update`**    | `status`, `list`, `inspect <id>`, `drift`, `apply <id>`, `rollback <id>`, `doctor` | MUTATOR (STAGING) | Upstream drift detection and staged update management |
| **`schedule`**  | `status`, `list`, `inspect <id>`, `run <id>`, `doctor` | MUTATOR (SCHEDULED) | Periodic background reconciliation and drift verification |
| **`observe`**   | `status`, `telemetry`, `checkpoint`, `snapshot`, `timeline`, `doctor` | READ-ONLY | Subsystem metrics, transaction timeline, Merkle proofs |
| **`admin`**     | `status`, `compact`, `restore <archive>`, `recover`, `chaos`, `doctor` | MUTATOR | Ledger compaction, crash recovery, chaos resilience tests |
| **`export`**    | `status`, `list`, `inspect <id>`, `build <id,target>`, `verify <pkg>`, `doctor` | MUTATOR (BUNDLE) | OCI Image Manifest v1, tarball bundling, Merkle sealing |
| **`status`**    | `status` | READ-ONLY | Unified global registry health overview |
| **`help`**      | `help` | READ-ONLY | Usage help and command reference |

---

## 3. Domain Command Details & Examples

### 3.1 Registry & Status

```powershell

# Global health doctor check

skillctl registry doctor

# Unified status output in JSON

skillctl status -Json

```

### 3.2 Discovery & Structure

```powershell

# List all discovered skills

skillctl discovery list

# Inspect structural analysis of a skill

skillctl structure inspect ai-engineer

```

### 3.3 Integrity & Verification

```powershell

# Verify content integrity and tamper detection

skillctl integrity verify sres-v1-sha256:...

```

### 3.4 Security & Threat Modeling

```powershell

# Inspect static security report

skillctl security inspect ai-engineer -Json

```

### 3.5 Curation, Materialization & Deployment

```powershell

# Compile a curated set

skillctl curation compile default-bundle

# Materialize adapted bundle for Gemini provider

skillctl materialize build default-bundle gemini

# Safely deploy active set with health probes

skillctl deploy apply default-bundle

```

### 3.6 Export & OCI Bundling

```powershell

# Export OCI Image Manifest bundle

skillctl export build default-bundle OCI_ARTIFACT

# Verify exported bundle integrity and quarantine anchor

skillctl export verify E:\.skill-registry\exports\bundle-oci.tar.gz

```
