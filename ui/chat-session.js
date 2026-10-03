/* Page-lifetime chat grant. No persistent storage; only /api/chat receives it. */
(function (root) {
  'use strict';
  function createChatSession(fetcher) {
    let token = '';
    return Object.freeze({
      isAuthorized() { return Boolean(token); },
      authorize(value) {
        token = '';
        if (typeof value !== 'string' || !value.trim() || /[\r\n]/.test(value)) return false;
        token = value.trim();
        return true;
      },
      clear() { token = ''; },
      async send(payload) {
        if (!token) throw new Error('Informe o token de acesso ao chat.');
        if (!['openai', 'groq', 'gemini', 'openrouter'].includes(payload.provider) ||
            typeof payload.model !== 'string' || !payload.model.trim()) {
          throw new Error('Selecione um provedor e informe o modelo explicitamente.');
        }
        return fetcher('/api/chat', {
          method: 'POST', redirect: 'error',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({ message: payload.message, provider: payload.provider,
            model: payload.model, apiKey: payload.apiKey })
        });
      }
    });
  }
  function detectApiKeyProvider(value) {
    if (typeof value !== 'string') return null;
    const key = value.trim();
    if (key.startsWith('gsk_')) return 'groq';
    if (key.startsWith('AQ.') || key.startsWith('AIza')) return 'gemini';
    if (key.startsWith('sk-or-')) return 'openrouter';
    if (key.startsWith('sk-')) return 'openai';
    return null;
  }
  function describeReply(data) {
    if (!data || !['BLOCKED', 'UNVERIFIED'].includes(data.status) || typeof data.reply !== 'string' || !data.reply.trim()) {
      return { status: 'BLOCKED', label: 'BLOCKED — resposta inválida', reply: 'O servidor não retornou uma resposta válida.' };
    }
    return { status: data.status, label: data.status === 'BLOCKED' ? 'BLOCKED — solicitação bloqueada' :
      'UNVERIFIED — resposta sem verificação independente', reply: data.reply };
  }
  const api = { createChatSession, detectApiKeyProvider, describeReply };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.JarvisChat = api;
})(globalThis);
