# Reanálise e fechamento das correções — 13 de setembro de 2026

Base: `91909f69bed720274a148a4411090f90d4511889`. Branch: `main`. O usuário autorizou concluir a revisão e criar um commit local; não houve autorização de push ou release.

## Resultado

As falhas reproduzidas nesta revisão foram corrigidas. A bateria completa de fixtures passou em **261 testes**, incluindo execução real de arquivos, reinício, autorização, memória, HTTP e formatação da interface. As validações finais estão em [full-suite.json](full-suite.json) e [full-suite.txt](full-suite.txt). O resultado comprova o escopo abaixo; não recupera a alegação histórica de certificação integral das 55 fases.

## Cobertura e preservação

- Inventário inicial: **1.565 arquivos versionados**; **483 arquivos autorais** indexados integralmente e copiados com verificação SHA-256 antes da revisão. [Manifesto inicial](baseline.json).
- Segunda cópia verificada dos módulos e testes antes da continuação: `backups/completion-20260913-181331/manifest.json`; 86 arquivos. Os dois scripts PowerShell corrigidos receberam cópias adicionais nessa pasta.
- Relatório histórico de release preservado em [additional-backup.json](additional-backup.json).
- A leitura semântica concentrou-se em execução, política, admissão, arquivos, recuperação, memória, contexto, medição, roteamento, fronteira HTTP, inserções HTML, exemplos e testes relacionados. A análise sintática abrangeu os arquivos Python/JSON selecionados e **107 scripts PowerShell** em tooling/tests.
- Inventário e análise sintática não equivalem à revisão semântica de cada linha. Não foram copiados para os testes dados privados, credenciais, notas pessoais do cofre ou corpos de skills de terceiros. Payloads em quarentena ficaram fora do escopo.

## Correções encerradas

| Área | Resultado implementado e verificado |
| --- | --- |
| Ação explícita | Requisitos de verificação não geram comandos executáveis. Planos de capacidades precisam de ação e verificações fornecidas pelo host. Ausência ou formato não suportado de ação produz falha, sem sucesso inventado. |
| Tentativas | Registro RUNNING persistido antes do efeito; resultado final atualiza a mesma identidade de tentativa. O teste inspeciona o estado em disco antes de permitir a escrita. |
| Dependências | A execução confere predecessores verificados no estado atual, inclusive na retomada. Uma onda planejada não autoriza dependências que falharam. |
| Recuperação | Tarefas verificadas são preservadas; leituras interrompidas podem ser repetidas; escritas de resultado ambíguo ficam pendentes de reconciliação, sem repetição automática. |
| Aprovação | Nome de operador ou assinatura fictícia não autorizam. Envelope assinado vincula missão/tarefa, ação, conteúdo, escopos, parâmetros e validade. Pedidos persistem; um marcador criado de forma exclusiva impede consumir a mesma concessão duas vezes. O estado persistido é reconferido antes do uso. |
| Limite de autonomia | R4 exige simultaneamente verificador confiável, concessão válida e teto de autonomia explicitamente configurado pelo host. R5 continua negado. Flags serializadas não concedem autoridade. |
| Arquivos | Escrita exige escopo canônico e hash anterior para sobrescrita. Backup físico verificado, temporário exclusivo, limite de 1 MiB, rechecagem anterior à publicação e proteção de estado/configuração/backups/Git/.env. Links, reparse points, streams e componentes ambíguos são recusados. |
| Política offline | A restrição global offline também bloqueia agentes com permissão individual de rede. |
| Memória | Versões conflitantes são preservadas e excluídas da recuperação ativa. Snapshots confinados, restauração transacional, validação de enums/confiança/datas e rejeição de proveniência vazia/desconhecida. Itens arquivados e primeiro item acima do orçamento não entram no resultado. |
| Isolamento | Componentes passam a respeitar a raiz configurada. Runtime usa sua própria telemetria e caminhos de cofre. Importar o módulo do cofre não carrega conteúdo privado. O validador usa cópia descartável com catálogo sintético. |
| Medição | Ações locais sem modelo registram zero tokens de modelo. Estimativas de catálogo permanecem identificadas como estimativas; recibos de modelo informam NOT_INVOKED. Resultados observados são atualizados nos recibos persistidos. |
| Roteamento | Ação local explícita restringe a seleção ao seu adaptador. Catálogo vazio permanece vazio; custos e capacidades inválidos são rejeitados. |
| Contexto | Decisões, riscos, incertezas, autoridade e restrições sobrevivem à limpeza/truncamento; metadados essenciais acompanham a compactação estruturada. |
| Verificação | Comandos, testes executáveis e consultas HTTP exigem habilitação explícita do host no verificador; não ficam implicitamente autorizados pela tarefa. Verificações de arquivo são confinadas. |
| Painel | Bind em loopback; validação de Host/Origin/cliente; JSON estrito e limitado; assets confinados; remoção de CORS universal. Testes fazem requisições HTTP reais aos métodos do handler, sem inicializar serviços privados. |
| Interface | Texto de catálogo, repositórios, chat e resultados recebe escape também de aspas em atributos. Markdown não rompe atributos por aspas injetadas. Missão malsucedida não recebe selo ou mensagem de sucesso. |
| PowerShell | Corrigidos escapes que impediam analisar Analyze-CatalogDeep.ps1 e Invoke-SecurityTriageReconciliation.ps1. Os 107 scripts passam no parser; os fluxos de governança não foram executados como efeito dessa validação. |
| Documentação | README, roadmap, exemplo e benchmark distinguem execução real, planejamento, estimativa e medição. Certificação histórica foi explicitamente contestada, mantendo rastreabilidade. |

O ajuste final da seleção de ferramentas na retomada foi novamente validado nos **8 testes integrados de fechamento**, todos aprovados: [completion-tests.json](completion-tests.json). A CI agora usa o mesmo validador isolado e inclui a verificação JavaScript. A CI remota não foi executada nesta sessão.

## Como reproduzir

Na raiz do projeto:

```powershell
python -B tooling/validate_isolated.py --report reports/local-validation.json
node --check ui/jarvis.js
```

O primeiro comando copia fontes autorais para uma pasta temporária, cria catálogo sintético e estado vazio, impede conexões externas dos testes Python, executa a descoberta completa e grava saída/código de retorno. Node.js valida as funções reais de formatação da interface; sua ausência é informada como teste ignorado, nunca como aprovação. A validação de sistema incluída na suíte também executa as baterias agentic; esses testes internos repetidos não são somados como testes únicos ao total externo de 261.

Os testes antigos que esperavam aprovação por nome, execução de verificadores como ações ou sucesso sem efeitos foram corrigidos. A segurança não foi relaxada para manter essas expectativas. O teste positivo de aprovação utiliza HMAC de fixture e passa por persistência, reinício e execução real.

## Limites operacionais mantidos

1. **Produto:** a execução validada é local e explícita. Resolução de uma capacidade em linguagem natural não constitui implementação automática dessa capacidade. Chamadas reais de modelos, provedores, infraestrutura remota e federação não são certificadas pelos testes locais.
2. **Host:** o responsável pela aplicação fornece e protege o verificador de identidade. A chave HMAC do teste é apenas uma fixture e não é configuração de produção. O teto padrão permanece restrito; habilitar A5 não elimina a política R5.
3. **Sistema de arquivos:** backup e rechecagem não são compare-and-swap do sistema operacional contra processos hostis. Um processo externo pode alterar o alvo entre a última leitura e a substituição. Escritas ambíguas exigem reconciliação; não há promessa de sandbox do sistema operacional.
4. **Memória:** proveniência identifica a fonte declarada; não autentica por si só a verdade semântica do conteúdo. A resolução de conflitos exige decisão explícita; a revisão não escolhe silenciosamente qual valor é verdadeiro.
5. **Interface:** loopback e Origin reduzem a exposição do navegador/rede; não autenticam processos locais hostis. Os testes HTTP não inicializam o servidor completo nem usam dados pessoais ou provedores reais.
6. **Validação:** sintaxe PowerShell/JavaScript não certifica os efeitos de cada script nem aparência visual em todos os navegadores. Integrações de produção precisam dos seus próprios testes e permissões.

Esses limites são fronteiras declaradas de operação e expansão do produto. O commit de correções não deve ser anunciado como certificação irrestrita ou conclusão de toda evolução futura do roadmap.

## Evidência histórica

[security-before.txt](security-before.txt) registra cinco falhas em oito casos iniciais. Os três casos HTTP desse registro já usavam o helper novo. [test-results.json](test-results.json) registra a primeira rodada de 26 testes, anterior ao fechamento integrado. As validações finais e seus hashes substituem esses números para a revisão atual.
