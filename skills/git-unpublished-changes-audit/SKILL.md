---
name: git-unpublished-changes-audit
description: Audits unpublished commits and tags against release registries across monorepos.
---

# Git Unpublished Changes Audit

Compare HEAD with the latest published releases (npm, PyPI, Crates.io, or Git release tags)
and produce an auditable inventory of all unpublished changes structured by architectural layer.

IMMEDIATELY output the analysis. NO unnecessary conversational preamble.

## CRITICAL: DO NOT just copy commit messages!

For each commit or diff range, you MUST:
1. Read the actual code diff to understand WHAT CHANGED.
2. Describe the REAL change in plain, precise technical language.
3. Explain WHY it matters to consumers, operators, or upstream systems.

## Universal Monorepo / Package Layers

Analyze every change against the repository's architectural layers:

| Layer | Typical Contents | Versioning Questions |
|---|---|---|
| **Core / Shared Components** | `packages/*-core`, libraries, schemas, shared utils | Do shared libraries require a patch/minor/major bump? Are downstream consumers broken? |
| **Application / CLI / Agent** | `src/`, root apps, CLI commands, agent configs, skills | What user-facing features or bug fixes are introduced? What semver bump applies? |
| **Adapters / Extensions** | Platform plugins, MCP runtimes, integrations | Do platform adapters need independent versioning or coordinated release? |

*Note: Exclude private internal test fixtures, temporary scratch directories, or local-only files from consumer-facing release notes.*

## Steps to Execute:

1. **Detect latest published versions/tags**:
   - For npm: query `npm view <pkg> version`
   - For Python: check PyPI or `pyproject.toml`
   - For Rust: check `Cargo.toml`
   - Universal Git fallback: `git describe --tags --abbrev=0`
2. **Inspect raw changes**:
   - Run `git diff <published-tag-or-version>..HEAD` to inspect all unreleased diffs.
   - Run `git log <published-tag-or-version>..HEAD --oneline` for commit history.
3. **Classify changed files**:
   - Group files into Core, Application, or Adapter layers.
   - Categorize each change: `feat`, `fix`, `refactor`, `perf`, `docs`, `security`.
4. **Evaluate breaking changes**:
   - Identify schema changes, signature alterations, or removed flags.
5. **Recommend SemVer bump**:
   - Determine whether changes require `PATCH` (backwards-compatible fixes), `MINOR` (new backwards-compatible features), or `MAJOR` (breaking changes).

## Output Format

### Change Summaries
- `feat`: "Added [capability] that [action]" (explain impact, not just commit title)
- `fix`: "Fixed [issue] where [behavior] occurred, now [resolution]"
- `refactor`: "Refactored [component] to [benefit]"

### Layered Impact Matrix
| Layer | Changed Files | Breaking? | Recommended Bump |
|---|---|---|---|
| Core / Shared | ... | Yes / No | patch / minor / major |
| Application / CLI | ... | Yes / No | patch / minor / major |
| Adapters / Integrations | ... | Yes / No | patch / minor / major |

### Overall Release Recommendation
- **Current Published**: `vX.Y.Z`
- **Recommended Next**: `vX.Y.Z` (with explicit technical justification)