# ADR-024: Registry export formats and trust claims

## Status

**PARTIAL / OCI creation and intake disabled.** This decision supersedes the previous `ACCEPTED (Phase 22 / Gate 22 Certified)` status, which was not supported by the implementation.

## Context

An audit of `tooling/RegistryCore.psm1`, `tooling/OciDistributionEngine.psm1`, their schemas, examples, and generated exports found that export files with `.json` and `.tar.gz` extensions contained only a short marker string. The OCI path emitted synthetic skill text, used a digest-shaped string as a signature, and returned `VALID` without cryptographic signature verification. The pull path promoted that digest check to `signature_verified=true` and `quarantine_assessment=CLEAN`. These outputs were not valid evidence of package contents, publisher identity, or trust.

## Decision

1. `New-RegistryExportBundle` creates only a real, parseable JSON metadata descriptor (format `2.0.0`). OCI and tarball requests fail closed until real packers and verification exist.
2. The descriptor fingerprints only the enumerated public schemas and quarantine-link file. Its named `catalog_snapshot.sha256` is a sorted path/hash inventory fingerprint; it is not a Merkle root, signature, or publisher identity.
3. Local verification reports byte/JSON/snapshot consistency against the mutable local ledger. It always reports `signature_verified=false` and `authenticity_established=false`.
4. `New-OciSkillBundle` and `Invoke-OciPullStaging` fail before writing or copying files. `Test-OciPackageVerification` can report digest consistency, but never reports a signature as verified.
5. Historical exports and examples remain in place for provenance, but old marker payloads are classified as legacy/unverified and are not packages. They are not silently rewritten into apparently valid artifacts.
6. User memory is stored in ignored `state/jarvis_memory.local.json`. The tracked `state/jarvis_memory.json` is an empty template, and public Obsidian Note 19 excludes private profiles, facts, counts, and runtime heuristics.

## Consequences

- Metadata export remains available and explicitly unsigned.
- OCI/tar distribution is unavailable until content binding, real archive serialization, signer key management, trusted signature verification, and safe intake checks are implemented.
- Existing clients that expect a `VERIFIED_VALID` export result must handle the new `CONTENT_CHECKS_MATCH` state and its authentication limitations.
- Historical files remain in Git history. This change removes personal records from the current public tree but does not rewrite public history.

## Acceptance criteria for re-enabling OCI

- Package the exact selected `SKILL.md` bytes and declared dependencies; reject missing or synthetic source records.
- Produce standards-conformant OCI layer bytes and verify every digest and size.
- Sign the exact manifest with a managed private key; verify with an explicitly trusted public key and test invalid, absent, changed, expired, and untrusted signatures.
- Never map digest consistency alone to signature verification, cleanliness, approval, or activation.
- Intake uses isolated non-destructive staging, explicit quarantine policy, auditable human approval, and no automatic activation.
- Run isolated positive and negative tests without fixed developer paths or deletion of pre-existing output.
