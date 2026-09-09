---
name: github-issue-pr-triage
description: "Triage incoming GitHub issues and Pull Requests using GitHub CLI (gh) in read-only analysis mode. Prioritizes bugs, identifies regressions, maps duplicates, and drafts structured resolution proposals. Triggers: github triage, issue triage, pr triage, triage issues, triage github, bug triage."
---

# GitHub Issue & PR Triage

Perform fast, deterministic triage of GitHub issues and pull requests using the official `gh` CLI.
Analyzes bug reports, categorizes impact, detects duplicates, and drafts actionable triage summaries
without writing or pushing unauthorized comments.

## Golden rules

- **Non-Destructive & Read-Only**: Use `gh issue list --json` and `gh pr list --json` for passive querying. Never close issues or merge PRs automatically during triage.
- **Reproducibility First**: Differentiate between verified bugs with reproduction steps and unconfirmed user environment questions.
- **Linear Prioritization**: Map items to P0 (Blocker/Outage), P1 (Critical degradation), P2 (Standard defect), P3 (Minor/Cosmetic).

## Triage Workflow

```bash
# 1. Fetch open issues without labels
gh issue list --state open --limit 50 --json number,title,author,labels,createdAt

# 2. Fetch open PRs needing review
gh pr list --state open --search "review:required" --json number,title,headRefName,updatedAt

# 3. Analyze linked commits and diff stats
gh pr diff <PR_NUMBER> --stat
```

## Triage Matrix Output

Produce a triage table:
| Number | Title | Type | Priority | Affected Component | Recommended Action |
|---|---|---|---|---|---|
| #102 | Crash on startup | Bug | P0 | Auth Core | Assign maintainer, immediate hotfix |
| #105 | Add dark mode | Feat | P3 | UI/Theme | Queue for roadmap milestone |