#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jarvis_weaponize_repo.py // J.A.R.V.I.S. Autonomous Weaponization Engine
========================================================================
Protocolo de Segurança Soberana SSP-v13.4 | Pure Python 3.12 Standard Library

Transforma um repositório bruto do GitHub em uma ARMA OPERACIONAL ATIVA:
1. Ingestão de documentação, árvore de arquivos e especificações da ferramenta.
2. Extração de sintaxe de comandos, flags CLI, runtime e receitas de uso real.
3. Auditoria estática de segurança fail-closed (SSP-v13).
4. Cristalização e forja da habilidade canônica: skills/<nome>/SKILL.md.
5. Registro de status no banco SQLite (state/arsenal_library.sqlite).
"""

import os
import sys
import time
import json
import re
import sqlite3
import argparse
import urllib.request
import urllib.error
from pathlib import Path

# UTF-8 Console Support
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

REGISTRY_ROOT = Path(r"E:\.skill-registry")
SKILLS_DIR = REGISTRY_ROOT / "skills"
STAGING_DIR = REGISTRY_ROOT / "staging" / "weaponize"
DB_FILE = REGISTRY_ROOT / "state" / "arsenal_library.sqlite"
MCP_CONFIG = Path.home() / ".gemini" / "config" / "mcp_config.json"

def resolve_token() -> str:
    # 1. Variáveis de ambiente
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN") or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token and token.strip():
        return token.strip()
    # 2. Configuração local protegida do MCP (fora do repositório)
    if MCP_CONFIG.exists():
        try:
            cfg = json.loads(MCP_CONFIG.read_text(encoding="utf-8"))
            gh = cfg.get("mcpServers", {}).get("github-mcp-server", {})
            token = gh.get("env", {}).get("GITHUB_PERSONAL_ACCESS_TOKEN")
            if token and token.strip():
                return token.strip()
        except Exception:
            pass
    return ""

def get_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "JARVIS-Weaponization-Engine/2.0 (robertoatila)",
        "X-GitHub-Api-Version": "2022-11-28"
    }

def fetch_repo_meta(repo: str, token: str) -> dict:
    repo = repo.strip().replace("https://github.com/", "").strip("/")
    url = f"https://api.github.com/repos/{repo}"
    req = urllib.request.Request(url, headers=get_headers(token))
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"[ERRO API {e.code}] Não foi possível obter metadados de {repo}: {e.reason}")
        return {}
    except Exception as e:
        print(f"[ERRO] {e}")
        return {}

def fetch_repo_readme(repo: str, token: str) -> str:
    repo = repo.strip().replace("https://github.com/", "").strip("/")
    url = f"https://api.github.com/repos/{repo}/readme"
    headers = get_headers(token)
    headers["Accept"] = "application/vnd.github.raw+json"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        return ""

def audit_security_patterns(text: str) -> tuple[bool, list[str]]:
    """
    Verificação estática de segurança fail-closed conforme SSP-v13.
    Bloqueia repositórios com assinaturas flagrantes de malware/exfiltração descontrolada.
    """
    findings = []
    suspicious_patterns = [
        (r"eval\(base64_decode", "Obfuscated base64 eval block"),
        (r"discord\.com/api/webhooks/[0-9]+/[A-Za-z0-9_-]+", "Discord webhook exfiltration hook"),
        (r"api\.telegram\.org/bot[0-9]+:[A-Za-z0-9_-]+", "Telegram bot token exfiltration hook"),
        (r"cmd\.exe\s+/c\s+powershell.*-enc", "Hidden base64-encoded powershell command")
    ]
    for pattern, label in suspicious_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            findings.append(label)

    passed = len(findings) == 0
    return passed, findings

def extract_cli_commands(readme: str) -> list[str]:
    """
    Extrai exemplos de linhas de comando executáveis do README.
    """
    commands = []
    # Blocos de código bash/sh/powershell/console
    code_blocks = re.findall(r"```(?:bash|sh|shell|console|powershell|cmd)?\r?\n([\s\S]*?)```", readme, re.IGNORECASE)
    for block in code_blocks:
        for line in block.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Remove prompts comuns ($ >)
            clean_cmd = re.sub(r"^[\$#>]\s*", "", line).strip()
            if clean_cmd and len(clean_cmd) > 3 and not clean_cmd.startswith("//"):
                commands.append(clean_cmd)
                if len(commands) >= 8:
                    break
        if len(commands) >= 8:
            break
    return commands

def weaponize(repo: str):
    token = resolve_token()
    clean_repo = repo.strip().replace("https://github.com/", "").strip("/")
    short_name = clean_repo.split("/")[-1].lower()
    
    print("=" * 80)
    print(f" ⚔️  J.A.R.V.I.S. WEAPONIZATION PROTOCOL // ALVO: {clean_repo}")
    print("=" * 80)

    # 1. Obtenção de metadados
    print("[1/5] Extraindo especificações e telemetria do GitHub...")
    meta = fetch_repo_meta(clean_repo, token)
    if not meta:
        print(f"[FALHA] Repositório {clean_repo} inacessível.")
        return

    stars = meta.get("stargazers_count", 0)
    desc = meta.get("description") or "Sem descrição fornecida."
    lang = meta.get("language") or "Multi-linguagem"
    homepage = meta.get("homepage") or ""
    topics = meta.get("topics") or []
    license_name = meta.get("license", {}).get("name") if meta.get("license") else "Não especificada"

    print(f"      Nome: {meta.get('full_name')} | Estrelas: {stars:,} ⭐ | Linguagem: {lang}")
    print(f"      Licença: {license_name}")

    # 2. Obtenção do README e documentação
    print("[2/5] Baixando inteligência e manual de instruções (README)...")
    readme = fetch_repo_readme(clean_repo, token)
    if not readme:
        print("      [AVISO] README não encontrado via API. Gerando esqueleto padrão.")

    # 3. Auditoria de Segurança SSP-v13
    print("[3/5] Executando auditoria fail-closed (SSP-v13)...")
    sec_passed, findings = audit_security_patterns(readme)
    if not sec_passed:
        print(f"      [BLOQUEADO] Assinaturas maliciosas detectadas: {findings}")
        print("      Cancelando weaponização por diretiva de segurança.")
        return
    print("      [PASS] Nenhuma anomalia crítica de exfiltração encontrada.")

    # 4. Extração de capacidades e comandos de ação
    print("[4/5] Destilando comandos operacionais e sintaxe CLI...")
    extracted_cmds = extract_cli_commands(readme)
    cmd_section = ""
    if extracted_cmds:
        cmd_section = "\n```bash\n" + "\n".join(extracted_cmds[:6]) + "\n```"
    else:
        cmd_section = f"\n```bash\n# Uso canônico padrão para {short_name}:\n{short_name} --help\n```"

    # 5. Forjamento da Skill Canônica
    print("[5/5] Forjando habilidade canônica e manual de combate...")
    skill_dir = SKILLS_DIR / short_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skill_dir / "SKILL.md"

    # Classificação tática
    topics_str = " ".join(topics).lower()
    full_text = f"{clean_repo} {desc} {topics_str}".lower()
    squad_name = "Hyperion-FullStack"
    if re.search(r"exploit|payload|reversing|decompile|apktool|jadx|ghidra|pentest|bypass|malware", full_text):
        squad_name = "Cyberspace-Offensive"
    elif re.search(r"firewall|hardening|security|privacy|audit|shield|crypto", full_text):
        squad_name = "Aegis-Defensive"
    elif re.search(r"agent|ai|llm|rag|gpt|claude|gemini|swarm|autogen", full_text):
        squad_name = "Neuro-Cognitive"
    elif re.search(r"network|proxy|kernel|ebpf|xdp|packet|tcp|udp", full_text):
        squad_name = "Tactical-Kernel"

    skill_content = f"""---
name: {short_name}
description: Ferramenta canônica {clean_repo} ({stars:,} estrelas). {desc[:120]}
squad: {squad_name}
version: 1.0.0
upstream: https://github.com/{clean_repo}
---

# {short_name.upper()} // Habilidade Operacional J.A.R.V.I.S.

## 1. Visão Tática e Propósito
- **Repositório Upstream:** [{clean_repo}](https://github.com/{clean_repo}) ({stars:,} estrelas ⭐)
- **Linguagem / Stack:** {lang}
- **Esquadrão Responsável:** `{squad_name}`
- **Missão:** {desc}

## 2. Diretrizes de Uso para o J.A.R.V.I.S.
- **Soberania Local:** Operação determinística em conformidade com o Protocolo SSP-v13.
- **Consumo de Contexto:** Não leia o código fonte inteiro a menos que seja estritamente necessário. Use os comandos abaixo para executar a tarefa diretamente no terminal.

## 3. Comandos Homologados & Receitas de Execução
{cmd_section}

## 4. Integração em Missões Autônomas
Quando o operador solicitar tarefas relacionadas a `{short_name}`:
1. Verifique se o executável ou dependência está presente via terminal (`where {short_name}` ou `Get-Command {short_name}`).
2. Se ausente, sugira a instalação via gestor de pacotes (ex: `winget`, `pip`, `npm`, `cargo`) ou clone isolado em `staging/`.
3. Execute a ação solicitada, analise os resultados e entregue o objetivo final.
"""

    skill_file.write_text(skill_content.strip() + "\n", encoding="utf-8")
    print(f"      [SUCESSO] Habilidade canônica forjada em: {skill_file}")

    # Atualiza status no SQLite
    if DB_FILE.exists():
        try:
            conn = sqlite3.connect(str(DB_FILE))
            with conn:
                conn.execute("""
                    UPDATE arsenal_tools
                    SET capabilities = json_insert(capabilities, '$[#]', 'weaponized'),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE full_name = ? OR name = ?;
                """, (clean_repo, short_name))
            conn.close()
            print("      [BANCO] Status atualizado no Arsenal SQLite.")
        except Exception as e:
            print(f"      [AVISO] Erro ao atualizar status no SQLite: {e}")

    print("\n" + "=" * 80)
    print(f" 🗡️  ARMA PRONTA PARA COMBATE: {short_name} agora é uma skill utilizável!")
    print("=" * 80)

def main():
    parser = argparse.ArgumentParser(description="J.A.R.V.I.S. Autonomous Weaponization Engine")
    parser.add_argument("--repo", "-r", type=str, help="Repositório do GitHub (ex: 'skylot/jadx' ou 'https://github.com/skylot/jadx')")
    parser.add_argument("--batch", "-b", type=str, help="Arquivo com múltiplos repositórios para weaponizar em lote")

    args = parser.parse_args()

    if args.repo:
        weaponize(args.repo)
    elif args.batch:
        p = Path(args.batch)
        if p.exists():
            repos = [line.strip() for line in p.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]
            for r in repos:
                weaponize(r)
                time.sleep(1)
        else:
            print(f"[ERRO] Arquivo {args.batch} não encontrado.")
    else:
        print("\nInforme o repositório para weaponizar:")
        try:
            target = input("Repo > ").strip()
            if target:
                weaponize(target)
        except (KeyboardInterrupt, EOFError):
            pass

if __name__ == "__main__":
    main()
