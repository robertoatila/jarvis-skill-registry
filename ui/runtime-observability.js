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

  const api = Object.freeze({
    RuntimeObservabilityError,
    listMissions,
    getMissionSummary,
    getMissionTimeline
  });

  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.JarvisRuntimeObservability = api;
})(globalThis);
