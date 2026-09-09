---
name: pr-review-resolution
description: Analyzes and systematically resolves pull request review comments and automated checks.
---

# PR Review Resolution

Systematically inspect review comments, feedback threads, and CI failures on open Pull Requests.
Guides the developer or agent through understanding feedback, implementing fixes, verifying regressions,
and replying with clear technical context.

## Golden rules

- **Never Blindly Agree**: Understand the reviewer's underlying concern. Verify whether the requested change breaks contracts or has unintended side effects.
- **Zero Force-Push Without Policy**: Never overwrite branch history with `git push -f` unless explicitly coordinated with team policy.
- **Test Before Replying**: Never mark a review thread as resolved or push commits without local test validation.
- **Transparent Thread Replies**: Provide brief, respectful explanations linking to the commit SHA that resolves the comment.

## Resolution Lifecycle

1. **Catalog Feedback**: Group review comments into:
   - Blocking / Required Changes (Security, Architecture, Bugs).
   - Suggestions & Refactorings (Style, Minor improvements).
   - Questions / Clarifications (Requires technical justification).
2. **Reproduce & Implement**:
   - Write regression test reproducing the reviewer's finding.
   - Implement minimal, focused fix.
3. **Verify**:
   - Run linter, type-check, and targeted tests.
4. **Push & Reply**:
   - Push commit with conventional commit message referencing the PR.