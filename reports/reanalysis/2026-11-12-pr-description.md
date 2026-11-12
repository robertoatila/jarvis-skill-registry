<!-- Texto do pull request da branch arena/82188603-jarvis-skill-registry. Uso: gh pr create --base main --title "Harden ingestion and command execution; measured figures only; portable test battery" --body-file reports/reanalysis/2026-11-12-pr-description.md -->

## 🎯 Pull Request Overview

Review of `Updates.md` and `SECURITY_AUDIT.md` against the code, followed by the fixes that held up. Full record: `reports/reanalysis/2026-11-12-closure.md`. Technical reference: `docs/architecture/LOCAL_RUNTIME_SAFEGUARDS.md`.

**Security**

- `POST /api/ingest/promote` accepted a skill name that wrote outside `skills/` (reproduced on `main`). The name is now validated, the write is confined, and replacing an existing skill requires `overwrite: true`.
- Third-party text from GitHub is normalised by `tooling/agentic/untrusted_text.py` before it reaches a generated skill.
- No `shell=True` in the runtime (`tooling/agentic/safe_command.py`).
- Directory junctions are detected on Python 3.10 and 3.11, where the check used to be skipped.
- `/api/pipeline/run` no longer answers `PASS` when the audit script is missing.
- A personal tailnet hostname was removed from `ui/index.html`. **It is still in the Git history.**

**Stated figures**

- Cockpit, README, public site and desktop launcher no longer ship remembered numbers. Values are measured or omitted. The site said 394 skills and replayed output of commands that do not exist; it now shows the measured 166 and recorded output of five real commands.

**Portability and maintenance**

- `python jarvis.py --full-test` passes on Linux with Python 3.11 (it failed on `main`) and now discovers every `tests/test_*.py`.
- Paths outside the checkout are resolved in `tooling/agentic/config.py`.
- New: `tooling/validate_repository_contracts.py`, `tooling/large_artifacts.py`, a narrow `.gitattributes`, a ruff-only `pyproject.toml`.

**Behaviour changes**

1. `infrastructure.run_command` rejects shell syntax (`&&`, `|`, `;`, redirection, substitution) with `BLOCKED_DISALLOWED`, exit 126. Variables, `~` and globs are not expanded.
2. `/api/ingest/promote` returns `409` for an existing skill unless `overwrite` is sent.
3. `/api/pipeline/run` returns `UNAVAILABLE` when the audit script is missing.
4. Service-worker cache is `jarvis-mark-liv-shell-v13` (was `v10`).
5. `tooling/build_site.py` writes only with `--force`.

**Not validated**

Nothing here was run on Windows or macOS, in PowerShell or in a real browser. `evidence/current.json` is unchanged. The PowerShell layer was not modified.

## 🔗 Related Issues / Proposals

None. Source documents: `Updates.md`, `SECURITY_AUDIT.md`.

## 🛡️ Sovereign Security Protocol v13 (SSP-v13) Checklist

- [x] **SSP13-01 (Zero Secret Leakage)**: `python tooling/audit_pre_publish_security.py` returned exit code 0.
- [x] **SSP13-02 (Merkle Integrity)**: no change under `skills/`, `releases/`, `state/canonical-merkle.json` or `evidence/`.
- [ ] **SSP13-04 (Token Budget Defense)**: no skill frontmatter changed. Two agent descriptions (`quantum-recon-osint`, `quantum-vault-curator`) lost a remembered total and are shorter, but at 18 and 17 words they are still above 15, as they were on `main`.
- [x] **SSP13-06 (Path Anonymization)**: no added line contains a `C:\Users\...` path. Existing ones in the PowerShell layer were left as they are.
- [ ] **SSP13-09 (WCAG 2.1 AA)**: not verified. The HUD changes are text and placeholder values only; no browser or accessibility check was run.
- [ ] **SSP13-10 (Pre-Publish Gate)**: not run. `pwsh` was not available; `tooling/Bootstrap.ps1` must be run on Windows before merge.

## 🧪 Verification & Test Results

Linux, Python 3.11.2, Node 22.22.3.

```text
python jarvis.py --full-test                                  127 suites, 907/907, VERDICT: PASS, exit 0
python jarvis.py --doctor                                     exit 0
python jarvis.py --test                                       exit 0
node tests/test_chat_session.cjs                              exit 0
node tests/test_operational_cockpit.cjs                       exit 0
node tests/test_runtime_observability.cjs                     exit 0
python tooling/validate_repository_contracts.py --summary     PASS_WITH_WARNINGS (1 known warning)
python tooling/audit_documentation_claims.py                  PASS, 0 violations
python tooling/audit_pre_publish_security.py                  exit 0
python tooling/large_artifacts.py verify                      PASS
ruff check .                                                  All checks passed
git status --short (after the battery)                        empty
```

Base for comparison (`main@06f369f`): `--full-test` exit 1, 104 suites, 662 tests, 2 errored.

The one validator warning is the frontmatter position in `skills/git-bugfix-contribution/SKILL.md`; its hash is pinned by the v1.1.0 lockfiles, so the fix belongs with the next release seal.
