# Schema 29: SkillRegistryStructuralAnalysis (structural-analysis.schema.json)

**Schema Identifier:** `urn:skill-registry:structural-analysis:1.0.0`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Canonical schema for static, non-executable structural analysis reports in Skill Registry.

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `string` | `YES` | - |
| `analysis_id` | `string` | `YES` | - |
| `resource_id` | `string` | `YES` | - |
| `source_id` | `string` | `YES` | - |
| `analyzed_utc` | `string` | `YES` | - |
| `status` | `string` | `YES` | - |
| `structure` | `object` | `YES` | - |
| `declared_metadata` | `object` | `YES` | - |
| `observed_metadata` | `object` | `YES` | - |
| `inferred_metadata` | `object` | `YES` | - |
| `quarantine_check` | `object` | `YES` | - |
| `audit_transaction_id` | `string` | `YES` | - |
| `error_message` | `string null` | `NO` | - |

## 3. Required Properties

- `schema_version`
- `analysis_id`
- `resource_id`
- `source_id`
- `analyzed_utc`
- `status`
- `structure`
- `declared_metadata`
- `observed_metadata`
- `inferred_metadata`
- `quarantine_check`
- `audit_transaction_id`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
