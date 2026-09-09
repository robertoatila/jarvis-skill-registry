---
name: tech-debt-audit
description: "Audit, quantify, and categorize architectural, technical, and testing debt across a codebase. Produces a structured Tech Debt Scorecard with prioritized remediation backlog. Triggers: tech debt, tech debt audit, code debt, audit debt, architectural debt, refactoring backlog."
---

# Tech Debt Audit

Scan, catalog, and evaluate technical debt across a repository to produce an actionable,
prioritized remediation plan. Evaluates architectural decay, missing test coverage,
deprecated dependencies, and dead configuration layers without mutating source files.

## Technical Debt Classification Matrix

| Dimension | Indicators | Severity Score (1-10) |
|---|---|---|
| **Architectural** | Circular dependencies, leaky abstractions, monorepo boundary violations | High (7-10) |
| **Code Quality** | Complex God-classes, high cyclomatic complexity, copy-paste duplication | Medium (4-6) |
| **Testing** | Untested critical paths, flakiness, missing regression mocks | High (7-9) |
| **Dependencies** | Outdated major packages, unmaintained libraries, security advisories | Medium-High (5-8) |
| **Documentation & Typings**| Inaccurate docstrings, implicit `any` types, missing interface contracts | Low-Medium (2-5) |

## Audit Steps

1. **Static Analysis & Metrics Collection**:
   - Inspect repository structure and file distribution.
   - Run type-checkers (`tsc --noEmit`, `mypy`, or `cargo check`).
   - Identify TODO, FIXME, HACK, and DEPRECATED markers.
2. **Prioritization Scoring**:
   - Calculate Effort vs. Impact ratio for each debt item.
3. **Generate Debt Scorecard**:
   - Save report to `${EVIDENCE_DIR:-.evidence/tech-debt}/debt-scorecard.md`.