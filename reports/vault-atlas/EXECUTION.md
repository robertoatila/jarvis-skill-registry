---
type: execution
status: completed
tags: [jarvis/vault, jarvis/evidence]
---

# Execução do Cognitive Atlas

Data local: 2026-09-28. Branch: `feat/cognitive-vault-atlas`, alinhada com `origin/main` (`d5f0b6cbc70b2de09679778ab5ad1a7ffbf9727f`). O commit inicial do Atlas (`881a73d`) já consta no histórico remoto de `main`; as extensões desta atualização seguem para revisão na PR #70, separada da PR #53. Nenhum merge de PR ocorreu.

## Inventário e migração

- Inventário inicial do repositório: **5.082 arquivos**. A contagem inclui duplicatas, backups e cópias de distribuição. Scans não seguiram `.git`, caches Python, perfil de navegador nem fixture com junction.
- Antes da primeira escrita no Vault ativo, **45 arquivos** receberam backup físico verificado por SHA-256 e **1.863 notas Markdown existentes** tiveram seu hash registrado no manifesto local de preservação.
- Depois da projeção: **1.860 notas anteriores permaneceram byte a byte idênticas**, três notas existentes (`00`, `03` e `docs/README.md`) mudaram apenas em blocos gerenciados e foram verificadas byte a byte fora deles; zero notas foram apagadas ou desapareceram.
- A página `06 - GitHub Starred Repositories.md` e `cache/starred_catalog.json` permaneceram byte a byte iguais aos hashes do backup. Os nós e links humanos originais do Canvas continuam presentes.
- O cache original desta Vault tem **3.816 registros** de **3.815 identidades GitHub únicas**. As duas versões de `awarexone/agentic-bug-hunter` foram ambas preservadas, com hashes de registro, na mesma nota de referência.
- A geração criou **4.222 notas de navegação locais regeneráveis** sob `JARVIS/Atlas/` (páginas por referência, linguagem, proprietário e coleções), sem copiar o cache inteiro nem os textos importados de skills. O Atlas não atualiza contagem de estrelas nem acessa a rede.
- O Atlas consultou **959 notas Markdown** fora das pastas de backup/distribuição, contando caminhos para conteúdo importado sem lê-lo. Há 168 caminhos de skills ativos no disco. As coleções são construídas pelo prefixo existente ou pela propriedade `type` explicitamente declarada; não há classificação semântica por similaridade.
- Foram registrados **dois vínculos tipados explícitos**, entre este guia, seu plano e o relatório. Pessoas e execuções sem fontes não foram inventadas.

## Graph View real do Obsidian

Obsidian desktop **1.13.7** foi conferido com CLI e renderização real. Antes das mudanças, indexava 2.414 notas e o grafo ativo continha notas, tags, anexos e destinos inexistentes, incluindo 2.832 anexos e 194 destinos inexistentes. A tag `github-starred` aparecia numa única nota, então ela sozinha não explicava o anel de milhares de pontos visto na captura anterior.

Depois da indexação, `app.metadataCache.initialized` era verdadeiro e `inProgressTaskCount` era zero. O Vault indexava **6.644 notas**, com **11.125 conexões** na configuração Universo aplicada; a verificação do índice não encontrou nenhum link sem destino começando em `JARVIS/Atlas/`. O modo Núcleo exibiu **5.050 nós** no teste de filtro. Os dados e referências GitHub seguem acessíveis no Vault e no modo Externo.

Na tela, os grupos do Obsidian ajudam a distinguir hubs, projetos, documentação, evidências, pessoas, memória, skills e referências. O Atlas organiza as referências por linguagem e, para proprietários repetidos, por conta. A captura foi feita pelo CLI do Obsidian com o perfil Universo aplicado e está em `docs/assets/cognitive-vault-graph-universe.png`. É uma captura do renderizador real; as posições mudam quando o layout recalcula. A cor e a posição no grafo não expressam confiança. O tamanho ainda é atribuído pelo Obsidian com base em backlinks reais e no multiplicador global; o plugin nativo não oferece tamanho individual por grupo.

O J.A.R.V.I.S. já tinha as três skills de Obsidian no registry, todas elegíveis como `ACTIVE` e `VERIFIED_ADAPTED`. Esta continuação conecta o roteador de intenção ao catálogo governado para carregar automaticamente `obsidian-cli-controller`, `obsidian-markdown-syntax` e `obsidian-database-bases`; quarentena/tombstones removem a capacidade. `skillctl.ps1 obsidian tools` enumera as skills disponíveis e detecta o executável local (`D:\obsidian\Obsidian.com`). Isso não confirma uma sessão do app nem executa comandos por conta própria.

## Testes e checagens

| Checagem | Resultado |
| --- | --- |
| 14 testes dedicados do Atlas (mais um teste de bloqueio por junction) | **PASS**, todos executados |
| 5 testes de roteamento e disponibilidade das ferramentas Obsidian | **PASS**, incluindo quarentena e skill ausente |
| 14 testes da integração de workspace | **PASS** |
| 6 testes existentes de recibos do Vault | **PASS** |
| Bateria portátil de runtime (execução completa mais recente) | **PARTIAL**; 642/644 passaram; um teste de benchmark e um teste HTTP local excederam o timeout sob carga |
| Repetições isoladas dos dois conjuntos que expiraram | **PASS**; 6/6 testes de exemplos/benchmark e 9/9 testes HTTP do HUD |
| `python jarvis.py --doctor` | **PASS** |
| `python jarvis.py --test` | **PASS** |
| `python benchmarks/context_budget_benchmark.py` | **PASS**; 2.197 bytes serializados de um orçamento de 2.200. Mede bytes UTF-8, não tokens, custo, qualidade ou latência |
| `python tooling/audit_pre_publish_security.py` | **PASS**; 1.836 arquivos elegíveis, 14/14 invariantes e nenhuma violação |
| `git diff --check` | **PASS** |
| Segunda sincronização do Atlas no Vault ativo | **SUCCESS**, `changed_files: []` |
| Resolução de links Atlas pelo Obsidian | **PASS**, nenhum destino inexistente |
| `tooling/skillctl.ps1 obsidian tools` | **PASS**, três skills elegíveis e executável CLI localizado; sessão do app não confirmada |

O teste de publicação alterou `benchmarks/runtime_latency_report.json` com medições incidentais. Esse arquivo foi restaurado e excluído do commit. GitHub Actions não foi criado nem usado como gate. Nada foi mesclado.

## Limites conhecidos e continuação

O inventário abrange caminhos e contagens do repositório; os binários e os milhares de corpos copiados não foram interpretados como conhecimento. As relações tipadas apenas comprovam o que o autor declarou. O título visual de cada nota GitHub é o proprietário/nome normalizado; os dois registros conflitantes continuam identificados como versões do cache, não como estado atual confirmado no GitHub.

A geração de arquivos é segura por nota e passível de repetir, mas o lote inteiro não é uma transação global. Uma interrupção pode deixar uma geração parcial; executar novamente preserva originais e converge. Notas que futuramente saírem do cache ficam no disco como snapshots e exigem revisão humana antes de descarte.
