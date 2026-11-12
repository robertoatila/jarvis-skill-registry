# Revisão das propostas de `Updates.md` — 2026-11-12

> Atualização: os números e a lista de pendências abaixo descrevem a primeira rodada (`5095866`). A segunda rodada, que implementou nove das dez propostas finais, está em `2026-11-12-second-round-implementation.md`. O fechamento, com os resultados finais e as pendências vigentes, está em `2026-11-12-closure.md`.

## Escopo e limite de evidência

Revisão do snapshot `main@06f369f573b654f41ee8e4693a7b0ba5f80404cb` (1.967 arquivos rastreados), feita em Linux com Python 3.11.2 e Node 22.22.3. Cada proposta de `Updates.md` e de `SECURITY_AUDIT.md` foi conferida contra o código antes de qualquer mudança.

O que este relatório **não** cobre: os gates PowerShell (`tests/Invoke-*Tests.ps1`, `tooling/*.ps1`) não foram executados porque não há PowerShell neste ambiente; nenhum teste de navegador foi executado; nada foi validado em Windows ou macOS. `evidence/current.json` continua sendo a autoridade de release e segue `INCOMPLETE`.

## Resultados medidos neste ambiente

| Verificação | Antes | Depois |
| --- | --- | --- |
| `python jarvis.py --full-test` | 104 suítes, 662 testes, 2 com erro (exit 1) | 107 suítes, 720 testes, 720 aprovados (exit 0) |
| 12 módulos `tests/test_*.py` fora da bateria | 104 OK | 104 OK |
| Testes Node (`node --test` + companion) | 22 aprovados + PASS | 22 aprovados + PASS |
| `python jarvis.py --doctor` / `--test` | PASS | PASS |
| `tooling/audit_documentation_claims.py` | PASS | PASS |
| `tooling/audit_pre_publish_security.py` | PASS | PASS |
| `tooling/validate_repository_contracts.py` | não existia | PASS_WITH_WARNINGS (0 erros, 2 avisos) |

Os dois erros iniciais vinham de `Path.is_junction()`, que só existe a partir do Python 3.12, enquanto `README.md` e `QUICKSTART.md` prometem 3.10+.

## Propostas de `Updates.md`: situação

| Proposta | Situação | Observação |
| --- | --- | --- |
| P0 — sanitização na ingestão autônoma | **Implementada** | Ver "Mudanças". |
| P0 — auditar PII/credenciais | **Conferida, sem achado novo** | Nenhum segredo encontrado. O único e-mail pessoal rastreado é o campo `author` de `package.json`, que é contato público intencional. |
| P0 — tirar `cache/starred_catalog.json` e `audit/events.jsonl` do Git | **Não aplicada; proposta mantida** | O servidor carrega o catálogo na inicialização. Removê-lo exige antes um caminho de download/geração. |
| P0 — tirar `.obsidian/workspace.json` do Git | **Rejeitada** | O arquivo é rastreado de propósito: `tests/test_agentic_validate_isolated.py` o usa como exemplo de arquivo público e `AGENTS.md` manda preservar `.obsidian/`. |
| P1 — mover notas 00–32 para `vault/` | **Bloqueada por política** | `AGENTS.md` proíbe a movimentação em massa; `tests/test_agentic_repository_information_architecture.py` exige as notas na raiz. |
| P1 — `.github/workflows/ci.yml` como gate | **Conflita com a política do repositório** | `evidence/current.json` declara `github_actions_authority: false` e o auditor de documentação proíbe apresentar CI como autoridade. Um workflow só caberia como sinal consultivo. |
| P1 — validar JSON de `adapters/` e frontmatter de `agents/` | **Implementada sem CI** | `tooling/validate_repository_contracts.py`, coberto pela bateria. |
| P2 — schema de adapter | **Já existia; corrigido** | `schemas/adapter.schema.json` não aceitava `CURSOR`, usado por `adapters/cursor/adapter.json`. |
| P2 — `pyproject.toml` + mypy | **Não aplicada; proposta mantida** | Ver "Novas propostas", item 6. |
| P2 — FastAPI / React + Tailwind | **Rejeitada** | Contraria o princípio de launcher sem dependências (`python jarvis.py`, só biblioteca padrão). |

Afirmações de `Updates.md` que não correspondem ao repositório: "não há `tests/`" (há 117 módulos Python, 34 scripts PowerShell e 4 testes Node), "benchmarks são scripts soltos" (há relatórios e testes de contrato), "não há UI estruturada" (`ui/` e `design-system/` existem) e "não há schema de adapter". A afirmação "não há workflows de CI" é verdadeira e é uma decisão documentada.

## Mudanças neste candidato

**Fronteira para texto de terceiros.** `tooling/agentic/untrusted_text.py` reduz nomes, descrições e tópicos vindos do GitHub a uma linha limitada, sem caracteres de controle, invisíveis ou delimitadores de marcação, e sinaliza texto em forma de instrução (heurística EN/PT). A ausência do sinal não prova que o texto é seguro. Medido sobre as 74.653 descrições do catálogo: 3 sinalizadas como instrução, 3.323 com marcação removida, 196 com caracteres invisíveis removidos.

**Ciclo autônomo e conversor (`tooling/jarvis_server.py`, `tooling/repo_to_skill.py`).** Campos do catálogo passam pela fronteira antes de entrar em um `SKILL.md`; descrição suspeita vai para quarentena; a escrita fica confinada a `skills/<nome>`; o espelho fixo em `C:/Users/Ad/.gemini` virou a variável opcional `JARVIS_IDE_SKILLS_DIR`; as chamadas ao Node não usam mais `shell=True`; o fallback `D:\node.exe` foi removido. O conversor não detectava um slug vazio, que gravaria `skills/SKILL.md`, e reportava `overwritten` para toda escrita.

**`POST /api/ingest/promote`.** O nome vinha do corpo da requisição e era concatenado ao caminho: `canonical_name: "../x"` gravava fora de `skills/` (confirmado em diretório temporário antes da correção). Agora: nome de um único segmento, 400 para nome ou manifesto inválido, 413 acima de 256 KiB, 409 quando a skill existe com conteúdo diferente e `overwrite` não é `true`. A resposta deixou de chamar a gravação de homologação de segurança.

**`POST /api/workflow/execute` e `/api/ingest/analyze`.** A rota inventava estrelas, linguagem, pontuação, economia de tokens e `security_status: PASS` para qualquer repositório. Agora devolve apenas o que está no catálogo local; fora dele, os campos vêm `null` e o status é `UNKNOWN`. A pontuação é declarada como heurística de metadados. Um repositório só é associado ao catálogo por `dono/nome` exato; nome sem dono só casa quando é único (3.318 nomes do catálogo são ambíguos).

**`POST /api/pipeline/run`.** Sem o script de auditoria, a rota respondia `PASS`. Agora responde `UNAVAILABLE`.

**Cockpit (`ui/jarvis.js`, `ui/index.html`).** Removida a simulação que exibia uma proposta fabricada quando o servidor falhava. Removidos valores padrão que apareciam como telemetria quando o servidor devolvia `null`: taxa de sucesso `100%`, `40.2x`, `97.51%`, `125 µs`, `26549` repositórios, `392` skills, `2254` repositórios sincronizados, "145 skills". O cache do service worker subiu para `v11` porque `jarvis.js` é servido cache-first.

**Compatibilidade e portabilidade.** Guarda `hasattr` para `is_junction` em `tooling/agentic/composite.py`; `Optional` ausente em `system_test_runner.py`; `omni_recall.py` passou a ler a raiz de `CONFIG` em vez de `E:/.skill-registry`.

**Índice de skills.** `skills/git-bugfix-contribution/SKILL.md` começa com BOM e um aviso em blockquote antes do frontmatter; o cockpit exibia a descrição como ausente. O leitor do servidor agora tolera esse prefixo. O arquivo não foi alterado porque seu hash está fixado em `releases/v1.1.0/lockfiles`.

**Configuração.** `.env.example` listava sete variáveis que nenhum código lê e `QUICKSTART.md` mandava copiá-lo para `.env`, que nenhum código carrega. O exemplo agora documenta só variáveis realmente lidas e diz que `.env` não é carregado automaticamente.

**Benchmark.** `tests/test_agentic_examples.py` regravava o arquivo rastreado `benchmarks/runtime_latency_report.json` a cada `--full-test`, sujando o checkout com tempos da máquina local. O benchmark ganhou `--output` e `--no-write`; o teste grava em diretório temporário.

**Validador de contratos.** `tooling/validate_repository_contracts.py` (biblioteca padrão) verifica adapters contra o schema, 32 pares instância/schema em `schemas/`, parse de 471 arquivos JSON/JSONL rastreados, frontmatter de 11 agentes e 166 skills, sintaxe Python 3.10 em 246 arquivos e wikilinks das notas numeradas. O avaliador de JSON Schema embutido falha explicitamente diante de uma palavra-chave que não implementa; ele concordou com a biblioteca `jsonschema` em 14.600 instâncias mutadas dos schemas do repositório (comparação feita uma vez, fora da bateria).

**Testes novos.** `tests/test_agentic_untrusted_text.py`, `tests/test_agentic_skill_ingestion_routes.py` (HTTP real contra raiz temporária) e `tests/test_agentic_repository_contracts.py`: 58 testes.

**Documentação.** Link quebrado em `docs/roadmap/JARVIS_AUTONOMOUS_INTELLIGENCE_PLAN.md`; exemplo inválido em `docs/ADAPTER_DEVELOPMENT_GUIDE.md` (`CUSTOM_AGENT` não está no enum e faltava `version`); `AGENTS.md` e `CONTRIBUTING.md` citam o novo validador e a regra de texto de terceiros.

## Achados em aberto

1. **Números do `README.md` não batem com este checkout.** O README registra "798 testes / 111 suítes", "394 skills canônicas" e "42.872 repositórios"; o checkout tem 166 `skills/*/SKILL.md`, 74.653 entradas no catálogo e, neste ambiente, 107 suítes / 720 testes. A transcrição do README vem de outra máquina (`E:\.skill-registry`), por isso não foi sobrescrita.
2. **Placeholders estáticos em `ui/index.html`.** A aba de benchmarks ainda traz no HTML `40.2x`, `97.51%`, `125 µs`, "42.872 Repos + 394 Skills" e a linha "[PASS] Compressão 40.2x validada" (linhas 380, 496, 1612–1624, 1692–1693, 1793, 1820). Elas ficam visíveis até a resposta do servidor chegar e permanecem se ela falhar.
3. **`shell=True` restante:** `tooling/agentic/infrastructure.py:96`, `pc_operator.py:333`, `swe_orchestrator.py:332`, `verification.py:197`, `tooling/jarvis_desktop.py:168`.
4. **Caminhos de estação de trabalho fixos:** `omni_recall.py` (banco em `D:/Program Files/jarvis-arsenal`), `build_ultimate_arsenal.py`, `fix_markdown_lint.py`, `harvest_starred_by_keyword.py`, `star_org_profiles.py`, `sync_and_optimize_arsenal.py`, `repo_to_skill.py`, além dos contadores e caminhos `E:/` no docstring de `jarvis_mcp_server.py`.
5. **Junctions no Windows com Python 3.10/3.11.** A guarda `hasattr(path, "is_junction")` evita o erro, mas nessas versões uma junction não é detectada.
6. **Wikilinks:** 9 alvos inexistentes em `02 - Security & Quarantine Ledger.md` (skills removidas).
7. **Arquivos grandes no Git:** `docs/assets/cognitive-vault-graph-animation.mp4` (49,3 MB), `cache/starred_catalog.json` (40,9 MB), `index/conflicts.jsonl` (39,3 MB).
8. **Arquivos soltos na raiz:** dois `Screenshot_20261112_*_Chrome.jpg` e `evidence.txt`.

## Novas propostas

1. **Incluir os 12 módulos `tests/test_*.py` fora do padrão `test_agentic_*` na bateria.** Hoje `--full-test` não executa, entre outros, `test_ui_security`, `test_remote_companion` e `test_memory_privacy_projection` (104 testes).
2. **Derivar os números do README de uma medição.** Estender `tooling/audit_documentation_claims.py` para comparar a contagem de skills e de entradas do catálogo com o checkout, ou remover os números fixos.
3. **Fazer o HTML do cockpit nascer sem números.** Trocar os placeholders do item 2 acima por `n/d` e deixar só o JavaScript preencher.
4. **Trocar `shell=True` por listas de argumentos** nos cinco pontos restantes, começando por `verification.py` e `swe_orchestrator.py`, que executam comandos derivados de planos.
5. **Centralizar caminhos externos em `tooling/agentic/config.py`** (variáveis de ambiente com padrão relativo ao checkout), como já foi feito para `JARVIS_REGISTRY_ROOT`.
6. **`pyproject.toml` só com configuração de lint**, sem dependências de runtime, começando por regras de correção (`E9`, `F63`, `F7`, `F82`) e ampliando aos poucos. Uma varredura com `ruff` encontrou cerca de 700 ocorrências, a maioria imports não usados e `except Exception`.
7. **`.gitattributes`** para fixar finais de linha e marcar `*.mp4`, `*.jpg` e `*.sqlite` como binários; 147 arquivos têm BOM.
8. **Tirar os três arquivos grandes do histórico ativo** por um script de download/geração verificado por hash, mantendo o servidor funcional sem o catálogo.
9. **Detecção de reparse point independente de versão** para Windows com Python anterior a 3.12 (`st_file_attributes`).
10. **Mover o frontmatter de `git-bugfix-contribution` para o início do arquivo** na próxima selagem de release, já que a mudança altera o hash fixado.
