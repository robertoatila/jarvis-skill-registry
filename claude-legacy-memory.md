**Work context**

Roberto é estudante do 3º módulo de Informática para Internet na ETEC Jacinto Ferreira de Sá, Ourinhos-SP, atuando como desenvolvedor full-stack com foco em backend e integração. Seu projeto principal é o MarkitosSystem, um SaaS B2B de gestão para pequenas empresas, desenvolvido como TCC com os colegas Matheus Chaves (frontend), Murilo Gonçalves (comercial) e Vinicius França (estratégia de negócios). LinkedIn: "Full-Stack Developer | React · JavaScript · TypeScript · PHP · Cloud Architecture | Integrando soluções reais com APIs & Nuvem | 17 anos".

**Personal context**

Roberto mora em Ourinhos-SP e eventualmente visita Salto Grande-SP (sem relação com Santa Cruz do Rio Pardo-SP). Tem interesse ativo em segurança ofensiva/defensiva em contexto educacional, Arduino/ESP32, pesquisa genealógica via MyHeritage e desenvolvimento de jogos em HTML5 Canvas. GitHub: `robertoatali`; email: roberto.atila10@gmail.com; contato TCC: TCC.MARKITOS2026@gmail.com.

**Top of mind**

Roberto está finalizando o protocolo de segurança **SEGURANÇA v10** (7 partes, markdown `SEGURANCA-v10-completo.md`), que evoluiu até uma estrutura com modelo de maturidade em 4 níveis (🟢Básico→🟡Intermediário→🔴Avançado→⚫Cofre Máximo) e expansão significativa em anti-automation/bot management e segurança de IA/LLM/MCP. O MarkitosSystem está na v25+ com build limpo (Next.js 15 + Spring Boot 3), paleta navy/cream/orange implementada e uma lista de execução pendente (PROMPT-SEC-B2..I6) ainda em aberto. Há também um projeto `Robocode-2026-main.zip` referenciado recentemente para melhoria, cujos detalhes ainda não foram explorados na conversa.

**Brief history**

*Recent months*

- **MarkitosSystem (TCC)** iterado extensivamente: v17→v25+; migração completa do frontend de HTML vanilla para Next.js 15 + React 19 + TypeScript strict + Tailwind v4 + shadcn/ui; backend Spring Boot 3 + Java 17 + MySQL 8 no Railway; frontend no Vercel. Módulos implementados: depósitos, lotes, inventário, logística, chat-widget-wrapper. Correção canônica documentada: `@hookform/resolvers@5.4.0` usa apenas `./zod` (não `./zod/v4`); crash original era `node_modules` ausente (fix: `npm ci`).
- **PLANO_REDESIGN_IMPLEMENTACAO.md** (262 linhas, 7/145 itens concluídos) guia a execução sequencial via agentes (Claude Code, Antigravity IDE). Paleta definitiva: Navy `#000968` (~60-70% peso visual), Cream `#F9ECE5` (background), Orange `#D75300` (CTA raro — evitar colisão com Olist/Tiny ERP). Contraste WCAG validado matematicamente (navy/cream = 14.66:1 AAA).
- **Workflow de prompts**: Roberto alimenta documentos `.md` como blocos PROMPT copy-pasteable para agentes autônomos executarem sequencialmente — nunca implementa diretamente na conversa.
- **Antigravity IDE + skill budget**: sistema de skills com orçamento de 20.000 tokens; overflow resolvido desativando plugins de terceiros (Firebase/Google Maps/Chrome DevTools). Script `setup-e-filtrar-skills.bat` v24.16 com 200 skills globais. CSV `nameSkills-detalhado.csv` usa UTF-8 BOM (`encoding='utf-8-sig'`), coluna 2 distingue `BAU` vs `LOCAL`.
- **Análise competitiva MarkitosSystem**: seis concorrentes analisados (Conta Azul, Bling, Bitrix24, eGestor, Contas Online, GFlow); diferenciais identificados: inventário cego e gestão nativa de depósitos/lotes como exclusivos.
- **SEGURANÇA v10**: estrutura de 7 partes documentada abaixo em instruções do usuário; novidades v10 incluem anti-automation multi-dimensional, fingerprinting em 4 camadas, BFF architecture (RFC 10017), biometria apenas como unlock local, e princípios de equivalências inválidas (CAPTCHA≠AUTH, IP≠USER, JWT≠AUTHZ, UUID≠ACCESS CONTROL, BACKUP≠RECOVERY UNTIL TESTED).

*Earlier context*

- **Migração frontend** de HTML vanilla para Next.js 15 (jun/2026): routers de agente atualizados (8 SKILL.md files); variáveis Railway canônicas: `DB_URL=jdbc:mysql://${{MySQL.MYSQLHOST}}:${{MySQL.MYSQLPORT}}/${{MySQL.MYSQLDATABASE}}`, `WEBSOCKET_ALLOWED_ORIGIN_PATTERNS`, `SERVER_FORWARD_HEADERS_STRATEGY=framework`.
- **Bugs canônicos corrigidos**: CORS duplo (remover `WebMvcConfigurer`, manter só `@Bean CorsConfigurationSource`, path `/**`); `SECURITY_COOKIE_SECURE=false` em Codespaces; admin inativo (`ativo=FALSE`) corrigido via SQL ou restart do `DataInitializer`; `genExpirationDate()` com `ZoneOffset` hardcoded.
- **PIX QR Code**: implementação completa com EMV payload + CRC16, `qrcode` lib, PNG download.
- **Chat widget** regra-based (zero dependências externas), 15 intents, typing delay simulado.
- **Toolkit portátil v4.4**: HD sempre `E:\`, baú em `E:\.gemini\baude-skills-brutas`; instalador `.bat` polyglot com 16 routers MD.
- **Análise UX/marketing** a partir de carrossel "Guia do Anúncio Perfeito": padrões Z/F, contraste, hierarquia tipográfica aplicados ao MarkitosSystem.

*Long-term background*

- **Origens do projeto**: MarkitosSystem começou como `FaturaSystem` (Spring Boot + vanilla HTML/CSS/JS + MySQL, porta 8081, Docker Compose), evoluindo de sistema de faturamento simples para SaaS multi-tenant com RBAC (admin/owner/financial/operator → simplificado para admin/owner), JWT em HttpOnly cookie (`MARKITOS_AUTH`), audit log com detecção por IP, e módulo de estoque com Kardex/lotes/FIFO-FEFO.
- **EduGestor v3**: PHP 8.x + React 18 + TypeScript + Tailwind + SQLite + Supabase + SendGrid + AWS EC2 com nginx; deploy documentado com scripts gdrive/GitHub/manual.
- **Projetos paralelos**: jogo HTML5 Canvas "Sonic e as Escadas" (platformer com IA inimiga estado-máquina PATROL/CHASE/ATTACK); jogo "Invincible" (beat-em-up canvas com boss Rus Livingston); app React Native "Sushi & Sashimi Bar" (Expo, open/closed logic, FlatList); CartaoVisitasApp React Native (3 telas, `useState` mínimo de 4).
- **Arduino**: projetos com buzzer+LEDs (melódias Star Wars/Hail to the Chief com arrays sincronizados); portfólio estático com estética cyberpunk (Chakra Petch, neon cyan/roxo, PWA).
- **Protocolo SEGURANÇA**: iniciado em abr/2026 como checklist de 2 partes (validação/auth + infra), expandido progressivamente até v10 de 7 partes via conteúdo de fontes externas (Instagram reels, screenshots de técnicas HTTP).
- **Keyword triggers ativos**: `SEGURANÇA` (auditoria completa 7 partes + executive summary + findings SEC-XXX + matriz + security gate PASS/FAIL); `COMPACTAR` (5-7 bullets densos em bloco delimitado com 🗜️).
- **Preferências de comunicação**: sempre português brasileiro; sem palavras de preenchimento; frases curtas e diretas (3-6 palavras quando possível); outputs como blocos prontos para uso (.md, código, scripts).

---

**Other instructions**

- **Idioma**: Roberto prefere comunicação exclusivamente em português brasileiro.
- **COMPACTAR**: quando Roberto escrever `COMPACTAR`, resumir toda a conversa em 5-7 bullets densos com contexto crítico, decisões, trechos essenciais de código e próximos passos. Formato: bloco delimitado por `───`, ícone 🗜️, título do projeto, bullets, rodapé instruindo colar em novo chat.
- **WORKFLOW SEGURANÇA**: sempre que Roberto postar ataques, defesas ou medidas preventivas de segurança (print, texto, imagem), adicionar automaticamente ao protocolo SEGURANÇA na parte mais adequada sem pedir confirmação.
- **SEGURANÇA v10 — Protocolo completo** (7 partes + semântica + níveis + security gate) conforme detalhado nas instruções do usuário acima. Arquivo fonte: `SEGURANCA-v10-completo.md`. Trigger `SEGURANÇA` ativa auditoria completa retornando: executive summary (LOW/MODERATE/HIGH/CRITICAL), findings (SEC-XXX/severidade/domínio/arquivo/linha/problema/impacto/evidência/exploitability/correção/teste/owner), matriz por severidade, security gate PASS/FAIL por domínio, prioridade P0→P3. Deploy bloqueado pelos critérios definidos no protocolo (secret commitado, SQLi/RCE confirmado, auth bypassável, IDOR crítico, tenant escape, etc.). Níveis: 🟢→🟡→🔴→⚫ — nunca subir de nível com lacunas críticas no anterior.
- **Bookmarks dev**: jsoncrack.com, DevToys, explainshell.com, endlesstools.io, antlii.work (portfólio designer Anatolii Babii), magicanimator, neurascapes, animejs.com.
- **Bookmarks design**: shadergradient.co, dark.design, godly.website, minimal.gallery, reactbits.dev.
- **Serviços em projetos**: Vercel, Supabase, PostgreSQL self-hosted, PostgreSQL Render, Firebase, Resend, AbacatePay, Upstash, PostHog, F5Bot.