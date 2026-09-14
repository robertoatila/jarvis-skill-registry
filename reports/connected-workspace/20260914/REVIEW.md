# Revisão: workspace conectado, Obsidian e seleção de skills

Base: `dda1098172b231d63590f579b9320bf9252ae046`, branch `main`.

## Alterações

- Central de conexões com carregamento, erro, atualização manual e preparação de contexto compartilhável.
- Serviço leve independente dos trabalhadores do servidor legado, limitado a loopback e recursos explícitos.
- Sugestão de skills por metadados, com quantidade e orçamento limitados, sem instalação, invocação de modelos ou leitura de memória privada.
- Projeção do Obsidian com preservação de notas humanas, backup físico verificado, escrita temporária e detecção de mudanças concorrentes.
- Tombstones de quarentena prevalecem sobre catálogo e exame de diretórios; alteração do índice invalida caches de manifestos e execução. Índice inválido interrompe disclosure e não reutiliza catálogo antigo.
- Remoção de números de exemplo na inicialização dos indicadores alterados e de mensagens falsas de sucesso na sincronização.

## Evidências

- `full-suite.json` / `.txt`: 272 testes gerais passaram antes das últimas adições de servidor e índice inválido.
- `completion.json` / `.txt`: 12 testes específicos passaram, incluindo HTTP real em fixture, preservação de notas e quarentena em cache.
- `final-suite.json` / `.txt`: 274 testes executados; 273 passaram e o benchmark de latência excedeu seu limite de 30 segundos. Inclui o teste adicional de índice corrompido. A falha está preservada, sem aumento do limite do teste.
- `examples-recheck.json` / `.txt`: os seis testes de exemplos e benchmark passaram na repetição isolada (15,630 segundos de execução dos testes), sem mudar o código ou o limite. O timeout não se reproduziu nessa rodada; isso não estabelece uma causa definitiva nem elimina a sensibilidade à carga da máquina.
- `static-checks.json`: sete arquivos Python analisados, dois JavaScript verificados e hashes das fontes alteradas.
- `live-http.json`: serviço local consultou o índice real, encontrou 144 candidatas e preparou contexto sem executar ações. Tempos são amostras únicas, não um benchmark.
- `20 - Central de Integracoes Jarvis.md`: arquivo fisicamente criado, com navegação e links das 144 skills sugeríveis por metadados.
- Backup inicial: `backups/connected-workspace-20260913-230827/manifest.json`; cópias verificadas por SHA-256 antes da edição.

## Limites confirmados

A consulta de conexão detectou o comando Codex e adaptadores de formato para Codex, ChatGPT e Gemini. Não houve verificação de sessão autenticada dos aplicativos. Obsidian e Antigravity não foram encontrados no PATH consultado; isso não prova ausência de instalação.

O índice real usa rótulos legados `VERIFIED_ADAPTED`, ausentes do enum atual do schema. O hub reconhece esse rótulo apenas para sugestões. Não migrou nem promoveu o catálogo. A dispensa `FLAGGED_REVIEW_WAIVER` ficou fora das sugestões.

Integração entre aplicativos significa contexto compartilhável com entrega manual nesta versão. Planejamento livre por modelo, controle de sessões, instalação autônoma, sincronização bidirecional e autonomia completa continuam pendentes. Não há alegação de conclusão do roadmap inteiro.

Não foi possível fazer inspeção visual: o inventário da ferramenta de navegador estava vazio. Foram verificados sintaxe JavaScript, respostas HTTP e estrutura servida; navegação por teclado, responsividade e aparência precisam de validação visual.

O script PowerShell de sincronização antigo permanece legado e fora do botão atualizado. A proteção contra mudanças concorrentes em arquivos é conservadora; não é uma transação contra escritores externos hostis. Nenhum push ou deploy foi executado.
