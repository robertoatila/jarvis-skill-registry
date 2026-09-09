# Schema 08: CuratedSkillSetManifest (curated-set.schema.json)

**Schema Identifier:** `https://skill-registry.local/schemas/curated-set.schema.json`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Schema definition for curated skill bundles and canonical active sets in Skill Registry

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `string` | `YES` | - |
| `set_id` | `string` | `YES` | - |
| `profile_name` | `string` | `YES` | - |
| `target_provider` | `string` | `YES` | - |
| `compiled_utc` | `string` | `YES` | - |
| `total_skills` | `integer` | `YES` | - |
| `selected_resources` | `array` | `YES` | - |
| `selection_criteria` | `object` | `YES` | - |
| `bundle_merkle_root` | `string` | `YES` | - |
| `audit_transaction_id` | `string null` | `NO` | - |

## 3. Required Properties

- `schema_version`
- `set_id`
- `profile_name`
- `target_provider`
- `compiled_utc`
- `total_skills`
- `selected_resources`
- `selection_criteria`
- `bundle_merkle_root`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
