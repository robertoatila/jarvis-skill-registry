import os
import sys
import time
import json
import urllib.request
import urllib.error
from pathlib import Path

# Força UTF-8 no Windows Console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

REGISTRY_ROOT = Path(r"E:\.skill-registry")
PROGRESS_FILE = REGISTRY_ROOT / ".star_progress.json"
MCP_CONFIG = Path.home() / ".gemini" / "config" / "mcp_config.json"

QUERY = "Android"
MIN_STARS = 999
DEFAULT_START_MAX = 300000

def resolve_token() -> str:
    # 1. Environment variable
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN") or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token and token.strip():
        return token.strip()
    
    # 2. mcp_config.json
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

def load_progress() -> set:
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data)
        except Exception as e:
            print(f"[WARN] Falha ao carregar progresso: {e}")
    return set()

def save_progress(data: set):
    try:
        temp_file = PROGRESS_FILE.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(sorted(list(data)), f, indent=2)
        temp_file.replace(PROGRESS_FILE)
    except Exception as e:
        print(f"[WARN] Falha ao salvar progresso: {e}")

def get_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "JARVIS-Android-Star-Runner/1.0 (robertoatila)",
        "X-GitHub-Api-Version": "2022-11-28"
    }

def fetch_top_stars(token: str) -> int:
    headers = get_headers(token)
    url = f"https://api.github.com/search/repositories?q={QUERY}+stars:>={MIN_STARS}&sort=stars&order=desc&per_page=1"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            items = data.get("items", [])
            total_count = data.get("total_count", 0)
            print(f"[INFO] Total de repositórios encontrados para '{QUERY}' com >= {MIN_STARS} estrelas: {total_count:,}")
            if items:
                top_stars = items[0]["stargazers_count"]
                print(f"[INFO] Top repositório inicial: {items[0]['full_name']} ({top_stars:,} estrelas)")
                return top_stars + 50
    except Exception as e:
        print(f"[WARN] Não foi possível obter o teto dinâmico de estrelas: {e}")
    return DEFAULT_START_MAX

def run():
    token = resolve_token()
    if not token:
        print("[ERRO] Nenhum token GitHub válido encontrado.")
        sys.exit(1)

    headers = get_headers(token)
    already_starred = load_progress()

    print("=" * 75)
    print(" corrida soberana de favoritar github // j.a.r.v.i.s. ")
    print(f" Palavra-chave alvo : '{QUERY}'")
    print(f" Limite inferior    : {MIN_STARS} estrelas")
    print(f" Histórico atual    : {len(already_starred):,} repositórios registrados")
    print("=" * 75)

    current_max = fetch_top_stars(token)
    total_newly_starred = 0
    total_already_had = 0

    while current_max >= MIN_STARS:
        page = 1
        window_has_items = False
        lowest_seen_in_window = current_max

        print(f"\n>>> [JANELA] Buscando repositórios na faixa: {MIN_STARS}..{current_max} estrelas...")

        while page <= 20:  # Limite de 1.000 itens por busca do GitHub (20 * 50)
            url = f"https://api.github.com/search/repositories?q={QUERY}+stars:{MIN_STARS}..{current_max}&sort=stars&order=desc&per_page=50&page={page}"
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
                        wait_seconds = 60
                        if reset_header:
                            try:
                                wait_seconds = max(5, int(reset_header) - int(time.time()) + 2)
                            except Exception:
                                pass
                        print(f"\n[RATE-LIMIT HTTP {e.code}] Pausando {wait_seconds}s para regeneração de cota...")
                        time.sleep(min(wait_seconds, 65))
                    elif e.code == 422:
                        # Página além do índice máximo permitido
                        res_data = {"items": []}
                        break
                    else:
                        print(f"\n[HTTP ERROR {e.code}] {e.reason}. Tentativa {attempt + 1}/5...")
                        time.sleep(3)
                except Exception as e:
                    print(f"\n[CONN ERROR] {e}. Tentativa {attempt + 1}/5...")
                    time.sleep(3)

            if not res_data:
                print(f"[WARN] Falha repetida na requisição da página {page}. Avançando janela.")
                break

            items = res_data.get("items", [])
            if not items:
                break

            window_has_items = True

            for item in items:
                repo_name = item["full_name"]
                stars = item["stargazers_count"]
                lowest_seen_in_window = min(lowest_seen_in_window, stars)

                if stars < MIN_STARS:
                    print(f"\n[META ATINGIDA] Repositório {repo_name} atingiu {stars} estrelas (< {MIN_STARS}).")
                    save_progress(already_starred)
                    print(f"\nCorrida finalizada com sucesso! Novos favoritados: {total_newly_starred}")
                    return

                if repo_name in already_starred:
                    total_already_had += 1
                    continue

                # Efetua o estrelamento no GitHub via PUT
                star_url = f"https://api.github.com/user/starred/{repo_name}"
                star_req = urllib.request.Request(star_url, data=b"", method="PUT", headers=headers)

                starred_ok = False
                for star_attempt in range(3):
                    try:
                        with urllib.request.urlopen(star_req, timeout=15) as star_resp:
                            if star_resp.status in (204, 304):
                                starred_ok = True
                                break
                    except urllib.error.HTTPError as star_err:
                        if star_err.code in (403, 429):
                            print(f"\n[STAR RATE LIMIT] Pausando 30s...")
                            time.sleep(30)
                        elif star_err.code == 404:
                            # Repo deletado ou privado
                            break
                        else:
                            time.sleep(1)
                    except Exception:
                        time.sleep(1)

                if starred_ok:
                    already_starred.add(repo_name)
                    total_newly_starred += 1
                    print(f"[{total_newly_starred:04d}] ⭐ Favoritado: {repo_name:<42} | {stars:>7,} estrelas", flush=True)

                    if total_newly_starred % 15 == 0:
                        save_progress(already_starred)

                # Cadência para respeitar limites do Core API (5000 req/h = ~1.4 req/s)
                time.sleep(0.35)

            page += 1
            # Pausa suave entre páginas de busca (Search API: 30 req/min)
            time.sleep(1.2)

        if not window_has_items:
            print("\nNenhum outro repositório encontrado na janela atual.")
            break

        # Atualiza o teto da próxima janela usando o menor valor de estrelas visto
        if lowest_seen_in_window <= MIN_STARS:
            print(f"\n[META ALCANÇADA] Menor contagem de estrelas observada ({lowest_seen_in_window}) atingiu o piso de {MIN_STARS}!")
            break

        if lowest_seen_in_window >= current_max:
            current_max -= 1
        else:
            current_max = lowest_seen_in_window

        save_progress(already_starred)
        print(f"[STATUS] Progresso salvo. Próximo teto: {current_max} estrelas. Novos favoritados até agora: {total_newly_starred}")

    save_progress(already_starred)
    print("\n" + "=" * 75)
    print(f" CORRIDA CONCLUÍDA: {QUERY} ATE {MIN_STARS} ESTRELAS ")
    print(f" Novos repositórios favoritados : {total_newly_starred}")
    print(f" Repositórios já favoritados    : {total_already_had}")
    print(f" Total no banco de progresso    : {len(already_starred):,}")
    print("=" * 75)

if __name__ == "__main__":
    run()
