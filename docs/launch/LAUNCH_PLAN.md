# Launch Plan — 1 Star to 100+

## Objective

Turn J.A.R.V.I.S. from an architecture-heavy repository into a project that a new developer can understand, run, verify and share in minutes.

The target is **100+ genuine GitHub stars from users who understand the project**, not star exchanges, purchased engagement or vanity traffic.

## Positioning

Primary promise:

> **A local-first cognitive runtime for AI agents: persistent memory, dynamic skills, bounded context, tool/model routing and verified execution.**

One-line problem statement:

> Most agents can call tools. J.A.R.V.I.S. is built to decide what context is worth loading, which capability should act, how much resource should be spent, how to verify success and what should be remembered afterward.

Primary differentiators to prove rather than merely claim:

1. Context is bounded/expanded deliberately instead of dumped wholesale.
2. Execution and verification are separate state dimensions.
3. Tool/model selection is policy/capability-aware.
4. Persistent memory carries provenance and admits only useful information.
5. Runtime attempts, evidence, costs and side effects can be inspected.

## Launch gates

Do not run a broad launch until the first six gates are green.

- [x] Public repository with visual identity and architecture diagrams.
- [x] Three-command onboarding path (`clone`, `cd`, `python jarvis.py`).
- [x] Local prerequisite doctor and server self-test path.
- [x] Explicit current-vs-planned capability boundary in README.
- [ ] CI green on the launch PR.
- [ ] Record a real 60–90 second demo; no simulated output presented as telemetry.
- [ ] Tag a release whose notes match the exact validated commit.
- [ ] Set the GitHub social preview to `.github/assets/jarvis-social-preview.png`.
- [ ] Set a public homepage/demo URL in repository metadata.
- [ ] Enable GitHub Discussions with Q&A / Ideas / Show-and-tell categories.
- [ ] Create at least 5 contributor-sized issues.
- [ ] Capture one benchmark that compares context/resource usage using a reproducible fixture.

## Product funnel

### Visitor → understands

The first README viewport must answer:

- What is this?
- Why should I care?
- Can I run it now?
- Is the autonomy real or aspirational?

Success signal: visitor reaches quickstart or architecture links instead of bouncing.

### Understands → runs

Target path:

```bash
git clone https://github.com/robertoatila/jarvis-skill-registry.git
cd jarvis-skill-registry
python jarvis.py
```

Success signal: local HUD opens; `python jarvis.py --doctor` passes.

### Runs → trusts

Expose:

- exact test command;
- current validated baseline;
- known gaps;
- architecture diagrams that distinguish tested, partial and planned scope.

Success signal: user can reproduce at least one validation path.

### Trusts → stars / contributes

Provide:

- concise contribution path;
- small issues;
- obvious skill/adapter/provider extension points;
- a public roadmap.

Success signal: stars, forks, issue comments, PRs and repeat visitors.

## Launch sequence

### D-7 to D-3 — proof and packaging

1. Merge the onboarding/positioning PR only after CI is green.
2. Record the 90-second demo in `DEMO_90S.md` using actual runtime output.
3. Produce one reproducible benchmark around context selection or verification overhead.
4. Prepare a release candidate and exact release notes.
5. Verify README rendering on desktop/mobile GitHub.
6. Set social preview/homepage metadata and enable Discussions.

### D-2 — contributor surface

Open narrowly scoped issues such as:

- first external provider fixture with deterministic mocked transport;
- macOS/Linux quickstart verification;
- context-budget benchmark fixture;
- first third-party skill contribution walkthrough;
- HUD screenshot/demo capture automation.

At least two should be suitable for a first-time contributor.

### D-1 — content staging

Prepare the launch posts from `LAUNCH_KIT.md`. Every post should lead with a problem/result, not "please star my repo".

Create one short GIF/clip for the README and social posts. Recommended visual sequence:

`prompt → context/tool/model decision → execution → verification → memory/resource receipt`.

### Launch day

Publish within a compact 4–8 hour window so discussion and traffic reinforce each other:

1. GitHub release.
2. Show HN.
3. X/Twitter thread.
4. LinkedIn technical post.
5. Relevant Reddit communities, adapted to each community's rules.
6. MCP / agent / local-LLM communities where self-promotion is explicitly allowed.

Reply to technical questions quickly and with evidence. Do not cross-post identical spam text.

### D+1 to D+7

- ship fixes raised by early users;
- quote real benchmark numbers only after reproduction;
- turn repeated questions into docs;
- highlight external contributions;
- publish one technical deep dive on context governance or verification semantics.

## Content angles

Use technical claims that are easy to understand and test:

- "Why an agent should justify every context expansion"
- "Execution succeeded is not the same as the task succeeded"
- "Persistent memory without provenance becomes a hallucination cache"
- "A cheap model should not be used because it is cheap; it should be used when the task contract allows it"
- "The control plane should spend tokens like a budget, not like an infinite buffer"

Avoid generic positioning such as "the most advanced agent framework" unless there is defensible comparative evidence.

## Metrics

Track weekly:

- GitHub unique visitors;
- clones;
- stars and star conversion from visitors;
- forks;
- unique contributors;
- issue/PR participation;
- demo views and click-through rate;
- quickstart failures reported;
- time from clone to first successful HUD launch.

Milestones:

| Stage | Target | Interpretation |
| --- | ---: | --- |
| Validation | 10 stars | people outside the author understand enough to care |
| Proof | 30 stars | demo/value proposition is shareable |
| Launch | 70 stars | distribution channels are working |
| Community | 100+ stars | project has repeatable discovery beyond the author's network |

## Stop conditions

Do not amplify the launch if any of these are true:

- quickstart is broken on the primary supported environment;
- demo uses fabricated telemetry without an explicit mock label;
- README claims functionality that the tagged release does not contain;
- CI is red;
- provider credentials or private data are required for the basic local experience;
- the first-time contributor path requires understanding the entire architecture.

Fix the funnel before buying attention with more distribution.
