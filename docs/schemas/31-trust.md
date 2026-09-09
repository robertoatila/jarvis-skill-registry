# Schema 31: Skill Registry Trust Model Schema (trust.schema.json)

**Schema Identifier:** `urn:skill-registry:trust:1.0.0`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Trust level assignment, evaluation criteria, and security classification.

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `object` | `YES` | - |
| `resource_id` | `string` | `YES` | - |
| `trust_level` | `string` | `YES` | - |
| `evaluated_utc` | `object` | `YES` | - |
| `security_review` | `object` | `YES` | - |
| `permissions` | `object` | `YES` | - |

## 3. Required Properties

- `schema_version`
- `resource_id`
- `trust_level`
- `evaluated_utc`
- `security_review`
- `permissions`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
