# ADR-024: Registry Export, OCI Image Bundling & Cryptographic Sealing

## Status

ACCEPTED (Phase 22 / Gate 22 Certified)

## Context

Deploying skill bundles across air-gapped environments, container registries, or multi-machine clusters requires standardized packaging formats. Exporting must preserve cryptographic provenance and quarantine links without permitting unattended promotion.

## Decision

Implement the Registry Export Engine (`Export-RegistryArtifactBundle`, `Test-RegistryExportBundleIntegrity`):

1. Defined by Schema #33 (`schemas/registry-export-bundle.schema.json`).
2. Supports export targets:
   - `OCI_ARTIFACT`: Standard OCI Image Manifest v1 (`application/vnd.oci.image.manifest.v1+json`) with layer SHA-256 digests and annotations.
   - `STANDALONE_TARBALL`: Compressed tarball containing skill payload and manifest.
   - `METADATA_ONLY`: Standalone JSON metadata descriptor.
3. Computes and embeds global deterministic Merkle root anchors.
4. Validates quarantine link integrity (`gov-quarantine-link-v1`) on every bundle.
5. Records export events in `index/exports.jsonl`.

## Alternatives Considered

- *Proprietary zip archive format*: Rejected in favor of open OCI Image Specification standards.

## Consequences

- **Positive**: Cloud-native interoperability, container registry compatibility, verifiable cryptographic sealing.
- **Negative**: Bundling large composite skills incurs archive creation time.

## Security Implications

Guarantees exported bundles carry immutable proof of quarantine compliance and content integrity.

## Related Phases / Gates

- Phase 22: Registry Export & Sealing (Gate 22)
