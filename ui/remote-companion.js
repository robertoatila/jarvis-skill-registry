/* J.A.R.V.I.S. Universal Remote Companion — thin client for the authoritative PC runtime. */
(function (root, factory) {
  'use strict';
  const api = factory(root);
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else {
    root.JarvisRemoteCompanion = api;
    api.autoMount();
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function (root) {
  'use strict';

  const API_PREFIX = '/api/remote/v1';
  const PROTOCOL_VERSION = 'jarvis-remote/1';
  const KEYS = Object.freeze({
    deviceId: 'jarvis.remote.device_id',
    sessionId: 'jarvis.remote.session_id',
    cursor: 'jarvis.remote.cursor',
    credential: 'jarvis.remote.credential',
  });
  const STATES = Object.freeze({
    HOST_OFFLINE: 'HOST_OFFLINE',
    HOST_ONLINE: 'HOST_ONLINE',
    PAIR_DEVICE: 'PAIR_DEVICE',
    DEVICE_TRUSTED: 'DEVICE_TRUSTED',
    DEVICE_REVOKED: 'DEVICE_REVOKED',
    CONNECTING: 'CONNECTING',
    CONNECTED: 'CONNECTED',
    RECONNECTING: 'RECONNECTING',
    SESSION_RESUMED: 'SESSION_RESUMED',
    MISSION_RUNNING: 'MISSION_RUNNING',
    MISSION_WAITING: 'MISSION_WAITING',
    ERROR: 'ERROR',
  });

  function memoryStorage() {
    const values = new Map();
    return {
      getItem(key) { return values.has(key) ? values.get(key) : null; },
      setItem(key, value) { values.set(key, String(value)); },
      removeItem(key) { values.delete(key); },
    };
  }

  function randomHex(bytes = 32) {
    const cryptoObject = root && root.crypto;
    if (!cryptoObject || typeof cryptoObject.getRandomValues !== 'function') {
      throw new Error('Secure browser randomness is unavailable.');
    }
    const data = new Uint8Array(bytes);
    cryptoObject.getRandomValues(data);
    return Array.from(data, (value) => value.toString(16).padStart(2, '0')).join('');
  }

  function requestId() {
    const cryptoObject = root && root.crypto;
    if (cryptoObject && typeof cryptoObject.randomUUID === 'function') {
      return cryptoObject.randomUUID();
    }
    return `req-${Date.now()}-${randomHex(8)}`;
  }

  async function readBody(response) {
    try {
      return await response.json();
    } catch (_error) {
      return {};
    }
  }

  function parseCommandLine(value) {
    const input = String(value || '').trim();
    if (!input) return [];
    const argv = [];
    let current = '';
    let quote = null;
    for (const ch of input) {
      if (quote) {
        if (ch === quote) quote = null;
        else current += ch;
        continue;
      }
      if (ch === '"' || ch === "'") {
        quote = ch;
        continue;
      }
      if (/\s/.test(ch)) {
        if (current) {
          argv.push(current);
          current = '';
        }
        continue;
      }
      current += ch;
    }
    if (quote) throw new Error('Unclosed quote in command.');
    if (current) argv.push(current);
    return argv;
  }

  function createRemoteCompanion(options = {}) {
    const fetcher = options.fetcher || (root && root.fetch && root.fetch.bind(root));
    if (typeof fetcher !== 'function') throw new TypeError('fetcher must be callable');
    const localStore = options.localStore || (root && root.localStorage) || memoryStorage();
    const sessionStore = options.sessionStore || (root && root.sessionStorage) || memoryStorage();
    const credentialFactory = options.credentialFactory || (() => randomHex(32));
    const requestIdFactory = options.requestIdFactory || requestId;
    const origin = options.origin || (root && root.location && root.location.origin) || '';

    let deviceId = localStore.getItem(KEYS.deviceId) || '';
    let credential = sessionStore.getItem(KEYS.credential) || '';
    let sessionId = localStore.getItem(KEYS.sessionId) || '';
    let cursor = Number.parseInt(localStore.getItem(KEYS.cursor) || '0', 10);
    if (!Number.isInteger(cursor) || cursor < 0) cursor = 0;
    let host = null;
    let state = deviceId && credential ? STATES.CONNECTING : STATES.PAIR_DEVICE;
    let lastError = null;
    const listeners = new Set();
    const eventListeners = new Set();

    function snapshot() {
      return Object.freeze({
        state,
        deviceId: deviceId || null,
        sessionId: sessionId || null,
        cursor,
        host,
        lastError,
        credentialPresent: Boolean(credential),
      });
    }

    function notify() {
      const value = snapshot();
      listeners.forEach((listener) => {
        try { listener(value); } catch (_error) { /* UI listeners are isolated. */ }
      });
    }

    function setState(next, error = null) {
      state = next;
      lastError = error ? String(error.message || error) : null;
      notify();
    }

    function setCursor(value) {
      if (!Number.isInteger(value) || value < cursor) return;
      cursor = value;
      localStore.setItem(KEYS.cursor, String(value));
    }

    function clearSession() {
      sessionId = '';
      cursor = 0;
      localStore.removeItem(KEYS.sessionId);
      localStore.removeItem(KEYS.cursor);
    }

    function markRevoked() {
      credential = '';
      sessionStore.removeItem(KEYS.credential);
      clearSession();
      setState(STATES.DEVICE_REVOKED);
    }

    function deviceHeaders(extra = {}) {
      const headers = { ...extra };
      if (deviceId && credential) {
        headers['X-Jarvis-Device-ID'] = deviceId;
        headers['X-Jarvis-Device-Credential'] = credential;
      }
      return headers;
    }

    async function request(path, init = {}, requireDevice = true) {
      const headers = requireDevice ? deviceHeaders(init.headers || {}) : { ...(init.headers || {}) };
      const response = await fetcher(path, { ...init, headers });
      const body = await readBody(response);
      if (response.status === 403 && requireDevice) {
        markRevoked();
      }
      return { response, body };
    }

    async function refreshHost() {
      if (!deviceId || !credential) {
        setState(STATES.PAIR_DEVICE);
        return snapshot();
      }
      setState(STATES.CONNECTING);
      try {
        const { response, body } = await request(`${API_PREFIX}/host`);
        if (response.status === 403) return snapshot();
        if (!response.ok || body.status !== 'ONLINE') {
          host = body || null;
          setState(STATES.HOST_OFFLINE);
          return snapshot();
        }
        host = body;
        setState(STATES.HOST_ONLINE);
        return snapshot();
      } catch (error) {
        host = null;
        setState(STATES.HOST_OFFLINE, error);
        return snapshot();
      }
    }

    async function createPairingOffer(labelHint = '') {
      const { response, body } = await request(
        `${API_PREFIX}/pairing/offers`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ label_hint: String(labelHint || '').trim() || null }),
        },
        false,
      );
      if (!response.ok || !body.offer_id || !body.pairing_secret) {
        throw new Error(body.reason || 'Pairing offer could not be created on this host.');
      }
      let base = origin || '';
      if (typeof body.pairing_endpoint === 'string' && body.pairing_endpoint.trim()) {
        try {
          const candidate = new URL(body.pairing_endpoint.trim());
          const rootOnly = candidate.pathname === '/' && !candidate.search && !candidate.hash;
          const safeProtocol = candidate.protocol === 'http:' || candidate.protocol === 'https:';
          if (safeProtocol && rootOnly && !candidate.username && !candidate.password) {
            base = candidate.origin;
          }
        } catch (_error) {
          // Invalid advertised endpoints never replace the current trusted origin.
        }
      }
      const url = new URL(base ? `${base}/remote` : '/remote', base || 'http://localhost');
      url.searchParams.set('remote', '1');
      url.searchParams.set('offer', body.offer_id);
      url.searchParams.set('pairing_secret', body.pairing_secret);
      return { ...body, pairing_url: base ? url.toString() : `${url.pathname}${url.search}` };
    }

    async function completePairing({ offerId, pairingSecret, label }) {
      const normalizedOffer = String(offerId || '').trim();
      const normalizedSecret = String(pairingSecret || '').trim();
      const normalizedLabel = String(label || 'Remote device').trim() || 'Remote device';
      if (!normalizedOffer || !normalizedSecret) {
        setState(STATES.PAIR_DEVICE);
        throw new Error('Pairing offer and secret are required.');
      }
      setState(STATES.PAIR_DEVICE);
      const nextCredential = String(credentialFactory());
      if (nextCredential.length < 32 || /[\r\n]/.test(nextCredential)) {
        throw new Error('Generated device credential is invalid.');
      }
      const { response, body } = await request(
        `${API_PREFIX}/pairing/complete`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            offer_id: normalizedOffer,
            pairing_secret: normalizedSecret,
            credential: nextCredential,
            label: normalizedLabel,
          }),
        },
        false,
      );
      if (!response.ok || !body.device_id) {
        setState(STATES.PAIR_DEVICE);
        throw new Error(body.reason || 'Pairing rejected.');
      }
      deviceId = String(body.device_id);
      credential = nextCredential;
      localStore.setItem(KEYS.deviceId, deviceId);
      // Credential is intentionally page/session-lifetime only. It is never put in localStorage.
      sessionStore.setItem(KEYS.credential, credential);
      clearSession();
      setState(STATES.DEVICE_TRUSTED);
      return snapshot();
    }

    async function openSession() {
      const { response, body } = await request(
        `${API_PREFIX}/sessions`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ device_id: deviceId }),
        },
      );
      if (response.status === 403) return snapshot();
      if (!response.ok || !body.session_id) {
        setState(STATES.ERROR, body.reason || 'Remote session could not be opened.');
        return snapshot();
      }
      sessionId = String(body.session_id);
      localStore.setItem(KEYS.sessionId, sessionId);
      setCursor(0);
      setState(STATES.CONNECTED);
      return snapshot();
    }

    async function replayEvents() {
      if (!sessionId || !deviceId || !credential) return [];
      const { response, body } = await request(
        `${API_PREFIX}/sessions/${encodeURIComponent(sessionId)}/events?after=${cursor}&limit=100`,
      );
      if (response.status === 403) return [];
      if (!response.ok || !Array.isArray(body.events)) {
        setState(STATES.ERROR, body.reason || 'Remote event replay failed.');
        return [];
      }
      let latest = cursor;
      for (const event of body.events) {
        if (event && Number.isInteger(event.seq) && event.seq > latest) latest = event.seq;
        eventListeners.forEach((listener) => {
          try { listener(event); } catch (_error) { /* Event rendering is isolated. */ }
        });
      }
      if (latest > cursor) {
        setCursor(latest);
        await request(
          `${API_PREFIX}/sessions/${encodeURIComponent(sessionId)}/ack`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_id: deviceId, seq: latest }),
          },
        );
      }
      return body.events;
    }

    async function connect() {
      if (!deviceId || !credential) {
        setState(STATES.PAIR_DEVICE);
        return snapshot();
      }
      setState(sessionId ? STATES.RECONNECTING : STATES.CONNECTING);
      await refreshHost();
      if (state === STATES.HOST_OFFLINE || state === STATES.DEVICE_REVOKED) return snapshot();

      if (sessionId) {
        const { response, body } = await request(
          `${API_PREFIX}/sessions/${encodeURIComponent(sessionId)}`,
        );
        if (response.status === 403) return snapshot();
        if (response.ok && body && ['OPEN', 'DETACHED'].includes(body.status)) {
          await replayEvents();
          if (state !== STATES.DEVICE_REVOKED && state !== STATES.ERROR) {
            setState(STATES.SESSION_RESUMED);
          }
          return snapshot();
        }
        clearSession();
      }
      return openSession();
    }

    async function sendMessage(text, payload = {}) {
      const message = String(text || '').trim();
      if (!message) throw new Error('Message is required.');
      if (!host || host.status !== 'ONLINE') {
        setState(STATES.HOST_OFFLINE);
        throw new Error('Host offline: message was not sent.');
      }
      if (!deviceId || !credential) {
        setState(STATES.PAIR_DEVICE);
        throw new Error('Pair device before sending messages.');
      }
      if (!sessionId) {
        setState(STATES.RECONNECTING);
        throw new Error('Remote session is not connected.');
      }

      setState(STATES.MISSION_RUNNING);
      const envelope = {
        protocol: PROTOCOL_VERSION,
        session_id: sessionId,
        device_id: deviceId,
        request_id: String(requestIdFactory()),
        kind: 'message',
        payload: { ...(payload && typeof payload === 'object' ? payload : {}), text: message },
      };
      const { response, body } = await request(
        `${API_PREFIX}/sessions/${encodeURIComponent(sessionId)}/messages`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(envelope),
        },
      );
      if (response.status === 403) throw new Error('Device revoked or unauthorized.');
      if (!response.ok) {
        setState(STATES.ERROR, body.reason || 'Remote message failed.');
        throw new Error(body.reason || 'Remote message failed.');
      }
      setState(body.mission_id ? STATES.MISSION_RUNNING : STATES.CONNECTED);
      return body;
    }

    async function sendCommand(command, options = {}) {
      const argv = Array.isArray(command) ? command.map((item) => String(item)) : parseCommandLine(command);
      if (!argv.length) throw new Error('Command is required.');
      if (!host || host.status !== 'ONLINE') {
        setState(STATES.HOST_OFFLINE);
        throw new Error('Host offline: command was not sent.');
      }
      if (!deviceId || !credential) {
        setState(STATES.PAIR_DEVICE);
        throw new Error('Pair device before sending commands.');
      }
      if (!sessionId) {
        setState(STATES.RECONNECTING);
        throw new Error('Remote session is not connected.');
      }
      const timeout = Number.isFinite(Number(options.timeoutSeconds))
        ? Math.trunc(Number(options.timeoutSeconds))
        : 120;
      const envelope = {
        protocol: PROTOCOL_VERSION,
        session_id: sessionId,
        device_id: deviceId,
        request_id: String(requestIdFactory()),
        kind: 'command',
        payload: {
          argv,
          cwd: String(options.cwd || '.'),
          timeout_seconds: timeout,
        },
      };
      const { response, body } = await request(
        `${API_PREFIX}/sessions/${encodeURIComponent(sessionId)}/messages`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(envelope),
        },
      );
      if (response.status === 403) throw new Error('Device revoked or unauthorized.');
      if (!response.ok) {
        setState(STATES.ERROR, body.reason || 'Remote command request failed.');
        throw new Error(body.reason || 'Remote command request failed.');
      }
      setState(body.status === 'APPROVAL_REQUIRED' ? STATES.MISSION_WAITING : STATES.CONNECTED);
      return body;
    }

    async function approveAction(actionId, actionDigest) {
      const normalizedId = String(actionId || '').trim();
      const normalizedDigest = String(actionDigest || '').trim();
      if (!normalizedId || !normalizedDigest) throw new Error('Action id and digest are required.');
      if (!host || host.status !== 'ONLINE') {
        setState(STATES.HOST_OFFLINE);
        throw new Error('Host offline: approval was not sent.');
      }
      if (!sessionId || !deviceId || !credential) {
        throw new Error('Remote session is not connected.');
      }
      setState(STATES.MISSION_RUNNING);
      const envelope = {
        protocol: PROTOCOL_VERSION,
        session_id: sessionId,
        device_id: deviceId,
        request_id: String(requestIdFactory()),
        kind: 'approve_action',
        payload: {
          action_id: normalizedId,
          action_digest: normalizedDigest,
        },
      };
      const { response, body } = await request(
        `${API_PREFIX}/sessions/${encodeURIComponent(sessionId)}/messages`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(envelope),
        },
      );
      if (response.status === 403) throw new Error('Device revoked or unauthorized.');
      if (!response.ok) {
        setState(STATES.ERROR, body.reason || 'Remote approval failed.');
        throw new Error(body.reason || 'Remote approval failed.');
      }
      setState(STATES.CONNECTED);
      return body;
    }

    async function pollOnce() {
      if (!sessionId) return [];
      const events = await replayEvents();
      if (state === STATES.MISSION_RUNNING && events.length === 0) {
        setState(STATES.MISSION_WAITING);
      } else if (events.some((event) => event && event.kind === 'assistant_message')) {
        setState(STATES.CONNECTED);
      }
      return events;
    }

    function disconnect() {
      // Do not close the server-side session: the PC may keep the mission alive.
      if (sessionId) setState(STATES.RECONNECTING);
      else setState(deviceId && credential ? STATES.DEVICE_TRUSTED : STATES.PAIR_DEVICE);
    }

    return Object.freeze({
      refreshHost,
      createPairingOffer,
      completePairing,
      connect,
      sendMessage,
      sendCommand,
      approveAction,
      replayEvents,
      pollOnce,
      disconnect,
      getState: () => state,
      snapshot,
      onState(listener) {
        if (typeof listener !== 'function') throw new TypeError('listener must be callable');
        listeners.add(listener);
        listener(snapshot());
        return () => listeners.delete(listener);
      },
      onEvent(listener) {
        if (typeof listener !== 'function') throw new TypeError('listener must be callable');
        eventListeners.add(listener);
        return () => eventListeners.delete(listener);
      },
    });
  }

  const STATE_LABELS = Object.freeze({
    HOST_OFFLINE: 'HOST OFFLINE',
    HOST_ONLINE: 'HOST ONLINE',
    PAIR_DEVICE: 'PAIR DEVICE',
    DEVICE_TRUSTED: 'DEVICE TRUSTED',
    DEVICE_REVOKED: 'DEVICE REVOKED',
    CONNECTING: 'CONNECTING',
    CONNECTED: 'CONNECTED',
    RECONNECTING: 'RECONNECTING',
    SESSION_RESUMED: 'SESSION RESUMED',
    MISSION_RUNNING: 'MISSION RUNNING',
    MISSION_WAITING: 'MISSION WAITING',
    ERROR: 'ERROR',
  });

  function mountRemoteCompanion() {
    if (!root || !root.document || root.document.getElementById('remoteCompanionApp')) return null;
    const document = root.document;
    const modal = document.getElementById('modalMobileCompanion');
    const body = modal && modal.querySelector('.modal-body');
    if (!body) return null;

    const shell = document.createElement('section');
    shell.id = 'remoteCompanionApp';
    shell.className = 'remote-companion-app';
    shell.setAttribute('aria-label', 'JARVIS Remote Companion');
    shell.innerHTML = `
      <div class="remote-companion-head">
        <div>
          <span class="remote-kicker">UNIVERSAL REMOTE // SAME PC BRAIN</span>
          <h3>J.A.R.V.I.S. Remote Companion</h3>
        </div>
        <span id="remoteCompanionState" class="remote-state">PAIR DEVICE</span>
      </div>
      <div id="remoteCompanionHost" class="remote-host-line">Host ainda não verificado.</div>
      <div class="remote-pair-grid" id="remotePairPanel">
        <label>Dispositivo<input id="remoteDeviceLabel" class="hud-input" value="Remote device" autocomplete="off"></label>
        <label>Offer ID<input id="remotePairOffer" class="hud-input" autocomplete="off"></label>
        <label>Pairing secret<input id="remotePairSecret" class="hud-input" type="password" autocomplete="off"></label>
        <div class="remote-actions">
          <button id="remoteCreateOffer" class="btn-hud-secondary" type="button">Gerar link no PC</button>
          <button id="remotePairDevice" class="btn-hud-primary" type="button">Parear dispositivo</button>
        </div>
        <input id="remotePairUrl" class="hud-input remote-pair-url" readonly aria-label="Link de pareamento">
      </div>
      <div class="remote-session-grid">
        <div class="remote-actions">
          <button id="remoteConnect" class="btn-hud-primary" type="button">Conectar / Retomar</button>
          <button id="remoteDisconnect" class="btn-hud-secondary" type="button">Desanexar</button>
        </div>
        <div id="remoteEventLog" class="remote-event-log" role="log" aria-live="polite"></div>
        <div class="remote-compose">
          <textarea id="remoteMessage" class="hud-input" rows="3" placeholder="Mensagem para o J.A.R.V.I.S. do PC"></textarea>
          <button id="remoteSend" class="btn-hud-primary" type="button" disabled>Enviar</button>
        </div>
        <div class="remote-compose remote-command-compose">
          <input id="remoteCommand" class="hud-input" autocomplete="off" spellcheck="false" placeholder="Comando no PC: python tooling/validate_v020_plan4.py --gate portable-runtime">
          <button id="remoteRunCommand" class="btn-hud-secondary" type="button" disabled>Solicitar execução</button>
        </div>
      </div>`;
    body.appendChild(shell);

    const params = new URLSearchParams(root.location ? root.location.search : '');
    const remoteEntry = params.get('remote') === '1';
    const offerFromUrl = params.get('offer') || '';
    const secretFromUrl = params.get('pairing_secret') || '';
    const offerInput = document.getElementById('remotePairOffer');
    const secretInput = document.getElementById('remotePairSecret');
    if (offerFromUrl) offerInput.value = offerFromUrl;
    if (secretFromUrl) secretInput.value = secretFromUrl;
    if (secretFromUrl && root.history && root.location) {
      const cleaned = new URL(root.location.href);
      cleaned.searchParams.delete('pairing_secret');
      cleaned.searchParams.delete('offer');
      root.history.replaceState({}, document.title, `${cleaned.pathname}${cleaned.search}${cleaned.hash}`);
    }
    if (remoteEntry || offerFromUrl || secretFromUrl) {
      document.body.classList.add('remote-companion-mode');
      modal.classList.add('active');
      modal.style.display = 'flex';
    }

    const client = createRemoteCompanion();
    const stateEl = document.getElementById('remoteCompanionState');
    const hostEl = document.getElementById('remoteCompanionHost');
    const sendButton = document.getElementById('remoteSend');
    const messageInput = document.getElementById('remoteMessage');
    const commandInput = document.getElementById('remoteCommand');
    const runCommandButton = document.getElementById('remoteRunCommand');
    const eventLog = document.getElementById('remoteEventLog');
    const pairUrl = document.getElementById('remotePairUrl');
    const connectButton = document.getElementById('remoteConnect');

    function renderState(value) {
      stateEl.textContent = STATE_LABELS[value.state] || value.state;
      stateEl.dataset.state = value.state;
      const transport = value.host && value.host.transport_status;
      const endpoint = transport && transport.public_or_private_endpoint;
      hostEl.textContent = value.host && value.host.status === 'ONLINE'
        ? `HOME-PC ONLINE${endpoint ? ` // ${endpoint}` : ''}`
        : (value.lastError ? `Host indisponível // ${value.lastError}` : 'Host ainda não verificado.');
      const interactive = [
        STATES.CONNECTED,
        STATES.SESSION_RESUMED,
        STATES.MISSION_RUNNING,
        STATES.MISSION_WAITING,
      ].includes(value.state);
      sendButton.disabled = !interactive;
      runCommandButton.disabled = !interactive;
      connectButton.disabled = value.state === STATES.CONNECTING;
    }

    function appendEvent(event) {
      if (!event || !eventLog) return;
      const row = document.createElement('div');
      row.className = `remote-event remote-event-${String(event.kind || 'event').replace(/[^a-z0-9_-]/gi, '')}`;
      const payload = event.payload && typeof event.payload === 'object' ? event.payload : {};
      if (event.kind === 'approval_required' && payload.action_id && payload.action_digest) {
        const argv = payload.command && Array.isArray(payload.command.argv)
          ? payload.command.argv.join(' ')
          : 'command';
        const label = document.createElement('div');
        label.textContent = `[${event.seq || '—'}] Aprovação necessária // ${argv}`;
        const button = document.createElement('button');
        button.className = 'btn-hud-primary';
        button.type = 'button';
        button.textContent = 'Aprovar no PC';
        button.addEventListener('click', async () => {
          button.disabled = true;
          try {
            await client.approveAction(payload.action_id, payload.action_digest);
            await client.pollOnce();
          } catch (error) {
            appendEvent({ seq: '!', kind: 'error', payload: { text: error.message } });
            button.disabled = false;
          }
        });
        row.appendChild(label);
        row.appendChild(button);
      } else if (event.kind === 'action_receipt' && payload.receipt) {
        const receipt = payload.receipt;
        const text = `${receipt.status || 'UNKNOWN'} // exit=${receipt.exit_code ?? '—'}`;
        row.textContent = `[${event.seq || '—'}] ${text}`;
        const output = [receipt.stdout, receipt.stderr].filter(Boolean).join('\n');
        if (output) {
          const pre = document.createElement('pre');
          pre.textContent = output;
          row.appendChild(pre);
        }
      } else {
        const text = payload.text || payload.reply || payload.reason || event.kind || 'event';
        row.textContent = `[${event.seq || '—'}] ${text}`;
      }
      eventLog.appendChild(row);
      eventLog.scrollTop = eventLog.scrollHeight;
    }

    client.onState(renderState);
    client.onEvent(appendEvent);

    document.getElementById('remoteCreateOffer').addEventListener('click', async () => {
      try {
        const offer = await client.createPairingOffer(document.getElementById('remoteDeviceLabel').value);
        offerInput.value = offer.offer_id;
        secretInput.value = offer.pairing_secret;
        pairUrl.value = offer.pairing_url;
      } catch (error) {
        stateEl.textContent = `ERROR // ${error.message}`;
      }
    });

    document.getElementById('remotePairDevice').addEventListener('click', async () => {
      try {
        await client.completePairing({
          offerId: offerInput.value,
          pairingSecret: secretInput.value,
          label: document.getElementById('remoteDeviceLabel').value,
        });
        secretInput.value = '';
        await client.connect();
      } catch (error) {
        stateEl.textContent = `ERROR // ${error.message}`;
      }
    });

    connectButton.addEventListener('click', () => client.connect());
    document.getElementById('remoteDisconnect').addEventListener('click', () => client.disconnect());
    sendButton.addEventListener('click', async () => {
      const text = messageInput.value.trim();
      if (!text) return;
      try {
        await client.sendMessage(text);
        appendEvent({ seq: 'local', kind: 'user', payload: { text } });
        messageInput.value = '';
        await client.pollOnce();
      } catch (error) {
        appendEvent({ seq: '!', kind: 'error', payload: { text: error.message } });
      }
    });

    runCommandButton.addEventListener('click', async () => {
      const command = commandInput.value.trim();
      if (!command) return;
      try {
        const result = await client.sendCommand(command);
        appendEvent({
          seq: 'local',
          kind: 'command_requested',
          payload: { text: `Solicitado // ${command} // ${result.status || ''}` },
        });
        await client.pollOnce();
      } catch (error) {
        appendEvent({ seq: '!', kind: 'error', payload: { text: error.message } });
      }
    });

    let pollTimer = root.setInterval ? root.setInterval(async () => {
      const current = client.getState();
      if ([STATES.CONNECTED, STATES.SESSION_RESUMED, STATES.MISSION_RUNNING, STATES.MISSION_WAITING].includes(current)) {
        try { await client.pollOnce(); } catch (_error) { /* State machine reports degradation. */ }
      }
    }, 2000) : null;

    if (root.addEventListener) {
      root.addEventListener('pagehide', () => {
        if (pollTimer && root.clearInterval) root.clearInterval(pollTimer);
        pollTimer = null;
        client.disconnect();
      }, { once: true });
    }

    const initial = client.snapshot();
    if (initial.credentialPresent) client.connect();
    else renderState(initial);

    if (root.navigator && 'serviceWorker' in root.navigator && root.location) {
      const secure = root.location.protocol === 'https:' || ['localhost', '127.0.0.1', '::1'].includes(root.location.hostname);
      if (secure) root.navigator.serviceWorker.register('/service-worker.js').catch(() => {});
    }
    return client;
  }

  function autoMount() {
    if (!root || !root.document) return;
    if (root.document.readyState === 'loading') {
      root.document.addEventListener('DOMContentLoaded', mountRemoteCompanion, { once: true });
    } else {
      mountRemoteCompanion();
    }
  }

  return Object.freeze({ STATES, parseCommandLine, createRemoteCompanion, mountRemoteCompanion, autoMount });
});
