# Historical Documentation Policy

Historical material is retained for provenance, migration context, design evolution and release archaeology. Keeping it does not make every old statement part of the current runtime contract.

## Interpretation rules

A historical document is **not current validation evidence** unless a current executable test, release artifact, or explicitly fresh validation record points back to it. **Do not infer current runtime behavior** from an old roadmap, milestone report, experiment note, screenshot, benchmark, or superseded architecture narrative.

When a historical file conflicts with a current source, use this precedence:

1. executable contracts and fresh CI/release evidence;
2. root [`../../AGENTS.md`](../../AGENTS.md) invariants and repository policy;
3. current active plan/specification referenced by [`../README.md`](../README.md);
4. current architecture/security/design documentation;
5. historical records.

## Compatibility policy

Do not mass-move existing public documentation merely to make the tree look cleaner. External links, issue references, release notes and the Obsidian vault may depend on those paths. Prefer indexing and classification first. Move or delete a historical file only when its references have been audited and a compatibility/migration reason is documented.

## What belongs here

This directory may hold future archive indexes, supersession maps and migrated historical documents. Existing legacy material can remain at its current path until there is evidence that moving it is safe and useful.

The immutable `v0.1.0` release and its evidence remain release history, not a target for cleanup or retagging.
