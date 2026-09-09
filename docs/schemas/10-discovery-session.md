# Schema 10: SkillRegistryDiscoverySession (discovery-session.schema.json)

**Schema Identifier:** `urn:skill-registry:discovery-session:1.0.0`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Canonical definition of a completed or active Discovery Session in Skill Registry.

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `string` | `YES` | - |
| `discovery_id` | `string` | `YES` | - |
| `source_id` | `string` | `YES` | - |
| `started_utc` | `string` | `YES` | - |
| `completed_utc` | `string` | `YES` | - |
| `status` | `string` | `YES` | - |
| `candidates_scanned_count` | `integer` | `YES` | - |
| `candidates_discovered_count` | `integer` | `YES` | - |
| `quarantine_violations_blocked` | `integer` | `YES` | - |
| `boundaries_evaluated` | `array` | `YES` | - |
| `audit_transaction_id` | `string` | `YES` | - |
| `error_message` | `string null` | `NO` | - |

## 3. Required Properties

- `schema_version`
- `discovery_id`
- `source_id`
- `started_utc`
- `completed_utc`
- `status`
- `candidates_scanned_count`
- `candidates_discovered_count`
- `quarantine_violations_blocked`
- `boundaries_evaluated`
- `audit_transaction_id`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
