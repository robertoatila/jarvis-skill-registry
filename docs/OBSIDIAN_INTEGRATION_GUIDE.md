# Obsidian no J.A.R.V.I.S.

Este guia descreve o que o repositório oferece hoje para Obsidian e distingue navegação, skills e plugins. As notas e visualizações ajudam a explorar o Vault; a execução e as permissões continuam sob as regras do runtime J.A.R.V.I.S.

## Comece pelos mapas

- [[00 - J.A.R.V.I.S. Cognitive Vault|00 · Painel mestre]]: navegação do Vault.
- [[01 - Arsenal Map of Content|01 · Skills e capacidades]]: catálogo de skills.
- [[06 - GitHub Starred Repositories|06 · Repositórios externos]]: conhecimento importado do GitHub.
- [[17 - Protocolo de Seguranca Soberana v13|17 · Índice do protocolo]]: entrada para a fonte canônica indicada no Vault.
- [[19 - Memoria Persistente e Conhecimento Episodico|19 · Memória persistente]]: projeção de memória e conhecimento episódico.
- [[29 - Conhecimento Externo|29 · Conhecimento externo]]: referências importadas.
- [[31 - Agentes e Ferramentas|31 · Agentes e ferramentas]]: navegação para capacidades do runtime.

Para a arquitetura da projeção, dos perfis de grafo e de suas fontes, consulte o [Cognitive Atlas](vault/COGNITIVE_ATLAS.md).

## Graph View

A configuração global fica em .obsidian/graph.json. Ela mostra tags, anexos, links não resolvidos e órfãos, e usa grupos coloridos para destacar hubs, skills, documentação, evidências, idiomas e áreas operacionais. As forças, o tamanho dos nós e as setas mudam a apresentação; não criam wikilinks.

O grafo pode mostrar relações por links explícitos e por tags compartilhadas. Uma cor ou uma aresta de tag é um recurso de navegação, não prova de relação semântica. Para explorar o Vault inteiro, mantenha o conteúdo indexado; use os filtros do painel para reduzir temporariamente o que aparece. Com anexos, órfãos e notas não resolvidas visíveis, o grafo pode exigir mais recursos em Vaults grandes.

![Pôster da animação do Graph View do Cognitive Vault](assets/cognitive-vault-graph-animation-poster.png)

[Assistir à animação gravada no Obsidian](assets/cognitive-vault-graph-animation.mp4)

## Skills de Obsidian no J.A.R.V.I.S.

O dispatcher de Obsidian carrega somente as três skills abaixo quando elas estão ativas, verificadas e presentes no registry:

- [[skills/obsidian-cli-controller/SKILL.md|obsidian-cli-controller]]: opera pela CLI oficial do Obsidian; requer a CLI instalada e o Obsidian aberto.
- [[skills/obsidian-markdown-syntax/SKILL.md|obsidian-markdown-syntax]]: escreve Markdown compatível com wikilinks, callouts, propriedades e embeds.
- [[skills/obsidian-database-bases/SKILL.md|obsidian-database-bases]]: cria e valida arquivos .base.

O catálogo também contém [[skills/json-canvas-visualizer/SKILL.md|json-canvas-visualizer]], mas essa skill ainda não faz parte do dispatcher específico de Obsidian. Encontrar o executável ou uma skill não confirma que uma sessão do Obsidian esteja aberta. Essas skills não adicionam uma interface de chat ou voz ao Obsidian.

## Plugin opcional Claudian

O instalador opcional busca a última release estável do [repositório oficial Claudian](https://github.com/YishenTu/claudian), valida os digests SHA-256 publicados pelo GitHub e o ID do manifesto (realclaudian), e instala somente main.js, manifest.json e styles.css quando disponível:

    python tooling/install_obsidian_plugins.py

Use --vault <caminho> quando o Vault estiver fora da raiz deste repositório. O instalador preserva os dados existentes do plugin e os demais IDs em community-plugins.json; não altera app.json nem desativa o modo de segurança. Se o modo de segurança estiver ativo, habilite plugins comunitários pelas configurações do Obsidian e recarregue o plugin manualmente.

Claudian é um plugin comunitário que incorpora agentes de programação ao Vault. Ele pode ler e alterar arquivos e executar comandos; instale-o somente se confiar no projeto e na release. Ele não fornece voz ao runtime J.A.R.V.I.S. O instalador não copia automaticamente dados de uma antiga pasta com ID diferente.

## Verificações

Para conferir localmente o roteamento dos skills e o instalador:

    python -m unittest tests.test_agentic_obsidian_tooling tests.test_install_obsidian_plugins -v
    python jarvis.py --doctor
