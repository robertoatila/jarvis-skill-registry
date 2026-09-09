# Schema 24: SecurityAssessmentReport (security-report.schema.json)

**Schema Identifier:** `https://skill-registry.local/schemas/security-report.schema.json`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Schema definition for static security evaluation and threat modeling reports in Skill Registry

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `string` | `YES` | - |
| `report_id` | `string` | `YES` | - |
| `resource_id` | `string` | `YES` | - |
| `assessed_utc` | `string` | `YES` | - |
| `risk_level` | `string` | `YES` | - |
| `verdict` | `string` | `YES` | - |
| `risk_score` | `integer` | `YES` | - |
| `findings` | `array` | `YES` | - |
| `scanned_files_count` | `integer` | `YES` | - |
| `ruleset_version` | `string` | `YES` | - |
| `audit_transaction_id` | `string null` | `NO` | - |

## 3. Required Properties

- `schema_version`
- `report_id`
- `resource_id`
- `assessed_utc`
- `risk_level`
- `verdict`
- `risk_score`
- `findings`
- `scanned_files_count`
- `ruleset_version`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
