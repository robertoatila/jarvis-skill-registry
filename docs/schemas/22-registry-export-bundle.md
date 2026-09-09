# Schema 22: RegistryExportBundleManifest (registry-export-bundle.schema.json)

**Schema Identifier:** `https://skill-registry.local/schemas/registry-export-bundle.schema.json`
**Schema Standard:** Draft 2020-12
**Specification Version:** 1.0.0

## 1. Description & Purpose

Schema #33 - Portable, cryptographically sealed export bundle manifest with OCI Image format compliance

## 2. Structural Definition & Properties

| Property | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `export_id` | `string` | `YES` | - |
| `bundle_type` | `string` | `YES` | - |
| `export_format_version` | `string` | `YES` | - |
| `created_utc` | `string` | `YES` | - |
| `registry_metadata` | `object` | `YES` | - |
| `quarantine_anchor` | `object` | `YES` | - |
| `canonical_merkle_root` | `string` | `YES` | - |
| `manifest_counts` | `object` | `YES` | - |
| `bundle_payload` | `object` | `YES` | - |
| `oci_descriptor` | `object` | `NO` | - |
| `governance_lock` | `object` | `YES` | - |

## 3. Required Properties

- `export_id`
- `bundle_type`
- `export_format_version`
- `created_utc`
- `registry_metadata`
- `quarantine_anchor`
- `canonical_merkle_root`
- `manifest_counts`
- `bundle_payload`
- `governance_lock`

## 4. Invariants & Governance Rules

- `additionalProperties: false` is strictly enforced.
- Validated against JSON Schema Draft 2020-12 specification.
- Changes require formal Architecture Decision Record and Gate approval.
