# Schema 23: Skill Registry Resource Schema (resource.schema.json)

**Schema Identifier:** `urn:skill-registry:resource:1.0.0`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Canonical schema for a skill resource representation decoupled from physical payload.

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `object` | `YES` | - |
| `resource_id` | `string` | `YES` | - |
| `canonical_name` | `string` | `YES` | - |
| `version` | `string` | `YES` | - |
| `display_name` | `string` | `YES` | - |
| `description` | `string` | `YES` | - |
| `provenance_id` | `string` | `YES` | - |
| `lifecycle_state` | `string` | `YES` | - |
| `trust_level` | `string` | `YES` | - |
| `capabilities` | `array` | `YES` | - |
| `content_identity` | `object` | `YES` | - |
| `created_utc` | `object` | `YES` | - |
| `updated_utc` | `object` | `YES` | - |

## 3. Required Properties

- `schema_version`
- `resource_id`
- `canonical_name`
- `version`
- `display_name`
- `description`
- `provenance_id`
- `lifecycle_state`
- `trust_level`
- `capabilities`
- `content_identity`
- `created_utc`
- `updated_utc`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
