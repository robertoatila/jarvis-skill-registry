# Schema #33: Registry metadata export manifest

**Schema:** [`registry-export-bundle.schema.json`](../../schemas/registry-export-bundle.schema.json)
**Format:** `2.0.0`
**Status:** metadata-only; unsigned

The v2 descriptor contains registry metadata, selected inventory counts, a scoped SHA-256 snapshot fingerprint, quarantine-link fields, and the digest of its JSON payload. It does not include skill source files and is not a package archive.

The snapshot is computed over the sorted relative paths and SHA-256 hashes of `schemas/*.schema.json` and `governance/quarantine-link.json`. It is an inventory fingerprint, not a Merkle tree or authenticity proof. Verification compares the payload and selected files with a mutable local ledger; it does not authenticate who created or changed that ledger.

Only `METADATA_ONLY` is currently implemented. `OCI_ARTIFACT` and `STANDALONE_TARBALL` fail closed because the repository does not yet have a real OCI/tar packer and trusted signature verifier. Historical marker files remain untrusted legacy records and are not promoted by the current verifier.

See [ADR-024](../adr/ADR-024-export-oci-sealing.md) for the trust boundary and the criteria for restoring package distribution.
