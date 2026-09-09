# Skill Registry — Operations & Maintenance Playbook

**Version:** 1.0.0 (Phase 24 Edition)

---

## 1. System Requirements & Installation

### Environment

- **Operating System:** Windows 10/11 or Windows Server (PowerShell 5.1+ / PowerShell Core 7+).
- **Disk Requirements:** Standard NTFS filesystem supporting append-only file operations.
- **Dependencies:** Pure PowerShell — zero external binary or cloud service dependencies.

### Verification on Installation

```powershell

# Verify Registry Core and Schema Integrity

skillctl registry doctor

```

Expected Output:

```text
=== SKILL REGISTRY DOCTOR ===
Configuration Check   : PASS
Quarantine Guard Link : PASS
Schema System Check   : PASS (33 schemas)
Lock / Journal Health : PASS
Overall Diagnosis     : HEALTHY

```

---

## 2. Day-2 Operational Runbook

### 2.1 Registering New Source Repositories

```powershell

# Register a local source folder as UNTRUSTED

Import-Module E:\.skill-registry\tooling\RegistryCore.psm1
Register-RegistrySource -SourceType 'LOCAL_DIRECTORY' -OriginUri 'C:\path\to\skills' -TrustLevel 'UNTRUSTED'

```

### 2.2 Triggering Discovery & Analysis

```powershell

# Ingest and analyze all registered sources

Invoke-RegistryDiscovery
Invoke-RegistryRealArsenalIngestion

```

### 2.3 Compacting Historical Ledgers

```powershell

# Compact historical records according to retention policy

skillctl admin compact

```
