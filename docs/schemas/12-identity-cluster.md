# Schema 12: Skill Registry Identity Cluster Schema (identity-cluster.schema.json)

**Schema Identifier:** `urn:skill-registry:identity-cluster:1.0.0`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Canonical schema for identity clusters, deduplication relationships, and canonical resource leader resolution.

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `object` | `YES` | - |
| `cluster_id` | `string` | `YES` | - |
| `cluster_type` | `string` | `YES` | - |
| `canonical_name` | `string` | `YES` | - |
| `leader_resource_id` | `string` | `YES` | - |
| `member_count` | `integer` | `YES` | - |
| `members` | `array` | `YES` | - |
| `divergence_analysis` | `object` | `NO` | - |
| `resolution_policy` | `object` | `YES` | - |
| `audit_transaction_id` | `string` | `NO` | - |
| `created_utc` | `object` | `YES` | - |
| `updated_utc` | `object` | `YES` | - |

## 3. Required Properties

- `schema_version`
- `cluster_id`
- `cluster_type`
- `canonical_name`
- `leader_resource_id`
- `member_count`
- `members`
- `resolution_policy`
- `created_utc`
- `updated_utc`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
