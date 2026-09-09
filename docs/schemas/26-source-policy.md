# Schema 26: SkillRegistrySourcePolicy (source-policy.schema.json)

**Schema Identifier:** `urn:skill-registry:source-policy:1.0.0`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Fine-grained permissions and capability gates governing a registered Source.

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `schema_version` | `string` | `YES` | - |
| `policy_id` | `string` | `YES` | - |
| `source_id` | `string` | `YES` | - |
| `discovery_allowed` | `boolean` | `YES` | - |
| `metadata_read_allowed` | `boolean` | `YES` | - |
| `content_read_allowed` | `boolean` | `YES` | - |
| `hash_allowed` | `boolean` | `YES` | - |
| `copy_allowed` | `boolean` | `YES` | - |
| `execution_allowed` | `boolean` | `YES` | - |
| `import_allowed` | `boolean` | `YES` | - |
| `routing_allowed` | `boolean` | `YES` | - |
| `promotion_allowed` | `boolean` | `YES` | - |
| `quarantine_precedence` | `boolean` | `YES` | - |

## 3. Required Properties

- `schema_version`
- `policy_id`
- `source_id`
- `discovery_allowed`
- `metadata_read_allowed`
- `content_read_allowed`
- `hash_allowed`
- `copy_allowed`
- `execution_allowed`
- `import_allowed`
- `routing_allowed`
- `promotion_allowed`
- `quarantine_precedence`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
