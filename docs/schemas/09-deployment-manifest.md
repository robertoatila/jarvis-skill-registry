# Schema 09: SkillRegistryDeploymentManifest (deployment-manifest.schema.json)

**Schema Identifier:** `https://skill-registry.local/schemas/deployment-manifest.schema.json`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Schema #27: Formal contract for safe skill deployment, activation, live wiring, rollback snapshots, and drift tracking.

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `string` | `YES` | - |
| `deployment_id` | `string` | `YES` | - |
| `resource_id` | `string` | `YES` | - |
| `canonical_name` | `string` | `NO` | - |
| `materialization_id` | `string` | `YES` | - |
| `execution_profile_id` | `string` | `YES` | - |
| `target_provider` | `string` | `YES` | - |
| `destination_path` | `string` | `YES` | - |
| `deployment_mode` | `string` | `YES` | - |
| `pre_deploy_backup_path` | `string null` | `NO` | - |
| `deployed_content_hash` | `string` | `YES` | - |
| `probe_status` | `string` | `YES` | - |
| `lifecycle_state` | `string` | `YES` | - |
| `trust_level` | `string` | `YES` | - |
| `deployed_files` | `array` | `NO` | - |
| `deployed_utc` | `string` | `YES` | - |
| `activated_utc` | `string null` | `NO` | - |
| `deactivated_utc` | `string null` | `NO` | - |
| `rolled_back_utc` | `string null` | `NO` | - |
| `audit_transaction_id` | `string` | `YES` | - |

## 3. Required Properties

- `schema_version`
- `deployment_id`
- `resource_id`
- `materialization_id`
- `execution_profile_id`
- `target_provider`
- `destination_path`
- `deployment_mode`
- `lifecycle_state`
- `deployed_content_hash`
- `probe_status`
- `trust_level`
- `deployed_utc`
- `audit_transaction_id`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
