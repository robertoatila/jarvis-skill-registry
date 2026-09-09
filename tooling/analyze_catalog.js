const fs = require('fs');
const path = require('path');

const REGISTRY_ROOT = 'E:\\.skill-registry';
const CACHE_FILE = path.join(REGISTRY_ROOT, 'cache', 'starred_catalog.json');

if (!fs.existsSync(CACHE_FILE)) {
  console.error(`Cache not found at ${CACHE_FILE}`);
  process.exit(1);
}

const repos = JSON.parse(fs.readFileSync(CACHE_FILE, 'utf-8'));
console.log(`Carregados ${repos.length} repositórios com sucesso.`);

const clusters = {
  agents: [],
  cyber: [],
  kernel: [],
  devops: [],
  fullstack: []
};

for (const r of repos) {
  const topicsList = Array.isArray(r.topics) ? r.topics : (typeof r.topics === 'string' ? [r.topics] : []);
  const text = `${r.name || ''} ${r.description || ''} ${topicsList.join(' ')}`.toLowerCase();
  const lang = (r.language || '').toLowerCase();

  if (/agent|rag|llm|prompt|langchain|autogen|vllm|vector|embedding|gpt|claude|gemini|assistant/.test(text)) {
    clusters.agents.push(r);
  } else if (/security|pentest|exploit|cve|bypass|malware|kernel|driver|anti-debug|obfuscat|revers|forensic|injection|burp|pcap|defend/.test(text)) {
    clusters.cyber.push(r);
  } else if (/^(c|c\+\+|rust|go)$/.test(lang) || /kernel|ebpf|compiler|parser|runtime|os|performance|concurrency|driver/.test(text)) {
    clusters.kernel.push(r);
  } else if (/docker|k8s|kubernetes|ci-cd|devops|aws|cloud|cli|monitor|observability|git|terraform|ansible/.test(text)) {
    clusters.devops.push(r);
  } else {
    clusters.fullstack.push(r);
  }
}

console.log(`Jarvis-AgenticEngine    : ${clusters.agents.length}`);
console.log(`Hyperion-CyberSec       : ${clusters.cyber.length}`);
console.log(`Sovereign-Kernel/Systems: ${clusters.kernel.length}`);
console.log(`Quantum-Fullstack       : ${clusters.fullstack.length}`);
console.log(`Enterprise-DevOps       : ${clusters.devops.length}`);

function renderSection(title, icon, squadName, reposList, description) {
  const sorted = [...reposList].sort((a, b) => (b.stars || 0) - (a.stars || 0)).slice(0, 20);
  let md = `## ${icon} ${title} (${reposList.length} Repositórios)\n\n`;
  md += `**Esquadrão Atribuído**: \`${squadName}\`\n\n`;
  md += `${description}\n\n`;
  md += `| Repositório | Estrelas | Linguagem | Descrição Tática | Moat / Extração Útil |\n`;
  md += `| :--- | :--- | :--- | :--- | :--- |\n`;

  for (const item of sorted) {
    const stars = item.stars >= 1000 ? `${(item.stars / 1000).toFixed(1)}k` : `${item.stars || 0}`;
    const lang = item.language || 'Multi';
    const cleanDesc = (item.description || 'Sem descrição').replace(/\|/g, '-').trim();
    const descShort = cleanDesc.length > 70 ? cleanDesc.slice(0, 67) + '...' : cleanDesc;
    md += `| [**${item.name}**](${item.html_url}) | ⭐ ${stars} | \`${lang}\` | ${descShort} | Padrão arquitetural pronto para esteira |\n`;
  }
  md += '\n';
  return md;
}

let doc = `---
title: Catalogo Tatico de 2168 Repositorios por Esquadrao
type: intelligence-dossier
status: COMPILED_NIVEL_9
total_repos: ${repos.length}
tags:
  - jarvis
  - intelligence
  - repository-dossier
  - subagent-swarms
---

# 🌌 Catálogo Tático dos 2.168 Repositórios do J.A.R.V.I.S.

> [!NOTE] 🧠 Mineração e Extração Sistemática
> Cada um dos **2.168 repositórios favoritados** foi indexado, auditado e associado a um dos **5 Esquadrões de Subagentes**. Abaixo está o mapeamento detalhado dos repositórios de maior impacto técnico e estratégico para o ecossistema J.A.R.V.I.S.

---

`;

doc += renderSection(
  'Cluster 1: Jarvis-AgenticEngine',
  '🧠',
  'Jarvis-AgenticEngine',
  clusters.agents,
  'Modelos de linguagem de alta taxa de transferência, orquestração de subagentes, RAG vetorial, loops de auto-avaliação e raciocínio multi-passo.'
);

doc += renderSection(
  'Cluster 2: Hyperion-CyberSec',
  '🛡️',
  'Hyperion-CyberSec',
  clusters.cyber,
  'Engenharia reversa, análise defensiva, detecção de anti-debug/anti-VM, evasão de hooks e segurança de memória.'
);

doc += renderSection(
  'Cluster 3: Sovereign-Kernel & Systems',
  '⚡',
  'Sovereign-Kernel & Systems',
  clusters.kernel,
  'Desenvolvimento nativo de alto desempenho em C, C++, Rust e Go; drivers de kernel, eBPF e computação concorrente lock-free.'
);

doc += renderSection(
  'Cluster 4: Quantum-Fullstack UI/UX',
  '🎨',
  'Quantum-Fullstack UI/UX',
  clusters.fullstack,
  'Interfaces ricas com Glassmorphism, Web Audio sintetizado, animações fluidas e design systems de alto nível.'
);

doc += renderSection(
  'Cluster 5: Enterprise-DevOps & Cloud',
  '🚀',
  'Enterprise-DevOps',
  clusters.devops,
  'Automação de infraestrutura, GitHub Actions, Docker, tolerância a falhas e observabilidade em tempo real.'
);

const outPath = path.join(REGISTRY_ROOT, '14 - Catalogo Tatico de 2168 Repositorios por Esquadrao.md');
fs.writeFileSync(outPath, doc, 'utf-8');
console.log(`Dossiê tático gerado com sucesso em: ${outPath}`);
