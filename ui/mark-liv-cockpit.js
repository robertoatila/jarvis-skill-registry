(() => {
  'use strict';

  const REFRESH_MS = 5000;
  const MODULES = [
    { id: 'terminal', label: 'Terminal & Voice', meta: 'chat + voz', tab: 'tabNeural' },
    { id: 'dag', label: 'Mission DAG', meta: 'waves + receipts', tab: 'tabPipeline' },
    { id: 'skills', label: 'Arsenal', meta: 'skills canônicas', tab: 'tabArsenal' },
    { id: 'radar', label: 'Radar', meta: 'favoritos + 100k+', tab: 'tabIngest' },
    { id: 'memory', label: 'Hipocampo', meta: 'memória + Obsidian', tab: 'tabObsidian' },
    { id: 'telemetry', label: 'Mark-LIV', meta: 'telemetria host', scroll: 'markLivTelemetryCluster' }
  ];

  const state = {
    status: null,
    hardware: null,
    telemetry: null,
    keys: null,
    memory: null,
    dag: null,
    receipts: null,
    lastRefresh: null
  };

  function el(id) {
    return document.getElementById(id);
  }

  function finite(value) {
    return typeof value === 'number' && Number.isFinite(value);
  }

  function hasFiniteNumber(value) {
    return value !== null
      && value !== undefined
      && value !== ''
      && Number.isFinite(Number(value));
  }

  function clampPct(value) {
    const numeric = Number(value);
    return Number.isFinite(numeric) ? Math.max(0, Math.min(100, numeric)) : 0;
  }

  function text(target, value, fallback = '—') {
    const node = typeof target === 'string' ? el(target) : target;
    if (!node) return;
    const normalized = value === null || value === undefined || value === '' ? fallback : String(value);
    node.textContent = normalized;
  }

  function shortHash(value) {
    if (typeof value !== 'string' || !value.trim()) return '—';
    const clean = value.trim();
    return clean.length > 14 ? `${clean.slice(0, 7)}…${clean.slice(-5)}` : clean;
  }

  function protocolLabel(value) {
    const raw = String(value || '').trim();
    if (!raw) return 'PROTOCOLO —';
    return raw
      .replace(/^SOVEREIGN_SECURITY_PROTOCOL_/i, 'SSP-')
      .replaceAll('_', ' ');
  }

  function renderTrustBadge() {
    const protocol = state.hardware && state.hardware.protocol;
    const governance = state.status && state.status.governance_status;
    const hash = state.status && state.status.canonical_merkle_root;
    const sealed = typeof governance === 'string' && /sealed/i.test(governance);
    text('markLivGovernance', `${protocolLabel(protocol)}${sealed ? ' · SEALED' : ''}`);
    text('markLivIntegrityHash', shortHash(hash), 'hash —');
    const badge = el('markLivGovernanceBadge');
    if (badge) {
      badge.title = `${protocolLabel(protocol)} // ${governance || 'governance —'} // Merkle ${hash || '—'}`;
      badge.classList.toggle('mark-liv-offline', Boolean(governance && !sealed));
    }
  }

  async function fetchJson(path) {
    const response = await fetch(path, { headers: { Accept: 'application/json' } });
    if (!response.ok) throw new Error(`${path} -> HTTP ${response.status}`);
    return response.json();
  }

  function cockpitMarkup() {
    const modules = MODULES.map((module) => `
      <button class="mark-liv-module" type="button" data-mark-module="${module.id}" data-mark-tab="${module.tab || ''}" data-mark-scroll="${module.scroll || ''}">
        <strong>${module.label}</strong>
        <span>${module.meta}</span>
      </button>
    `).join('');

    return `
      <section class="mark-liv-cockpit" id="markLivCockpit" aria-label="J.A.R.V.I.S. Mark-LIV Holomat Quantum Cockpit">
        <div class="mark-liv-command-strip">
          <div class="mark-liv-brand">
            <div class="mark-liv-brand__mark" aria-hidden="true">LIV</div>
            <div class="mark-liv-brand__title">
              <span class="mark-liv-brand__eyebrow">HOLOMAT QUANTUM COCKPIT // LIVE RUNTIME</span>
              <strong>J.A.R.V.I.S. MARK-LIV</strong>
            </div>
          </div>
          <div class="mark-liv-badge" data-tone="green" id="markLivGovernanceBadge">
            <span class="mark-liv-dot"></span>
            <span id="markLivGovernance">PROTOCOLO —</span>
            <span class="mark-liv-badge__hash" id="markLivIntegrityHash">hash —</span>
          </div>
          <div class="mark-liv-badge" id="markLivSkillBadge">
            <span id="markLivSkillCount">—</span><span>SKILLS</span>
          </div>
          <div class="mark-liv-badge" data-tone="amber" id="markLivRepoBadge">
            <span id="markLivRepoCount">—</span><span>REPOS</span>
          </div>
          <div class="mark-liv-voice-controls" aria-label="Controles rápidos de voz">
            <label for="markLivVoiceProfile">VOZ</label>
            <select id="markLivVoiceProfile" aria-label="Perfil rápido de voz">
              <option value="british">EN-GB</option>
              <option value="us_male">EN-US</option>
              <option value="pt_natural">PT-BR</option>
              <option value="muted">MUDO</option>
            </select>
            <button type="button" id="markLivMicButton" aria-pressed="false" title="Ditado por microfone; o texto não é enviado automaticamente">MIC</button>
          </div>
        </div>

        <div class="mark-liv-phase-rail" id="markLivPhaseRail" aria-label="Quatro fases operacionais">
          <div class="mark-liv-phase" data-phase="decompose">
            <span class="mark-liv-phase__index">01</span>
            <span class="mark-liv-phase__copy"><strong>DECOMPOSIÇÃO</strong><span>aguardando DAG</span></span>
          </div>
          <div class="mark-liv-phase" data-phase="skills">
            <span class="mark-liv-phase__index">02</span>
            <span class="mark-liv-phase__copy"><strong>SELEÇÃO DE SKILLS</strong><span>aguardando catálogo</span></span>
          </div>
          <div class="mark-liv-phase" data-phase="execute">
            <span class="mark-liv-phase__index">03</span>
            <span class="mark-liv-phase__copy"><strong>EXECUÇÃO GOVERNADA</strong><span>aguardando runtime</span></span>
          </div>
          <div class="mark-liv-phase" data-phase="synthesis">
            <span class="mark-liv-phase__index">04</span>
            <span class="mark-liv-phase__copy"><strong>SÍNTESE</strong><span>aguardando evidence</span></span>
          </div>
        </div>

        <div class="mark-liv-grid">
          <article class="mark-liv-reactor-card">
            <span class="mark-liv-kicker">ARC REACTOR // SOVEREIGN CORE</span>
            <div class="mark-liv-reactor" aria-hidden="true">
              <div class="mark-liv-reactor__core">ONLINE</div>
            </div>
            <div class="mark-liv-reactor-meta">
              <div class="mark-liv-mini-stat"><span>MERKLE</span><strong id="markLivMerkle">—</strong></div>
              <div class="mark-liv-mini-stat"><span>UPTIME</span><strong id="markLivUptime">—</strong></div>
              <div class="mark-liv-mini-stat"><span>BACKEND</span><strong id="markLivBackend">—</strong></div>
              <div class="mark-liv-mini-stat"><span>ARMOR</span><strong id="markLivArmorIntegrity">—</strong></div>
              <div class="mark-liv-mini-stat" id="markLivPowerStat"><span>POWER</span><strong id="markLivPower">—</strong></div>
              <div class="mark-liv-mini-stat"><span>VOICE</span>
                <div class="mark-liv-voice-wave" id="markLivVoiceWave" aria-label="Indicador visual de voz">
                  ${'<i></i>'.repeat(12)}
                </div>
              </div>
            </div>
          </article>

          <article class="mark-liv-intel-panel">
            <div class="mark-liv-router">
              <div>
                <span class="mark-liv-kicker">OMNIROUTE // MOTOR DE INFERÊNCIA</span>
                <strong id="markLivProvider">NÃO CONFIGURADO</strong>
                <span id="markLivProviderMeta">carregando configuração do host</span>
              </div>
              <div class="mark-liv-mini-stat">
                <span>LATÊNCIA OBSERVADA</span>
                <strong id="markLivLatency">—</strong>
              </div>
            </div>

            <div class="mark-liv-context-meter">
              <div class="mark-liv-context-meter__labels">
                <span>CONTEXT ANTI-ROT // USO MEDIDO</span>
                <span id="markLivContextLabel">—</span>
              </div>
              <div class="mark-liv-context-meter__track" aria-hidden="true">
                <div class="mark-liv-context-meter__fill" id="markLivContextFill"></div>
              </div>
              <div class="mark-liv-context-meter__labels">
                <span id="markLivContextUsed">—</span>
                <span id="markLivContextHeadroom">—</span>
              </div>
            </div>

            <div class="mark-liv-dag-mini" aria-label="Prévia do Mission DAG">
              <svg id="markLivDagSvg" viewBox="0 0 640 180" role="img" aria-label="Grafo de missão J.A.R.V.I.S."></svg>
            </div>
          </article>

          <article class="mark-liv-telemetry-cluster" id="markLivTelemetryCluster">
            <span class="mark-liv-kicker">MARK-LIV ARMOR TELEMETRY // HOST</span>
            <div class="mark-liv-gauges">
              <div class="mark-liv-gauge" id="markLivCpuGauge"><div class="mark-liv-gauge__copy"><strong id="markLivCpu">—</strong><span>CPU</span></div></div>
              <div class="mark-liv-gauge" id="markLivRamGauge"><div class="mark-liv-gauge__copy"><strong id="markLivRam">—</strong><span>RAM</span></div></div>
              <div class="mark-liv-gauge" data-tone="amber" id="markLivDiskGauge"><div class="mark-liv-gauge__copy"><strong id="markLivDisk">—</strong><span>DISCO</span></div></div>
              <div class="mark-liv-gauge" data-mode="count" id="markLivThreadsGauge"><div class="mark-liv-gauge__copy"><strong id="markLivThreads">—</strong><span>THREADS</span></div></div>
              <div class="mark-liv-gauge" data-mode="unavailable" id="markLivTempGauge"><div class="mark-liv-gauge__copy"><strong id="markLivTemp">—</strong><span>TEMP</span></div></div>
              <div class="mark-liv-gauge" id="markLivContextGauge"><div class="mark-liv-gauge__copy"><strong id="markLivContextGaugeValue">—</strong><span>CONTEXTO</span></div></div>
            </div>
            <div class="mark-liv-subsystems" id="markLivSubsystems">
              <div class="mark-liv-subsystem"><span>TELEMETRIA</span><strong>AGUARDANDO</strong></div>
            </div>
          </article>
        </div>

        <nav class="mark-liv-module-deck" aria-label="Módulos do Holomat Mark-LIV">
          ${modules}
        </nav>

        <div class="mark-liv-lower-grid">
          <article class="mark-liv-dag-panel">
            <span class="mark-liv-kicker">MISSION DAG & WAVE STUDIO</span>
            <div class="mark-liv-reactor-meta" style="margin-top:.55rem">
              <div class="mark-liv-mini-stat"><span>MISSÃO</span><strong id="markLivMissionId">—</strong></div>
              <div class="mark-liv-mini-stat"><span>WAVES</span><strong id="markLivWaveCount">—</strong></div>
              <div class="mark-liv-mini-stat"><span>NÓS</span><strong id="markLivNodeCount">—</strong></div>
              <div class="mark-liv-mini-stat"><span>TELEMETRIA</span><strong id="markLivSpanCount">—</strong></div>
            </div>
            <div class="mark-liv-wave-strip" id="markLivWaveStrip" aria-label="Waves da missão"></div>
            <div class="mark-liv-dag-detail" id="markLivDagDetail" aria-live="polite">
              Selecione um nó do DAG para inspecionar estado, agente, dependências e evidência.
            </div>
            <div class="mark-liv-receipts" id="markLivReceipts" aria-label="Receipts recentes">
              <div class="mark-liv-receipt">Sem receipts persistidos carregados.</div>
            </div>
          </article>

          <article class="mark-liv-memory-panel">
            <span class="mark-liv-kicker">HIPOCAMPO // MEMORY RECALL STREAM</span>
            <div class="mark-liv-memory-feed" id="markLivMemoryFeed">
              <div class="mark-liv-memory-item">Aguardando memória persistente do host.</div>
            </div>
          </article>
        </div>
      </section>

      <aside class="mark-liv-dock" id="markLivDock" aria-label="Ações rápidas Mark-LIV">
        <button type="button" data-mark-action="remote" title="Remote Mobile Companion">QR</button>
        <button type="button" data-mark-action="ingest" title="Ingestão / Radar">IN</button>
        <button type="button" data-mark-action="audit" title="Auditoria / Missões">AU</button>
        <button type="button" data-mark-action="obsidian" title="Cofre Obsidian">OB</button>
        <button type="button" data-mark-action="fullscreen" title="Modo Standalone / Fullscreen">F11</button>
      </aside>
    `;
  }

  function mount() {
    if (el('markLivCockpit')) return;
    const header = el('jarvisHeader');
    if (!header || !header.parentNode) return;

    const wrapper = document.createElement('div');
    wrapper.innerHTML = cockpitMarkup();
    const cockpit = wrapper.firstElementChild;
    const dock = wrapper.lastElementChild;
    header.insertAdjacentElement('afterend', cockpit);
    document.body.appendChild(dock);

    const title = document.querySelector('.header-main-title');
    if (title) title.innerHTML = 'J.A.R.V.I.S. <span class="highlight-cyan">MARK-LIV</span>';
    const sup = document.querySelector('.header-sup');
    if (sup) sup.textContent = 'HOLOMAT QUANTUM COCKPIT // COGNITIVE RUNTIME';

    bindModules();
    bindDock();
    bindVoiceControls();
    syncVoiceState();
  }

  function activateTab(tabId) {
    if (!tabId) return;
    const source = document.querySelector(`.nav-tab[data-tab="${tabId}"]`);
    if (source) {
      source.click();
      source.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }

  function bindModules() {
    document.querySelectorAll('[data-mark-module]').forEach((button) => {
      button.addEventListener('click', () => {
        document.querySelectorAll('[data-mark-module]').forEach((item) => item.classList.remove('is-active'));
        button.classList.add('is-active');
        const tab = button.getAttribute('data-mark-tab');
        const scroll = button.getAttribute('data-mark-scroll');
        if (tab) activateTab(tab);
        if (scroll && el(scroll)) el(scroll).scrollIntoView({ behavior: 'smooth', block: 'center' });
      });
    });
  }

  function bindDock() {
    const dock = el('markLivDock');
    if (!dock) return;
    dock.addEventListener('click', async (event) => {
      const button = event.target.closest('[data-mark-action]');
      if (!button) return;
      const action = button.dataset.markAction;
      if (action === 'remote') {
        const existing = el('btnMobileCompanion');
        if (existing) existing.click();
      } else if (action === 'ingest') {
        activateTab('tabIngest');
        const input = el('inputRepoUrl');
        if (input) input.focus();
      } else if (action === 'audit') {
        activateTab('tabPipeline');
        const auditButton = el('btnRunMasterPipeline');
        if (auditButton && !auditButton.disabled) auditButton.click();
      } else if (action === 'obsidian') {
        activateTab('tabObsidian');
        const syncButton = el('btnSyncObsidianVault');
        if (syncButton && !syncButton.disabled) syncButton.click();
      } else if (action === 'fullscreen') {
        try {
          if (document.fullscreenElement) await document.exitFullscreen();
          else if (document.documentElement.requestFullscreen) await document.documentElement.requestFullscreen();
        } catch (_) {}
      }
    });
  }

  function bindVoiceControls() {
    const quickProfile = el('markLivVoiceProfile');
    const sourceProfile = el('selectVoiceProfile');
    const micButton = el('markLivMicButton');
    const composer = el('neuralInputMsg');
    const wave = el('markLivVoiceWave');

    if (quickProfile && sourceProfile) {
      quickProfile.value = sourceProfile.value || 'british';
      quickProfile.addEventListener('change', () => {
        sourceProfile.value = quickProfile.value;
        sourceProfile.dispatchEvent(new Event('change', { bubbles: true }));
      });
      sourceProfile.addEventListener('change', () => {
        quickProfile.value = sourceProfile.value || 'british';
      });
    }

    if (!micButton) return;
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      micButton.disabled = true;
      micButton.title = 'Reconhecimento de voz indisponível neste navegador';
      return;
    }

    let recognition = null;
    let listening = false;

    const setListening = (value) => {
      listening = Boolean(value);
      micButton.setAttribute('aria-pressed', String(listening));
      micButton.textContent = listening ? 'STOP' : 'MIC';
      micButton.classList.toggle('is-active', listening);
      if (wave) wave.classList.toggle('is-listening', listening);
    };

    micButton.addEventListener('click', () => {
      if (listening && recognition) {
        recognition.stop();
        return;
      }

      recognition = new Recognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      const profile = quickProfile ? quickProfile.value : 'british';
      recognition.lang = profile === 'pt_natural' ? 'pt-BR' : (profile === 'british' ? 'en-GB' : 'en-US');
      recognition.addEventListener('start', () => setListening(true), { once: true });
      recognition.addEventListener('end', () => setListening(false), { once: true });
      recognition.addEventListener('error', () => setListening(false), { once: true });
      recognition.addEventListener('result', (event) => {
        const result = event.results && event.results[0] && event.results[0][0];
        const transcript = result && typeof result.transcript === 'string' ? result.transcript.trim() : '';
        if (!transcript || !composer) return;
        composer.value = transcript;
        composer.dispatchEvent(new Event('input', { bubbles: true }));
        composer.focus();
      });
      try {
        recognition.start();
      } catch (_) {
        setListening(false);
      }
    });
  }

  function syncVoiceState() {
    const wave = el('markLivVoiceWave');
    const source = el('valVoiceState');
    if (!wave || !source) return;

    const applyAvailability = () => {
      const enabled = !/muda|muted|off|inativ/i.test(source.textContent || '');
      wave.classList.toggle('is-disabled', !enabled);
    };
    applyAvailability();
    new MutationObserver(applyAvailability).observe(source, {
      childList: true,
      subtree: true,
      characterData: true
    });

    document.addEventListener('jarvis:voice-speaking', (event) => {
      const speaking = Boolean(event.detail && event.detail.speaking);
      wave.classList.toggle('is-speaking', speaking);
    });
  }

  function setGauge(id, value) {
    const gauge = el(id);
    if (gauge) gauge.style.setProperty('--gauge-value', String(clampPct(value)));
  }

  function renderStatus(data) {
    if (!data || typeof data !== 'object') return;
    state.status = data;
    renderTrustBadge();
    text('markLivSkillCount', Number.isFinite(Number(data.canonical_active_skills_count))
      ? Number(data.canonical_active_skills_count).toLocaleString('pt-BR') : '—');
    text('markLivRepoCount', Number.isFinite(Number(data.total_starred_catalog_count))
      ? Number(data.total_starred_catalog_count).toLocaleString('pt-BR') : '—');
    text('markLivMerkle', shortHash(data.canonical_merkle_root));
    text('markLivBackend', data.backend_engine || 'Python runtime');

    const tg = data.token_governance || {};
    const utilization = finite(Number(tg.utilization_pct)) ? clampPct(tg.utilization_pct) : null;
    const headroom = finite(Number(tg.headroom_pct)) ? clampPct(tg.headroom_pct) : (utilization === null ? null : 100 - utilization);
    const fill = el('markLivContextFill');
    if (fill) fill.style.width = utilization === null ? '0%' : `${utilization}%`;
    const contextMeter = fill && fill.closest('.mark-liv-context-meter');
    if (contextMeter) {
      contextMeter.dataset.budgetState = utilization === null
        ? 'unknown'
        : (utilization < 30 ? 'safe' : (utilization < 70 ? 'warn' : 'critical'));
    }
    text('markLivContextLabel', utilization === null ? 'SEM MEDIÇÃO' : `${utilization.toFixed(1)}% usado`);
    text('markLivContextUsed', finite(Number(tg.tokens_estimated)) && finite(Number(tg.budget_limit))
      ? `${Number(tg.tokens_estimated).toLocaleString('pt-BR')} / ${Number(tg.budget_limit).toLocaleString('pt-BR')} tokens`
      : 'tokens —');
    text('markLivContextHeadroom', headroom === null ? 'headroom —' : `${headroom.toFixed(1)}% headroom`);
    text('markLivContextGaugeValue', utilization === null ? '—' : `${utilization.toFixed(0)}%`);
    setGauge('markLivContextGauge', utilization || 0);

    const skillsPhase = document.querySelector('[data-phase="skills"]');
    if (skillsPhase && Number(data.canonical_active_skills_count) > 0) {
      skillsPhase.dataset.state = 'ready';
      const note = skillsPhase.querySelector('.mark-liv-phase__copy span');
      if (note) note.textContent = `${Number(data.canonical_active_skills_count).toLocaleString('pt-BR')} skills disponíveis`;
    }

    const executePhase = document.querySelector('[data-phase="execute"]');
    if (executePhase && data.system_state) {
      executePhase.dataset.state = 'ready';
      const note = executePhase.querySelector('.mark-liv-phase__copy span');
      if (note) note.textContent = String(data.system_state).replaceAll('_', ' ');
    }
  }

  function renderHardware(data) {
    if (!data || typeof data !== 'object') return;
    const cpu = clampPct(data.cpu_usage_pct);
    const ram = clampPct(data.ram && data.ram.load_pct);
    const disks = data.disks && typeof data.disks === 'object' ? Object.values(data.disks) : [];
    const disk = disks.length && finite(Number(disks[0].used_pct)) ? clampPct(disks[0].used_pct) : null;

    text('markLivCpu', finite(Number(data.cpu_usage_pct)) ? `${cpu.toFixed(0)}%` : '—');
    text('markLivRam', data.ram && finite(Number(data.ram.load_pct)) ? `${ram.toFixed(0)}%` : '—');
    text('markLivDisk', disk === null ? '—' : `${disk.toFixed(0)}%`);
    text('markLivThreads', Number.isInteger(Number(data.runtime_threads_active))
      ? String(Number(data.runtime_threads_active)) : '—');
    text('markLivTemp', hasFiniteNumber(data.temperature_c)
      ? `${Number(data.temperature_c).toFixed(1)}°C` : '—');
    const tempGauge = el('markLivTempGauge');
    if (tempGauge) {
      tempGauge.dataset.mode = hasFiniteNumber(data.temperature_c) ? 'temperature' : 'unavailable';
      tempGauge.title = hasFiniteNumber(data.temperature_c)
        ? 'Temperatura reportada pelo host'
        : String(data.temperature_status || 'Sensor de temperatura indisponível');
    }
    text('markLivUptime', data.uptime || '—');
    text('markLivArmorIntegrity', finite(Number(data.armor_integrity_pct))
      ? `${Number(data.armor_integrity_pct).toFixed(1)}%` : '—');
    text('markLivPower', hasFiniteNumber(data.power_watts)
      ? `${Number(data.power_watts).toFixed(1)} W` : '—');
    const powerStat = el('markLivPowerStat');
    if (powerStat) {
      powerStat.title = hasFiniteNumber(data.power_watts)
        ? 'Potência reportada pelo host'
        : String(data.power_status || 'Sensor de potência indisponível');
    }
    state.hardware = data;
    renderTrustBadge();
    setGauge('markLivCpuGauge', cpu);
    setGauge('markLivRamGauge', ram);
    setGauge('markLivDiskGauge', disk || 0);

    const subsystems = el('markLivSubsystems');
    if (subsystems) {
      subsystems.replaceChildren();
      const entries = Object.entries(data.subsystems || {}).slice(0, 6);
      const sensorRows = [
        ['TEMPERATURA', hasFiniteNumber(data.temperature_c) ? `${Number(data.temperature_c).toFixed(1)}°C` : String(data.temperature_status || 'UNAVAILABLE')],
        ['POTÊNCIA', hasFiniteNumber(data.power_watts) ? `${Number(data.power_watts).toFixed(1)} W` : String(data.power_status || 'UNAVAILABLE')],
        ['THREADS RUNTIME', Number.isInteger(Number(data.runtime_threads_active)) ? String(Number(data.runtime_threads_active)) : '—']
      ];
      sensorRows.forEach(([name, status]) => {
        const row = document.createElement('div');
        row.className = 'mark-liv-subsystem';
        const key = document.createElement('span');
        const value = document.createElement('strong');
        key.textContent = name;
        value.textContent = status;
        row.append(key, value);
        subsystems.appendChild(row);
      });
      if (!entries.length) {
        const row = document.createElement('div');
        row.className = 'mark-liv-subsystem';
        row.innerHTML = '<span>TELEMETRIA</span><strong>SEM SUBSISTEMAS</strong>';
        subsystems.appendChild(row);
      }
      entries.forEach(([name, status]) => {
        const row = document.createElement('div');
        row.className = 'mark-liv-subsystem';
        const key = document.createElement('span');
        const value = document.createElement('strong');
        key.textContent = name.replaceAll('_', ' ').toUpperCase();
        value.textContent = String(status);
        row.append(key, value);
        subsystems.appendChild(row);
      });
    }
  }

  function renderKeys(data) {
    const preferred = data && (data.preferred_provider || data.preferredProvider);
    const active = data && Array.isArray(data.active_providers) ? data.active_providers : [];
    text('markLivProvider', preferred ? String(preferred).toUpperCase() : 'HEURÍSTICA / NÃO CONFIGURADO');
    text('markLivProviderMeta', active.length
      ? `providers disponíveis: ${active.map(String).join(' · ')}`
      : 'nenhum provider cloud confirmado pelo host');
  }

  function renderTelemetry(data) {
    if (!data || typeof data !== 'object') return;
    const latency = Number(data.avg_duration_ms);
    text('markLivLatency', Number.isFinite(latency) ? `${Math.round(latency)} ms` : '—');
    text('markLivSpanCount', Number.isFinite(Number(data.total_spans))
      ? Number(data.total_spans).toLocaleString('pt-BR') : '—');
    const synthesis = document.querySelector('[data-phase="synthesis"]');
    if (synthesis && Number(data.total_spans) > 0) {
      synthesis.dataset.state = 'ready';
      const note = synthesis.querySelector('.mark-liv-phase__copy span');
      if (note) note.textContent = `${Number(data.total_spans).toLocaleString('pt-BR')} spans observados`;
    }
  }

  function renderMemory(data) {
    const feed = el('markLivMemoryFeed');
    if (!feed) return;
    feed.replaceChildren();
    const memories = data && Array.isArray(data.memories) ? data.memories.slice(-4).reverse() : [];
    if (!memories.length) {
      const empty = document.createElement('div');
      empty.className = 'mark-liv-memory-item';
      empty.textContent = 'Nenhuma memória persistente retornada pelo host.';
      feed.appendChild(empty);
      return;
    }
    memories.forEach((memory) => {
      const row = document.createElement('div');
      row.className = 'mark-liv-memory-item';
      const category = document.createElement('b');
      category.textContent = `[${String(memory.category || 'memory').toUpperCase()}] `;
      const fact = document.createTextNode(String(memory.fact || memory.text || memory.content || 'registro sem texto'));
      row.append(category, fact);
      feed.appendChild(row);
    });
  }

  function normalizeDag(data) {
    const dag = data && data.dag && typeof data.dag === 'object' ? data.dag : data;
    let nodes = [];
    if (dag && Array.isArray(dag.nodes)) nodes = dag.nodes;
    else if (dag && dag.nodes && typeof dag.nodes === 'object') nodes = Object.values(dag.nodes);
    const schedule = data && data.schedule && typeof data.schedule === 'object' ? data.schedule : {};
    return {
      missionId: (data && (data.mission_id || data.missionId)) || schedule.mission_id || '—',
      nodes,
      edges: dag && Array.isArray(dag.edges) ? dag.edges : [],
      waves: Array.isArray(schedule.waves) ? schedule.waves : []
    };
  }

  function taskStateClass(status) {
    const normalized = String(status || 'PENDING').toUpperCase();
    if (normalized === 'VERIFIED') return 'is-verified';
    if (normalized === 'RUNNING' || normalized === 'EXECUTED' || normalized === 'READY') return 'is-running';
    if (normalized === 'FAILED' || normalized === 'CANCELLED') return 'is-failed';
    return 'is-pending';
  }

  function waveIndexForTask(waves, taskId) {
    for (const wave of waves) {
      if (Array.isArray(wave.task_ids) && wave.task_ids.includes(taskId)) {
        return Number.isInteger(wave.wave_index) ? wave.wave_index : waves.indexOf(wave);
      }
    }
    return null;
  }

  function renderWaveStrip(waves, nodes) {
    const strip = el('markLivWaveStrip');
    if (!strip) return;
    strip.replaceChildren();
    if (!waves.length) {
      const empty = document.createElement('span');
      empty.className = 'mark-liv-wave-chip is-empty';
      empty.textContent = 'Sem waves retornadas';
      strip.appendChild(empty);
      return;
    }
    const byId = new Map(nodes.map((node) => [String(node.task_id || node.id || ''), node]));
    waves.forEach((wave, index) => {
      const taskIds = Array.isArray(wave.task_ids) ? wave.task_ids : [];
      const statuses = taskIds.map((id) => String((byId.get(String(id)) || {}).status || 'PENDING').toUpperCase());
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'mark-liv-wave-chip';
      chip.dataset.waveIndex = String(Number.isInteger(wave.wave_index) ? wave.wave_index : index);
      if (statuses.some((status) => status === 'RUNNING' || status === 'READY' || status === 'EXECUTED')) {
        chip.classList.add('is-running');
      } else if (statuses.length && statuses.every((status) => status === 'VERIFIED')) {
        chip.classList.add('is-verified');
      } else if (statuses.some((status) => status === 'FAILED' || status === 'CANCELLED')) {
        chip.classList.add('is-failed');
      }
      chip.textContent = `W${index + 1} · ${taskIds.length} task${taskIds.length === 1 ? '' : 's'}`;
      chip.title = taskIds.join(', ') || 'wave sem tarefas';
      chip.addEventListener('click', () => {
        const first = taskIds.length ? document.querySelector(`[data-mark-task-id="${CSS.escape(String(taskIds[0]))}"]`) : null;
        if (first) {
          first.focus();
          first.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        }
      });
      strip.appendChild(chip);
    });
  }

  function showDagNodeDetail(node, waves) {
    const detail = el('markLivDagDetail');
    if (!detail) return;
    const taskId = String(node.task_id || node.id || 'unknown');
    const waveIndex = waveIndexForTask(waves, taskId);
    const deps = Array.isArray(node.dependencies) ? node.dependencies : [];
    const verifications = Array.isArray(node.verification_requirements) ? node.verification_requirements : [];
    const verified = verifications.filter((item) => String(item.status || '').toUpperCase() === 'VERIFIED').length;
    detail.replaceChildren();

    const title = document.createElement('strong');
    title.textContent = String(node.title || taskId);
    const meta = document.createElement('span');
    meta.textContent = `${taskId} // ${String(node.status || 'PENDING').toUpperCase()} // ${String(node.agent_profile || 'agent —')}`;
    const depsLine = document.createElement('span');
    depsLine.textContent = `Wave: ${waveIndex === null ? '—' : waveIndex + 1} · Dependências: ${deps.length ? deps.join(', ') : 'nenhuma'} · Verificações: ${verified}/${verifications.length}`;
    detail.append(title, meta, depsLine);
  }

  function renderDag(data) {
    const normalized = normalizeDag(data || {});
    text('markLivMissionId', normalized.missionId);
    text('markLivNodeCount', normalized.nodes.length || '—');
    text('markLivWaveCount', normalized.waves.length || '—');
    renderWaveStrip(normalized.waves, normalized.nodes);

    const phase = document.querySelector('[data-phase="decompose"]');
    if (phase && normalized.nodes.length) {
      phase.dataset.state = 'ready';
      const note = phase.querySelector('.mark-liv-phase__copy span');
      if (note) note.textContent = `${normalized.nodes.length} nós no DAG`;
    }

    const svg = el('markLivDagSvg');
    if (!svg) return;
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    const ns = 'http://www.w3.org/2000/svg';
    const nodes = normalized.nodes.slice(0, 8);
    if (!nodes.length) {
      const label = document.createElementNS(ns, 'text');
      label.setAttribute('x', '24');
      label.setAttribute('y', '92');
      label.setAttribute('fill', '#7ca7b5');
      label.setAttribute('font-size', '11');
      label.textContent = 'Nenhum DAG ativo retornado pelo runtime.';
      svg.appendChild(label);
      return;
    }

    const byId = new Map(nodes.map((node) => [String(node.task_id || node.id || ''), node]));
    const positions = new Map();
    const step = 570 / Math.max(nodes.length - 1, 1);
    nodes.forEach((node, index) => {
      positions.set(String(node.task_id || node.id || index), {
        x: 35 + index * step,
        y: index % 2 ? 110 : 70
      });
    });

    const edges = normalized.edges.filter((edge) => (
      edge && positions.has(String(edge.from)) && positions.has(String(edge.to))
    ));
    const derivedEdges = edges.length ? edges : nodes.slice(1).map((node, index) => ({
      from: String(nodes[index].task_id || nodes[index].id || index),
      to: String(node.task_id || node.id || index + 1)
    }));

    derivedEdges.forEach((edge) => {
      const from = positions.get(String(edge.from));
      const to = positions.get(String(edge.to));
      if (!from || !to) return;
      const line = document.createElementNS(ns, 'line');
      line.setAttribute('class', 'mark-liv-dag-edge');
      line.setAttribute('x1', String(from.x));
      line.setAttribute('y1', String(from.y));
      line.setAttribute('x2', String(to.x));
      line.setAttribute('y2', String(to.y));
      svg.appendChild(line);
    });

    nodes.forEach((node, index) => {
      const taskId = String(node.task_id || node.id || `node-${index + 1}`);
      const pos = positions.get(taskId);
      const group = document.createElementNS(ns, 'g');
      group.setAttribute('class', `mark-liv-dag-node ${taskStateClass(node.status)}`);
      group.setAttribute('tabindex', '0');
      group.setAttribute('role', 'button');
      group.setAttribute('data-mark-task-id', taskId);
      group.setAttribute('aria-label', `${node.title || taskId}: ${node.status || 'PENDING'}`);
      const circle = document.createElementNS(ns, 'circle');
      circle.setAttribute('cx', String(pos.x));
      circle.setAttribute('cy', String(pos.y));
      circle.setAttribute('r', '12');
      const title = document.createElementNS(ns, 'title');
      title.textContent = `${node.title || taskId} // ${node.status || 'PENDING'}`;
      circle.appendChild(title);
      const label = document.createElementNS(ns, 'text');
      label.setAttribute('x', String(pos.x));
      label.setAttribute('y', String(pos.y + 28));
      label.setAttribute('text-anchor', 'middle');
      label.textContent = taskId.length > 15 ? `${taskId.slice(0, 13)}…` : taskId;
      const activate = () => showDagNodeDetail(node, normalized.waves);
      group.addEventListener('click', activate);
      group.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          activate();
        }
      });
      group.append(circle, label);
      svg.appendChild(group);
    });

    showDagNodeDetail(nodes[0], normalized.waves);
  }

  function renderReceipts(payload) {
    const container = el('markLivReceipts');
    if (!container) return;
    container.replaceChildren();
    const events = payload && Array.isArray(payload.events) ? payload.events.slice(-6).reverse() : [];
    if (!events.length) {
      const empty = document.createElement('div');
      empty.className = 'mark-liv-receipt';
      empty.textContent = 'Sem receipts persistidos para exibir.';
      container.appendChild(empty);
      return;
    }
    events.forEach((event) => {
      const row = document.createElement('div');
      row.className = 'mark-liv-receipt';
      const eventType = String(event.event_type || 'EVENT').toUpperCase();
      const stateValue = event.data && (
        event.data.verification_state
        || event.data.execution_state
        || event.data.recovery_state
        || event.data.decision_type
      );
      const heading = document.createElement('strong');
      heading.textContent = `${eventType} · ${event.task_id || 'mission'}`;
      const meta = document.createElement('span');
      meta.textContent = `${stateValue || 'OBSERVED'} · ${event.receipt_id || 'receipt —'}`;
      row.append(heading, meta);
      container.appendChild(row);
    });
  }

  async function loadLatestReceipts() {
    try {
      const listing = await fetchJson('/api/runtime/missions');
      const missions = listing && Array.isArray(listing.missions) ? listing.missions.slice() : [];
      missions.sort((a, b) => String(b.last_event_utc || '').localeCompare(String(a.last_event_utc || '')));
      if (!missions.length || !missions[0].mission_id) {
        state.receipts = { events: [] };
        renderReceipts(state.receipts);
        return;
      }
      const missionId = encodeURIComponent(String(missions[0].mission_id));
      const timeline = await fetchJson(`/api/runtime/missions/${missionId}/timeline`);
      state.receipts = timeline;
      renderReceipts(timeline);
    } catch (_) {
      state.receipts = null;
      renderReceipts({ events: [] });
    }
  }

  async function refresh() {
    const requests = [
      ['status', '/api/status', renderStatus],
      ['hardware', '/api/system/telemetry', renderHardware],
      ['keys', '/api/keys/status', renderKeys],
      ['telemetry', '/api/agentic/telemetry', renderTelemetry],
      ['memory', '/api/memory', renderMemory],
      ['dag', '/api/agentic/dag/active', renderDag]
    ];

    await Promise.all(requests.map(async ([key, path, renderer]) => {
      try {
        const data = await fetchJson(path);
        state[key] = data;
        renderer(data);
      } catch (error) {
        if (key === 'hardware') {
          ['markLivCpu', 'markLivRam', 'markLivDisk'].forEach((id) => text(id, '—'));
        }
      }
    }));
    await loadLatestReceipts();
    state.lastRefresh = Date.now();
    document.dispatchEvent(new CustomEvent('jarvis:mark-liv-refresh', { detail: { ...state } }));
  }

  function init() {
    if (document.body.classList.contains('mark-liv-ready')) return;
    mount();
    document.body.classList.add('mark-liv-ready');
    refresh();
    window.setInterval(refresh, REFRESH_MS);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
