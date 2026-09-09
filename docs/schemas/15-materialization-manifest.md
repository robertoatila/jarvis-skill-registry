# Schema 15: MaterializationManifest (materialization-manifest.schema.json)

**Schema Identifier:** `https://skill-registry.local/schemas/materialization-manifest.schema.json`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Schema definition for intermediate materialized skill artifacts and adaptation lineage in Skill Registry

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `string` | `YES` | - |
| `materialization_id` | `string` | `YES` | - |
| `source_resource_id` | `string` | `YES` | - |
| `target_provider` | `string` | `YES` | - |
| `adapter_id` | `string` | `YES` | - |
| `adapter_version` | `string` | `YES` | - |
| `source_content_hash` | `string` | `YES` | - |
| `materialized_content_hash` | `string` | `YES` | - |
| `materialized_files` | `array` | `YES` | - |
| `transformation_mode` | `string` | `YES` | - |
| `transformation_parameters` | `object` | `NO` | - |
| `created_utc` | `string` | `YES` | - |
| `trust_level` | `string` | `YES` | - |
| `staging_path` | `string` | `YES` | - |
| `audit_transaction_id` | `string null` | `NO` | - |

## 3. Required Properties

- `schema_version`
- `materialization_id`
- `source_resource_id`
- `target_provider`
- `adapter_id`
- `adapter_version`
- `source_content_hash`
- `materialized_content_hash`
- `materialized_files`
- `transformation_mode`
- `created_utc`
- `trust_level`
- `staging_path`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
