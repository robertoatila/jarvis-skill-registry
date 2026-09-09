# Schema 25: SkillRegistrySource (source.schema.json)

**Schema Identifier:** `urn:skill-registry:source:1.0.0`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Canonical definition of a declared or registered resource source in Skill Registry.

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `string` | `YES` | - |
| `source_id` | `string` | `YES` | - |
| `source_type` | `string` | `YES` | - |
| `source_locator` | `string` | `YES` | - |
| `normalized_locator_key` | `string` | `NO` | - |
| `display_name` | `string` | `YES` | - |
| `namespace` | `string` | `YES` | - |
| `associated_provider_id` | `string null` | `NO` | - |
| `policy_id` | `string` | `YES` | - |
| `trust_level` | `string` | `YES` | - |
| `lifecycle_state` | `string` | `YES` | - |
| `boundaries` | `object` | `YES` | - |
| `registered_utc` | `string` | `YES` | - |
| `updated_utc` | `string` | `YES` | - |

## 3. Required Properties

- `schema_version`
- `source_id`
- `source_type`
- `source_locator`
- `display_name`
- `namespace`
- `policy_id`
- `trust_level`
- `lifecycle_state`
- `boundaries`
- `registered_utc`
- `updated_utc`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
