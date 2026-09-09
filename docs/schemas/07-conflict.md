# Schema 07: Skill Registry Conflict Matrix Schema (conflict.schema.json)

**Schema Identifier:** `https://skill-registry.local/schemas/conflict.schema.json`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Definition of mutual incompatibility, contradictory instructions, and precedence rules.

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `string` | `YES` | - |
| `conflict_id` | `string` | `YES` | - |
| `resource_a_id` | `string` | `YES` | - |
| `resource_b_id` | `string` | `YES` | - |
| `conflict_type` | `string` | `YES` | - |
| `severity` | `string` | `YES` | - |
| `reason` | `string` | `YES` | - |
| `resolution_rule` | `string` | `YES` | - |
| `preferred_resource_id` | `string null` | `YES` | - |
| `shadowed_resource_id` | `string null` | `YES` | - |
| `detected_utc` | `string` | `YES` | - |
| `audit_transaction_id` | `string null` | `NO` | - |

## 3. Required Properties

- `schema_version`
- `conflict_id`
- `resource_a_id`
- `resource_b_id`
- `conflict_type`
- `severity`
- `reason`
- `resolution_rule`
- `preferred_resource_id`
- `shadowed_resource_id`
- `detected_utc`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
