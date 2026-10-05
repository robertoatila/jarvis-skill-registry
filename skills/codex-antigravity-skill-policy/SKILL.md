---
name: codex-antigravity-skill-policy
description: Use para orientar Codex, Antigravity, Claude Code e agentes quando houver.
---
# Codex / Antigravity Skill Policy

Não leia todas as skills.
Não exija comandos com cifrão.
Leia a skill roteadora correta e depois o pacote certo.

Mapa:
- layout, UI, CSS, HTML, redesign, dashboard, login, home, register -> markitos-layout-router
- segurança, auth, JWT, RBAC, XSS, SQLi, CSRF, IDOR, CORS -> markitos-security-router
- backend, Java, Spring Boot, controller, service, repository, DTO, endpoint, API -> markitos-backend-router
- database, MySQL, SQL, schema, migration, query, JPA, Hibernate, DataInitializer -> markitos-database-router
- Railway, Docker, deploy, logs, healthcheck, variáveis, build -> markitos-deploy-router
- bug, review, refatoração, regressão, diff, patch, pre-push -> markitos-review-router

Para MarkitosSystem, nunca usar apenas frontend-developer em tarefas visuais.
Para MarkitosSystem, nunca usar apenas backend genérico em tarefas Spring Boot.
Para MarkitosSystem, nunca usar apenas database genérico em tarefas MySQL.
