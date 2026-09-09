# Schema 01: Skill Registry Provider Adapter Schema (adapter.schema.json)

**Schema Identifier:** `urn:skill-registry:adapter:1.0.0`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Definition of translation/adaptation rules for exporting skills across runtimes.

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `object` | `YES` | - |
| `adapter_id` | `string` | `YES` | - |
| `target_provider` | `string` | `YES` | - |
| `transformation_mode` | `string` | `YES` | - |
| `parameters` | `object` | `YES` | - |
| `version` | `string` | `YES` | - |

## 3. Required Properties

- `schema_version`
- `adapter_id`
- `target_provider`
- `transformation_mode`
- `parameters`
- `version`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
