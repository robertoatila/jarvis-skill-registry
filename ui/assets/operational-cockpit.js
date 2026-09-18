/* Receipt-driven Operational Cockpit. Structured evidence only; no synthetic progress. */
(function (root) {
  'use strict';

  function finiteNumber(value) {
    return typeof value === 'number' && Number.isFinite(value);
  }

  function formatNumber(value) {
    if (!finiteNumber(value)) return '—';
    return Number.isInteger(value) ? String(value) : String(Number(value.toFixed(3)));
  }

  function formatOperationalMeasurement(measurement) {
    const value = measurement && typeof measurement === 'object' ? measurement : {};
    const status = typeof value.status === 'string' ? value.status.toUpperCase() : 'UNKNOWN';
    const unit = typeof value.unit === 'string' && value.unit ? value.unit : 'valor';

    if (status === 'NOT_APPLICABLE') {
      return { display: 'N/A', status, accessible: `Não aplicável para ${unit}` };
    }
    if (status === 'UNKNOWN' || !finiteNumber(value.value)) {
      return { display: '—', status: status === 'NO_DATA' ? 'NO_DATA' : 'UNKNOWN', accessible: `Valor desconhecido para ${unit}` };
    }

    const display = formatNumber(value.value);
    const label = status === 'ESTIMATED' ? 'estimado' : status === 'PARTIAL' ? 'medição parcial' : 'medido';
    return { display, status, accessible: `${display} ${unit}, ${label}` };
  }

  function formatVerificationRate(summary) {
    if (!summary || summary.verification_rate_status === 'NO_DATA' || !finiteNumber(summary.verification_rate)) {
      return { display: '—', status: 'NO_DATA', accessible: 'Sem dados de verificação' };
    }
    const pct = summary.verification_rate * 100;
    const display = `${Number.isInteger(pct) ? pct : Number(pct.toFixed(1))}%`;
    return { display, status: 'MEASURED', accessible: `${display} de verificações confirmadas por receipts` };
  }

  function eventGroups(events) {
    const groups = {};
    for (const event of Array.isArray(events) ? events : []) {
      if (!event || typeof event !== 'object' || typeof event.event_type !== 'string') continue;
      const type = event.event_type.toUpperCase();
      (groups[type] ||= []).push(event);
    }
    return groups;
  }

  function observedTasks(events) {
    const tasks = new Map();
    for (const event of Array.isArray(events) ? events : []) {
      if (!event || typeof event.task_id !== 'string' || !event.task_id) continue;
      const item = tasks.get(event.task_id) || { taskId: event.task_id, eventCount: 0, eventTypes: [] };
      item.eventCount += 1;
      if (!item.eventTypes.includes(event.event_type)) item.eventTypes.push(event.event_type);
      tasks.set(event.task_id, item);
    }
    return [...tasks.values()].sort((a, b) => a.taskId.localeCompare(b.taskId));
  }

  function observedAttempts(events) {
    const attempts = new Map();
    for (const event of Array.isArray(events) ? events : []) {
      if (!event || typeof event.attempt_id !== 'string' || !event.attempt_id) continue;
      const current = attempts.get(event.attempt_id) || {
        attemptId: event.attempt_id,
        taskId: event.task_id || null,
        executionState: null,
        verificationState: null,
        recoveryState: null
      };
      const data = event.data && typeof event.data === 'object' ? event.data : {};
      if (event.event_type === 'EXECUTION' && typeof data.execution_state === 'string') current.executionState = data.execution_state;
      if (event.event_type === 'VERIFICATION' && typeof data.verification_state === 'string') current.verificationState = data.verification_state;
      if (event.event_type === 'RECOVERY' && typeof data.recovery_state === 'string') current.recoveryState = data.recovery_state;
      attempts.set(event.attempt_id, current);
    }
    return [...attempts.values()].sort((a, b) => a.attemptId.localeCompare(b.attemptId));
  }

  function deriveState(groups) {
    if ((groups.RECOVERY || []).some(event => {
      const state = event.data && event.data.recovery_state;
      return typeof state === 'string' && /RECONCILIATION|PENDING|AMBIGUOUS/i.test(state);
    })) return 'RECONCILIATION_PENDING';

    if ((groups.VERIFICATION || []).some(event => {
      const state = event.data && event.data.verification_state;
      return typeof state === 'string' && /REJECTED|FAILED|BLOCKED/i.test(state);
    })) return 'ATTENTION_REQUIRED';

    const verifications = groups.VERIFICATION || [];
    if (verifications.length && verifications.every(event => event.data && event.data.verification_state === 'VERIFIED')) {
      return 'VERIFIED';
    }
    if ((groups.EXECUTION || []).length) return 'EXECUTED_UNVERIFIED';
    if (Object.values(groups).some(values => values.length)) return 'OBSERVED';
    return 'NO_DATA';
  }

  function deriveOutcome(groups) {
    const decisions = groups.DECISION || [];
    for (let index = decisions.length - 1; index >= 0; index -= 1) {
      const outcome = decisions[index].data && decisions[index].data.actual_outcome;
      if (typeof outcome === 'string' && outcome.trim()) {
        return { display: outcome.trim(), accessible: `Resultado registrado em receipt: ${outcome.trim()}` };
      }
    }
    return { display: '—', accessible: 'Nenhum outcome autoritativo foi registrado nos receipts disponíveis' };
  }

  function mapContext(events) {
    return (events || []).map(event => {
      const data = event.data || {};
      return {
        receiptId: event.receipt_id,
        taskId: event.task_id || null,
        sources: Array.isArray(data.sources_loaded) ? data.sources_loaded.slice() : [],
        serializedBytes: finiteNumber(data.serialized_bytes) ? data.serialized_bytes : null,
        tokenEstimate: finiteNumber(data.token_estimate) ? data.token_estimate : null
      };
    });
  }

  function mapRouting(events) {
    return (events || []).map(event => {
      const data = event.data || {};
      return {
        receiptId: event.receipt_id,
        taskId: event.task_id || null,
        decisionType: data.decision_type || 'decision',
        selected: data.selected_candidate || null,
        candidates: Array.isArray(data.candidates) ? data.candidates.slice() : [],
        rejected: data.rejected_candidates && typeof data.rejected_candidates === 'object'
          ? { ...data.rejected_candidates } : {}
      };
    });
  }

  function mapVerification(events) {
    return (events || []).map(event => ({
      receiptId: event.receipt_id,
      attemptId: event.attempt_id || null,
      taskId: event.task_id || null,
      state: event.data && event.data.verification_state || 'UNKNOWN',
      evidenceIds: event.data && Array.isArray(event.data.evidence_ids) ? event.data.evidence_ids.slice() : []
    }));
  }

  function mapMemory(events) {
    return (events || []).map(event => ({
      receiptId: event.receipt_id,
      taskId: event.task_id || null,
      memoryId: event.data && event.data.memory_id || null,
      tier: event.data && event.data.tier || null,
      verificationState: event.data && event.data.verification_state || null,
      matchedItems: event.data && Array.isArray(event.data.matched_items) ? event.data.matched_items.slice() : []
    }));
  }

  function deriveOperationalCockpitModel(summary, timeline) {
    if (!summary || !timeline || summary.mission_id !== timeline.mission_id) {
      throw new Error('MISSION_OBSERVABILITY_MISMATCH');
    }
    const events = Array.isArray(timeline.events) ? timeline.events : [];
    const groups = eventGroups(events);
    const tasks = observedTasks(events);
    const attempts = observedAttempts(events);
    const verificationSummary = summary.verification_summary || {};
    const resourceSummary = summary.resource_summary || {};
    const verifiedCount = verificationSummary.by_state && Number.isInteger(verificationSummary.by_state.VERIFIED)
      ? verificationSummary.by_state.VERIFIED : 0;

    return {
      missionId: summary.mission_id,
      state: deriveState(groups),
      outcome: deriveOutcome(groups),
      tasks,
      attempts,
      context: mapContext(groups.CONTEXT),
      routing: mapRouting(groups.DECISION),
      verifications: mapVerification(groups.VERIFICATION),
      memory: mapMemory(groups.MEMORY),
      governor: (groups.GOVERNOR || []).map(event => ({ receiptId: event.receipt_id, data: { ...(event.data || {}) } })),
      effects: (groups.EFFECT || []).map(event => ({ receiptId: event.receipt_id, data: { ...(event.data || {}) } })),
      resources: {
        tokens: formatOperationalMeasurement(resourceSummary.tokens),
        costUsd: formatOperationalMeasurement(resourceSummary.cost_usd),
        latency: formatOperationalMeasurement(resourceSummary.latency_ms)
      },
      progression: {
        eventCount: Number.isInteger(summary.event_count) ? summary.event_count : events.length,
        taskCount: tasks.length,
        attemptCount: Number.isInteger(resourceSummary.attempt_count) ? resourceSummary.attempt_count : attempts.length,
        verificationCount: Number.isInteger(verificationSummary.count) ? verificationSummary.count : 0,
        verifiedCount,
        verificationRate: formatVerificationRate(verificationSummary)
      },
      unknownFields: Array.isArray(summary.unknown_fields) ? summary.unknown_fields.slice() : []
    };
  }

  function text(doc, id, value, accessible) {
    const node = doc.getElementById(id);
    if (!node) return;
    node.textContent = value;
    if (accessible) node.setAttribute('aria-label', accessible);
  }

  function clearList(doc, id, emptyText) {
    const node = doc.getElementById(id);
    if (!node) return null;
    node.replaceChildren();
    if (emptyText) {
      const empty = doc.createElement('div');
      empty.className = 'jv-empty is-empty';
      empty.textContent = emptyText;
      node.appendChild(empty);
    }
    return node;
  }

  function appendItem(doc, container, title, detail, state) {
    const item = doc.createElement('article');
    item.className = 'jv-cockpit-item';
    const heading = doc.createElement('strong');
    heading.className = 'jv-cockpit-item__title';
    heading.textContent = title;
    const meta = doc.createElement('span');
    meta.className = 'jv-cockpit-item__meta';
    meta.textContent = detail;
    item.append(heading, meta);
    if (state) {
      const badge = doc.createElement('span');
      badge.className = 'jv-status jv-status--info';
      badge.textContent = state;
      item.appendChild(badge);
    }
    container.appendChild(item);
  }

  function renderModel(doc, model) {
    const cockpit = doc.getElementById('operationalCockpit');
    if (cockpit && cockpit.classList) {
      cockpit.classList.toggle(
        'is-blocked',
        model.state === 'ATTENTION_REQUIRED' || model.state === 'RECONCILIATION_PENDING'
      );
    }
    text(doc, 'operationalMissionState', model.state, `Estado derivado de receipts: ${model.state}`);
    text(doc, 'operationalMissionOutcome', model.outcome.display, model.outcome.accessible);
    text(doc, 'operationalEventCount', String(model.progression.eventCount), `${model.progression.eventCount} eventos estruturados`);
    text(doc, 'operationalAttemptCount', String(model.progression.attemptCount), `${model.progression.attemptCount} tentativas observadas`);
    text(doc, 'operationalVerifiedCount', String(model.progression.verifiedCount), `${model.progression.verifiedCount} verificações VERIFIED`);
    text(doc, 'operationalVerificationRate', model.progression.verificationRate.display, model.progression.verificationRate.accessible);

    text(doc, 'operationalTokens', model.resources.tokens.display, model.resources.tokens.accessible);
    text(doc, 'operationalCost', model.resources.costUsd.display, model.resources.costUsd.accessible);
    text(doc, 'operationalLatency', model.resources.latency.display, model.resources.latency.accessible);

    let container = clearList(doc, 'operationalDAG', model.tasks.length ? '' : '— Nenhum task/DAG estruturado observado.');
    if (container) model.tasks.forEach(task => appendItem(doc, container, task.taskId, `${task.eventCount} eventos · ${task.eventTypes.join(', ')}`));

    container = clearList(doc, 'operationalAttemptsList', model.attempts.length ? '' : '— Nenhuma tentativa observada.');
    if (container) model.attempts.forEach(attempt => appendItem(
      doc, container, attempt.attemptId,
      `task ${attempt.taskId || '—'} · execução ${attempt.executionState || '—'} · verificação ${attempt.verificationState || '—'}`,
      attempt.recoveryState || null
    ));

    container = clearList(doc, 'operationalContextList', model.context.length ? '' : '— Nenhum ContextReceipt observado.');
    if (container) model.context.forEach(item => appendItem(
      doc, container, item.sources.join(', ') || 'Contexto sem fontes listadas',
      `${item.serializedBytes === null ? '—' : item.serializedBytes + ' B'} · tokens ${item.tokenEstimate === null ? '—' : item.tokenEstimate}`
    ));

    container = clearList(doc, 'operationalRoutingList', model.routing.length ? '' : '— Nenhum DecisionReceipt de routing observado.');
    if (container) model.routing.forEach(item => appendItem(
      doc, container, item.selected || '— sem seleção',
      `${item.decisionType} · candidatos ${item.candidates.length} · excluídos ${Object.keys(item.rejected).length}`
    ));

    container = clearList(doc, 'operationalVerificationList', model.verifications.length ? '' : '— Nenhuma verificação observada.');
    if (container) model.verifications.forEach(item => appendItem(
      doc, container, item.state,
      `attempt ${item.attemptId || '—'} · evidências ${item.evidenceIds.join(', ') || '—'}`
    ));

    container = clearList(doc, 'operationalMemoryList', model.memory.length ? '' : '— Nenhum evento de memória observado.');
    if (container) model.memory.forEach(item => appendItem(
      doc, container, item.memoryId || (item.matchedItems.join(', ') || 'MemoryReceipt'),
      `tier ${item.tier || '—'} · verificação ${item.verificationState || '—'}`
    ));

    const progression = doc.getElementById('operationalProgression');
    if (progression) {
      progression.textContent = `${model.progression.eventCount} eventos · ${model.progression.taskCount} tasks observadas · ${model.progression.verifiedCount}/${model.progression.verificationCount} verificações VERIFIED`;
      progression.setAttribute('aria-label', 'Progressão operacional derivada somente de receipts reais');
    }
  }

  function createController(options) {
    const doc = options && options.document;
    const client = options && options.client;
    const fetchImpl = options && options.fetchImpl;
    const onUpdate = options && typeof options.onUpdate === 'function' ? options.onUpdate : null;
    if (!doc || !client) throw new Error('COCKPIT_DEPENDENCY_MISSING');

    const select = doc.getElementById('operationalMissionSelect');
    const refreshButton = doc.getElementById('operationalRefresh');
    const status = doc.getElementById('operationalStatus');
    let currentMission = null;

    function setStatus(message, busy, error = false) {
      if (status) {
        status.textContent = message;
        if (status.classList) status.classList.toggle('is-error', Boolean(error));
      }
      const cockpit = doc.getElementById('operationalCockpit');
      if (cockpit) {
        cockpit.setAttribute('aria-busy', busy ? 'true' : 'false');
        if (cockpit.classList) {
          cockpit.classList.toggle('is-loading', Boolean(busy));
          cockpit.classList.toggle('is-error', Boolean(error));
        }
      }
    }

    async function loadMission(missionId) {
      if (!missionId) return null;
      setStatus('Carregando receipts da missão…', true);
      try {
        const [summary, timeline] = await Promise.all([
          client.getMissionSummary(missionId, fetchImpl),
          client.getMissionTimeline(missionId, fetchImpl)
        ]);
        const model = deriveOperationalCockpitModel(summary, timeline);
        currentMission = missionId;
        renderModel(doc, model);
        setStatus(`Missão ${missionId}: ${model.state}`, false);
        if (onUpdate) onUpdate(model);
        return model;
      } catch (error) {
        setStatus('Observabilidade indisponível; nenhum estado foi inferido.', false, true);
        throw error;
      }
    }

    async function refresh() {
      setStatus('Consultando missões persistidas…', true);
      try {
        const listing = await client.listMissions(fetchImpl);
        if (select) {
          const preferred = currentMission || select.value;
          select.replaceChildren();
          const placeholder = doc.createElement('option');
          placeholder.value = '';
          placeholder.textContent = listing.count ? 'Selecione uma missão' : 'Nenhuma missão observada';
          select.appendChild(placeholder);
          for (const mission of listing.missions) {
            const option = doc.createElement('option');
            option.value = mission.mission_id;
            option.textContent = `${mission.mission_id} · ${mission.receipt_count} receipts`;
            select.appendChild(option);
          }
          if (listing.missions.some(item => item.mission_id === preferred)) select.value = preferred;
          if (select.classList) select.classList.toggle('is-selected', Boolean(select.value));
        }
        setStatus(listing.count ? `${listing.count} missão(ões) com receipts persistidos.` : 'Nenhuma missão com receipts persistidos.', false);
        if (listing.count === 0) return null;
        const target = (select && select.value) || listing.missions[0].mission_id;
        if (select) {
          select.value = target;
          if (select.classList) select.classList.toggle('is-selected', Boolean(target));
        }
        return loadMission(target);
      } catch (error) {
        setStatus('Não foi possível consultar observabilidade do runtime.', false, true);
        throw error;
      }
    }

    function bind() {
      if (select) select.addEventListener('change', () => {
        if (select.value) loadMission(select.value).catch(() => {});
      });
      if (refreshButton) refreshButton.addEventListener('click', () => {
        refresh().catch(() => {});
      });
    }

    return Object.freeze({ bind, refresh, loadMission });
  }

  const api = Object.freeze({
    formatOperationalMeasurement,
    deriveOperationalCockpitModel,
    createController
  });

  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.JarvisOperationalCockpit = api;
})(globalThis);
