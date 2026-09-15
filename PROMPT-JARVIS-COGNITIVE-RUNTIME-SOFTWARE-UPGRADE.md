# JARVIS — Cognitive Runtime Software Upgrade

> Prompt de execução para evoluir o `jarvis-skill-registry` em um runtime cognitivo autônomo, econômico em contexto, orientado por capabilities, independente de provedor e capaz de operar local-first/cloud-optional sem criar uma arquitetura paralela.

## PAPEL

Atue como **Staff/Principal AI Systems Engineer** trabalhando diretamente no repositório atual.

Seu objetivo não é criar mais um framework multiagente nem adicionar componentes por quantidade. O objetivo é **melhorar o runtime existente**, fazendo o Jarvis tomar decisões melhores, mais baratas, mais explicáveis e mais independentes de fornecedor.

Trabalhe incrementalmente, preserve contratos estáveis e use os nomes, tipos, módulos e abstrações **reais do repositório**. Os exemplos deste documento são conceituais e não autorizam a criação de APIs duplicadas.

---

# OBJETIVO FINAL

Evoluir o Jarvis para que consiga, em runtime:

- selecionar modelo/backend pela capacidade necessária, não por fornecedor hardcoded;
- selecionar ferramentas/skills pela necessidade da tarefa e pelas permissões disponíveis;
- montar apenas o contexto realmente necessário;
- respeitar um orçamento explícito de contexto/tokens/custo;
- usar evidence e confidence para alterar o próprio fluxo de execução;
- classificar falhas e escolher fallback apropriado sem loops cegos;
- compartilhar infraestrutura de inferência entre agentes sem compartilhar estado privado;
- operar em modo `local_only` de forma verificável e fail-closed;
- persistir apenas memórias relevantes, novas e confiáveis;
- reutilizar resultados válidos via cache sem ignorar freshness/policy;
- explicar por que escolheu determinado modelo, ferramenta, contexto e fallback;
- manter o domínio/core independente de OpenAI, Ollama, vLLM, llama.cpp ou qualquer outro provider específico.

O resultado esperado é um **Cognitive Runtime provider-agnostic, capability-driven, context-efficient, evidence-aware e observable**.

---

# REGRAS INEGOCIÁVEIS

1. **Apenas software.** Não dependa de GPU, DGX, hardware específico ou infraestrutura inexistente para considerar a implementação concluída.
2. **Não crie uma arquitetura paralela.** Antes de adicionar qualquer módulo, procure abstrações existentes que já façam parte do trabalho.
3. **Preserve compatibilidade** de APIs, contratos públicos, schemas e comportamento existente sempre que houver caminho razoável.
4. **Provider/model IDs não pertencem ao core.** Detalhes como OpenAI, Ollama, vLLM, llama.cpp etc. devem ficar em adapters, manifests, registry ou configuração.
5. **Policy é hard constraint.** Score, custo ou conveniência nunca podem superar autorização, privacidade ou restrições de rede.
6. **`local_only` deve ser enforcement real e fail-closed.** Nunca faça fallback silencioso para cloud.
7. **Nenhum fallback pode enfraquecer permissões.** Uma falha não autoriza rede, ferramenta, provider ou ação anteriormente negada.
8. **Retries devem ser limitados e observáveis.** Proibido `retry until success` sem bound.
9. **Não invente métricas.** Meça baseline quando houver instrumentação; caso contrário, diga explicitamente que o dado ainda não existe.
10. **Não faça mega-refactor.** Entregue mudanças pequenas, testáveis e revisáveis em sequência lógica.
11. **Não pare no planejamento** quando houver caminho seguro para implementar e validar.
12. **Use os contratos reais do projeto.** Tipos ilustrativos deste prompt devem ser adaptados, não copiados cegamente.
13. **Não implemente subsistemas fora de escopo** só porque seriam interessantes futuramente.
14. **Toda decisão automatizada relevante deve ser explicável por reason codes ou dados equivalentes**, sem exigir exposição de raciocínio interno do modelo.

---

# FASE 0 — RECUPERAR E ENTENDER O ESTADO REAL

Antes de modificar qualquer arquivo:

```bash
git status
git diff
git diff --stat
git log -n 10 --oneline
```

Se houver trabalho interrompido ou alterações locais, classifique cada conjunto relevante como:

- `COMPLETE`
- `PARTIAL`
- `BROKEN`
- `UNRELATED`

Não descarte trabalho válido e não assuma que uma fase anterior terminou corretamente.

Depois, mapeie no código atual:

- cognitive/model routing;
- provider/model adapters;
- skill/tool registry;
- execution runtime;
- context construction;
- memory/retrieval;
- evidence/provenance/confidence;
- authorization/execution policy;
- failure/retry/reconciliation;
- caching existente;
- telemetry/logging/tracing;
- testes de contrato e integração relacionados.

## Saída obrigatória da discovery

Antes da implementação, produza um mapa curto contendo:

```text
Existing component -> responsabilidade atual -> lacuna -> extensão proposta -> arquivos afetados
```

Se já existir uma abstração equivalente à proposta abaixo, **estenda-a**. Não crie uma segunda versão.

---

# ARQUITETURA-ALVO

```text
User / Agent Request
        |
        v
Task / Intent Contract
        |
        v
Policy + Capability Requirements
        |
        v
Context Compiler <------ Memory Retrieval
        |                       |
        |                       v
        |                 Evidence / Provenance
        v
+------------------------------------------------+
|                Cognitive Router                |
|                                                |
|  hard constraints -> candidate filtering      |
|                   -> scoring                   |
|                   -> deterministic selection  |
|                   -> fallback plan             |
+-----------------------+------------------------+
                        |
                        v
               Execution Runtime
                 /             \
                v               v
         Model Backend       Skills / Tools
                \               /
                 v             v
              Evidence + Confidence
                        |
                        v
          Failure / Retry / Reconcile
                        |
                        v
                   Final Result
                        |
                        v
              Selective Memory Write
                        |
                        v
                 Decision Trace
```

A arquitetura deve permitir trocar providers/backends sem reescrever o domínio.

---

# FASE 1 — CAPABILITY MANIFESTS E EXECUTION REQUIREMENTS

## Problema

O runtime não deve escolher recursos por nomes específicos quando o que realmente precisa é de uma **capacidade**.

Exemplo de necessidade conceitual:

```text
reasoning: high
context: >= 32k
tools: required
privacy: local
latency: relaxed
cost: bounded
confidence: high
```

## Implementação

Estenda os contratos existentes para que modelos, backends e ferramentas possam declarar capabilities e restrições relevantes, por exemplo:

- classe de reasoning;
- capacidade de contexto;
- suporte a tool/function calling;
- locality;
- necessidade de network;
- classe de latência;
- custo relativo ou classe de custo;
- reliability metadata, quando mensurável;
- streaming/batching, quando relevante;
- limitações conhecidas;
- status/availability/freshness, quando aplicável.

A solicitação de execução deve expressar **requirements**, não nomes de fornecedor.

Exemplo conceitual — adapte aos contratos reais:

```ts
type CapabilityRequest = {
  reasoning: "low" | "medium" | "high";
  minContextTokens?: number;
  requiresTools?: boolean;
  privacy: "local" | "cloud_allowed";
  latencyClass: "interactive" | "batch";
  maxRelativeCost?: number;
  minConfidence?: number;
};

type ExecutionPolicy = {
  network: "allow" | "deny";
  providers: "local_only" | "local_preferred" | "any";
  externalTools: "allow" | "deny";
  memory: "local" | "configured";
};
```

## Acceptance criteria

- core/domain não precisa conhecer nomes de providers;
- manifests são validáveis;
- request inválido falha de forma tipada;
- policy e capability request podem ser testados separadamente;
- alterações antigas continuam funcionando via compatibilidade/defaults quando possível.

---

# FASE 2 — COGNITIVE ROUTER ADAPTATIVO

Transforme seleção de modelo/tool/backend em decisão determinística e explicável.

## Pipeline mínimo

```text
1. carregar candidates
2. aplicar hard constraints
3. rejeitar candidates incompatíveis com reason code
4. pontuar candidates restantes
5. desempatar deterministicamente
6. selecionar execução primária
7. preparar fallback elegível
8. emitir decision metadata
```

## Hard constraints primeiro

Exemplos:

- `local_only` elimina cloud;
- `network=deny` elimina recursos que precisam de egress;
- falta de tool support elimina modelo quando tools são obrigatórias;
- contexto insuficiente elimina candidato quando não existe estratégia segura de redução;
- permission denial elimina ferramenta independentemente do score.

Somente candidatos elegíveis podem ser pontuados.

## Scoring

Use sinais existentes ou introduza pesos configuráveis para fatores como:

- capability fit;
- reliability;
- contexto disponível;
- latência;
- custo;
- disponibilidade;
- preferência local;
- histórico operacional somente se já houver telemetria confiável.

Não use falsa precisão.

## Decisão conceitual

```ts
type RoutingDecision = {
  modelId: string;
  toolIds: string[];
  contextBudget: number;
  rationaleCodes: string[];
  fallbackPlan: string[];
};
```

Adapte aos tipos reais.

## Acceptance criteria

- mesma entrada + mesmo registry/policy state => mesma decisão;
- hard constraints sempre vencem scoring;
- reason codes mostram por que candidatos foram aceitos/rejeitados;
- ausência de candidato compatível produz erro tipado;
- não há fallback arbitrário para provider mais permissivo.

---

# FASE 3 — CONTEXT COMPILER + BUDGET EXPLÍCITO

O Jarvis não deve enviar histórico inteiro por padrão.

Construa o contexto por prioridade, incluindo apenas o necessário:

```text
1. system/runtime contract obrigatório
2. objetivo atual
3. estado mínimo da tarefa
4. evidence obrigatória
5. memórias relevantes
6. outputs recentes realmente necessários
7. contexto opcional enquanto houver budget
```

## Requisitos

- budget explícito por chamada;
- contabilização previsível de tamanho/tokens quando o provider permitir;
- ordenação estável de prioridades;
- tool outputs muito grandes devem ser reduzidos, resumidos ou referenciados antes da reinjeção;
- preservar provenance/source references mesmo quando conteúdo for compactado;
- conteúdo obrigatório nunca deve desaparecer silenciosamente para fazer a chamada caber;
- overflow deve produzir estratégia controlada ou falha tipada;
- memória recuperada também consome budget;
- evitar duplicação entre histórico, memória e evidence.

## Testes obrigatórios

- budget nunca é ultrapassado silenciosamente;
- itens obrigatórios têm precedência sobre opcionais;
- truncation/summarization preserva provenance;
- comportamento é determinístico para mesma entrada;
- context overflow aciona estratégia prevista, não crash genérico.

---

# FASE 4 — EVIDENCE E CONFIDENCE COMO CONTROLE DE EXECUÇÃO

Confidence não pode ser metadata decorativa.

O runtime deve transformar confidence/evidence em ação.

Exemplo conceitual:

```text
high confidence
    -> aceitar/continuar

medium confidence
    -> verificar / buscar evidence adicional

low confidence
    -> trocar estratégia, modelo ou ferramenta
    -> retry bounded quando justificável
    -> ou safe stop
```

Os thresholds devem vir de contratos/configuração existentes ou de uma policy explícita — nunca de números mágicos espalhados pelo código.

## Evidence

Toda evidence relevante deve apontar para provenance suficiente, como:

- tool invocation;
- source/document/resource;
- result identifier/hash;
- timestamp/freshness, quando relevante;
- processo de validação, quando existente.

## Regras

- não fabricar evidence;
- não inflar confidence porque a execução “parece correta”;
- evidence stale deve poder perder peso ou ser rejeitada;
- conflito entre evidências deve ser representável;
- ação tomada por confidence deve aparecer no decision trace.

---

# FASE 5 — FAILURE CLASSIFICATION + BOUNDED FALLBACK

Não repita a mesma execução cegamente.

Classifique falhas em categorias tipadas ou equivalentes aos contratos reais. Cobrir, no mínimo, os conceitos:

```text
transient_provider_error
provider_unavailable
context_overflow
capability_mismatch
tool_failure
policy_denial
low_confidence
invalid_output_contract
```

Associe cada classe a ações permitidas, por exemplo:

```text
retry same strategy
switch model
switch tool
recompile/reduce context
gather evidence
abort safely
```

## Regras

- máximo de tentativas/depth configurável;
- retry exige condição que possa plausivelmente mudar;
- `policy_denial` é terminal enquanto a policy não mudar por via autorizada;
- fallback não pode violar privacy/network/auth;
- fallback deve escolher apenas candidates previamente elegíveis ou reavaliados sob a mesma policy;
- cada transição deve ser rastreável;
- loops de fallback precisam ser detectados.

## Acceptance criteria

Um erro de provider, um overflow de contexto e uma negação de policy devem produzir comportamentos **diferentes e previsíveis**.

---

# FASE 6 — MEMÓRIA PERSISTENTE SELETIVA

O Jarvis não deve persistir cada turno indiscriminadamente.

## Read path

A recuperação deve ser:

- relevante para a tarefa atual;
- bounded;
- deduplicada;
- provenance-aware;
- sujeita ao context budget;
- sujeita à policy.

## Write gate

Antes de persistir algo, considere sinais como:

- relevância futura;
- novidade;
- confiança;
- provenance;
- duplicidade;
- estabilidade temporal;
- escopo correto.

A memória deve suportar dedupe/versionamento/invalidation de forma compatível com o design existente.

## Proibido

```text
persist every turn
persist tool noise
persist low-confidence claims as fact
use memory to bypass permissions
inject all memory into every prompt
```

## Acceptance criteria

- informação duplicada não cria crescimento desnecessário;
- memória de baixa confiança não vira fato silenciosamente;
- provenance continua disponível;
- retrieval respeita budget e isolamento de sessão/agente.

---

# FASE 7 — LOCAL-FIRST / CLOUD-OPTIONAL E SHARED INFERENCE

O runtime deve funcionar com diferentes backends por adapters/manifests/configuração.

## Provider abstraction

Trocar:

```text
provider A -> provider B
```

não deve exigir reescrever routing, memory, evidence ou orchestration.

## Shared inference

Vários agentes podem compartilhar:

- uma instância de backend;
- um model pool;
- scheduler/queue de inferência existente ou mínima abstração equivalente.

Mas devem permanecer isolados:

- session state;
- context;
- auth scope;
- memory scope;
- tool permissions;
- trace correlation.

Não use estado global mutável para dados específicos de agente.

## `local_only`

Quando ativado:

```text
cloud providers      -> ineligible
external network     -> denied
external tools       -> denied quando a policy assim determinar
compatible local mem -> required quando configurado
```

Se nenhum backend local elegível existir:

```text
FAIL CLOSED
```

Nunca:

```text
"local failed, trying cloud..."
```

sem alteração explícita e autorizada da policy.

Se o projeto diferenciar localhost, LAN e internet egress, preserve essa semântica e cubra-a em testes.

---

# FASE 8 — CACHE DETERMINÍSTICO PRIMEIRO

Antes de criar semantic cache complexo, implemente ou fortaleça cache determinístico compatível com a arquitetura atual.

A key precisa incorporar todos os fatores que alteram o resultado, quando relevantes:

- model/backend + versão;
- request normalizada;
- identidade/hash do contexto;
- policy;
- tool state/freshness;
- configuração relevante;
- versões de contracts/prompts;
- evidence freshness, quando aplicável.

## Regras

- cache nunca ignora auth/policy;
- dado stale não pode ser tratado como fresh;
- invalidação precisa ser explícita/testável;
- emitir hit/miss/invalidation telemetry;
- semantic cache só entra se já existir infraestrutura adequada ou por feature flag/opt-in claramente isolado.

---

# FASE 9 — DECISION TRACE E OBSERVABILIDADE

Cada execução deve poder responder, por dados estruturados e sem depender de chain-of-thought:

```text
Qual tarefa foi recebida?
Quais candidates estavam disponíveis?
Quais foram rejeitados e por quê?
Qual modelo/backend foi selecionado?
Quais tools foram autorizadas/selecionadas?
Qual context budget foi planejado e utilizado?
Houve cache hit/miss?
Quais evidence refs sustentaram a execução?
Qual confidence afetou o fluxo?
Houve retry/fallback?
Qual foi o motivo?
Qual foi o outcome?
Quanto tempo/custo relativo foi observado quando mensurável?
```

## Trace mínimo sugerido

- run/task ID;
- candidate set;
- rejection reason codes;
- selected model/backend;
- selected tools;
- routing rationale codes;
- context budget + actual usage;
- cache state;
- evidence refs;
- confidence state/action;
- retry/fallback path;
- timing;
- cost class/estimate somente quando realmente disponível;
- final outcome.

## Privacidade operacional

Não coloque por padrão em traces:

- secrets;
- tokens de autenticação;
- credenciais;
- raw sensitive tool payloads;
- prompt completo quando metadata/hash é suficiente.

---

# TESTES OBRIGATÓRIOS

Use a stack de testes existente. Não introduza framework de teste novo sem necessidade.

## Unit

Cubra pelo menos:

- manifest validation;
- capability filtering;
- hard constraints;
- deterministic scoring/tie-break;
- context budget;
- context priority;
- confidence -> action;
- failure classification;
- bounded retry/fallback;
- loop detection;
- memory write gate;
- memory dedupe;
- cache key/invalidation;
- `local_only` fail-closed;
- decision reason codes.

## Integration

Cubra pelo menos:

1. trocar provider/backend via adapter + manifest/config sem alterar core;
2. dois agentes compartilhando backend sem compartilharem estado privado;
3. provider failure acionando fallback permitido;
4. fallback mantendo auth/privacy/network policy;
5. `local_only` sem tentativa de cloud;
6. context overflow acionando recompilação/falha controlada;
7. low confidence acionando verificação/estratégia alternativa;
8. evidence/provenance sobrevivendo à compactação de contexto.

## Regression

Execute todas as verificações já definidas pelo projeto, incluindo as aplicáveis:

```text
unit tests
integration tests
contract tests
typecheck
lint
build
```

Não declare sucesso se uma verificação obrigatória falhar.

---

# MÉTRICAS: BASELINE -> AFTER

Quando o projeto já tiver como medir, registre antes/depois para:

- context tokens por execução;
- modelo/cost class selecionado;
- número de tool calls;
- número de retries;
- cache hit rate;
- duração total;
- fallback rate;
- memory writes por execução;
- candidate rejection distribution.

Não force metas percentuais sem baseline real.

O objetivo é tornar possível demonstrar empiricamente que o Jarvis está:

```text
usando menos contexto inútil
usando modelos maiores apenas quando necessário
repetindo menos trabalho
falhando de forma previsível
explicando suas decisões operacionais
```

---

# ORDEM DE EXECUÇÃO

Implemente nesta sequência, salvo dependência real encontrada durante discovery:

```text
1. capability contracts / manifests
2. adaptive cognitive routing
3. context compiler + budget
4. evidence/confidence control flow
5. typed failure + bounded fallback
6. selective persistent memory
7. local/shared inference abstraction
8. deterministic cache
9. decision trace + metrics
```

Cada fase deve:

```text
inspect -> implement smallest compatible diff -> targeted tests -> fix -> continue
```

Não acumule nove fases sem testes intermediários.

---

# STOP CONDITIONS

Pare a alteração específica e reporte claramente quando:

- uma migração quebraria API pública sem compatibility path;
- existe conflito semântico entre contratos reais do projeto;
- o comportamento esperado não pode ser inferido com segurança;
- testes mostram uma regressão arquitetural que exige decisão de design maior;
- seria necessário enfraquecer policy para fazer a feature funcionar.

Nesses casos:

1. preserve o comportamento existente;
2. documente o blocker;
3. implemente o incremento seguro mais próximo, quando possível;
4. não esconda a limitação com fallback silencioso.

---

# FORA DE ESCOPO DESTA EXECUÇÃO

Não desvie a implementação para:

- scheduler genérico;
- self-learning/reinforcement automático;
- auto-modificação irrestrita de código;
- federation/distributed nodes;
- n8n;
- HUD/UI;
- novo framework multiagente;
- hardware provisioning;
- benchmarking de hardware;
- funcionalidades puramente cosméticas.

Esses temas podem existir futuramente, mas não devem bloquear nem diluir este upgrade do runtime.

---

# DEFINITION OF DONE

A execução só está concluída quando, dentro do escopo realmente implementado:

- [ ] model/tool/backend selection é capability-driven;
- [ ] hard policy constraints precedem scoring;
- [ ] core não possui dependência desnecessária de provider específico;
- [ ] routing é determinístico para mesmo estado;
- [ ] context compiler possui budget explícito;
- [ ] evidence/provenance é preservada;
- [ ] confidence altera control flow;
- [ ] falhas são classificadas de forma útil;
- [ ] retries/fallbacks são bounded;
- [ ] fallback não enfraquece policy;
- [ ] memória é seletiva e provenance-aware;
- [ ] shared inference não cruza estados de agentes;
- [ ] `local_only` é fail-closed e testado;
- [ ] cache respeita freshness/auth/policy;
- [ ] decision trace explica seleção e fallback sem expor chain-of-thought;
- [ ] testes novos relevantes foram adicionados;
- [ ] regressões existentes foram verificadas;
- [ ] docs/config/defaults/migration notes foram atualizados quando necessário;
- [ ] nenhuma métrica foi inventada.

---

# FORMATO DO RELATÓRIO FINAL

Ao terminar, responda exatamente com estas seções:

## 1. Estado inicial

- branch/HEAD;
- working tree encontrado;
- trabalho interrompido recuperado, se houver;
- principais contratos reutilizados.

## 2. Mapa arquitetural

- componentes existentes;
- extensões realizadas;
- dependências relevantes;
- decisões de compatibilidade.

## 3. Alterações

Para cada mudança:

```text
arquivo -> alteração -> motivo -> contrato afetado
```

## 4. Testes e validações

Liste comandos executados e resultado real.

Não escreva `passed` para teste que não foi executado.

## 5. Métricas

Apresente baseline/after apenas onde existirem dados reais.

## 6. Riscos residuais

Somente riscos concretos e ainda existentes.

## 7. Próximo passo prioritário

Escolha **um** próximo incremento de maior impacto e explique por quê.

---

# PRINCÍPIO CENTRAL

Não maximize quantidade de agentes, modelos ou ferramentas.

Maximize a qualidade da decisão do runtime:

```text
menor recurso capaz de cumprir o contrato
+ contexto mínimo suficiente
+ evidence suficiente
+ policy preservada
+ fallback previsível
+ estado isolado
+ resultado observável
```

O Jarvis deve ser capaz de usar um modelo pequeno quando ele basta, escalar quando a tarefa exige, operar localmente quando a policy exige e explicar operacionalmente **o que selecionou, por que selecionou e o que fez quando algo falhou**.
