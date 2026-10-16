# J.A.R.V.I.S. Prompt Packs & Autonomous Architecture Blueprint Catalog

Este diretório reúne a coleção canônica de **Guias de Engenharia, Prompt Packs e Blueprints de Arquitetura Autônoma** do ecossistema J.A.R.V.I.S. (AI Workshop / Zubair Trabzada Edition 2026).

---

## Sumário Executivo dos Packs

| Arquivo | Tema Central | Modelos / Stacks | Principais Mecanismos & Invariantes |
| :--- | :--- | :--- | :--- |
| [`JARVIS-Prompt-Pack.pdf`](JARVIS-Prompt-Pack.pdf) | **The Original Second Brain** | Claude Opus / Local CLI | Galáxia 3D com `3d-force-graph`, mergulho de câmera até a nota de origem (*fly-to-source*), voz de mordomo britânico, endpoint `/remember` para crescimento ao vivo sem recarregamento. |
| [`Build-Your-Own-Jarvis-Opus-5.5-Prompt-Pack.pdf`](Build-Your-Own-Jarvis-Opus-5.5-Prompt-Pack.pdf) | **Desktop + Mobile Autonomous Agent** | Claude Opus 5.5, Retell AI, Telegram | 18 prompts em 2 partes: Linha telefônica com Retell, Google Line (Gmail/Calendar OAuth com PKCE), Bot do Telegram via long-polling, ordens permanentes (*standing orders*), *busy opener*, *hotline* com portão de código secreto de 4 dígitos, e auditoria de segurança lock down. |
| [`Build-Your-Own-Jarvis-GPT-6-Astra-Prompt-Pack.pdf`](Build-Your-Own-Jarvis-GPT-6-Astra-Prompt-Pack.pdf) | **Autonomous Organs & Accountability** | GPT-6 Astra, OpenRouter | 16 prompts em 2 partes: Sessões de foco (*focus sessions*), trava adiada (*deferred lock*), comando "lock this tab", nomeação falada da distração com descarte imediato (privacidade estrita), olhos por webcam para postura, *screen watch* com detecção de estagnação, e instrumentação diagnóstica antes do fix. |
| [`Build-Your-Own-Jarvis-Fable-5.1-Prompt-Pack.pdf`](Build-Your-Own-Jarvis-Fable-5.1-Prompt-Pack.pdf) | **Second Edition High-Density** | Claude Fable 5.1 | 8 prompts de alta densidade onde 1 prompt substitui 3: síntese automática de galáxia, olhos na tela via `getDisplayMedia`, harness `preflight.py` obrigatório para validação de ponta a ponta, e troca de modelo em tempo de execução via voz. |
| [`Give-Your-Jarvis-Reflexes-Jev-Prompt-Pack.pdf`](Give-Your-Jarvis-Reflexes-Jev-Prompt-Pack.pdf) | **Fast Reflex Layer (200ms)** | TypeSafe AI (Jev) | Faixa de pré-processamento (*prepass strip*) com 5 perguntas e portões calibrados (`LANE_ACT`, `COMPLETE_FIRE`, `ADDRESSED_ROOM`, `STAKES_CONFIRM`), verificação de notas no cofre (*vault check*), **The Judge** (bloqueio de afirmações de ações executadas sem recibo), modo filmagem e shadow governor de triagem. |
| [`Give-Your-Jarvis-X-Ray-Vision-REA-Prompt-Pack.pdf`](Give-Your-Jarvis-X-Ray-Vision-REA-Prompt-Pack.pdf) | **X-Ray Vision & Reverse Engineering** | REA (`rea-agents`), Node 24+, Chrome CDP | Inspeção autônoma de sites em perfil limpo e isolado de Chrome via porta 9333, rolagem automatizada, log de recursos, fingerprint de licenças (Three.js, GSAP), síntese de teardown e nascimento da nota diretamente no Obsidian vault sob `[[REA]]`. |
| [`HOLO-Start-Here.pdf`](HOLO-Start-Here.pdf) & [`holo-gestures-free.zip`](holo-gestures-free.zip) | **HOLO Bare-Hands Gestures** | MediaPipe WASM local, Three.js | Controle gestual sem toque para notas markdown e modelos 3D GLB (Smithsonian Apollo 11 e Triceratops). 100% local, zero nuvem, zero telemetria externa. Extraído operacionalmente em `D:\Program Files\jarvis-arsenal\holo\`. |
| [`Jarvis-Screen-Starter-Pack.pdf`](Jarvis-Screen-Starter-Pack.pdf) | **Screen Eyes & Careful Driver** | Python Pillow, AppleScript / Shell | Screen-guide com ponteiro vermelho-laranja indicando o controle exato no desktop, regras de condutor cuidadoso com confirmação explícita passo a passo e recusas estritas para pagamentos/senhas/exclusões. |
| [`Jarvis-Phone-Starter-Pack.pdf`](Jarvis-Phone-Starter-Pack.pdf) | **Phone Pack & Deals Engine** | Retell AI, Headless Chrome, Telegram | Scripts oficiais para agente de reservas e agendamentos, agente de consultas rápidas (90 segundos), recepcionista com portão de código seguro de 4 dígitos, e motor de propostas/faturas (HTML para PDF via Chrome headless) enviado para Telegram. |
| [`Run-Jarvis-for-Pennies-Cost-Guide.pdf`](Run-Jarvis-for-Pennies-Cost-Guide.pdf) | **Cost Governance & Economics** | Ollama, Anthropic, Retell, ElevenLabs | Arquitetura de custo zero para operações locais (Ollama, Web Speech, HOLO, notas 3D) e micro-tarifação para chamadas sob demanda (Sonnet a ~1.5¢/resposta, Retell a ~15¢/ligação). |
| [`AI-Debate-Night-Prompt-Pack.pdf`](AI-Debate-Night-Prompt-Pack.pdf) | **Multi-Agent AI Debate Show** | Claude vs GPT / Dual Personas | Debate interativo entre JARVIS (mordomo implacável e polido focado no longo prazo) e TARS (robô literal e direto focado na missão em 8 palavras), moderado pelo oficial CASE com seletores de humor, rodadas relâmpago e testes de estresse. |
| [`Your-Jarvis-in-Sixteen-Languages-Prompt-Pack.pdf`](Your-Jarvis-in-Sixteen-Languages-Prompt-Pack.pdf) | **Multilingual JARVIS** | Internationalization | Adaptação e tradução contextual para 16 idiomas preservando tom butleriano britânico. |
| [`Ultimate Prompting Guide for Video Generation Models.pdf`](Ultimate Prompting Guide for Video Generation Models.pdf) | **Generative Video Directing** | Video LLMs & Diffusion | Guia mestre de engenharia de prompt para geração e transição cinematográfica de vídeo. |

---

## Invariantes de Execução Soberana (SSP-v13.4)

1. **Zero Vazamento de Credenciais:** Nenhuma chave de API (Anthropic, OpenAI, Retell, Telegram) pode ser colada em janelas de chat ou versionada em repositórios abertos. Elas residem estritamente em `config/api_keys.json` ou variáveis de ambiente protegidas pelo `.gitignore`.
2. **Governança de Armazenamento no Disco D:** Nenhum arquivo temporário pesado, modelo GGUF, cache de clonagem ou binário é descarregado na partição de sistema `C:\`. Toda infraestrutura pesada reside em `D:\Program Files\jarvis-arsenal\`.
3. **The Judge & Recibos Estritos:** O assistente nunca pode declarar "feito" ou "enviado" sem um recibo de execução determinístico emitido pela ferramenta subjacente.
4. **Harness Preflight:** Nenhuma implementação é declarada completa sem a aprovação estrita dos testes executáveis em tempo real (`jarvis.py --doctor`, `jarvis.py --test`, `audit_pre_publish_security.py`).
