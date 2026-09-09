# Schema 18: Skill Registry Provider Schema (provider.schema.json)

**Schema Identifier:** `urn:skill-registry:provider:1.0.0`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Definition of supported AI agent runtime providers (Gemini, Claude, Codex, ChatGPT, Agents).

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `object` | `YES` | - |
| `provider_id` | `string` | `YES` | - |
| `provider_name` | `string` | `YES` | - |
| `runtime_family` | `string` | `YES` | - |
| `supported_input_formats` | `array` | `YES` | - |
| `instruction_style` | `string` | `YES` | - |
| `capabilities_supported` | `array` | `YES` | - |
| `enabled` | `boolean` | `YES` | - |

## 3. Required Properties

- `schema_version`
- `provider_id`
- `provider_name`
- `runtime_family`
- `supported_input_formats`
- `instruction_style`
- `capabilities_supported`
- `enabled`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
