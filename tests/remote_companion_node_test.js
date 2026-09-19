'use strict';

const assert = require('assert');
const { STATES, createRemoteCompanion } = require('../ui/remote-companion.js');

function memoryStorage(seed = {}) {
  const data = new Map(Object.entries(seed));
  return {
    getItem(key) { return data.has(key) ? data.get(key) : null; },
    setItem(key, value) { data.set(key, String(value)); },
    removeItem(key) { data.delete(key); },
    dump() { return Object.fromEntries(data.entries()); },
  };
}

function response(status, body) {
  return {
    ok: status >= 200 && status < 300,
    status,
    async json() { return body; },
  };
}

async function testOfflineBlocksFakeSend() {
  const calls = [];
  const localStore = memoryStorage({
    'jarvis.remote.device_id': 'device-1',
    'jarvis.remote.session_id': 'session-1',
  });
  const sessionStore = memoryStorage({ 'jarvis.remote.credential': 'c'.repeat(64) });
  const client = createRemoteCompanion({
    localStore,
    sessionStore,
    fetcher: async (path) => {
      calls.push(path);
      if (path.endsWith('/host')) return response(200, { status: 'OFFLINE' });
      throw new Error('message endpoint must not be called while host is offline');
    },
  });

  await client.refreshHost();
  assert.strictEqual(client.getState(), STATES.HOST_OFFLINE);
  await assert.rejects(() => client.sendMessage('continue'), /offline/i);
  assert.strictEqual(calls.filter((x) => x.includes('/messages')).length, 0);
}

async function testReconnectUsesLastCursor() {
  const calls = [];
  const localStore = memoryStorage({
    'jarvis.remote.device_id': 'device-1',
    'jarvis.remote.session_id': 'session-1',
    'jarvis.remote.cursor': '7',
  });
  const sessionStore = memoryStorage({ 'jarvis.remote.credential': 'd'.repeat(64) });
  const client = createRemoteCompanion({
    localStore,
    sessionStore,
    fetcher: async (path, init = {}) => {
      calls.push({ path, init });
      if (path.endsWith('/host')) return response(200, { status: 'ONLINE' });
      if (path === '/api/remote/v1/sessions/session-1') {
        return response(200, { session_id: 'session-1', device_id: 'device-1', status: 'OPEN' });
      }
      if (path.includes('/events?after=7&limit=100')) {
        return response(200, {
          session_id: 'session-1',
          after: 7,
          events: [{ seq: 8, kind: 'assistant_message', payload: { text: 'resumed' } }],
        });
      }
      if (path.endsWith('/ack')) return response(200, { last_ack_seq: 8 });
      throw new Error(`unexpected request ${path}`);
    },
  });

  await client.connect();
  assert.strictEqual(client.getState(), STATES.SESSION_RESUMED);
  assert(calls.some((entry) => entry.path.includes('/events?after=7&limit=100')));
  assert.strictEqual(localStore.getItem('jarvis.remote.cursor'), '8');
}

async function testRevokedDeviceTransitionsToRepair() {
  const localStore = memoryStorage({
    'jarvis.remote.device_id': 'device-1',
    'jarvis.remote.session_id': 'session-1',
  });
  const sessionStore = memoryStorage({ 'jarvis.remote.credential': 'e'.repeat(64) });
  const client = createRemoteCompanion({
    localStore,
    sessionStore,
    fetcher: async (path) => {
      if (path.endsWith('/host')) return response(200, { status: 'ONLINE' });
      if (path === '/api/remote/v1/sessions/session-1') {
        return response(403, { status: 'ERROR', reason: 'REMOTE_DEVICE_NOT_AUTHORIZED' });
      }
      throw new Error(`unexpected request ${path}`);
    },
  });

  await client.connect();
  assert.strictEqual(client.getState(), STATES.DEVICE_REVOKED);
  assert.strictEqual(sessionStore.getItem('jarvis.remote.credential'), null);
}

async function testPairingPersistsCredentialForRememberedDevice() {
  const localStore = memoryStorage();
  const sessionStore = memoryStorage();
  const credential = 'f'.repeat(64);
  const client = createRemoteCompanion({
    localStore,
    sessionStore,
    credentialFactory: () => credential,
    fetcher: async (path, init = {}) => {
      if (path.endsWith('/pairing/complete')) {
        const body = JSON.parse(init.body);
        assert.strictEqual(body.credential, credential);
        return response(201, { device_id: 'device-paired', label: 'Phone', status: 'ACTIVE' });
      }
      throw new Error(`unexpected request ${path}`);
    },
  });

  await client.completePairing({ offerId: 'offer-1', pairingSecret: 'secret-1', label: 'Phone' });
  assert.strictEqual(client.getState(), STATES.DEVICE_TRUSTED);
  assert.strictEqual(localStore.getItem('jarvis.remote.device_id'), 'device-paired');
  assert.strictEqual(sessionStore.getItem('jarvis.remote.credential'), credential);
  assert.strictEqual(localStore.getItem('jarvis.remote.credential'), credential);
}

async function testPairingCanRemainSessionOnly() {
  const localStore = memoryStorage();
  const sessionStore = memoryStorage();
  const credential = 'h'.repeat(64);
  const client = createRemoteCompanion({
    localStore,
    sessionStore,
    credentialFactory: () => credential,
    fetcher: async (path, init = {}) => {
      if (path.endsWith('/pairing/complete')) {
        return response(201, { device_id: 'device-session', label: 'Phone', status: 'ACTIVE' });
      }
      throw new Error(`unexpected request ${path}`);
    },
  });
  await client.completePairing({
    offerId: 'offer-2',
    pairingSecret: 'secret-2',
    label: 'Phone',
    rememberDevice: false,
  });
  assert.strictEqual(sessionStore.getItem('jarvis.remote.credential'), credential);
  assert.strictEqual(localStore.getItem('jarvis.remote.credential'), null);
}


async function testPairingOfferUsesVerifiedRemoteEndpoint() {
  const client = createRemoteCompanion({
    localStore: memoryStorage(),
    sessionStore: memoryStorage(),
    origin: 'http://127.0.0.1:8899',
    fetcher: async (path) => {
      if (path.endsWith('/pairing/offers')) {
        return response(201, {
          offer_id: 'offer-remote',
          pairing_secret: 's'.repeat(64),
          pairing_endpoint: 'http://100.101.102.103:8899',
        });
      }
      throw new Error(`unexpected request ${path}`);
    },
  });

  const offer = await client.createPairingOffer('Phone');
  assert(offer.pairing_url.startsWith('http://100.101.102.103:8899/remote?remote=1'));
  assert(!offer.pairing_url.includes('127.0.0.1'));
}


async function testPairingOfferUsesHttpsServeRemoteShell() {
  const client = createRemoteCompanion({
    localStore: memoryStorage(),
    sessionStore: memoryStorage(),
    origin: 'http://127.0.0.1:8899',
    credentialFactory: () => 'f'.repeat(64),
    fetcher: async (path) => {
      if (path.endsWith('/pairing/offers')) {
        return response(201, {
          offer_id: 'offer-https',
          pairing_secret: 's'.repeat(43),
          pairing_endpoint: 'https://home-pc.example.ts.net',
        });
      }
      throw new Error(`unexpected request ${path}`);
    },
  });
  const offer = await client.createPairingOffer('Phone');
  assert(offer.pairing_url.startsWith('https://home-pc.example.ts.net/remote?remote=1'));
  assert(offer.pairing_url.includes('offer=offer-https'));
}

async function testCommandApprovalFlow() {
  const calls = [];
  const localStore = memoryStorage({
    'jarvis.remote.device_id': 'device-1',
    'jarvis.remote.session_id': 'session-1',
  });
  const sessionStore = memoryStorage({ 'jarvis.remote.credential': 'g'.repeat(64) });
  const ids = ['req-command', 'req-approval'];
  const client = createRemoteCompanion({
    localStore,
    sessionStore,
    requestIdFactory: () => ids.shift(),
    fetcher: async (path, init = {}) => {
      if (path.endsWith('/host')) return response(200, { status: 'ONLINE' });
      if (path === '/api/remote/v1/sessions/session-1') {
        return response(200, { session_id: 'session-1', device_id: 'device-1', status: 'OPEN' });
      }
      if (path.includes('/events?after=0&limit=100')) {
        return response(200, { session_id: 'session-1', after: 0, events: [] });
      }
      if (path.endsWith('/messages')) {
        const body = JSON.parse(init.body);
        calls.push(body);
        if (body.kind === 'command') {
          return response(202, {
            status: 'APPROVAL_REQUIRED',
            action_id: 'rcmd-' + 'a'.repeat(24),
            action_digest: 'b'.repeat(64),
          });
        }
        if (body.kind === 'approve_action') {
          return response(202, { status: 'PASS', exit_code: 0 });
        }
      }
      throw new Error(`unexpected request ${path}`);
    },
  });

  await client.connect();
  const requested = await client.sendCommand(
    'python tooling/validate_v020_plan4.py --gate portable-runtime',
    { timeoutSeconds: 300 },
  );
  assert.strictEqual(requested.status, 'APPROVAL_REQUIRED');
  assert.deepStrictEqual(calls[0].payload.argv, [
    'python',
    'tooling/validate_v020_plan4.py',
    '--gate',
    'portable-runtime',
  ]);
  assert.strictEqual(calls[0].payload.timeout_seconds, 300);

  const approved = await client.approveAction(requested.action_id, requested.action_digest);
  assert.strictEqual(approved.status, 'PASS');
  assert.strictEqual(calls[1].kind, 'approve_action');
  assert.strictEqual(calls[1].payload.action_id, requested.action_id);
  assert.strictEqual(calls[1].payload.action_digest, requested.action_digest);
}

async function testNaturalLanguageTaskApprovalFlow() {
  const calls = [];
  const localStore = memoryStorage({
    'jarvis.remote.device_id': 'device-1',
    'jarvis.remote.session_id': 'session-1',
  });
  const sessionStore = memoryStorage({ 'jarvis.remote.credential': 'i'.repeat(64) });
  const ids = ['req-task', 'req-plan'];
  const client = createRemoteCompanion({
    localStore,
    sessionStore,
    requestIdFactory: () => ids.shift(),
    fetcher: async (path, init = {}) => {
      if (path.endsWith('/host')) return response(200, { status: 'ONLINE' });
      if (path === '/api/remote/v1/sessions/session-1') {
        return response(200, { session_id: 'session-1', device_id: 'device-1', status: 'OPEN' });
      }
      if (path.includes('/events?after=0&limit=100')) {
        return response(200, { session_id: 'session-1', after: 0, events: [] });
      }
      if (path.endsWith('/messages')) {
        const body = JSON.parse(init.body);
        calls.push(body);
        if (body.kind === 'task') {
          return response(202, {
            status: 'PLAN_APPROVAL_REQUIRED',
            task_id: 'rtask-' + 'a'.repeat(24),
            plan_digest: 'b'.repeat(64),
          });
        }
        if (body.kind === 'approve_plan') {
          return response(202, { status: 'COMPLETED' });
        }
      }
      throw new Error(`unexpected request ${path}`);
    },
  });

  await client.connect();
  const planned = await client.sendTask('corrija o login e rode os testes focados');
  assert.strictEqual(planned.status, 'PLAN_APPROVAL_REQUIRED');
  assert.strictEqual(calls[0].kind, 'task');
  assert.strictEqual(calls[0].payload.goal, 'corrija o login e rode os testes focados');

  const approved = await client.approvePlan(planned.task_id, planned.plan_digest);
  assert.strictEqual(approved.status, 'COMPLETED');
  assert.strictEqual(calls[1].kind, 'approve_plan');
  assert.strictEqual(calls[1].payload.task_id, planned.task_id);
  assert.strictEqual(calls[1].payload.plan_digest, planned.plan_digest);
}

(async () => {
  await testOfflineBlocksFakeSend();
  await testReconnectUsesLastCursor();
  await testRevokedDeviceTransitionsToRepair();
  await testPairingPersistsCredentialForRememberedDevice();
  await testPairingCanRemainSessionOnly();
  await testPairingOfferUsesVerifiedRemoteEndpoint();
  await testPairingOfferUsesHttpsServeRemoteShell();
  await testCommandApprovalFlow();
  await testNaturalLanguageTaskApprovalFlow();
  process.stdout.write('remote companion node contract: PASS\n');
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
