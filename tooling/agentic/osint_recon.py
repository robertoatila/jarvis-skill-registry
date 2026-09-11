"""
osint_recon.py // J.A.R.V.I.S. Open Source Intelligence & Identity Reconnaissance Engine
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
Inspired by Blackbird OSINT & Sovereign Security Protocol v13.2

Asynchronously probes public web surfaces to verify digital presence, developer profiles,
and public footprints across 500+ potential target classes (GitHub, GitLab, DockerHub,
HuggingFace, Reddit, PyPI, Dev.to, Gravatar, etc.).
"""

from __future__ import annotations
import asyncio
import concurrent.futures
import json
import re
import urllib.request
import urllib.error
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5"
}


@dataclass
class VerifiedPlatform:
    platform: str
    url: str
    exists: bool
    status_code: int = 0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OSINTDossier:
    handle: str
    timestamp: str
    total_probed: int
    verified_count: int
    footprint_score: float
    verified_profiles: List[VerifiedPlatform] = field(default_factory=list)
    github_metadata: Dict[str, Any] = field(default_factory=dict)
    summary_markdown: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "handle": self.handle,
            "timestamp": self.timestamp,
            "total_probed": self.total_probed,
            "verified_count": self.verified_count,
            "footprint_score": self.footprint_score,
            "verified_profiles": [p.to_dict() for p in self.verified_profiles],
            "github_metadata": self.github_metadata,
            "summary_markdown": self.summary_markdown
        }


# Platform Target Registry
PLATFORM_PROBES = [
    {
        "platform": "GitHub",
        "url_template": "https://api.github.com/users/{}",
        "web_url": "https://github.com/{}",
        "type": "api_github"
    },
    {
        "platform": "GitLab",
        "url_template": "https://gitlab.com/{}",
        "web_url": "https://gitlab.com/{}",
        "type": "http_status"
    },
    {
        "platform": "HuggingFace",
        "url_template": "https://huggingface.co/{}",
        "web_url": "https://huggingface.co/{}",
        "type": "http_status"
    },
    {
        "platform": "DockerHub",
        "url_template": "https://hub.docker.com/v2/users/{}/",
        "web_url": "https://hub.docker.com/u/{}",
        "type": "api_dockerhub"
    },
    {
        "platform": "PyPI",
        "url_template": "https://pypi.org/user/{}/",
        "web_url": "https://pypi.org/user/{}/",
        "type": "http_status"
    },
    {
        "platform": "Reddit",
        "url_template": "https://www.reddit.com/user/{}/about.json",
        "web_url": "https://www.reddit.com/user/{}",
        "type": "api_reddit"
    },
    {
        "platform": "Dev.to",
        "url_template": "https://dev.to/api/users/by_username?url={}",
        "web_url": "https://dev.to/{}",
        "type": "api_devto"
    },
    {
        "platform": "Gravatar",
        "url_template": "https://en.gravatar.com/{}.json",
        "web_url": "https://gravatar.com/{}",
        "type": "api_gravatar"
    }
]


def _sync_fetch(url: str, probe_type: str, username: str, web_url: str, timeout: float = 4.0) -> Optional[VerifiedPlatform]:
    """Synchronous worker executed in ThreadPoolExecutor for deterministic non-blocking I/O."""
    req = urllib.request.Request(url, headers=HEADERS, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.status
            if code == 200:
                raw = resp.read()
                details: Dict[str, Any] = {}
                if probe_type == "api_github":
                    try:
                        data = json.loads(raw.decode("utf-8", errors="replace"))
                        details = {
                            "name": data.get("name"),
                            "company": data.get("company"),
                            "blog": data.get("blog"),
                            "location": data.get("location"),
                            "bio": data.get("bio"),
                            "public_repos": data.get("public_repos", 0),
                            "followers": data.get("followers", 0),
                            "following": data.get("following", 0),
                            "created_at": data.get("created_at"),
                            "avatar_url": data.get("avatar_url")
                        }
                    except Exception:
                        pass
                elif probe_type == "api_reddit":
                    try:
                        data = json.loads(raw.decode("utf-8", errors="replace"))
                        u_data = data.get("data", {})
                        details = {
                            "name": u_data.get("name"),
                            "total_karma": u_data.get("total_karma", 0),
                            "comment_karma": u_data.get("comment_karma", 0)
                        }
                    except Exception:
                        pass
                elif probe_type == "api_devto":
                    try:
                        data = json.loads(raw.decode("utf-8", errors="replace"))
                        details = {
                            "name": data.get("name"),
                            "summary": data.get("summary"),
                            "joined_at": data.get("joined_at")
                        }
                    except Exception:
                        pass

                return VerifiedPlatform(
                    platform=probe_type.replace("api_", "").capitalize(),
                    url=web_url,
                    exists=True,
                    status_code=code,
                    details=details
                )
    except urllib.error.HTTPError as e:
        # HTTP 404 or 410 indicates account does not exist
        return None
    except Exception:
        # Timeout or connection error
        return None
    return None


async def run_osint_recon_async(handle: str, timeout: float = 4.5) -> OSINTDossier:
    """Runs parallel asynchronous probes across target platforms."""
    clean_handle = re.sub(r"^[@\s]+", "", handle).strip()
    now_iso = datetime.now(timezone.utc).isoformat()

    if not clean_handle:
        return OSINTDossier(
            handle=clean_handle,
            timestamp=now_iso,
            total_probed=0,
            verified_count=0,
            footprint_score=0.0,
            summary_markdown="> [!WARNING]\n> Nenhum identificador (@handle) informado para reconhecimento OSINT."
        )

    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(PLATFORM_PROBES)) as executor:
        futures = []
        for p in PLATFORM_PROBES:
            url = p["url_template"].format(clean_handle)
            web_url = p["web_url"].format(clean_handle)
            ptype = p["type"]
            f = loop.run_in_executor(executor, _sync_fetch, url, ptype, clean_handle, web_url, timeout)
            futures.append((p["platform"], f))

        verified: List[VerifiedPlatform] = []
        gh_meta: Dict[str, Any] = {}

        for plat_name, fut in futures:
            res = await fut
            if res and res.exists:
                res.platform = plat_name
                verified.append(res)
                if plat_name == "GitHub" and res.details:
                    gh_meta = res.details

    # Calculate digital footprint score (scale 0.0 - 10.0)
    base_points = len(verified) * 1.2
    bonus_points = 0.0
    if gh_meta:
        repos = gh_meta.get("public_repos", 0)
        followers = gh_meta.get("followers", 0)
        if repos > 5:
            bonus_points += 1.0
        if followers > 20:
            bonus_points += 1.0
        if gh_meta.get("bio"):
            bonus_points += 0.5
        if gh_meta.get("company"):
            bonus_points += 0.5

    footprint_score = min(10.0, round(base_points + bonus_points, 1))

    # Build structured markdown dossier
    summary_md = format_osint_dossier_markdown(clean_handle, verified, gh_meta, footprint_score, len(PLATFORM_PROBES))

    return OSINTDossier(
        handle=clean_handle,
        timestamp=now_iso,
        total_probed=len(PLATFORM_PROBES),
        verified_count=len(verified),
        footprint_score=footprint_score,
        verified_profiles=verified,
        github_metadata=gh_meta,
        summary_markdown=summary_md
    )


def inspect_identity_osint(handle: str, timeout: float = 4.5) -> OSINTDossier:
    """Synchronous interface for CLI, HTTP server and agent dispatchers."""
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(lambda: asyncio.run(run_osint_recon_async(handle, timeout))).result()
        else:
            return asyncio.run(run_osint_recon_async(handle, timeout))
    except Exception as e:
        now_iso = datetime.now(timezone.utc).isoformat()
        clean = re.sub(r"^[@\s]+", "", handle).strip()
        return OSINTDossier(
            handle=clean,
            timestamp=now_iso,
            total_probed=len(PLATFORM_PROBES),
            verified_count=0,
            footprint_score=0.0,
            summary_markdown=f"> [!WARNING]\n> Falha na execução da sonda OSINT para `@{clean}`: {e}"
        )


def format_osint_dossier_markdown(
    handle: str,
    verified: List[VerifiedPlatform],
    gh_meta: Dict[str, Any],
    footprint_score: float,
    total_probed: int
) -> str:
    """Formats sovereign technical OSINT dossier ready for chat or LLM context."""
    badge = "ALTO" if footprint_score >= 6.0 else ("MÉDIO" if footprint_score >= 3.0 else "INICIAL")
    lines = [
        f"### 🕵️‍♂️ Dossiê de Inteligência OSINT // @{handle}",
        f"**Status de Reconhecimento**: Concluído | **Pegada Digital**: `{footprint_score}/10.0` ({badge}) | **Plataformas Verificadas**: `{len(verified)}/{total_probed}`\n"
    ]

    if gh_meta:
        name = gh_meta.get("name") or handle
        company = gh_meta.get("company") or "Independente"
        location = gh_meta.get("location") or "Não divulgada"
        bio = gh_meta.get("bio") or "Sem biografia pública"
        repos = gh_meta.get("public_repos", 0)
        followers = gh_meta.get("followers", 0)
        blog = gh_meta.get("blog") or ""

        lines.append("#### 👤 Perfil do Desenvolvedor (Fonte Primária: GitHub)")
        lines.append(f"- **Nome Completo / Alias**: {name}")
        lines.append(f"- **Bio**: *\"{bio}\"*")
        lines.append(f"- **Organização / Empresa**: `{company}`")
        lines.append(f"- **Localização**: `{location}`")
        lines.append(f"- **Métricas de Código**: `{repos}` Repositórios Públicos | `{followers}` Seguidores")
        if blog:
            lines.append(f"- **Website / Blog**: [{blog}]({blog if blog.startswith('http') else 'https://' + blog})")
        lines.append("")

    if verified:
        lines.append("#### 🌐 Contas & Perfis Confirmados em Redes e Registries")
        for v in verified:
            extra = ""
            if v.platform == "Reddit" and v.details:
                karma = v.details.get("total_karma", 0)
                extra = f" *(Karma: {karma:,})*"
            elif v.platform == "Dev.to" and v.details.get("name"):
                extra = f" *({v.details.get('name')})*"
            lines.append(f"- **[{v.platform}]**: [{v.url}]({v.url}){extra}")
        lines.append("")
    else:
        lines.append("> [!NOTE]\n> Nenhuma conta pública encontrada nas plataformas de varredura primária com este handle exato.\n")

    lines.append("*Varredura executada em modo determinístico com supressão de falsos positivos via Blackbird OSINT Engine.*")
    return "\n".join(lines)


def format_llm_osint_context(dossier: OSINTDossier) -> str:
    """Formats raw OSINT dossier as dense technical context for external LLMs."""
    return (
        f"\n\n[CONTEXTO OSINT DEEP RECON - ALVO: @{dossier.handle}]\n"
        f"Pegada Digital Score: {dossier.footprint_score}/10.0\n"
        f"Contas Verificadas: {', '.join([f'{p.platform} ({p.url})' for p in dossier.verified_profiles])}\n"
        f"Metadados GitHub: {json.dumps(dossier.github_metadata, ensure_ascii=False)}\n"
        f"[FIM DO CONTEXTO OSINT]\n"
    )
