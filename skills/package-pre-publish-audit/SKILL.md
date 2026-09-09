---
name: package-pre-publish-audit
description: Audits packages and tarballs before publishing to npm, PyPI, or Crates.io.
---

# Package Pre-Publish Audit

Audit and verify package distribution tarballs, manifests, and build outputs before publishing
to package registries (npm, PyPI, Crates.io, or Maven).
Ensures zero unintended files, credentials, local path leaks, or broken entrypoint links exist in release artifacts.

## Critical Pre-Publish Checklist

1. **Secret & Credential Scrubbing**:
   - Verify `.npmignore`, `.gitignore`, or `package.json` `files` field.
   - Assert `.env`, private keys, local auth tokens, and test fixtures are excluded.
2. **Entrypoint & Typing Integrity**:
   - Assert `main`, `module`, `bin`, and `types` in `package.json` (or `pyproject.toml` / `Cargo.toml`) point to valid, existing files in build output.
3. **Tarball Content Inspection (Dry-Run)**:
   - Run dry-run packaging and inspect the file list line by line.
4. **License & README Verification**:
   - Ensure `LICENSE` file is bundled and matches the declared SPDX license identifier.
   - Confirm `README.md` is present and rendered cleanly without broken links.

## Execution Commands by Ecosystem

```bash
# npm / JavaScript
npm pack --dry-run --json > .evidence/npm-pack-preview.json

# Python / PyPI
python -m build --sdist --wheel && twine check dist/*

# Rust / Crates.io
cargo package --list
```