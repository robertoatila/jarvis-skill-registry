---
name: governed-package-publish
description: "Execute safe, governed package publishing across npm, PyPI, and Crates.io with mandatory two-phase dry-run, linear git history enforcement, and strict prohibition of force-pushes. Triggers: publish package, package publish, release package, governed publish, npm publish, cargo publish."
---

# Governed Package Publish

Execute safe, governed package releases to public and private registries.
Enforces a strict two-phase dry-run workflow, linear history validation, and absolute protection
against history rewriting.

## CRITICAL SAFETY INVARIANTS (ENFORCED)

> **CRITICAL POLICY: `git push --force` / `git push -f` is STRICTLY PROHIBITED.**
> Publishing workflows must ALWAYS rely on verified linear commit history and immutable git tags.
> Any command attempting to force-push git branches or tags will be immediately aborted.

- **Mandatory Two-Phase Execution**:
  1. Phase 1 (Dry-Run): Build, audit, and simulate publication (`--dry-run`).
  2. Phase 2 (Release): Requires explicit human approval before registry token submission.
- **Git State Cleanliness**: Working tree must be 100% clean (`git status --porcelain` is empty) with HEAD synchronized with upstream remote.
- **Signed Git Tags**: Every release must produce an immutable git tag matching SemVer (`vX.Y.Z`).

## Governed Release Procedure

### Step 1: Pre-Flight Cleanliness & Tag Check
```bash
# Ensure clean working directory
if [ -n "$(git status --porcelain)" ]; then echo "ERROR: Uncommitted changes present"; exit 1; fi

# Verify linear branch state
git fetch origin && git log HEAD..origin/$(git branch --show-current)
```

### Step 2: Dry-Run Publication
```bash
# npm Dry Run
npm publish --dry-run

# Cargo Dry Run
cargo publish --dry-run
```

### Step 3: Governed Release (Human Approval Required)
```bash
# Tag creation and standard push (NO FORCE)
git tag -a "v$(node -p "require('./package.json').version")" -m "Release v$(node -p "require('./package.json').version")"
git push origin main --tags

# Registry submission with provenance
npm publish --provenance --access public
```