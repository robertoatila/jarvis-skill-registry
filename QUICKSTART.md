# J.A.R.V.I.S. Quickstart

This guide is the shortest supported path from a fresh checkout to the local HUD.

## Requirements

- Git
- Python 3.10+ (Python 3.12 recommended)
- A modern browser

The launcher itself uses only the Python standard library.

## 1. Clone

```bash
git clone https://github.com/robertoatila/jarvis-skill-registry.git
cd jarvis-skill-registry
```

## 2. Validate the checkout

```bash
python jarvis.py --doctor
```

Expected result: every local prerequisite is reported as `PASS`. This command does not make provider/network calls.

## 3. Launch

```bash
python jarvis.py
```

The launcher starts the existing server on `http://127.0.0.1:8899` and attempts to open the HUD in your default browser.

To use another port or skip browser opening:

```bash
python jarvis.py --port 9000 --no-browser
```

## Provider-backed chat

The HUD can load without a provider key. Provider-backed inference is a separate capability and requires explicit configuration/authorization.

Start from the checked-in examples instead of committing real credentials:

```bash
# Unix/macOS
cp config/api_keys.example.json config/api_keys.json
cp .env.example .env

# PowerShell
Copy-Item config/api_keys.example.json config/api_keys.json
Copy-Item .env.example .env
```

Review the active server/provider boundary before adding credentials: [docs/architecture/SERVER_INFERENCE_BOUNDARY.md](docs/architecture/SERVER_INFERENCE_BOUNDARY.md).

## Validate behavior

Fast server self-test:

```bash
python jarvis.py --test
```

Portable Python master battery:

```bash
python jarvis.py --full-test
```

Cross-platform support is established only by fresh direct reports from `python tooling/validate_v020_plan4.py --gate portable-runtime` on Windows, Linux and macOS. The older PowerShell governance/distribution stack still contains historical Windows path assumptions, so its compatibility evidence comes from `python tooling/validate_v020_plan4.py --gate legacy-governance` on Windows using the expected `E:\.skill-registry` layout. Workflow status is not validation evidence.

## What a successful first run proves

A successful launch proves that your checkout can start the local HUD/server boundary. It does **not** by itself prove:

- live provider connectivity;
- external mutations;
- browser rendering across all platforms;
- empirical model routing quality;
- full autonomous execution;
- production deployment readiness.

Those claims require their own evidence.

Current v0.2 machine status is recorded in [`evidence/current.json`](evidence/current.json). A component or harness being implemented does not make its gate PASS; use the direct gate runner and preserve the generated JSON report.

## Troubleshooting

### `Doctor failed`

Restore the missing checkout files and rerun:

```bash
python jarvis.py --doctor
```

### Port 8899 is already in use

```bash
python jarvis.py --port 8900
```

### HUD opens but provider chat is blocked

This can be expected when provider configuration or authorization is absent. Configure a supported provider explicitly; do not modify the runtime to silently bypass the boundary.

### Need a reproducible bug report

Open an issue and include:

- OS and Python version;
- exact command;
- expected behavior;
- actual behavior;
- minimal logs with credentials removed;
- whether `python jarvis.py --doctor` and `python jarvis.py --full-test` pass.
