# Browser smoke test

The browser smoke suite uses Playwright only as a rendering/interaction harness.

It starts the actual stdlib JARVIS server on an ephemeral loopback port, seeds one
deterministic receipt ledger in a temporary state directory and verifies the
served HUD. It does not validate provider correctness, inference quality or
domain behavior.

Install the pinned test dependency and Chromium:

```bash
npm install
npm run test:browser:install
```

Run:

```bash
npm run test:browser
```

Generated Playwright output is ignored by Git.
