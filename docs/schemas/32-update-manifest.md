# Schema 32: Skill Registry Update Manifest Schema (update-manifest.schema.json)

**Schema Identifier:** `urn:skill-registry:update-manifest:1.0.0`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Schema for upstream drift detection, semantic change classification, safe staging, and atomic update manifests.

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `object` | `YES` | - |
| `update_id` | `string` | `YES` | - |
| `resource_id` | `string` | `YES` | - |
| `canonical_name` | `string` | `YES` | - |
| `source_id` | `string` | `YES` | - |
| `upstream_locator` | `string` | `YES` | - |
| `commit_before` | `string null` | `YES` | - |
| `commit_after` | `string null` | `YES` | - |
| `detected_drift_type` | `string` | `YES` | - |
| `semantic_classification` | `string` | `YES` | - |
| `security_verdict` | `string` | `YES` | - |
| `quarantine_status` | `string` | `YES` | - |
| `lifecycle_state` | `string` | `YES` | - |
| `dry_run` | `boolean` | `YES` | - |
| `pre_update_backup_path` | `string null` | `NO` | - |
| `staging_path` | `string null` | `NO` | - |
| `previous_content_hash` | `object` | `NO` | - |
| `updated_content_hash` | `object` | `NO` | - |
| `diff_summary` | `object` | `NO` | - |
| `evaluated_utc` | `object` | `YES` | - |
| `staged_utc` | `string null` | `NO` | - |
| `applied_utc` | `string null` | `NO` | - |
| `rolled_back_utc` | `string null` | `NO` | - |
| `audit_transaction_id` | `string null` | `NO` | - |

## 3. Required Properties

- `schema_version`
- `update_id`
- `resource_id`
- `canonical_name`
- `source_id`
- `upstream_locator`
- `commit_before`
- `commit_after`
- `detected_drift_type`
- `semantic_classification`
- `security_verdict`
- `quarantine_status`
- `lifecycle_state`
- `dry_run`
- `evaluated_utc`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
