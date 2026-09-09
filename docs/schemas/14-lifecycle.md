# Schema 14: Skill Registry Lifecycle Schema (lifecycle.schema.json)

**Schema Identifier:** `urn:skill-registry:lifecycle:1.0.0`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Lifecycle state machine definition and transition rules with strict quarantine precedence.

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `object` | `YES` | - |
| `resource_id` | `string` | `YES` | - |
| `current_state` | `string` | `YES` | - |
| `history` | `array` | `YES` | - |
| `last_transition_utc` | `object` | `YES` | - |

## 3. Required Properties

- `schema_version`
- `resource_id`
- `current_state`
- `history`
- `last_transition_utc`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
