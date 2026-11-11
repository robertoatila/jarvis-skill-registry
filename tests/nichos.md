A busca de developer já atingiu o corte: na página 77, o primeiro resultado está com 1000 estrelas e estrelado; o seguinte está com 997. Não avancei abaixo desse ponto.
Levantei temas amplos de tecnologia para pesquisar no GitHub. Os volumes abaixo são contagens aproximadas de repositórios associados a tópicos do GitHub, consultadas em páginas do próprio site; não são contagens da busca por palavra e podem variar:

1. Python — 911.784 repositórios no tópico; a busca geral mostra 7,2 milhões de resultados.
2. Machine learning — cerca de 249 mil.
3. IA — cerca de 180 mil.
4. Android — cerca de 160 mil.
5. Análise de dados — cerca de 62 mil.
6. Web — cerca de 47,5 mil.
7. DevOps — cerca de 46,4 mil.
8. Cibersegurança — cerca de 40,6 mil.
9. Programação — cerca de 17,9 mil.
10. Aplicações web — cerca de 13,9 mil.
Fontes: tópico Python no GitHub, Machine Learning, IA, Android, Análise de dados, Web, DevOps, Cibersegurança, Programação, Aplicações web.

- **Todos os 10 Nichos Oficiais Concluídos com Sucesso** (Python, Machine Learning, IA, Android, Análise de Dados, Web, DevOps, Cibersegurança, Programação e Aplicações Web): Colheita, etiquetagem e estrelamento finalizados até o piso estrito de $\ge 999$ estrelas.
- **Arsenal SQLite Soberano**: **22.295 ferramentas ativas indexadas** em `state/arsenal_library.sqlite` com FTS5 e busca textual completa.
- **Ledger Global & HUD**: **18.410 repositórios estrelados** sincronizados no HUD e integrados às ferramentas MCP do `jarvis-sovereign-gateway`.

### Onda 2 — Nichos Técnicos Especializados (100% Concluída — Piso $\ge 999$ ⭐)

11. `reverse-engineering` (Engenharia reversa, análise de binários e descompilação) — **Concluído** (169 novos repositórios catalogados até 999 ⭐).
12. `cryptography` (Criptografia, cifras, pós-quântica e segurança matemática) — **Concluído** (107 novos repositórios catalogados até 999 ⭐).
13. `llm-agents` & `autonomous-agents` (Arquiteturas de agentes e orquestração de IA) — **Concluído** (11 novos repositórios catalogados até 999 ⭐).
14. `embedded-systems` (Firmware, RTOS e IoT) — **Concluído** (508 novos repositórios catalogados até 999 ⭐).
15. `distributed-systems` (Sistemas distribuídos, bancos descentralizados e consenso) — **Concluído** (245 novos repositórios catalogados até 999 ⭐).

### Onda 3 — Nicho WhatsApp (Gateways, bots e dashboards multi-sessão — Concluída, piso $\ge 999$ ⭐)

Tópicos de origem: `automation`, `baileys`, `chatbot`, `dashboard`, `gateway`, `multi-client`, `multi-connection`, `multi-session`, `next-auth`, `nextjs`, `prisma`, `rest-api`, `self-hosted`, `webhook`, `whatsapp`, `whatsapp-api`, `whatsapp-bot`, `whatsapp-web`.

- Tópicos específicos do WhatsApp são colhidos diretamente (`topic:whatsapp-api`, `topic:baileys` etc.); os genéricos são sempre interseccionados com `topic:whatsapp` para não varrer o GitHub inteiro.
- Fila de colheita: `config/niche_wave3_whatsapp.txt` (18 consultas), executada por `tooling/harvest_starred_by_keyword.py`.
- **Resultado medido:** 42 novos repositórios favoritados (`topic:whatsapp-api` 9, `topic:whatsapp-bot` 8, `topic:whatsapp-web` 4, `topic:whatsapp` 21). Catálogo HUD: 22.296 → 22.336 ferramentas; ledger de progresso: 18.452 repositórios.
- Já cobertos por ondas anteriores (0 novos): `baileys`, `whatsapp+chatbot`, `whatsapp+dashboard`, `whatsapp+gateway`, `whatsapp+rest-api`, `whatsapp+self-hosted`, `whatsapp+nextjs`.
- Sem nenhum repositório ≥ 999 ⭐ com o tópico: `multi-session`, `multi-connection`, `multi-client`, `whatsapp+automation`, `whatsapp+webhook`, `whatsapp+next-auth`, `whatsapp+prisma`. Esses tópicos existem só em repositórios menores, como `WA-AKG` e `w-azap`, abaixo do piso; não houve relaxamento do piso.

### Onda 4 — Ecossistema LLM & Agentes Autônomos (Runtimes, Frameworks, RAG e Serving — Concluída, piso $\ge 999$ ⭐)

Tópicos de origem:

- **Runtimes & Local Serving**: `topic:vllm`, `topic:ollama`, `topic:llama-cpp`, `topic:local-llm`, `topic:llm-serving`, `topic:unsloth`, `topic:axolotl`.
- **Frameworks, Agentes & RAG**: `topic:langchain`, `topic:langgraph`, `topic:llamaindex`, `topic:crewai`, `topic:autogen`, `topic:dify`.
- **Gateways & UI**: `topic:litellm`, `topic:open-webui`.
- **Interseções Estratégicas**: `topic:llm`, `topic:rag+topic:llm`, `topic:fine-tuning+topic:llm`, `topic:guardrails+topic:llm`.
- Fila de colheita estruturada em: `config/niche_wave4_llm.txt` (19 consultas), executada por `tooling/harvest_starred_by_keyword.py`.
- **Resultado medido:** **628 novos repositórios favoritados** (`topic:llm` 458, `topic:ollama` 47, `topic:langchain` 45, `topic:vllm` 23, `topic:llama-cpp` 18, `topic:local-llm` 9, `topic:llm-serving` 9, `topic:open-webui` 6, `topic:dify` 5, `topic:langgraph` 3, `topic:unsloth` 2, `topic:llamaindex` 1, `topic:crewai` 1, `topic:litellm` 1).
- **Catálogo HUD / Arsenal SQLite**: expandido de 22.336 para **22.623 ferramentas ativas** indexadas com FTS5.
- **Ledger Global de Progresso**: expandido de 18.452 para **19.080 repositórios estrelados**.
- **Casos de borda:** `topic:axolotl` não retornou itens com esse tópico direto, mas o repositório oficial (`axolotl-ai-cloud/axolotl` com 12.573 ⭐) foi capturado e indexado com sucesso na varredura de `topic:llm`. Consultas interseccionadas (`topic:rag+topic:llm`, `topic:fine-tuning+topic:llm`, `topic:guardrails+topic:llm` e `topic:autogen`) tiveram 100% dos seus repositórios já cobertos e catalogados pelas etapas precedentes.

### Nicho Registrado via Captura Visual (`image-nicho3.png`) — Downloaders & Bandwidth Aggregation

Tópicos capturados na imagem (`image-nicho3.png`):
- `bandwidth-aggregation` (Agregação de banda e canais de rede paralelos)
- `cross-platform` (Suporte multiplataforma)
- `desktop-app` (Aplicações desktop nativas / GUI)
- `downloader` (Motores de download acelerado)
- `downloadmanager` (Gerenciadores de download multi-conexão)
- `linux` (Compatibilidade com Linux)
- `macos` (Compatibilidade com macOS)
- `multiconnection` (Múltiplas conexões HTTP/TCP concorrentes)
- `parallel-downloads` (Download paralelo em blocos/chunks)
- `windows` (Compatibilidade com Windows)

> [!NOTE]
> A imagem original do grafo do Obsidian (`image.png`, 1013x1030 px) foi restaurada em sua resolução nativa. A imagem de tags do nicho de downloaders foi preservada separadamente como [`image-nicho3.png`](image-nicho3.png).




### Onda 11 — Alta Performance, Otimização, Sistemas Operacionais & Games (Concluída, piso $\ge 999$ ⭐)

Tópicos de origem: `performance`, `optimize`, `fps`, `fast`, `operating system`, `game`, `evolution`.

- Fila executada por `tooling/harvest_starred_by_keyword.py` (7 consultas paginadas).
- **Resultado medido:** **2.194 novos repositórios favoritados** (piso rigoroso $\ge 999$ ⭐). Destaques indexados: `affaan-m/ECC` (293.396 ⭐), `zed-industries/zed` (92.436 ⭐), `minio/minio` (61.294 ⭐), `rustfs/rustfs` (35.573 ⭐), `envoyproxy/envoy` (29.158 ⭐), `locustio/locust` (28.254 ⭐), `fmtlib/fmt` (25.897 ⭐), `deepseek-ai/DeepInfer` (24.494 ⭐), `microsoft/mimalloc` (13.520 ⭐), `brendangregg/perf-tools` (10.481 ⭐), `scylladb/seastar` (9.406 ⭐), `swiftlang/swift-evolution` (15.879 ⭐).
- **Catálogo HUD / Arsenal SQLite**: expandido para **35.638 ferramentas ativas** indexadas com FTS5.
- **Ledger Global de Progresso**: expandido para **32.876 repositórios estrelados**.


### Onda 12 — Nicho Dados Abertos Brasil, Documentos, ETL & Identidade (Concluída, piso $\ge 300$ ⭐)

Tópicos de origem: `brazil`, `brasil`, `cnpj`, `etl`, `open-data`, `pipeline`, `receita-federal`, `cpf`, `rg`, `document`, `identidade`, `identity`, `id`.

- Fila executada por `tooling/harvest_starred_by_keyword.py` com **corte estrito de 300 estrelas** (13 consultas paginadas).
- **Resultado medido:** **2.939 novos repositórios favoritados** (piso rigoroso $\ge 300$ ⭐). Destaques indexados: `Universidade-Livre/ciencia-da-computacao` (21.021 ⭐), `BrasilAPI/BrasilAPI` (11.524 ⭐), `backend-br/vagas` (8.058 ⭐), `lerrua/remote-jobs-brazil` (5.196 ⭐), `bacen/pix-api` (3.001 ⭐), `osintbrazuca/osint-brazuca` (2.845 ⭐), `ctresb/leis` (2.690 ⭐), `arthurspk/guiadobackend` (2.452 ⭐), `brazilian-utils/javascript` (1.686 ⭐), `osintbrazuca/osint-brazuca-regex` (1.014 ⭐), `ipea/geobr` (970 ⭐), `tbrugz/geodata-br` (915 ⭐), `turicas/socios-brasil` (612 ⭐), `guibranco/BancosBrasileiros` (554 ⭐), `brazilian-utils/python` (535 ⭐), `BoletoNet/boletonet` (505 ⭐), `DeHor-Labs/mcp-fiscal-brasil` (422 ⭐), `tiagoporto/gerador-validador-cpf` (406 ⭐), `caiopizzol/cnpj-data-pipeline` (341 ⭐).
- **Catálogo HUD / Arsenal SQLite**: expandido para **38.514 ferramentas ativas** indexadas com FTS5.
- **Ledger Global de Progresso**: expandido para **35.815 repositórios estrelados**.


### Onda 13 — Perfis Oficiais de IA de Fronteira: DeepSeek & Qwen (Concluída, piso $\ge 300$ ⭐)

Perfis e Organizações Oficiais: `deepseek-ai` e `QwenLM`.

- Executado via `tooling/star_org_profiles.py` varrendo 100% dos repositórios oficiais com piso $\ge 300$ estrelas.
- **DeepSeek (`deepseek-ai`)**: 42 repositórios elegíveis (destaques: `deepseek-harness` 277k ⭐, `DeepSeek-V3` 104k ⭐, `DeepSeek-R1` 92k ⭐, `DeepSeek-Coder` 24k ⭐, `DeepSeek-OCR` 24k ⭐, `Janus` 17k ⭐, `FlashMLA` 13k ⭐, `3FS` 10k ⭐, `DeepEP` 10k ⭐, `DeepGEMM` 9k ⭐).
- **Qwen (`QwenLM`)**: 34 repositórios elegíveis (destaques: `qwen-code` 29k ⭐, `Qwen3` 27k ⭐, `Qwen` 22k ⭐, `Qwen3-VL` 20k ⭐, `Qwen-Agent` 17k ⭐, `Qwen3-Coder` 16k ⭐, `Qwen3-TTS` 14k ⭐, `Qwen-Image` 8.4k ⭐, `Qwen-VL` 6.7k ⭐, `Qwen3.8` 4.4k ⭐, `open-computer-use` 308 ⭐).
- **Resultado medido:** **56 novos repositórios favoritados**.
- **Catálogo HUD / Arsenal SQLite**: expandido para **38.560 ferramentas ativas** indexadas com FTS5.
- **Ledger Global de Progresso**: expandido para **35.871 repositórios estrelados**.


### Onda 14 — Utilitários, Validação, Documentos e Telecom / Formatos (Concluída, piso $\ge 300$ ⭐)

Tópicos de origem (Tags da Imagem): `barcode`, `qrcode`, `geoip`, `currency`, `faker`, `validator`, `holidays`, `cep`, `cnpj`, `fipe`, `number-to-words`, `email-validator`.

- Fila executada por `tooling/harvest_starred_by_keyword.py` com **corte estrito de 300 estrelas** (12 consultas paginadas).
- **Resultado medido:** **1.118 novos repositórios favoritados** (piso rigoroso $\ge 300$ ⭐). Destaques indexados:
  - **Faker & Mocking:** `typicode/json-server` (75.734 ⭐), `fzaninotto/Faker` (26.613 ⭐), `joke2k/faker` (19.487 ⭐), `faker-js/faker` (15.546 ⭐), `SWivid/F5-TTS` (15.546 ⭐).
  - **Validação de Esquemas & Tipos:** `K-Dense-AI/scientific-agent-skills` (56.602 ⭐), `moment/moment` (47.871 ⭐), `react-hook-form/react-hook-form` (44.912 ⭐), `colinhacks/zod` (44.301 ⭐), `wshobson/agents` (42.364 ⭐), `pydantic/pydantic` (29.404 ⭐), `validatorjs/validator.js` (23.741 ⭐), `jquense/yup` (23.650 ⭐), `hapijs/joi` (21.165 ⭐), `go-playground/validator` (20.223 ⭐), `google/libphonenumber` (18.347 ⭐), `ajv-validator/ajv` (14.873 ⭐).
  - **Códigos de Barra, QR & Rede/GeoIP:** `zxing/zxing` (34.186 ⭐), `Loyalsoldier/v2ray-rules-dat` (21.016 ⭐).
  - **Moedas & Financeiro:** `kdeldycke/awesome-falsehood` (27.842 ⭐), `akfamily/akshare` (23.271 ⭐), `dogecoin/dogecoin` (15.204 ⭐).
  - **Validação de Email:** `egulias/EmailValidator` (11.641 ⭐), `JoshData/python-email-validator` (1.458 ⭐), `truemail-rb/truemail` (1.291 ⭐), `mfbx9da4/deep-email-validator` (933 ⭐).
  - **Feriados Mundiais:** `vacanza/holidays` (1.975 ⭐), `nager/Nager.Date` (1.442 ⭐), `commenthol/date-holidays` (1.119 ⭐), `azuyalabs/yasumi` (1.105 ⭐), `workalendar/workalendar` (946 ⭐), `spatie/holidays` (411 ⭐).
  - **Brasil, CEP, CNPJ, FIPE e Utilidades:** `ceph/ceph` (17.211 ⭐), `BrasilAPI/cep-promise` (2.979 ⭐), `brazilian-utils/javascript` (1.686 ⭐), `cuducos/minha-receita` (1.610 ⭐), `LaravelLegends/pt-br-validator` (649 ⭐), `geekcom/validator-docs` (585 ⭐), `finotilucas/Correios-Brasil` (553 ⭐), `VitorLuizC/brazilian-values` (549 ⭐), `brazilian-utils/python` (535 ⭐), `fabioserpa/CNPJ-full` (508 ⭐), `alvarofpp/validate-docbr` (485 ⭐), `aphonsoar/Receita_Federal_do_Brasil_-_Dados_Publicos_CNPJ` (459 ⭐), `kwn/number-to-words` (428 ⭐), `Hitmasu/OpenCNPJ` (427 ⭐), `DeHor-Labs/mcp-fiscal-brasil` (423 ⭐), `SeuAliado/OpenCEP` (420 ⭐), `deividfortuna/fipe` (415 ⭐), `rictom/rede-cnpj` (351 ⭐), `caiopizzol/cnpj-data-pipeline` (341 ⭐).
- **Catálogo HUD / Arsenal SQLite**: expandido para **39.654 ferramentas ativas** indexadas com FTS5.
- **Ledger Global de Progresso**: expandido para **36.989 repositórios estrelados**.


### Onda 15 — Ecossistema de Agentes Autônomos de Código: Apps CC-Switch (Concluída, piso $\ge 300$ ⭐)

Tópicos de origem (Launcher CC-Switch): `cc-switch`, `claude-code`, `claude code`, `codex-cli`, `codex cli`, `openclaw`, `open-claw`, `opencode`, `open-code`, `hermes-agent`, `hermes agent`, `hermes-desktop`, `droid`, `factory-droid`, `pi-agent`, `pi-ai`, `cline`, `copilot-cli`, `copilot cli`, `oh-my-pi`, `deepseek-harness`, `deepseek harness`, `qwen-code`, `qwen code`, `qwen-coder`, `terminal-ai`, `ai-terminal`.

- Fila executada por `tooling/harvest_starred_by_keyword.py` com **corte estrito de 300 estrelas** (27 consultas paginadas).
- **Resultado medido:** **2.449 novos repositórios favoritados** (piso rigoroso $\ge 300$ ⭐). Destaques indexados:
  - **CC-Switch & Multi-Provider Managers:** `lonr-6/cc-desktop-switch` (803 ⭐), `Laliet/cc-switch-web` (528 ⭐), `ming86/cc-account-switcher` (452 ⭐), `mistydew/tokenicode-deepseek-alpha` (384 ⭐), `Golden-Promise/vscode-cc-switch` (309 ⭐).
  - **Claude Code & Frameworks de Engenharia Reversa:** `morluto/rea` (446.678 ⭐), `nextlevelbuilder/ui-ux-pro-max-skill` (147.342 ⭐), `alchaincyf/nuwa-skill` (37.900 ⭐), `img2threejs/img2threejs` (21.060 ⭐), `open-gsd/gsd-core` (11.386 ⭐), `microsoft/TokenEconomizer` (5.510 ⭐), `wesammustafa/Claude-Code-Quest` (3.660 ⭐).
  - **OpenClaw & Orquestradores de Agentes:** `openclaw/openclaw` (394.251 ⭐), `Graphify-Labs/graphify` (144.995 ⭐).
  - **OpenCode & Interpreters:** `affaan-m/ECC` (300.201 ⭐), `code-yeongyu/oh-my-openagent` (70.803 ⭐).
  - **Hermes Agent & Hermes Desktop:** `stablyai/orca` (120.355 ⭐), `Mintplex-Labs/anything-llm` (68.115 ⭐), `fathah/hermes-desktop` (14.554 ⭐), `Orkas-AI/Orkas` (9.147 ⭐).
  - **Codex CLI & Orquestração Multi-Agente:** `slopus/happy` (24.558 ⭐), `OrchestratorInc/agent-orchestrator` (14.362 ⭐).
  - **Droid & DroidDeck:** `Droid-Deck/DroidDeck` (19.026 ⭐), `Wei-Shaw/claude-relay-service` (12.797 ⭐).
  - **Cline:** `cline/cline` (71.465 ⭐), `zhaoxuya520/reverse-skill` (44.373 ⭐).
  - **Pi, Pi Agent & Oh My Pi:** `can1357/oh-my-pi` (38.425 ⭐), `pixel-agents-hq/pixel-agents` (10.130 ⭐), `mvschwarz/openrig` (8.792 ⭐), `gamedev-skills/awesome-gamedev-agent-skills` (8.019 ⭐).
  - **Copilot CLI:** `microsoft/skill-recorder` (5.728 ⭐), `folke/sidekick.nvim` (2.813 ⭐).
  - **DeepSeek Harness:** `nexu-io/open-design` (106.829 ⭐), `tt-a1i/archify` (95.044 ⭐).
  - **Qwen Code:** `vshulcz/deja-vu` (1.467 ⭐), `Piebald-AI/awesome-gemini-cli` (604 ⭐).
  - **Terminal AI & MCPs de Controle:** `wonderwhy-er/DesktopCommanderMCP` (10.275 ⭐), `thinkany-ai/termany` (504 ⭐), `e2b-dev/llm-code-interpreter` (481 ⭐).
- **Catálogo HUD / Arsenal SQLite**: expandido para **42.076 ferramentas ativas** indexadas com FTS5.
- **Ledger Global de Progresso**: expandido para **39.438 repositórios estrelados**.


### Onda 16 — Engenharia Hiper-Nichada e Baixo Nível (Concluída, piso $\ge 300$ ⭐)

Tópicos de origem: `ebpf`, `osdev`, `zero-knowledge`, `zk-snark`, `simd`, `formal-verification`, `fuzzing`, `jit-compiler`, `lock-free`, `decompiler`, `sdr`.

- Fila executada por `tooling/harvest_starred_by_keyword.py` com **corte estrito de 300 estrelas** (11 consultas paginadas).
- **Resultado medido:** **812 novos repositórios favoritados** (piso rigoroso $\ge 300$ ⭐), superando a marca de 40.000 repositórios.
- **Catálogo HUD / Arsenal SQLite**: expandido para **42.875 ferramentas ativas** indexadas com FTS5.
- **Ledger Global de Progresso**: expandido para **40.250 repositórios estrelados**.


### Onda 17 — Top 10 Linguagens de Programação do Mundo (Concluída, piso $\ge 300$ ⭐)

Tópicos de origem: `python`, `javascript`, `typescript`, `java`, `csharp`, `cpp`, `golang`, `rust`, `php`, `c-language`.

- Fila executada por `tooling/harvest_starred_by_keyword.py` com **corte estrito de 300 estrelas** (10 consultas paginadas).
- **Resultado medido:** **30.552 novos repositórios favoritados** (piso rigoroso $\ge 300$ ⭐), atingindo a marca de **70.802 repositórios estrelados no GitHub**. Destaques indexados:
  - **Python (15.897 ferramentas no arsenal):** `donnemartin/system-design-primer` (377.475 ⭐), `vinta/awesome-python` (333.652 ⭐), `521xueweihan/HelloGitHub` (187.874 ⭐), `jackfrued/Python-100-Days` (187.785 ⭐), `nvbn/thefuck` (97.945 ⭐), `freqtrade/freqtrade` (56.721 ⭐), `odoo/odoo` (55.678 ⭐).
  - **JavaScript (7.707 ferramentas no arsenal):** `freeCodeCamp/freeCodeCamp` (458.830 ⭐), `react/react` (252.470 ⭐), `vuejs/vue` (207.800 ⭐).
  - **TypeScript (8.058 ferramentas no arsenal):** `n8n-io/n8n` (209.983 ⭐), `microsoft/vscode` (195.257 ⭐), `shadcn-ui/ui` (94.000 ⭐).
  - **Java (6.148 ferramentas no arsenal):** `trekhleb/javascript-algorithms` (196.724 ⭐), `Snailclimb/JavaGuide` (159.508 ⭐), `spring-projects/spring-boot` (75.200 ⭐).
  - **Go (5.097 ferramentas no arsenal):** `practical-tutorials/project-based-learning` (289.458 ⭐), `avelino/awesome-go` (193.082 ⭐), `kubernetes/kubernetes` (112.000 ⭐).
  - **Rust (4.703 ferramentas no arsenal):** `morluto/rea` (448.571 ⭐), `ultraworkers/claw-code` (194.801 ⭐), `astral-sh/uv` (65.000 ⭐).
  - **C++ (3.051 ferramentas no arsenal):** `CyC2018/CS-Notes` (186.472 ⭐), `ggml-org/llama.cpp` (133.896 ⭐).
  - **PHP (2.941 ferramentas no arsenal):** `ohmyzsh/ohmyzsh` (190.420 ⭐), `laravel/laravel` (85.393 ⭐).
  - **C# (1.967 ferramentas no arsenal):** `jellyfin/jellyfin` (59.176 ⭐), `files-community/Files` (46.571 ⭐).
  - **C (1.660 ferramentas no arsenal):** `huihut/interview` (38.299 ⭐), `vlang/v` (38.095 ⭐), `redis/redis` (67.000 ⭐).
- **Catálogo HUD / Arsenal SQLite**: expandido de 42.875 para **71.350 ferramentas ativas** indexadas com FTS5 (+28.475 novas adições).
- **Ledger Global de Progresso**: expandido de 40.250 para **70.802 repositórios estrelados** (+30.552 repositórios).
- **Espelho Drive D:** Sincronizado em `D:\Program Files\jarvis-arsenal\data\arsenal_library.sqlite` (71.350 ferramentas).


### Onda 18 — AppSec, Injeções, Automação Telegram, Padrões DI e IaC (Concluída, piso $\ge 300$ ⭐)

Tópicos de origem: `ssti`, `command-injection`, `template-injection`, `telethon`, `pyrogram`, `userbot`, `dependency-injection`, `iac`, `infrastructure-as-code`, `jailbreak`.

- Fila executada por `tooling/harvest_starred_by_keyword.py` com **corte estrito de 300 estrelas** (10 consultas paginadas).
- **Resultado medido:** **318 novos repositórios favoritados** (piso rigoroso $\ge 300$ ⭐). Destaques indexados:
  - **SSTI & Template Injections:** `epinna/tplmap` (4.215 ⭐), `vladko312/SSTImap` (1.727 ⭐), `Adamkadaban/CTFs` (872 ⭐), `DiogoMRSilva/websitesVulnerableToSSTI` (422 ⭐), `Hackmanit/TInjA` (428 ⭐).
  - **Command Injection:** `commixproject/commix` (5.903 ⭐), `arch3rPro/PentestTools` (1.816 ⭐), `libnet/nemesis` (530 ⭐), `ewilded/shelling` (441 ⭐).
  - **Automação & Clientes Telegram:** `LonamiWebs/Telethon` (12.066 ⭐), `pyrogram/pyrogram` (4.613 ⭐), `ItIsMeCall911/Awesome-Telegram-OSINT` (2.940 ⭐), `chigwell/telegram-mcp` (2.018 ⭐), `IVETRI/SongPlayRoBot` (1.039 ⭐), `TeamPGM/PagerMaid-Pyro` (813 ⭐).
  - **Injeção de Dependência (DI Patterns):** `google/dagger` (17.200 ⭐), `uber-go/dig` (4.100 ⭐), `alexzaitsev/apk-dependency-graph` (760 ⭐), `Papooch/nestjs-cls` (712 ⭐), `Swinject/Swinject` (6.200 ⭐).
  - **Infrastructure as Code (IaC Templates):** `hashicorp/terraform` (50.191 ⭐), `aquasecurity/trivy` (39.207 ⭐), `crossplane/crossplane` (12.236 ⭐), `DNSControl/dnscontrol` (4.001 ⭐), `octodns/octodns` (3.778 ⭐), `iann0036/former2` (2.417 ⭐).
  - **Jailbreak (LLM Red-Teaming, Benchmarks & Device Research):** `SheltonLiu-N/AutoDAN` (469 ⭐), `SlowLow999/UltraBr3aks` (467 ⭐), `Alejandros17487/ai-jailbreaks` (430 ⭐), `TrustAI-laboratory/Learn-Prompt-Hacking` (392 ⭐), `kpwn/yalu` (390 ⭐), `TheOfficialFloW/Trinity` (388 ⭐), `CHATS-lab/persuasive_jailbreaker` (367 ⭐).
- **Catálogo HUD / Arsenal SQLite**: expandido de 71.350 para **71.660 ferramentas ativas** indexadas com FTS5 (+310 ferramentas).
- **Ledger Global de Progresso**: expandido de 70.802 para **71.120 repositórios estrelados** (+318 repositórios).
- **Espelho Drive D:** Sincronizado em `D:\Program Files\jarvis-arsenal\data\arsenal_library.sqlite` (71.660 ferramentas).


### Onda 19 — Termos Restantes: CSTI, Scrapers, OSINT, RCE e Templates (Concluída, piso $\ge 300$ ⭐)

Tópicos de origem: `csti`, `scrapers`, `web-scraping`, `osint`, `haveibeenpwned`, `breach-detection`, `rce`, `di-patterns`, `configuration-injection`, `iac-templates`, `scripts`.

- Fila executada por `tooling/harvest_starred_by_keyword.py` com **corte estrito de 300 estrelas** (11 consultas paginadas).
- **Resultado medido:** **2.164 novos repositórios favoritados** (piso rigoroso $\ge 300$ ⭐), elevando o total da conta para **73.284 repositórios estrelados**. Destaques indexados:
  - **CSTI & Injeções:** `cs0x7f/cstimer` (792 ⭐), `tijme/angularjs-csti-scanner` (325 ⭐).
  - **Scrapers & Motores de Coleta:** `gocolly/colly` (25.589 ⭐), `apify/apify-mcp-server` (15.598 ⭐), `omkarcloud/botasaurus` (5.832 ⭐), `drawrowfly/tiktok-scraper` (5.252 ⭐), `speedyapply/JobSpy` (4.689 ⭐).
  - **Web Scraping & Agentes de Navegação:** `firecrawl/firecrawl` (200.444 ⭐), `browser-use/browser-use` (120.575 ⭐).
  - **OSINT & Pesquisa de Fontes Abertas:** `sherlock-project/sherlock` (108.704 ⭐), `koala73/worldmonitor` (90.454 ⭐).
  - **Auditoria de Credenciais & Breach Detection:** `khast3x/h8mail` (5.375 ⭐), `thewhiteh4t/pwnedOrNot` (2.677 ⭐), `KatrielMoses/MailAccess` (1.771 ⭐).
  - **RCE & Exploração:** `reddelexc/hackerone-reports` (6.666 ⭐), `k8gege/K8tools` (6.247 ⭐).
  - **Scripts & Automações Gerais:** `massgravel/Microsoft-Activation-Scripts` (198.413 ⭐), `nvm-sh/nvm` (95.788 ⭐), `0xdea/ghidra-scripts` (304 ⭐).
- **Catálogo HUD / Arsenal SQLite**: expandido de 71.660 para **73.766 ferramentas ativas** indexadas com FTS5 (+2.106 ferramentas).
- **Ledger Global de Progresso**: expandido de 71.120 para **73.284 repositórios estrelados** (+2.164 repositórios).
- **Espelho Drive D:** Sincronizado em `D:\Program Files\jarvis-arsenal\data\arsenal_library.sqlite` (73.766 ferramentas).


### Onda 20 — Visualização de Dados, Web Design e Engenharia Frontend (Concluída, piso $\ge 300$ ⭐)

Tópicos de origem: `dataviz`, `webdesign`, `frontend`.

- Fila executada por `tooling/harvest_starred_by_keyword.py` com **corte estrito de 300 estrelas** (3 consultas paginadas).
- **Resultado medido:** **1.200 repositórios processados e favoritados** nesta onda (**526 novos registros líquidos adicionados** ao SQLite FTS5 sobre os 73.766 anteriores), elevando o total do arsenal para **74.292 ferramentas indexadas**. Destaques por categoria:
  - **DataViz (`dataviz` — 69 repositórios):** `plouc/nivo` (14.134 ⭐), `rougier/scientific-visualization-book` (11.682 ⭐), `GoAdminGroup/go-admin` (9.017 ⭐), `pa7/heatmap.js` (6.380 ⭐), `holoviz/panel` (5.823 ⭐), `swimlane/ngx-charts` (4.357 ⭐).
  - **WebDesign (`webdesign` — 22 repositórios):** `creativetimofficial/material-kit` (5.919 ⭐), `silexlabs/Silex` (3.037 ⭐), `nicolesaidy/awesome-web-design` (2.812 ⭐).
  - **Frontend (`frontend` — 1.111 repositórios):** `react/react` (252.499 ⭐), `vuejs/vue` (212.623 ⭐), `msitarzewski/agency-agents` (167.678 ⭐).
- **Catálogo HUD / Arsenal SQLite**: expandido de 73.766 para **74.292 ferramentas ativas** indexadas com FTS5 (+526 adições líquidas).
  - Distribuição atualizada dos Esquadrões: **Cyberspace** (4.289), **Aegis** (4.558), **Neuro-Cognitive** (18.761), **Tactical** (4.700), **Hyperion** (41.984).
- **Ledger Global de Progresso (`.star_progress.json`)**: consolidado e sincronizado com o SQLite em **74.292 repositórios estrelados**.
- **Espelho Drive D:** Sincronizado em `D:\Program Files\jarvis-arsenal\data\arsenal_library.sqlite` (74.292 ferramentas, 54,69 MB, índices compostos ativos).


### Onda 20b — Expansão Data Visualization & Web Design (Concluída, piso $\ge 300$ ⭐)

Tópicos de origem: `data-visualization`, `web-design`.

- Fila executada por `tooling/harvest_starred_by_keyword.py` com **corte estrito de 300 estrelas** (2 consultas paginadas, deduplicadas contra os 74.292 registros prévios).
- **Resultado medido:** **361 novos repositórios favoritados** (**+361 adições inéditas** ao SQLite FTS5), além de 559 já catalogados atualizados. Destaques por categoria:
  - **Data Visualization (`data-visualization` — 702 candidatos, +270 novos):** líder `d3/d3` (113.903 ⭐), `airbnb/visx` (21.102 ⭐), `c3js/c3` (9.350 ⭐), `uber/react-vis` (8.784 ⭐), `visgl/react-map-gl` (8.514 ⭐), `antvis/F2` (7.996 ⭐).
  - **Web Design (`web-design` — 217 candidatos, +91 novos):** líder `Leonxlnx/taste-skill` (113.051 ⭐), `Heydon/principles-of-web-accessibility` (997 ⭐), `Skyscanner/backpack` (543 ⭐), `carbon-design-system/carbon-web-components` (476 ⭐).
- **Catálogo HUD / Arsenal SQLite & `.star_progress.json`**: expandido de 74.292 para **74.653 ferramentas/repositórios** (+361 adições líquidas).
  - Distribuição atualizada dos Esquadrões: **Cyberspace** (4.298), **Aegis** (4.568), **Neuro-Cognitive** (18.824), **Tactical** (4.713), **Hyperion** (42.250).
- **Espelho Drive D:** Sincronizado em `D:\Program Files\jarvis-arsenal\data\arsenal_library.sqlite` (74.653 ferramentas).
