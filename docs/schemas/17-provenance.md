# Schema 17: Skill Registry Provenance Schema (provenance.schema.json)

**Schema Identifier:** `urn:skill-registry:provenance:1.0.0`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Immutable origin, repository, commit/revision, and acquisition chain metadata.

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `object` | `YES` | - |
| `provenance_id` | `string` | `YES` | - |
| `source_type` | `string` | `YES` | - |
| `origin_uri` | `string` | `YES` | - |
| `repository_root` | `string null` | `YES` | - |
| `relative_path` | `string` | `YES` | - |
| `revision` | `object` | `YES` | - |
| `observed_utc` | `object` | `YES` | - |
| `ingested_by_tool` | `object` | `YES` | - |
| `integrity_chain` | `object` | `YES` | - |

## 3. Required Properties

- `schema_version`
- `provenance_id`
- `source_type`
- `origin_uri`
- `repository_root`
- `relative_path`
- `revision`
- `observed_utc`
- `ingested_by_tool`
- `integrity_chain`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
