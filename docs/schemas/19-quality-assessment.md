# Schema 19: QualityAssessmentEvaluation (quality-assessment.schema.json)

**Schema Identifier:** `https://skill-registry.local/schemas/quality-assessment.schema.json`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Schema definition for static quality assessment and functional utility evaluation reports in Skill Registry

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `string` | `YES` | - |
| `evaluation_id` | `string` | `YES` | - |
| `resource_id` | `string` | `YES` | - |
| `evaluated_utc` | `string` | `YES` | - |
| `dimensions` | `object` | `YES` | - |
| `composite_score` | `integer` | `YES` | - |
| `quality_tier` | `string` | `YES` | - |
| `verdict` | `string` | `YES` | - |
| `strengths` | `array` | `YES` | - |
| `weaknesses` | `array` | `YES` | - |
| `audit_transaction_id` | `string null` | `NO` | - |

## 3. Required Properties

- `schema_version`
- `evaluation_id`
- `resource_id`
- `evaluated_utc`
- `dimensions`
- `composite_score`
- `quality_tier`
- `verdict`
- `strengths`
- `weaknesses`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
