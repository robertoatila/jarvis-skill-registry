# Direct Linux evidence — PR #56

Validated source commit: `a0c761a84b5b88add1ea7c2afd77208599733a05`.
Date: 2026-09-22. GitHub Actions was not used.

| Gate | Result | Commands |
| --- | --- | ---: |
| portable-runtime / Linux | PASS | 4 |
| contracts | PASS | 1 |
| integration | PASS | 4 |
| recovery | PASS | 2 |
| benchmarks-claims | PASS | 4 |
| browser-ui | FAIL — browser provisioning blocked | 1 |

The portable gate exercised the master battery, doctor, Python preflight and
actual loopback HUD startup through the quickstart verifier. Integration includes
Python deterministic-provider/HUD fixtures and the three Node contract suites.
Benchmark claims remain serialized UTF-8 byte measurements, not token/cost savings.

Playwright 1.63.0 installed successfully. Chromium 153.0.8010.12 / revision 1243
installation returned an invalid/truncated ZIP. A separate headless-only
installation attempt failed with the same ZIP error. Installer logs are included. The browser gate started the
fixture server but could not launch the missing browser executable. The FAIL report
is preserved: no UI behavior is certified by this attempt.

Reports bind the source commit above. The later evidence-only commit that stores
this directory is not itself represented as exact-HEAD runtime validation.
No application source or dependency pin changed. Windows, macOS, Windows legacy
governance, successful browser smoke, full release evidence and PR #53 physical
Windows acceptance remain pending. Do not declare protocol Intermediário PASS.

## Browser provisioning follow-up — 2026-09-22

A bounded HTTP check of the exact headless-shell installer URL
(`https://cdn.playwright.dev/builds/cft/153.0.8010.12/linux64/chrome-headless-shell-linux64.zip`)
returned HTTP 200 with `content-type: text/html` and `content-length: 195`.
The response body is an HTML page titled `Site Unavailable`, stating
`Unable to access this site.` It is not a ZIP archive. This explains the
installer's ZIP parsing failure in this environment; it does not establish
whether the upstream archive is corrupt or which network component served the page.

No browser was present at `/opt/google/chrome`, `/ms-playwright`,
`/root/.cache/ms-playwright`, `/usr/bin/chromium` or `/usr/bin/google-chrome`.
The check does not constitute an exhaustive filesystem search. No dependency
version, browser gate or application source was changed to obtain a passing result.
The browser gate remains FAIL until the pinned browser can be provisioned and
the smoke test actually completes. These are provisioning observations, not
new runtime validation of the evidence-only commits.
