# Security Policy

## Current protocol source

The repository's current policy text is [Sovereign Security Protocol v13.4.0](docs/security/PROTOCOLO_SEGURANCA_v13.4_CANONICO.md), dated 2026-09-29 in the source document. Its repository status is **CANÔNICO**. The source declares the explicit activation trigger `SEGURANÇA`; its presence does not prove that controls are implemented, tested, or satisfied for a release.

See the [security documentation index](docs/security/README.md) for provenance, the Obsidian entry point, historical versions, and the limits of the machine-readable subset. The JSON descriptor retains inherited v13.2 invariants and a historical Merkle anchor; it is not the full v13.4 control set.

## Reporting a vulnerability

Do not publish exploit details, secrets, or unpatched vulnerability information in a public issue. If GitHub Private Vulnerability Reporting is enabled for this repository, use a private Security Advisory. If it is unavailable, contact the repository owner privately through the GitHub profile before sharing sensitive details. This policy makes no response-time promise.

## Existing pre-publish check

Run the repository's static pre-publish check for changes that affect publishable content:

```bash
python tooling/audit_pre_publish_security.py
```

This check is one validation input. A successful result alone does not establish full protocol conformance or release readiness; use the direct gates and current evidence required by the affected project.
