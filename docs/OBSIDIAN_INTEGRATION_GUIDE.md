# Guia de Integração e Operação do Obsidian no J.A.R.V.I.S.

O repositório `.skill-registry` foi concebido nativamente como um **Segundo Cérebro Criptográfico** e visual para o ecossistema J.A.R.V.I.S. Este guia resume a arquitetura de navegação, visualização em grafo, consultas dinâmicas e integração com o runtime autônomo.

---

## 1. Arquitetura de Mapas de Conteúdo (MOCs)

O vault utiliza uma hierarquia estrita de notas numeradas que funcionam como estações centrais de navegação:

- **[[00 - J.A.R.V.I.S. Cognitive Vault|00 - Painel Mestre]]**: Ponto de entrada unificado para todos os centros de comando, status forense e governança.
- **[[01 - Arsenal Map of Content|01 - Arsenal de Skills]]**: Catálogo de habilidades canônicas divididas por domínios (AI, Segurança, DevTools, etc.).
- **[[06 - GitHub Starred Repositories|06 - Radar de Favoritos do GitHub]]**: Repositórios favoritados pelo operador, minerados e classificados em 5 clusters.
- **[[19 - Memoria Persistente e Conhecimento Episodico|19 - Memória Persistente]]**: Hipocampo neural com memórias episódicas, fatos confirmados e sincronização bidirecional.
- **[[21 - Repositorios 100k+ Estrelas e Radar de Sites Oficiais|21 - Radar 100k+ Estrelas]]**: Catálogo dos 53 maiores projetos open-source globais com documentações oficiais.
- **[[22 - Relatorios e Evidencias das Fases de Evolucao|22 - Relatórios e Evidências]]**: MOC estelar conectando todas as 34 fases de evolução e os 7 marcos estáveis.

---

## 2. Visualização em Grafo (Graph View & Constelação Cósmica)

Ao abrir a visualização em grafo (`Ctrl + G`), a configuração em `.obsidian/graph.json` aplica as seguintes regras de cores e forças:

- 🟢 **Verde Esmeralda (`path:skills`)**: O Arsenal de Habilidades homologadas.
- 🟡 **Âmbar / Laranja (`path:reports`)**: Laudos de auditoria e cadernos de evidências das 34 fases.
- 🟣 **Roxo / Índigo (`path:docs`)**: Especificações arquiteturais e manuais de governança.
- 🔵 **Ciano / Neon (`file:"00 - J.A.R.V.I.S. Cognitive Vault"`)**: O centro gravitacional do Segundo Cérebro.
- 🟠 **Ouro (`tag:#github-starred`)**: O catálogo de favoritos do GitHub.

> [!TIP] Dica de Navegação no Grafo
> Ative o filtro **Setas** para visualizar o fluxo direcional das dependências e navegue com zoom dinâmico para inspecionar os clusters temáticos de IA e Cibersegurança.

---

## 3. Diagrama Visual Interativo (Obsidian Canvas)

O arquivo **[[JARVIS-Brain-Map.canvas]]** oferece uma visão espacial da armadura e dos agentes:

- Blocos interativos conectando os 4 Agentes Quânticos (`Quantum-ReconAgent`, `Quantum-SynthesisAgent`, `Quantum-VisualizerAgent`, `Quantum-AuditAgent`).
- Linhas de fluxo demonstrando o ciclo de 4 fases (Planejamento ➔ Seleção de Skills ➔ Execução Segura ➔ Síntese).

---

## 4. Consultas Dinâmicas via Plugin Dataview

Caso o plugin de comunidade **Dataview** esteja instalado no Obsidian, você pode executar consultas SQL-like diretamente nas notas:

```dataview
TABLE description, version, tier
FROM "skills"
WHERE contains(tags, "security")
SORT file.name ASC
```

---

## 5. Sincronização Automática com o Runtime

O servidor soberano `tooling/jarvis_server.py` sincroniza eventos de memória e novas descobertas em tempo real:

- Novos fatos identificados pelo agente durante conversas são persistidos na nota `19`.
- A mineração de repositórios atualiza o catálogo `06`.
- A integridade do vault pode ser verificada a qualquer momento com:

```bash
python jarvis.py --doctor
```
