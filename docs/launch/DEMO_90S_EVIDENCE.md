# J.A.R.V.I.S. 90-Second Demo Evidence

This page records the exact evidence used to render the public demo assets. The
video and GIF are generated from real local runtime/CI outputs; the inference
backend shown in the decision sequence is explicitly a deterministic local
fixture and is not presented as a live provider.

## Capture identity

- Demo: `jarvis-public-demo-90s-v1`
- Exact source commit: `9bd059df24f0d4b9796045657ef207d0583eefb7`
- Claim boundary: real local runtime receipts with deterministic fixture backend; no live provider, browser-rendering, quality, or dollar-savings claim
- Provider key required: **no**
- Live provider used: **no**

## Public quickstart

- `python jarvis.py --doctor`: **PASS**
- Local HUD: **HTTP 200**
- HUD URL used by verifier: `http://127.0.0.1:57975/`

## Structured runtime evidence

- Context benchmark: **4140 B naive → 2197 B admitted**, budget 2200 B.
- Context token estimate: **None** — no byte→token conversion is claimed.
- Skill resolver selected: `systematic-code-debugging`.
- Model router selected: `demo-local-fixture`.
- Governor action: `CONTINUE`.
- Inference execution receipt: `invocation_occurred=true`.
- Inference verification receipt: **VERIFIED**.
- Local adapter: `local.read_file`.
- Local verification: **VERIFIED**.

## Media outputs

- 82-second 1920×1080 MP4: [jarvis-demo-90s.mp4](../assets/jarvis-demo-90s.mp4)
- 14-second README/social loop: [jarvis-demo-loop.gif](../assets/jarvis-demo-loop.gif)

The rendered captions contain structured receipts and measured evidence only.
They do not expose or claim private chain-of-thought.
