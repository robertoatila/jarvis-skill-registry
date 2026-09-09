# Skill Registry — Crash Recovery & Disaster Restore Playbook

**Version:** 1.0.0 (Phase 24 Edition)

---

## 1. Crash Recovery Architecture

The registry guarantees recovery from sudden process termination, kernel crashes, or power loss via:

1. **Journal Replay (`transactions/journal.jsonl`)**: Incomplete transactions marked as `STARTED` without a corresponding `COMMITTED` entry are detected on startup.
2. **Lock Expiration & Cleanup (`state/locks/`)**: Orphaned locks held by dead process IDs are automatically evicted.
3. **Atomic Ledger Truncation**: Corrupted partial tail lines in JSONL ledgers are rolled back to the last known committed transaction offset.

---

## 2. Automated Recovery Procedures

### 2.1 Quick Automated Health Recovery

```powershell

# Perform automated crash recovery

skillctl admin recover

```

### 2.2 Deep Disaster Recovery Checkpoint

```powershell

# In PowerShell session

Import-Module E:\.skill-registry\tooling\RegistryCore.psm1
$recoveryResult = Invoke-RegistryCrashRecovery
if ($recoveryResult.status -in @('HEALTHY', 'RECONCILED')) {
    Write-Host "Registry successfully recovered and consistent." -ForegroundColor Green
}

```

---

## 3. Restoring from Sealed Archives

To restore an index ledger from an archived historical snapshot:

```powershell

# Restore archive by ID

skillctl admin restore arch-20260831T...

```
