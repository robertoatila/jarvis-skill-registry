# Operacao 2: GitHub Deep Triage & Classification Report

**Skill Registry v1.0.0 - Triagem Multi-Sinal & Inspecao de Arvores**
- **Total de Repositorios Avaliados**: **1857**
- **Metodologia**: Multi-Signal Scoring (Topics + Name + Desc + Lang + Popularity)
- **Data/Hora (UTC)**: 2026-09-01T18:39:41.5159182Z

---

## 1. Distribuicao por Tiers de Relevancia

| Tier | Descricao | Quantidade de Repositorios |
| :--- | :--- | :--- |
| **Tier 1: Agentic & Skill Candidates** | Repositorios com alta densidade de agentes, MCP, skills e assistentes | **263** |
| **Tier 2: Tooling & Infra** | Ferramentas de seguranca, automacao, CLI e infraestrutura | **343** |
| **Tier 3: Libraries & Frameworks** | Bibliotecas de runtime, SDKs e frameworks de aplicacao | **1040** |
| **Tier 4: General Software** | Software geral, documentacao, repositorios auxiliares | **211** |

---

## 2. Top 20 Repositorios com Maior Relevancia Identificados

| # | Repositorio | Score | Categoria Inferida | Linguagem | Stars |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **code-yeongyu/oh-my-openagent** | 1 | AGENT_SKILL_COLLECTION | TypeScript | 68590 |
| 2 | **OthmanAdi/planning-with-files** | 1 | AGENT_SKILL_COLLECTION | Shell | 26555 |
| 3 | **thedotmack/claude-mem** | 1 | AGENT_SKILL_COLLECTION | JavaScript | 92870 |
| 4 | **HKUDS/nanobot** | 1 | MCP_PROTOCOL_SERVER | Python | 47618 |
| 5 | **kepano/obsidian-skills** | 1 | AGENT_SKILL_COLLECTION | Unknown | 47640 |
| 6 | **decolua/9router** | 1 | PLATFORM_ASSISTANT_TOOLING | JavaScript | 26863 |
| 7 | **promptfoo/promptfoo** | 1 | PLATFORM_ASSISTANT_TOOLING | TypeScript | 24731 |
| 8 | **mksglu/context-mode** | 1 | MCP_PROTOCOL_SERVER | TypeScript | 20294 |
| 9 | **diegosouzapw/OmniRoute** | 1 | MCP_PROTOCOL_SERVER | TypeScript | 59743 |
| 10 | **zhayujie/CowAgent** | 1 | MCP_PROTOCOL_SERVER | Python | 46750 |
| 11 | **ComposioHQ/awesome-claude-skills** | 1 | MCP_PROTOCOL_SERVER | Python | 74217 |
| 12 | **jeecgboot/JeecgBoot** | 1 | MCP_PROTOCOL_SERVER | Java | 47590 |
| 13 | **Donchitos/Claude-Code-Game-Studios** | 1 | AGENT_SKILL_COLLECTION | Shell | 24732 |
| 14 | **calesthio/OpenMontage** | 1 | AGENT_SKILL_COLLECTION | Python | 55318 |
| 15 | **ToolJet/ToolJet** | 1 | MCP_PROTOCOL_SERVER | JavaScript | 40808 |
| 16 | **addyosmani/agent-skills** | 1 | AGENT_SKILL_COLLECTION | JavaScript | 91421 |
| 17 | **Graphify-Labs/graphify** | 1 | MCP_PROTOCOL_SERVER | Python | 113312 |
| 18 | **K-Dense-AI/scientific-agent-skills** | 1 | AGENT_SKILL_COLLECTION | Python | 41421 |
| 19 | **op7418/guizang-ppt-skill** | 1 | AGENT_SKILL_COLLECTION | HTML | 25426 |
| 20 | **Panniantong/Agent-Reach** | 1 | MCP_PROTOCOL_SERVER | Python | 77333 |
| 21 | **Orchestra-Research/AI-Research-SKILLs** | 1 | AGENT_SKILL_COLLECTION | TeX | 12223 |
| 22 | **lsdefine/GenericAgent** | 1 | AGENT_SKILL_COLLECTION | Python | 14098 |
| 23 | **ruvnet/ruflo** | 1 | MCP_PROTOCOL_SERVER | TypeScript | 70120 |
| 24 | **langgenius/dify** | 1 | MCP_PROTOCOL_SERVER | TypeScript | 154112 |
| 25 | **Leonxlnx/taste-skill** | 1 | AGENT_SKILL_COLLECTION | JavaScript | 83236 |

---

## 3. Inspecao de Arvores (Git Trees API - Sem Clones)

Foram inspecionadas as arvores de arquivos dos repositorios mais relevantes de Tier 1:
- **Total de Arvores Inspecionadas**: 2
- **Artefatos Candidatos Descobertos**: **598**
- **Ledger de Artefatos**: [staging/github-inlet/candidate-artifacts.jsonl](file:///E:/.skill-registry/staging/github-inlet/candidate-artifacts.jsonl)

---

## 4. Classificacao Estrita dos Artefatos Descobertos

Os artefatos identificados foram classificados sem auto-promocao:
- SKILL_DEFINITION_CANDIDATE: Arquivos estruturados com instrucoes/frontmatter de skill.
- AGENT_CONFIG_ARTIFACT: Configuracoes de comportamento (.cursorrules, claude.json).
- PROMPT_TEMPLATE_ARTIFACT: Templates de prompts desacoplados de logica executavel.
- CAPABILITY_ARTIFACT: Servidores MCP e modulos de ferramentas prontas para orquestracao.
