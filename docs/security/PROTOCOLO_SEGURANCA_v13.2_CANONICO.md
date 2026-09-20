🔐 PROTOCOLO SEGURANÇA v13.2

Versão: 13.2.0
Data-base: 09/09/2026
Status: CANÔNICO
Substitui: v7 · v8 · v9 · v10 · v11 · v12
Modelo: Secure by Design + Production Engineering
Gatilho: "SEGURANÇA"

«Um sistema não está pronto para produção apenas porque compila.

Um controle não existe apenas porque há código relacionado.

PASS exige implementação + evidência + teste + resultado verificável.»

---

0.0 DELTA v13 — MELHORIAS SOBRE A v12

A v13 preserva os 9 domínios e adiciona:

- RELEASE GATE separado em SECURITY + QUALITY + RELIABILITY + PRIVACY/COMPLIANCE;
- evidence freshness vinculada a commit, artefato e ambiente;
- SLSA 1.2 e verificação explícita de provenance;
- priorização de vulnerabilidades com KEV + EPSS + CVSS 4.0 + SSVC/contexto;
- controles de release safety, migrations, filas e feature flags;
- ampliação de AI/RAG/Agents/MCP com referências OWASP 2026;
- proteção explícita contra tool poisoning, rug pull, excessive agency e memory poisoning;
- orçamento e kill switch para loops/agentes;
- authorization per tool e per resource em MCP;
- critérios de blockers para cross-tenant RAG/MCP e artifact provenance mismatch;
- finding format com mapeamento a padrões e contexto de exploração;
- auditoria de insecure defaults com Trail of Bits `insecure-defaults`;
- fail-closed obrigatório para flags críticas como `REQUIRE_AUTH`;
- databases em Docker privadas por padrão, sem publicação de porta ao host quando não necessária;
- credenciais default/dev proibidas em produção e rotação obrigatória após suspeita de exposição;
- segmentação explícita entre rede de clientes/guest, aplicação, administração e dados;
- subnetting sem ACL/firewall não conta como isolamento;
- microsegmentação e service-specific connectivity para workloads críticos;
- management plane privado, sem SSH/RDP/painéis administrativos expostos diretamente à Internet;
- reverse proxy/WAF/CDN/DMZ podem reduzir exposição, mas ocultação não substitui AuthN/AuthZ;
- regras específicas para Docker/firewall, incluindo risco de portas publicadas contornarem políticas UFW.
- evidência inválida quando produzida por commit/artefato diferente do que vai a produção.

Regra:

EVIDENCE FROM OLD COMMIT
≠
PASS FOR CURRENT RELEASE

RELEASE
=
SECURITY PASS
+
QUALITY PASS
+
RELIABILITY PASS
+
PRIVACY/COMPLIANCE PASS WHEN APPLICABLE

---

0. OBJETIVO

Este protocolo estabelece o baseline para:

- aplicações web;
- SaaS;
- APIs;
- backends;
- sistemas multi-tenant;
- bancos de dados;
- storage;
- sistemas empresariais;
- aplicações financeiras;
- sistemas com dados pessoais;
- cloud;
- containers;
- CI/CD;
- supply chain;
- caches;
- filas;
- WebSockets;
- webhooks;
- OAuth/OIDC;
- IA generativa;
- RAG;
- agentes;
- MCP;
- infraestrutura;
- observabilidade;
- disaster recovery;
- acessibilidade;
- documentação arquitetural.

O ciclo protegido passa a ser:

DESIGN
  ↓
IMPLEMENT
  ↓
REVIEW
  ↓
TEST
  ↓
BUILD
  ↓
DEPLOY
  ↓
OBSERVE
  ↓
RESPOND
  ↓
RECOVER
  ↓
LEARN

---

0.1 REFERÊNCIAS CANÔNICAS

Segurança de aplicações

- OWASP Top 10:2025;
- OWASP ASVS 5.0.0;
- OWASP API Security Top 10:2023;
- OWASP Cheat Sheet Series;
- OWASP Automated Threats;
- OWASP Bot Management;
- OWASP Credential Stuffing Prevention.

OWASP Top 10:2025 é a versão atual e inclui Broken Access Control, Security Misconfiguration, Software Supply Chain Failures, Cryptographic Failures, Injection, Insecure Design, Authentication Failures, Integrity Failures, Logging/Alerting Failures e Mishandling of Exceptional Conditions.

Para verificação técnica, ASVS 5.0.0 deve ter precedência sobre tratar o Top 10 como checklist, pois a própria OWASP recomenda ASVS como padrão verificável para design, code review e testes.

---

Identidade

- NIST SP 800-63-4;
- NIST SP 800-63B-4;
- RFC 8725;
- RFC 9700;
- RFC 10017.

NIST SP 800-63B-4 é final desde julho de 2025.

RFC 10017, publicado em agosto de 2026, formaliza OAuth 2.0 para aplicações em browser. O padrão BFF mantém access/refresh tokens fora do JavaScript e é fortemente recomendado para aplicações empresariais, sensíveis e que tratam dados pessoais.

---

Secure SDLC e supply chain

- NIST SP 800-218 SSDF 1.1;
- NIST SP 800-218A;
- CISA KEV;
- SBOM;
- provenance;
- artifact signing;
- SLSA 1.2;
- CVSS 4.0;
- EPSS;
- CISA SSVC.

SSDF 1.1 continua sendo a versão final; SP 800-218 Rev. 1 / SSDF 1.2 permanece draft em setembro de 2026.

SLSA 1.2 é a versão aprovada atual e adiciona/estrutura trilhas de Build e Source, provenance e propriedades verificadas.

CVSS não deve ser usado isoladamente para priorização. Combinar severidade técnica com exploração real, probabilidade de exploração, exposição, criticidade do ativo e impacto.

---

IA, agentes e MCP

- OWASP GenAI LLM Top 10 2026;
- OWASP Top 10 for Agentic Applications 2026;
- OWASP MCP Top 10;
- OWASP Practical Guide for Secure MCP Server Development;
- NIST SP 800-218A.

IA generativa, agentes e MCP são tratados como trust boundaries explícitas.

Model output, tool output, retrieved context, memory e conteúdo externo permanecem não confiáveis até validação e autorização.

---

Incident Response e continuidade

- NIST CSF 2.0;
- NIST SP 800-61 Rev. 3;
- NIST SP 800-34 Rev. 1.

NIST SP 800-61 Rev. 3 é a recomendação final atual para integração de incident response ao gerenciamento de risco.

---

Acessibilidade

Baseline:

WCAG 2.2
NÍVEL AA

WCAG 2.2 é W3C Recommendation e Level AA inclui os critérios A e AA.

---

Privacidade e compliance

Conforme aplicabilidade:

- LGPD;
- regulamentações ANPD;
- GDPR;
- HIPAA;
- PCI DSS 4.0.1.

PCI DSS 4.0.1 continua sendo a versão publicada atual em agosto de 2026.

---

0.2 OS 9 DOMÍNIOS

PARTE 1
Governança, Arquitetura e Secure SDLC

PARTE 2
Identity, AuthN, AuthZ, Sessions e Anti-Abuse

PARTE 3
Web, API, Injection e Business Logic

PARTE 4
Data, Database, RLS, Privacy e Compliance

PARTE 5
Cloud, Infrastructure, Secrets e Supply Chain

PARTE 6
Reliability, Resilience, Performance e DR

PARTE 7
Logging, Audit, Detection e Incident Response

PARTE 8
Testing, Quality Engineering e Accessibility

PARTE 9
AI, RAG, Agents e MCP

---

0.3 NÍVEIS

Nível| Aplicação
🟢 BÁSICO| qualquer aplicação com usuário real
🟡 INTERMEDIÁRIO| produção, SaaS, autenticação, PII
🔴 AVANÇADO| multi-tenant, financeiro, escala
⚫ COFRE MÁXIMO| alto impacto, regulado, crítico

Fluxo:

BÁSICO COMPLETO
      ↓
INTERMEDIÁRIO
      ↓
AVANÇADO
      ↓
COFRE MÁXIMO

---

0.4 STATUS DOS CONTROLES

Somente utilizar:

PASS
FAIL
UNKNOWN
N/A
PENDING EXTERNAL ACTION
PENDING LEGAL
ACCEPTED RISK

PASS

Exige evidência objetiva.

UNKNOWN

Não foi possível verificar.

N/A

Existe justificativa técnica de não aplicabilidade.

ACCEPTED RISK

Exige:

RISCO
JUSTIFICATIVA
OWNER
CONTROLE COMPENSATÓRIO
EXPIRAÇÃO
APROVAÇÃO

---

0.5 DEFINITION OF DONE

Um controle crítico somente recebe PASS com:

- [ ] implementação;
- [ ] teste;
- [ ] evidência;
- [ ] resultado esperado;
- [ ] resultado real;
- [ ] owner;
- [ ] data;
- [ ] regressão quando possível.

Para controles críticos, a evidência deve registrar quando aplicável:

- CONTROL ID;
- standard mapping;
- commit SHA;
- artifact digest;
- ambiente;
- comando/teste executado;
- timestamp;
- tool/version;
- resultado bruto ou referência verificável.

Evidência de outro commit, outro artefato ou outro ambiente não prova a release atual sem justificativa explícita.

Exemplo:

CONTROL:
Tenant isolation

IMPLEMENTATION:
TenantAuthorizationService

TEST:
Tenant A → resource B

EXPECTED:
403 / 404

ACTUAL:
403

EVIDENCE:
integration test

OWNER:
Backend

REGRESSION:
CI

---

0.6 SECURITY / PRODUCTION BLOCKERS

Produção deve ser bloqueada para:

- secret ativo exposto;
- credential leak;
- RCE;
- SQL Injection explorável;
- command injection;
- auth bypass;
- privilege escalation crítica;
- cross-tenant access;
- IDOR/BOLA crítico;
- mass assignment privilegiado;
- armazenamento inseguro de senha;
- banco sensível exposto;
- storage sensível público;
- vulnerabilidade crítica ativamente explorada sem mitigação;
- supply-chain compromise;
- build não validado;
- migration destrutiva sem recovery plan;
- falha crítica de autorização;
- corrupção de dados conhecida;
- DR necessário sem backup recuperável;
- release produzida a partir de artefato diferente do validado;
- provenance/signature/digest incompatível com o artefato aprovado;
- cross-tenant leak em RAG, vector DB, agent memory ou MCP;
- agente/MCP com capacidade destrutiva ampla sem autorização e controles compensatórios;
- restore obrigatório falhando ou não verificável;
- migration crítica sem rollback/roll-forward/recovery testável;
- vulnerabilidade KEV aplicável e exposta sem correção ou mitigação formal;
- auth/admin crítico sem telemetria mínima para detectar abuso conhecido;
- mecanismo de fallback que transforma falha de segurança em allow;
- banco de dados sensível publicado na interface pública sem necessidade arquitetural e sem controles compensatórios;
- PostgreSQL/Redis/MySQL/MongoDB exposto à Internet por `ports:`/host binding quando deveria ser somente interno;
- credencial padrão, exemplo, dev ou conhecida ativa em produção;
- `POSTGRES_HOST_AUTH_METHOD=trust` ou autenticação equivalente sem senha em superfície alcançável;
- flag crítica de segurança ausente resultando em estado permissivo (`REQUIRE_AUTH` ausente → auth desligada).

---

PARTE 1 — GOVERNANÇA, ARQUITETURA E SECURE SDLC

🟢 BÁSICO

1.1 Inventário

Mapear:

- frontend;
- backend;
- APIs;
- banco;
- cache;
- filas;
- storage;
- WebSockets;
- webhooks;
- domínios;
- subdomínios;
- cloud;
- CI/CD;
- integrações;
- terceiros;
- repositórios;
- ambientes;
- secrets;
- certificados;
- IA;
- MCP;
- owners.

---

1.2 Data Classification

PUBLIC
INTERNAL
CONFIDENTIAL
SENSITIVE
CRITICAL

Inventariar:

- PII;
- credenciais;
- tokens;
- dados financeiros;
- documentos;
- dados empresariais;
- fingerprints;
- telemetria;
- biometria;
- logs.

---

1.3 Trust Boundaries

Produzir diagrama mostrando:

INTERNET
   ↓
EDGE
   ↓
FRONTEND
   ↓
BACKEND
   ↓
DATA LAYER
   ↓
THIRD PARTIES

Fronteiras devem ser tratadas explicitamente.

---

1.4 Secure Defaults

DEFAULT DENY

- endpoints privados por padrão;
- debug desligado;
- permissões mínimas;
- storage privado;
- recursos experimentais privados;
- ações administrativas protegidas.

---

🟡 INTERMEDIÁRIO

1.5 Threat Modeling

Para features críticas:

STRIDE
+
ABUSE CASES
+
BUSINESS LOGIC
+
TRUST BOUNDARIES

Analisar:

- spoofing;
- tampering;
- repudiation;
- disclosure;
- denial of service;
- elevation of privilege.

---

1.6 Abuse Cases

Perguntar:

E se alterar o ID?

E se trocar tenant?

E se ignorar o frontend?

E se repetir a ação?

E se usar 10.000 IPs?

E se mandar duas requisições simultâneas?

E se inverter a ordem das operações?

E se comprometer uma conta?

E se comprometer um admin?

E se uma dependência externa mentir?

---

1.7 Risk Register

Cada risco:

ID
ASSET
THREAT
VULNERABILITY
LIKELIHOOD
IMPACT
OWNER
MITIGATION
RESIDUAL RISK
DEADLINE
STATUS

---

1.8 Code Review

Review deve verificar:

- correctness;
- security;
- AuthN;
- AuthZ;
- tenant isolation;
- data access;
- validation;
- concurrency;
- errors;
- observability;
- performance;
- accessibility;
- tests.

OWASP também recomenda explicitamente server-side authorization, fail-safe defaults e review de sessão/IDOR em code review.

---

1.9 CODEOWNERS

Utilizar para áreas críticas quando possível:

- authentication;
- payment;
- authorization;
- migrations;
- CI/CD;
- cloud;
- crypto;
- security configuration.

---

🔴 AVANÇADO

1.10 Architecture Review

Obrigatório para:

- auth;
- multi-tenancy;
- pagamento;
- storage;
- encryption;
- cache;
- queues;
- public APIs;
- AI/agents;
- MCP;
- network architecture.

---

1.11 Architecture Diagrams

Manter no repositório:

System Context

USERS
  ↓
SYSTEM
  ↓
EXTERNAL SYSTEMS

Containers

BROWSER
  ↓
FRONTEND
  ↓
BACKEND
  ↓
DATABASE

 ↘ CACHE
 ↘ STORAGE
 ↘ QUEUE

Deployment

Mostrar:

- cloud;
- regions;
- proxies;
- CDN;
- instances;
- database;
- storage;
- network boundaries.

Data Flow Diagram

Mostrar dados sensíveis atravessando sistemas.

Security Architecture

Mostrar:

- AuthN;
- AuthZ;
- tenant;
- secrets;
- KMS;
- audit logs;
- WAF;
- bot defense;
- backups.

---

1.12 ADR — Architecture Decision Records

Diretório recomendado:

docs/adr/

Formato:

# ADR-XXX — Decisão

## Status

## Context

## Decision

## Alternatives

## Consequences

## Security Impact

## Reliability Impact

## Data/Privacy Impact

## Rollback

ADRs para decisões importantes:

- auth;
- sessions;
- JWT;
- BFF;
- multi-tenancy;
- database;
- RLS;
- cache;
- queue;
- storage;
- encryption;
- rate limiting;
- logging;
- backup;
- AI/MCP.


---

1.13 Control Mapping

Controles críticos devem, quando aplicável, mapear para referências estáveis:

- OWASP ASVS `v5.0.0-x.y.z`;
- OWASP Top 10:2025;
- OWASP API Security Top 10:2023;
- NIST SSDF;
- NIST 800-63-4;
- PCI DSS;
- WCAG 2.2;
- OWASP GenAI / Agentic / MCP.

Não usar somente nome genérico quando existir requisito verificável versionado.

---

1.14 Security Requirements as Code / Policy

Quando viável:

REQUIREMENT
  ↓
CONTROL
  ↓
TEST
  ↓
CI GATE
  ↓
EVIDENCE

Políticas críticas repetíveis devem migrar de documentação manual para validação automatizada sem eliminar review humano.

---

1.15 Insecure Defaults Audit

Configuração ausente deve falhar para o estado seguro.

Exemplos proibidos em produção:

`REQUIRE_AUTH` ausente → autenticação desligada

`DEBUG` ausente → debug ligado

`TLS_VERIFY` ausente → verificação desligada

`SECRET_KEY` ausente → segredo de exemplo

`ADMIN_PASSWORD` ausente → senha conhecida

Regra:

MISSING SECURITY CONFIG
→ FAIL CLOSED / FAIL FAST

Não:

MISSING SECURITY CONFIG
→ CONTINUE INSECURE

Auditar:

- fallback secrets;
- default credentials;
- fail-open switches;
- weak crypto defaults;
- permissive ACL/CORS/file modes;
- debug leakage.

Para finding real, provar:

DEFAULT REACHABLE
+
INSECURE VALUE ACTIVE
+
SECURITY SINK
+
PRODUCTION REACHABILITY

---

1.16 Fail-Closed Configuration Contract

Cada configuração de segurança crítica deve declarar:

- nome;
- secure default;
- comportamento quando ausente;
- comportamento quando inválida;
- environment scope;
- owner;
- test;
- startup validation.

Para produção, preferir:

CONFIG INVALID / MISSING
→ STARTUP FAILURE

em vez de fallback silencioso.

---

⚫ COFRE MÁXIMO

- AppSec formal;
- architecture board;
- security champion;
- risk acceptance formal;
- independent audits;
- vulnerability disclosure;
- supplier governance;
- metrics executivas;
- tabletop exercises;
- separation of duties.

---

PARTE 2 — IDENTITY, AUTHENTICATION, AUTHORIZATION, SESSION E ANTI-ABUSE

🟢 BÁSICO

2.1 Password Storage

Preferir:

ARGON2ID
   ↓
SCRYPT
   ↓
BCRYPT / PBKDF2 quando justificável

OWASP recomenda Argon2id para novos sistemas; um perfil mínimo atualmente documentado é 19 MiB, duas iterações e paralelismo 1, embora a configuração deva ser calibrada ao ambiente.

Nunca:

PLAINTEXT
MD5
SHA-1
SHA-256(password)
REVERSIBLE PASSWORD ENCRYPTION

---

2.2 Password Policy

NIST SP 800-63B-4 estabelece:

SINGLE FACTOR:
mínimo 15 caracteres

PARTE DE MFA:
mínimo 8

Também:

- permitir 64+ caracteres;
- password manager;
- autofill;
- paste;
- blocklist de senhas comprometidas;
- sem composição arbitrária;
- sem troca periódica obrigatória sem comprometimento.

---

2.3 Authentication

Servidor é autoridade.

REQUEST
  ↓
CREDENTIAL / SESSION
  ↓
VALIDATION
  ↓
IDENTITY
  ↓
ACCOUNT STATE

Frontend redirect:

if (!user) ...

é UX.

Não segurança suficiente.

---

2.4 Recovery

- token aleatório;
- single-use;
- TTL;
- armazenar de forma segura;
- rate limit;
- resposta anti-enumeration;
- invalidar após uso;
- notificar alteração;
- revisar sessões;
- não confiar em "Host" arbitrário para construir link.

---

🟡 INTERMEDIÁRIO

2.5 MFA

Obrigatório conforme risco para:

- owner;
- admin;
- infraestrutura;
- cloud;
- secrets;
- funções críticas.

Preferência:

PASSKEY / WEBAUTHN
       ↓
TOTP
       ↓
FALLBACK ADEQUADO

---

2.6 Biometrics

BIOMETRIC
≠
SERVER-STORED PASSWORD

Preferir:

LOCAL BIOMETRIC
     ↓
UNLOCK PRIVATE KEY
     ↓
WEBAUTHN
     ↓
SERVER VERIFIES SIGNATURE

NIST não considera biometria isolada um autenticador e prefere verificação biométrica local associada a autenticador físico.

---

2.7 Session Lifecycle

Toda sessão possui:

CREATE
  ↓
ROTATE
  ↓
USE
  ↓
REFRESH
  ↓
EXPIRE
  ↓
REVOKE
  ↓
DESTROY

Definir:

- idle timeout;
- absolute timeout;
- renewal;