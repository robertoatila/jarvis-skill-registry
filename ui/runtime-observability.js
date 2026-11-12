/* Read-only runtime observability client. No chat/provider credentials are reused. */
(function (root) {
  'use strict';

  const MISSION_ID_RE = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/;

  class RuntimeObservabilityError extends Error {
    constructor(code, message) {
      super(message || code);
      this.name = 'RuntimeObservabilityError';
      this.code = code;
    }
  }

  function requireMissionId(id) {
    if (typeof id !== 'string' || !MISSION_ID_RE.test(id)) {
      throw new RuntimeObservabilityError('INVALID_MISSION_ID');
    }
    return id;
  }

  function requireFetch(fetchImpl) {
    if (typeof fetchImpl !== 'function') {
      throw new RuntimeObservabilityError('FETCH_UNAVAILABLE');
    }
    return fetchImpl;
  }

  function assertPlainObject(value, code) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) {
      throw new RuntimeObservabilityError(code);
    }
    return value;
  }

  function assertNonNegativeInteger(value, code) {
    if (!Number.isInteger(value) || value < 0) {
      throw new RuntimeObservabilityError(code);
    }
    return value;
  }

  function assertUnknownFields(value) {
    if (!Array.isArray(value) || value.some(item => typeof item !== 'string')) {
      throw new RuntimeObservabilityError('MALFORMED_UNKNOWN_FIELDS');
    }
    return value;
  }

  function assertResourceSummary(value) {
    const summary = assertPlainObject(value, 'MALFORMED_RESOURCE_SUMMARY');
    assertNonNegativeInteger(summary.attempt_count, 'MALFORMED_ATTEMPT_COUNT');
    for (const name of ['tokens', 'cost_usd', 'latency_ms']) {
      const metric = assertPlainObject(summary[name], 'MALFORMED_RESOURCE_METRIC');
      if (!['MEASURED', 'ESTIMATED', 'PARTIAL', 'NOT_APPLICABLE', 'UNKNOWN'].includes(metric.status)) {
        throw new RuntimeObservabilityError('MALFORMED_RESOURCE_STATUS');
      }
      if (typeof metric.unit !== 'string' || !metric.unit) {
        throw new RuntimeObservabilityError('MALFORMED_RESOURCE_UNIT');
      }
      if (metric.value !== null && (typeof metric.value !== 'number' || !Number.isFinite(metric.value))) {
        throw new RuntimeObservabilityError('MALFORMED_RESOURCE_VALUE');
      }
      if (['UNKNOWN', 'NOT_APPLICABLE'].includes(metric.status) && metric.value !== null) {
        throw new RuntimeObservabilityError('MALFORMED_RESOURCE_VALUE');
      }
    }
    return summary;
  }

  function assertVerificationSummary(value) {
    const summary = assertPlainObject(value, 'MALFORMED_VERIFICATION_SUMMARY');
    assertNonNegativeInteger(summary.count, 'MALFORMED_VERIFICATION_COUNT');
    const byState = assertPlainObject(summary.by_state, 'MALFORMED_VERIFICATION_STATES');
    for (const count of Object.values(byState)) {
      assertNonNegativeInteger(count, 'MALFORMED_VERIFICATION_STATE_COUNT');
    }
    if (!['MEASURED', 'NO_DATA'].includes(summary.verification_rate_status)) {
      throw new RuntimeObservabilityError('MALFORMED_VERIFICATION_RATE_STATUS');
    }
    if (summary.verification_rate_status === 'NO_DATA') {
      if (summary.verification_rate !== null || summary.count !== 0) {
        throw new RuntimeObservabilityError('MALFORMED_VERIFICATION_RATE');
      }
    } else if (
      typeof summary.verification_rate !== 'number' ||
      !Number.isFinite(summary.verification_rate) ||
      summary.verification_rate < 0 ||
      summary.verification_rate > 1
    ) {
      throw new RuntimeObservabilityError('MALFORMED_VERIFICATION_RATE');
    }
    return summary;
  }

  function assertTimelineEvent(value) {
    const event = assertPlainObject(value, 'MALFORMED_TIMELINE_EVENT');
    if (
      typeof event.receipt_id !== 'string' || !event.receipt_id ||
      typeof event.event_type !== 'string' || !event.event_type ||
      typeof event.created_utc !== 'string' || !event.created_utc
    ) {
      throw new RuntimeObservabilityError('MALFORMED_TIMELINE_EVENT');
    }
    assertPlainObject(event.data, 'MALFORMED_TIMELINE_EVENT_DATA');
    return event;
  }

  async function requestJson(path, fetchImpl) {
    const fetcher = requireFetch(fetchImpl);
    const response = await fetcher(path, {
      method: 'GET',
      redirect: 'error',
      credentials: 'same-origin',
      headers: { Accept: 'application/json' }
    });

    if (!response || typeof response !== 'object') {
      throw new RuntimeObservabilityError('INVALID_RESPONSE');
    }
    if (response.redirected === true || response.type === 'opaqueredirect') {
      throw new RuntimeObservabilityError('REDIRECT_REJECTED');
    }
    if (response.ok !== true) {
      const status = Number.isInteger(response.status) ? response.status : 0;
      throw new RuntimeObservabilityError(
        'HTTP_' + status,
        'Runtime observability request failed with HTTP ' + status
      );
    }
    if (typeof response.json !== 'function') {
      throw new RuntimeObservabilityError('INVALID_RESPONSE');
    }

    let payload;
    try {
      payload = await response.json();
    } catch (_) {
      throw new RuntimeObservabilityError('INVALID_JSON');
    }
    return assertPlainObject(payload, 'MALFORMED_PAYLOAD');
  }

  function validateMissionList(payload) {
    assertNonNegativeInteger(payload.count, 'MALFORMED_MISSION_COUNT');
    if (!Array.isArray(payload.missions) || payload.missions.length !== payload.count) {
      throw new RuntimeObservabilityError('MALFORMED_MISSION_LIST');
    }
    for (const mission of payload.missions) {
      assertPlainObject(mission, 'MALFORMED_MISSION');
      requireMissionId(mission.mission_id);
      assertNonNegativeInteger(mission.receipt_count, 'MALFORMED_RECEIPT_COUNT');
      if (
        mission.last_event_utc !== null &&
        (typeof mission.last_event_utc !== 'string' || !mission.last_event_utc)
      ) {
        throw new RuntimeObservabilityError('MALFORMED_LAST_EVENT');
      }
    }
    return payload;
  }

  function validateSummary(payload, id) {
    if (payload.mission_id !== id) {
      throw new RuntimeObservabilityError('MISSION_ID_MISMATCH');
    }
    assertNonNegativeInteger(payload.event_count, 'MALFORMED_EVENT_COUNT');
    assertResourceSummary(payload.resource_summary);
    assertVerificationSummary(payload.verification_summary);
    assertUnknownFields(payload.unknown_fields);
    return payload;
  }

  function validateTimeline(payload, id) {
    if (payload.mission_id !== id) {
      throw new RuntimeObservabilityError('MISSION_ID_MISMATCH');
    }
    if (!Array.isArray(payload.events)) {
      throw new RuntimeObservabilityError('MALFORMED_TIMELINE');
    }
    payload.events.forEach(assertTimelineEvent);
    assertResourceSummary(payload.resource_summary);
    assertVerificationSummary(payload.verification_summary);
    assertUnknownFields(payload.unknown_fields);
    return payload;
  }

  async function listMissions(fetchImpl = root.fetch) {
    return validateMissionList(
      await requestJson('/api/runtime/missions', fetchImpl)
    );
  }

  async function getMissionSummary(id, fetchImpl = root.fetch) {
    const missionId = requireMissionId(id);
    return validateSummary(
      await requestJson(
        '/api/runtime/missions/' + encodeURIComponent(missionId) + '/summary',
        fetchImpl
      ),
      missionId
    );
  }

  async function getMissionTimeline(id, fetchImpl = root.fetch) {
    const missionId = requireMissionId(id);
    return validateTimeline(
      await requestJson(
        '/api/runtime/missions/' + encodeURIComponent(missionId) + '/timeline',
        fetchImpl
      ),
      missionId
    );
  }

  const NOT_AVAILABLE = 'n/d';

  function finiteNumber(value) {
    return typeof value === 'number' && Number.isFinite(value) ? value : null;
  }

  function formatCount(value) {
    const number = finiteNumber(value);
    return number === null ? NOT_AVAILABLE : number.toLocaleString('pt-BR');
  }

  function formatMilliseconds(value) {
    const number = finiteNumber(value);
    if (number === null || number < 0) return NOT_AVAILABLE;
    if (number < 1) return `${number.toLocaleString('pt-BR', { maximumFractionDigits: 4 })} ms (${Math.round(number * 1000)} µs)`;
    return `${number.toLocaleString('pt-BR', { maximumFractionDigits: 3 })} ms`;
  }

  /*
   * Display model for GET /api/benchmarks/insane.  Every field is either a
   * value present in the payload or the literal "n/d": a missing report is
   * never replaced by a remembered or default figure.
   */
  function describeBenchmarkReport(payload) {
    const data = payload && typeof payload === 'object' ? payload : {};
    const token = data.token_compression && typeof data.token_compression === 'object' ? data.token_compression : {};
    const latency = data.micro_latencies && typeof data.micro_latencies === 'object' ? data.micro_latencies : {};
    const governance = data.ide_governance && typeof data.ide_governance === 'object' ? data.ide_governance : {};
    const arsenal = data.sqlite_arsenal && typeof data.sqlite_arsenal === 'object' ? data.sqlite_arsenal : {};
    const sources = data.sources && typeof data.sources === 'object' ? data.sources : {};

    const ratio = typeof token.compression_ratio === 'string' && token.compression_ratio.trim()
      ? token.compression_ratio.trim()
      : NOT_AVAILABLE;
    const savings = finiteNumber(token.savings_pct);
    const eager = finiteNumber(token.monolithic_eager_tokens);
    const working = finiteNumber(token.active_working_tokens);
    const hasTokenReport = ratio !== NOT_AVAILABLE && savings !== null;

    const wave = finiteNumber(latency.wave_scheduling_ms);
    const policy = finiteNumber(latency.policy_evaluation_ms);
    const merkle = finiteNumber(latency.merkle_lockfile_ms);
    const planning = finiteNumber(latency.mission_planning_ms);
    const hasLatencyReport = [wave, policy, merkle, planning].some((value) => value !== null);
    const waveShort = wave === null ? NOT_AVAILABLE : `${Math.round(wave * 1000)} µs`;

    const headroom = finiteNumber(governance.free_headroom_pct);
    const headroomSource = typeof sources.headroom_source === 'string' && sources.headroom_source !== 'unknown'
      ? sources.headroom_source
      : null;

    let workingShare = null;
    if (eager !== null && working !== null && eager > 0 && working >= 0) {
      workingShare = Math.min(100, (working / eager) * 100);
    }

    const tokenDetail = eager !== null && working !== null
      ? `De ${formatCount(eager)} para ${formatCount(working)} tokens`
      : 'Sem relatório carregado';
    const waveDetailParts = [];
    if (policy !== null) waveDetailParts.push(`Policy: ${formatMilliseconds(policy)}`);
    if (merkle !== null) waveDetailParts.push(`Merkle: ${formatMilliseconds(merkle)}`);

    let verdict = 'Sem relatório carregado';
    if (hasTokenReport && hasLatencyReport) verdict = 'Lido dos relatórios locais';
    else if (hasTokenReport || hasLatencyReport) verdict = 'Relatório parcial';

    return Object.freeze({
      hasTokenReport,
      hasLatencyReport,
      ratio,
      savingsLabel: savings === null
        ? 'Redução não informada'
        : `${savings.toLocaleString('pt-BR')}% de redução no relatório de tokens`,
      tokenDetail,
      wave: waveShort,
      waveDetail: waveDetailParts.length ? waveDetailParts.join(' | ') : 'Sem relatório carregado',
      headroom: headroom === null ? NOT_AVAILABLE : `${headroom.toLocaleString('pt-BR')}%`,
      headroomDetail: headroomSource ? `Fonte: ${headroomSource}` : 'Fonte não informada',
      repos: formatCount(arsenal.total_repos),
      skillsDetail: `Skills ativas: ${formatCount(arsenal.active_skills)}`,
      latencies: Object.freeze({
        wave: formatMilliseconds(wave),
        policy: formatMilliseconds(policy),
        merkle: formatMilliseconds(merkle),
        planning: formatMilliseconds(planning)
      }),
      bars: Object.freeze({
        workingLabel: working === null
          ? NOT_AVAILABLE
          : `${formatCount(working)} tokens${workingShare === null ? '' : ` (${workingShare.toLocaleString('pt-BR', { maximumFractionDigits: 2 })}%)`}`,
        workingWidthPct: workingShare === null ? 0 : workingShare,
        eagerLabel: eager === null ? NOT_AVAILABLE : `${formatCount(eager)} tokens (100%)`,
        eagerWidthPct: eager === null ? 0 : 100
      }),
      rowRatio: hasTokenReport ? `${ratio} (${savings.toLocaleString('pt-BR')}%)` : NOT_AVAILABLE,
      rowWave: wave === null ? NOT_AVAILABLE : `${waveShort} (local)`,
      navBadge: ratio === NOT_AVAILABLE && wave === null
        ? '—'
        : `${ratio} · ${waveShort}`,
      verdict
    });
  }

  const api = Object.freeze({
    RuntimeObservabilityError,
    listMissions,
    getMissionSummary,
    getMissionTimeline,
    describeBenchmarkReport
  });

  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.JarvisRuntimeObservability = api;
})(globalThis);
