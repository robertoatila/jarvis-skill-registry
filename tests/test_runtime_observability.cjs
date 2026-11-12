const { test } = require('node:test');
const assert = require('node:assert/strict');
const {
  RuntimeObservabilityError,
  listMissions,
  getMissionSummary,
  getMissionTimeline
} = require('../ui/runtime-observability.js');

function response(payload, overrides = {}) {
  return {
    ok: true,
    status: 200,
    redirected: false,
    type: 'basic',
    async json() { return payload; },
    ...overrides
  };
}

const resources = {
  attempt_count: 1,
  tokens: { status: 'MEASURED', value: 8, unit: 'tokens' },
  cost_usd: { status: 'UNKNOWN', value: null, unit: 'USD' },
  latency_ms: { status: 'UNKNOWN', value: null, unit: 'ms' }
};

const verification = {
  count: 1,
  by_state: { VERIFIED: 1 },
  verification_rate: 1,
  verification_rate_status: 'MEASURED'
};

test('list missions uses fixed GET route without authorization leakage', async () => {
  let request;
  const payload = {
    missions: [{
      mission_id: 'mis-001',
      receipt_count: 3,
      last_event_utc: '2026-09-18T00:00:02+00:00'
    }],
    count: 1
  };
  const result = await listMissions(async (...args) => {
    request = args;
    return response(payload);
  });

  assert.deepEqual(result, payload);
  assert.equal(request[0], '/api/runtime/missions');
  assert.equal(request[1].method, 'GET');
  assert.equal(request[1].redirect, 'error');
  assert.equal(request[1].credentials, 'same-origin');
  assert.deepEqual(request[1].headers, { Accept: 'application/json' });
  assert.equal('Authorization' in request[1].headers, false);
  assert.equal('body' in request[1], false);
});

test('summary and timeline use encoded allowlisted mission ids only', async () => {
  const calls = [];
  const fetcher = async (path, options) => {
    calls.push([path, options]);
    if (path.endsWith('/summary')) {
      return response({
        mission_id: 'mis-abc:1',
        event_count: 3,
        resource_summary: resources,
        verification_summary: verification,
        unknown_fields: ['resources.cost_usd', 'resources.latency_ms']
      });
    }
    return response({
      mission_id: 'mis-abc:1',
      events: [{
        receipt_id: 'rcp-1',
        event_type: 'VERIFICATION',
        created_utc: '2026-09-18T00:00:02+00:00',
        task_id: 'tsk-1',
        attempt_id: 'att-1',
        trace_id: 'trc-1',
        data: { verification_state: 'VERIFIED', evidence_ids: ['ev-1'] }
      }],
      resource_summary: resources,
      verification_summary: verification,
      unknown_fields: ['resources.cost_usd', 'resources.latency_ms']
    });
  };

  await getMissionSummary('mis-abc:1', fetcher);
  await getMissionTimeline('mis-abc:1', fetcher);

  assert.equal(calls[0][0], '/api/runtime/missions/mis-abc%3A1/summary');
  assert.equal(calls[1][0], '/api/runtime/missions/mis-abc%3A1/timeline');
  for (const [, options] of calls) {
    assert.equal(options.method, 'GET');
    assert.equal(options.redirect, 'error');
    assert.equal(options.headers.Authorization, undefined);
  }
});

test('malformed mission ids reject before fetch', async () => {
  let calls = 0;
  const fetcher = async () => {
    calls++;
    throw new Error('must not fetch');
  };

  for (const id of ['', '../escape', 'mis/escape', 'space id', '%2e%2e', 'a'.repeat(129)]) {
    await assert.rejects(
      getMissionSummary(id, fetcher),
      error => error instanceof RuntimeObservabilityError &&
        error.code === 'INVALID_MISSION_ID'
    );
  }
  assert.equal(calls, 0);
});

test('redirects and non-success responses fail closed', async () => {
  await assert.rejects(
    listMissions(async () => response({}, { redirected: true })),
    error => error.code === 'REDIRECT_REJECTED'
  );
  await assert.rejects(
    listMissions(async () => response({}, { ok: false, status: 503 })),
    error => error.code === 'HTTP_503'
  );
  await assert.rejects(
    listMissions(async () => ({ ok: true, status: 200, json: null })),
    error => error.code === 'INVALID_RESPONSE'
  );
});

test('malformed mission list and summary payloads are rejected', async () => {
  await assert.rejects(
    listMissions(async () => response({ missions: [], count: 1 })),
    error => error.code === 'MALFORMED_MISSION_LIST'
  );
  await assert.rejects(
    getMissionSummary('mis-001', async () => response({
      mission_id: 'mis-other',
      event_count: 0,
      resource_summary: resources,
      verification_summary: verification,
      unknown_fields: []
    })),
    error => error.code === 'MISSION_ID_MISMATCH'
  );
  await assert.rejects(
    getMissionSummary('mis-001', async () => response({
      mission_id: 'mis-001',
      event_count: -1,
      resource_summary: resources,
      verification_summary: verification,
      unknown_fields: []
    })),
    error => error.code === 'MALFORMED_EVENT_COUNT'
  );
});

test('malformed timeline/resource/no-data semantics are rejected', async () => {
  await assert.rejects(
    getMissionTimeline('mis-001', async () => response({
      mission_id: 'mis-001',
      events: [{}],
      resource_summary: resources,
      verification_summary: verification,
      unknown_fields: []
    })),
    error => error.code === 'MALFORMED_TIMELINE_EVENT'
  );

  const badResources = {
    ...resources,
    cost_usd: { status: 'UNKNOWN', value: 0, unit: 'USD' }
  };
  await assert.rejects(
    getMissionSummary('mis-001', async () => response({
      mission_id: 'mis-001',
      event_count: 0,
      resource_summary: badResources,
      verification_summary: {
        count: 0,
        by_state: {},
        verification_rate: null,
        verification_rate_status: 'NO_DATA'
      },
      unknown_fields: ['resources.cost_usd', 'verification.rate']
    })),
    error => error.code === 'MALFORMED_RESOURCE_VALUE'
  );

  await assert.rejects(
    getMissionSummary('mis-001', async () => response({
      mission_id: 'mis-001',
      event_count: 0,
      resource_summary: resources,
      verification_summary: {
        count: 0,
        by_state: {},
        verification_rate: 1,
        verification_rate_status: 'NO_DATA'
      },
      unknown_fields: ['verification.rate']
    })),
    error => error.code === 'MALFORMED_VERIFICATION_RATE'
  );
});

const { describeBenchmarkReport } = require('../ui/runtime-observability.js');

test('benchmark display model shows only values present in the report payload', () => {
  const view = describeBenchmarkReport({
    status: 'REPORT_BACKED',
    sources: { headroom_source: 'benchmarks/token_benchmark_report.json' },
    token_compression: {
      compression_ratio: '22.1x',
      savings_pct: 95.48,
      monolithic_eager_tokens: 464389,
      active_working_tokens: 20987
    },
    micro_latencies: {
      wave_scheduling_ms: 0.0746,
      policy_evaluation_ms: 1.312,
      mission_planning_ms: 40.927,
      merkle_lockfile_ms: 19.8921
    },
    ide_governance: { free_headroom_pct: 95.48 },
    sqlite_arsenal: { total_repos: 74653, active_skills: 166 }
  });

  assert.equal(view.hasTokenReport, true);
  assert.equal(view.hasLatencyReport, true);
  assert.equal(view.ratio, '22.1x');
  assert.equal(view.wave, '75 µs');
  assert.equal(view.headroom, '95,48%');
  assert.equal(view.repos, '74.653');
  assert.equal(view.skillsDetail, 'Skills ativas: 166');
  assert.equal(view.tokenDetail, 'De 464.389 para 20.987 tokens');
  assert.equal(view.rowRatio, '22.1x (95,48%)');
  assert.equal(view.navBadge, '22.1x · 75 µs');
  assert.equal(view.latencies.wave, '0,0746 ms (75 µs)');
  assert.equal(view.latencies.merkle, '19,892 ms');
  assert.equal(view.bars.eagerWidthPct, 100);
  assert.ok(Math.abs(view.bars.workingWidthPct - (20987 / 464389) * 100) < 1e-9);
  assert.equal(view.headroomDetail, 'Fonte: benchmarks/token_benchmark_report.json');
  assert.equal(view.verdict, 'Lido dos relatórios locais');
});

test('benchmark display model never invents a figure for a missing report', () => {
  const emptyPayloads = [
    undefined,
    null,
    'not an object',
    {},
    {
      status: 'UNAVAILABLE',
      sources: { headroom_source: 'unknown' },
      token_compression: { compression_ratio: null, savings_pct: null },
      micro_latencies: { wave_scheduling_ms: null },
      ide_governance: { free_headroom_pct: null },
      sqlite_arsenal: { total_repos: null, active_skills: null }
    }
  ];
  for (const payload of emptyPayloads) {
    const view = describeBenchmarkReport(payload);
    assert.equal(view.hasTokenReport, false);
    assert.equal(view.hasLatencyReport, false);
    assert.equal(view.ratio, 'n/d');
    assert.equal(view.wave, 'n/d');
    assert.equal(view.headroom, 'n/d');
    assert.equal(view.repos, 'n/d');
    assert.equal(view.rowRatio, 'n/d');
    assert.equal(view.navBadge, '—');
    assert.equal(view.bars.workingWidthPct, 0);
    assert.equal(view.bars.eagerWidthPct, 0);
    assert.equal(view.verdict, 'Sem relatório carregado');
    // No text shown to the operator may carry a number.
    const texts = [];
    (function collect(value) {
      if (typeof value === 'string') texts.push(value);
      else if (value && typeof value === 'object') Object.values(value).forEach(collect);
    })(view);
    assert.ok(texts.length > 10);
    for (const text of texts) assert.doesNotMatch(text, /\d/);
  }
});

test('benchmark display model rejects non-numeric and malformed values', () => {
  const view = describeBenchmarkReport({
    token_compression: { compression_ratio: '  ', savings_pct: '97.51', monolithic_eager_tokens: 0, active_working_tokens: 10 },
    micro_latencies: { wave_scheduling_ms: '0.1246', policy_evaluation_ms: NaN, merkle_lockfile_ms: Infinity, mission_planning_ms: 12.5 },
    ide_governance: { free_headroom_pct: '90.1' },
    sqlite_arsenal: { total_repos: '42872' }
  });
  assert.equal(view.ratio, 'n/d');
  assert.equal(view.hasTokenReport, false);
  assert.equal(view.wave, 'n/d');
  assert.equal(view.headroom, 'n/d');
  assert.equal(view.repos, 'n/d');
  assert.equal(view.latencies.policy, 'n/d');
  assert.equal(view.latencies.merkle, 'n/d');
  assert.equal(view.latencies.planning, '12,5 ms');
  assert.equal(view.hasLatencyReport, true);
  assert.equal(view.verdict, 'Relatório parcial');
  // A zero baseline cannot produce a share.
  assert.equal(view.bars.workingWidthPct, 0);
  assert.equal(view.bars.workingLabel, '10 tokens');
});
