#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
install_obsidian_plugins.py // J.A.R.V.I.S. Obsidian Plugin Installer
Downloads and installs top starred community plugins directly into .obsidian/plugins/
and enables them in community-plugins.json and app.json.
"""

import os
import sys
import json
import urllib.request
from pathlib import Path

REGISTRY_ROOT = Path(__file__).resolve().parent.parent
OBSIDIAN_DIR = REGISTRY_ROOT / ".obsidian"
PLUGINS_DIR = OBSIDIAN_DIR / "plugins"

sys.path.insert(0, str(REGISTRY_ROOT / "tooling"))
from sync_starred_repos import resolve_token

PLUGINS_TO_INSTALL = [
    {
        "repo": "blacksmithgu/obsidian-dataview",
        "id": "dataview",
        "name": "Dataview"
    },
    {
        "repo": "Vinzent03/obsidian-git",
        "id": "obsidian-git",
        "name": "Obsidian Git"
    },
    {
        "repo": "brianpetro/obsidian-smart-connections",
        "id": "smart-connections",
        "name": "Smart Connections"
    },
    {
        "repo": "SilentVoid13/Templater",
        "id": "templater-obsidian",
        "name": "Templater"
    },
    {
        "repo": "logancyang/obsidian-copilot",
        "id": "copilot",
        "name": "Copilot"
    },
    {
        "repo": "YishenTu/claudian",
        "id": "claudian",
        "name": "Claudian (Claude Code / Codex)"
    }
]


def install_plugin(token: str, repo: str, plugin_id: str, name: str):
    headers = {"User-Agent": "JARVIS-Plugin-Installer"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    print(f"[PLUGIN-INSTALL] Buscando última release de {repo} ({name})...")
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[ERRO] Falha ao buscar release para {repo}: {e}")
        return False

    assets = {a.get("name"): a.get("browser_download_url") for a in data.get("assets", [])}
    required = ["main.js", "manifest.json"]
    optional = ["styles.css"]

    target_dir = PLUGINS_DIR / plugin_id
    target_dir.mkdir(parents=True, exist_ok=True)

    for item in required + optional:
        if item in assets:
            dl_url = assets[item]
            file_path = target_dir / item
            print(f"  -> Baixando {item}...")
            dl_req = urllib.request.Request(dl_url, headers={"User-Agent": "JARVIS"})
            try:
                with urllib.request.urlopen(dl_req, timeout=30) as dl_resp:
                    file_path.write_bytes(dl_resp.read())
            except Exception as e:
                print(f"  [AVISO] Erro ao baixar {item}: {e}")
                if item in required:
                    return False
        elif item in required:
            print(f"  [ERRO] Arquivo obrigatório {item} não encontrado nos assets de {repo}!")
            return False

    print(f"[OK] {name} instalado com sucesso em .obsidian/plugins/{plugin_id}")
    return True


def enable_community_plugins(installed_ids):
    OBSIDIAN_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Update app.json to enable safeMode: false
    app_json_path = OBSIDIAN_DIR / "app.json"
    app_data = {}
    if app_json_path.exists():
        try:
            app_data = json.loads(app_json_path.read_text(encoding="utf-8"))
        except Exception:
            app_data = {}
    app_data["safeMode"] = False
    app_json_path.write_text(json.dumps(app_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print("[CONFIG] app.json atualizado: safeMode = false (plugins comunitários liberados).")

    # 2. Update community-plugins.json
    comm_plugins_path = OBSIDIAN_DIR / "community-plugins.json"
    enabled = []
    if comm_plugins_path.exists():
        try:
            enabled = json.loads(comm_plugins_path.read_text(encoding="utf-8"))
        except Exception:
            enabled = []
    
    for pid in installed_ids:
        if pid not in enabled:
            enabled.append(pid)

    comm_plugins_path.write_text(json.dumps(enabled, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[CONFIG] community-plugins.json atualizado com {len(enabled)} plugins habilitados: {enabled}")


def main():
    token = resolve_token()
    PLUGINS_DIR.mkdir(parents=True, exist_ok=True)

    installed = []
    for p in PLUGINS_TO_INSTALL:
        ok = install_plugin(token, p["repo"], p["id"], p["name"])
        if ok:
            installed.append(p["id"])

    if installed:
        enable_community_plugins(installed)
        print(f"\n[SUCESSO TOTAL] {len(installed)} plugins do Obsidian instalados e ativados no seu cofre!")


if __name__ == "__main__":
    main()
