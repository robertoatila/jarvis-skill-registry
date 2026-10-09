import os
import sys
import time
import json
import urllib.request
import urllib.error

# Força UTF-8 no Windows Console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def resolve_token():
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN") or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token and token.strip():
        return token.strip()
    mcp_config = os.path.expanduser(r"~/.gemini/config/mcp_config.json")
    if os.path.exists(mcp_config):
        try:
            with open(mcp_config, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                token = cfg.get("mcpServers", {}).get("github-mcp-server", {}).get("env", {}).get("GITHUB_PERSONAL_ACCESS_TOKEN")
                if token and token.strip():
                    return token.strip()
        except Exception:
            pass
    return ""

TOKEN = resolve_token()
QUERY = "hacktoberfest"
MIN_STARS = 999
START_MAX_STARS = 3836

# Todo o log e rastreamento fica estritamente no drive E:\ (zero arquivos no C:\ ou Desktop)
PROGRESS_FILE = r"E:\.skill-registry\.star_progress.json"

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()

def save_progress(data):
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(data), f)
    except Exception:
        pass

def run():
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Mozilla/5.0",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    already_starred = load_progress()
    print("=" * 70)
    print("CONTINUAÇÃO: FAVORITAMENTO HACKTOBERFEST (J.A.R.V.I.S.)")
    print("=" * 70)
    print(f"Buscando de {START_MAX_STARS} estrelas até {MIN_STARS} estrelas...")
    print(f"Repositórios já registrados no histórico: {len(already_starred)}")
    print("-" * 70)

    current_max = START_MAX_STARS
    total_starred = 0
    last_seen_repo = None

    while current_max >= MIN_STARS:
        page = 1
        window_has_items = False

        while page <= 20: # Limite de 1000 itens por janela do GitHub
            url = f"https://api.github.com/search/repositories?q={QUERY}+stars:{MIN_STARS}..{current_max}&sort=stars&order=desc&per_page=50&page={page}"
            req = urllib.request.Request(url, headers=headers)

            try:
                with urllib.request.urlopen(req) as resp:
                    res_data = json.loads(resp.read().decode())
            except urllib.error.HTTPError as e:
                if e.code == 403:
                    print("\n[Rate Limit] Aguardando 60 segundos...")
                    time.sleep(60)
                    continue
                elif e.code == 422:
                    break
                else:
                    print(f"\n[Erro API {e.code}]: {e.reason}")
                    break

            items = res_data.get("items", [])
            if not items:
                break

            window_has_items = True

            for item in items:
                repo_name = item["full_name"]
                stars = item["stargazers_count"]
                last_seen_repo = (repo_name, stars)

                if stars < MIN_STARS:
                    print(f"\n[FIM] Repositório {repo_name} atingiu {stars} estrelas (< {MIN_STARS}). Finalizado com sucesso!")
                    save_progress(already_starred)
                    return

                if repo_name in already_starred:
                    continue

                star_url = f"https://api.github.com/user/starred/{repo_name}"
                star_req = urllib.request.Request(star_url, data=b"", method="PUT", headers=headers)

                try:
                    with urllib.request.urlopen(star_req) as star_resp:
                        if star_resp.status in (204, 304):
                            already_starred.add(repo_name)
                            total_starred += 1
                            print(f"[{total_starred:04d}] ⭐ Favoritado: {repo_name} ({stars:,} estrelas)", flush=True)
                            if total_starred % 25 == 0:
                                save_progress(already_starred)
                except urllib.error.HTTPError as err:
                    pass

                time.sleep(0.25)

            page += 1

        if not window_has_items or not last_seen_repo:
            print("\nTodos os repositórios da faixa foram concluídos!")
            break

        # Próxima janela de busca usando o piso de estrelas do último repositório visto
        last_name, last_stars = last_seen_repo
        if last_stars <= MIN_STARS or last_stars >= current_max:
            current_max -= 1
        else:
            current_max = last_stars

        save_progress(already_starred)

    print(f"\nProcesso concluído com êxito! Total de novos repositórios favoritados: {total_starred}")

if __name__ == "__main__":
    run()
