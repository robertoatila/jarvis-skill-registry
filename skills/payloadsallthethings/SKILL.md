---
name: payloadsallthethings
description: Curated OWASP attack dictionaries and bypass payloads for authorized web security audits.
---

# payloadsallthethings // Offensive DAST & Attack Dictionary Suite

> [!WARNING] ðŸ›¡ï¸ Protocolo de Contencao e Sandbox (Fail-Closed)
> Esta habilidade contem dicionarios de teste de vulnerabilidades (OWASP Top 10, SQLi, XSS, SSRF, SSTI, bypass de autenticacao).
> Homologada com **Waiver de Seguranca WAIVER-2026-SEC-010** para auditorias defensivas no MarkitosSystem e ambientes autorizados.
> **Regra de Ouro**: Apenas referencia passiva de vetores e validacao de sanitizacao; execucao direta proibida sem confirmacao explicita do operador.

## Capacidades Operacionais
1. **Auditoria DAST**: Cargas de teste para validacao de sanitizacao de inputs (RFC 10017 / BFF).
2. **Cheatsheets de Bypass**: Verificacao de regras de WAF, validacao de encoding e normalizacao de URL.
3. **Validacao de Contramedidas**: Comparacao contra os 4 niveis de maturidade do protocolo SEGURANCA v10.

## Instrucoes de Execucao
- Carregamento lazy sob demanda para analise de seguranca ofensiva/defensiva.
- Nunca emitir payloads brutos em ambientes de producao sem autorizacao formal.