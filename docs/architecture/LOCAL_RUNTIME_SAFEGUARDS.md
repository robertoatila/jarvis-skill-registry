# Local Runtime Safeguards

Reference for the safeguards added on 2026-11-12. Each section names the module, what it enforces, how to check it and what it does not cover.

**Evidence limit.** Everything here was exercised on Linux with Python 3.11.2 and Node 22. The PowerShell gates, real browsers, Windows and macOS were not run; Windows-only branches were exercised only through tests that substitute the platform. `evidence/current.json` remains the release authority and is unchanged.

The change history, measurements and open items are in [`reports/reanalysis/2026-11-12-closure.md`](../../reports/reanalysis/2026-11-12-closure.md).

## Quick reference

| Concern | Module | Check |
| --- | --- | --- |
| Third-party text reaching skills or prompts | `tooling/agentic/untrusted_text.py` | `python -m unittest tests.test_agentic_untrusted_text` |
| Writes from the ingestion routes | `tooling/jarvis_server.py` | `python -m unittest tests.test_agentic_skill_ingestion_routes` |
| Command execution without a shell | `tooling/agentic/safe_command.py` | `python -m unittest tests.test_agentic_safe_command` |
| Symbolic links and directory junctions | `tooling/agentic/path_links.py` | `python -m unittest tests.test_agentic_path_links` |
| Locations outside the checkout | `tooling/agentic/config.py` | `python -m unittest tests.test_agentic_external_paths` |
| Large optional files | `tooling/large_artifacts.py` | `python tooling/large_artifacts.py status` |
| Structural contracts of distributed files | `tooling/validate_repository_contracts.py` | `python tooling/validate_repository_contracts.py --summary` |
| Stated figures in docs and on the site | `tooling/audit_documentation_claims.py` | `python tooling/audit_documentation_claims.py` |
| Cockpit and site content | `ui/`, `site/` | `tests.test_agentic_cockpit_no_seeded_telemetry`, `tests.test_agentic_site_claims` |
| Line endings of checksummed files | `.gitattributes` | `python -m unittest tests.test_agentic_release_checksum_line_endings` |

All of the test modules above run as part of `python jarvis.py --full-test`.

## 1. Third-party text is data

Repository names, descriptions and topics fetched from GitHub are written by strangers. The autonomous cycle used to paste them into generated `SKILL.md` files.

`sanitize_untrusted_text(value, *, max_chars=240, max_words=None)` returns `SanitizedText(text, flags)`. It removes control and invisible characters, markup, chat-template tokens and frontmatter fences, collapses the text to one line and truncates it. Text that reads as an instruction to a model is replaced by `NEUTRAL_PLACEHOLDER` and flagged `instruction_like_content`. `describe_external_repository` and `frontmatter_scalar` build on it for the two places that emit third-party text.

Limits: this is a normaliser, not a classifier. A description can still mislead a reader in plain prose; the flag is a reason to review, and its absence is not a clearance.

## 2. Ingestion routes

| Route | Behaviour |
| --- | --- |
| `POST /api/workflow/execute`, `POST /api/ingest/analyze` | Produce a proposal only. They never write under `skills/`. |
| `POST /api/ingest/promote` | Writes one `skills/<name>/SKILL.md`. `400` for an invalid name or body, `413` above 256 KiB, `409 CONFLICT` when the skill exists and `overwrite` is not set. The response carries `index_refreshed`. |
| `POST /api/pipeline/run` | `UNAVAILABLE` when the pipeline script is missing, instead of a simulated success. |
| `POST /api/sync-stars` | `503` when Node.js is not on `PATH`. |

The skill name must match `[A-Za-z0-9][A-Za-z0-9._-]*`, be at most 100 characters, not end with a dot and not be a reserved Windows device name, and the resolved target must be a direct child of `skills/` that is neither a symbolic link nor a junction. Before this change a crafted name could write outside `skills/`; this was reproduced against the old code and is covered by a test.

A promoted skill is also copied to an IDE skills directory when that directory already exists. `JARVIS_IDE_SKILLS_DIR` names it; the default is `~/.gemini/config/skills`. Set the variable to an empty string to disable the copy.

## 3. Commands run without a shell

`safe_command.run_command_line(command, *, cwd, timeout, env)` starts exactly one process with `shell=False`. `split_command` turns a command string into arguments and raises `CommandRejected` for anything a shell would interpret: `;`, `&&`, `||`, `|`, redirections, backticks, `$(...)`, unquoted parentheses, a word-initial `#`, and escapes whose meaning differs between shells.

Consequences for callers:

- `infrastructure.run_command` returns `BLOCKED_DISALLOWED` with exit code `126` for a rejected command, `127` when the program is not found and `124` on timeout.
- Variables, `~` and globs are **not** expanded. Pass the expanded value, or pass an argument list.
- A task plan that relied on shell operators is now blocked instead of executed. `runtime_core` forwards the task command unchanged, so such a plan must be rewritten as separate steps.

Limits: this removes shell interpretation; it is not a sandbox. The started program has the permissions of the user. One internal use of `shell=` remains in `tooling/validate_v020_plan4.py`, for `.cmd`/`.bat` on Windows over a fixed list of npm commands.

The POSIX splitter was compared with `/bin/sh` on 5,314 generated inputs and the Windows splitter with the documented `CommandLineToArgvW` rules on 200,000 generated inputs, without a mismatch. The Windows comparison used a reference implementation, not a Windows host.

## 4. Links and junctions

`Path.is_junction()` exists from Python 3.12. The earlier `hasattr` guard avoided a crash on 3.10 and 3.11 but skipped the check there, so on Windows a directory junction passed rules that refuse linked paths.

`path_links.is_junction(path)` reads the reparse tag from `os.lstat`, which is what the 3.12 standard library does, and never raises. `path_links.is_link(path)` is true for a symbolic link or a junction. They replace the earlier guard at ten call sites in seven modules. The repository validator rejects a direct `.is_junction()` call (`python-compat` check).

## 5. Locations outside the checkout

No module under `tooling/` names a drive letter, except the documented legacy default in `tooling/agentic/config.py`.

| Variable | Meaning | Default |
| --- | --- | --- |
| `JARVIS_REGISTRY_ROOT` | Checkout root | Directory containing `jarvis.py` |
| `JARVIS_ARSENAL_HOME` | External arsenal directory (`data/arsenal_library.sqlite`, model file) | Windows: `D:/Program Files/jarvis-arsenal`; elsewhere: `~/.jarvis-arsenal` |
| `GEMINI_ROOT` | Gemini configuration root | `~/.gemini` |
| `JARVIS_IDE_SKILLS_DIR` | IDE mirror for promoted skills; empty string disables it | `~/.gemini/config/skills`, used only if it exists |
| `JARVIS_LARGE_ARTIFACTS_BASE_URL` | Source for `large_artifacts.py fetch` | unset (no download) |

The external arsenal directory is written to only when the variable is set or the default directory already exists. `.env.example` documents every variable.

## 6. Large optional artifacts

`config/large-artifacts.json` lists three tracked files with their size, SHA-256, kind and purpose:

| Path | Kind | Used by |
| --- | --- | --- |
| `cache/starred_catalog.json` | `live` | Server arsenal views when no SQLite database is present |
| `index/conflicts.jsonl` | `live` | Generated record of namespace clashes; no tool in this checkout reads it |
| `docs/assets/cognitive-vault-graph-animation.mp4` | `static` | Linked from three documents |

```bash
python tooling/large_artifacts.py status            # which files are present and whether they match
python tooling/large_artifacts.py verify            # exit 1 only for a changed static artifact
python tooling/large_artifacts.py verify --require-all
python tooling/large_artifacts.py record            # re-record size and hash after a deliberate change
python tooling/large_artifacts.py fetch --base-url https://example.org/jarvis-artifacts
```

An absent file is acceptable: the Python battery, `--doctor` and `--test` pass without all three. A `live` cache that differs from the manifest is reported as rewritten, not as corruption.

`fetch` has no built-in source. It accepts `https://` (or loopback `http://`), refuses credentials, query strings and redirects to another scheme, downloads to a temporary file and installs it only when size and SHA-256 match the manifest. It never replaces an existing file without `--force`.

When neither a database nor the catalog exists, `GET /api/arsenal/stats` and `GET /api/arsenal/search` return `catalog_available: false` and the cockpit says the catalog is absent.

Limits: the files are still tracked and the history was not rewritten, so the clone size is unchanged. No download location has been published; `fetch` was exercised against a local test server only.

## 7. Repository contract validator

`python tooling/validate_repository_contracts.py --summary` runs seven offline checks with the standard library: `adapters`, `schema-instances`, `json-parse`, `agents`, `skills`, `python-compat` and `vault-links`. `--check <name>` runs one, `--strict` turns warnings into failures, and the exit code is `1` on failure.

A pass means those structural rules held for the checkout. It is not a security audit and not release evidence. The one standing warning is the frontmatter position of `skills/git-bugfix-contribution/SKILL.md`, whose hash is pinned by the v1.1.0 lockfiles; it is to be corrected together with the next release seal.

## 8. Stated figures

- `tooling/audit_documentation_claims.py` compares any stated number of canonical skills with the number of `skills/*/SKILL.md` files, in the governed documents and in `site/index.html`.
- The README states no repository count. `GET /api/arsenal/stats` reports the count of whichever source is loaded.
- `ui/index.html` ships placeholders. Benchmark, inventory and schedule values appear only after the corresponding API answers; a missing value renders as `n/d`.
- The site section formerly called a live simulator replays recorded output of five commands that exist in the checkout. A test fails if a replayed command names a missing file, flag or route.
- `tooling/jarvis_desktop.py` counts skills on disk and asks the local server for the catalog size.
- `tooling/build_site.py` holds an older template than the tracked page. It writes only when run with `--force`; importing it has no effect.

## 9. Line endings and release checksums

`.gitattributes` declares binary types and pins the line ending of the files whose bytes are recorded in `releases/*/checksums.sha256`. There is no global `* text=auto` rule, so no other file is renormalised.

On a checkout with LF line endings the recorded checksums that reproduce are 7 of 7 for v1.1.0 (previously 0), 14 of 21 for v1.0.0 (previously 2) and 1 of 2 for v2.0.0 (unchanged). The remaining v1.0.0 entries are six ledgers whose content changed after the seal and `index/capabilities.jsonl`, a live index left unpinned. Attributes cannot repair those.

## 10. Optional lint

`pyproject.toml` contains only `[tool.ruff]`. It adds no dependency and does not make the repository a package. `ruff check .` reports syntax errors, undefined names, redefinitions, unused imports, unused local variables and f-strings without placeholders, and currently reports nothing. The star re-exports in `memory.py`, `planner_resolver.py`, `runtime.py` and `runtime_adaptive_core.py` are deliberate and their rules stay disabled. Ruff is not installed by the project and its result is not validation evidence.

## 11. Test battery

`python jarvis.py --full-test` discovers every `tests/test_*.py`. Before this change it ran only `test_agentic_*.py`, which left twelve modules out. A run no longer rewrites the tracked benchmark reports or leaves `evidence.txt` at the root.

## Not covered

- The PowerShell layer (`tooling/*.ps1`, `tooling/*.psm1`, `tests/Invoke-*Tests.ps1`) was not changed or run. Of those files, 48 name a `C:\Users\<user>` path and 114 name `E:\.skill-registry`.
- Historical reports, staged plans and vault notes keep the paths and numbers they were written with.
- The personal tailnet hostname removed from `ui/index.html` is still present in the Git history of `main`.
