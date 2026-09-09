# Schema 27: SkillRegistrySourceProvenance (source-provenance.schema.json)

**Schema Identifier:** `urn:skill-registry:source-provenance:1.0.0`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Immutable origin, author, and acquisition provenance record for a registered Source.

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `string` | `YES` | - |
| `source_provenance_id` | `string` | `YES` | - |
| `source_id` | `string` | `YES` | - |
| `declared_by` | `string` | `YES` | - |
| `declared_utc` | `string` | `YES` | - |
| `source_type` | `string` | `YES` | - |
| `origin_locator` | `string` | `YES` | - |
| `initial_revision` | `string null` | `NO` | - |
| `audit_transaction_id` | `string` | `YES` | - |
| `declaration_notes` | `string null` | `NO` | - |

## 3. Required Properties

- `schema_version`
- `source_provenance_id`
- `source_id`
- `declared_by`
- `declared_utc`
- `source_type`
- `origin_locator`
- `audit_transaction_id`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
