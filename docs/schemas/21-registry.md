# Schema 21: Skill Registry Configuration Schema (registry.schema.json)

**Schema Identifier:** `urn:skill-registry:registry:1.0.0`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Schema for the canonical Skill Registry configuration metadata.

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `object` | `YES` | - |
| `registry_id` | `string` | `YES` | - |
| `registry_name` | `string` | `YES` | - |
| `created_utc` | `object` | `YES` | - |
| `mode` | `string` | `YES` | - |
| `version` | `string` | `YES` | - |
| `paths` | `object` | `YES` | - |
| `security_anchors` | `object` | `YES` | - |

## 3. Required Properties

- `schema_version`
- `registry_id`
- `registry_name`
- `created_utc`
- `mode`
- `version`
- `paths`
- `security_anchors`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
