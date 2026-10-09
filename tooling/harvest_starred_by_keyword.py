#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
harvest_starred_by_keyword.py // J.A.R.V.I.S. Sovereign Arsenal & Star Runner
=============================================================================
Protocolo Soberano SSP-v13 | Pure Python 3.12 Standard Library | Zero Pip Deps

Objetivos:
1. Corrida de estrelamento paginada no GitHub palavra por palavra até 999 estrelas.
2. Ingestão, etiquetagem e classificação tática em tempo real para USO OPERACIONAL.
3. Indexação ultrarrápida em SQLite FTS5 (state/arsenal_library.sqlite) e atualização
   do catálogo HUD (cache/starred_catalog.json) e ledger (.star_progress.json).
4. Suporte a busca instantânea CLI (--search "termo") para uso em missões autônomas.
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
from datetime import datetime

# Garante suporte a UTF-8 no Windows Console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

REGISTRY_ROOT = Path(r"E:\.skill-registry")
CACHE_FILE = REGISTRY_ROOT / "cache" / "starred_catalog.json"
PROGRESS_FILE = REGISTRY_ROOT / ".star_progress.json"
DB_FILE = REGISTRY_ROOT / "state" / "arsenal_library.sqlite"
MCP_CONFIG = Path.home() / ".gemini" / "config" / "mcp_config.json"

MIN_STARS_DEFAULT = 999

# Mapeamento canônico dos 5 Esquadrões J.A.R.V.I.S.
SQUADS = {
    1: {"name": "Cyberspace", "desc": "Cibersegurança Ofensiva, Pentest, Evasão & Reversing"},
    2: {"name": "Aegis", "desc": "Hardening, Defesa Ativa, Criptografia & Privacidade"},
    3: {"name": "Neuro-Cognitive", "desc": "Agentes de IA, RAG, LLMs & Automação Inteligente"},
    4: {"name": "Tactical", "desc": "Redes, Proxies, Kernel, eBPF & Baixo Nível"},
    5: {"name": "Hyperion", "desc": "DevTools, Compiladores, Frameworks & Arquitetura"}
}

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

def init_database() -> sqlite3.Connection:
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_FILE))
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS arsenal_tools (
                full_name TEXT PRIMARY KEY,
                name TEXT,
                html_url TEXT,
                description TEXT,
                stars INTEGER,
                language TEXT,
                topics TEXT,
                keyword TEXT,
                squad_id INTEGER,
                squad_name TEXT,
                capabilities TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_stars ON arsenal_tools(stars);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_squad ON arsenal_tools(squad_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_keyword ON arsenal_tools(keyword);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_lang ON arsenal_tools(language);")

        # Tabela virtual de busca em texto completo (FTS5)
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS arsenal_fts USING fts5(
                full_name,
                name,
                description,
                topics,
                capabilities,
                content='arsenal_tools',
                content_rowid='rowid'
            );
        """)

        # Triggers de sincronização FTS5
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS arsenal_ai AFTER INSERT ON arsenal_tools BEGIN
                INSERT INTO arsenal_fts(rowid, full_name, name, description, topics, capabilities)
                VALUES (new.rowid, new.full_name, new.name, new.description, new.topics, new.capabilities);
            END;
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS arsenal_ad AFTER DELETE ON arsenal_tools BEGIN
                INSERT INTO arsenal_fts(arsenal_fts, rowid, full_name, name, description, topics, capabilities)
                VALUES ('delete', old.rowid, old.full_name, old.name, old.description, old.topics, old.capabilities);
            END;
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS arsenal_au AFTER UPDATE ON arsenal_tools BEGIN
                INSERT INTO arsenal_fts(arsenal_fts, rowid, full_name, name, description, topics, capabilities)
                VALUES ('delete', old.rowid, old.full_name, old.name, old.description, old.topics, old.capabilities);
                INSERT INTO arsenal_fts(rowid, full_name, name, description, topics, capabilities)
                VALUES (new.rowid, new.full_name, new.name, new.description, new.topics, new.capabilities);
            END;
        """)

    # Auto-bootstrap a partir de cache/starred_catalog.json se o banco estiver vazio
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM arsenal_tools;")
    count = cur.fetchone()[0]
    if count == 0 and CACHE_FILE.exists():
        try:
            print(f"[*] Inicializando banco SQLite a partir de {CACHE_FILE}...")
            raw_data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            items = raw_data if isinstance(raw_data, list) else raw_data.get("repositories", [])
            with conn:
                for item in items:
                    record_repo_in_arsenal(conn, item, "cached-seed")
            print(f"[+] Bootstrap concluído: {len(items):,} ferramentas inseridas e indexadas em SQLite FTS5!")
        except Exception as e:
            print(f"[WARN] Falha no bootstrap inicial: {e}")

    return conn

def classify_and_tag(r: dict) -> tuple[int, str, list[str]]:
    """
    Classifica o repositório em um dos 5 Esquadrões e infere etiquetas de capacidade.
    """
    name = (r.get("name") or "").lower()
    desc = (r.get("description") or "").lower()
    topics = r.get("topics") or []
    topics_str = " ".join(topics).lower() if isinstance(topics, list) else str(topics).lower()
    text = f"{name} {desc} {topics_str}"

    capabilities = []

    # Inferência de capacidades técnicas reais
    if re.search(r"cli|terminal|command-line|cmd|console", text):
        capabilities.append("cli")
    if re.search(r"sdk|library|wrapper|api-client", text):
        capabilities.append("sdk")
    if re.search(r"reverse|disassembl|decompile|apktool|jadx|ghidra|ida", text):
        capabilities.append("reverse-engineering")
    if re.search(r"exploit|payload|cve|poc|bypass|pentest|injection", text):
        capabilities.append("offensive-tool")
    if re.search(r"agent|multi-agent|swarm|autonomous|orchestrat", text):
        capabilities.append("agentic-system")
    if re.search(r"rag|embedding|vector|similarity|qdrant|chroma|pinecone", text):
        capabilities.append("vector-rag")
    if re.search(r"llm|chatgpt|openai|claude|gemini|deepseek|ollama", text):
        capabilities.append("llm-engine")
    if re.search(r"audit|scanner|sast|dast|security-check|hardening", text):
        capabilities.append("security-auditing")
    if re.search(r"ebpf|xdp|packet|sniffer|wireshark|pcap|socket", text):
        capabilities.append("low-level-network")
    if re.search(r"gui|desktop|electron|tauri|qt|flutter", text):
        capabilities.append("gui-client")
    if re.search(r"docker|container|kubernetes|k8s|helm|devops", text):
        capabilities.append("container-ops")

    # Classificação tática por Esquadrão
    if re.search(r"obfus|hook|evasion|antivm|debugger|inject|rootkit|payload|bypass|exploit|killer|malware|offensive|pentest|reversing|ghidra|ida|cve|metasploit|sniff|bruteforce|phish", text):
        squad_id = 1
        squad_name = SQUADS[1]["name"]
    elif re.search(r"adblock|firewall|hardening|security|privacy|audit|shield|guard|antivirus|cleaner|defense|snyk|trivy|fail2ban|zerotrust|crypto|secret|auth|sandbox", text):
        squad_id = 2
        squad_name = SQUADS[2]["name"]
    elif re.search(r"agent|ai|llm|rag|gpt|claude|gemini|langchain|autogen|crewai|vllm|dspy|prompt|embedding|qdrant|chroma|ollama|deepseek|vision|neural", text):
        squad_id = 3
        squad_name = SQUADS[3]["name"]
    elif re.search(r"bgp|xdp|ebpf|network|socket|packet|router|vpn|wireguard|proxy|tunnel|dns|pcap|tcp|udp|http|quic|kernel|driver", text):
        squad_id = 4
        squad_name = SQUADS[4]["name"]
    else:
        squad_id = 5
        squad_name = SQUADS[5]["name"]

    return squad_id, squad_name, capabilities

def load_progress() -> set:
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data)
        except Exception:
            pass
    return set()

def save_progress(data: set):
    try:
        temp = PROGRESS_FILE.with_suffix(".tmp")
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(sorted(list(data)), f, indent=2)
        temp.replace(PROGRESS_FILE)
    except Exception as e:
        print(f"[WARN] Falha ao salvar .star_progress.json: {e}")

def get_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "JARVIS-Sovereign-Arsenal-Runner/2.0 (robertoatila)",
        "X-GitHub-Api-Version": "2022-11-28"
    }

def record_repo_in_arsenal(conn: sqlite3.Connection, r: dict, keyword: str):
    squad_id, squad_name, caps = classify_and_tag(r)
    full_name = r.get("full_name") or r.get("name")
    name = r.get("name") or full_name.split("/")[-1]
    url = r.get("html_url") or f"https://github.com/{full_name}"
    desc = (r.get("description") or "").replace("\n", " ").strip()
    stars = r.get("stargazers_count", r.get("stars", 0))
    lang = r.get("language") or "Unknown"
    topics = r.get("topics") or []
    topics_json = json.dumps(topics, ensure_ascii=False)
    caps_json = json.dumps(caps, ensure_ascii=False)

    with conn:
        conn.execute("""
            INSERT INTO arsenal_tools (
                full_name, name, html_url, description, stars, language,
                topics, keyword, squad_id, squad_name, capabilities, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(full_name) DO UPDATE SET
                stars = excluded.stars,
                description = excluded.description,
                topics = excluded.topics,
                keyword = excluded.keyword,
                squad_id = excluded.squad_id,
                squad_name = excluded.squad_name,
                capabilities = excluded.capabilities,
                updated_at = CURRENT_TIMESTAMP;
        """, (full_name, name, url, desc, stars, lang, topics_json, keyword, squad_id, squad_name, caps_json))

def sync_cache_catalog_from_db(conn: sqlite3.Connection):
    """
    Sincroniza o SQLite com cache/starred_catalog.json para consumo do Command Center HUD e MCP.
    """
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT full_name, name, html_url, description, stars, language, topics, squad_id, squad_name, capabilities
            FROM arsenal_tools
            ORDER BY stars DESC
        """)
        rows = cur.fetchall()
        catalog = []
        for row in rows:
            catalog.append({
                "full_name": row[0],
                "name": row[1],
                "html_url": row[2],
                "description": row[3],
                "stars": row[4],
                "language": row[5],
                "topics": json.loads(row[6]) if row[6] else [],
                "squad_id": row[7],
                "squad": row[8],
                "capabilities": json.loads(row[9]) if row[9] else []
            })
        
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        temp = CACHE_FILE.with_suffix(".tmp")
        temp.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(CACHE_FILE)
        print(f"[CATALOG SYNC] Catálogo HUD atualizado ({len(catalog):,} ferramentas indexadas).")
    except Exception as e:
        print(f"[WARN] Erro ao sincronizar cache/starred_catalog.json: {e}")

def run_harvest_for_keyword(keyword: str, min_stars: int, token: str, conn: sqlite3.Connection, already_starred: set):
    headers = get_headers(token)
    print("\n" + "=" * 78)
    print(f" >>> INICIANDO COLHEITA & ESTRELAMENTO PARA: '{keyword}' (Piso: {min_stars} ⭐)")
    print("=" * 78)

    # 1. Obtem teto de estrelas dinamicamente
    top_url = f"https://api.github.com/search/repositories?q={keyword}+stars:>={min_stars}&sort=stars&order=desc&per_page=1"
    req = urllib.request.Request(top_url, headers=headers)
    current_max = 250000
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            total_found = data.get("total_count", 0)
            items = data.get("items", [])
            print(f"[*] Repositórios candidatos com >= {min_stars} estrelas: {total_found:,}")
            if items:
                top_stars = items[0]["stargazers_count"]
                current_max = top_stars + 20
                print(f"[*] Líder da categoria: {items[0]['full_name']} ({top_stars:,} ⭐)")
            if total_found == 0:
                print(f"[INFO] Nenhum repositório com >= {min_stars} estrelas encontrado para '{keyword}'.")
                return
    except Exception as e:
        print(f"[WARN] Erro ao obter teto inicial de estrelas: {e}. Usando teto padrão.")

    kw_newly_starred = 0
    kw_already_had = 0

    while current_max >= min_stars:
        page = 1
        window_has_items = False
        lowest_seen = current_max

        print(f"\n[JANELA] Varrendo faixa: {min_stars}..{current_max} estrelas...")

        while page <= 20:
            url = f"https://api.github.com/search/repositories?q={keyword}+stars:{min_stars}..{current_max}&sort=stars&order=desc&per_page=50&page={page}"
            req = urllib.request.Request(url, headers=headers)

            res_data = None
            for attempt in range(5):
                try:
                    with urllib.request.urlopen(req, timeout=20) as resp:
                        res_data = json.loads(resp.read().decode())
                        break
                except urllib.error.HTTPError as e:
                    if e.code in (403, 429):
                        reset_header = e.headers.get("X-RateLimit-Reset")
                        wait_sec = 60
                        if reset_header:
                            try:
                                wait_sec = max(5, int(reset_header) - int(time.time()) + 2)
                            except Exception:
                                pass
                        print(f"\n[RATE-LIMIT HTTP {e.code}] Aguardando {wait_sec}s para regeneração de tokens...")
                        time.sleep(min(wait_sec, 65))
                    elif e.code == 422:
                        res_data = {"items": []}
                        break
                    else:
                        print(f"\n[HTTP {e.code}] Tentativa {attempt + 1}/5...")
                        time.sleep(3)
                except Exception as e:
                    print(f"\n[CONEXÃO] {e}. Tentativa {attempt + 1}/5...")
                    time.sleep(3)

            if not res_data:
                break

            items = res_data.get("items", [])
            if not items:
                break

            window_has_items = True

            for item in items:
                repo_name = item["full_name"]
                stars = item["stargazers_count"]
                lowest_seen = min(lowest_seen, stars)

                # Grava no banco SQLite independente de já ter dado star ou não
                record_repo_in_arsenal(conn, item, keyword)

                if stars < min_stars:
                    print(f"\n[PISO ALCANÇADO] {repo_name} atingiu {stars} ⭐ (< {min_stars}).")
                    save_progress(already_starred)
                    print(f"[RESUMO '{keyword}'] Novos favoritados: {kw_newly_starred} | Já favoritados: {kw_already_had}")
                    return

                if repo_name in already_starred:
                    kw_already_had += 1
                    continue

                # Envia estrela no GitHub
                star_url = f"https://api.github.com/user/starred/{repo_name}"
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
                    already_starred.add(repo_name)
                    kw_newly_starred += 1
                    squad_id, squad_name, caps = classify_and_tag(item)
                    caps_str = " ".join([f"#{c}" for c in caps[:3]])
                    print(f"[{kw_newly_starred:04d}] ⭐ {repo_name:<38} | {stars:>6,} ⭐ | [{squad_name}] {caps_str}", flush=True)

                    if kw_newly_starred % 15 == 0:
                        save_progress(already_starred)
                        conn.commit()

                # Cadência para 5.000 req/h
                time.sleep(0.35)

            page += 1
            # Pausa para Search API (30 req/min)
            time.sleep(1.2)

        if not window_has_items:
            break

        if lowest_seen <= min_stars:
            print(f"\n[PISO ALCANÇADO] Faixa atingiu {lowest_seen} ⭐!")
            break

        if lowest_seen >= current_max:
            current_max -= 1
        else:
            current_max = lowest_seen

        save_progress(already_starred)
        conn.commit()

    save_progress(already_starred)
    conn.commit()
    print(f"\n[CONCLUÍDO '{keyword}'] Novos favoritados: {kw_newly_starred} | Já cadastrados: {kw_already_had}")

def search_arsenal_cli(query: str):
    """
    Pesquisa instantânea em linguagem natural no Arsenal Soberano via SQLite FTS5.
    Permite que o J.A.R.V.I.S. encontre ferramentas em 2 milissegundos durante missões!
    """
    conn = init_database()
    cur = conn.cursor()

    # Prepara query para FTS5
    clean_query = re.sub(r"[^\w\s-]", "", query).strip()
    if not clean_query:
        print("[ERRO] Consulta vazia.")
        return

    terms = clean_query.split()
    # 1. Tenta AND com prefixo
    fts_and = " AND ".join([f'"{t}"*' for t in terms])
    # 2. Alternativa OR para termos múltiplos
    fts_or = " OR ".join([f'"{t}"*' for t in terms])

    t0 = time.time()
    rows = []
    try:
        cur.execute("""
            SELECT t.full_name, t.stars, t.language, t.squad_name, t.description, t.capabilities, t.html_url
            FROM arsenal_fts f
            JOIN arsenal_tools t ON f.rowid = t.rowid
            WHERE arsenal_fts MATCH ?
            ORDER BY rank, t.stars DESC
            LIMIT 15;
        """, (fts_and,))
        rows = cur.fetchall()

        if len(rows) < 3 and len(terms) > 1:
            cur.execute("""
                SELECT t.full_name, t.stars, t.language, t.squad_name, t.description, t.capabilities, t.html_url
                FROM arsenal_fts f
                JOIN arsenal_tools t ON f.rowid = t.rowid
                WHERE arsenal_fts MATCH ?
                ORDER BY rank, t.stars DESC
                LIMIT 15;
            """, (fts_or,))
            or_rows = cur.fetchall()
            existing_names = {r[0] for r in rows}
            for r in or_rows:
                if r[0] not in existing_names:
                    rows.append(r)
            rows = rows[:15]
    except Exception:
        # Fallback para LIKE se FTS5 falhar na sintaxe
        like_query = f"%{clean_query}%"
        cur.execute("""
            SELECT full_name, stars, language, squad_name, description, capabilities, html_url
            FROM arsenal_tools
            WHERE full_name LIKE ? OR description LIKE ? OR topics LIKE ?
            ORDER BY stars DESC
            LIMIT 15;
        """, (like_query, like_query, like_query))
        rows = cur.fetchall()

    duration = (time.time() - t0) * 1000

    print("=" * 80)
    print(f" 🗡️  J.A.R.V.I.S. ARSENAL // RESULTADOS PARA: '{query}' ({duration:.1f}ms)")
    print("=" * 80)

    if not rows:
        print("Nenhuma ferramenta encontrada no arsenal correspondente a esta missão.")
        return

    for idx, r in enumerate(rows, 1):
        caps = json.loads(r[5]) if r[5] else []
        caps_str = " ".join([f"#{c}" for c in caps])
        print(f"\n{idx:02d}. {r[0]} ({r[1]:,} ⭐) [{r[2]}] - {r[3]}")
        print(f"    Capacidades: {caps_str}")
        print(f"    Descrição  : {r[4][:120]}...")
        print(f"    Repositório: {r[6]}")
    print("\n" + "=" * 80)

def main():
    parser = argparse.ArgumentParser(description="J.A.R.V.I.S. Sovereign Arsenal Harvester & Star Runner")
    parser.add_argument("--words", "-w", type=str, help="Palavras-chave separadas por vírgula (ex: 'Android,Reverse-Engineering,LLM')")
    parser.add_argument("--file", "-f", type=str, help="Arquivo .txt contendo palavras-chave, uma por linha")
    parser.add_argument("--min-stars", "-m", type=int, default=MIN_STARS_DEFAULT, help="Piso mínimo de estrelas (padrão: 999)")
    parser.add_argument("--search", "-s", type=str, help="Busca instantânea de armas/ferramentas no arsenal local via FTS5")
    parser.add_argument("--sync-only", action="store_true", help="Apenas sincroniza SQLite com cache/starred_catalog.json")

    args = parser.parse_args()

    # Modo 1: Busca no Arsenal para Missões
    if args.search:
        search_arsenal_cli(args.search)
        return

    token = resolve_token()
    if not token:
        print("[ERRO CRÍTICO] Token do GitHub não configurado.")
        sys.exit(1)

    conn = init_database()

    # Modo 2: Apenas sincronização de catálogo
    if args.sync_only:
        sync_cache_catalog_from_db(conn)
        return

    # Modo 3: Colheita de Palavras
    keywords_to_process = []

    if args.words:
        keywords_to_process = [w.strip() for w in args.words.split(",") if w.strip()]
    elif args.file:
        p = Path(args.file)
        if p.exists():
            keywords_to_process = [line.strip() for line in p.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]
        else:
            print(f"[ERRO] Arquivo {args.file} não encontrado.")
            return

    if not keywords_to_process:
        # Lista canônica tática de expansão J.A.R.V.I.S.
        print("\nNenhuma palavra-chave informada via --words ou --file.")
        print("Digite a palavra-chave desejada (ou múltiplas separadas por vírgula):")
        try:
            user_input = input("Palavras > ").strip()
            if user_input:
                keywords_to_process = [w.strip() for w in user_input.split(",") if w.strip()]
        except (KeyboardInterrupt, EOFError):
            pass

    if not keywords_to_process:
        print("[INFO] Operação encerrada. Use --help para opções.")
        return

    already_starred = load_progress()
    print("\n" + "=" * 78)
    print(" INICIANDO ROTINA DE COLHEITA DO ARSENAL SOBERANO ")
    print(f" Palavras na fila    : {', '.join(keywords_to_process)}")
    print(f" Piso de corte       : {args.min_stars} estrelas")
    print(f" Banco SQLite        : {DB_FILE}")
    print(f" Repositórios no set : {len(already_starred):,}")
    print("=" * 78)

    for kw in keywords_to_process:
        run_harvest_for_keyword(kw, args.min_stars, token, conn, already_starred)

    # Sincroniza cache consolidado ao final
    sync_cache_catalog_from_db(conn)

    print("\n" + "=" * 78)
    print(" TODAS AS PALAVRAS DA FILA FORAM PROCESSADAS COM SUCESSO! ")
    print(f" Total no banco de progresso: {len(already_starred):,} repositórios")
    print("=" * 78)

if __name__ == "__main__":
    main()
