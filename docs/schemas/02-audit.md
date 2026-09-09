# Schema 02: Skill Registry Audit Event Schema (audit.schema.json)

**Schema Identifier:** `urn:skill-registry:audit:1.0.0`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Structured append-only audit event record.

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `object` | `YES` | - |
| `event_id` | `string` | `YES` | - |
| `event_type` | `string` | `YES` | - |
| `timestamp_utc` | `object` | `YES` | - |
| `transaction_id` | `string null` | `YES` | - |
| `component` | `string` | `YES` | - |
| `action` | `string` | `YES` | - |
| `target_resource_id` | `string null` | `YES` | - |
| `policy_applied` | `string` | `YES` | - |
| `result` | `string` | `YES` | - |
| `details` | `object` | `YES` | - |

## 3. Required Properties

- `schema_version`
- `event_id`
- `event_type`
- `timestamp_utc`
- `transaction_id`
- `component`
- `action`
- `target_resource_id`
- `policy_applied`
- `result`
- `details`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
