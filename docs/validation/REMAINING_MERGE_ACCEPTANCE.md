# Remaining direct merge acceptance

GitHub Actions is not used. This checklist is a handoff, not passing evidence.
Run on dedicated clean checkouts; preserve existing work and device state.
Fetch the branch, record `git rev-parse HEAD`, and confirm the working tree is
clean before collecting evidence. Repeat acceptance if application code changes.

## PR #53 — physical Windows and paired phone

Branch: `feat/remote-pc-command-runtime`.
Last Linux-tested source: `a79a3f59b7370ccdfd7471ea16083bd768f5a092`.
Linux evidence does not certify Windows execution.

From the branch root on Windows, execute each command separately and stop if
its exit code is nonzero (`$LASTEXITCODE` in PowerShell):

```powershell
git rev-parse HEAD
git status --short
python tooling/validate_v020_plan4.py --gate portable-runtime --report reports/acceptance/portable-runtime-windows.json
python tooling/validate_v020_plan4.py --gate legacy-governance --report reports/acceptance/legacy-governance-windows.json
python -m unittest discover -s tests -p 'test_agentic_remote*.py' -v
node tests/remote_companion_node_test.js
python jarvis.py remote-doctor
```

The legacy gate refuses to overwrite an existing `E:\.skill-registry`.
Do not delete that directory to make the gate pass; use the supported checkout
or a machine with the required free path.

Continue with [Remote Second Brain](../REMOTE_SECOND_BRAIN.md) for explicit
Serve provisioning, resident service installation and pairing. These steps
change PC configuration and are not part of the automatic test commands above.

Record these actual observations with the tested commit and Windows version:

- Remote doctor readiness, verified Serve mapping and HKCU autostart.
- Pairing from the physical phone, without publishing the pairing URL or credential.
- A harmless command such as `python jarvis.py --doctor` requests approval;
  it executes only after the exact action digest is approved.
- A small task presents its plan before any write; approve the exact plan digest,
  then inspect the PC-side file changes and receipts.
- Repeating approval returns the stored receipt without repeating effects.
- Reopen/reconnect from the phone, then revoke the test device and confirm that
  its previous credential no longer authenticates.

Record failures as failures. A successful receipt alone does not prove that
all effects are correct. Keep raw pairing links, credentials and private source
out of published evidence. The PR remains draft until the physical flow passes.

## PR #56 — platform, browser and release evidence

Branch: `security/55-protocol-v13-2-intermediate`.
Last Linux-tested source: `1bdeca031f1882d4134e733660dec8a8f15bae74`.
Use a separate checkout from PR #53; its reports cannot certify this branch.

Run portable-runtime on Windows and macOS, and legacy-governance on Windows:

```powershell
python tooling/validate_v020_plan4.py --gate portable-runtime
python tooling/validate_v020_plan4.py --gate legacy-governance
```

Do not run the Windows-only legacy command on macOS. Default report filenames
include the platform. Preserve the generated JSON and its exact commit identity.

On a supported host with access to the pinned browser download:

```text
npm install --ignore-scripts --no-audit --no-fund --package-lock=false
npm run test:browser:install
python tooling/validate_v020_plan4.py --gate browser-ui
```

Stop if provisioning fails. Do not replace the pinned browser or edit a FAIL
report into PASS. In the current Linux environment the download returned a
195-byte HTML “Site Unavailable” page, not the required Chromium archive.

Collect the remaining release evidence required by `evidence/current.json` and
the canonical release procedure on the final candidate. Review the PARTIAL and
UNKNOWN boundaries in `SECURITY_AUDIT.md`. Passing the commands above alone does
not declare protocol Intermediário PASS or authorize release promotion.

## Return for review

Provide the generated gate reports plus the physical acceptance observations,
commit SHA, OS and runtime versions. Include failing reports and the stage that
failed. No credentials are needed. Reconcile branch changes and recheck the
final candidate before merging; do not reuse historical results for a new SHA.
