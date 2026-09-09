# Schema 05: CompactionRetentionManifest (compaction-retention.schema.json)

**Schema Identifier:** `https://skill-registry.local/schemas/compaction-retention.schema.json`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Schema for skill registry ledger compaction, audit archive retention, and restore manifests.

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `string` | `YES` | - |
| `archive_id` | `string` | `YES` | - |
| `archive_type` | `string` | `YES` | - |
| `created_utc` | `string` | `YES` | - |
| `source_ledger` | `string` | `YES` | - |
| `archive_file_path` | `string` | `YES` | - |
| `archive_sha256_hash` | `string` | `YES` | - |
| `records_archived_count` | `integer` | `YES` | - |
| `pre_compaction_records_count` | `integer` | `YES` | - |
| `post_compaction_records_count` | `integer` | `YES` | - |
| `archive_merkle_root` | `string` | `YES` | - |
| `initiator` | `string` | `YES` | - |
| `governance_lock` | `object` | `YES` | - |

## 3. Required Properties

- `schema_version`
- `archive_id`
- `archive_type`
- `created_utc`
- `source_ledger`
- `archive_file_path`
- `archive_sha256_hash`
- `records_archived_count`
- `pre_compaction_records_count`
- `post_compaction_records_count`
- `archive_merkle_root`
- `initiator`
- `governance_lock`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
