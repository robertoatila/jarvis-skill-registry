# Skill Registry — Phase 15: Activation, Safe Deployment & Live Wiring Reconnaissance Report

- **Registry ID**: `reg-e01f28b4-6a89-4b21-9c3f-7e9b04821a11`
- **Recon Date**: `2026-08-31T04:09:00Z`
- **Current State**: `GATE_14_PASSED`
- **Target Gate**: `GATE_15_ACTIVATION_SAFE_DEPLOYMENT`
- **Reconnaissance Mode**: `READ-ONLY (Strict Governance Invariant)`

---

## 1. Live Destination Target Inventory

The read-only scan inventoried all live runtime skill directories across the system:

| Destination ID | Provider | Target Directory | Existing Skills | Type |
| :--- | :--- | :--- | :--- | :--- |
| `dest-gemini-global-v1` | **GEMINI** | `C:\Users\Ad\.gemini\skills` | 165 skills | Physical Dir |
| `dest-gemini-workspace-v1` | **GEMINI** | `E:\.gemini\skills` | 189 skills | Physical Dir |
| `dest-claude-global-v1` | **CLAUDE** | `C:\Users\Ad\.claude\skills` | 165 skills | Physical Dir |
| `dest-codex-global-v1` | **CODEX** | `C:\Users\Ad\.codex\skills` | 166 skills | Physical Dir |
| `dest-agent-global-v1` | **GENERIC_AGENT** | `C:\Users\Ad\.agent\skills` | 165 skills | Physical Dir |
| `dest-agents-global-v1` | **GENERIC_AGENT** | `C:\Users\Ad\.agents\skills` | 165 skills | Physical Dir |

### Baseline State Observations

1. All existing destinations currently store unpacked, unlinked directories.
2. There are currently zero active registry-managed symlinks or directory junctions.
3. Staging area `E:\.skill-registry\staging\materialized` holds 23 materialized skill bundles ready for structured deployment.

---

## 2. Separation of Lifecycle Stages

To prevent security escalations, cross-contamination, and accidental executions, the system strictly separates four distinct lifecycle phases:

```text
[PHASE 13: MATERIALIZATION]
Adapts canonical skill to target provider syntax into staging/materialized/<mat-id>/
          │
          ▼
[PHASE 14: EXECUTION PROFILING]
Binds declarative process limits, network egress policy, filesystem rules, and env var scrubbing
          │
          ▼
[PHASE 15: DEPLOYMENT & STAGING]
Takes pre-deployment backup snapshot, validates pre-mount Merkle hash, stages target artifact
          │
          ▼
[PHASE 15: ACTIVATION & LIVE WIRING]
Commits live link/copy, runs post-mount health probe, validates zero-drift, records active state

```

---

## 3. Deployment Modes & Atomic Execution

Two supported deployment mechanisms ensure safe installation across different environments:

1. **`MODE_ATOMIC_COPY`**:
   - Creates a temporary directory in target staging (`<dest>\.tmp-<deploy-id>`).
   - Copies materialized files and validates SHA-256 Merkle root hash.
   - If target skill exists, moves existing directory to `backups/deployments/<deploy-id>/`.
   - Renames temporary directory to active destination name atomically.
   - Ideal for cross-drive operations (e.g. `E:` -> `C:`).

2. **`MODE_MANAGED_JUNCTION`**:
   - Creates an NTFS Directory Junction or Symlink directly pointing to `staging/materialized/<mat-id>`.
   - Advantage: zero file duplication, instant atomic swap, single source of truth for updates.

---

## 4. Rollback Architecture & Automated Trigger Conditions

Every deployment transaction automatically creates a restorable snapshot in `E:\.skill-registry\backups\deployments/<deploy-id>/`.

### Automatic Rollback Triggers

1. **`POST_MOUNT_PROBE_FAILED`**: Post-mount health check fails (e.g., `SKILL.md` unreadable, missing required frontmatter).
2. **`MERKLE_ROOT_HASH_MISMATCH`**: Deployed files do not match the sealed materialization manifest hash.
3. **`QUARANTINE_VIOLATION_DETECTED`**: Post-mount scan detects a tombstone path or quarantined payload reference.
4. **`STRUCTURAL_CORRUPTION_DETECTED`**: Dangerous file extensions, broken symlinks, or missing entrypoints detected.
5. **`TRANSACTION_ABORTED_OR_LOCKED`**: Concurrency lock contention or uncommitted ACID transaction.
6. **`OPERATOR_MANUAL_ROLLBACK`**: Invocation of `skillctl deploy rollback <deploy_id>`.

---

## 5. Drift Detection Subsystem

The deployment subsystem will continuously monitor live destinations against sealed deployment manifests:

- **`IN_SYNC`**: Live directory SHA-256 Merkle root matches deployment manifest exactly.
- **`DRIFT_MODIFIED`**: One or more live files have been altered outside the Registry.
- **`DRIFT_ADDED`**: Untracked files were placed in the deployed skill folder.
- **`DRIFT_DELETED`**: Required skill files were removed from the deployed directory.
- **`DRIFT_CORRUPTED`**: Target junction is broken or pointing to a non-existent path.

---

## 6. Threat Model & Invariant Enforcements

1. **Quarantine Sovereignty**: Under no condition will a quarantined, blocked, or shadowed skill be deployed (`REFUSED_QUARANTINE`).
2. **Trust Level Immutability**: Deploying a skill to a live environment does NOT elevate its `trust_level` (`UNTRUSTED` remains `UNTRUSTED`).
3. **Zero Dynamic Execution**: Deployment, activation, probing, and rollback execute zero untrusted payload binaries or scripts.
4. **Non-Destructive Backups**: All overwrites or updates are preceded by verifiable, full backup snapshots.
