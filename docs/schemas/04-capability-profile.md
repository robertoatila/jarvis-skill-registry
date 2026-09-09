# Schema 04: Skill Registry Capability Profile Schema (capability-profile.schema.json)

**Schema Identifier:** `urn:skill-registry:capability-profile:1.0.0`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Formal semantic surface profile, declared/inferred capabilities, taxonomy normalization, and dependency declarations for a skill resource.

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `object` | `YES` | - |
| `profile_id` | `string` | `YES` | - |
| `resource_id` | `string` | `YES` | - |
| `canonical_name` | `string` | `YES` | - |
| `primary_domain` | `string` | `YES` | - |
| `declared_capabilities` | `array` | `YES` | - |
| `inferred_capabilities` | `array` | `YES` | - |
| `canonical_capabilities` | `array` | `YES` | - |
| `capability_density_score` | `number` | `YES` | - |
| `dependency_requirements` | `array` | `YES` | - |
| `audit_transaction_id` | `string` | `NO` | - |
| `created_utc` | `object` | `YES` | - |
| `updated_utc` | `object` | `YES` | - |

## 3. Required Properties

- `schema_version`
- `profile_id`
- `resource_id`
- `canonical_name`
- `primary_domain`
- `declared_capabilities`
- `inferred_capabilities`
- `canonical_capabilities`
- `capability_density_score`
- `dependency_requirements`
- `created_utc`
- `updated_utc`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
