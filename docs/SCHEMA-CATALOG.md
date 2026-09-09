# Skill Registry — Schema Catalog & Specifications

**Specification Version:** 1.0.0  
**JSON Schema Standard:** Draft 2020-12  
**Total Active Schemas:** 33  
**Registry Root:** `E:\.skill-registry\schemas\`

---

## 1. Complete Catalog Index

| Schema # | Schema File | Index Type / Entity | Primary Purpose | Producer Subsystem |
| :--- | :--- | :--- | :--- | :--- |
| **01** | `registry.schema.json` | `REGISTRY_CONFIG` | Global registry configuration, storage paths, and health status | System Core |
| **02** | `source.schema.json` | `SOURCES` | Source location registration, boundaries, and policies | Source Engine |
| **03** | `source-policy.schema.json` | `SOURCE_POLICY` | Source filtering, inclusion, and exclusion rule policies | Source Engine |
| **04** | `source-state.schema.json` | `SOURCE_STATE` | Operational state and synchronization status of sources | Source Engine |
| **05** | `source-provenance.schema.json` | `SOURCE_PROVENANCE` | Repository lineage and acquisition metadata for sources | Source Engine |
| **06** | `discovery-session.schema.json` | `DISCOVERIES` | Discovery session metrics, candidate counts, and runtimes | Discovery Engine |
| **07** | `resource.schema.json` | `RESOURCES` | Canonical catalog of discovered skill definitions | Discovery Engine |
| **08** | `structural-analysis.schema.json` | `STRUCTURAL_ANALYSES` | File layouts, packaging types, entrypoints, and risk levels | Structural Engine |
| **09** | `provenance.schema.json` | `PROVENANCE` | Immutable origin lineage, commit SHAs, and integrity chains | Provenance Engine |
| **10** | `integrity-manifest.schema.json` | `INTEGRITY_MANIFESTS` | Cryptographic Merkle trees of skill file SHA-256 hashes | Integrity Engine |
| **11** | `identity-cluster.schema.json` | `IDENTITY_CLUSTERS` | Deduplication clusters, content divergence, canonical leaders | Identity Engine |
| **12** | `capability.schema.json` | `CAPABILITIES` | Canonical capability taxonomy definitions and synonym maps | Capability Engine |
| **13** | `capability-profile.schema.json` | `CAPABILITY_PROFILES` | Declared and inferred semantic capability maps for skills | Capability Engine |
| **14** | `provider.schema.json` | `PROVIDERS` | AI provider target runtime configurations and features | Compatibility Engine |
| **15** | `compatibility.schema.json` | `COMPATIBILITY_MATRICES` | Multi-adapter provider compatibility scores and matrices | Compatibility Engine |
| **16** | `adapter.schema.json` | `ADAPTER_CONFIG` | Adapter translation specifications for target runtimes | Adaptation Engine |
| **17** | `security-report.schema.json` | `SECURITY_REPORTS` | Static AST / regex security audits and threat findings | Security Engine |
| **18** | `quality-assessment.schema.json` | `QUALITY_EVALUATIONS` | 5-dimensional quality, maintainability, and token scores | Quality Engine |
| **19** | `conflict.schema.json` | `CONFLICTS` | Namespace collisions, capability clashes, and shadowing records | Conflict Engine |
| **20** | `curated-set.schema.json` | `CURATED_SETS` | Declarative skill bundles, selectors, and token budgets | Curation Engine |
| **21** | `materialization-manifest.schema.json` | `MATERIALIZATIONS` | Staged provider adaptation manifests and output hashes | Materialization Engine |
| **22** | `execution-profile.schema.json` | `EXECUTION_PROFILES` | Sandboxing contracts, network rules, and resource limits | Profile Engine |
| **23** | `deployment-manifest.schema.json` | `DEPLOYMENTS` | Active and retired workspace mounts and health probes | Deployment Engine |
| **24** | `update-manifest.schema.json` | `UPDATES` | Detected upstream content and metadata drift records | Update Engine |
| **25** | `update-orchestration.schema.json` | `UPDATE_QUEUES` | Sequenced update batches awaiting supervisor promotion | Orchestration Engine |
| **26** | `reconciliation-schedule.schema.json` | `SCHEDULES` | Background reconciliation cron schedules and drift rules | Reconciliation Engine |
| **27** | `operational-observability.schema.json` | `OBSERVABILITY_SNAPSHOTS` | Subsystem telemetry, performance, and Merkle checkpoints | Observability Engine |
| **28** | `compaction-retention.schema.json` | `ARCHIVES` | Compaction rules, retention policies, and archive records | Compaction Engine |
| **29** | `transaction.schema.json` | `TRANSACTIONS` | Atomic ACID journal entries and rollback snapshots | Transaction Engine |
| **30** | `audit.schema.json` | `AUDIT_EVENTS` | Immutable audit trail events and operator actions | Audit Engine |
| **31** | `trust.schema.json` | `TRUST_POLICIES` | Trust tier definitions, boundaries, and validation policies | Governance Engine |
| **32** | `lifecycle.schema.json` | `LIFECYCLE_STATES` | State transition models for skills and deployments | Lifecycle Engine |
| **33** | `registry-export-bundle.schema.json` | `EXPORTS` | OCI Image Manifest v1, tarball bundles, and Merkle sealing | Export Engine |

---

## 2. Invariant Rules Across All Schemas

1. **`$schema` Declarator**: Every schema targets `"https://json-schema.org/draft/2020-12/schema"`.
2. **`additionalProperties: false`**: Enforced on all top-level objects to reject undocumented properties.
3. **`schema_version`**: Standard semantic version string (`"1.0.0"`).
4. **Timestamps**: All timestamps strictly adhere to ISO 8601 UTC format with trailing `Z` or UTC offset.
5. **Identifiers**: Resource IDs follow standardized prefixes (`sres-v1-sha256:...`, `prov-v1-sha256:...`, `iman-...`, `cpro-...`, `tx-...`, `dep-...`).
