# Schema 06: Skill Registry Provider Compatibility Matrix Schema (compatibility.schema.json)

**Schema Identifier:** `urn:skill-registry:compatibility:1.0.0`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Multidimensional compatibility mapping per provider and skill resource.

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `object` | `YES` | - |
| `resource_id` | `string` | `YES` | - |
| `evaluated_utc` | `object` | `YES` | - |
| `ratings` | `object` | `YES` | - |

## 3. Required Properties

- `schema_version`
- `resource_id`
- `evaluated_utc`
- `ratings`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
