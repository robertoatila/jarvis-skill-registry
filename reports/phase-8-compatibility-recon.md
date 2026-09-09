# Phase 8 Reconnaissance: Provider Compatibility Matrix & Adaptation Layer

**Skill Registry Lifecycle Platform**  
**Date**: 2026-08-31  
**Phase**: Phase 8 — Compatibility  
**Status**: `READ_ONLY_RECONNAISSANCE_COMPLETE`

---

## 1. Context & Baseline Assessment

With Phases 0–7 sealed (`GATE_7=PASS`), the registry has established:

- Foundation, sources, and boundary containment (Phases 1–2).
- Metadata-first discovery and structural analysis (Phases 3–4).
- Cryptographic provenance and Merkle content integrity sealing (Phase 5).
- Multi-dimensional identity clustering and canonical leader resolution (Phase 6).
- Standardized capability taxonomy, normalization, and capability profiles (Phase 7).

Phase 8 now establishes the **Provider Compatibility Matrix & Adaptation Subsystem**, mapping candidate skills across leading AI agent runtimes and calculating adaptation requirements without executing any payloads.

---

## 2. Compatibility Architecture Model

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                    COMPATIBILITY EVALUATION ENGINE                      │
├─────────────────────────────────────────────────────────────────────────┤
│ Input: Discovered Resource + Structural Analysis + Capability Profile   │
│                                                                         │
│ Target Providers Evaluated:                                             │
│   1. GEMINI        (Native SKILL.md / System Instructions / JSON Spec)  │
│   2. CLAUDE        (CLAUDE.md / Tool Prompts / Subagents)               │
│   3. CODEX         (Codex CLI / Python Execution / Ast Transforms)      │
│   4. OPENAI        (ChatGPT Apps / OpenAPI Specs / Assistants)          │
│   5. GENERIC_AGENT (MCP Servers / Standard CLI / Bash Tools)            │
│                                                                         │
│ Rating Levels:                                                          │
│   - NATIVE       : Direct execution without format changes              │
│   - ADAPTABLE    : Functional via registered transformation adapter     │
│   - PARTIAL      : Degraded or subset capability supported              │
│   - INCOMPATIBLE : Prohibited formats, dangerous binaries, or unsupported│
│   - UNKNOWN      : Insufficient metadata to determine compatibility     │
└─────────────────────────────────────────────────────────────────────────┘

```

---

## 3. Structural Gaps & Required Components

1. **Schemas**:
   - `schemas/compatibility.schema.json` (Existing Draft 2020-12).
   - `schemas/provider.schema.json` (Existing Draft 2020-12).
   - `schemas/adapter.schema.json` (Existing Draft 2020-12).
2. **Indices**:
   - `index/compatibility.jsonl` (Transactional compatibility matrix index).
3. **Core Engine Functions** (`tooling/RegistryCore.psm1`):
   - `Invoke-RegistryCompatibilityEvaluation`
   - `Get-RegistryCompatibilityMatrix`
   - `Test-RegistryProviderCompatibility`
   - `Resolve-RegistryAdaptiveTransformation`
4. **CLI Domain** (`tooling/skillctl.ps1`):
   - `skillctl compatibility status`
   - `skillctl compatibility list`
   - `skillctl compatibility inspect <id>`
   - `skillctl compatibility matrix`
   - `skillctl compatibility doctor`
5. **Test Suite**: `tests/Invoke-CompatibilityTests.ps1` with 30 synthetic test scenarios.

---

## 4. Governance & Security Invariants

- **Zero Execution**: Compatibility evaluation is purely static and deterministic based on metadata and structural evidence. No payloads or adapters are executed.
- **Quarantine Authority**: Quarantined/blocked skills are marked `INCOMPATIBLE` across all providers.
- **Trust Level Invariance**: `trust_level` remains unmodified throughout compatibility analysis.
- **ACID Transactions**: All matrix evaluations committed via `Invoke-RegistryTransaction` (`COMPATIBILITY_MATRIX_SEAL`).
