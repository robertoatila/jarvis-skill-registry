# Public Launch Kit

Use these as starting points. Adapt each post to the community and its rules; do not paste identical promotional text everywhere.

## Show HN

### Title

**Show HN: J.A.R.V.I.S. – a local-first cognitive runtime for verifiable AI agents**

### Body

I have been building J.A.R.V.I.S., a local-first runtime focused on the control plane around AI agents rather than another chat wrapper.

The problem I am trying to solve is that long-lived agents tend to accumulate context, hard-code tool/model choices, confuse execution with success, and turn memory into an unverified dump.

J.A.R.V.I.S. makes those concerns explicit: context admission, capability/tool/model selection, execution attempts, independent verification state, resource budgets and persistent memory with provenance.

The repository is still active development, so the README separates what exists today from the autonomous target. The current local foundation includes the skill registry, execution contracts/DAG, bounded inference, verification primitives, a local HUD and cognitive-vault tooling. The latest recorded local baseline before this launch work passed 283 Python tests across 42 suites plus 6 Node tests.

The new quickstart is intentionally small:

```bash
git clone https://github.com/robertoatila/jarvis-skill-registry.git
cd jarvis-skill-registry
python jarvis.py
```

I am especially interested in criticism around context governance, verification semantics and memory admission. What would you need to see measured before trusting an agent runtime like this?

Repo: https://github.com/robertoatila/jarvis-skill-registry

## Reddit — technical / Local LLM / agent communities

### Suggested title

**I’m building an agent runtime that separates “the tool ran” from “the task was actually verified”**

### Body

A failure mode I keep seeing in agent systems is that an exit code, API response or tool call gets treated as task success. Another is loading far more context than the current decision needs.

I’m building J.A.R.V.I.S. around explicit control-plane contracts: bounded context, capability-aware tool/model routing, durable execution attempts, independent verification/recovery/outcome states and persistent memory with provenance.

It is not “fully autonomous” yet and I am deliberately keeping that distinction visible in the README. The current local foundation can be run with:

```bash
git clone https://github.com/robertoatila/jarvis-skill-registry.git
cd jarvis-skill-registry
python jarvis.py
```

I would value technical feedback more than stars: which of these would you benchmark first — context selection, routing quality, verification reliability, memory retrieval or cost/latency?

Repo: https://github.com/robertoatila/jarvis-skill-registry

## X / Twitter — launch thread

### Post 1

AI agents can call tools.

The harder problem is deciding:
- what context is worth loading;
- which tool/model should act;
- whether the result actually worked;
- what deserves to be remembered.

I’m building J.A.R.V.I.S. around that control plane.

https://github.com/robertoatila/jarvis-skill-registry

### Post 2

The core rule: **execution is not verification**.

J.A.R.V.I.S. keeps execution state, verification state, recovery state and mission outcome separate. A command can exit 0 and the mission can still be unverified.

### Post 3

The second rule: context is a budget, not an infinite buffer.

The Context Governor direction is to expand information only when a task can justify the extra context, instead of dumping the whole repository into every turn.

### Post 4

Current state: skill registry + runtime contracts/DAG + bounded inference + verification primitives + local HUD + persistent-memory foundations.

The README explicitly labels partial/planned areas instead of pretending the whole autonomous target already exists.

### Post 5

Quickstart:

```bash
git clone https://github.com/robertoatila/jarvis-skill-registry.git
cd jarvis-skill-registry
python jarvis.py
```

If you work on agent runtimes, I’d rather get one hard architectural objection than 100 generic compliments.

## LinkedIn

### Post

Most AI-agent demos optimize for how much the agent can do. I have been working on the opposite question: **how much should an agent be allowed to do without evidence?**

J.A.R.V.I.S. is a local-first cognitive runtime built around five control-plane problems:

- context admission instead of unlimited context growth;
- capability-aware tool/model selection;
- durable execution attempts and side-effect records;
- verification that is independent from execution status;
- persistent memory with provenance instead of an unfiltered transcript dump.

The project is intentionally explicit about its current boundary. The full autonomous target is not complete. The repository already contains the governed skill registry, execution foundation, bounded inference, verification primitives, local HUD and cognitive-vault/memory foundations; the roadmap tracks the remaining integration and empirical validation work.

The quickstart is now three commands:

```bash
git clone https://github.com/robertoatila/jarvis-skill-registry.git
cd jarvis-skill-registry
python jarvis.py
```

The next public milestone is not “more features”. It is stronger evidence: real demo telemetry, reproducible context/resource benchmarks and external contributors who can challenge the assumptions.

Repository: https://github.com/robertoatila/jarvis-skill-registry

## Short Discord / community post

I’m building J.A.R.V.I.S., a local-first agent runtime focused on bounded context, tool/model routing, independent verification and persistent memory with provenance. The README now separates current behavior from the autonomous target, and the local HUD has a three-command quickstart. I’m looking for technical feedback on what benchmark would make the project most credible next: context savings, routing quality, verification reliability or memory retrieval. Repo: https://github.com/robertoatila/jarvis-skill-registry

## Response rules during launch

- Answer technical criticism with code/evidence, not defensiveness.
- Never ask people to trade stars.
- Never claim a benchmark before publishing the fixture and method.
- Convert repeated questions into README/FAQ changes within 24 hours when practical.
- Link directly to the relevant file/issue instead of replying with architecture buzzwords.
- If someone finds a real flaw, open an issue and credit them.
