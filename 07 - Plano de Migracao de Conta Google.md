---
title: 07 - Plano de Migracao de Conta Google & Preservacao Soberana
type: migration-guide
created: 2026-09-04
status: READY_TO_USE
tags:
  - migration
  - google-account
  - antigravity
  - sovereignty
  - disaster-recovery
---

# 🛡️ Plano de Migração de Conta Google // Antigravity & Skill Registry

> [!IMPORTANT] 🌟 Resumo Executivo: Vai Mudar Muita Coisa?
> **NÃO! Quase nada muda.** Mais de **95% do seu ambiente de trabalho, arsenal e configurações é 100% LOCAL e SOBERANO** no seu computador Windows (`C:\Users\Ad\` e `E:\.skill-registry\`).
>
> A sua conta Google é usada pelo Antigravity **apenas para autenticação e cota do modelo de IA na nuvem (Gemini)**. As suas skills, MCPs, tokens, scripts, ferramentas e notas do Obsidian **não pertencem ao Google** e não são apagados quando você troca de conta.

---

## 📊 Matriz Comparativa: O Que Fica vs. O Que Muda

| Componente | Localização | Afetado pela Troca de Conta? | Ação Necessária |
| :--- | :--- | :---: | :--- |
| **Arsenal Canônico (143 Skills)** | `E:\.skill-registry\skills\` | ❌ **NÃO (Zero Risco)** | Nenhuma. Fica 100% intacto no disco `E:`. |
| **Skills do Workspace (165)** | `C:\Users\Ad\.gemini\skills\` | ❌ **NÃO (Zero Risco)** | Nenhuma. Pertencem ao seu usuário Windows `Ad`. |
| **Servidores MCP (`mcp_config.json`)** | `C:\Users\Ad\.gemini\config\` | ❌ **NÃO (Zero Risco)** | Nenhuma. Chrome DevTools e GitHub MCP continuam configurados. |
| **Token do GitHub (`ghp_...`)** | `mcp_config.json` | ❌ **NÃO (Zero Risco)** | Nenhuma. O GitHub é independente do Google. |
| **Catálogo de Favoritos (2.168)** | `E:\.skill-registry\cache\` | ❌ **NÃO (Zero Risco)** | Nenhuma. 500 já minerados e cacheados localmente. |
| **Obsidian Vault & Canvas** | `E:\.skill-registry\` | ❌ **NÃO (Zero Risco)** | Nenhuma. O Obsidian é offline e perpétuo. |
| **J.A.R.V.I.S. Command Center HUD** | `http://localhost:8899/` | ❌ **NÃO (Zero Risco)** | Nenhuma. Servidor local .NET/PowerShell. |
| **Login no Antigravity IDE** | App Antigravity | ⚠️ **SIM** | Fazer logout da conta antiga e login com a nova conta. |
| **Plano / Assinatura de IA** | Nuvem Google | ⚠️ **SIM** | A nova conta Google precisa estar com a assinatura ativa. |
| **Histórico de Chats na Nuvem** | Nuvem Google | ⚠️ **SIM** | Chats sincronizados na nuvem antiga não aparecem na nova. *(Os logs locais em `brain/` continuam salvos no disco)*. |

---

## 🚀 Roteiro de Migração em 3 Etapas Simples

### Etapa 1: Pré-Migração (Fazer antes de trocar a conta)

Gere um instantâneo de segurança criptográfico de todas as suas configurações locais com 1 comando:

```powershell
# No terminal PowerShell na raiz do projeto:
skillctl backup
```

- **O que ele faz:** Compacta `mcp_config.json`, todas as 165 skills locais, o manifesto da release e o estado soberano em um arquivo ZIP com hash SHA-256 salvo em `E:\.skill-registry\backups\`.
- **Resultado:** Backup blindado pronto para qualquer eventualidade.

---

### Etapa 2: A Troca da Conta (No dia da migração)

1. Certifique-se de que a **nova conta Google** já está com o plano contratado/ativo (Google One AI Premium / Antigravity).
2. Abra o **Antigravity IDE**.
3. Clique no ícone de perfil/avatar (canto da janela ou no menu de configurações do IDE).
4. Clique em **"Sign Out"** (ou "Desconectar").
5. Clique em **"Sign In with Google"** e entre com as credenciais da **nova conta Google**.
6. Conceda as permissões de acesso ao Antigravity.

---

### Etapa 3: Pós-Migração (Auditoria de Saúde em 1 Comando)

Logo após fazer login na nova conta, valide se o ambiente reconheceu tudo perfeitamente:

```powershell
skillctl health
```

*(ou `skillctl verify-migration`)*

O J.A.R.V.I.S. executará automaticamente **7 verificações de integridade**:

1. ✅ Integridade do arquivo `mcp_config.json`
2. ✅ Validação do Token do GitHub (`robertoatila`) via REST API
3. ✅ Contagem das 165 skills ativas no diretório do workspace
4. ✅ Validação das 143 skills canônicas do arsenal
5. ✅ Validação da Merkle Root criptográfica da Release Hyperion
6. ✅ Integridade dos 7 MOCs e do Canvas no Obsidian
7. ✅ Comunicação com o servidor do J.A.R.V.I.S. na porta `8899`

---

## 🛟 Plano de Contingência (Disaster Recovery)

Se por qualquer motivo o instalador da nova conta tentar sobrescrever arquivos de configuração locais:

1. Vá até a pasta `E:\.skill-registry\backups\`.
2. Localize o arquivo `antigravity_backup_<DATA>.zip`.
3. Para restaurar manualmente:
   - Extraia o arquivo `mcp_config.json` para `C:\Users\Ad\.gemini\config\mcp_config.json`.
   - Extraia a pasta `user_skills` para `C:\Users\Ad\.gemini\skills\`.
4. Execute `skillctl health` para confirmar que 100% dos serviços voltaram ao ar.

---

## 🔗 Navegação no Segundo Cérebro

- [[00 - J.A.R.V.I.S. Cognitive Vault|Voltar ao Painel Mestre MOC]]
- [[01 - Arsenal Map of Content|Ver Arsenal de 143 Skills]]
- [[05 - Hyperion Forensic Baseline|Ver Baseline Imutável Hyperion]]
- [[06 - GitHub Starred Repositories|Ver Repositórios Mined (2.1k)]]
