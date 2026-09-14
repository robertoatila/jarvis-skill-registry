# Consolidação dos fluxos existentes

Base: `157063ef7468352eb2ae038e16aca8d0615c5865`, branch `main`.

A revisão anterior introduziu um segundo servidor, um seletor de skills por palavras e um segundo objetivo de interface. Esta alteração remove esses caminhos paralelos.

## Resultado

- `tooling/workspace_server.py` removido; o processo local da porta 8900 criado na revisão anterior foi encerrado.
- `WorkspaceHub.prepare()` e `/api/workspace/prepare` removidos. O hub remanescente consulta somente metadados para inventário e projeção.
- O lançador existente produz o plano e seu contexto compartilhável através de `AutonomousMissionPlanner.format_handoff`. O formatador não seleciona skills novamente nem executa ações.
- A interface usa o objetivo existente. Alterações invalidam o texto preparado. O grafo após planejamento usa a mesma resposta da missão, com tarefas marcadas como propostas.
- As informações de conexão foram incorporadas à aba existente do Obsidian.
- Botão, script PowerShell e entrada Python usam `CognitiveVaultBridge.sync_registry`. São atualizados os seis MOCs existentes e o Canvas. A nota 20 foi reduzida a uma referência para a navegação existente, preservando conteúdo humano externo ao bloco.
- O outro escritor de memória, presente no servidor principal, também passou a usar `update_projection`, mantendo a mesma proteção de conteúdo humano.

## Verificação

- `full-suite.json` e `full-suite.txt`: **274 testes passaram**, execução isolada com catálogo sintético, estado privado vazio e rede externa bloqueada.
- `targeted.json` e `targeted.txt`: 13 testes específicos passaram, incluindo compartilhamento sem nova resolução, preservação e idempotência do Canvas, quarentena e ausência do segundo campo/endpoint.
- Após o ajuste final para não recriar a lista de skills em um MOC que já possui o mapa, `completion.json` e `completion.txt` registram 14 testes específicos aprovados. A suíte geral de 274 testes antecede esse ajuste; o novo caso verifica explicitamente que o link existente aparece apenas uma vez.
- Sintaxe dos dois JavaScript verificada com Node; script PowerShell validado pelo parser.
- A execução direta do script PowerShell foi bloqueada pela política de execução local. A sincronização real foi concluída pela entrada Python equivalente, sem mudar a política do Windows.
- `preservation.json`: 22 arquivos do backup inicial reverificados; conteúdo original dos seis MOCs preservado; todos os nós e arestas originais do Canvas preservados.
- Backup físico: `backups/consolidation-20260914-142342/manifest.json`. As escritas nas notas também produziram backups individuais verificados.

## Limites

Esta alteração consolida as duplicações introduzidas na revisão anterior; não certifica ausência de toda redundância no restante do projeto. A interface principal conserva componentes legados ainda sujeitos a revisão.

Não houve inspeção visual em navegador, ativação de sessões externas ou execução autônoma de um objetivo. O plano usa as capacidades fornecidas pelo lançador existente; compartilhar seu texto não comprova disponibilidade ou autorização de execução de cada skill proposta. A entrega aos aplicativos continua manual.

A projeção conserva conteúdo histórico externo aos blocos; esse conteúdo não equivale a uma nova certificação. O resumo gerenciado do Canvas usa um prefixo reservado e mantém o grafo humano. Cada escrita é protegida individualmente; a sincronização de vários arquivos não é uma transação única.
