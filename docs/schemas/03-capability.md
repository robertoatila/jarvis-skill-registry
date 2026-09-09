# Schema 03: Skill Registry Capability Schema (capability.schema.json)

**Schema Identifier:** `urn:skill-registry:capability:1.0.0`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Taxonomy definition for extracted and indexed agent capabilities.

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `object` | `YES` | - |
| `capability_id` | `string` | `YES` | - |
| `domain` | `string` | `YES` | - |
| `description` | `string` | `YES` | - |
| `keywords` | `array` | `YES` | - |
| `aliases` | `array` | `YES` | - |

## 3. Required Properties

- `schema_version`
- `capability_id`
- `domain`
- `description`
- `keywords`
- `aliases`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
