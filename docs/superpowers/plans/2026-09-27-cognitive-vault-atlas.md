---
type: plan
tags: [jarvis/vault]
jarvis_relations: [{"type": "supported_by", "target": "reports/vault-atlas/EXECUTION.md"}]
---

# Plano mestre — Cognitive Vault e Atlas semântico

Data: 2026-09-27. Escopo: navegação humana, projeções locais e Graph View. Base: `origin/main` em `e08b8d7587f8df69f7ac54e9e4911f4d9c865bf6`; branch exclusiva `feat/cognitive-vault-atlas`. A PR #53 e seu protocolo remoto permanecem separados. Não recriar Actions, não alterar versões, não fazer merge nesta tarefa.

## Diagnóstico e fontes de verdade

O Vault ativo confirmado no registro do Obsidian é o checkout de trabalho existente. A inspeção inventariou todos os diretórios, exceto metadados Git, caches Python, sessões de navegador e um junction de fixture que não deve ser seguido: 5.082 arquivos, incluindo cópias e backups. A leitura aprofundada cobriu documentação canônica, configurações `.obsidian`, MOCs, cache de favoritos, índice de recursos, bridge, projector, recibos, watcher e testes.

O Obsidian 1.13.7 informou 2.414 notas indexadas e o grafo inicial desenhava 5.745 nós: 2.416 nós de arquivo sem tipo especial, 303 tags, 2.832 anexos e 194 destinos inexistentes. Uma única nota tinha a tag `github-starred`. Portanto, o anel visual não pode ser atribuído diretamente a milhares de notas com essa tag. O cache local tinha 3.816 registros, correspondentes a 3.815 identidades GitHub únicas; o cache da base da PR tinha 3.708 registros e 3.707 identidades. Essas medidas pertencem a fontes distintas.

O checkout ativo tinha alterações prévias no workspace Obsidian, no MOC 06 e no cache. O desenvolvimento ocorre em worktree isolado da main para não incorporá-las à PR do Atlas nem à PR remota.

## Fases e critérios de aceitação

| Fase | Trabalho e dependências | Critério de sucesso |
| --- | --- | --- |
| 0 — inventário | Mapear repositório completo por área; ler contratos e superfícies do Vault | Vault ativo confirmado, estado Git registrado, escopos e ausências explícitos |
| 1 — preservação | Backup das superfícies afetadas; hash de fontes e notas preexistentes | Backup recuperável; nenhuma alteração prévia perdida |
| 2 — arquitetura | Preservar hubs 00–23; adicionar 24–32; subíndices paginados e mapa de propriedade | Navegação central alcança todos os hubs; zero links gerados sem destino |
| 3 — Atlas externo | Projetar identidades do cache; linguagens e proprietários explícitos | Toda identidade representada, duplicatas preservadas, zero classificação por palavra-chave |
| 4 — relações | Contrato de frontmatter, tags e relações tipadas; links nativos e backlinks | Destinos validados; erro interrompe antes da escrita; nenhuma pessoa/execução inventada |
| 5 — visual | Universo/Núcleo/Externo; cores, forças, tamanhos globais e filtros | Perfis aplicados e inspecionados no Obsidian real; conteúdo permanece acessível |
| 6 — execução incremental | Prévia; aplicação isolada; aplicação no Vault ativo; segunda execução | Idempotência; preservação de bytes fora dos blocos; ausência de exclusões |
| 7 — validação/publicação | Testes específicos, bateria portátil, doctor, self-test, benchmark e auditor de publicação | Resultados exatos registrados; commits/PR separados, sem merge |
| 8 — curadoria contínua | Autorias de pessoas/projetos e relações com evidência explícita | Ampliação por fontes reais; obsolescência revisada sem exclusão automática |

## Propriedade e operação

O usuário mantém textos humanos, organização manual e Canvas. `CognitiveVaultBridge.sync_registry` mantém a projeção canônica. `VaultAtlas` é somente o renderizador de coleções dessa bridge. `ManagedVaultProjector` mantém backups/escritas e recibos; `VaultWatcher` continua reconhecendo apenas hashes exatos. O runtime de planejamento, admissão de memória e execução não muda de autoridade.

Não reclassificar documentos históricos como comprovação atual. Não esconder ausência de pessoas/execuções com dados demonstrativos. Pessoas e resultados só entram por notas explícitas; o contrato já permite sua conexão quando existirem.

## Validação incremental e recuperação

1. Fixtures: preservar CRLF humano, não interpretar Markdown injetado de fonte externa, paginar sem cortar registros, rejeitar caminhos fora do Vault, duplicação de marcadores, fontes/destinos alterados, cache inválido e relações sem destino.
2. Recibos: consumir uma vez, exigir hash exato, compatibilidade entre formato agregado existente e individual do Atlas.
3. Worktree: gerar pelo comando canônico; repetir e comparar mudanças.
4. Vault ativo: backup verificado, gerar com os dados locais atuais, conferir hashes de todos os originais, aplicar somente opções do grafo autorizadas.
5. Obsidian: conferir índices reais, resolução de links gerados, contagens, perfis e capturas do grafo. Registrar as diferenças entre contagem de arquivos no disco, índice e grafo visível.
6. Publicação: anexar resultados diretos à PR; não usar GitHub Actions como gate e não fazer merge.

Em falha de pré-validação: nenhuma escrita do Atlas começa. Em falha após início de múltiplas escritas: conservar backups e recibos concluídos, registrar resultado parcial e repetir com fontes estáveis. Não anunciar atomicidade global. O procedimento de recuperação está em [Cognitive Atlas](../../vault/COGNITIVE_ATLAS.md).

## Estado da execução

O estado final, métricas locais, verificações, limites e referência da PR serão registrados em [relatório de execução](../../../reports/vault-atlas/EXECUTION.md). Esse relatório complementa este plano; não substitui a evidência de release em `evidence/current.json`.
