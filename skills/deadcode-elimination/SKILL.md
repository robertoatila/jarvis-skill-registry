---
name: deadcode-elimination
description: Detects and prunes dead code, unused functions, orphan modules, and obsolete dependencies.
---

# Dead Code Elimination

Identify, verify, and safely prune dead code, unreferenced exports, orphan files,
and unused package dependencies. Prevents false-positive deletion by requiring
compilation and test verification at every step.

## Safety Invariants (Read Before Deleting Anything)

- **Test Suite Green First**: Never start dead code elimination while the test suite is failing.
- **Dynamic Reflection Awareness**: Check for dynamic imports (`import()`, `require()`, reflection, dependency injection containers) before declaring an export dead.
- **Atomic Commits per Batch**: Delete in small, cohesive groups (one commit per module or package) with descriptive commit messages.
- **Verification Gate**: After every removal, run full type-check and unit tests. If tests fail, immediately revert (`git checkout -- <file>`).

## Detection Strategy

1. **Unused Exports**: Run ecosystem analyzers (`knip`, `ts-prune`, `cargo-udeps`, `flake8/vulture`).
2. **Orphan Assets & Configs**: Scan for unreferenced CSS, JSON, and template assets.
3. **Obsolete Dependencies**: Identify packages declared in manifests but never imported across the codebase.

## Execution Procedure

```bash
# Step 1: Baseline verification
npm test && npm run build

# Step 2: Identify candidate unused exports
npx knip --reporter json > .evidence/deadcode-candidates.json

# Step 3: Remove candidate batch, then re-verify
git commit -m "refactor(cleanup): eliminate unused module X"
```