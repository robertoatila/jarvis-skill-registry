# Schema 11: ExecutionProfile (execution-profile.schema.json)

**Schema Identifier:** `https://skill-registry.local/schemas/execution-profile.schema.json`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Schema for Execution Profiles and Runtime Sandbox Specifications in the Skill Registry platform

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `string` | `YES` | - |
| `profile_id` | `string` | `YES` | - |
| `profile_name` | `string` | `YES` | - |
| `description` | `string` | `NO` | - |
| `target_trust_level` | `string` | `YES` | - |
| `isolation_level` | `string` | `YES` | - |
| `network_policy` | `string` | `YES` | - |
| `allowed_domains` | `array` | `NO` | - |
| `filesystem_policy` | `string` | `YES` | - |
| `process_limits` | `object` | `YES` | - |
| `env_variable_policy` | `string` | `YES` | - |
| `whitelisted_env_vars` | `array` | `NO` | - |
| `created_utc` | `string` | `YES` | - |
| `audit_transaction_id` | `string null` | `NO` | - |

## 3. Required Properties

- `schema_version`
- `profile_id`
- `profile_name`
- `target_trust_level`
- `isolation_level`
- `network_policy`
- `filesystem_policy`
- `process_limits`
- `env_variable_policy`
- `created_utc`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
