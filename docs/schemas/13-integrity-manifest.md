# Schema 13: Skill Registry Cryptographic Integrity Manifest Schema (integrity-manifest.schema.json)

**Schema Identifier:** `urn:skill-registry:integrity-manifest:1.0.0`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Canonical schema for deterministic, Merkle-like content integrity manifests and tamper verification.

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `object` | `YES` | - |
| `manifest_id` | `string` | `YES` | - |
| `resource_id` | `string` | `YES` | - |
| `provenance_id` | `string` | `YES` | - |
| `source_id` | `string` | `YES` | - |
| `generated_utc` | `string` | `YES` | - |
| `algorithm` | `object` | `YES` | - |
| `manifest_hash` | `string` | `YES` | - |
| `content_hash` | `string` | `YES` | - |
| `file_count` | `integer` | `YES` | - |
| `byte_sum` | `integer` | `YES` | - |
| `files` | `array` | `YES` | - |
| `quarantine_check` | `object` | `YES` | - |
| `audit_transaction_id` | `string` | `YES` | - |

## 3. Required Properties

- `schema_version`
- `manifest_id`
- `resource_id`
- `provenance_id`
- `source_id`
- `generated_utc`
- `algorithm`
- `manifest_hash`
- `content_hash`
- `file_count`
- `byte_sum`
- `files`
- `quarantine_check`
- `audit_transaction_id`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
