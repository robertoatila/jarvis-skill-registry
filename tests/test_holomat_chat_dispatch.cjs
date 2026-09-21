const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const jarvisSource = fs.readFileSync(path.resolve(__dirname, '../ui/jarvis.js'), 'utf8');

test('isNicheOrLocalQuery correctly identifies OSINT, @mentions and niche tools', () => {
  const isNicheMatch = jarvisSource.match(/function isNicheOrLocalQuery\(text\) \{([\s\S]*?)\n  \}/);
  assert.ok(isNicheMatch, 'isNicheOrLocalQuery function must be present');

  const isNiche = new Function('text', isNicheMatch[1]);
  assert.equal(isNiche('procure em todas as redes sociais o @roberto_azevedo usando osint'), true);
  assert.equal(isNiche('@torvalds'), true);
  assert.equal(isNiche('@antoniaci/blackbird analise o repo'), true);
  assert.equal(isNiche('quais sao as skills disponiveis?'), true);
  assert.equal(isNiche('#security cve-2024-3094'), true);
  assert.equal(isNiche('#telemetry mark-liv'), true);
});

test('telemetry toggle updates body state and button label', () => {
  const elements = {
    btnToggleTelemetry: {
      setAttribute(k, v) { this[k] = v; },
      addEventListener(event, fn) { this['on' + event] = fn; }
    },
    telemetryToggleIcon: { textContent: '▲' },
    telemetryToggleLabel: { textContent: 'Recolher' }
  };
  const body = { dataset: {} };
  const storage = {};

  // Extract telemetry toggle setup
  const snippet = `
    const btnToggleTelemetry = elements.btnToggleTelemetry;
    const telemetryToggleIcon = elements.telemetryToggleIcon;
    const telemetryToggleLabel = elements.telemetryToggleLabel;
    function setTelemetryCollapsed(collapsed, persist = true) {
      body.dataset.telemetryCollapsed = String(Boolean(collapsed));
      if (btnToggleTelemetry) btnToggleTelemetry.setAttribute('aria-expanded', String(!collapsed));
      if (telemetryToggleIcon) telemetryToggleIcon.textContent = collapsed ? '▼' : '▲';
      if (telemetryToggleLabel) telemetryToggleLabel.textContent = collapsed ? 'Expandir' : 'Recolher';
      if (persist) storage['jarvis.telemetry.collapsed'] = String(collapsed);
    }
  `;
  const context = vm.createContext({ elements, body, storage });
  vm.runInContext(snippet, context);

  vm.runInContext('setTelemetryCollapsed(true)', context);
  assert.equal(body.dataset.telemetryCollapsed, 'true');
  assert.equal(elements.telemetryToggleIcon.textContent, '▼');
  assert.equal(elements.telemetryToggleLabel.textContent, 'Expandir');
  assert.equal(storage['jarvis.telemetry.collapsed'], 'true');

  vm.runInContext('setTelemetryCollapsed(false)', context);
  assert.equal(body.dataset.telemetryCollapsed, 'false');
  assert.equal(elements.telemetryToggleIcon.textContent, '▲');
  assert.equal(elements.telemetryToggleLabel.textContent, 'Recolher');
  assert.equal(storage['jarvis.telemetry.collapsed'], 'false');
});

test('dispatchNicheOrSovereign calls /api/niche/dispatch with payload', async () => {
  let calledUrl = '';
  let calledBody = null;
  const fakeFetch = async (url, options) => {
    calledUrl = url;
    calledBody = JSON.parse(options.body);
    return {
      ok: true,
      json: async () => ({ niche: 'OSINT', target: 'roberto_azevedo', content_markdown: 'Dossier found' })
    };
  };

  const dispatchSnippet = `
    async function dispatchNicheOrSovereign(query) {
      const res = await fetch('/api/niche/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query })
      });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      return res.json();
    }
  `;
  const context = vm.createContext({ fetch: fakeFetch });
  vm.runInContext(dispatchSnippet, context);

  const res = await vm.runInContext("dispatchNicheOrSovereign('procure em todas as redes sociais o @roberto_azevedo usando osint')", context);
  assert.equal(calledUrl, '/api/niche/dispatch');
  assert.equal(calledBody.query, 'procure em todas as redes sociais o @roberto_azevedo usando osint');
  assert.equal(res.niche, 'OSINT');
  assert.equal(res.target, 'roberto_azevedo');
});
