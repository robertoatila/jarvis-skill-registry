const { test } = require('node:test');
const assert = require('node:assert/strict');
const { createChatSession, describeReply } = require('../ui/chat-session.js');
const payload = { message: 'hello', provider: 'groq', model: 'explicit-model', apiKey: 'provider-key' };
test('missing/invalid grant and implicit routing never send', async () => {
  let calls = 0;
  const session = createChatSession(() => { calls++; });
  await assert.rejects(session.send(payload));
  assert.equal(session.authorize('bad\r\ntoken'), false);
  session.authorize('access-token');
  await assert.rejects(session.send({ ...payload, provider: 'auto' }));
  await assert.rejects(session.send({ ...payload, model: '' }));
  assert.equal(calls, 0);
});
test('grant sent only in fixed chat header, redirects refused, body allowlisted', async () => {
  let request;
  const session = createChatSession(async (...args) => { request = args; return { ok: true }; });
  session.authorize('access-token');
  await session.send({ ...payload, token: 'access-token', url: 'https://other.invalid' });
  assert.equal(request[0], '/api/chat');
  assert.equal(request[1].headers.Authorization, 'Bearer access-token');
  assert.equal(request[1].redirect, 'error');
  assert.deepEqual(JSON.parse(request[1].body), payload);
  session.clear();
  await assert.rejects(session.send(payload));
});
test('separate page sessions do not inherit grants', async () => {
  const one = createChatSession(async () => ({}));
  one.authorize('access-token');
  await assert.rejects(createChatSession(async () => ({})).send(payload));
});
test('transport failure does not retry', async () => {
  let calls = 0;
  const session = createChatSession(async () => { calls++; throw new Error('network'); });
  session.authorize('access-token');
  await assert.rejects(session.send(payload), /network/);
  assert.equal(calls, 1);
});
test('blocked/unverified are explicit and malformed results never become success', () => {
  assert.match(describeReply({ status: 'BLOCKED', reply: 'Denied' }).label, /BLOCKED/);
  assert.match(describeReply({ status: 'UNVERIFIED', reply: '<script>x</script>' }).label, /sem verificação/);
  for (const data of [null, {}, { status: 'SUCCEEDED', reply: 'ok' }, { status: 'UNVERIFIED', reply: '' }]) {
    assert.equal(describeReply(data).status, 'BLOCKED');
  }
});
test('actual HUD controls clear input and revoke grant on pagehide', async () => {
  const fs = require('node:fs');
  const vm = require('node:vm');
  const source = fs.readFileSync(require.resolve('../ui/jarvis.js'), 'utf8');
  const listeners = {};
  const elements = {};
  for (const id of ['inputChatToken', 'chatTokenStatus', 'btnSetChatToken', 'btnClearChatToken']) {
    elements[id] = { value: '', addEventListener(event, fn) { listeners[id + event] = fn; } };
  }
  let sent = 0;
  const context = vm.createContext({
    JarvisChat: require('../ui/chat-session.js'),
    document: { getElementById: id => elements[id] },
    window: { fetch: async () => { sent++; return {}; }, addEventListener: (event, fn) => { listeners[event] = fn; } }
  });
  const start = source.indexOf('  const chatSession =');
  const end = source.indexOf("  window.addEventListener('pagehide', clearChatToken);", start);
  assert.ok(start > 0 && end > start);
  vm.runInContext(source.slice(start, end) + "  window.addEventListener('pagehide', clearChatToken);", context);
  elements.inputChatToken.value = 'access-token';
  listeners.btnSetChatTokenclick();
  assert.equal(elements.inputChatToken.value, '');
  await vm.runInContext("chatSession.send({provider:'groq',model:'m',message:'hi'})", context);
  listeners.pagehide();
  await assert.rejects(vm.runInContext("chatSession.send({provider:'groq',model:'m',message:'hi'})", context));
  assert.equal(sent, 1);
  assert.equal(elements.chatTokenStatus.textContent, 'Token ausente.');
});
