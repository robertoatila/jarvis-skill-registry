---
title: Automacao Total e Pipeline Autonoma do JARVIS
type: sovereign-pipeline-guide
status: FULLY_AUTOMATED_v2.1
total_repos_supported: 2168
pipeline_steps: 5
fail_closed_rules: 13
tags:
  - jarvis
  - autonomous-pipeline
  - token-budget
  - continuous-learning
  - subagents
---

# ⚡ Automação Total e Pipeline Autônoma do J.A.R.V.I.S.

> [!IMPORTANT] 🚀 Arquitetura de Auto-Evolução Contínua
> O J.A.R.V.I.S. não é um repositório estático. Ele é um **sistema vivo de inteligência**, capaz de ingerir repositórios do seu GitHub, analisar sua segurança contra 13 regras restritas, podar descrições para respeitar o orçamento de tokens, sintetizar contratos executáveis e alimentar o Obsidian e os 5 esquadrões de subagentes automaticamente.

---

## 🔁 1. A Esteira Autônoma de 5 Passos (The 5-Step Ingestion Engine)

```text
 ┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
 │ 1. LER      │ ──> │ 2. ANALISAR  │ ──> │ 3. PODAR    │ ──> │ 4. MELHORAR  │ ──> │ 5. IMPLEMENT.│
 │ Ingestão de │     │ 13 Regras de │     │ Poda Ativa  │     │ Síntese de   │     │ Commit no    │
 │ Código & AST│     │ Segurança    │     │ <= 25 pals. │     │ SKILL.md     │     │ Arsenal & IDE│
 └─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘     └──────────────┘
```

### Passo 1: LER (Ingestão & Reconhecimento de Código)

- Lê os metadados do repositório (`package.json`, `Cargo.toml`, `go.mod`, `pyproject.toml`, `README.md`).
- Mapeia arquitetura, linguagem primária e tópicos do GitHub.

### Passo 2: ANALISAR (Laudo Forense Fail-Closed)

- Avalia contra as 13 regras restritas do Hyperion (execução remota não autenticada, dump de credenciais sem autorização, bibliotecas obsoletas, etc.).
- Determina se o repositório é promovível ou deve ser isolado em quarentena (`Tombstone`).

### Passo 3: PODAR (Governança de Token Budget)

- **A Lei do Mito do Compounding**: Apenas instruções enxutas e de alta densidade semântica mantêm a IA rápida e inteligente.
- Reduz a descrição do sistema para **rigorosamente $\le 25$ palavras**, garantindo que centenas de skills coexistam no IDE sem consumir a janela de contexto.

### Passo 4: MELHORAR (Síntese do Contrato Soberano)

- Gera o arquivo canônico `SKILL.md` com metadados YAML, capacidades formais e instruções operacionais sem quaisquer marcadores fictícios (*Zero Placeholders*).
- Formata os 6 lockfiles multiplataforma (Cursor, Gemini/Antigravity, Codex, Claude, ChatGPT e Genérico).

### Passo 5: IMPLEMENTAR (Homologação e Distribuição Automática)

- Grava no cofre soberano em [`E:\.skill-registry\skills`](file:///e:/.skill-registry/skills).
- Espelha instantaneamente para [`C:\Users\Ad\.gemini\config\skills`](file:///C:/Users/Ad/.gemini/config/skills) via [`Sync-SovereignArsenalToIde.ps1`](file:///e:/.skill-registry/tooling/Sync-SovereignArsenalToIde.ps1).
- Atualiza o grafo e as notas do Obsidian.

---

## 🛠️ 2. Ferramental de Execução por Linha de Comando (CLI Soberano)

Para rodar a pipeline sem precisar da interface web:

```powershell
# Ingestão de um repositório arbitrário via CLI
powershell -ExecutionPolicy Bypass -NoProfile -File "E:\.skill-registry\tooling\Invoke-JarvisSkillWorkflow.ps1" -RepoFullName "microsoft/autogen"

# Sincronização em lote para o Antigravity IDE
powershell -ExecutionPolicy Bypass -NoProfile -File "E:\.skill-registry\tooling\Sync-SovereignArsenalToIde.ps1"

# Reinicialização rápida do servidor backend
powershell -ExecutionPolicy Bypass -NoProfile -File "E:\.skill-registry\tooling\Restart-JarvisServer.ps1"
```

---

## 🖥️ 3. Acesso com 1 Clique (Zero-Flicker Launcher)

- **Localização**: [`C:\Users\Ad\Desktop\J.A.R.V.I.S..lnk`](file:///C:/Users/Ad/Desktop/J.A.R.V.I.S..lnk)
- **Comportamento**:
  - Inicia via `wscript.exe` com zero janelas de CMD piscando.
  - Verifica e ativa a porta `8899` em background se necessário.
  - Vocaliza confirmação de integridade por áudio SAPI nativo.
  - Abre o Command Center HUD com visual holográfico e áudio interativo.

---

## 📅 4. Esteira Mestra Autônoma Dominical (Todo Domingo às 20:00)

Agendamento no Windows Task Scheduler (`Jarvis-Weekly-Sunday-Autonomous-Pipeline`) para execução autônoma completa aos domingos às 20:00:

```text
 ┌──────────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
 │ 1. PUXAR STARS API   │ ──> │ 2. ATUALIZAR REPOS   │ ──> │ 3. SEPARAR & FILTRAR │
 │ sync_starred_repos   │     │ instalador-repo (205)│     │ setup-e-filtrar-sk.  │
 └──────────────────────┘     └──────────────────────┘     └──────────────────────┘
            │                                                         │
            ▼                                                         ▼
 ┌──────────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
 │ 4. AVALIAÇÃO SSP-v13 │ ──> │ 5. INSTALAR NO IDE   │ ──> │ 6. RECEIPT & LEDGER  │
 │ Triagem e SKILL.md   │     │ sync_and_optimize    │     │ Quantum Ledger + SAPI│
 └──────────────────────┘     └──────────────────────┘     └──────────────────────┘
```

1. **Puxar Novos Repositórios**: Sincroniza até **50.000 repositórios** favoritados da API do GitHub via [`sync_starred_repos.py`](file:///e:/.skill-registry/tooling/sync_starred_repos.py) com paginação dinâmica inteligente (Link header `rel="next"`).
2. **Atualizar Repositórios Brutos**: `git pull`/`git fetch` nos 205 repositórios do baú via [`instalador-repo.bat`](file:///e:/.skill-registry/instalador-repo.bat) e validação de SHAs no lockfile.
3. **Separar e Extrair Skills**: Extrai as 165 skills ativas do baú via [`setup-e-filtrar-skills.bat`](file:///e:/.skill-registry/setup-e-filtrar-skills.bat).
4. **Avaliação Autônoma SSP-v13**: Avalia candidatos recentes, isola riscos em quarentena fail-closed e gera novos contratos `SKILL.md`.
5. **Instalar em Tudo e Todos**: Sincroniza o arsenal completo no IDE global (`C:\Users\Ad\.gemini\config\skills`) com poda ativa ($\le 12$ palavras) mantendo uso de tokens $< 35\%$.
6. **Auditoria & Assinatura**: Grava o comprovante em `evidence/sunday_autonomous_receipt.json` e vocaliza a conclusão via síntese de voz nativa SAPI.

### Comandos de Gestão da Rotina Dominical

```powershell
# Registrar / Reagendar tarefa semanal no Windows
powershell -ExecutionPolicy Bypass -NoProfile -File "E:\.skill-registry\tooling\Register-JarvisSundayTask.ps1" -Time "20:00"

# Executar manualmente a qualquer momento (sem esperar domingo)
powershell -ExecutionPolicy Bypass -NoProfile -File "E:\.skill-registry\tooling\Invoke-SundayMasterAutonomousRoutine.ps1"
```

