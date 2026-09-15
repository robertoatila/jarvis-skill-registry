# Interface consolidada do Jarvis

Esta versão substitui a central paralela introduzida em `157063e`. A interface principal e o planejador existente voltam a ser os pontos de entrada.

## Missões e contexto

Na interface principal, use o campo de objetivo do lançador de missões e **Planejar DAG**. O planejamento continua usando `AutonomousMissionPlanner` e `AutonomousSkillResolver`. A resposta inclui o contexto formatado a partir da mesma missão, com seu identificador, objetivo, tarefas, agentes e skills propostas. Não há uma segunda seleção por palavras.

Em **Compartilhar o plano desta missão**, revise o texto e copie para outro aplicativo. Alterar o objetivo invalida o texto preparado. O grafo do planejamento usa a resposta da mesma missão; tarefas propostas não recebem o selo VERIFIED.

As capacidades continuam vindo dos controles existentes do lançador. Isso não implementa inferência livre de todas as capacidades a partir do texto do objetivo. Um plano também não comprova disponibilidade de todas as skills propostas nem execução autorizada.

## Aplicativos

A aba existente **Cofre Obsidian** contém as informações de conexão. O único endpoint de inventário adicional é `GET /api/workspace`. O endpoint paralelo de preparação e o servidor da porta 8900 foram removidos.

Comando no PATH, adaptador de formato e sessão autenticada são evidências diferentes. Não há conexão automática com sessões do Codex, ChatGPT ou Antigravity. O compartilhamento do plano continua manual.

## Obsidian

O botão existente e `tooling/Sync-ObsidianVault.ps1` delegam à mesma implementação: `CognitiveVaultBridge.sync_registry`.

```powershell
python -m tooling.agentic.workspace_hub --root E:/.skill-registry --sync-obsidian
```

São atualizados os MOCs existentes 00 a 05 e `JARVIS-Brain-Map.canvas`. O índice fornece apenas metadados; corpos de skills e memória privada não são necessários para essa projeção. Rótulos legados do índice são descritos como metadados, sem certificação atual.

O Markdown usa um bloco gerenciado, preservando texto externo. O Canvas preserva os nós, arestas e campos humanos; atualiza apenas os elementos com prefixo reservado `jarvis:projection:`. O resumo gerenciado complementa o grafo existente sem reconstruí-lo em paralelo. Há backup dos bytes originais, hash verificado e verificação de alteração concorrente por arquivo. A sincronização de vários arquivos não é uma transação única: falhas podem ocorrer depois de outros arquivos terem sido atualizados.

A nota 20 foi mantida como referência para a navegação existente, evitando quebrar links ou apagar anotações humanas. Os dois caminhos de projeção da memória pessoal também usam o mesmo escritor que preserva notas. O conteúdo histórico fora dos blocos continua preservado e não equivale a uma verificação atual.

## Evidências e limites

Consulte `reports/consolidation/20260914/REVIEW.md`. A suíte usa uma cópia isolada e estado privado vazio. Não houve inspeção visual em navegador nem ativação de sessões externas. Autonomia completa e controle direto dos aplicativos continuam pendentes.
