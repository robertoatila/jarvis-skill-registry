/* Separate, read-only workspace view. All remote text uses textContent. */
(() => {
  const panel = document.getElementById('workspaceHub');
  const status = document.getElementById('workspaceStatus');
  const list = document.getElementById('workspaceConnections');
  const refresh = document.getElementById('workspaceRefresh');
  const form = document.getElementById('workspaceGoalForm');
  const output = document.getElementById('workspaceHandoff');
  const copy = document.getElementById('workspaceCopy');
  const result = document.getElementById('workspaceResult');
  const prepare = form.querySelector('button');
  async function request(url) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch(url, {signal: controller.signal, cache: 'no-store'});
      if (!response.ok) throw new Error('Não foi possível consultar o serviço local.');
      return await response.json();
    } finally { clearTimeout(timer); }
  }
  async function load() {
    refresh.disabled = true;
    panel.setAttribute('aria-busy', 'true');
    status.textContent = 'Consultando o workspace…';
    list.replaceChildren();
    try {
      const data = await request('/api/workspace');
      status.textContent = `${data.eligible_skills} skills elegíveis no índice. ${data.catalog_error || data.autonomy.mode + '.'}`;
      for (const connection of data.connections) {
        const item = document.createElement('li');
        const name = document.createElement('h3');
        name.textContent = connection.name;
        const state = document.createElement('p');
        state.textContent = connection.status;
        const detail = document.createElement('small');
        detail.textContent = connection.detail;
        item.append(name, state, detail);
        list.append(item);
      }
      const link = document.getElementById('workspaceObsidian');
      if (typeof data.obsidian_url === 'string' && data.obsidian_url.startsWith('obsidian://open?')) {
        link.href = data.obsidian_url;
        link.hidden = false;
      }
    } catch (error) {
      document.getElementById('workspaceObsidian').hidden = true;
      status.textContent = 'Serviço local indisponível. Inicie o Jarvis e use Atualizar conexões.';
    } finally {
      refresh.disabled = false;
      panel.setAttribute('aria-busy', 'false');
    }
  }
  refresh.addEventListener('click', load);
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    prepare.disabled = true;
    copy.disabled = true;
    output.value = '';
    result.textContent = 'Selecionando skills por metadados…';
    try {
      const data = await request('/api/workspace/prepare?goal=' + encodeURIComponent(document.getElementById('workspaceGoal').value));
      output.value = data.handoff;
      copy.disabled = false;
      result.textContent = `${data.skills.length} candidatas; cerca de ${data.estimated_metadata_tokens} tokens de metadados. ${data.catalog_error || 'Contexto pronto. Nenhuma execução iniciada.'}`;
    } catch (error) { result.textContent = 'Não foi possível preparar o contexto. Verifique o serviço e tente novamente.'; }
    finally { prepare.disabled = false; }
  });
  copy.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(output.value);
      result.textContent = 'Contexto copiado. Cole na tarefa do Codex, Antigravity ou ChatGPT para continuar.';
    } catch (error) {
      output.focus(); output.select();
      result.textContent = 'Texto selecionado. Use Ctrl+C para copiar.';
    }
  });
  load();
})();
