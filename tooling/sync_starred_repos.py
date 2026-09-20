#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_starred_repos.py // J.A.R.V.I.S. Starred Repositories Synchronizer
Pure Python 3.12 Standard Library. Zero pip dependencies.
Fetches starred repositories from GitHub API using the sovereign PAT in mcp_config.json,
updates cache/starred_catalog.json, and regenerates 06 - GitHub Starred Repositories.md
with strict markdownlint compliance.
"""

import os
import sys
import json
import re
import urllib.request
import urllib.error
from pathlib import Path

REGISTRY_ROOT = Path(__file__).resolve().parent.parent
CACHE_FILE = REGISTRY_ROOT / "cache" / "starred_catalog.json"
DOC_FILE = REGISTRY_ROOT / "06 - GitHub Starred Repositories.md"
MCP_CONFIG = Path.home() / ".gemini" / "config" / "mcp_config.json"


def resolve_token() -> str:
    # 1. Environment
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN") or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token.strip()
    # 2. mcp_config.json
    if MCP_CONFIG.exists():
        try:
            cfg = json.loads(MCP_CONFIG.read_text(encoding="utf-8"))
            gh = cfg.get("mcpServers", {}).get("github-mcp-server", {})
            token = gh.get("env", {}).get("GITHUB_PERSONAL_ACCESS_TOKEN")
            if token:
                return token.strip()
        except Exception as e:
            print(f"[WARN] Failed reading token from {MCP_CONFIG}: {e}", file=sys.stderr)
    return ""


def fetch_starred(token: str, max_pages: int = 40, per_page: int = 100):
    headers = {
        "User-Agent": "JARVIS-Starred-Sync",
        "Accept": "application/vnd.github.v3+json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    all_items = []
    print(f"[JARVIS-SYNC] Iniciando busca paginada no GitHub (até {max_pages} páginas, {per_page} itens/pág)...")

    for page in range(1, max_pages + 1):
        url = f"https://api.github.com/user/starred?per_page={per_page}&page={page}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if not data:
                    print(f"[JARVIS-SYNC] Página {page} vazia. Término da paginação.")
                    break
                print(f"[JARVIS-SYNC] Página {page}: obtidos {len(data)} repositórios.")
                all_items.extend(data)
                # Check link header for last page
                link_header = resp.headers.get("Link", "")
                if 'rel="next"' not in link_header and page > 1:
                    print(f"[JARVIS-SYNC] Última página alcançada ({page}).")
                    break
        except urllib.error.HTTPError as e:
            print(f"[ERROR] HTTP {e.code} ao buscar página {page}: {e.reason}", file=sys.stderr)
            break
        except Exception as e:
            print(f"[ERROR] Erro ao buscar página {page}: {e}", file=sys.stderr)
            break

    return all_items


def classify_repo(r: dict) -> str:
    name = r.get("name", "")
    desc = r.get("description") or ""
    topics = r.get("topics") or []
    topics_str = " ".join(topics) if isinstance(topics, list) else ""
    text = f"{name} {desc} {topics_str}".lower()

    if re.search(r"obfus|hook|evasion|antivm|debugger|inject|rootkit|payload|bypass|exploit|killer|malware|offensive|pentest|reversing|ghidra|ida|cve|metasploit", text):
        return "Cibersegurança, Pentest & Evasão"
    elif re.search(r"adblock|hblock|firewall|hardening|security|privacy|audit|shield|guard|antivirus|cleaner|defense|snyk|trivy|fail2ban|zerotrust", text):
        return "Hardening, Defesa & Privacidade"
    elif re.search(r"agent|ai|llm|rag|gpt|claude|gemini|langchain|autogen|crewai|vllm|dspy|prompt|embedding|qdrant|chroma|ollama|deepseek|fine-tun", text):
        return "Agentes de IA, RAG & LLMs"
    elif re.search(r"bgp|xdp|ebpf|network|socket|packet|router|vpn|wireguard|proxy|tunnel|dns|pcap|tcp|udp|http|quic", text):
        return "Redes, Proxies & Kernel / XDP"
    else:
        return "DevTools, Compiladores & Linguagens"


def main():
    token = resolve_token()
    if not token:
        print("[ERROR] Token do GitHub não encontrado em ambiente ou mcp_config.json!", file=sys.stderr)
        sys.exit(1)

    print("[JARVIS-SYNC] Token resolvido com sucesso.")

    # Load existing cache
    existing_items = []
    if CACHE_FILE.exists():
        try:
            existing_items = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            print(f"[JARVIS-SYNC] Cache atual carregado: {len(existing_items)} repositórios.")
        except Exception as e:
            print(f"[WARN] Falha ao ler cache existente: {e}", file=sys.stderr)

    existing_map = {}
    for item in existing_items:
        key = item.get("full_name") or item.get("name")
        if key:
            existing_map[key] = item

    # Fetch from GitHub
    fetched = fetch_starred(token, max_pages=40, per_page=100)
    print(f"[JARVIS-SYNC] Total de repositórios obtidos do GitHub: {len(fetched)}")

    if not fetched:
        print("[WARN] Nenhum repositório retornado do GitHub. Abortando atualização.")
        return

    new_count = 0
    updated_count = 0

    for r in fetched:
        full_name = r.get("full_name", "")
        name = r.get("name", "")
        key = full_name or name
        if not key:
            continue

        normalized = {
            "name": name,
            "full_name": full_name,
            "html_url": r.get("html_url", f"https://github.com/{full_name}"),
            "description": (r.get("description") or "").replace("\n", " ").strip(),
            "stars": r.get("stargazers_count", 0),
            "language": r.get("language") or "Unknown",
            "topics": r.get("topics") or []
        }

        if key in existing_map:
            # Update stars and topics
            existing_map[key].update(normalized)
            updated_count += 1
        else:
            existing_map[key] = normalized
            new_count += 1

    # Final combined list sorted by stars descending
    combined = list(existing_map.values())
    combined.sort(key=lambda x: x.get("stars", 0), reverse=True)

    # Save cache
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(combined, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[JARVIS-SYNC] Cache atualizado em {CACHE_FILE}: {len(combined)} repositórios ({new_count} novos, {updated_count} atualizados).")

    # Classify into clusters
    clusters = {
        "Cibersegurança, Pentest & Evasão": [],
        "Hardening, Defesa & Privacidade": [],
        "Agentes de IA, RAG & LLMs": [],
        "Redes, Proxies & Kernel / XDP": [],
        "DevTools, Compiladores & Linguagens": []
    }

    for item in combined:
        cat = classify_repo(item)
        clusters[cat].append(item)

    # Regenerate 06 - GitHub Starred Repositories.md
    total_starred = len(combined)
    lines = []
    lines.append("---")
    lines.append("title: 06 - GitHub Starred Repositories (Pipeline de Expansao)")
    lines.append("type: starred-catalog")
    lines.append(f"total_github_starred: {total_starred}")
    lines.append(f"mined_in_cache: {total_starred}")
    lines.append("user: robertoatila")
    lines.append("tags:")
    lines.append("  - github-starred")
    lines.append("  - candidate-pipeline")
    lines.append("  - sovereign-miner")
    lines.append("---")
    lines.append("")
    lines.append(f"# Catalogo de Repositorios Favoritados no GitHub ({total_starred} Total)")
    lines.append("")
    lines.append("> [!TIP] Tesouro Bruto do Arsenal")
    lines.append(f"> O usuario possui **{total_starred} repositorios favoritados** no GitHub. Este indice lista os **{total_starred} repositorios minerados** nesta rodada, categorizados automaticamente para analise e proposta via J.A.R.V.I.S.")
    lines.append("")
    lines.append("[[00 - J.A.R.V.I.S. Cognitive Vault|Voltar ao Painel Mestre]]")
    lines.append("")
    lines.append("## Como Ingerir Qualquer um Desses Repositorios")
    lines.append("")
    lines.append("```powershell")
    lines.append("# Exemplo para ingerir o KiExitDispatcher/GoDefender:")
    lines.append("skillctl ingest KiExitDispatcher/GoDefender")
    lines.append("")
    lines.append("# Ou abra o J.A.R.V.I.S. Command Center no navegador:")
    lines.append("skillctl jarvis")
    lines.append("```")
    lines.append("")

    for cat_name, cat_items in clusters.items():
        cat_items.sort(key=lambda x: x.get("stars", 0), reverse=True)
        lines.append(f"## {cat_name} ({len(cat_items)} repositorios)")
        lines.append("")
        lines.append("| Repositorio | Estrelas | Linguagem | Descricao | Acao J.A.R.V.I.S. |")
        lines.append("| :--- | :---: | :---: | :--- | :--- |")

        for r in cat_items:
            full_name = r.get("full_name") or r.get("name")
            html_url = r.get("html_url", f"https://github.com/{full_name}")
            stars = r.get("stars", 0)
            lang = r.get("language") or "Unknown"
            desc = r.get("description") or ""
            if len(desc) > 75:
                desc = desc[:72] + "..."
            desc = desc.replace("|", "/")
            lines.append(f"| [{full_name}]({html_url}) | {stars} | {lang} | {desc} | `skillctl ingest {full_name}` |")

        lines.append("")

    DOC_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[JARVIS-SYNC] Documento regenerado com sucesso em {DOC_FILE} com estrita conformidade markdownlint.")


if __name__ == "__main__":
    main()
