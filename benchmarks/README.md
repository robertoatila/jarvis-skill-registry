# Benchmarks

Benchmarks in this directory are intended to make narrow, reproducible claims. They are not marketing numbers.

## Context budget v1

Run:

```bash
python benchmarks/context_budget_benchmark.py
```

The fixture compares two representations of the same candidate context set:

1. a naive serialized envelope containing every fixture item;
2. the envelope admitted by `tooling.agentic.context_governor.compile_context` under a fixed byte budget.

The output reports:

- declared budget in bytes;
- naive serialized bytes;
- bounded serialized bytes;
- bytes not admitted;
- loaded and omitted sources;
- the selection reason and estimator recorded in the context receipt.

### Claim boundary

This benchmark measures **serialized UTF-8 bytes only**. It does not claim:

- provider-specific token counts;
- dollar savings;
- answer quality;
- latency improvement;
- superior model routing;
- end-to-end agent performance.

Those require separate instrumentation and fixtures.

### Pass conditions

The benchmark exits non-zero if:

- admitted context exceeds the declared budget;
- required mission context is not loaded;
- the fixture no longer demonstrates bounded admission compared with the naive envelope.

When publishing numbers, always record the exact git commit/tag and raw JSON output from that revision.
