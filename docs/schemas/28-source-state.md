# Schema 28: SkillRegistrySourceState (source-state.schema.json)

**Schema Identifier:** `urn:skill-registry:source-state:1.0.0`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Lifecycle state history and snapshot for a registered Source.

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `string` | `YES` | - |
| `source_id` | `string` | `YES` | - |
| `current_state` | `string` | `YES` | - |
| `last_transition_utc` | `string` | `YES` | - |
| `history` | `array` | `YES` | - |

## 3. Required Properties

- `schema_version`
- `source_id`
- `current_state`
- `last_transition_utc`
- `history`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
