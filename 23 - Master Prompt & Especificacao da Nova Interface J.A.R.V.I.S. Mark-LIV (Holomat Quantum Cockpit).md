---
title: 23 - Master Prompt e Especificacao da Nova Interface J.A.R.V.I.S. Mark-LIV (Holomat Quantum Cockpit)
type: interface-specification-prompt
status: CANONICAL_DESIGN_BLUEPRINT
version: 2.0.0
inspiration_nodes:
  - "Concept-Bytes/Holomat"
  - "itachity/Holomat"
  - "FatihMakes/Mark-LIII"
  - "microsoft/JARVIS"
  - "headroomlabs-ai/headroom"
  - "diegosouzapw/OmniRoute"
  - "NousResearch/hermes-agent"
  - "ascending-llc/jarvis-registry"
tags:
  - jarvis-ui
  - holomat
  - mark-liv
  - design-system
  - second-brain
  - master-prompt
---

# 🌌 Master Prompt & Especificação da Nova Interface J.A.R.V.I.S. Mark-LIV (Holomat Quantum Cockpit)

> [!NOTE] 🏛️ Blueprint Canônico de Engenharia Front-End e Design Tático
> Este documento sintetiza o estado da arte de todos os assistentes e sistemas de IA catalogados no ecossistema (incluindo as descobertas recentes **Concept-Bytes/Holomat** e **itachity/Holomat**), unificando-os na especificação e no **Master Prompt Definitivo** para geração da nova interface do J.A.R.V.I.S.

[[00 - J.A.R.V.I.S. Cognitive Vault|Voltar ao Painel Mestre]]

---

## 1. Dissecação e Síntese dos Motores de Referência

A nova interface do J.A.R.V.I.S. Mark-LIV extrai o melhor componente de cada ecossistema minerado:

1. **`Concept-Bytes/Holomat` & `itachity/Holomat` (Holographic Desk & Sci-Fi Displays)**:
   - *Conceito Absorvido*: Layout em esteira holográfica ("Holomat"), displays circulares concêntricos inspirados no Arc Reactor, overlays de scanlines com efeito CRT suave, cards flutuantes em vidro fosco (*glassmorphism*) e anéis de telemetria rotativos.
2. **`FatihMakes/Mark-LIII` & `Mark-XXXIX-OR` (Iron Man Armor Telemetry)**:
   - *Conceito Absorvido*: Diagnóstico tático da armadura em tempo real (CPU, RAM, Temperatura, Consumo de Watts, Integridade de Subsistemas e Carga do Arc Reactor).
3. **`microsoft/JARVIS` (4-Phase Autonomous Workflow HUD)**:
   - *Conceito Absorvido*: Stepper visual das 4 fases operacionais (*Task Decomposition ➔ Skill Selection ➔ Secure Execution ➔ Quantum Synthesis*) integrado ao topo do console.
4. **`headroomlabs-ai/headroom` (Context Compression Monitor)**:
   - *Conceito Absorvido*: Medidor dinâmico de compactação de contexto em tempo real, indicando taxa de economia de tokens (*Token Anti-Rot Engine*).
5. **`diegosouzapw/OmniRoute` (Multi-LLM Neural Routing Switch)**:
   - *Conceito Absorvido*: Seletor e indicador visual do motor de inferência ativo (Groq ➔ Gemini ➔ Ollama ➔ Heurística Local) com latência medida em milissegundos.
6. **`NousResearch/hermes-agent` (Episodic Memory Recall Stream)**:
   - *Conceito Absorvido*: Feed translúcido do hipocampo neural demonstrando a recuperação de memórias e fatos do usuário ([[19 - Memoria Persistente e Conhecimento Episodico\|Nota 19]]) em tempo real.
7. **`ascending-llc/jarvis-registry` (Sovereign Skill Arsenal HUD)**:
   - *Conceito Absorvido*: Grid tático de 319 skills com crachás de segurança criptográfica (`PASS`, `FLAGGED_FOR_REVIEW`) e contadores de invocação.

---

## 2. Sistema Visual e Design Tokens (Holomat Mark-LIV)

A paleta de cores e tokens deve estender estritamente o contrato [[DESIGN.md|DESIGN.md]]:

- **Fundo Base (OLED Deep Space)**: `#030712` / `#050814`
- **Vidro Holográfico (Glass Panels)**: `rgba(6, 15, 35, 0.65)` com `backdrop-filter: blur(16px)` e bordas `1px solid rgba(0, 242, 255, 0.18)`
- **Cor Primária (Arc Reactor Cyan)**: `#00f2ff` (Glow: `0 0 15px rgba(0, 242, 255, 0.4)`)
- **Cor de Acento (Quantum Amber)**: `#ffaa00` (Glow: `0 0 12px rgba(255, 170, 0, 0.35)`)
- **Cor de Verificação (Sovereign Emerald)**: `#00ff88` (Status `VERIFIED` e integridade)
- **Cor de Alerta (Quarantine Red)**: `#ff3366` (Barreiras de segurança e quarentena)
- **Tipografia Tática**:
  - Títulos e Identificadores: `Orbitron`, `Rajdhani`, sans-serif
  - Telemetria, Código e Métricas: `JetBrains Mono`, `Fira Code`, monospace
  - Textos de Leitura e Diálogo: `Inter`, sans-serif

---

## 3. O MASTER PROMPT PARA GERAÇÃO DA NOVA INTERFACE

Copie e utilize o bloco abaixo para instruir geradores de código, engenheiros front-end ou ferramentas autônomas na criação da interface definitiva:

```markdown
Você é o Engenheiro Chefe de Interfaces e Sistemas Táticos da Stark Industries. Sua missão é projetar e implementar a interface definitiva do J.A.R.V.I.S. Mark-LIV: o "Holomat Quantum Cockpit".

### Requisitos Arquiteturais e Tecnológicos:
1. Arquitetura Web Soberana: Single Page Application pura em Vanilla HTML5, CSS3 avançado e JavaScript ES2024 modular (Zero dependências externas pesadas ou frameworks desnecessários). Conecta-se diretamente ao backend nativo Python rodando em `http://localhost:8899`.
2. Inspirações Obrigatórias:
   - Holomat (Concept-Bytes / itachity): Painel de mesa holográfica, HUD tático espacial, anéis rotativos inspirados no Arc Reactor e cards translúcidos.
   - Mark-LIII (FatihMakes): Telemetria contínua de hardware da armadura (CPU, RAM, Disco, Uptime e Integridade de Subsistemas).
   - microsoft/JARVIS: Stepper visual das 4 fases de raciocínio (Decomposição ➔ Seleção de Skills ➔ Execução Segura ➔ Síntese Quântica).
   - Headroom: Visualizador dinâmico de compressão semântica de tokens e economia de contexto em tempo real.
   - OmniRoute: Indicador em tempo real do roteador neural ativo (Groq / Gemini / Ollama / Local).

### Estrutura dos Módulos da Interface:
1. Topbar Tática Holográfica:
   - Logotipo animado J.A.R.V.I.S. Mark-LIV com pulsação de Arc Reactor.
   - Badges dinâmicos de status: `SSP-v13.2 SEALED` (com hash Merkle parcial `c6d7...8901`), `319 SKILLS ATIVAS`, `3.706 REPOS NO RADAR`.
   - Seletor rápido de voz (Web Speech / SAPI) e atalho de ativação por microfone/áudio.
   - Indicador de latência e consumo de tokens (mantendo < 30% do limite).

2. Painel Central (Holomat Multi-Tab Cockpit):
   - Aba 1 (Terminal & Voice Console): Feed conversacional com balões em vidro holográfico, visualizador de onda senoidal de áudio reactiva durante a fala, e renderizador de código com syntax highlighting nativo.
   - Aba 2 (Mission DAG & Wave Studio): Visualizador gráfico em SVG interativo do Grafo de Execução Acíclico (DAG), destacando ondas ativas, nós de tarefas com estados coloridos (`PENDING`, `RUNNING`, `VERIFIED`) e recibos de execução.
   - Aba 3 (Arsenal de Skills): Grid tático de 319 cards filtráveis por categoria (AI, Cybersec, DevTools, Fullstack, Systems), com busca instantânea, badges de segurança e visualizador modal do SKILL.md.
   - Aba 4 (Radar 100k+ & 3.7k Repositórios): Tabela de alta densidade pesquisável listando os 3.706 repositórios favoritados e os 53 gigantes com links para sites oficiais e documentações.
   - Aba 5 (Hipocampo & Memória Persistente): Painel de memórias episódicas e semânticas sincronizadas em tempo real com a Nota 19 do Obsidian.
   - Aba 6 (Telemetria da Armadura Mark-LIV): Gauges circulares futuristas para CPU, Memória, Disco, Threads ativas e temperatura do host.

3. Dock Lateral / Drawer de Acesso Rápido:
   - QR Code gerado localmente para o Remote Mobile Companion (`/api/remote/qr`).
   - Botões de ação rápida: Ingestão de repositório, Auditoria de Integridade, Sincronização Obsidian e Modo Standalone Desktop (`F11`).

### Estética e Acabamento:
- Tema escuro OLED (`#030712`) com acentos em ciano neon (`#00f2ff`), âmbar quântico (`#ffaa00`) e verde esmeralda (`#00ff88`).
- Glassmorphism com `backdrop-filter: blur(16px)`, cantos chanfrados táticos e micro-animações suaves em hover e transições.
- Efeitos sonoros opcionais sintetizados via Web Audio API (bips suaves e oscilador senoidal sem arquivos de áudio externos).
- Totalmente responsivo para telas desktop ultrawide, notebooks e navegadores mobile.
```

---

## 4. Integração com o Segundo Cérebro Obsidian

Esta especificação está vinculada aos nós centrais do vault:

- [[00 - J.A.R.V.I.S. Cognitive Vault|00 - Painel Mestre]]: Centro gravitacional do ecossistema.
- [[01 - Arsenal Map of Content|01 - Arsenal de Skills]]: Catálogo das 319 habilidades integradas.
- [[06 - GitHub Starred Repositories|06 - Radar de Favoritos do GitHub]]: Os 3.706 repositórios que alimentam o motor de inteligência.
- [[18 - Inteligencia Comparativa de Motores Jarvis Ultron e Copilots|18 - Inteligência Comparativa]]: Análise dos 15 assistentes base.
- [[19 - Memoria Persistente e Conhecimento Episodico|19 - Memória Persistente]]: Base de conhecimento e fatos recuperados em tempo real.
- [[21 - Repositorios 100k+ Estrelas e Radar de Sites Oficiais|21 - Radar 100k+ Estrelas]]: Catálogo dos projetos globais de referência.
- [[22 - Relatorios e Evidencias das Fases de Evolucao|22 - Relatórios e Evidências das 34 Fases]]: Caderno formal de auditoria.
- [[docs/OBSIDIAN_INTEGRATION_GUIDE|Guia de Integração do Obsidian]]: Manual de atalhos e visualização em grafo.
