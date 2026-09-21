---
title: "ROWZY / JARVIS — inventário técnico do vídeo de referência"
type: external-reference-analysis
status: REFERENCE_ONLY_NOT_IMPLEMENTED
created: 2026-09-21
authoring: assistant-analysis-requested-by-user
source_video_id: w7hDGVUIeQg
source_conversation_id: 6ab09443-6fd4-83e9-bd64-387c01d5e696
evidence_scope: markdown-and-sampled-video-frames
tags:
  - jarvis
  - external-reference
  - rowzy
  - voice
  - dashboard
  - integrations
  - provenance
---

# ROWZY / JARVIS: inventário técnico e prioridades de reaproveitamento

> Referência externa e propostas de aplicação. Este documento não altera contratos canônicos, não constitui autorização de execução e não comprova funcionalidades implementadas no JARVIS deste repositório. Mensagens de agentes filmadas são relatos do material, não testes executados nesta análise.

## Origem e navegação

- [Vídeo de referência](https://www.youtube.com/watch?v=w7hDGVUIeQg).
- [Markdown original preservado](sources/rowzy-w7hDGVUIeQg-description.md).
- [Registro de procedência e hashes](sources/rowzy-w7hDGVUIeQg-provenance.json).
- [Índice de documentação](../README.md).
- [[00 - J.A.R.V.I.S. Cognitive Vault|Mapa principal do Obsidian]].
- [[12 - Arquitetura de Audio e Voz Holografica J.A.R.V.I.S.|Arquitetura de voz existente]].
- [[19 - Memoria Persistente e Conhecimento Episodico|Memória existente]].
- [[20 - Central de Integracoes Jarvis|Navegação de integrações existente]].
- [[23 - Master Prompt & Especificacao da Nova Interface J.A.R.V.I.S. Mark-LIV (Holomat Quantum Cockpit)|Referência de interface existente]].

## Escopo da incorporação documental

O texto integral da análise entregue na conversa foi preservado abaixo, inclusive os 16 grupos de achados, o fluxo reconstituído, a matriz de problemas e as prioridades P0–P3. A única adaptação no corpo esclarece que a afirmação de ausência de alterações se refere à etapa original de análise. Metadados internos de citação de memória do assistente não integram o documento.

Na incorporação de 2026-09-21, a configuração local do Obsidian confirmou que o vault ativo é o próprio repositório E:\.skill-registry. Por isso existe uma única cópia canônica desta análise, indexada tanto em docs/README.md quanto no MOC do vault. Links adicionais foram colocados fora dos blocos de projeção gerenciada.

Foram lidos AGENTS.md, README.md, docs/README.md, CONTRIBUTING.md, docs/REMOTE_SECOND_BRAIN.md e o fluxo CognitiveVaultBridge.sync_registry. O sincronizador de catálogo atualiza MOCs de skills e Canvas; não é necessário executá-lo para publicar esta referência Markdown no mesmo vault. Nenhum novo sincronizador ou sistema paralelo foi criado.

A documentação corrente descreve um runtime residente, MemoryFabric e ponte bidirecional do vault. Esse contexto reforça a prioridade de integrar voz, proveniência e visualização aos caminhos existentes. A leitura documental não é nova validação empírica do runtime. As referências históricas no fim da análise original permanecem explicitamente históricas.

## Análise integral

**O material é uma referência útil para o seu JARVIS principalmente em quatro pontos: integração de dados pessoais, separação entre usuários e conexões, voz com processamento local e um dashboard que combina métricas com uma interface futurista.** Ele também registra problemas de implementação valiosos: autenticação funcionando sem histórico carregado, diferenças entre ambientes, conflitos de deployment e números fictícios usados durante o desenvolvimento visual.

Li integralmente o markdown, inspecionei o conteúdo do ZIP e examinei dezenas de quadros distribuídos pelo vídeo, ampliando telas de banco de dados, autenticação, configurações, desenvolvimento e interface.

O ZIP contém **um único MP4 de 282.660.708 bytes**, com duração de **13min18,674s**. A cópia encontrada em Downloads é idêntica ao MP4 dentro do ZIP, verificada por SHA-256:

`10EF63364507EEA9C606DBA5A64EA3F4E86D61872826299D6BEB28408D0E25FF`

**Limite da análise:** não fiz transcrição integral do áudio nem auditoria do código do aplicativo mostrado. Portanto, o inventário abaixo cobre o markdown, os quadros examinados e os textos legíveis nas telas; não atribuo ao vídeo falas que não transcrevi. Na etapa original de análise, nenhum arquivo de projeto ou repositório foi criado ou alterado; os quadros foram processados em memória. A presente etapa registra essa análise como documentação, por solicitação posterior do usuário.

Para deixar a procedência clara, uso estas distinções:

| Marca | Significado |
|---|---|
| **Observado** | Elemento efetivamente visível no vídeo: interface, configuração, esquema, arquivo, mensagem ou resultado apresentado. |
| **Declarado** | Afirmação do markdown ou de uma pessoa/agente em uma tela do vídeo. Comprova que a afirmação foi feita, sem validar automaticamente sua correção. |
| **Inferido** | Interpretação técnica plausível, ainda sem demonstração suficiente. |
| **Proposto** | Ideia de aplicação futura ao seu JARVIS. |

**O aplicativo mostrado se chama ROWZY; JARVIS é a referência e a camada de assistente.** Também aparece **Vitality**, identificado no vídeo como um aplicativo anterior de Luke. Isso ajuda a entender que parte do trabalho foi reaproveitamento e evolução de uma base existente, incluindo referências visuais, em vez de uma construção inteiramente nova.

1. **Arquitetura e stack: o material aponta para um aplicativo web com serviços externos e um componente local de voz.**

   O markdown descreve cinco dias de trabalho de dois irmãos, Luke e Rowan, partindo de um mockup no Canva. As telas mostram desenvolvimento assistido por IA, configuração de serviços e sucessivas versões do dashboard.

   | Camada | Tecnologia ou componente | Evidência e limite |
   |---|---|---|
   | Aplicativo web | **Next.js** | **Declarado** no markdown. **Observados** arquivos como `next.config.ts`, `next-env.d.ts`, `src`, `public` e `package.json`. |
   | Linguagem/configuração | **TypeScript** | **Observados** `tsconfig.json`, `next.config.ts` e artefatos associados. Versões não identificadas. |
   | Banco e autenticação | **Supabase** | **Observados** painel do banco, schemas, tabelas, relações e mensagens sobre Supabase Auth. |
   | Hospedagem | **Vercel** | **Observados** deployments de Preview e Production, variáveis de ambiente e URLs hospedadas. |
   | Versionamento | **Git/GitHub** | **Observados** branches, commits, referências a checkouts e associação entre versões e deployments. |
   | Desenvolvimento por IA | **Codex, Claude Code e ChatGPT** | **Declarados e observados** no processo de construção. |
   | IA externa | **Gemini API / Google AI Studio** | **Declarados**; aparece criação de chave e a variável `GEMINI_API_KEY`. A função final exata não fica demonstrada. |
   | Outra configuração de IA | **OpenAI API** | **Observada** a variável `OPENAI_API_KEY`; isso não comprova qual modelo ou rota a utilizava. |
   | Execução local de LLM | **Ollama + Gemma 3** | **Declarados** na seção de voz. Ollama também aparece nas telas. |
   | Reconhecimento de fala | **Whisper** | **Declarado** e incluído no fluxo escrito de voz. |
   | Síntese de voz | **Qwen3-TTS / MLX Audio** | **Declarados** na descrição. A configuração final não é recuperável apenas das telas examinadas. |
   | Experimentos de voz | **OpenVoice e Fish Audio** | **Observados** download de modelos OpenVoice e interface de síntese no Fish Audio. Não devem ser confundidos automaticamente com o motor final. |
   | Memória local | **SQLite** | **Declarado** na seção do sistema de voz, junto da memória de conversação local. |
   | Design | **Canva, Mobbin, Pinterest** | **Declarados e observados** como ferramentas/referências de design. |
   | Edição do vídeo | **CapCut** | **Declarado** como ferramenta de edição, sem evidência de participação no runtime do aplicativo. |

   **Inferência de arquitetura:** existe uma separação entre o aplicativo hospedado, a persistência/autenticação e um auxiliar local de voz. O transporte exato entre navegador e auxiliar — HTTP local, WebSocket ou outro mecanismo — não ficou comprovado.

   O material **não estabelece** versões de dependências, biblioteca dos gráficos, framework de animação, modelo exato do Gemini, tamanho/quantização do Gemma 3, variante do Whisper ou configuração final de TTS.

2. **O modelo de dados é uma das referências mais concretas do vídeo.**

   Por volta de [08:40](https://www.youtube.com/watch?v=w7hDGVUIeQg&t=520s), o visualizador do Supabase mostra estas tabelas no schema `public`:

   | Tabela observada | Campos legíveis ou grupos de campos | Utilidade arquitetural |
   |---|---|---|
   | `dashboards` | `id`, `name`, `created_at`, `updated_at` | O dashboard existe como entidade própria. |
   | `dashboard_memberships` | `id`, `dashboard_id`, `user_id`, `person_key`, `display_name`, datas | Relaciona usuários ao dashboard e à identidade apresentada na interface. |
   | `whoop_connections` | `id`, `dashboard_id`, `user_id`, `whoop_user_id`, `status`, `scopes`, `token_expires_at`, `last_synced_at`, `error_message`, `connected_at`, datas | Separa a identidade interna da conta do provedor e registra o estado operacional da conexão. |
   | `whoop_daily_metrics` | Identificadores de conexão/dashboard/usuário/ciclo, métricas de saúde, estados e datas de atualização | Armazena dados históricos e rastreia sua origem. |
   | `progress_photos` | `id`, `user_id`, `storage_path`, `captured_on`, `angle`, `weight_kg`, `note`, `created_at` | Prevê fotos de evolução com data, contexto e referência ao armazenamento. |

   Também aparecem em `whoop_connections` campos de controle de sincronização como `sync_lease_owner` e outros nomes truncados relacionados à expiração da reserva e à última tentativa.

   **Inferido:** esses campos sugerem coordenação para evitar que duas execuções sincronizem a mesma conexão ao mesmo tempo. Os nomes de commits sobre ordenação de locks reforçam essa interpretação, mas o algoritmo não foi inspecionado.

   A modelagem observada permite distinguir:

   - O usuário autenticado no aplicativo.
   - Sua participação em um dashboard.
   - A conta WHOOP conectada.
   - Os dados recebidos dessa conexão.
   - O estado e a antiguidade da sincronização.

   **Proposto para o JARVIS:** reaproveitar essa separação conceitual. Uma pessoa, uma conta externa, uma autorização e uma coleção de dados são entidades diferentes, mesmo quando inicialmente existe apenas um usuário.

   A presença das tabelas no schema `public` **não comprova acesso público aos dados**. As políticas de autorização não foram examinadas.

3. **Contas separadas e dashboard compartilhado são conceitos diferentes no projeto.**

   **Declarado:** cada irmão possui uma conta privada separada.

   **Observado:** Luke e Rowan aparecem simultaneamente na interface, cada um com seus indicadores e seu estado WHOOP. Em uma versão, Luke aparece conectado enquanto Rowan apresenta erro e um botão de reconexão. O banco contém `dashboard_memberships`, além de `user_id` e `dashboard_id`.

   **Inferido:** há um dashboard compartilhado entre membros autorizados, com conexões pessoais distintas. Isso é mais específico do que simplesmente “duas contas isoladas”.

   O material não permite confirmar:

   - Se cada usuário só pode visualizar seus próprios dados.
   - Se ambos consentem com a visualização cruzada.
   - Quais papéis ou permissões existem.
   - Se a separação é imposta em todas as consultas.
   - Se YouTube, Instagram e TikTok também têm conexões individuais para cada irmão.

   **Proposto:** no seu JARVIS, separar explicitamente “minha conta”, “minhas integrações” e “dados compartilhados neste espaço”. A interface deve tornar essa distinção compreensível, e o backend deve aplicá-la.

4. **A autenticação vai além da tela de login e registra problemas reais de callbacks e sessões.**

   Em [05:20](https://www.youtube.com/watch?v=w7hDGVUIeQg&t=320s), aparece a rota `/auth/confirm`, com uma tela intermediária para confirmar um link de e-mail. O texto informa que verificações automáticas de segurança de e-mail não devem ativar o link; o usuário precisa clicar em **Continue**.

   Em [09:20](https://www.youtube.com/watch?v=w7hDGVUIeQg&t=560s), a tela de entrada mostra:

   - E-mail e senha.
   - Conta privada ROWZY.
   - Recuperação de senha.
   - Botão de entrada.

   Em [03:05](https://www.youtube.com/watch?v=w7hDGVUIeQg&t=185s), uma mensagem de agente descreve:

   - Autenticação SSR com Supabase.
   - Implementação no App Router.
   - Validação de sessão por `getClaims()`.
   - Lista explícita de destinos permitidos para redirecionamento.
   - Verificação de membership antes da leitura do dashboard.
   - Tratamento de convite e recuperação de senha.
   - Um marcador de fluxo assinado, de curta duração e mantido no servidor.
   - Um problema em que o hostname temporário de Preview poderia separar o cookie PKCE do hostname estável usado pelo callback.

   Esses mecanismos são **declarados em uma tela de desenvolvimento**. Não inspecionei sua implementação.

   **Referências reaproveitáveis:** confirmação explícita de links de uso único; continuidade da sessão entre callback e aplicativo; domínio estável para fluxos de autenticação; autorização antes de consultar dados; e testes separados para login, convite, recuperação e integração externa.

5. **A integração WHOOP é a mais detalhada e melhor sustentada pelo material.**

   Em [02:25](https://www.youtube.com/watch?v=w7hDGVUIeQg&t=145s), o painel de desenvolvedor mostra uma URL de callback terminada em:

   `/api/whoop/callback`

   Os escopos visíveis são:

   - `read:recovery`
   - `read:cycles`
   - `read:sleep`
   - `read:workout`
   - `read:profile`

   A tela de consentimento também explicita categorias como perfil, recuperação, ciclos, sono e exercícios.

   **Observado:** conexão por usuário, botão para conectar/reconectar, estado de erro, datas de sincronização, expiração de token no esquema e configuração de credenciais do aplicativo.

   **Declarado:** sincronização automática de dados de saúde.

   **Não comprovado:** periodicidade exata, uso de webhooks, estratégia completa de renovação de tokens, paginação, limites de API e cobertura de todos os escopos na versão final.

   Um ponto especialmente útil: o material trata **conexão, sincronização e histórico disponível como estados distintos**. Essa distinção deveria orientar tanto a arquitetura quanto a UX do seu JARVIS.

6. **O inventário de métricas de saúde é mais amplo do que os indicadores grandes do dashboard.**

   Há evidência no esquema de dados e/ou nas telas para:

   | Grupo | Métricas e informações |
   |---|---|
   | Recuperação | Score de recuperação, estado do score, frequência cardíaca de repouso, HRV/RMSSD. |
   | Esforço/ciclo | Strain, início/fim do ciclo, identificador do ciclo, energia em quilojoules, frequência cardíaca média e máxima. |
   | Sono | Performance, duração, necessidade de sono, eficiência, consistência, frequência respiratória. |
   | Estágios do sono | Sono leve, profundo, REM e tempo acordado. |
   | Outros sinais | SpO₂ e temperatura da pele. |
   | Proveniência | Datas de atualização do ciclo, recuperação e sono; data de sincronização; conexão e usuário de origem. |
   | Apresentação | Séries históricas, sparklines, valores ausentes, variações e mensagens de interpretação. |

   A interface exibe um indicador chamado **“Locked In”**, além de métricas individuais de recuperação, sono, HRV e strain. Em quadros examinados, esses números são diferentes entre si.

   **Inferido:** “Locked In” é um indicador próprio ou composto, não simplesmente uma repetição do score WHOOP.

   **Não comprovado:** fórmula, pesos, tratamento de dados ausentes ou validade desse indicador.

   **Proposto:** qualquer score composto do JARVIS deve informar seus componentes, a data considerada e o que acontece quando faltam dados. Um círculo visualmente completo não deve esconder um conjunto incompleto de informações.

7. **As integrações sociais têm configuração concreta, mas a veracidade dos números varia durante a construção.**

   O markdown lista:

   - YouTube Data API.
   - YouTube Analytics API.
   - Instagram Platform e Meta Developer Apps.
   - TikTok Developers e cadastro de aplicativos.

   Em [04:40](https://www.youtube.com/watch?v=w7hDGVUIeQg&t=280s), a Vercel mostra nomes de variáveis, com valores ocultos:

   | Provedor/função | Variáveis visíveis |
   |---|---|
   | YouTube | `YOUTUBE_API_KEY`, `YOUTUBE_OAUTH_CLIENT_ID`, `YOUTUBE_OAUTH_CLIENT_SECRET`, `YOUTUBE_OAUTH_REFRESH_TOKEN` |
   | Instagram | `META_IG_ACCOUNT_ID`, `META_IG_ACCESS_TOKEN` |
   | TikTok | `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET` |
   | WHOOP | `WHOOP_CLIENT_ID`, `WHOOP_CLIENT_SECRET` |
   | IA | `GEMINI_API_KEY`, `OPENAI_API_KEY` |
   | Aplicação/automação | `ROWZY_APP_URL`, `CRON_SECRET` |

   **Observado:** configuração por provedor e por ambiente/branch. **Não comprovado:** que todas essas credenciais fossem válidas, usadas pelo runtime ou suficientes para obter todas as métricas mostradas.

   As telas sociais apresentam:

   - Inscritos do YouTube.
   - Seguidores de Instagram e TikTok.
   - Variações e totais em janelas como 30 dias.
   - Alcance, visualizações ou indicadores associados, conforme a tela.
   - Sparklines e representações de tendência.
   - Uma visualização ampliada por plataforma, como **Instagram Signal**.

   Há duas ressalvas decisivas:

   **Primeira:** em [06:20](https://www.youtube.com/watch?v=w7hDGVUIeQg&t=380s), o pedido de design solicita expressamente dados fictícios para desenvolver o visual.

   **Segunda:** em [07:50](https://www.youtube.com/watch?v=w7hDGVUIeQg&t=470s), uma mensagem de agente afirma que, naquele estado da branch, ainda não existia ingestão/armazenamento social.

   Isso não prova que a integração permaneceu ausente até o final, mas impede classificar todos os gráficos do vídeo como dados reais.

   **Proposto:** cada métrica do JARVIS deveria carregar origem, conta, período, horário de coleta e condição — real, simulada, desatualizada ou indisponível.

8. **A sincronização e o preenchimento do histórico merecem prioridade maior que a animação dos gráficos.**

   Em [09:20](https://www.youtube.com/watch?v=w7hDGVUIeQg&t=560s), o usuário reclama que a conexão aparece como concluída, mas parte do score e os gráficos estão ausentes.

   O agente responde que:

   - A autenticação OAuth teria sido corrigida.
   - O problema restante seria de armazenamento/preenchimento histórico.
   - Dias completos anteriores de sono e recuperação não teriam sido importados.
   - Estava sendo implementado um preenchimento de **14 dias**.
   - O score passaria a usar o dia completo mais recente.
   - Uma reconexão bem-sucedida dispararia sincronização automaticamente.

   Tudo isso é **diagnóstico e plano declarados na tela**. A demonstração posterior de séries históricas é compatível com uma evolução, mas não substitui verificação dos registros.

   Também aparecem:

   - Botões de sincronização manual.
   - Horários da última sincronização.
   - `CRON_SECRET` na configuração.
   - Campos para controlar tentativas e concorrência.

   **Inferido:** o projeto combina ações manuais, eventos de conexão e alguma forma de automação agendada. A agenda concreta não foi identificada.

   **Proposto:** o JARVIS deve distinguir pelo menos: desconectado; autorizado; importação inicial em andamento; sincronizado; histórico parcial; dado atrasado; falha; reconexão necessária. Repetir uma sincronização também deve preservar a consistência dos dados, sem duplicar registros.

9. **O sistema de voz é híbrido no processo de desenvolvimento, com um fluxo local explicitamente planejado.**

   Em [07:50](https://www.youtube.com/watch?v=w7hDGVUIeQg&t=470s), a tela apresenta um arquivo de teste `rowzy-voice-test_000.wav`, uma afirmação de que o teste local funcionou e o fluxo:

   **Microfone → Whisper → Ollama → voz escolhida**

   Em seguida, há a decisão de construir primeiro um **auxiliar local privado**, testar o ciclo completo no Mac e só depois conectá-lo ao dashboard.

   O markdown acrescenta Gemma 3, Qwen3-TTS, MLX Audio e SQLite.

   Também há evidências de experimentação:

   - Em [07:05](https://www.youtube.com/watch?v=w7hDGVUIeQg&t=425s), aparece a preparação de uma referência de áudio relacionada ao personagem.
   - Em [07:35](https://www.youtube.com/watch?v=w7hDGVUIeQg&t=455s), o Fish Audio mostra uma voz de comunidade, texto para síntese e clipes gerados. A interface exibe o modelo **Fish Audio S2.1 Pro** naquele experimento.
   - Em [07:45](https://www.youtube.com/watch?v=w7hDGVUIeQg&t=465s), o terminal mostra downloads de modelos **OpenVoice**.
   - Em [08:00](https://www.youtube.com/watch?v=w7hDGVUIeQg&t=480s), uma mensagem relata interrupção de download por falta de espaço e posterior retomada.

   **Conclusão sustentada:** houve comparação ou experimentação de soluções de voz, seguida de trabalho para um ciclo local. **Não é possível fixar um único motor de TTS como responsável por todas as cenas.**

   Não foram determinados:

   - Latência de STT, LLM e TTS.
   - Streaming de áudio.
   - Cancelamento/interrupção de fala.
   - Detecção de silêncio.
   - Controle de eco.
   - Modelo e tamanho exatos.
   - Consumo de memória.
   - Funcionamento offline completo.
   - Qualidade em português.

   **Proposto:** reaproveitar a separação STT → interpretação/contexto → resposta → TTS, com estados visíveis e componentes substituíveis. A escolha concreta dos motores deve depender dos requisitos do seu JARVIS e do ambiente em que ele já funciona.

10. **A interface final associa o assistente aos dados, mas não revela o mecanismo de consulta.**

    Em [11:20](https://www.youtube.com/watch?v=w7hDGVUIeQg&t=680s), a tela **Instagram Signal** mostra uma resposta textual do assistente mencionando **4.630 no YouTube e 16.611 no Instagram**, coerente com valores apresentados nas telas próximas.

    **Observado:** resposta contextualizada com números do dashboard e uma barra inferior de atividade/resposta.

    **Não comprovado:** se esses valores foram obtidos por consulta ao banco, chamada de ferramenta, contexto pré-montado, leitura da interface ou outra estratégia. A cena também não prova a autenticidade externa dos números.

    O fluxo abaixo é uma **reconstituição provável**, não um diagrama extraído do código:

    ```mermaid
    flowchart LR
        A[Contas e APIs externas] --> B[Autorização e sincronização]
        B --> C[Dados por usuário e conexão]
        C --> D[Dashboard web]
        M[Microfone] --> S[Whisper]
        S --> L[LLM via Ollama]
        C -. Contexto: mecanismo não demonstrado .-> L
        Q[Memória local declarada] -.-> L
        L --> T[Síntese de voz]
        L --> R[Resposta textual]
        R --> D
    ```

    **Proposto:** o assistente do JARVIS deveria responder a partir da mesma camada de dados usada pelo dashboard, preservando usuário, origem, período e validade. Isso reduz o risco de a interface mostrar uma informação e a voz afirmar outra.

11. **A memória é declarada como local, mas sua estrutura não foi demonstrada.**

    O markdown afirma **memória de conversação local** e lista **SQLite** no sistema de voz.

    Isso permite registrar a intenção de persistir conversas localmente, mas não comprova:

    - Busca semântica ou embeddings.
    - Memória vetorial.
    - Sumarização automática.
    - Separação de memória por usuário.
    - Política de retenção.
    - Sincronização entre computadores.
    - Recuperação de fatos de longo prazo.
    - Conexão dessa memória com as métricas do dashboard.

    **Proposto para o seu JARVIS:** distinguir histórico de conversa, preferências pessoais, fatos persistentes e dados externos temporais. Uma métrica de ontem não deve se transformar em um “fato permanente” só porque foi mencionada em uma conversa.

12. **O dashboard oferece uma linguagem visual reaproveitável, com evolução visível entre as versões.**

    Os quadros de [03:40](https://www.youtube.com/watch?v=w7hDGVUIeQg&t=220s), [09:40](https://www.youtube.com/watch?v=w7hDGVUIeQg&t=580s) e [11:50](https://www.youtube.com/watch?v=w7hDGVUIeQg&t=710s) mostram essa evolução.

    | Elemento | Evidência visual |
    |---|---|
    | Estrutura | Duas colunas pessoais laterais e uma região central mais larga. |
    | Identidade pessoal | Luke e Rowan identificados separadamente; fotografias no centro superior. |
    | Fundo | Muito escuro, com tonalidades verde-azuladas e efeitos discretos de luz. |
    | Cartões | Contornos finos, transparência, cantos arredondados em versões iniciais e enquadramento mais técnico em versões posteriores. |
    | Tipografia | Números grandes e expressivos; rótulos pequenos, espaçados e frequentemente monoespaçados; textos editoriais em algumas versões. |
    | Saúde | Anéis circulares, score principal, séries menores, lista compacta de indicadores e horários de atualização. |
    | Redes sociais | Três módulos centrais: YouTube em vermelho/rosa, Instagram em roxo e TikTok em verde/ciano. |
    | Visualizações | Superfícies de partículas semelhantes a montanhas ou ondas, combinadas com totais e gráficos menores. |
    | Assistente | Ícone de microfone, estado do assistente e faixa inferior com texto e atividade visual. |
    | Sessão | Entrada, saída e telas de confirmação coerentes com a identidade visual. |
    | Tempo pessoal | Módulo circular de idade, próximo aniversário, dias restantes e progresso de uma “órbita”. |
    | Detalhamento | Tela dedicada **Instagram Signal**, além da visão geral. |

    Em [06:20](https://www.youtube.com/watch?v=w7hDGVUIeQg&t=380s), aparecem decisões explícitas de design:

    - Reutilizar o fundo do Vitality.
    - Gradientes de aurora sutis.
    - Montanha em SVG.
    - Textura de granulação.
    - Partículas que sobem lentamente.
    - Reduzir lavagens verdes excessivamente brilhantes.
    - Escurecer e tornar mais transparentes as molduras das fotos.
    - Estreitar as colunas laterais para ampliar a região central.
    - Repetir a visualização de partículas nas três redes sociais.

    **Limite:** a expressão “milhões de pontos” aparece como desejo no pedido visual. Não é uma contagem técnica comprovada. Tampouco é possível afirmar que os efeitos usam Three.js, WebGL, Canvas ou uma biblioteca específica.

13. **Há várias ideias de UX úteis, mas alguns elementos apenas anunciam recursos.**

    **Observado:**

    - Estado de conexão por pessoa.
    - Botão de reconexão próximo ao problema.
    - Última sincronização visível.
    - Valores ausentes representados por traços.
    - Microfone persistente.
    - Resposta textual acompanhando o assistente.
    - Visão geral e uma visão ampliada por plataforma.
    - Explicação textual junto dos indicadores.
    - Área de fotos de progresso.

    **Comprovação insuficiente:**

    - Uma versão mostra a indicação de que upload de fotos ainda viria depois, apesar da tabela `progress_photos` já existir.
    - A interface final contém indicações de ativação por “Jarvis” e por palmas; isso não comprova detecção funcional desses gatilhos.
    - O estado **Processing** aparece, mas não permite medir o tempo de resposta.
    - Não foi demonstrada experiência móvel ou acessibilidade completa.

    **Proposto:** conservar a clareza de estado, reconexão localizada, contexto da resposta e navegação entre resumo/detalhe. Para o JARVIS, os efeitos visuais deveriam acompanhar o estado real: escutando, transcrevendo, consultando, respondendo e indisponível.

    As superfícies de partículas podem funcionar como identidade visual. Se forem usadas como gráficos analíticos, precisam ter significado claro; o material não demonstra que sua geometria represente fielmente uma série real.

14. **Deployment e coordenação de desenvolvimento aparecem como fontes importantes de dificuldade.**

    Em [10:20](https://www.youtube.com/watch?v=w7hDGVUIeQg&t=620s), a lista da Vercel mostra muitos deployments, com estados **Ready** e **Blocked**, além de Preview e Production.

    Os títulos visíveis incluem trabalhos sobre:

    - Estado real da conexão WHOOP.
    - Aceitação de hashes de tokens do Supabase.
    - Confirmação explícita de links de e-mail.
    - Fundação de autenticação.
    - Ordenação de locks de conexão.
    - Segurança de renovação de tokens.
    - Fundação OAuth WHOOP.

    Em [00:20](https://www.youtube.com/watch?v=w7hDGVUIeQg&t=20s), mensagens de agentes descrevem outros problemas:

    - Um teste de acesso sem sessão recebia redirecionamento da proteção de Preview da Vercel antes de alcançar o aplicativo.
    - Havia diferença entre a versão esperada e a publicada.
    - O backend teria alcançado o Supabase, mas faltaria uma configuração remota de schema.
    - Testes locais teriam passado apesar dessa diferença.

    **Observado:** as mensagens e a lista de versões existem. **Não verificado:** a correção técnica de cada diagnóstico.

    **Proposto:** o JARVIS deveria distinguir a proteção da plataforma da autenticação da aplicação; registrar versão e ambiente de cada implantação; e testar o fluxo real de ponta a ponta no ambiente correto. Um build concluído não demonstra que OAuth, histórico e permissões estejam funcionando.

    A sugestão mostrada no vídeo para expor um schema específico do Supabase é contextual. Não há base para transplantá-la ao seu projeto sem examinar sua arquitetura e suas permissões.

15. **O processo de construção oferece referências de organização, sem provar uma arquitetura multiagente no produto final.**

    **Observado no desenvolvimento:**

    - Uso de `AGENTS.md` e `CLAUDE.md`.
    - Branches com responsabilidades diferentes.
    - Codex apresentado como coordenador em uma mensagem.
    - Claude Code trabalhando em um escopo descrito como frontend/Vercel.
    - Solicitações para verificar branch e commit antes de continuar.
    - Auditorias de contexto para evitar trabalho duplicado.
    - Uso de skills, conectores e subagentes nas ferramentas de desenvolvimento.
    - Uma tela de configuração de conector MCP, em torno de 04:20.

    **Distinção necessária:** isso demonstra agentes e MCP sendo usados para construir o sistema. Não comprova que o JARVIS em execução possua um orquestrador multiagente ou um servidor MCP próprio.

    Também aparece um pedido sobre um contrato chamado `SocialMetricsCore`, snapshots de contas sociais, pontos diários, métricas de conteúdo e registros de sincronização. Trata-se de **planejamento observado**, sem confirmação do schema social final.

    **Proposto:** reaproveitar a disciplina de fonte de verdade, responsabilidade por tarefa e verificação de trabalho já existente. A quantidade de agentes mostrada na ferramenta não é, por si só, uma referência de eficiência.

16. **Os problemas e limitações devem entrar no inventário junto com as funcionalidades.**

    | Problema ou limitação | Evidência | Aprendizado para aplicação |
    |---|---|---|
    | OAuth e links quebrados | Descrição e telas de diagnóstico | Testar o ciclo completo, incluindo retorno ao aplicativo e associação ao usuário correto. |
    | Configuração remota divergente da local | Diagnóstico mostrado em 00:20 | Validar contratos/configurações no ambiente real. |
    | Conectado sem dados suficientes | Reclamação e diagnóstico em 09:20 | Separar autorização, ingestão e completude. |
    | Histórico de sono/recuperação ausente | Markdown, campos vazios e diagnóstico | Planejar importação inicial e atualização de dias já existentes. |
    | Números sociais fictícios | Markdown e pedido explícito de UI | Identificar dados simulados de maneira inequívoca. |
    | Produção/Preview confusos | Mensagens e lista de deployments | Rastrear ambiente, branch e versão servida. |
    | Download de modelo interrompido | Mensagens na etapa de voz | Verificar espaço e permitir retomada. Os números de espaço exibidos são relatos do agente, não medições feitas nesta análise. |
    | Interface promete mais do que foi demonstrado | Upload futuro, gatilhos de voz/palmas | Diferenciar disponível, experimental e planejado. |
    | Memória pouco especificada | Declaração genérica e SQLite listado | Definir conteúdo, escopo e recuperação antes de depender dela. |
    | Desempenho não quantificado | Ausência de benchmarks nos elementos examinados | Medir latência, uso de recursos e falhas no projeto de destino. |
    | Finanças/calendário ainda futuros | Markdown os apresenta como próximos domínios | Tratar como expansão planejada, não integração existente. |

    Há ainda textos de exemplo na ferramenta de TTS falando em comparar semanas e lembrar o usuário no dia seguinte. **Um texto usado para testar uma voz não comprova que comparação histórica ou lembretes tenham sido implementados.**

**Para eventual aplicação no seu JARVIS, esta é a ordem de prioridade que eu adotaria.** Ela prioriza utilidade e confiabilidade antes de ampliar o acabamento visual.

| Prioridade | Item reaproveitável | Resultado esperado | Critério concreto para considerar pronto |
|---|---|---|---|
| **P0** | Origem e validade de cada informação | Assistente e dashboard sabem de onde veio cada dado. | Métricas exibem usuário/conta, período, coleta e condição real/simulada/ausente. |
| **P0** | Separação entre identidade, conexão e espaço compartilhado | Evitar associação incorreta entre pessoas e integrações. | Cada consulta e resposta respeita o contexto de autorização definido. |
| **P0** | Estados completos de sincronização | Acabar com “conectado” como sinônimo de “funcionando”. | UI distingue autorização, importação, histórico parcial, sucesso e erro. |
| **P0** | Fonte comum de dados para voz e dashboard | Respostas coerentes com a tela. | A resposta informa o mesmo valor e período da consulta estruturada correspondente. |
| **P1** | Histórico e atualização idempotente | Séries utilizáveis e recuperáveis. | Repetir sincronização não duplica dados; lacunas continuam identificáveis. |
| **P1** | Entrada por voz no fluxo existente | Interação prática com o JARVIS. | Ciclo completo com transcrição, resposta textual, áudio, falhas e cancelamento compreensíveis. |
| **P1** | Memória com escopo e procedência | Continuidade sem transformar informação temporária em fato permanente. | Conversas, preferências e dados externos têm tratamento distinto. |
| **P1** | Estados e recuperação na interface | Usuário consegue entender e corrigir problemas. | Conexão, reconexão, última atualização e motivo de indisponibilidade são claros. |
| **P1** | Validação por ambiente | Reduzir regressões de autenticação/deployment. | Login, callback, autorização e leitura de dados funcionam no ambiente publicado correspondente. |
| **P2** | Dashboard modular e detalhamento | Visão rápida sem perder profundidade. | Resumo e detalhe usam as mesmas métricas e definições. |
| **P2** | Linguagem visual futurista | Identidade consistente. | Animações preservam legibilidade e não encobrem ausência ou erro de dados. |
| **P2** | Observabilidade | Saber onde o sistema falha ou fica lento. | Medir sucesso/atraso de sync, completude, latência de STT/LLM/TTS e falhas de conexão. |
| **P3** | Wake word, palmas e efeitos adicionais | Conveniência complementar. | Avaliação de falsos acionamentos e controle claro de ativação. |
| **P3** | Fotos de progresso, tempo pessoal, finanças e calendário | Expansão de domínio. | Entram conforme uma necessidade real do usuário e com integração demonstrável. |

No seu caso, essa aplicação deve respeitar a estrutura que já existe. **Pelo registro histórico do seu JARVIS — que não reauditei nesta execução e pode ter mudado — já havia um planejador/resolvedor canônico, uma entrada de missão na interface e uma ponte de sincronização com o vault.** Assim, as ideias do vídeo devem orientar extensões desses caminhos: voz como outra forma de entrada, dashboard como apresentação do estado existente e memória integrada ao sistema já adotado. O vídeo não fornece motivo suficiente para substituir sua stack ou criar outro planejador, outro painel independente ou um segundo sistema de memória.

O material deixa sem resposta a implementação final do transporte de voz, a política completa de autorização, o mecanismo de recuperação de memória, a fórmula do score próprio, a autenticidade de cada métrica social e o desempenho operacional. **Esses pontos permanecem como lacunas documentadas, não como funcionalidades confirmadas.**
