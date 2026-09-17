# 90-Second Demo Script

## Goal

Show one concrete reason to care about J.A.R.V.I.S.: the runtime should make agent decisions inspectable instead of presenting a black-box answer.

The recording must use real runtime output. If a segment is mocked, the frame must display `MOCK / TARGET BEHAVIOR` continuously.

> **Captured:** the evidence-backed public demo is generated from exact source commit `9bd059df24f0d4b9796045657ef207d0583eefb7`. See [DEMO_90S_EVIDENCE.md](DEMO_90S_EVIDENCE.md), the [82-second MP4](../assets/jarvis-demo-90s.mp4) and the [14-second README/social loop](../assets/jarvis-demo-loop.gif). The inference sequence is explicitly labeled as a deterministic local fixture backend; no live-provider execution is claimed.

## Setup

- Clean checkout of the exact release-candidate commit.
- `python jarvis.py --doctor` passes.
- Provider configuration is local and redacted from capture.
- Use a small public test repository or deterministic fixture; never use private code in the public demo.
- Terminal font and HUD zoom should remain readable on a phone.

## Timeline

### 0–8s — Hook

On screen:

> **AI agents can call tools. But who decides what context is worth paying for — and how do you know the result actually worked?**

Show the J.A.R.V.I.S. hero for no more than two seconds, then move immediately to execution.

### 8–18s — Start from zero

Terminal:

```bash
python jarvis.py --doctor
python jarvis.py
```

Show the HUD opening locally. Keep the local URL visible briefly.

Narration/caption:

> "J.A.R.V.I.S. is a local-first cognitive runtime. The launcher has no external Python dependency; provider execution is a separate, explicitly configured boundary."

### 18–30s — Give one mission

Use a mission whose result can be independently checked, for example:

> Analyze this fixture repository, identify the highest-confidence performance bottleneck, propose the smallest safe patch, run the relevant tests, and stop if the evidence is insufficient.

Do not use a vague "build me an app" demo. The point is decision quality and verification.

### 30–48s — Show selection, not chain-of-thought

Expose structured runtime decisions/receipts only:

```text
CONTEXT      selected paths / rejected expansion
SKILL        resolved capability
TOOL         selected adapter
MODEL        selected backend/profile
BUDGET       context / cost / latency constraints
AUTHORITY    allowed / blocked action classes
```

Do **not** display private reasoning. The demo should show inspectable decisions, contracts and evidence.

### 48–66s — Execute and verify

Show:

```text
EXECUTION    attempt id + observable action
EVIDENCE     tests / artifact / source inspection
VERIFY       VERIFIED | UNVERIFIED | BLOCKED
OUTCOME      useful result separated from command exit status
```

If verification fails, keep the failure in the demo. A truthful blocked/unverified outcome is stronger than a fake green result.

### 66–78s — Resource receipt

Show only metrics actually measured by the tagged build, for example:

```text
context admitted: <measured>
context rejected: <measured>
model/backend: <actual>
latency: <measured>
verification evidence: <count/type>
memory admission: <actual decision>
```

If token/cost savings are not instrumented yet, do not estimate them in the public demo.

### 78–90s — Close

Screen:

> **Execute less blindly. Verify more. Remember only what earned it.**

Then:

```text
github.com/robertoatila/jarvis-skill-registry
python jarvis.py
```

CTA:

> "Try the quickstart, break the assumptions, or contribute a skill/provider/benchmark."

## Capture checklist

- [x] Exact commit/tag visible in description.
- [x] No API keys, usernames, private paths or personal notifications on screen.
- [x] No simulated telemetry presented as real.
- [x] 1080p minimum.
- [x] Captions burned in.
- [x] First meaningful technical frame before 10 seconds.
- [x] Repository URL visible at the end.
- [x] Export a 10–20 second loop/GIF from the strongest decision → verification sequence for README/social use.

## Suggested title

**I built a cognitive runtime that makes AI agents justify context, tools and success**

## Suggested thumbnail text

**CAN YOUR AGENT PROVE IT WORKED?**
