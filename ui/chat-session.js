/* Page-lifetime chat grant. No persistent storage; only /api/chat receives it. */
(function (root) {
  'use strict';
  function createChatSession(fetcher) {
    let token = '';
    return Object.freeze({
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
  function describeReply(data) {
    if (!data || !['BLOCKED', 'UNVERIFIED'].includes(data.status) || typeof data.reply !== 'string' || !data.reply.trim()) {
      return { status: 'BLOCKED', label: 'BLOCKED — resposta inválida', reply: 'O servidor não retornou uma resposta válida.' };
    }
    return { status: data.status, label: data.status === 'BLOCKED' ? 'BLOCKED — solicitação bloqueada' :
      'UNVERIFIED — resposta sem verificação independente', reply: data.reply };
  }
  const api = { createChatSession, describeReply };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.JarvisChat = api;
})(globalThis);

/* Browser-only progressive enhancement. Node/CommonJS tests remain dependency-free. */
if (typeof document !== 'undefined' && !document.querySelector('script[data-jarvis-experience]')) {
  const experienceScript = document.createElement('script');
  experienceScript.src = '/assets/design-system/experience-system.js';
  experienceScript.dataset.jarvisExperience = 'v2';
  experienceScript.async = false;
  document.head.appendChild(experienceScript);
}

/* Universal Remote Companion bootstrap: isolated from the large desktop HUD bundle. */
if (typeof document !== 'undefined') {
  if (!document.querySelector('link[rel="manifest"][data-jarvis-remote]')) {
    const manifest = document.createElement('link');
    manifest.rel = 'manifest';
    manifest.href = '/manifest.webmanifest';
    manifest.dataset.jarvisRemote = 'v1';
    document.head.appendChild(manifest);
  }
  if (!document.querySelector('link[data-jarvis-remote-style]')) {
    const remoteStyle = document.createElement('link');
    remoteStyle.rel = 'stylesheet';
    remoteStyle.href = '/remote-companion.css';
    remoteStyle.dataset.jarvisRemoteStyle = 'v1';
    document.head.appendChild(remoteStyle);
  }
  if (!document.querySelector('script[data-jarvis-remote]')) {
    const remoteScript = document.createElement('script');
    remoteScript.src = '/remote-companion.js';
    remoteScript.dataset.jarvisRemote = 'v1';
    remoteScript.async = false;
    document.head.appendChild(remoteScript);
  }
}
