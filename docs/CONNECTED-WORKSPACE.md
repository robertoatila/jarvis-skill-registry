# Workspace conectado

A central prepara contexto compartilhável para Obsidian, Antigravity, Codex e ChatGPT. Ela consulta metadados locais e não inicia modelos, sessões de aplicativos ou instalação de skills.

## Abrir a interface leve

Na raiz do repositório:

```powershell
python -m tooling.workspace_server --root E:/.skill-registry --port 8900
```

Abra `http://127.0.0.1:8900`. Esse serviço inicia apenas a central de conexões e preparação de contexto, sem os trabalhadores autônomos do servidor legado. Escuta somente loopback, rejeita origens externas e serve uma lista fixa de arquivos. O painel também aparece na interface principal do Jarvis.

Informe um objetivo e escolha **Preparar contexto compartilhado**. Revise o texto e copie para uma tarefa no aplicativo de destino. O texto contém a raiz do projeto, o objetivo e as skills candidatas. A entrega entre aplicativos é manual; não há confirmação automática de recebimento, execução ou conclusão.

## Seleção e limites de autonomia

- Seleção determinística por correspondência de termos no identificador, descrição e capacidades.
- Até cinco candidatas e aproximadamente 700 tokens de metadados por preparação; essa estimativa não mede uso de um modelo.
- Usa apenas `index/resources.jsonl`. Não lê corpos de skills nem memória pessoal para preparar contexto.
- Considera registros `ACTIVE` com `TRUSTED` ou o rótulo legado `VERIFIED_ADAPTED`. O segundo rótulo existe no índice real, mas diverge do enum do schema atual: sua compatibilidade aqui vale somente para sugestões, não certifica nem autoriza execução.
- Exclui candidatos não promovidos, dispensas de revisão e entradas em quarentena. Tombstones prevalecem sobre registros ativos duplicados.
- O executor existente suporta ações locais explícitas de leitura e escrita, com escopos e verificação. Planejamento livre por modelo, instalação autônoma e controle direto das sessões dos aplicativos continuam pendentes.

Comando encontrado no PATH e adaptador de formato presente são evidências distintas de sessão conectada. O painel não declara conexão operacional com base apenas nessas evidências. ChatGPT Desktop não tem detecção de sessão implementada. Nenhuma credencial é consultada pelo hub.

## Obsidian

```powershell
python -m tooling.agentic.workspace_hub --root E:/.skill-registry --sync-obsidian
```

Atualiza `20 - Central de Integracoes Jarvis.md` com navegação para memória, roadmap, documentação e skills elegíveis. O botão de sincronização na interface principal usa essa mesma projeção; ele não regenera os MOCs e o Canvas históricos. O antigo script `Sync-ObsidianVault.ps1` continua como ferramenta legada, fora desse fluxo, e não recebeu a mesma revisão.

`CognitiveVaultBridge.sync_to_obsidian()` passa a atualizar somente um bloco delimitado na nota de memória. Na primeira sincronização, conteúdo antigo é preservado e o bloco é acrescentado. Alterações fora dele são preservadas; alterações dentro dele serão substituídas na próxima projeção.

Antes de alterar uma nota existente, o projetor preserva os bytes originais em `backups/vault-projection/*.bak` e verifica seu hash. Atualizações idênticas não geram nova escrita nem backup. Marcadores incompletos ou ambíguos interrompem a operação. Arquivos ligados por symlink/junction são rejeitados. A verificação de alteração concorrente reduz sobrescritas acidentais, mas não é uma transação contra um escritor externo hostil.

O Obsidian permanece uma projeção. Editar uma nota não altera a autoridade de execução do runtime.

## Verificação desta entrega

Os resultados estão em `reports/connected-workspace/20260914/`. A suíte geral usa uma cópia isolada, catálogo sintético e estado privado vazio. O índice real foi consultado somente como metadados; a nota central foi fisicamente criada. Não há certificação de implantação, teste visual em navegador ou conexão autenticada com os aplicativos de destino.
