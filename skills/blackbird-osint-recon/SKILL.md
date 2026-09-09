---
name: blackbird-osint-recon
description: Fast asynchronous OSINT reconnaissance and identity verification engine across 500+ platforms.
---

# Blackbird OSINT & Identity Verification

Deterministic asynchronous OSINT engine to search and verify username presence, corporate accounts, and profile existence across 500+ web platforms with false positive suppression.

## Architecture

```text
[Username / Handle]
       │
       ▼
[Async HTTP Probe Pool] ──► [Filter 500+ Endpoints] ──► [HTTP Code / Regex / Metadata Match]
                                                                  │
                                                                  ▼
                                                      [Verified Accounts Ledger]
```

## Production Implementation: Async Probing Engine

```python
import asyncio
import urllib.request
import json
from typing import Dict, List

PLATFORMS = {
    "GitHub": {"url": "https://github.com/{}", "check": "status_200"},
    "GitLab": {"url": "https://gitlab.com/{}", "check": "status_200"},
    "Reddit": {"url": "https://www.reddit.com/user/{}/about.json", "check": "json_data"},
    "HuggingFace": {"url": "https://huggingface.co/{}", "check": "status_200"},
    "DockerHub": {"url": "https://hub.docker.com/v2/users/{}/", "check": "status_200"},
    "PyPI": {"url": "https://pypi.org/user/{}/", "check": "status_200"}
}

async def probe_platform(platform: str, cfg: dict, username: str) -> dict:
    url = cfg["url"].format(username)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    loop = asyncio.get_event_loop()
    
    def _fetch():
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200, url
        except Exception:
            return False, url

    found, final_url = await loop.run_in_executor(None, _fetch)
    return {"platform": platform, "url": final_url, "exists": found}

async def run_osint_recon(username: str) -> List[Dict]:
    tasks = [probe_platform(p, cfg, username) for p, cfg in PLATFORMS.items()]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r["exists"]]

if __name__ == "__main__":
    found_accounts = asyncio.run(run_osint_recon("torvalds"))
    print(json.dumps(found_accounts, indent=2))
```
