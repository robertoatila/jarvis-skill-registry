# Skill Registry — Repository Structure & Layout Specification

**Version:** 1.0.0 (Phase 24 Edition)

---

## 1. Directory Tree & Functional Subsystems

```text
E:\.skill-registry\
├── adapters/               # Target AI Provider Adapters
│   ├── chatgpt/            # ChatGPT / OpenAI Apps SDK Adapter
│   ├── claude/             # Anthropic Claude Adapter
│   ├── codex/              # OpenAI Codex / Tool Calling Adapter
│   ├── gemini/             # Google Gemini / Antigravity Adapter
│   └── generic/            # Generic Agent Runtime Adapter
│
├── archives/               # Compacted Historical Ledger Archives (.tar.gz)
├── audit/                  # Immutable Audit Logs (audit-events.jsonl)
├── backups/                # Periodic System State Backups
├── cache/                  # Ephemeral Index & Hashing Cache
├── config/                 # Registry Configuration & Policies
│   ├── policy.json         # General Registry Governance Policy
│   └── registry.json       # Registry Identification & Root Paths
│
├── docs/                   # Complete Architectural Documentation
│   ├── adr/                # Architecture Decision Records (ADRs 001–026)
│   ├── examples/           # Sanitized Synthetic Reference Examples
│   ├── schemas/            # 33 JSON Schema Specifications
│   ├── ARCHITECTURE.md     # 30-Chapter Architecture Handbook
│   ├── CLI.md              # Complete CLI Operational Reference
│   ├── EXTENDING.md        # Provider & Adapter Extension Guide
│   ├── GOVERNANCE.md       # Governance Lifecycle & Gates Manual
│   ├── OPEN_SOURCE_BOUNDARY.md # Data Classification & Privacy Policy
│   ├── OPERATIONS.md       # Operational Runbook & Day-2 Guide
│   ├── RECOVERY.md         # Crash Recovery & Restore Playbook
│   ├── REPOSITORY-STRUCTURE.md # This layout specification
│   ├── SCHEMA-CATALOG.md   # Schema Master Index Catalog
│   └── SECURITY.md         # Threat Model & Security Guarantees
│
├── exports/                # Exported OCI Image Manifests & Bundles
├── governance/             # Sovereign Governance Anchors
│   ├── quarantine-link.json# 118 Tombstones & 8 Blocked Subtrees
│   └── trust-policy.json   # Trust Tier Definitions & Isolation Rules
│
├── index/                  # 24 Append-Only ACID JSONL Ledgers
├── profiles/               # 4 Standardized Runtime Execution Profiles
│   ├── network-restricted.json
│   ├── offline-developer.json
│   ├── provider-native.json
│   └── strict-sandbox.json
│
├── reports/                # Historical Phase & Gate Certification Reports
├── schemas/                # 33 JSON Schema Draft 2020-12 Schema Files
├── staging/                # Intermediate Staged Provider Materializations
├── state/                  # Runtime Ephemeral State & Locks
│   ├── current-state.json  # Current Canonical Registry State
│   └── locks/              # Active Process Locking Directory
│
├── tests/                  # Automated Test Suites (Phases 0–24)
├── tooling/                # Production Registry Core Modules
│   ├── RegistryCore.psm1   # Authoritative Registry Core Engine
│   └── skillctl.ps1        # Unified CLI Front-End Implementation
│
├── transactions/           # Transaction Journal & Recovery Snapshots
│   └── journal.jsonl       # Append-Only ACID Transaction Journal
│
└── CONTRIBUTING.md         # Contributor & Development Guidelines

```
