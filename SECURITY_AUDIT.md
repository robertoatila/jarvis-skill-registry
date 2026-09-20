# SECURITY_AUDIT — PROTOCOLO SEGURANÇA v13.2 / Intermediário

- Protocolo: **13.2.0 já existia na main antes desta auditoria**
- Nível alvo: **INTERMEDIÁRIO — PRODUCTION DEFENSIBLE**
- Issue: #55
- Branch: `security/55-protocol-v13-2-intermediate`
- Baseline: `0dc49677ff2136b9b02cce2e29ebaccf4d5699e0`
- Snapshot de código desta auditoria: `9dff264ab6c5d8617bfd61890e774a4d78cf7b4a`
- Estado global: **INTERMEDIATE_PENDING_DIRECT_VALIDATION**
- Autoridade de evidência: `evidence/current.json` + gates diretos; GitHub Actions não substitui validação direta.

## Correção do estado histórico

`governance/sovereign-security-protocol-v13.json` já está em `version: 13.2.0` e `ACTIVE_SEALED`.
Portanto, o problema não era ausência do protocolo no JARVIS. O bloqueio é execução/evidência: `evidence/current.json` permanece `INCOMPLETE` e vários gates estão `DIRECT_VALIDATION_REQUIRED`.

## Findings

### JAR-SEC-001 — HIGH / P1 — FIXED_IN_BRANCH / TEST_PENDING

`N8nAdapter`:
- tinha segredo HMAC default conhecido;
- aceitava trigger sem assinatura;
- assinava apenas o payload, sem vincular envelope;
- não exigia timestamp/nonce nem impedia replay.

Correção:
- segredo explícito `JARVIS_N8N_WEBHOOK_SECRET`, mínimo 16 caracteres e diferente do legado;
- assinatura obrigatória;
- HMAC cobre event type, mission id, timestamp, nonce e payload;
- janela de freshness;
- nonce one-time em replay cache;
- testes para unsigned, tamper, stale e replay.

### JAR-SEC-002 — HIGH / P1 — FIXED_IN_BRANCH / TEST_PENDING

`FederationRouter` tratava SHA-256 sem chave como `signature_sha256`, enquanto o trust tier era apenas uma declaração.

Correção:
- nó remoto não pode ser registrado sem `JARVIS_FEDERATION_EXCHANGE_SECRET` explícito >= 32 caracteres;
- envelope usa HMAC-SHA256;
- exchange id não reutilizável;
- verificação inclui freshness e replay;
- tamper/replay têm testes negativos;
- trust tier desconhecido é rejeitado no parse;
- `UNTRUSTED_EXTERNAL` nunca é candidato a offload;
- o campo enganoso `signature_sha256` deixa de ser usado nesse caminho e vira `signature_hmac_sha256`.

### JAR-EVID-001 — HIGH / P1 — OPEN

`evidence/current.json` ainda exige validação direta para:
- portable runtime Windows/Linux/macOS;
- legacy governance Windows;
- browser smoke;
- release evidence completo.

Nenhuma evidência histórica é promovida automaticamente para o snapshot atual.

### JAR-STACK-001 — HIGH / P1 — OPEN

PRs ativas:
- #53 — remote PC command runtime, HEAD `ab72eafc58e02ecd9ccbf1187c2def9ff0c40596`;
- #54 — Mark-LIV Holomat cockpit, HEAD `804f42e7c895e328bfc4eb72978822c045d34f33`.

Elas partem da main e **não contêm** as correções deste branch. Antes de merge, precisam incorporar o hardening aplicável e executar evidência fresca no novo HEAD.

### JAR-TRUST-001 — MEDIUM / P2 — OPEN

O audit de trust boundaries ainda lista áreas que não podem ser promovidas só pelas duas correções acima: interseção completa de permissões, secret-reference materialization, integridade/freshness de artifact reuse e authenticated evidence. Requer inspeção/execução adicional.

## 9 domínios

| Domínio | Estado | Evidência / limite |
| --- | --- | --- |
| 1. Governança / Secure SDLC | PARTIAL | v13.2 selado, issue/branch/audit; evidence corrente ainda incomplete. |
| 2. Identity / AuthN / AuthZ / Session / Anti-Abuse | PARTIAL | Policy/grants existem; identidade distribuída e permissões efetivas ainda têm open gates. |
| 3. Web / API / Injection / Business Logic | PARTIAL | n8n foi endurecido; endpoint/browser/remote atuais exigem rerun. |
| 4. Data / DB / RLS / Privacy | PARTIAL/N/A | Não é SaaS DB central clássico; vault/state/telemetry continuam exigindo minimização e secret handling. |
| 5. Cloud / Infra / Secrets / Supply Chain | PARTIAL | pre-publish/Merkle/quarantine existem; secret refs e evidence auth ainda incompletos. |
| 6. Reliability / Resilience / Performance / DR | PARTIAL | checkpoints/recovery existem; current direct portable gates pendentes. |
| 7. Logging / Audit / Detection / IR | PARTIAL | ledgers/telemetry existem; autenticidade de evidence e sinks ainda aberta. |
| 8. Testing / Quality / Accessibility | PENDING | histórico forte; snapshot atual e PRs #53/#54 exigem execução direta. |
| 9. AI / RAG / Agents / MCP | PARTIAL | authorization/policy robustos em partes; n8n/federation corrigidos, demais trust boundaries ainda abertos. |

## Release gates

| Gate | Estado |
| --- | --- |
| Security | **PENDING** — dois P1 corrigidos, testes diretos + demais trust gates pendentes |
| Quality | **PENDING** — full-test/browser/current branch não executados |
| Reliability | **PENDING** — portable runtime/current heads sem evidência fresca |
| Privacy/Compliance | **PARTIAL** — vault/telemetry/secret materialization ainda requer fechamento |

## Validação obrigatória antes de fechar Intermediário

```bash
python jarvis.py --doctor
python jarvis.py --full-test
python jarvis.py --test
python -m unittest tests.test_agentic_n8n tests.test_agentic_federation
python tooling/validate_v020_plan4.py --gate portable-runtime
python tooling/validate_v020_plan4.py --gate legacy-governance
npm run test:browser
```

Executar os gates de plataforma exigidos pelo repositório e registrar SHA, ambiente, artefato e timestamp.

Depois:
1. atualizar `evidence/current.json` apenas com evidência direta;
2. incorporar este hardening em #53/#54 e rerodar;
3. revisar `docs/security/TRUST_BOUNDARIES.md` com evidência do código atual;
4. manter UNKNOWN onde identidade/secret/evidence não tiver prova.

**Não está autorizado declarar Intermediário PASS neste snapshot enquanto `evidence/current.json` permanecer incompleto.**
