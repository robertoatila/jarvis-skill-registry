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
