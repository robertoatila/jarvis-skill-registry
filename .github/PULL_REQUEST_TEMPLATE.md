## 🎯 Pull Request Overview
A concise summary of the changes proposed in this PR.

## 🔗 Related Issues / Proposals
Closes #...

## 🛡️ Sovereign Security Protocol v13 (SSP-v13) Checklist
Please verify the following invariants before submitting:
- [ ] **SSP13-01 (Zero Secret Leakage)**: Verified that `python tooling/audit_pre_publish_security.py` returns Exit Code 0.
- [ ] **SSP13-02 (Merkle Integrity)**: Verified that existing canonical skill content hashes are unaltered or properly re-anchored.
- [ ] **SSP13-04 (Token Budget Defense)**: Frontmatter descriptions are $\le 15$ words with zero embedded shell scripts or bloat.
- [ ] **SSP13-06 (Path Anonymization)**: No hardcoded local host directories (`C:\Users\...`).
- [ ] **SSP13-09 (WCAG 2.1 AA)**: All UI / HUD changes maintain high contrast, semantic ARIA landmarks, and keyboard navigability.
- [ ] **SSP13-10 (Pre-Publish Gate)**: Self-test bootstrap passes: `pwsh -File ./tooling/Bootstrap.ps1`.

## 🧪 Verification & Test Results
```text
// Paste output of audit_pre_publish_security.py or test runner here
```
