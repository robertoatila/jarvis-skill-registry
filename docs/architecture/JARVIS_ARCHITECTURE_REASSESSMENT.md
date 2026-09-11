> **Historical reference — 2026-09-11:** The [canonical forward roadmap](../roadmap/JARVIS_AUTONOMOUS_INTELLIGENCE_PLAN.md) supersedes older phase sequences and maturity claims in this document. Counts, benchmarks and certification statements below retain their historical scope; they do not certify the recovered current runtime. See the roadmap for current evidence and unresolved integration gaps.

# J.A.R.V.I.S. // Reavaliação Crítica da Arquitetura de Evolução Autônoma
**Documento Canônico:** `docs/architecture/JARVIS_ARCHITECTURE_REASSESSMENT.md`  
**Data:** 10 de Setembro de 2026  
**Status:** RATIFICADO // REVISÃO ARQUITETURAL SOBERANA  
**Escopo:** Repositório `robertoatila/jarvis-skill-registry`  
**Regra Operacional:** Não implementar código de produção nesta fase. Revisão analítica, validação empírica e saneamento de dependências.

---

## 1. Inspeção do Estado Real do Repositório

Foi realizada uma varredura forense completa em todas as árvores de implementação do repositório:
- `tooling/agentic/` (26 módulos Python 3.12 pure standard library)
- `tests/` (25 suítes de testes automatizados, 134 testes)
- `schemas/` (116 esquemas JSON)
- `config/` (`api_keys.json`, `policy.json`, `registry.json`)
- `state/` (`checkpoints/`, `learning/`, `telemetry/`, `quantum-agent-ledger.jsonl`)
- `ui/` (`index.html`, `jarvis.js`, `jarvis.css`)

### Matriz de Classificação das 25 Capacidades

```text
Classificações:
EXISTS       ── Implementado e testado no código atual.
PARTIAL      ── Parcialmente implementado, incompleto ou não integrado ao loop principal.
EQUIVALENT   ── Implementado sob outro nome ou paradigma (ex.: PowerShell/JSONL).
MISSING      ── Ausente como componente formal de primeira classe.
CONFLICTING  ── Múltiplas implementações competindo pela mesma autoridade.
OBSOLETE     ── Legado não utilizado pelo runtime ativo.
```

| # | Capacidade | Classificação | Localização no Código Real | Evidência / Diagnóstico Técnico |
| :--- | :--- | :--- | :--- | :--- |
| **01** | **Runtime State** | `PARTIAL` | `tooling/agentic/models.py`<br/>`resilience.py` | Estados de enum (`TaskStatus`, `MissionStatus`) existem e `MissionCheckpoint` salva snapshots em JSON. Contudo, não há um State Store unificado autoritativo em tempo de execução; a execução em `runtime.py` mantém variáveis em memória e dispersa eventos. |
| **02** | **Mission/Task Execution** | `EXISTS` | `tooling/agentic/runtime.py`<br/>`dag.py` | `JarvisAgenticRuntime.execute_goal` orquestra as fases da missão sobre `TaskNode` e `ExecutionDAG`. Realiza execução de comandos reais via `InfrastructureSkillDriver`. |
| **03** | **Agents** | `EXISTS` | `tooling/agentic/profiles.py`<br/>`delegator.py` | 4 agentes quânticos canônicos (`Quantum-AuditAgent`, etc.) e registro `AgentProfileRegistry`. 4 topologias de swarm (`MESH`, `HIERARCHICAL`, `ORCHESTRATOR`, `SWARM`). |
| **04** | **Skills** | `EXISTS` | `skills/` (154 skills)<br/>`progressive_disclosure.py`<br/>`composite.py` | 154 skills canônicas em disco. Motores de divulgação progressiva, habilidades compostas e ciclo de vida. |
| **05** | **Resolver** | `EXISTS` | `tooling/agentic/planner_resolver.py` | `AutonomousSkillResolver` com 14 regras determinísticas de resolução, desempate por fitness, localidade e trust tier. |
| **06** | **Policy & Authorization** | `MISSING` | `config/policy.json` (apenas catálogo) | **LACUNA CRÍTICA**: Existe apenas um arquivo de 11 linhas para governança estática de catálogo. Não existe um `PolicyEngine` em tempo de execução interceptando chamadas para validar permissões de agentes, escopos ou níveis de risco. |
| **07** | **Permissions** | `PARTIAL` | `tooling/agentic/profiles.py` | `AgentConstraints` declara `read_only` e `network_access`, e `TaskNode` possui `read_scopes` e `write_scopes`. Porém, nenhum módulo bloqueia ativamente um processo que escreva fora de seu escopo declarado durante o `subprocess.Popen`. |
| **08** | **Verification** | `EXISTS` | `tooling/agentic/verification.py` | `VerificationEngine` com 9 tipos de checagem concreta, hash SHA-256 de evidência e garantia estrita fail-closed ($Task\ Execution \neq Task\ Verification$). |
| **09** | **Artifacts** | `PARTIAL` | `tooling/agentic/models.py` | `TaskNode.artifacts` é apenas uma lista de strings (`List[str]`). Não há classe `Artifact` formalizando hash, produtor, metadados, ambiente e integridade. |
| **10** | **Provenance** | `PARTIAL` | `tooling/agentic/verification.py`<br/>`learning.py` | Hashes de evidência são gerados individualmente, mas não há um encadeamento criptográfico formal ligando Tarefa ──> Artefato ──> Verificação ──> Commit. |
| **11** | **Telemetry** | `EXISTS` | `tooling/agentic/telemetry.py` | `TelemetryCollector` com spans compatíveis com OpenTelemetry, contagem de tokens, latências e persistência em `telemetry_spans.jsonl`. |
| **12** | **Persistence** | `CONFLICTING` | `audit/events.jsonl`<br/>`transactions/journal.jsonl`<br/>`state/checkpoints/`<br/>`state/quantum-agent-ledger.jsonl` | Múltiplos mecanismos de persistência competem sem hierarquia definida. Não está formalizado quem é a fonte de verdade do estado operacional vs auditoria vs cache. |
| **13** | **Retries** | `EXISTS` | `tooling/agentic/resilience.py`<br/>`goal_loop.py` | `FailureRecoveryEngine` calcula backoff exponencial, rastreia limites de tentativas (`max_retries`) e gera ações de recuperação. |
| **14** | **Budgets** | `PARTIAL` | `tooling/agentic/budgets.py` | `BudgetTracker` implementa circuit breaker com limites de tokens, tempo e custo. Contudo, **NÃO está conectado** ao loop de execução em `runtime.py`. |
| **15** | **Configuration** | `MISSING` | Múltiplos arquivos | Caminhos (`REGISTRY_ROOT = Path("E:/.skill-registry")`) e constantes estão hardcoded em mais de 15 arquivos Python independentes, sem um carregador unificado. |
| **16** | **Schemas** | `PARTIAL` | `schemas/` (116 arquivos)<br/>`models.py` | 116 esquemas JSON existem no disco, mas os modelos Python executam apenas validação superficial de string (`schema_version == "1.0.0"`). |
| **17** | **Migrations** | `MISSING` | Inexistente | Não há versionamento retrocompatível, transformadores de dados ou rotinas de migração para registros persistidos em disco. |
| **18** | **Security** | `PARTIAL` | `audit_pre_publish_security.py`<br/>`infrastructure.py` | Varredura estática pré-publicação excelente (14 invariantes SSP-v13.2). Porém, o driver de subprocessos usa `shell=True` com blacklist de apenas 7 comandos regex. |
| **19** | **Secrets** | `PARTIAL` | `config/api_keys.example.json` | Protegidos no `.gitignore` e na auditoria estática. Falta sanitização ativa em runtime para evitar vazamento em saídas de ferramentas que vão para a telemetria ou Obsidian. |
| **20** | **MCP** | `EXISTS` | `tooling/jarvis_mcp_server.py`<br/>`McpApiGateway.psm1` | Gateway MCP stdio/SSE com ferramentas operacionais e integração com o cockpit. |
| **21** | **External Tools** | `PARTIAL` | `tooling/agentic/infrastructure.py` | Execução direta de comandos via subprocesso local sem sandboxing de sistema operacional (Job Objects no Windows ou cgroups no Linux). |
| **22** | **Swarm** | `EXISTS` | `tooling/agentic/delegator.py` | Orquestração multiagente com matriz de topologias (`MESH`, `HIERARCHICAL`, `ORCHESTRATOR`, `SWARM`). |
| **23** | **Federation** | `PARTIAL` | `tooling/agentic/federation.py` | Roteamento e registro de nós (`FederationRouter`). Porém, confia em anúncios locais sem autenticação mTLS ou validação criptográfica de identidade. |
| **24** | **HUD** | `EXISTS` | `ui/index.html`<br/>`ui/jarvis.js`<br/>`jarvis_server.py` | Cockpit operacional na porta 8899 com visualização de ondas de execução, telemetria em tempo real e acessibilidade WCAG 2.1 AA. |
| **25** | **Cognitive Vault** | `EXISTS` | `vault.py`<br/>`00 - J.A.R.V.I.S. Cognitive Vault.md` | 20 Mapas de Conteúdo (MOCs), visualização em grafo galáxia e exportação de heurísticas validadas para o Obsidian. |

---

## 2. Validação das Dependências Arquiteturais

### O Grafo de Dependências Reais

```text
┌─────────────────────────┐
│     POLICY ENGINE       │◄─────────────────────────────┐
└────────────┬────────────┘                              │
             │ autoriza                                  │
             ▼                                           │
┌─────────────────────────┐     valida escopos           │
│   PERSISTENT STATE      │──────────────────────────────┤
└────────────┬────────────┘                              │
             │ armazena                                  │
             ▼                                           │
┌─────────────────────────┐                              │
│      ARTIFACTS &        │                              │
│       PROVENANCE        │                              │
└────────────┬────────────┘                              │
             │ produz                                    │
             ▼                                           │
┌─────────────────────────┐                              │
│  VERIFICATION ENGINE    │                              │
└────────────┬────────────┘                              │
             │ gera evidência confiável                  │
             ▼                                           │
┌─────────────────────────┐                              │
│        TELEMETRY        │                              │
└────────────┬────────────┘                              │
             │ alimenta métricas                         │
             ▼                                           │
┌─────────────────────────┐     guia planejamento        │
│      SKILL FITNESS      │──────────────────────────────┘
└────────────┬────────────┘
             │ seleciona melhor ferramenta
             ▼
┌─────────────────────────┐
│    LEARNING RECORDS     │
└────────────┬────────────┘
             │ sintetiza heurísticas
             ▼
┌─────────────────────────┐
│       ADAPTATION        │
└─────────────────────────┘
```

---

## 3. Inversões Críticas Identificadas no Roadmap Original

Analisando a sequência das 29 fases propostas originalmente, foram identificadas **6 inversões graves de causalidade arquitetural**:

### Inversão 1: `Skill Fitness` (Fase 08) e `Experiments` (Fase 09) antes de `Verification` (Fase 19)
- **Problema**: O motor de Fitness calcula o score de uma habilidade a partir da sua taxa de sucesso em verificação (`verification_pass_rate`). Na ordem original, Fitness foi construído na Fase 08, enquanto o `VerificationEngine` só apareceu na Fase 19!
- **Consequência**: Durante 11 fases, o sistema calculou scores e realizou experimentos baseando-se em suposições não verificadas ou mocks de sucesso, violando o princípio fundamental da evidência confiável.
- **Correção**: `Verification & Evidence` deve ser adiantado para a camada de Fundação (antes de qualquer cálculo de métricas ou fitness).

### Inversão 2: `Learning Records` (Fase 12) antes de `Verification & Evidence` (Fase 19)
- **Problema**: `LearningRecord` exige um payload de `evidence: Dict[str, Any]`. Na fase 12, esse payload era arbitrário porque o modelo canônico de evidência só foi concebido na fase 19.
- **Consequência**: O sistema tenta registrar "aprendizado" antes de ter a ferramenta necessária para provar que a abordagem executada realmente funcionou.
- **Correção**: A extração de heurísticas e aprendizado só pode ocorrer sobre tarefas formalmente certificadas pelo `VerificationEngine`.

### Inversão 3: `Autonomous Goal Loop` (Fase 10) antes de `Recovery` (Fase 21) e `Budgets` (Fase 22)
- **Problema**: Liberar autonomia sem circuit breaker (`BudgetTracker`) e sem persistência tolerante a falhas (`FailureRecoveryEngine`) cria o risco imediato de loops infinitos, consumo descontrolado de tokens ou estado corrompido em caso de interrupção abrupta.
- **Consequência**: Autonomia sem salvaguardas de infraestrutura básica.
- **Correção**: Circuit breakers de orçamento e recuperação atômica devem existir antes de se habilitar o loop autônomo.

### Inversão 4: `Infrastructure Skills` (Fase 15) sem `Policy Engine` ou `Approval Gates`
- **Problema**: O driver de infraestrutura executa comandos de shell (`shell=True`). Sem um motor de políticas e sem portões de aprovação baseados em risco, o runtime confia exclusivamente em uma blacklist de 7 expressões regulares, sem verificar se o agente solicitante possui autorização para tal operação.
- **Consequência**: Risco de escalada de privilégios e mutação indevida de ambiente.
- **Correção**: O `Policy & Authorization Engine` deve preceder qualquer driver de execução de comandos.

### Inversão 5: `Multi-Node Federation` (Fase 16) antes de `Verification` e `Artifact Provenance`
- **Problema**: Federar nós remotos sem modelo canônico de artefato e sem verificação estrita permite que um nó remoto retorne qualquer payload que será aceito sem validação de integridade.
- **Consequência**: Propagação de código ou estado não verificado pela rede.
- **Correção**: Federação deve ser classificada como funcionalidade avançada e depender de modelos estáveis de proveniência e verificação local.

### Inversão 6: `Restart Resilience` (Fase 21) após `Runtime End-to-End` (Fase 20)
- **Problema**: A capacidade de pausar, salvar e retomar uma missão após falha ou reinicialização foi tratada como um "adicional" na fase 21, após a montagem do runtime.
- **Consequência**: O agendador de ondas foi construído primariamente em memória, exigindo adaptações tardias para recuperar tarefas interrompidas.
- **Correção**: O estado de execução deve ser persistente e transacional desde o núcleo do agendador.

---

## 4. Lacunas Arquiteturais de Primeira Classe

### A. Policy & Authorization Engine (Ausente)

O runtime necessita de um componente central de autorização que avalie deterministicamente a tupla:

$$\text{EvaluatePolicy}(\text{Agent}, \text{Action}, \text{Tool/Skill}, \text{Resource}, \text{Mission}, \text{RiskLevel}) \to \{\text{ALLOW}, \text{DENY}, \text{REQUIRE\_APPROVAL}\}$$

#### Escopos Mandatórios:
1. **Filesystem**: Validação estrita de que caminhos em `read_scopes` e `write_scopes` estão contidos em `REGISTRY_ROOT` (anti path-traversal e symlink-escape).
2. **Network**: Bloqueio de conexões externas quando `network_access == False`; validação de domínio em caso positivo.
3. **Shell Commands**: Whitelist estrita baseada no perfil do agente; proibição de comandos com privilégios de administrador ou destrutivos.
4. **Approval Gates**: Interrupção síncrona aguardando assinatura do operador para ações de risco elevado (R4/R5).

---

### B. Modelo Canônico de Artefatos & Proveniência (Parcial)

Substituir `TaskNode.artifacts: List[str]` por uma entidade canônica:

```python
@dataclass
class Artifact:
    artifact_id: str             # art-uuid
    mission_id: str              # mis-uuid
    task_id: str                 # tsk-01
    producer: str                # runtime:Quantum-AuditAgent
    artifact_type: str           # SOURCE_CODE | CONFIG | TEST_REPORT | METRIC | BINARY
    path: str                    # Caminho relativo normalizado
    size_bytes: int              # Tamanho exato
    sha256: str                  # Hash criptográfico do conteúdo
    environment: Dict[str, str]  # OS, Python version, platform
    verification_state: str      # UNVERIFIED | VERIFIED | REJECTED
    created_utc: str             # ISO-8601 UTC
    parent_artifacts: List[str]  # Cadeia de proveniência
```

---

### C. Modelo de Estado do Runtime (Fontes de Verdade Claras)

Para eliminar conflitos entre múltiplos arquivos de estado e ledgers, define-se a taxonomia formal de dados:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 1. AUTHORITATIVE STATE (Fonte da Verdade Única da Operação)             │
│    - state/missions/{mission_id}.json                                  │
│    - Contém: Mission, DAG completo, TaskNodes, Status, Bindings.       │
│    - Mutação: Somente via escrita atômica transacional (.tmp -> .json). │
├────────────────────────────────────────────────────────────────────────┤
│ 2. AUDIT EVENTS (Histórico Imutável Append-Only / Não-Autoritativo)     │
│    - state/telemetry/telemetry_spans.jsonl                             │
│    - audit/events.jsonl                                                │
│    - state/quantum-agent-ledger.jsonl                                  │
│    - Papel: Auditoria forense, observabilidade e telemetria.           │
│    - Invariante: Nunca utilizado para carregar o estado da missão.     │
├────────────────────────────────────────────────────────────────────────┤
│ 3. DERIVED STATE (Projeções Computadas a partir da Fonte da Verdade)   │
│    - state/telemetry/skill_fitness.json                                │
│    - state/learning/validated_heuristics.json                          │
│    - Papel: Otimização de consultas do Resolver e estatísticas.        │
│    - Invariante: Pode ser reconstruído a qualquer momento dos logs.     │
├────────────────────────────────────────────────────────────────────────┤
│ 4. CACHE (Descartável sem perda de corretude)                          │
│    - cache/catalog_index.json                                          │
│    - In-memory AST representations                                     │
└────────────────────────────────────────────────────────────────────────┘
```

---

### D. Estratégia de Schema & Migrações (Ausente)

Todos os modelos persistentes (`Mission`, `TaskNode`, `AgentProfile`, `Artifact`, `LearningRecord`) devem implementar:
1. `schema_version` semântico (`X.Y.Z`).
2. **Regra de Aditividade**: Campos novos devem possuir valores padrão seguros; campos desconhecidos em leituras são preservados sem causar falha.
3. **Pipeline de Migração**: O módulo `SchemaMigrator` aplicará transformadores sequenciais quando `stored_version < current_version`.
4. **Quarentena de Corrupção**: Se um arquivo `.json` estiver sintaticamente corrompido, o runtime deve movê-lo para `state/corrupted/{timestamp}_{filename}` e abortar a operação com erro explícito, sem sobrescrever o arquivo original.

---

### E. Modelo de Configuração Canônica (Ausente)

Centralizar parâmetros operacionais em um único ponto: `JarvisRuntimeConfig`.

Substituir constantes espalhadas por injeção controlada de dependências:
- Diretórios base (`registry_root`, `state_dir`, `skills_dir`, `cache_dir`).
- Limites de timeout e concorrência máxima.
- Configuração de telemetria e sinks de log.
- Flags de modo de segurança (`FAIL_CLOSED`, `OFFLINE_ONLY`, `STRICT_SANDBOX`).

---

## 5. Classes de Risco Operacional (R0 – R5)

O runtime adota formalmente a matriz de 6 classes de risco:

```text
┌──────┬───────────────────────────────┬───────────────────────────────────────────┐
│ R0   │ Read-Only                     │ Leitura de repositório, AST, inspeção     │
│      │                               │ ──> AUTO-APROVADO (conforme escopo)       │
├──────┼───────────────────────────────┼───────────────────────────────────────────┤
│ R1   │ Local Reversible Write        │ Escrita em /tmp, telemetria, checkpoints  │
│      │                               │ ──> AUTO-APROVADO em pastas de estado     │
├──────┼───────────────────────────────┼───────────────────────────────────────────┤
│ R2   │ Repository Mutation           │ Edição de arquivos na árvore de trabalho  │
│      │                               │ ──> AUTO-APROVADO; exige verificação      │
├──────┼───────────────────────────────┼───────────────────────────────────────────┤
│ R3   │ External Side Effect          │ HTTP request, download, chamada a API     │
│      │                               │ ──> EXIGE network_access + whitelist      │
├──────┼───────────────────────────────┼───────────────────────────────────────────┤
│ R4   │ Infra / Security Mutation     │ Instalação de pacote, ajuste de políticas │
│      │                               │ ──> EXIGE APROVAÇÃO DO OPERADOR           │
├──────┼───────────────────────────────┼───────────────────────────────────────────┤
│ R5   │ Destructive / Irreversible    │ git push, delete de recurso, formatação   │
│      │                               │ ──> BLOQUEADO DE MODO AUTÔNOMO            │
│      │                               │     Exige autorização interativa manual   │
└──────┴───────────────────────────────┴───────────────────────────────────────────┘
```

---

## 6. Ciclo de Vida dos Approval Gates

Para operações R4 e R5, implementa-se o autômato finito de aprovação:

```text
       ┌───────────┐
       │ REQUESTED │
       └─────┬─────┘
             │
             ▼
      ┌─────────────┐
      │ PENDING_ACK │─────── timeout (300s) ──────► ┌─────────┐
      └──────┬──────┘                              │ EXPIRED │
             │                                     └─────────┘
      ┌──────┴──────┐
      │             │
      ▼             ▼
┌──────────┐  ┌──────────┐
│ APPROVED │  │  DENIED  │
└─────┬────┘  └──────────┘
      │
      ▼
┌───────────┐
│ EXECUTED  │
└───────────┘
```

**Regra Soberana de Não-Auto-Concessão**:
Um Goal ou Tarefa autônoma **NUNCA** pode aprovar sua própria solicitação de privilégios ou assinar seu próprio token de autorização. Toda aprovação R4/R5 exige assinatura criptográfica ou input direto do operador humano.

---

## 7. Auditoria de Determinismo

Foram identificadas e mapeadas as seguintes fontes de não determinismo:

| Fonte no Código | Impacto | Mitigação Arquitetural |
| :--- | :--- | :--- |
| `uuid.uuid4()` | IDs aleatórios impedem replay determinístico de missões em testes | Implementar `IdProvider` com suporte a seeds determinísticas para suítes de teste. |
| `time.time()` / `time.perf_counter()` | Timestamps variáveis afetam scores de decay e medições | Implementar abstração `Clock` injetável para testes. |
| `Path.glob()` / `os.listdir()` | Ordem de retorno depende da tabela de arquivos do sistema operacional | Aplicar `sorted()` estrito em todas as listagens de catálogo e arquivos. |
| Iteração sobre `set` e `dict` | Ordem indefinida pode afetar a ordem de agendamento de tarefas | Ordenação ordinal determinística de IDs em todas as coleções de agendamento. |
| Resolução de empate de skills | Risco de escolha arbitrária | Regra canônica de desempate: Maior Fitness ──> Menor Latência ──> Maior Versão Semântica ──> Ordem Lexicográfica de `skill_id`. |

---

## 8. Auditoria de Recuperação & Classificação de Efeitos Colaterais

| Categoria de Ação | Exemplo de Operação | Semântica de Recuperação |
| :--- | :--- | :--- |
| **IDEMPOTENT** | Cálculo de AST, hashing de arquivo, leitura de catálogo, checagem de verificação | Repetir a execução livremente a qualquer momento sem efeitos adversos. |
| **RETRY_SAFE** | Compilação de código (`py_compile`), execução de suíte de testes unitários | Seguro para nova tentativa em caso de falha transitória ou timeout. |
| **REQUIRES_IDEMPOTENCY_KEY** | Registro de span de telemetria, criação de Learning Record, emissão de webhook | Exige deduplicação via `task_id` / `span_id` para evitar registros duplicados. |
| **REQUIRES_COMPENSATION** | Criação ou modificação de arquivo no workspace durante tarefa que falhou | Exige ação de compensação (rollback para snapshot prévio ou remoção do arquivo parcial). |
| **NOT_SAFE_TO_RETRY** | Operações destrutivas ou requisições HTTP mutantes não idempotentes | Falha imediata sem repetição automática; exige intervenção do operador. |

---

## 9. Classificação Estratégica: MVP vs Advanced

Para assegurar estabilidade sem inflar desnecessariamente o escopo inicial, as capacidades são distribuídas em camadas:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        CAMADAS ARQUITETURAIS                           │
├────────────────────────────────────────────────────────────────────────┤
│ 1. FOUNDATION (Mandatório no MVP)                                      │
│    - Baseline, Contratos, Schemas, Policy Engine (R0-R5),              │
│      Persistent State, Artifact & Provenance, Verification Engine.     │
├────────────────────────────────────────────────────────────────────────┤
│ 2. CORE RUNTIME (Mandatório no MVP)                                    │
│    - Agent Profiles, Progressive Disclosure (L0-L2), Telemetry,        │
│      Budgets / Circuit Breaker, Wave Scheduler, Restart Resilience.    │
├────────────────────────────────────────────────────────────────────────┤
│ 3. INTELLIGENCE (Mandatório para a Promessa Autônoma)                  │
│    - Repository Intelligence, Planner/Resolver, Skill Fitness,         │
│      Experiments, Autonomous Goal Loop, Learning Records.              │
├────────────────────────────────────────────────────────────────────────┤
│ 4. LIFECYCLE & INTERFACE (Consolidação do Sistema)                     │
│    - Skill Promotion, Package Manager, Cybernetic HUD Cockpit,         │
│      Obsidian Cognitive Vault Bridge.                                  │
├────────────────────────────────────────────────────────────────────────┤
│ 5. ADVANCED / DEFERRED (Pós-MVP // Não bloqueia lançamento)            │
│    - n8n Workflow Adapter (Integração externa de terceiros)            │
│    - Infrastructure Subprocess Mutations (Comandos de alto risco)       │
│    - Multi-Node Distributed Federation (Consenso e rede remota)        │
└────────────────────────────────────────────────────────────────────────┘
```

> [!IMPORTANT]
> **Decisão Arquitetural Recomendada**:
> Funcionalidades como **n8n Adapter** e **Multi-Node Federation** trazem superfícies de ataque externas e complexidade distribuída. Devem ser postergadas até que o núcleo local (Foundations + Core Runtime + Intelligence) esteja 100% endurecido, garantindo um produto inicial extremamente robusto e focado.

---

## 10. O Novo DAG do Roadmap Proposto (33 Fases Reordenadas)

A reordenação abaixo resolve todas as 6 inversões de dependência identificadas:

```text
00 Baseline & Diagnostic Verification
01 Canonical Architecture Contracts & Schema Strategy
02 Policy, Authorization & Risk Model (R0-R5)
03 Mission Model & Execution DAG
04 Persistent Runtime State & Checkpoint Store
05 Artifact & Cryptographic Provenance Model
06 Verification & Evidence Engine
07 Agent Profiles & Boundary Enforcers
08 Composite Skills & Dependency Graph
09 Progressive Disclosure Engine (L0/L1/L2)
10 Agentic Telemetry & OTEL Spans
11 Runtime Budgets & Circuit Breakers
12 Wave Scheduler with Scope Isolation
13 Failure Recovery & Restart Resilience
14 Repository Intelligence & AST Scanner
15 Autonomous Mission Planner & Skill Resolver
16 Skill Fitness Engine (Baseado em Evidências Verificadas)
17 Skill Experiment Engine (Testes A/B)
18 Software Engineering Orchestrator
19 Autonomous Goal Loop (Ciclo Fechado Seguro)
20 Learning Records & Heuristics Promotion
21 Skill Promotion & Deprecation Lifecycle
22 Cognitive Package Manager
23 Cybernetic HUD Cockpit (Visualização de Ondas e Métricas)
24 Obsidian Cognitive Vault Bridge
25 n8n Workflow Adapter [EXTERNO]
26 Infrastructure Skill Driver [MUTANTE]
27 Multi-Node Federation [DISTRIBUÍDO]
28 End-to-End Autonomous Runtime Integration
29 Automated Quality Review & Security Audit
30 Chaos & Fault Injection Testing
31 Canonical Documentation & Specification
32 Release Candidate Certification
```

### Detalhamento das Relações do Novo DAG (Fases Chave)

- **Fase 02 (Policy Engine)**:
  - *requires*: Fase 01 (Contracts)
  - *produces*: Avaliador de autorização, delimitador de escopos e regras de risco R0-R5.
  - *unblocks*: Fases 04, 07, 12, 18, 26.
- **Fase 04 (Persistent Runtime State)**:
  - *requires*: Fases 01, 02, 03.
  - *produces*: Armazenamento transacional atômico de missões e tarefas em disco.
  - *unblocks*: Fases 05, 06, 12, 13.
- **Fase 05 (Artifact & Provenance)**:
  - *requires*: Fase 04.
  - *produces*: Entidade `Artifact` canônica com SHA-256 e rastreabilidade de produtor.
  - *unblocks*: Fases 06, 13, 20.
- **Fase 06 (Verification & Evidence)**:
  - *requires*: Fases 04, 05.
  - *produces*: Prova determinística de conclusão de tarefas com evidência criptográfica.
  - *unblocks*: Fases 10, 16, 17, 18, 19, 20.
- **Fase 11 (Budgets & Circuit Breaker)**:
  - *requires*: Fase 03.
  - *produces*: Interrupção fail-closed contra loops infinitos e estouro de tokens/custo.
  - *unblocks*: Fases 12, 13, 19.
- **Fase 16 (Skill Fitness)**:
  - *requires*: Fases 06 (Verification) e 10 (Telemetry).
  - *produces*: Scores empíricos fundamentados em evidências reais de sucesso.
  - *unblocks*: Fases 17, 18, 19.

---

## 11. Performance Baseline & Diagnóstico Empírico

| Métrica de Desempenho | Valor Mensurado | Status Atual | Evidência / Metodologia |
| :--- | :--- | :--- | :--- |
| **Progressive Disclosure Token Savings** | **-95.48% (22.13x economia)** | `BASELINE_VERIFIED` | 464.389 tokens monolíticos ──> 20.987 tokens (L0+L2) medidos nas 154 skills em `benchmarks/token_benchmark_report.json`. |
| **System Test Battery Duration** | **3.54 segundos** | `BASELINE_VERIFIED` | 134 testes automatizados em 25 suítes (`run_tests.py`) em Python 3.12 pure stdlib (~26.4ms/teste). |
| **Pre-Publish Security Scan** | **~1.2 segundos** | `BASELINE_VERIFIED` | 1.440 arquivos elegíveis inspecionados (65.9 MB) em `audit_pre_publish_security.py`. |
| **AST Repository Indexing Latency** | `BASELINE_NOT_AVAILABLE` | `PENDING_BENCHMARK` | Não mensurado formalmente para repositórios acima de 100k linhas de código. |
| **Wave Scheduler Graph Planning Time** | `BASELINE_NOT_AVAILABLE` | `PENDING_BENCHMARK` | Não mensurado formalmente para grafos com mais de 50 tarefas concorrentes. |
| **Telemetry Append Disk Overhead** | `BASELINE_NOT_AVAILABLE` | `PENDING_BENCHMARK` | Requer teste de carga sob alta concorrência de I/O em JSONL. |

---

## 12. Critérios e Próximos Passos para a Continuidade

1. **Ratificação dos Contratos Canônicos Fundamentais**:
   - `docs/architecture/RUNTIME_EXECUTION_CONTRACT.md` (Ciclo de Vida, `ExecutionAttempt`, Idempotência, Reconciliação e Planos de Controle/Execução/Evidência)
   - `docs/architecture/FAILURE_SEMANTICS.md` (Taxonomia `FailureClass`, Atribuição de Falha, Matriz de Retry, Replay Determinístico e Regra de Ouro da Compensação)
   - `docs/security/TRUST_BOUNDARIES.md` (Interseção Estrita de Autorização, Matriz de Confiança, Proveniência Instrucional e Referência Segura a Segredos)
2. **Aprovação do Operador**: O operador deve avaliar esta reavaliação arquitetural e os contratos formalizados.
3. **Formalização do Modelo de Artefatos (Fase 05)**: Concluída com a entidade `Artifact` canônica com SHA-256 e proveniência auditável.
4. **Isolamento de Estado Autoritativo (Fase 04)**: Concluído com `StateStore` e preservação atômica em disco.
5. **Adesão Estrita ao Protocolo de Não-Antecipação**: O runtime autônomo e schedulers futuros permanecem estritamente bloqueados até que os quality gates definidos nestes contratos sejam plenamente satisfeitos.
5. **Nenhum Código Destrutivo**: Manter rigorosamente a governança de zero alterações cegas ou não autorizadas no repositório.
