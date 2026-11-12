# Segunda rodada: implementação das propostas — 2026-11-12

## Escopo e limite de evidência

Continuação de `2026-11-12-updates-proposal-review.md`. Aquela revisão terminou com dez propostas próprias; esta rodada implementa nove delas sobre `main@06f369f573b654f41ee8e4693a7b0ba5f80404cb`, na branch `arena/82188603-jarvis-skill-registry`.

Tudo foi medido em Linux, Python 3.11.2 e Node 22.22.3. **Não** foi executado: nenhum gate PowerShell (`tests/Invoke-*Tests.ps1`, `tooling/*.ps1`), nenhum navegador real, nada em Windows ou macOS. Os caminhos de código exclusivos de Windows foram exercitados apenas por testes que substituem a plataforma. `evidence/current.json` continua sendo a autoridade de release e segue `INCOMPLETE`; nada aqui altera esse estado.

## Resultados medidos

| Verificação | Base (`06f369f`) | Primeira rodada | Agora |
| --- | --- | --- | --- |
| `python jarvis.py --full-test` | 104 suítes, 662 testes, 2 com erro | 107 suítes, 720/720 | 126 suítes, 893/893 |
| Mesma bateria sem os três arquivos grandes em disco | não medido | não medido | 126 suítes, 893/893 |
| Testes Node (`.cjs`) | — | — | 25/25 |
| `python jarvis.py --doctor` / `--test` | — | saída 0 | saída 0 |
| `tooling/validate_repository_contracts.py --summary` | inexistente | `PASS_WITH_WARNINGS` | `PASS_WITH_WARNINGS` (2 avisos conhecidos) |
| `tooling/audit_documentation_claims.py` | — | `PASS` | `PASS`, 166 skills medidas |
| `ruff check .` (opcional, regras de `pyproject.toml`) | sem configuração | sem configuração | sem achados |

Os dois avisos do validador são anteriores a este trabalho: o frontmatter de `skills/git-bugfix-contribution/SKILL.md` (proposta 10) e nove wikilinks sem destino em `02 - Security & Quarantine Ledger.md`.

## O que foi feito, por proposta

| # | Proposta | Commit | Resultado |
| --- | --- | --- | --- |
| 1 | Bateria cobre todo `tests/test_*.py` | `ec439b4` | 12 módulos que nunca rodavam passaram a rodar |
| 2 | Números do README vêm de medição | `ec439b4` | contagem de skills medida pelo auditor; contagens fixas de testes removidas |
| 3 | Cockpit não embarca números | `ec439b4` | HTML só com marcadores; valores aparecem quando medidos |
| 4 | Sem `shell=True` no runtime | `df5e02d` | `tooling/agentic/safe_command.py`; operadores de shell são recusados |
| 5 | Caminhos externos centralizados | `1b7ef44` | nenhuma letra de unidade em `tooling/` fora de `config.py` |
| 6 | `pyproject.toml` só de ferramentas | `096e6c0` | regras de ruff restritas, sem metadados de pacote |
| 7 | `.gitattributes` estreito | `b76fec8` | binários declarados; fim de linha fixado só onde há checksum |
| 8 | Arquivos grandes | `10ecbf3` | inventário, verificação e restauração fail-closed; nada removido do Git |
| 9 | Junções em Python < 3.12 | `08e87de` | detecção pela reparse tag, igual em 3.10+ |
| 10 | Frontmatter de `git-bugfix-contribution` | — | permanece proposta (ver abaixo) |

### Proposta 3: dado pessoal encontrado

`ui/index.html` trazia fixo um hostname pessoal de tailnet (`desktop-…​.ts.net/remote/?remote=1`). Foi removido do arquivo, mas **continua no histórico Git** (`06f369f` e `5095866`). Remover do histórico exige reescrevê-lo; a alternativa mais simples é renomear o dispositivo ou a tailnet.

### Proposta 4: mudança de comportamento

`infrastructure.run_command` não aceita mais sintaxe de shell. Um comando com `&&`, `|`, `;`, redirecionamento ou substituição retorna `BLOCKED_DISALLOWED` (saída 126) em vez de ser executado. Expansão de variável, til e glob não é feita. Os dois chamadores em `tooling/agentic/runtime_core.py` repassam o comando da tarefa sem transformação; nenhuma tarefa exercitada pela bateria depende de sintaxe de shell, mas um plano externo que dependesse passará a ser bloqueado. O separador de argumentos foi comparado com `/bin/sh` em 5.314 casos e com as regras de `CommandLineToArgvW` em 200.000 casos gerados, sem divergência; a parte Windows não foi comparada com um Windows real.

Exceção mantida: `tooling/validate_v020_plan4.py` usa `shell=` para `.cmd`/`.bat` no Windows, sobre uma matriz interna fixa.

### Proposta 5: verificação

Os cinco scripts avulsos (`build_ultimate_arsenal`, `fix_markdown_lint`, `harvest_starred_by_keyword`, `star_org_profiles`, `sync_and_optimize_arsenal`) foram importados neste ambiente sem efeito colateral e sem criar diretório; não foram executados, porque gravam fora do checkout ou chamam a API do GitHub.

### Proposta 7: checksums de release

Num checkout com fim de linha LF, antes e depois:

| Release | Antes | Depois |
| --- | --- | --- |
| v1.1.0 | 0 de 7 | 7 de 7 |
| v1.0.0 | 2 de 21 | 14 de 21 |
| v2.0.0 | 1 de 2 | 1 de 2 |

O que atributos não resolvem: seis arquivos de v1.0.0 cujo conteúdo mudou desde o selo (`state/canonical-merkle.json`, `index/resources.jsonl`, `structural-analyses.jsonl`, `capability-profiles.jsonl`, `compatibility.jsonl`, `security-reports.jsonl`); `index/capabilities.jsonl`, que só bateria com CRLF e foi deixado sem fixação por ser um índice vivo; e `releases/v2.0.0/RELEASE_NOTES.md`. Não há regra global `* text=auto`, para não renormalizar os 1.970 arquivos.

### Proposta 8: decisão e limite

Os três arquivos (`cache/starred_catalog.json`, `index/conflicts.jsonl`, `docs/assets/cognitive-vault-graph-animation.mp4`; 124 MiB somados) **continuam rastreados**. Tirá-los do Git só faz sentido depois que existir um local publicado de onde restaurá-los, e reduzir o tamanho do clone exigiria reescrever o histórico. Nenhuma das duas coisas foi feita.

O que existe agora:

- `config/large-artifacts.json` registra caminho, tipo (`live` ou `static`), tamanho, SHA-256 e finalidade.
- `python tooling/large_artifacts.py status | verify | record | fetch`. Arquivo ausente é aceitável; cache `live` alterado é informado como "reescrito desde o registro"; só artefato `static` alterado é falha.
- `fetch` não tem origem padrão. Aceita apenas `https://` (ou `http://` de loopback), baixa para arquivo temporário e instala somente se tamanho e SHA-256 conferirem. Foi exercitado apenas contra um servidor de teste local; não existe origem real.
- O servidor responde `catalog_available: false` quando não há banco nem catálogo, e a tela do arsenal diz que o catálogo está ausente em vez de mostrar zero.

### Proposta 9

`Path.is_junction()` existe só a partir do Python 3.12. A guarda `hasattr` evitava a exceção, mas em Windows com Python 3.10 ou 3.11 pulava a checagem, e uma junção de diretório passava pelas regras de "sem caminhos ligados". `tooling/agentic/path_links.py` lê a reparse tag, como a biblioteca padrão faz no 3.12, e substitui a guarda em nove pontos de sete módulos. Validado com `os.lstat` substituído; não com uma junção real.

### Proposta 10: por que não foi aplicada

O SHA-256 de `skills/git-bugfix-contribution/SKILL.md` está fixado em `releases/v1.1.0/lockfiles/*.lock.json` e em `state/canonical-merkle.json`. Corrigir o frontmatter agora quebraria esses registros. A correção deve entrar junto com o próximo selo de release.

## Pendências conhecidas

- `tooling/jarvis_desktop.py` mostra "144 ATIVAS" e "2.168 INDEXADOS" fixos no painel tkinter.
- `ui/index.html` ainda tem rótulos `D:\`, o rodapé "Patamar 100% Soberano & Operacional", o selo "42 REPOSITORIES" e "Hoje às 20:00:00".
- Caminhos de unidade restam como texto em docstrings e prompts (`tooling/build_ultimate_arsenal.py`, `tooling/sync_and_optimize_arsenal.py`), no caminho padrão do Chrome em `tooling/agentic/pc_operator.py`, em `tests/nichos.md` e em `tooling/Invoke-ReleaseV11ForensicAudit.ps1`.
- "Pure Python 3.12" permanece em documentos não governados (`examples/`, `benchmarks/*.py`, `docs/CLI_REFERENCE.md`, `docs/SPECIFICATION.md`, `releases/v2.0.0/RELEASE_NOTES.md`).
- README mantém `42,872` com a nota "Measurement Boundary".
- Fora das regras habilitadas, o ruff ainda aponta 294 imports não usados, 130 nomes vindos de `import *`, 22 f-strings sem campo e 22 variáveis não usadas.
- 147 arquivos têm BOM; 3.318 nomes de repositório ambíguos no catálogo; duas capturas de tela e `evidence.txt` soltos na raiz.
