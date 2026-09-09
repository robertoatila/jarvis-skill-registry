# Phase 28 — Project Profiles & Deterministic Lockfiles Report

**Skill Registry Lifecycle Platform — Layer 3 Resolution**  
**Phase**: Phase 28 — Project Profiles + Lockfiles  
**Gate**: `GATE_28_RESOLUTION_OPERATIONAL`  
**Timestamp (UTC)**: 2026-09-01T17:15:00Z  
**Status**: `PASS (17/17 Test Scenarios — 100%)`  
**Governance Invariant**: `GATES 0–24 & 25–27 SEALED & IMMUTABLE`  
**Mode**: `PURE DECISION-MAKING & CRYPTOGRAPHIC RESOLUTION` (Zero Auto-Distribution)

---

## 1. Executive Summary

Phase 28 establishes the **Layer 3 (Resolution)** subsystem for the Skill Registry platform. It provides automated, heuristic and AST-based stack detection, semantic project profiling, capability resolution against unquarantined canonical skills, and bit-for-bit reproducible lockfile generation (`.skill-registry.lock`).

### Inviolable Safety Directives Enforced

1. **Resolution $\neq$ Auto-Distribution**: Detecting that a project uses Next.js or Python *never* triggers automatic installation or distribution. Detection and resolution are strictly pure, read-only decision-making phases:
   $$\text{Detect} \longrightarrow \text{Profile} \longrightarrow \text{Resolve} \longrightarrow \text{PLAN Preview} \longrightarrow \text{User Approval} \longrightarrow \text{Layer 4 Distribution Engine}$$
2. **Deterministic Cryptographic Reproducibility**: Given the identical tuple:
   $$(\text{Project Profile Hash},\ \text{Registry Merkle Anchor},\ \text{Resolver Version})$$
   the resolver guarantees a bit-for-bit identical resolution Merkle root and `.skill-registry.lock`.
3. **Fail-Closed Sovereign Quarantine**: Any skill flagged under `QUARANTINED` or `BLOCKED` in `governance/quarantine-link.json` or `index/resources.jsonl` is strictly excluded from candidate sets during capability matching.
4. **Multi-Target Constraints (6 Platforms)**: Project profiles and lockfiles bind target platform constraints across all 6 supported runtimes (`gemini`, `codex`, `claude`, `chatgpt`, `cursor`, `generic`).

---

## 2. Layer 3 Resolution Architecture

```text
                 PROJECT WORKSPACE
                        │
                        ▼
                Detect-ProjectStack
              (skillctl detect <path>)
                        │
           ┌────────────┼────────────┐
           ▼            ▼            ▼
       Languages    Frameworks    Tooling
                        │
                        ▼
               Get-ProjectProfile
             (skillctl profile <path>)
                        │
           ┌────────────┴────────────┐
           ▼                         ▼
      REQUIRED                   OPTIONAL
     Capabilities               Capabilities
           │                         │
           └────────────┬────────────┘
                        ▼
               Resolve-Capabilities
             (skillctl resolve <path>)
                        │
                        ▼
             Cross-Target Compatibility
                        │
                        ▼
              New-SkillRegistryLock
              (skillctl lock <path>)
                        │
                        ▼
              .skill-registry.lock
```

---

## 3. Schemas & Code Artifacts Delivered

- [project-detection.schema.json](file:///E:/.skill-registry/schemas/project-detection.schema.json) & [project-detection.json](file:///E:/.skill-registry/schemas/project-detection.json)
- [project-profile.schema.json](file:///E:/.skill-registry/schemas/project-profile.schema.json) & [project-profile.json](file:///E:/.skill-registry/schemas/project-profile.json)
- [capability-resolution.schema.json](file:///E:/.skill-registry/schemas/capability-resolution.schema.json) & [capability-resolution.json](file:///E:/.skill-registry/schemas/capability-resolution.json)
- [skill-registry-lock.schema.json](file:///E:/.skill-registry/schemas/skill-registry-lock.schema.json) & [skill-registry-lock.json](file:///E:/.skill-registry/schemas/skill-registry-lock.json)
- [compatibility-resolution.schema.json](file:///E:/.skill-registry/schemas/compatibility-resolution.schema.json) & [compatibility-resolution.json](file:///E:/.skill-registry/schemas/compatibility-resolution.json)
- [ResolutionEngine.psm1](file:///E:/.skill-registry/tooling/ResolutionEngine.psm1) *(Layer 3 Resolution Module)*
- [Invoke-ResolutionEngineTests.ps1](file:///E:/.skill-registry/tests/Invoke-ResolutionEngineTests.ps1) *(Phase 28 Test Harness)*
- [phase-28-project-profiles-lockfiles.json](file:///E:/.skill-registry/reports/phase-28-project-profiles-lockfiles.json)
- [phase-28-project-profiles-lockfiles.md](file:///E:/.skill-registry/reports/phase-28-project-profiles-lockfiles.md)

---

## 4. Test Suite Verification (17 / 17 PASS)

```text
============================================================
 RUNNING PHASE 28 TEST SUITE: RESOLUTION ENGINE & LOCKFILES 
============================================================
  [PASS] Test 01 : project-detection.schema.json exists and is valid JSON
  [PASS] Test 02 : project-detection.json defines detection structure
  [PASS] Test 03 : project-profile.schema.json exists and is valid JSON
  [PASS] Test 04 : project-profile.json defines profile structure and targets
  [PASS] Test 05 : capability-resolution.schema.json exists and is valid JSON
  [PASS] Test 06 : capability-resolution.json defines matched skills and Merkle root
  [PASS] Test 07 : skill-registry-lock.schema.json exists and is valid JSON
  [PASS] Test 08 : skill-registry-lock.json defines deterministic lockfile structure
  [PASS] Test 09 : compatibility-resolution.schema.json exists and is valid JSON
  [PASS] Test 10 : compatibility-resolution.json defines cross-target matrix verdict
  [PASS] Test 11 : Detect-ProjectStack accurately inspects workspace manifests
  [PASS] Test 12 : Get-ProjectProfile maps detected stack to capabilities profile
  [PASS] Test 13 : Resolve-Capabilities produces deterministic skill resolution
  [PASS] Test 14 : New-SkillRegistryLock writes valid .skill-registry.lock
  [PASS] Test 15 : Resolution Engine performs pure decision-making with zero distribution
  [PASS] Test 16 : Repeated capability resolution yields bit-for-bit identical Merkle root
  [PASS] Test 17 : Core Gates 0-24 immutability check verified
============================================================
 TEST RESULTS SUMMARY: 17 / 17 PASSED (0 FAILED)
============================================================
```

---

## 5. Governance Stop & Next Steps

```text
================================================================================
GOVERNANCE STATUS: PHASE 28 (PROJECT PROFILES + LOCKFILES) COMPLETE & OPERATIONAL
GATE 28 STATUS: PASS (17/17 TESTS — 100%)
CORE BASELINE: GATES 0–24 & 25–27 SEALED & IMMUTABLE
NEXT AUTHORIZED STAGE: GOVERNANCE REVIEW -> PHASE 29 (REMOTE OCI DISTRIBUTION)
================================================================================
```

Execution halted at Governance Stop. Ready for user review and authorization to proceed to **Phase 29 — Remote OCI Distribution** (Layer 4: OCI image artifact packaging, digest generation, cryptographic signing, and publishing/pulling to registries like GHCR or private registries).
