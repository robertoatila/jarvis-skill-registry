#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
star_org_profiles.py // J.A.R.V.I.S. Targeted Profile & Org Star Runner
=====================================================================
Stars all repositories with >= min_stars from target GitHub profiles/organizations,
classifying them and indexing them into SQLite FTS5 and the HUD catalog.
"""

import sys
import time
import json
import urllib.request
import urllib.error
from pathlib import Path

# Setup path to import sovereign harvest tools
TOOLING_DIR = Path(r"E:\.skill-registry\tooling")
sys.path.append(str(TOOLING_DIR))

import harvest_starred_by_keyword as hsbk

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ORGS = ["deepseek-ai", "QwenLM"]
MIN_STARS = 300

def run():
    token = hsbk.resolve_token()
    if not token:
        print("[ERRO] GitHub token not found.")
        sys.exit(1)

    headers = hsbk.get_headers(token)
    conn = hsbk.init_database()
    already_starred = hsbk.load_progress()

    print("=" * 78)
    print(" INICIANDO ESTRELAMENTO DIRECIONADO DE PERFIS / ORGS (J.A.R.V.I.S.) ")
    print(f" Organizações-Alvo  : {', '.join(ORGS)}")
    print(f" Piso Mínimo         : {MIN_STARS} ⭐")
    print(f" Repositórios no set : {len(already_starred):,}")
    print("=" * 78)

    total_newly_starred = 0
    total_already_had = 0

    for org in ORGS:
        print(f"\n[*] Obtendo repositórios da organização '{org}'...")
        page = 1
        all_repos = []
        while True:
            url = f"https://api.github.com/users/{org}/repos?per_page=100&page={page}"
            req = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=12) as resp:
                    data = json.loads(resp.read().decode())
                    if not data:
                        break
                    all_repos.extend(data)
                    if len(data) < 100:
                        break
                    page += 1
            except Exception as e:
                print(f"[ERRO] Falha ao listar {org} na página {page}: {e}")
                break

        eligible = [r for r in all_repos if r.get("stargazers_count", 0) >= MIN_STARS]
        eligible.sort(key=lambda x: x.get("stargazers_count", 0), reverse=True)
        print(f"[+] Total de repositórios em '{org}': {len(all_repos)} | Elegíveis (>= {MIN_STARS} ⭐): {len(eligible)}")

        for r in eligible:
            full_name = r["full_name"]
            stars = r["stargazers_count"]
            
            # Record in SQLite database regardless of star status
            hsbk.record_repo_in_arsenal(conn, r, f"org:{org}")

            if full_name in already_starred:
                total_already_had += 1
                continue

            # Star repository on GitHub
            star_url = f"https://api.github.com/user/starred/{full_name}"
            star_req = urllib.request.Request(star_url, data=b"", method="PUT", headers=headers)
            starred_ok = False

            for _ in range(3):
                try:
                    with urllib.request.urlopen(star_req, timeout=12) as star_resp:
                        if star_resp.status in (204, 304):
                            starred_ok = True
                            break
                except urllib.error.HTTPError as err:
                    if err.code in (403, 429):
                        time.sleep(30)
                    elif err.code == 404:
                        break
                    else:
                        time.sleep(1)
                except Exception:
                    time.sleep(1)

            if starred_ok:
                already_starred.add(full_name)
                total_newly_starred += 1
                squad_id, squad_name, caps = hsbk.classify_and_tag(r)
                caps_str = " ".join([f"#{c}" for c in caps[:3]])
                print(f"[{total_newly_starred:03d}] ⭐ {full_name:<38} | {stars:>7,} ⭐ | [{squad_name}] {caps_str}", flush=True)

                if total_newly_starred % 10 == 0:
                    hsbk.save_progress(already_starred)
                    conn.commit()

            time.sleep(0.35)

        hsbk.save_progress(already_starred)
        conn.commit()

    # Sync consolidated catalog to HUD and Drive D:
    hsbk.sync_cache_catalog_from_db(conn)

    print("\n" + "=" * 78)
    print(" ESTRELAMENTO DE PERFIS CONCLUÍDO COM SUCESSO! ")
    print(f" Novos favoritados  : {total_newly_starred}")
    print(f" Já cadastrados     : {total_already_had}")
    print(f" Total no progresso : {len(already_starred):,} repositórios")
    print("=" * 78)

if __name__ == "__main__":
    run()
