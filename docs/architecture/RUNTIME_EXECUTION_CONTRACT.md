# J.A.R.V.I.S. // Runtime Execution Contract

**Documento Canônico:** `docs/architecture/RUNTIME_EXECUTION_CONTRACT.md`  
**Status:** RATIFICADO // NORMATIVO  
**Classificação:** CONTRATO FUNDAMENTAL DO RUNTIME  
**Versão:** 1.0.0 (Protocolo SSP-v13.2 / Python 3.12 Stdlib)  
**Repositório:** `robertoatila/jarvis-skill-registry`  

---

## 1. Visão Geral e Propósito

Este documento estabelece a semântica formal, explícita e testável do ciclo de vida de execução do runtime autônomo J.A.R.V.I.S. Ele elimina ambiguidades operacionais e impede que subsistemas futuros — tais como **Wave Scheduler**, **Autonomous Goal Loop**, **Learning Engine**, **Infrastructure Skills**, **n8n Bridge** e **Multi-Node Federation** — sejam construídos sobre premissas implícitas ou estados colapsados.

O ciclo fundamental de execução governado por este contrato é:

```text
COMMAND
  │
  ▼
ATTEMPT (Tentativa individual isolada com contexto de nó/agente)
  │
  ▼
SIDE EFFECT (Registro explícito de mutação com semântica de idempotência)
  │
  ▼
RESULT (Saída bruta, exit code, referências de I/O)
  │
  ▼
ARTIFACT (Entregável persistido com hash criptográfico e metadados)
  │
  ▼
VERIFICATION (Avaliação independente contra requisitos formais de prova)
  │
  ▼
EVIDENCE (Registro assinado no ledger com fingerprint ambiental)
  │
  ▼
OUTCOME (Decisão qualificada de desfecho da missão/tarefa)
```

---

## 2. Mapa de Primitivas: Task vs. ExecutionAttempt

### 2.1 Diagnóstico do Código Existente

| Entidade | Status | Símbolo / Path | Comportamento Atual | Limitação Identificada |
| :--- | :--- | :--- | :--- | :--- |
| `TaskNode` | `EXISTING` | [TaskNode](file:///e:/.skill-registry/tooling/agentic/models.py#L558-L708) | Representa um nó estático no [ExecutionDAG](file:///e:/.skill-registry/tooling/agentic/dag.py#L42-L100). Mantém campos `status: TaskStatus`, `retry_count: int`, `max_retries: int` e `execution_result: Optional[Dict]`. | Colapsa tentativas em um contador escalar (`retry_count`). Ao retentar, `execution_result` era sobrescrito, destruindo o histórico forense e impedindo atribuição de falha por tentativa. |
| `ExecutionAttempt` | `FORMALIZED` | [ExecutionAttempt](file:///e:/.skill-registry/tooling/agentic/models.py#L368-L476) | Entidade de primeira classe que encapsula cada execução física de uma tarefa, registrando `attempt_id`, `node_id`, `agent_id`, `idempotency_key`, estados multidimensionais, `failure_class`, `failure_attribution` e `side_effects`. | Conecta-se retrocompativelmente a `TaskNode.attempts` via `TaskNode.record_attempt()`, preservando 100% de compatibilidade com serializações legadas. |

### 2.2 Invariante Estrutural

Uma `Task` permanece com sua identidade imutável (`task_id`), enquanto múltiplas `ExecutionAttempt` podem variar em:
1. Agente executor (`agent_id`);
2. Nó de processamento (`node_id` — local vs. remoto);
3. Ferramenta ou skill invocada (`tool_id`, `skill_id`);
4. Chave de idempotência e referências de I/O (`idempotency_key`);
5. Desfecho isolado e duração.

```text
Task T1 (Deploy Component)
 │
 ├── Attempt A1 [node=remote-east, agent=Quantum-Executor] ──> TIMEOUT (OUTCOME_UNKNOWN)
 │
 ├── Attempt A2 [node=remote-east, action=reconcile]       ──> RECONCILED (NOT_APPLIED)
 │
 └── Attempt A3 [node=local, agent=Quantum-Executor]       ──> FINISHED & VERIFIED (SUCCEEDED)
```

---

## 3. Separação Multidimensional de Estados

É estritamente proibido colapsar diferentes dimensões operacionais em um único campo de status. O runtime formaliza quatro eixos ortogonais:

```text
┌─────────────────────────┐     ┌─────────────────────────┐
│     EXECUTION STATE     │     │   VERIFICATION STATE    │
│  PENDING                │     │  UNVERIFIED             │
│  READY                  │     │  VERIFYING              │
│  RUNNING                │     │  VERIFIED               │
│  FINISHED               │     │  REJECTED               │
│  FAILED                 │     │  STALE                  │
│  CANCELLED              │     └─────────────────────────┘
│  TIMED_OUT              │
└─────────────────────────┘
            │                                │
            ▼                                ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│     RECOVERY STATE      │     │     MISSION OUTCOME     │
│  NOT_REQUIRED           │     │  SUCCEEDED              │
│  RETRY_PENDING          │     │  PARTIALLY_SUCCEEDED    │
│  RECONCILIATION_PENDING │     │  FAILED                 │
│  COMPENSATION_PENDING   │     │  CANCELLED              │
│  RECOVERY_PENDING       │     │  ABORTED_BY_POLICY      │
│  RECOVERED              │     │  BUDGET_EXCEEDED        │
│  UNRECOVERABLE          │     │  OUTCOME_UNKNOWN        │
└─────────────────────────┘     └─────────────────────────┘
```

### 3.1 Conflitos Semânticos Proibidos (Invariantes Negativas)

1. **`command exit code 0 ≠ desired state reached`**: Um comando de shell terminando com código zero indica apenas que o binário concluiu sem exceção fatal; não prova conformidade do sistema de arquivos ou persistência de estado.
2. **`execution finished ≠ verified`**: A execução do comando é uma asserção do agente; a verificação é uma prova coletada por inspeção independente (cf. [verification.py](file:///e:/.skill-registry/tooling/agentic/verification.py#L245-L272)).
3. **`task completed ≠ mission succeeded`**: A conclusão de todas as tarefas de uma onda não autoriza o sucesso da missão se houver cheques de prova pendentes, falhas de regressão ou estouro de orçamento.
4. **`artifact exists ≠ artifact is valid / fresh`**: A existência física de um arquivo não garante que seu conteúdo corresponde ao hash gerado na execução nem que ele permanece fresco em relação ao ambiente atual.
5. **`timeout ≠ confirmed failure`**: Uma expiração de tempo em operação remota ou distribuída indica **resultado desconhecido (`OUTCOME_UNKNOWN`)**, nunca falha determinística de execução.

---

## 4. Modelo de Side Effects e Idempotência

### 4.1 Taxonomia de Side Effects

Toda operação realizada pelo runtime deve ser categorizada antes de sua admissão:

| Tipo | Descrição | Exemplo | Risco |
| :--- | :--- | :--- | :--- |
| `PURE` | Sem leitura nem escrita no mundo externo; cálculo em memória. | Resolução topológica de DAG | R0 |
| `READ_ONLY` | Inspeciona estado persistente ou ambiente sem mutação. | `git status`, leitura de arquivo | R0 |
| `LOCAL_WRITE` | Gravação em diretórios efêmeros ou scratch do workspace. | Escrita em `tmp/`, cache local | R1 |
| `REPOSITORY_WRITE` | Mutação de arquivos versionados no repositório. | Edição de código-fonte, schemas | R2 |
| `EXTERNAL_WRITE` | Mutação via API externa, banco de dados ou webhook. | Disparo n8n, criação de issue GitHub | R3 |
| `INFRASTRUCTURE_MUTATION` | Modificação de configurações de sistema operacional, rede ou serviços. | Instalação de binários, firewall | R4 |
| `DESTRUCTIVE` | Eliminação irreversível de recursos ou dados. | `rm -rf`, DROP DATABASE, `git reset --hard` | R5 |

### 4.2 Contrato de Idempotência

Para cada classe de operação com side effect, o runtime aplica uma das seguintes políticas:

1. `IDEMPOTENT`: Múltiplas execuções com os mesmos parâmetros produzem rigorosamente o mesmo estado final no alvo (ex.: `mkdir -p`, escrita de arquivo com conteúdo fixo).
2. `RETRY_SAFE`: Operação que pode ser repetida com segurança mesmo que gere identificadores adicionais internamente inócuos (ex.: leitura paginada).
3. `IDEMPOTENCY_KEY_REQUIRED`: Requer cabeçalho ou chave criptográfica única (`idempotency_key = sha256(mission_id + task_id + attempt_number + input_hash)`) para evitar duplicações remotas.
4. `RECONCILIATION_REQUIRED`: É terminantemente proibido retentar sem antes inspecionar o alvo remoto para verificar se a mutação ocorreu durante timeout ou falha de transporte.
5. `COMPENSATION_REQUIRED`: Operação não idempotente que exige geração de ação compensatória comprovável antes de nova tentativa.
6. `UNSAFE_TO_RETRY`: Operação estritamente não repetível sem aprovação manual do operador.

---

## 5. Tratamento de Resultado Remoto Desconhecido (`OUTCOME_UNKNOWN`)

Quando uma operação que produz side effect externo sofre perda de conectividade, queda de conexão HTTP ou timeout:

```text
Jarvis envia comando externo (ex.: n8n, infraestrutura, nó federado)
               │
               ▼
      Conexão interrompida
               │
               ▼
       [OUTCOME_UNKNOWN]  (NÃO classificar como FAILED)
               │
               ▼
     Fase de Reconciliação
               │
   ┌───────────┴───────────┐
   ▼                       ▼
Alvo Inalterado       Alvo Modificado
   │                       │
   ▼                       ▼
RETRY_SAFE           Reconciliar Estado
                     ├── Se conforme: ACCEPT & VERIFY
                     ├── Se incompleto: COMPENSATE ou ESCALATE
                     └── NUNCA cegamente duplicar mutação
```

**Invariante Central:** Nenhum retry potencialmente duplicador de recursos pode ser disparado quando o resultado for `OUTCOME_UNKNOWN` e a operação não for comprovadamente idempotente.

---

## 6. Contrato Conceitual do Tool Adapter

Todo adaptador de ferramenta (local, MCP, API ou remoto) deve expor suas capacidades declaradas:

```text
supports_cancel              : bool  # Capacidade de abortar execução cooperativamente
supports_timeout             : bool  # Capacidade de aplicar deadline estrito sem vazamento de processos
supports_idempotency         : bool  # Garantia de execução idempotente nativa
supports_idempotency_key     : bool  # Aceitação de token de deduplicação externa
supports_reconcile           : bool  # Capacidade de inspecionar estado pós-interrupção
supports_compensation        : bool  # Fornece ação de reversão programática
supports_verification        : bool  # Retorna prova direta de conformidade
supports_dry_run             : bool  # Executa sem materializar side effect
supports_artifact_streaming  : bool  # Emite dados parciais com integridade incremental
```

*Regra de Ausência:* A ausência de uma capability indica **comportamento determinístico conhecido** (ex.: se `supports_cancel = False`, o runtime aplica contenção de processo via Job Objects/SIGKILL e marca o estado para reconciliação obrigatória), nunca fallback silencioso ou suposição de suporte.

---

## 7. Planos Arquiteturais: Separação de Responsabilidades

O runtime implementa separação formal entre três planos operacionais:

```text
┌─────────────────────────────────────────────────────────────┐
│                        CONTROL PLANE                        │
│  Goal Engine • Planner • Policy Engine • Resolver           │
│  Wave Scheduler • Budgets • State Store • Recovery Engine   │
└──────────────────────────────┬──────────────────────────────┘
                               │ Contrato de Execução / Autorização
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                       EXECUTION PLANE                       │
│  Quantum Agents • Skill Drivers • Tool Adapters (MCP/CLI)   │
│  Processos Locais • APIs Remotas • Nós Federados            │
└──────────────────────────────┬──────────────────────────────┘
                               │ Emissão de Artefatos
                               ▼
                       [ VERIFICAÇÃO INDEPENDENTE ]
                               │ Provas Criptográficas
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                       EVIDENCE PLANE                        │
│  Telemetry Spans • Audit Ledger • Skill Fitness             │
│  Experiment Engine • Learning Records • Cognitive Vault     │
└─────────────────────────────────────────────────────────────┘
```

### Invariantes de Isolamento dos Planos:
1. **Interface HUD é pura projeção**: A UI/HUD nunca comanda agentes diretamente sem passar pela autorização do Control Plane.
2. **Telemetria não é autoridade de estado**: Spans e eventos de telemetria registram o que ocorreu; a fonte de verdade do estado de execução é o [StateStore](file:///e:/.skill-registry/tooling/agentic/state_store.py) e o [ExecutionDAG](file:///e:/.skill-registry/tooling/agentic/dag.py).
3. **Execution Plane não expande autorização**: Nenhuma skill, ferramenta ou nó remoto pode solicitar ou conceder privilégios além da interseção calculada pelo Control Plane.
4. **Learning não ignora política**: Nenhuma heurística aprendida entra em vigor sem passar pelo gate de promoção e validação de política.

---

## 8. Quality Gates de Sub-sistemas

Antes de habilitar o consumo de subsistemas avançados pelo runtime, os seguintes gates devem ser satisfeitos:

### 8.1 Wave Scheduler Gate
- [x] Contrato de execução unificado com `ExecutionAttempt` formalizado.
- [x] Detecção estrita de ciclos e ordenação topológica determinística ([dag.py](file:///e:/.skill-registry/tooling/agentic/dag.py)).
- [x] Concorrência limitada por scopes de leitura/escrita e capacidade de agentes.
- [x] Rejeição de tarefas em cancelamento, timeout ou estouro de orçamento.
- [x] Tratamento explícito de `OUTCOME_UNKNOWN`.

### 8.2 Infrastructure Skills Gate
- [x] Side effects catalogados de R0 a R5 com política de bloqueio automático para R5 autônomo.
- [x] Semântica de idempotência por tentativa com suporte a `idempotency_key`.
- [x] Proibição formal de compensação sem proveniência criptográfica (`NO PROVENANCE → NO COMPENSATION`).
- [x] Contenção estrita de paths ao workspace do repositório ([policy.py](file:///e:/.skill-registry/tooling/agentic/policy.py)).
- [ ] Sandboxing de baixo nível do sistema operacional (Job Objects no Windows / cgroups no Linux) — *Pendente para Fase de Hardening*.

### 8.3 Learning & Fitness Gate
- [x] Provas de verificação com hashing SHA-256 e encadeamento no ledger.
- [x] Modelo de promoção em 3 níveis: `OBSERVATION → PATTERN → VALIDATED_HEURISTIC` ([learning.py](file:///e:/.skill-registry/tooling/agentic/learning.py)).
- [x] Atribuição estrita de falha: Falhas atribuídas a `NODE`, `ENVIRONMENT` ou `POLICY` **não** reduzem o fitness de uma `SKILL` ([models.py](file:///e:/.skill-registry/tooling/agentic/models.py)).
- [x] Separação de dados experimentais da linha de base de produção.

### 8.4 Multi-Node Federation Gate
- [ ] Autenticação criptográfica mTLS mútua entre nós.
- [ ] Handshake de compatibilidade de protocolo, versão de schema e hashes de skills.
- [ ] Correlação distribuída de tentativas com rastreabilidade de `parent_trace_id`.
- [ ] Garantia de que `node_id` autodeclarado é rejeitado sem atestação criptográfica.
