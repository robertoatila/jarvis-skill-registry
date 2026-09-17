# First External Skill Contribution

This walkthrough is the shortest supported path from a fresh fork to a reviewable pull request that adds **one skill**. You do not need to understand the full J.A.R.V.I.S. runtime.

The example is `text-stats`: a harmless, deterministic, local-only skill written from scratch for this walkthrough. It does not call a vendor, open the network, mutate infrastructure, or require credentials.

## 1. Start from a fresh fork and clone

Fork `robertoatila/jarvis-skill-registry` on GitHub, then clone **your fork** into a clean directory:

```bash
git clone https://github.com/<YOUR-GITHUB-USER>/jarvis-skill-registry.git
cd jarvis-skill-registry
git remote add upstream https://github.com/robertoatila/jarvis-skill-registry.git
git fetch upstream
git checkout -b feat/text-stats upstream/main
```

Confirm that the checkout is clean before editing:

```bash
git status --short
```

An empty result means you are starting from the expected clean baseline.

## 2. Create one canonical skill

Create:

```text
skills/text-stats/SKILL.md
```

The current catalog reader discovers a skill by its directory and reads `name`, `description`, and `tags` from the frontmatter near the top of `SKILL.md`.

Use this minimal example:

<!-- example-skill:start -->
```markdown
---
name: text-stats
description: Deterministically summarize basic statistics for user-provided text using local input only.
tags: [text, local, deterministic]
---

# Text Stats

Use this skill when a task needs simple, reproducible text measurements such as character, word, line, or non-empty-line counts.

## Contract

- Input: text explicitly supplied for analysis.
- Output: deterministic counts derived only from that input.
- No network access.
- No filesystem mutation.
- No external service or vendor dependency.
- No hidden side effects.

## Procedure

1. Read only the text supplied for the task.
2. Count the requested units deterministically.
3. Return the counts and state exactly what was measured.
4. Do not infer semantic quality, authorship, intent, or truth from the counts.

## Boundary

This skill measures text structure only. It does not execute commands, fetch remote content, or verify claims contained in the text.
```
<!-- example-skill:end -->

Keep the first contribution this small. Do not add scripts, dependencies, generated files, unrelated formatting, or a second skill unless the skill actually requires them.

## 3. Check provenance and license before copying anything

The `text-stats` example above is original repository documentation written from scratch, so there is no third-party implementation to import.

If your real contribution adapts third-party material, provenance and license review happen **before** copying it into `skills/`:

1. identify the exact upstream source, revision or release;
2. identify the license that applies to the material you want to reuse;
3. confirm that the license permits the intended redistribution/modification;
4. preserve attribution, copyright notices, NOTICE files, or license text when required;
5. record the upstream source and license in the pull request or a nearby reference file;
6. do not copy material whose provenance or license is unknown or incompatible.

A repository URL is not, by itself, permission to reuse its contents. Do not include credentials, private configuration, browser/session material, personal data, or vendor secrets as examples.

## 4. Run the minimum portable validation

From the repository root:

```bash
python jarvis.py --doctor
python jarvis.py --full-test
python benchmarks/context_budget_benchmark.py
python tooling/audit_pre_publish_security.py
```

These commands cover environment diagnostics, the discovered agentic test battery, the bounded-context benchmark invariants, and the pre-publish secret/hygiene audit.

For a documentation-only skill with no scripts or runtime adapter, do not claim more than these checks prove. CI will additionally exercise the repository's supported portable/Legacy matrix.

## 5. Interpret a failure; do not bypass it

If a command fails, **read the first failing test** or first concrete error before editing anything else. The first failure often identifies the smallest broken contract.

A useful sequence is:

1. copy the exact failing test/error and command into your notes;
2. determine whether the failure comes from your new skill, the checkout/environment, or a pre-existing baseline issue;
3. fix the cause rather than deleting assertions, changing expected values, disabling discovery, or weakening a gate;
4. rerun the narrow failing check when one exists;
5. rerun the full minimum validation above.

**Do not bypass** a failing test, audit, authorization check, or provenance/license requirement just to obtain a green result. If the baseline itself is broken, document the exact baseline SHA and failure instead of hiding it in the skill PR.

## 6. Review exactly what will be committed

Check the diff:

```bash
git status --short
git diff -- skills/text-stats/SKILL.md
```

For this walkthrough, the contribution should contain one skill and any narrowly necessary documentation/test evidence only.

Commit it:

```bash
git add skills/text-stats/SKILL.md
git commit -m "feat: add text-stats skill"
git rev-parse HEAD
```

Record the **exact commit SHA** returned by `git rev-parse HEAD`. Push your branch:

```bash
git push -u origin feat/text-stats
```

Then open a pull request from your fork into `robertoatila/jarvis-skill-registry:main`.

## 7. Put reproducible evidence in the pull request

A small skill PR should answer these five questions directly:

- **Problem** — What concrete capability or documentation gap exists?
- **Change** — What did this PR add? Keep the scope to one skill.
- **Evidence** — Provide the exact commit SHA, exact commands you ran, and their pass/fail results.
- **Boundary** — What do those checks *not* prove? For example, local deterministic validation does not prove compatibility with a provider you never called.
- **Risk** — What existing behavior could this change affect, and why is the scope small?

A compact evidence section can look like this:

```text
Exact commit: <40-character SHA>

Commands:
python jarvis.py --doctor
python jarvis.py --full-test
python benchmarks/context_budget_benchmark.py
python tooling/audit_pre_publish_security.py

Result:
- doctor: PASS
- full-test: PASS (<record the exact suite/test counts>)
- context benchmark: PASS (<record only the byte measurements it actually reports>)
- pre-publish audit: PASS
```

Do not include credentials, access tokens, local secret files, private paths, or copied terminal output that contains them.

## 8. Keep the claim narrow

A merged `SKILL.md` proves that the canonical skill definition is present and that the cited repository checks passed for the cited revision. It does not automatically prove external provider availability, tool execution, user authorization, or real-world outcome quality.

If the skill later gains scripts, network access, dependencies, external effects, or elevated authority, treat that as a separate change with the additional contracts and evidence appropriate to that behavior.
