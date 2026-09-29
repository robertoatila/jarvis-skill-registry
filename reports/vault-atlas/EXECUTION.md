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

Na continuação, o CLI confirmou uma reindexação concluída de **7.103 notas** e **12.186 conexões**, com zero tarefas pendentes e zero destinos Atlas sem resolução. A captura versionada acima permanece a imagem colorida obtida pelo renderizador real na verificação anterior (6.644 notas). Uma nova captura após a reindexação perdeu as cores de grupo no render, então não substituí a imagem estável por essa saída degradada.

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

## Reforço da teia e ajuste visual

Na captura enviada pelo usuário, a vista ampla mostrava um halo de notas sem links e um núcleo pequeno. A consulta ao índice do Obsidian encontrou **7.103 notas, 12.186 conexões e 1.569 notas sem grau** (22,1%). Para ligar a massa sem fingir relações semânticas, a configuração agora habilita mapas por caminho: **2.432 notas físicas** aparecem em **541 grupos de pasta** e **542 páginas de navegação**, além das páginas paginadas em coleções. Cada link significa somente que o arquivo pertence àquela pasta ou a uma subpasta. O gerador lê apenas nomes/caminhos para essa etapa, não segue caminhos vinculados, não lê nem reescreve os corpos de origem, e nunca apaga conteúdo.

A aplicação explícita ao Vault ativo terminou com **SUCCESS**, `navigation_notes: 2432`, `navigation_groups: 541`, `navigation_pages: 542`, **4.517 projeções alteradas** e zero exclusões. A aplicação também mesclou o perfil Universo no `.obsidian/graph.json` ativo por escrita verificada com backup, preservando campos desconhecidos. O perfil agora traz 23 grupos de cor, escala `0.01171875`, distância de link `105`, força `0.82`, multiplicador visual de nós `1.25` e linhas `0.5`; órfãos continuam ativados porque receberam a ligação estrutural.

As 16 verificações do Atlas passaram, incluindo preservação dos arquivos de origem e aplicação do perfil de outra checkout ao Vault. Depois da geração em lote, o Obsidian deixou de responder às chamadas CLI `eval` e `dev:screenshot`; foram canceladas após expirarem. Por isso, o novo número de notas/arestas já reindexadas e a aparência final renderizada não puderam ser confirmados nesta execução. A configuração do grafo e os mapas estão salvos no Vault; a conferência visual final ainda depende do CLI voltar a responder ou de reabrir a vista do grafo no Obsidian.

## Limites conhecidos e continuação

O inventário abrange caminhos e contagens do repositório; os binários e os milhares de corpos copiados não foram interpretados como conhecimento. As relações tipadas apenas comprovam o que o autor declarou. O título visual de cada nota GitHub é o proprietário/nome normalizado; os dois registros conflitantes continuam identificados como versões do cache, não como estado atual confirmado no GitHub.

A geração de arquivos é segura por nota e passível de repetir, mas o lote inteiro não é uma transação global. Uma interrupção pode deixar uma geração parcial; executar novamente preserva originais e converge. Notas que futuramente saírem do cache ficam no disco como snapshots e exigem revisão humana antes de descarte.

## Atualização visual e estado vivo — 2026-09-29

A captura colorida versionada foi obtida do Graph View real com os 23 grupos de cor aplicados e é a referência visual do perfil Universo; o arquivo enviado pelo usuário foi preservado como `cognitive-vault-graph-before-weave.png` para comparação. Após a atualização do índice e dos mapas, a sessão ativa confirmou **8.309 notas Markdown, 22.574 conexões resolvidas, zero tarefas pendentes e 563 páginas de navegação**. Esses números são uma leitura ao vivo do Vault `E:\.skill-registry`, não uma contagem do repositório nem promessa sobre o que cada máquina indexará.

O CLI voltou a responder. A nova captura ao vivo, feita enquanto o plugin Smart Connections ainda exibia progresso de embeddings, deixou as cores quase cinza; por isso, não foi promovida sobre a captura colorida estável. A paleta e os 23 filtros permanecem ativos na configuração, e grupos de cor são apresentados no renderizador como agrupamentos, não como confiança. Os mapas de caminho aumentam a conectividade estrutural sem declarar relações de assunto. A indexação atual já mostra 22.574 arestas — acima das 12.186 registradas anteriormente —, mas a configuração deve continuar sendo julgada com o grafo assentado e a sessão local, pois o layout físico é recalculado pelo Obsidian.

A navegação mais recente tem 563 páginas e os links dessas páginas foram verificados no índice do Obsidian sem destinos pendentes. Conteúdo `github-starred`, staging, backups, arquivos e demais áreas permanece no Vault; exclusões visuais existentes continuam sendo filtros da sessão do usuário, não remoções de conteúdo.

## Vídeo da animação nativa — 2026-09-29

O botão nativo **Animar** no painel de Filtros foi acionado no Graph View real. A gravação começa com o canvas vazio por 10 quadros (0 nós); após restaurar os filtros originais e clicar no botão nativo, o renderer começou com 394 nós e cresceu até **23.897 nós**, contagem mantida por 60 quadros de confirmação. Foram capturados 963 quadros, codificados a 2 fps em `docs/assets/cognitive-vault-graph-animation.mp4` (8 min 1,5 s; H.264, 1280×776). Os quadros 0 e 9 são inteiramente pretos/vazios; o quadro 10 já contém 988 pixels não pretos e a quantidade de pixels visíveis cresce nos pontos verificados até 202.937 no quadro final. Isso confirma a sequência vazia → animação nativa → grafo completo. O movimento e a montagem foram produzidos pelo Obsidian; apenas a captura dos quadros do canvas e a codificação MP4 foram externas. O quadro final acompanha o vídeo como pôster.
