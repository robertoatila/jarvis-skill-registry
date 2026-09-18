const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const {
  formatOperationalMeasurement,
  deriveOperationalCockpitModel
} = require('../ui/assets/operational-cockpit.js');

function fixture() {
  const summary = {
    mission_id: 'mis-cockpit',
    event_count: 8,
    resource_summary: {
      attempt_count: 2,
      tokens: { status: 'MEASURED', value: 0, unit: 'tokens' },
      cost_usd: { status: 'UNKNOWN', value: null, unit: 'USD' },
      latency_ms: { status: 'NOT_APPLICABLE', value: null, unit: 'ms' }
    },
    verification_summary: {
      count: 2,
      by_state: { VERIFIED: 1, REJECTED: 1 },
      verification_rate: 0.5,
      verification_rate_status: 'MEASURED'
    },
    unknown_fields: ['resources.cost_usd']
  };
  const timeline = {
    mission_id: 'mis-cockpit',
    events: [
      {
        receipt_id: 'ctx-1', event_type: 'CONTEXT',
        created_utc: '2026-09-18T00:00:00+00:00',
        task_id: 'tsk-a', attempt_id: null, trace_id: 'trc-a',
        data: { sources_loaded: ['README.md'], serialized_bytes: 512, token_estimate: null }
      },
      {
        receipt_id: 'dec-1', event_type: 'DECISION',
        created_utc: '2026-09-18T00:00:01+00:00',
        task_id: 'tsk-a', attempt_id: 'att-1', trace_id: 'trc-a',
        data: {
          decision_type: 'model_routing',
          candidates: ['local-a', 'cloud-b'],
          rejected_candidates: { 'cloud-b': 'LOCAL_ONLY' },
          selected_candidate: 'local-a'
        }
      },
      {
        receipt_id: 'exe-1', event_type: 'EXECUTION',
        created_utc: '2026-09-18T00:00:02+00:00',
        task_id: 'tsk-a', attempt_id: 'att-1', trace_id: 'trc-a',
        data: { adapter: 'inference:local-a', invocation_occurred: true, execution_state: 'FINISHED' }
      },
      {
        receipt_id: 'ver-1', event_type: 'VERIFICATION',
        created_utc: '2026-09-18T00:00:03+00:00',
        task_id: 'tsk-a', attempt_id: 'att-1', trace_id: 'trc-a',
        data: { verification_state: 'VERIFIED', evidence_ids: ['ev-1'] }
      },
      {
        receipt_id: 'exe-2', event_type: 'EXECUTION',
        created_utc: '2026-09-18T00:00:04+00:00',
        task_id: 'tsk-b', attempt_id: 'att-2', trace_id: 'trc-b',
        data: { adapter: 'local.read_file', invocation_occurred: true, execution_state: 'FINISHED' }
      },
      {
        receipt_id: 'rec-2', event_type: 'RECOVERY',
        created_utc: '2026-09-18T00:00:05+00:00',
        task_id: 'tsk-b', attempt_id: 'att-2', trace_id: 'trc-b',
        data: { recovery_state: 'RECONCILIATION_PENDING', retryable: false }
      },
      {
        receipt_id: 'ver-2', event_type: 'VERIFICATION',
        created_utc: '2026-09-18T00:00:06+00:00',
        task_id: 'tsk-b', attempt_id: 'att-2', trace_id: 'trc-b',
        data: { verification_state: 'REJECTED', evidence_ids: ['ev-2'] }
      },
      {
        receipt_id: 'mem-1', event_type: 'MEMORY',
        created_utc: '2026-09-18T00:00:07+00:00',
        task_id: 'tsk-a', attempt_id: 'att-1', trace_id: 'trc-a',
        data: { memory_id: 'mem-1', tier: 'semantic', verification_state: 'VERIFIED' }
      }
    ],
    resource_summary: summary.resource_summary,
    verification_summary: summary.verification_summary,
    unknown_fields: summary.unknown_fields
  };
  return { summary, timeline };
}

test('measurement formatter preserves zero, unknown and not-applicable semantics', () => {
  assert.deepEqual(
    formatOperationalMeasurement({ status: 'MEASURED', value: 0, unit: 'tokens' }),
    { display: '0', status: 'MEASURED', accessible: '0 tokens, medido' }
  );
  assert.deepEqual(
    formatOperationalMeasurement({ status: 'UNKNOWN', value: null, unit: 'USD' }),
    { display: '—', status: 'UNKNOWN', accessible: 'Valor desconhecido para USD' }
  );
  assert.deepEqual(
    formatOperationalMeasurement({ status: 'NOT_APPLICABLE', value: null, unit: 'ms' }),
    { display: 'N/A', status: 'NOT_APPLICABLE', accessible: 'Não aplicável para ms' }
  );
});

test('cockpit model is derived only from structured receipt evidence', () => {
  const { summary, timeline } = fixture();
  const model = deriveOperationalCockpitModel(summary, timeline);

  assert.equal(model.missionId, 'mis-cockpit');
  assert.equal(model.state, 'RECONCILIATION_PENDING');
  assert.equal(model.outcome.display, '—');
  assert.equal(model.tasks.length, 2);
  assert.deepEqual(model.tasks.map(item => item.taskId), ['tsk-a', 'tsk-b']);
  assert.equal(model.attempts.length, 2);
  assert.equal(model.context.length, 1);
  assert.equal(model.routing.length, 1);
  assert.equal(model.verifications.length, 2);
  assert.equal(model.memory.length, 1);
  assert.equal(model.progression.eventCount, 8);
  assert.equal(model.progression.verifiedCount, 1);
  assert.equal(model.progression.attemptCount, 2);
  assert.equal(model.resources.tokens.display, '0');
  assert.equal(model.resources.costUsd.display, '—');
  assert.equal(model.resources.latency.display, 'N/A');
});

test('empty evidence produces explicit no-data rather than fabricated progress', () => {
  const model = deriveOperationalCockpitModel({
    mission_id: 'mis-empty',
    event_count: 0,
    resource_summary: {
      attempt_count: 0,
      tokens: { status: 'UNKNOWN', value: null, unit: 'tokens' },
      cost_usd: { status: 'UNKNOWN', value: null, unit: 'USD' },
      latency_ms: { status: 'UNKNOWN', value: null, unit: 'ms' }
    },
    verification_summary: {
      count: 0,
      by_state: {},
      verification_rate: null,
      verification_rate_status: 'NO_DATA'
    },
    unknown_fields: ['verification.rate']
  }, {
    mission_id: 'mis-empty',
    events: [],
    resource_summary: {},
    verification_summary: {},
    unknown_fields: []
  });

  assert.equal(model.state, 'NO_DATA');
  assert.equal(model.outcome.display, '—');
  assert.equal(model.progression.eventCount, 0);
  assert.equal(model.progression.verificationRate.display, '—');
  assert.equal(model.progression.verificationRate.accessible, 'Sem dados de verificação');
});

test('operational cockpit markup exists inside preserved tabPipeline and loads bounded client first', () => {
  const html = fs.readFileSync(path.join(ROOT, 'ui/index.html'), 'utf8');
  for (const id of [
    'tabNeural', 'tabArsenal', 'tabIngest', 'tabSubagents',
    'tabSecurity', 'tabPipeline', 'tabObsidian',
    'operationalCockpit', 'operationalMissionSelect', 'operationalStatus',
    'operationalDAG', 'operationalAttemptsList', 'operationalContextList',
    'operationalRoutingList', 'operationalVerificationList',
    'operationalMemoryList', 'operationalResources', 'operationalProgression'
  ]) {
    assert.match(html, new RegExp('id="' + id + '"'));
  }
  const clientIndex = html.indexOf('<script src="runtime-observability.js"></script>');
  const cockpitIndex = html.indexOf('<script src="/assets/operational-cockpit.js"></script>');
  const jarvisIndex = html.indexOf('<script src="jarvis.js"></script>');
  assert.ok(clientIndex >= 0 && cockpitIndex > clientIndex && jarvisIndex > cockpitIndex);
});

test('legacy pipeline no longer fabricates PASS evidence on transport failure', () => {
  const source = fs.readFileSync(path.join(ROOT, 'ui/jarvis.js'), 'utf8');
  assert.doesNotMatch(source, /RESULTADO GERAL: 6\/6 GATES PASS/);
  assert.doesNotMatch(source, /Auditoria Forense: 6\/6 GATES PASS!/);
  assert.match(source, /UNVERIFIED/);
});

test('canonical cockpit CSS remains byte-identical to runtime mirror', () => {
  for (const name of ['components.css', 'patterns.css']) {
    assert.equal(
      fs.readFileSync(path.join(ROOT, 'design-system', name), 'utf8'),
      fs.readFileSync(path.join(ROOT, 'ui/assets/design-system', name), 'utf8')
    );
  }
});
