# Schema 30: Skill Registry Transaction Schema (transaction.schema.json)

**Schema Identifier:** `urn:skill-registry:transaction:1.0.0`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Atomic operation specification, transaction journal record, and rollback metadata.

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `object` | `YES` | - |
| `transaction_id` | `string` | `YES` | - |
| `operation_type` | `string` | `YES` | - |
| `initiator` | `string` | `YES` | - |
| `started_utc` | `object` | `YES` | - |
| `completed_utc` | `object` | `YES` | - |
| `status` | `string` | `YES` | - |
| `affected_resources` | `array` | `YES` | - |
| `rollback_snapshot` | `string null` | `YES` | - |
| `error_message` | `string null` | `YES` | - |

## 3. Required Properties

- `schema_version`
- `transaction_id`
- `operation_type`
- `initiator`
- `started_utc`
- `completed_utc`
- `status`
- `affected_resources`
- `rollback_snapshot`
- `error_message`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
