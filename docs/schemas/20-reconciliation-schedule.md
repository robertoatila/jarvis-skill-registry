# Schema 20: SkillRegistryReconciliationSchedule (reconciliation-schedule.schema.json)

**Schema Identifier:** `https://skill-registry.local/schemas/reconciliation-schedule.schema.json`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Schema #30: Contract for periodic upstream reconciliation scheduling, multi-source drift synchronization, dependency DAG resolution, retries, and circuit breaker governance.

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `string` | `YES` | - |
| `schedule_id` | `string` | `YES` | - |
| `schedule_name` | `string` | `YES` | - |
| `description` | `string` | `NO` | - |
| `interval_type` | `string` | `YES` | - |
| `interval_value` | `string integer` | `YES` | - |
| `scope` | `string` | `YES` | - |
| `target_namespaces` | `array` | `NO` | - |
| `target_source_ids` | `array` | `NO` | - |
| `policy_options` | `object` | `YES` | - |
| `dependency_resolution` | `object` | `YES` | - |
| `lifecycle_state` | `string` | `YES` | - |
| `consecutive_failures` | `integer` | `NO` | - |
| `last_execution` | `object null` | `NO` | - |
| `next_run_utc` | `string null` | `NO` | - |
| `created_utc` | `string` | `YES` | - |
| `updated_utc` | `string` | `YES` | - |
| `audit_transaction_id` | `string null` | `NO` | - |

## 3. Required Properties

- `schema_version`
- `schedule_id`
- `schedule_name`
- `interval_type`
- `interval_value`
- `scope`
- `policy_options`
- `dependency_resolution`
- `lifecycle_state`
- `created_utc`
- `updated_utc`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
