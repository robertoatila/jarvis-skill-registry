(() => {
  'use strict';

  const NS = 'http://www.w3.org/2000/svg';
  const LABELS = {
    note: 'ARQUIVO', project: 'PROJETO', client: 'CLIENTE', meeting: 'REUNIÃO',
    proposal: 'PROPOSTA', decision: 'DECISÃO', memory: 'MEMÓRIA', agent: 'AGENTE',
    security: 'SEGURANÇA', architecture: 'ARQUITETURA', core: 'SECOND BRAIN'
  };
  const state = { graph: null, memory: null, agents: [], operations: null, missionId: null, query: '', selected: null };

  const byId = (id) => document.getElementById(id);
  const esc = (value) => String(value == null ? '' : value);
  const short = (value, max = 46) => {
    const text = esc(value);
    return text.length > max ? text.slice(0, max - 1) + '…' : text;
  };
  const hash = (value) => {
    let h = 2166136261;
    for (const ch of esc(value)) {
      h ^= ch.charCodeAt(0);
      h = Math.imul(h, 16777619);
    }
    return h >>> 0;
  };
  const svg = (tag, attrs = {}) => {
    const node = document.createElementNS(NS, tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, esc(value)));
    return node;
  };

  function installShell() {
    const anchorButton = byId('tabBtnObsidian');
    const anchorPane = byId('tabObsidian');
    if (!anchorButton || !anchorPane || byId('tabBtnBrain')) return;

    const button = document.createElement('button');
    button.className = 'nav-tab';
    button.id = 'tabBtnBrain';
    button.dataset.tab = 'tabBrain';
    button.setAttribute('role', 'tab');
    button.setAttribute('aria-selected', 'false');
    button.setAttribute('aria-controls', 'tabBrain');
    button.innerHTML = '<span class="nav-text">Segundo Cérebro</span><span class="tab-badge pulse-badge" id="secondBrainNavBadge">GRAFO</span>';
    anchorButton.insertAdjacentElement('afterend', button);

    const pane = document.createElement('section');
    pane.className = 'hud-tab-pane second-brain-pane';
    pane.id = 'tabBrain';
    pane.setAttribute('role', 'tabpanel');
    pane.setAttribute('aria-labelledby', 'tabBtnBrain');
    pane.innerHTML = `
      <div class="second-brain-shell">
        <header class="second-brain-header">
          <div>
            <span class="second-brain-eyebrow">MEMÓRIA COMPARTILHADA // KNOWLEDGE FABRIC</span>
            <h2>J.A.R.V.I.S. Segundo Cérebro</h2>
            <p>Arquivos, projetos, reuniões, decisões e memórias conectados em uma projeção somente-leitura do cofre atual. Os agentes aparecem ao redor da mesma base de contexto.</p>
          </div>
          <div class="second-brain-kpis">
            <div><strong id="brainNodeCount">—</strong><span>NÓS</span></div>
            <div><strong id="brainEdgeCount">—</strong><span>LIGAÇÕES</span></div>
            <div><strong id="brainMemoryCount">—</strong><span>MEMÓRIAS</span></div>
            <div><strong id="brainAgentCount">—</strong><span>AGENTES</span></div>
            <div><strong id="brainHumanCount">0</strong><span>DECISÕES</span></div>
          </div>
        </header>
        <div class="second-brain-controls">
          <label><span>BUSCAR</span><input id="brainSearch" type="search" placeholder="arquivo, projeto, decisão, memória…" autocomplete="off"></label>
          <button id="brainRefresh" type="button" class="btn-action primary">Atualizar grafo</button>
          <span id="brainGeneratedAt">AGUARDANDO DADOS</span>
        </div>
        <section class="second-brain-ops-card" aria-labelledby="brainOpsTitle">
          <div class="second-brain-ops-head">
            <div>
              <span class="second-brain-card-label">OPERATION FABRIC // RECEIPT-BACKED</span>
              <h3 id="brainOpsTitle">Handoffs, execução e decisão humana</h3>
            </div>
            <div class="second-brain-ops-meta">
              <select id="brainMissionSelect" aria-label="Missão ativa"></select>
              <span id="brainMissionStatus">SEM MISSÃO ATIVA</span>
              <span id="brainReceiptCount">0 RECEIPTS</span>
            </div>
          </div>
          <div id="brainOperations" class="second-brain-operations">
            <div class="second-brain-loading">Carregando missões autoritativas e receipts…</div>
          </div>
        </section>
        <div class="second-brain-layout">
          <section class="second-brain-graph-card">
            <div class="second-brain-card-head">
              <div><span>SECOND BRAIN MAP</span><h3>Mapa vivo de contexto</h3></div>
              <div id="brainLegend" class="second-brain-legend"></div>
            </div>
            <div class="second-brain-stage">
              <svg id="brainGraph" viewBox="0 0 1200 700" role="img" aria-label="Grafo do Segundo Cérebro"></svg>
              <div id="brainEmpty" class="second-brain-empty">Carregando Segundo Cérebro…</div>
            </div>
          </section>
          <aside class="second-brain-sidebar">
            <section class="second-brain-info-card">
              <span class="second-brain-card-label">NÓ SELECIONADO</span>
              <h3 id="brainDetailTitle">Centro cognitivo</h3>
              <div id="brainDetailKind" class="second-brain-kind-pill">SECOND BRAIN</div>
              <p id="brainDetailBody">Selecione um ponto para inspecionar origem, tipo, tags e conectividade.</p>
              <dl id="brainDetailMeta" class="second-brain-meta"></dl>
            </section>
            <section class="second-brain-info-card">
              <span class="second-brain-card-label">ESCRITÓRIO DOS AGENTES</span>
              <h3>Times lendo a mesma memória</h3>
              <div id="brainAgentOffice" class="second-brain-agent-office"><div class="second-brain-loading">Carregando agentes…</div></div>
            </section>
            <section class="second-brain-info-card second-brain-human-gate">
              <span class="second-brain-card-label">FRONTEIRA HUMANA</span>
              <h3>Contexto não é autoridade</h3>
              <p>Notas e memórias informam o runtime. Aprovação, autorização e políticas continuam separadas e fail-closed.</p>
            </section>
          </aside>
        </div>
      </div>`;
    anchorPane.insertAdjacentElement('afterend', pane);
  }

  installShell();

  async function getJson(url) {
    const response = await fetch(url, { headers: { Accept: 'application/json' } });
    if (!response.ok) throw new Error('HTTP ' + response.status);
    return response.json();
  }

  function memoryNodes() {
    const items = state.memory && Array.isArray(state.memory.memories) ? state.memory.memories : [];
    return items.slice(0, 40).map((item, index) => {
      const fact = item.fact || item.content || item.text || ('Memória ' + (index + 1));
      return {
        id: 'memory:' + (item.id || hash(fact)),
        label: short(fact, 70),
        kind: 'memory',
        type: item.category || 'episodic',
        tags: [item.importance, item.source].filter(Boolean),
        path: null,
        degree: 1,
        fact
      };
    });
  }

  function model() {
    const raw = state.graph && Array.isArray(state.graph.nodes) ? state.graph.nodes : [];
    const ranked = [...raw].sort((a, b) => (Number(b.degree) || 0) - (Number(a.degree) || 0)).slice(0, 180);
    const nodes = ranked.concat(memoryNodes());
    const ids = new Set(nodes.map((node) => node.id));
    const sourceEdges = state.graph && Array.isArray(state.graph.edges) ? state.graph.edges : [];
    const edges = sourceEdges.filter((edge) => ids.has(edge.source) && ids.has(edge.target)).slice(0, 500);
    ranked.slice(0, 12).forEach((node) => edges.push({ source: '__brain__', target: node.id, relation: 'core' }));
    memoryNodes().slice(0, 16).forEach((node) => edges.push({ source: '__brain__', target: node.id, relation: 'memory' }));
    nodes.unshift({ id: '__brain__', label: 'SECOND BRAIN', kind: 'core', degree: 28, tags: [] });
    return { nodes, edges };
  }

  function positions(nodes) {
    const result = new Map([['__brain__', { x: 600, y: 350 }]]);
    const groups = new Map();
    nodes.filter((node) => node.id !== '__brain__').forEach((node) => {
      const key = node.kind || 'note';
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(node);
    });
    const kinds = [...groups.keys()].sort();
    kinds.forEach((kind, groupIndex) => {
      const group = groups.get(kind).sort((a, b) => (Number(b.degree) || 0) - (Number(a.degree) || 0));
      group.forEach((node, index) => {
        const band = Math.floor(index / 18);
        const slot = index % 18;
        const jitter = (hash(node.id) % 1000) / 1000 - 0.5;
        const start = Math.PI * 2 * groupIndex / Math.max(1, kinds.length);
        const span = Math.PI * 2 / Math.max(1, kinds.length);
        const angle = start + span * ((slot + 0.5) / Math.min(18, group.length || 1)) + jitter * 0.12;
        const radius = Math.min(315, Math.max(120, 150 + band * 58 - Math.min(45, (Number(node.degree) || 0) * 4) + jitter * 20));
        result.set(node.id, { x: 600 + Math.cos(angle) * radius, y: 350 + Math.sin(angle) * radius });
      });
    });
    return result;
  }

  function renderLegend(nodes) {
    const target = byId('brainLegend');
    if (!target) return;
    const counts = new Map();
    nodes.forEach((node) => {
      if (node.kind !== 'core') counts.set(node.kind || 'note', (counts.get(node.kind || 'note') || 0) + 1);
    });
    target.replaceChildren();
    [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 7).forEach(([kind, count]) => {
      const chip = document.createElement('span');
      chip.textContent = (LABELS[kind] || kind.toUpperCase()) + ' ' + count;
      target.appendChild(chip);
    });
  }

  function renderDetails(node, connections = null) {
    byId('brainDetailTitle').textContent = node.label || node.id;
    const kind = byId('brainDetailKind');
    kind.textContent = LABELS[node.kind] || esc(node.kind).toUpperCase();
    kind.dataset.kind = node.kind || 'note';
    byId('brainDetailBody').textContent = node.fact || (node.path ? 'Arquivo do cofre: ' + node.path : 'Nó do grafo cognitivo.');
    const meta = byId('brainDetailMeta');
    meta.replaceChildren();
    [
      ['Tipo', node.type || '—'],
      ['Conexões visíveis', esc(connections == null ? (node.degree || 0) : connections)],
      ['Tags', Array.isArray(node.tags) && node.tags.length ? node.tags.join(' · ') : '—'],
      ['Origem', node.path || (node.kind === 'memory' ? 'Memory Engine' : 'runtime')]
    ].forEach(([term, value]) => {
      const dt = document.createElement('dt'); dt.textContent = term;
      const dd = document.createElement('dd'); dd.textContent = value;
      meta.append(dt, dd);
    });
  }

  function selectNode(id) {
    state.selected = id;
    const current = model();
    const node = current.nodes.find((item) => item.id === id);
    if (!node) return;
    const neighbors = new Set([id]);
    current.edges.forEach((edge) => {
      if (edge.source === id) neighbors.add(edge.target);
      if (edge.target === id) neighbors.add(edge.source);
    });
    document.querySelectorAll('.second-brain-node').forEach((item) => {
      const nodeId = item.dataset.nodeId;
      item.classList.toggle('is-selected', nodeId === id);
      item.classList.toggle('is-dimmed', !neighbors.has(nodeId));
    });
    document.querySelectorAll('.second-brain-edge').forEach((item) => {
      const connected = item.dataset.source === id || item.dataset.target === id;
      item.classList.toggle('is-connected', connected);
      item.classList.toggle('is-dimmed', !connected);
    });
    renderDetails(node, neighbors.size - 1);
  }

  function applySearch() {
    const q = state.query.trim().toLocaleLowerCase('pt-BR');
    const current = model();
    const lookup = new Map(current.nodes.map((node) => [node.id, node]));
    document.querySelectorAll('.second-brain-node').forEach((item) => {
      const node = lookup.get(item.dataset.nodeId);
      if (!node || node.id === '__brain__') return;
      const text = [node.label, node.path, node.type, ...(node.tags || [])].filter(Boolean).join(' ').toLocaleLowerCase('pt-BR');
      item.classList.toggle('is-search-hidden', Boolean(q && !text.includes(q)));
    });
  }

  function activeMission() {
    const missions = state.operations && Array.isArray(state.operations.missions)
      ? state.operations.missions
      : [];
    if (!missions.length) return null;
    return missions.find((mission) => mission.mission_id === state.missionId) || missions[0];
  }

  function taskAgent(task) {
    return task && (task.selected_agent || task.planned_agent) || 'UNKNOWN';
  }

  function tasksForAgent(agent) {
    const mission = activeMission();
    if (!mission || !Array.isArray(mission.tasks)) return [];
    const agentId = agent && (agent.id || agent.name);
    return mission.tasks.filter((task) => taskAgent(task) === agentId);
  }

  function renderOperations() {
    const target = byId('brainOperations');
    const select = byId('brainMissionSelect');
    if (!target || !select) return;

    const missions = state.operations && Array.isArray(state.operations.missions)
      ? state.operations.missions
      : [];

    select.replaceChildren();
    if (!missions.length) {
      const option = document.createElement('option');
      option.value = '';
      option.textContent = 'Nenhuma missão ativa';
      select.appendChild(option);
      select.disabled = true;
      byId('brainMissionStatus').textContent = 'SEM MISSÃO ATIVA';
      byId('brainReceiptCount').textContent = '0 RECEIPTS';
      target.replaceChildren();
      const empty = document.createElement('div');
      empty.className = 'second-brain-ops-empty';
      empty.textContent = 'Nenhuma missão autoritativa ativa. O painel não substitui isso por um DAG demonstrativo.';
      target.appendChild(empty);
      return;
    }

    select.disabled = false;
    missions.forEach((mission) => {
      const option = document.createElement('option');
      option.value = mission.mission_id;
      option.textContent = short(mission.mission_id, 34);
      select.appendChild(option);
    });

    const mission = activeMission();
    state.missionId = mission.mission_id;
    select.value = mission.mission_id;
    byId('brainMissionStatus').textContent = mission.status || 'UNKNOWN';
    const receiptCount = mission.receipts && Number.isInteger(mission.receipts.event_count)
      ? mission.receipts.event_count
      : 0;
    byId('brainReceiptCount').textContent = receiptCount + ' RECEIPTS';

    target.replaceChildren();

    const taskLane = document.createElement('div');
    taskLane.className = 'second-brain-task-lane';
    const tasks = Array.isArray(mission.tasks) ? mission.tasks : [];
    tasks.forEach((task, index) => {
      const card = document.createElement('article');
      card.className = 'second-brain-task-card';
      card.dataset.status = task.status || 'UNKNOWN';
      card.dataset.gate = task.gate_state || 'NONE';

      const step = document.createElement('span');
      step.className = 'second-brain-task-step';
      step.textContent = 'TASK ' + String(index + 1).padStart(2, '0');

      const title = document.createElement('strong');
      title.textContent = task.title || task.task_id;

      const agent = document.createElement('p');
      agent.textContent = taskAgent(task);

      const meta = document.createElement('div');
      const status = document.createElement('span');
      status.textContent = task.status || 'UNKNOWN';
      const verification = document.createElement('span');
      verification.textContent = task.verification_state || task.execution_state || 'SEM RECEIPT';
      meta.append(status, verification);

      card.append(step, title, agent, meta);

      if (task.gate_state && task.gate_state !== 'NONE') {
        const gate = document.createElement('span');
        gate.className = 'second-brain-task-gate';
        gate.textContent = task.gate_state === 'WAITING_HUMAN'
          ? 'DECISÃO HUMANA'
          : task.gate_state;
        card.appendChild(gate);
      }

      taskLane.appendChild(card);
    });
    target.appendChild(taskLane);

    const handoffs = Array.isArray(mission.handoffs) ? mission.handoffs : [];
    const handoffSection = document.createElement('section');
    handoffSection.className = 'second-brain-handoff-section';
    const handoffTitle = document.createElement('div');
    handoffTitle.className = 'second-brain-ops-subtitle';
    handoffTitle.textContent = handoffs.length
      ? 'HANDOFFS ENTRE AGENTES • ' + handoffs.length
      : 'HANDOFFS ENTRE AGENTES • NENHUM';
    handoffSection.appendChild(handoffTitle);

    const handoffList = document.createElement('div');
    handoffList.className = 'second-brain-handoff-list';
    handoffs.forEach((handoff) => {
      const item = document.createElement('article');
      item.className = 'second-brain-handoff';
      item.dataset.state = handoff.state || 'PLANNED';

      const route = document.createElement('strong');
      route.textContent = short(handoff.from_agent, 22) + ' → ' + short(handoff.to_agent, 22);
      const tasksText = document.createElement('span');
      tasksText.textContent = handoff.from + ' → ' + handoff.to;
      const stateBadge = document.createElement('em');
      stateBadge.textContent = handoff.state || 'PLANNED';

      const context = document.createElement('small');
      const evidence = handoff.context_evidence && typeof handoff.context_evidence === 'object'
        ? handoff.context_evidence
        : {};
      context.textContent = handoff.context_shared
        ? 'CTX SHARED · ' + (evidence.shared_context_events || 0) + ' shared ctx · ' + (evidence.memory_matches || 0) + ' mem'
        : 'CTX NÃO OBSERVADO';

      item.append(route, tasksText, stateBadge, context);
      handoffList.appendChild(item);
    });
    if (!handoffs.length) {
      const none = document.createElement('div');
      none.className = 'second-brain-ops-empty compact';
      none.textContent = 'A missão atual não contém troca de agente entre dependências.';
      handoffList.appendChild(none);
    }
    handoffSection.appendChild(handoffList);
    target.appendChild(handoffSection);

    const gates = Array.isArray(mission.human_gates) ? mission.human_gates : [];
    const gateSection = document.createElement('section');
    gateSection.className = 'second-brain-gate-section';
    const gateTitle = document.createElement('div');
    gateTitle.className = 'second-brain-ops-subtitle';
    gateTitle.textContent = gates.length
      ? 'FRONTEIRA HUMANA • ' + gates.length + ' GATE(S)'
      : 'FRONTEIRA HUMANA • LIVRE';
    gateSection.appendChild(gateTitle);

    const gateList = document.createElement('div');
    gateList.className = 'second-brain-gate-list';
    gates.forEach((gate) => {
      const item = document.createElement('article');
      item.className = 'second-brain-gate-card';
      item.dataset.state = gate.gate_state || 'NONE';
      const title = document.createElement('strong');
      title.textContent = gate.title || gate.task_id;
      const agent = document.createElement('span');
      agent.textContent = gate.agent || 'UNKNOWN';
      const status = document.createElement('em');
      status.textContent = (gate.gate_state || 'NONE') + ' • ' + (gate.approval_status || 'UNKNOWN') + ' • ' + (gate.risk_level || 'UNKNOWN');
      const detail = document.createElement('small');
      const expiry = gate.expires_utc ? new Date(gate.expires_utc) : null;
      const expiryText = expiry && !Number.isNaN(expiry.getTime())
        ? ' · expira ' + expiry.toLocaleString('pt-BR')
        : '';
      detail.textContent = (gate.approval_id || 'sem approval id') + expiryText;

      item.append(title, agent, status, detail);

      if (gate.approval_id) {
        const copy = document.createElement('button');
        copy.type = 'button';
        copy.className = 'second-brain-copy-approval';
        copy.textContent = 'COPIAR ID';
        copy.title = 'Copiar identificador da aprovação persistida';
        copy.addEventListener('click', async () => {
          try {
            await navigator.clipboard.writeText(gate.approval_id);
            copy.textContent = 'COPIADO';
          } catch (_) {
            copy.textContent = short(gate.approval_id, 18);
          }
        });
        item.appendChild(copy);
      }

      gateList.appendChild(item);
    });
    if (!gates.length) {
      const none = document.createElement('div');
      none.className = 'second-brain-ops-empty compact';
      none.textContent = 'Nenhuma aprovação humana persistida para a missão selecionada.';
      gateList.appendChild(none);
    }
    gateSection.appendChild(gateList);
    target.appendChild(gateSection);
  }

  function renderAgents(layer) {
    const center = { x: 600, y: 350 };
    const agents = Array.isArray(state.agents) ? state.agents : [];
    agents.forEach((agent, index) => {
      const angle = -Math.PI / 2 + Math.PI * 2 * index / Math.max(1, agents.length);
      const x = center.x + Math.cos(angle) * 305;
      const y = center.y + Math.sin(angle) * 305;
      layer.appendChild(svg('line', { x1: center.x, y1: center.y, x2: x, y2: y, class: 'second-brain-agent-link' }));
      const group = svg('g', { class: 'second-brain-agent-node', transform: 'translate(' + x + ' ' + y + ')' });
      group.appendChild(svg('circle', { r: 16 }));
      const name = svg('text', { x: 22, y: -2, class: 'second-brain-agent-label' });
      name.textContent = short(agent.name || agent.id || 'Agente', 27);
      const status = svg('text', { x: 22, y: 12, class: 'second-brain-agent-status' });
      const assigned = tasksForAgent(agent);
      const memoryReads = assigned.reduce(
        (total, task) => total + Number(task.memory_events || 0) + Number(task.shared_context_events || 0),
        0
      );
      status.textContent = assigned.length
        ? (agent.status || 'ONLINE') + ' • ' + assigned.length + ' TASK' + (memoryReads ? ' • CTX ' + memoryReads : '')
        : (agent.status || 'UNKNOWN');
      group.append(name, status);
      layer.appendChild(group);
    });
  }

  function renderGraph() {
    const graph = byId('brainGraph');
    const empty = byId('brainEmpty');
    if (!graph) return;
    graph.replaceChildren();
    const current = model();
    if (current.nodes.length <= 1) {
      empty.hidden = false;
      empty.textContent = 'Nenhum nó do cofre disponível.';
      return;
    }
    empty.hidden = true;
    const pos = positions(current.nodes);
    const layer = svg('g');

    current.edges.forEach((edge) => {
      const a = pos.get(edge.source);
      const b = pos.get(edge.target);
      if (!a || !b) return;
      const line = svg('line', {
        x1: a.x, y1: a.y, x2: b.x, y2: b.y,
        class: 'second-brain-edge second-brain-edge--' + (edge.relation || 'link'),
        'data-source': edge.source, 'data-target': edge.target
      });
      line.dataset.source = edge.source;
      line.dataset.target = edge.target;
      layer.appendChild(line);
    });

    current.nodes.forEach((node) => {
      const point = pos.get(node.id);
      if (!point) return;
      const group = svg('g', {
        class: 'second-brain-node second-brain-node--' + (node.kind || 'note'),
        transform: 'translate(' + point.x + ' ' + point.y + ')',
        tabindex: '0'
      });
      group.dataset.nodeId = node.id;
      const radius = node.id === '__brain__' ? 28 : Math.min(12, 4.5 + Math.sqrt(Math.max(0, Number(node.degree) || 0)) * 1.6);
      if (node.id === '__brain__') group.appendChild(svg('circle', { r: 39, class: 'second-brain-core-ring' }));
      group.appendChild(svg('circle', { r: radius }));
      const label = svg('text', { x: radius + 7, y: 3, class: node.id === '__brain__' ? 'second-brain-core-label' : 'second-brain-node-label' });
      label.textContent = short(node.label, node.id === '__brain__' ? 20 : 34);
      group.appendChild(label);
      const activate = () => selectNode(node.id);
      group.addEventListener('click', activate);
      group.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); activate(); }
      });
      layer.appendChild(group);
    });

    renderAgents(layer);
    graph.appendChild(layer);
    renderLegend(current.nodes);
    applySearch();
  }

  function renderAgentOffice() {
    const target = byId('brainAgentOffice');
    target.replaceChildren();
    const agents = Array.isArray(state.agents) ? state.agents : [];
    if (!agents.length) {
      const item = document.createElement('div');
      item.className = 'second-brain-loading';
      item.textContent = 'Nenhum agente anunciado pelo runtime.';
      target.appendChild(item);
      return;
    }
    agents.forEach((agent) => {
      const card = document.createElement('article');
      const assigned = tasksForAgent(agent);
      card.className = 'second-brain-agent-card' + (assigned.length ? ' is-engaged' : '');
      const skills = Array.isArray(agent.skills) ? agent.skills.length : 0;
      card.innerHTML = '<strong></strong><p></p><div><span></span><span></span></div>';
      card.querySelector('strong').textContent = agent.name || agent.id || 'Agente';
      card.querySelector('p').textContent = agent.domain || 'domínio não informado';
      const spans = card.querySelectorAll('span');
      const contextEvents = assigned.reduce(
        (total, task) => total + Number(task.memory_events || 0) + Number(task.shared_context_events || 0),
        0
      );
      spans[0].textContent = contextEvents
        ? 'SHARED MEMORY OBSERVED'
        : (assigned.length ? 'CONTEXT ACTIVE' : (agent.status || 'UNKNOWN'));
      spans[1].textContent = assigned.length
        ? assigned.length + ' task(s) • ' + contextEvents + ' ctx • ' + skills + ' skills'
        : skills + ' skills';
      target.appendChild(card);
    });
  }

  function updateSummary() {
    const metrics = state.graph && state.graph.metrics ? state.graph.metrics : {};
    byId('brainNodeCount').textContent = metrics.nodes_total ?? '—';
    byId('brainEdgeCount').textContent = metrics.edges_total ?? '—';
    byId('brainMemoryCount').textContent = state.memory && state.memory.memories_count != null ? state.memory.memories_count : memoryNodes().length;
    byId('brainAgentCount').textContent = state.agents.length;
    const operationsMetrics = state.operations && state.operations.metrics
      ? state.operations.metrics
      : {};
    byId('brainHumanCount').textContent = Number.isInteger(operationsMetrics.waiting_human_total)
      ? operationsMetrics.waiting_human_total
      : 0;
    byId('secondBrainNavBadge').textContent = metrics.nodes_total ? metrics.nodes_total + ' NÓS' : 'GRAFO';
    const timestamp = state.graph && state.graph.generated_at ? new Date(state.graph.generated_at) : null;
    byId('brainGeneratedAt').textContent = timestamp && !Number.isNaN(timestamp.getTime()) ? 'ATUALIZADO ' + timestamp.toLocaleTimeString('pt-BR') : 'DADOS ATUAIS';
  }

  async function load() {
    const empty = byId('brainEmpty');
    const refresh = byId('brainRefresh');
    refresh.disabled = true;
    empty.hidden = false;
    empty.textContent = 'Mapeando arquivos e relações…';
    try {
      const [graph, memory, agents, operations] = await Promise.all([
        getJson('/api/second-brain/graph?max_nodes=320&max_edges=1200'),
        getJson('/api/memory').catch(() => ({ memories: [], memories_count: 0 })),
        getJson('/api/quantum-agents').catch(() => []),
        getJson('/api/second-brain/operations').catch(() => ({ missions: [], metrics: {} }))
      ]);
      state.graph = graph;
      state.memory = memory;
      state.agents = Array.isArray(agents) ? agents : [];
      state.operations = operations && typeof operations === 'object' ? operations : { missions: [] };
      const missions = Array.isArray(state.operations.missions) ? state.operations.missions : [];
      if (!missions.some((mission) => mission.mission_id === state.missionId)) {
        state.missionId = missions.length ? missions[0].mission_id : null;
      }
      updateSummary();
      renderOperations();
      renderAgentOffice();
      renderGraph();
    } catch (error) {
      empty.hidden = false;
      empty.textContent = 'Grafo indisponível: ' + error.message;
      console.warn('[JARVIS second-brain]', error);
    } finally {
      refresh.disabled = false;
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    byId('brainSearch').addEventListener('input', (event) => {
      state.query = event.target.value || '';
      applySearch();
    });
    byId('brainRefresh').addEventListener('click', load);
    byId('brainMissionSelect').addEventListener('change', (event) => {
      state.missionId = event.target.value || null;
      renderOperations();
      renderAgentOffice();
      renderGraph();
    });
    renderDetails({ id: '__brain__', label: 'Centro cognitivo', kind: 'core', tags: [], degree: 0 });
    load();
  });
})();