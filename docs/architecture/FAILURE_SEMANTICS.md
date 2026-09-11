# J.A.R.V.I.S. // Failure Semantics & Recovery Governance

**Documento Canônico:** `docs/architecture/FAILURE_SEMANTICS.md`  
**Status:** RATIFICADO // NORMATIVO  
**Classificação:** GOVERNANÇA DE FALHAS E RECUPERAÇÃO  
**Versão:** 1.0.0 (Protocolo SSP-v13.2 / Python 3.12 Stdlib)  
**Repositório:** `robertoatila/jarvis-skill-registry`  

---

## 1. Princípio Fundamental de Falhas

No runtime J.A.R.V.I.S., **falha operacional** e **responsabilidade pela falha** são conceitos rigorosamente separados.

O encadeamento obrigatório antes que qualquer evento de falha alimente motores de otimização, fitness ou aprendizagem é:

```text
EXECUTION (Disparo de comando ou ferramenta)
   │
   ▼
VERIFICATION (Inspeção independente de requisitos de prova)
   │
   ▼
FAILURE CLASSIFICATION (Taxonomia objetiva do erro ocorrido)
   │
   ▼
FAILURE ATTRIBUTION (Determinação causal da entidade responsável)
   │
   ▼
RECOVERY DISPATCH (Decisão qualificada: Retry, Reconcile, Compensate, Block, Escalate)
   │
   ▼
FITNESS / LEARNING ADMISSION (Ingestão qualificada no Evidence Plane)
```

---

## 2. Taxonomia Canônica de Falhas (`FailureClass`)

O runtime define 15 classes formais de falha ([models.py](file:///e:/.skill-registry/tooling/agentic/models.py#L228-L245)):

1. `TRANSIENT`: Falha temporária de I/O, lock de arquivo efêmero ou oscilação rápida de rede; elegível a retry com backoff.
2. `PERMANENT`: Erro determinístico de código, sintaxe inválida, lógica incorreta ou arquivo inexistente imutável; re-tentativa idêntica proibida.
3. `VALIDATION`: Falha em asserções de teste, schemas corrompidos ou integridade de dados não atendida.
4. `POLICY`: Operação bloqueada ativamente pelo [PolicyEngine](file:///e:/.skill-registry/tooling/agentic/policy.py) (ex.: risco R5 destrutivo, tentativa de path traversal).
5. `AUTHORIZATION`: Falha por escopo insuficiente, perfil de agente não autorizado ou recusa do operador humano.
6. `CONFLICT`: Concorrência de escrita detectada sobre o mesmo recurso ou divergência com branch base.
7. `TIMEOUT`: Limite de tempo excedido durante a execução de comando ou requisição de API.
8. `RESOURCE_EXHAUSTED`: Limite de tokens, memória, cota de API ou orçamento da missão esgotado.
9. `DEPENDENCY_FAILURE`: Tarefa pré-requisito falhou, tornando a tarefa dependente estruturalmente inexecutável.
10. `EXTERNAL_SERVICE`: Interrupção em serviço de terceiros (ex.: GitHub API, webhook n8n, DNS).
11. `MALFORMED_RESULT`: Ferramenta retornou saída ilegível, truncada ou fora da estrutura esperada.
12. `INTEGRITY_FAILURE`: Discrepância em hash SHA-256 de artefato ou corrupção de snapshot.
13. `COMPATIBILITY`: Incompatibilidade de plataforma de SO, arquitetura de CPU ou versão de runtime.
14. `CANCELLED`: Interrupção deliberada solicitada pelo usuário ou pelo circuito de segurança.
15. `UNKNOWN`: Causa raiz não identificável sem inspeção forense aprofundada.

---

## 3. Atribuição de Falhas (`FailureAttribution`)

Toda falha classificada deve ser atribuída com base em evidências verificáveis a uma das seguintes entidades:

```text
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     PLANNER     │     │    RESOLVER     │     │      AGENT      │
│ Plano inválido, │     │ Skill incorreta │     │ Raciocínio ou   │
│ ciclos no DAG   │     │ ou incompatível │     │ comando errôneo │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│      SKILL      │     │      TOOL       │     │      NODE       │
│ Bug interno no  │     │ Adapter quebrou │     │ Crash da VM/SO, │
│ código da skill │     │ ou timeout MCP  │     │ falta de RAM    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   ENVIRONMENT   │     │ EXTERNAL_SERV.  │     │     POLICY      │
│ Binário ausente │     │ Queda de API ou │     │ Ação barrada por│
│ no SO hospedeiro│     │ timeout remoto  │     │ regras de risco │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Regras de Ouro de Atribuição:

- **Regra 1 (Proteção de Fitness de Skills):** Se um nó remoto sofre crash (`FailureAttribution.NODE`), se a rede cai (`FailureAttribution.EXTERNAL_SERVICE`), se o sistema operacional não possui uma biblioteca instalada (`FailureAttribution.ENVIRONMENT`), ou se o operador humano nega uma aprovação (`FailureAttribution.POLICY`), **o score de confiabilidade da Skill NÃO PODE ser penalizado**.
- **Regra 2 (Falha de Agente vs. Skill):** Se o agente utilizou parâmetros ilegais para uma skill bem comportada, a atribuição recai sobre `FailureAttribution.AGENT`, não sobre a skill.
- **Regra 3 (Transparência Operacional):** Atribuições classificadas como `UNKNOWN` geram alerta de auditoria e exigem investigação antes de influenciar heurísticas permanentes.

---

## 4. Matriz de Políticas de Retry

O runtime proíbe sumariamente decisões de retry baseadas exclusivamente em `attempt_count < max_retries`. A tabela a seguir rege as ações automáticas autorizadas:

| Failure Class | Retry Permitido? | Mesmo Nó? | Outro Nó? | Outra Skill? | Reconciliação Prévia? | Compensação Necessária? | Bloqueia Dependentes? | Aprovação Humana? | Penaliza Fitness da Skill? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `TRANSIENT` | **SIM** | SIM | SIM | NÃO | Recomendada | NÃO | SE ESGOTAR | NÃO | NÃO |
| `PERMANENT` | **NÃO** | NÃO | NÃO | SIM | NÃO | SIM | **SIM** | NÃO | **SIM** |
| `VALIDATION` | **CONDICIONAL** | NÃO | SIM | SIM | NÃO | SIM | **SIM** | NÃO | **SIM** |
| `POLICY` | **NÃO** | NÃO | NÃO | NÃO | NÃO | NÃO | **SIM** | **SIM** | NÃO |
| `AUTHORIZATION` | **NÃO** | NÃO | NÃO | NÃO | NÃO | NÃO | **SIM** | **SIM** | NÃO |
| `CONFLICT` | **SIM** | SIM | NÃO | NÃO | **OBRIGATÓRIA**| NÃO | SE ESGOTAR | NÃO | NÃO |
| `TIMEOUT` | **CONDICIONAL** | NÃO | SIM | NÃO | **OBRIGATÓRIA**| SE MUTOU | SE ESGOTAR | NÃO | NÃO |
| `RESOURCE_EXHAUSTED`| **NÃO** | NÃO | SIM | NÃO | NÃO | NÃO | **SIM** | **SIM** | NÃO |
| `DEPENDENCY_FAILURE`| **NÃO** | NÃO | NÃO | NÃO | NÃO | NÃO | **SIM** | NÃO | NÃO |
| `EXTERNAL_SERVICE` | **SIM** | SIM | SIM | NÃO | **OBRIGATÓRIA**| NÃO | SE ESGOTAR | NÃO | NÃO |
| `MALFORMED_RESULT` | **CONDICIONAL** | SIM | SIM | SIM | NÃO | SE MUTOU | SE ESGOTAR | NÃO | **SIM** |
| `INTEGRITY_FAILURE` | **NÃO** | NÃO | NÃO | NÃO | **OBRIGATÓRIA**| SIM | **SIM** | **SIM** | NÃO |
| `COMPATIBILITY` | **NÃO** | NÃO | SIM | SIM | NÃO | NÃO | **SIM** | NÃO | NÃO |
| `CANCELLED` | **NÃO** | NÃO | NÃO | NÃO | **OBRIGATÓRIA**| SE MUTOU | **SIM** | NÃO | NÃO |
| `UNKNOWN` | **NÃO** | NÃO | NÃO | NÃO | **OBRIGATÓRIA**| NÃO | **SIM** | **SIM** | NÃO |

---

## 5. Rollback, Compensação e Semântica de Saga

Estes três conceitos possuem semânticas técnicas estritamente distintas e não devem ser confundidos:

### 5.1 Rollback
Restauração atômica direta de um snapshot prévio em sistema que suporta transações locais.
- **Exemplo Real:** Em gravação de arquivos de checkpoint ([resilience.py](file:///e:/.skill-registry/tooling/agentic/resilience.py#L114-L121)), gravação primeiro em `.tmp` com substituição atômica via `os.replace`. Se falhar, o arquivo de destino original permanece intacto.
- **Aplicabilidade:** Transações de filesystem local, rollback de transação SQL ou rollback de branch isolada do Git.

### 5.2 Compensação
Execução de uma **nova operação mutatória deliberada** destinada a neutralizar os efeitos de uma operação anterior já concretizada no mundo externo.
- **Exemplo Real:** Exclusão de bucket S3 criado, desprovisionamento de webhook em n8n ou exclusão de registro de DNS.
- **INVARIANTE OBRIGATÓRIA DE COMPENSAÇÃO:**
  ```text
  NO PROVENANCE → NO AUTOMATIC COMPENSATION
  ```
  Se o runtime não possuir o registro exato da proveniência do recurso criado ([SideEffectRecord](file:///e:/.skill-registry/tooling/agentic/models.py)), incluindo o identificador exato, o hash criptográfico e a ação de reversão aprovada, a compensação automática é estritamente **proibida**, sendo imediatamente escalada ao operador humano para evitar deleções acidentais de recursos compartilhados.

### 5.3 Saga
Orquestrador de longa duração para workflows distribuídos compostos por múltiplos passos:
```text
Passo A (Sucesso) ──> Passo B (Sucesso) ──> Passo C (Falha)
                                                    │
                                                    ▼
Compensar B (Reversão de B) ◄──────────────────────┘
     │
     ▼
Compensar A (Reversão de A)
     │
     ▼
Notificar Operador com Relatório Causal
```

---

## 6. Contrato de Replay Determinístico

Quando eventos do Audit Ledger ou Telemetria são reprocessados para recuperação de estado:

1. **Garantia de Equivalência:** `mesmos eventos aceitos → mesmo estado final derivado`.
2. **Isolamento de Efeitos:** O replay deve ser **estritamente livre de side effects**. É proibido que o reprocessamento de eventos dispare novamente chamadas de rede, escritas de arquivo ou comandos de shell.
3. **Distinção Operacional:**
   - **State Reconstruction:** Leitura sequencial de eventos do ledger para reconstruir projeções em memória (ex.: métricas, visualização do HUD).
   - **Execution Recovery:** Retomada física de processos interrompidos utilizando checkpoints transacionais com garantia de não reexecução de tarefas com status `VERIFIED`.

---

## 7. Critérios de Qualidade para Aprendizagem e Fitness

Nenhuma observação bruta de falha pode ser convertida imediatamente em heurística ou provocar penalidade de reputação:

```text
Observação Bruta
       │
       ▼
Validação de Prova (Hash SHA-256 verificado, exit code analisado)
       │
       ▼
Atribuição Causal Verificada (Apenas falhas atribuídas à Skill afetam a Skill)
       │
       ▼
Registro no Evidence Ledger (Com identificação de ambiente e dependências)
       │
       ▼
Detecção de Padrão (Mínimo de 3 observações idênticas em condições análogas)
       │
       ▼
Promoção para Heurística Validada (Aprovada por política e persistida no Cognitive Vault)
```
