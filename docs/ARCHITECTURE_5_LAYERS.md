# Skill Registry — 5-Layer Deep Architecture Specification

## Architectural Overview

The Skill Registry platform is organized into 5 strictly isolated layers. Each layer operates on formal JSON-Schema contracts and cryptographic anchors.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        LAYER 5 — EXPERIENCE                            │
│    MCP Server (Stdio/SSE)  •  REST API Gateway  •  Sidecar Observer    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────┴────────────────────────────────────┐
│                       LAYER 4 — DISTRIBUTION                           │
│   Distribution Engine  •  Remote OCI Packaging  •  Multi-Reg Federation│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────┴────────────────────────────────────┐
│                        LAYER 3 — RESOLUTION                            │
│     Project Stack Detection  •  Profile Mapping  •  Lockfile (.lock)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────┴────────────────────────────────────┐
│                       LAYER 2 — INTELLIGENCE                           │
│  Structural AST  •  Capability Taxonomy  •  Identity Deduplication     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────┴────────────────────────────────────┐
│                          LAYER 1 — CORE                                │
│    Discovery  •  Content SHA-256  •  Merkle Tree  •  Quarantine Link   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Core Integrity & Sovereign Authority

- **Sovereign Canonical Registry**: `E:\.skill-registry` holds the primary authority.
- **Deterministic Hashing**: Every file has a normalized UTF-8 (no BOM) SHA-256 digest.
- **Merkle Anchoring**: All canonical skills roll up to the sovereign Merkle root anchor (`urn:skill-registry:merkle-tree:v1`).
- **Fail-Closed Quarantine**: Controlled by `governance/quarantine-link.json`.

---

## Layer 2: Intelligence & Capabilities

- **Artifact Classification**: Strict boundary separation (`README ≠ PROMPT ≠ WORKFLOW ≠ AGENT_CONFIG ≠ SKILL`).
- **Identity & Deduplication**: Canonical resolution, alias normalization, and version mapping.
- **Semantic Capabilities**: Extracted capabilities registered against 6 target platforms.

---

## Layer 3: Resolution & Project Lockfiles

- **Stack Detection**: Static inspection of project manifest files (`package.json`, `tsconfig.json`, `requirements.txt`, etc.).
- **Deterministic Capability Solver**: Resolves minimal canonical skill set.
- **Sealed Lockfiles**: Emits `.skill-registry.lock` with bit-for-bit reproducibility.

---

## Layer 4: Distribution, OCI & Federation

- **8 Lifecycle Contracts**: Target inspection $\rightarrow$ Plan $\rightarrow$ Compile $\rightarrow$ Validate $\rightarrow$ Execute $\rightarrow$ Verify $\rightarrow$ Rollback $\rightarrow$ Uninstall.
- **ACID Transactions**: Journaled execution with automatic rollback on collision or verification failure.
- **Remote OCI Packaging**: Compiles verifiable OCI Image Manifests with Ed25519 signatures.
- **Multi-Registry Federation**: Sovereign peer-to-peer exchange with isolated staging inboxes.

---

## Layer 5: Experience & Governed Observation

- **Model Context Protocol (MCP)**: 6 tools (`query_skills`, `inspect_capabilities`, `verify_provenance`, `resolve_project`, `plan_distribution`, `execute_distribution`).
- **REST API Gateway**: High-performance HTTP routes matching the MCP contract.
- **Sidecar Background Observer**: Continuous passive loop (`READ -> ANALYZE -> PROPOSE -> [APPROVAL] -> ENGINES`) with zero autonomous writes.
