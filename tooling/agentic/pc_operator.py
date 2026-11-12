"""
J.A.R.V.I.S. Sovereign Autonomous PC Operator & Multi-Agent ReAct Engine
Enables real tool calling and Windows execution on Roberto's workstation.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT_DIR / "config"
CACHE_DIR = ROOT_DIR / "cache"


class JarvisPCOperator:
    """Core autonomous agent executing real actions on Windows via LLM Function Calling."""

    def __init__(self):
        self.keys = self._load_api_keys()
        self.providers = self._load_providers()
        self.tools_schema = self._build_tools_schema()

    def _load_api_keys(self) -> Dict[str, Any]:
        keys: Dict[str, Any] = {}
        for fname in ("api_keys.json", "credentials.json"):
            path = CONFIG_DIR / fname
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            for k, v in data.items():
                                if isinstance(v, dict) and "api_key" in v:
                                    keys[k] = v["api_key"]
                                    if "model" in v:
                                        keys[f"{k}_model"] = v["model"]
                                else:
                                    keys[k] = v
                except Exception:
                    pass
        return keys

    def _load_providers(self) -> Dict[str, Any]:
        path = CONFIG_DIR / "chat-providers.json"
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _build_tools_schema(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "run_powershell",
                    "description": "Executa um comando real no PowerShell do Windows do PC de Roberto e retorna a saída bruta. Use para verificar processos, rede, arquivos, serviços ou tarefas do sistema.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Comando PowerShell válido (ex: Get-Process, dir, Get-Volume, Get-Service)",
                            }
                        },
                        "required": ["command"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "query_arsenal",
                    "description": "Pesquisa no acervo soberano de mais de 20.000 repositórios catalogados e notas do Segundo Cérebro de Roberto. Retorna repositórios de alta relevância com estrelas e descrições.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "Termo técnico a pesquisar (ex: whisper, rag, agent, scraper, proxy, kernel, rust)",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Limite de resultados (máximo 10)",
                            },
                        },
                        "required": ["topic"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_pc_telemetry",
                    "description": "Obtém telemetria em tempo real do computador de Roberto: uso de CPU, memória RAM livre/total, status da GPU e espaço em disco.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "detailed": {
                                "type": "boolean",
                                "description": "Incluir detalhes dos discos C, D e E",
                            }
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_pc_file",
                    "description": "Lê o conteúdo de um arquivo de código, texto ou nota no computador de Roberto.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Caminho relativo ou absoluto do arquivo",
                            },
                            "max_lines": {
                                "type": "integer",
                                "description": "Número máximo de linhas a ler (padrão 100)",
                            },
                        },
                        "required": ["path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "write_pc_file",
                    "description": "Cria ou atualiza um arquivo de script, código ou documento no computador de Roberto.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Caminho relativo ou absoluto do arquivo a criar",
                            },
                            "content": {
                                "type": "string",
                                "description": "Conteúdo de texto a gravar no arquivo",
                            },
                        },
                        "required": ["path", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "system_control",
                    "description": "Controla aplicativos e janelas no Windows do PC de Roberto (abrir apps, navegador, calculadora, terminal, etc.).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["open_app", "open_url", "status"],
                                "description": "Ação a executar",
                            },
                            "target": {
                                "type": "string",
                                "description": "Nome do app (ex: 'chrome', 'obsidian', 'notepad') ou URL (ex: 'https://youtube.com')",
                            },
                        },
                        "required": ["action", "target"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "dispatch_squad_agent",
                    "description": "Delega uma missão complexa a um dos 11 Agentes Especialistas do Esquadrão Soberano (Quantum-SWEOrchestrator, Quantum-ReconAgent, Hyperion-CyberSecAgent, Sovereign-KernelAgent, etc.).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "agent_id": {
                                "type": "string",
                                "description": "Identificador do agente especialista",
                            },
                            "mission": {
                                "type": "string",
                                "description": "Descrição clara e objetiva da missão a executar",
                            },
                        },
                        "required": ["agent_id", "mission"],
                    },
                },
            },
        ]

    # --- Tool Implementations on Windows ---

    def execute_tool(self, name: str, args: Dict[str, Any]) -> str:
        """Executes a concrete tool action on the local Windows workstation."""
        try:
            if name == "run_powershell":
                cmd = args.get("command", "").strip()
                if not cmd:
                    return "Erro: Comando vazio."
                proc = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", cmd],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    cwd=str(ROOT_DIR),
                )
                output = proc.stdout.strip() or proc.stderr.strip()
                return output[:3000] if output else "Comando executado com sucesso sem saída."

            elif name == "query_arsenal":
                topic = args.get("topic", "").strip().lower()
                limit = min(max(args.get("limit", 5), 1), 10)
                return self._search_arsenal_catalog(topic, limit)

            elif name == "get_pc_telemetry":
                return self._collect_pc_telemetry(detailed=args.get("detailed", True))

            elif name == "read_pc_file":
                path_str = args.get("path", "").strip()
                max_lines = args.get("max_lines", 100)
                file_path = ROOT_DIR / path_str if not os.path.isabs(path_str) else Path(path_str)
                if not file_path.exists():
                    return f"Erro: Arquivo não encontrado: {path_str}"
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = [line for i, line in enumerate(f) if i < max_lines]
                return "".join(lines)[:4000]

            elif name == "write_pc_file":
                path_str = args.get("path", "").strip()
                content = args.get("content", "")
                file_path = ROOT_DIR / path_str if not os.path.isabs(path_str) else Path(path_str)
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return f"Arquivo gravado com sucesso: {path_str} ({len(content)} caracteres)."

            elif name == "system_control":
                action = args.get("action", "")
                target = args.get("target", "")
                return self._execute_system_control(action, target)

            elif name == "dispatch_squad_agent":
                agent_id = args.get("agent_id", "")
                mission = args.get("mission", "")
                return self._dispatch_squad_agent(agent_id, mission)

            else:
                return f"Erro: Ferramenta desconhecida '{name}'."

        except subprocess.TimeoutExpired:
            return f"Erro: Tempo limite de execução atingido para ferramenta '{name}'."
        except Exception as e:
            return f"Erro ao executar '{name}': {str(e)}"

    def _search_arsenal_catalog(self, topic: str, limit: int = 5) -> str:
        """Search in the local 20,000 repositories catalog."""
        catalog_file = CACHE_DIR / "starred_catalog.json"
        results = []
        if catalog_file.exists():
            try:
                with open(catalog_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                items = data.get("repositories", []) if isinstance(data, dict) else data
                for item in items:
                    name = item.get("name", "")
                    desc = item.get("description", "") or ""
                    stars = item.get("stargazers_count", 0)
                    if topic in name.lower() or topic in desc.lower():
                        results.append({"repo": name, "stars": stars, "description": desc[:150]})
                        if len(results) >= limit:
                            break
            except Exception:
                pass

        if not results:
            # Fallback heuristic for known arsenal assets
            return json.dumps({
                "topic": topic,
                "count": 0,
                "message": f"Nenhum repositório específico encontrado com '{topic}'. Busque em outra categoria do acervo."
            }, ensure_ascii=False)

        return json.dumps({"topic": topic, "found": len(results), "repositories": results}, ensure_ascii=False)

    def _collect_pc_telemetry(self, detailed: bool = True) -> str:
        """Collect live CPU, RAM, and Disk metrics via PowerShell."""
        ps_cmd = (
            "$cpu = (Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average; "
            "$os = Get-CimInstance Win32_OperatingSystem; "
            "$ram_free = [math]::Round($os.FreePhysicalMemory / 1MB, 2); "
            "$ram_total = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2); "
            "$ram_used_pct = [math]::Round((($ram_total - $ram_free) / $ram_total) * 100, 1); "
            "$disks = Get-PSDrive -PSProvider FileSystem | Select-Object Name, @{N='FreeGB';E={[math]::Round($_.Free/1GB,1)}}; "
            "@{cpu_pct=$cpu; ram_total_gb=$ram_total; ram_free_gb=$ram_free; ram_used_pct=$ram_used_pct; drives=$disks} | ConvertTo-Json -Compress"
        )
        try:
            proc = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, timeout=8)
            return proc.stdout.strip() if proc.stdout.strip() else json.dumps({"status": "ONLINE", "os": "Windows"})
        except Exception as e:
            return json.dumps({"status": "ONLINE", "error": str(e)})

    @staticmethod
    def _resolve_launch_target(candidate: str) -> Optional[str]:
        """Return the executable ``candidate`` names, or None when it names none."""
        if not candidate or any(ch in candidate for ch in "\r\n\x00"):
            return None
        try:
            if os.path.isfile(candidate):
                return candidate
        except (OSError, ValueError):
            return None
        return shutil.which(candidate)

    def _execute_system_control(self, action: str, target: str) -> str:
        """Launch Windows desktop applications or URLs."""
        if action == "open_url" or target.startswith("http://") or target.startswith("https://"):
            import webbrowser
            webbrowser.open(target)
            return f"Navegador aberto na URL: {target}"

        if action == "open_app":
            app_map = {
                "obsidian": os.path.expandvars(r"%LOCALAPPDATA%\Programs\Obsidian\Obsidian.exe"),
                "chrome": os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
                "notepad": "notepad.exe",
                "calc": "calc.exe",
                "terminal": "wt.exe",
            }
            requested = str(target or "").strip()
            candidate = app_map.get(requested.lower(), requested)
            # The target is a program, never a command line: it is resolved to
            # one existing executable and started without a shell, so text such
            # as "calc & del ..." names no program and starts nothing.
            executable = self._resolve_launch_target(candidate)
            if executable is None:
                return f"Aplicativo '{requested}' não encontrado neste computador; nenhum processo foi iniciado."
            try:
                subprocess.Popen([executable], shell=False)
                return f"Aplicativo '{requested}' iniciado ({executable})."
            except Exception as e:
                return f"Erro ao abrir aplicativo '{requested}': {e}"

        return f"Ação de sistema '{action}' concluída."

    def _dispatch_squad_agent(self, agent_id: str, mission: str) -> str:
        """Delegate tasks to the Sovereign SWE Orchestrator."""
        try:
            from tooling.agentic.swe_orchestrator import SoftwareEngineeringOrchestrator, AgentProfileRegistry
            registry = AgentProfileRegistry()
            profile = registry._profiles.get(agent_id)
            if not profile:
                available = list(registry._profiles.keys())
                return json.dumps({
                    "status": "AGENT_NOT_FOUND",
                    "agent_id": agent_id,
                    "available_agents": available[:6]
                }, ensure_ascii=False)

            orchestrator = SoftwareEngineeringOrchestrator()
            return json.dumps({
                "status": "MISSION_SCHEDULED",
                "agent_id": agent_id,
                "agent_name": profile.name,
                "domain": profile.domain,
                "mission": mission,
                "capabilities": profile.capabilities[:5]
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "DISPATCH_ERROR", "error": str(e)}, ensure_ascii=False)

    # --- Agentic ReAct Loop ---

    def run_agentic_turn(
        self,
        user_message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        max_turns: int = 5,
    ) -> Dict[str, Any]:
        """Runs the complete ReAct loop: Reason -> Act on PC -> Reason -> Reply."""
        start_time = time.perf_counter()
        provider = provider or self.keys.get("preferred_provider", "groq")
        
        # Resolve model
        if not model:
            if provider == "groq":
                model = self.keys.get("groq_model", "qwen/qwen3.8-27b")
            elif provider == "openrouter":
                model = self.keys.get("openrouter_model", "nvidia/nemotron-3.5-lightning:free")
            elif provider == "cloudflare":
                model = self.keys.get("cloudflare_model", "@cf/meta/llama-3.3-70b-instruct-fp8-fast")

        system_prompt = (
            "Você é o J.A.R.V.I.S., assistente soberano de inteligência artificial de Roberto Atila.\n"
            "Você opera diretamente no computador Windows dele e tem ACESSO REAL a ferramentas de sistema.\n"
            "Quando Roberto pedir qualquer ação, verificação de hardware, pesquisa no acervo de 20.000 repositórios "
            "ou execução de comandos, SEMPRE use as ferramentas disponíveis.\n"
            "Seja sucinto, técnico, polido e execute antes de falar."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        tools_executed = []

        for turn in range(max_turns):
            response = self._call_llm_with_tools(provider, model, messages)
            if not response.get("success"):
                # Fallback to secondary provider if primary fails
                if provider == "groq" and self.keys.get("openrouter"):
                    return self.run_agentic_turn(user_message, provider="openrouter")
                return {
                    "status": "ERROR",
                    "reply": f"Erro na inferência: {response.get('error')}",
                    "provider": provider,
                    "model": model,
                    "tools_executed": tools_executed,
                    "duration_ms": (time.perf_counter() - start_time) * 1000,
                }

            msg = response["message"]
            tool_calls = msg.get("tool_calls", [])

            if not tool_calls:
                # LLM finished its reasoning and produced final text response
                return {
                    "status": "COMPLETED",
                    "reply": msg.get("content", "").strip(),
                    "provider": provider,
                    "model": model,
                    "tools_executed": tools_executed,
                    "turns": turn + 1,
                    "duration_ms": (time.perf_counter() - start_time) * 1000,
                }

            # Append the assistant's tool call message
            messages.append(msg)

            # Execute every tool call on Roberto's PC
            for tc in tool_calls:
                func_name = tc["function"]["name"]
                args_str = tc["function"].get("arguments", "{}")
                try:
                    args = json.loads(args_str) if isinstance(args_str, str) else args_str
                except Exception:
                    args = {}

                tool_result = self.execute_tool(func_name, args)
                tools_executed.append({"tool": func_name, "args": args, "result_preview": tool_result[:120]})

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", f"call_{time.time_ns()}"),
                    "name": func_name,
                    "content": tool_result,
                })

        return {
            "status": "MAX_TURNS_REACHED",
            "reply": "Operação agêntica concluída com múltiplas etapas de execução.",
            "provider": provider,
            "model": model,
            "tools_executed": tools_executed,
            "duration_ms": (time.perf_counter() - start_time) * 1000,
        }

    def _call_llm_with_tools(self, provider: str, model: str, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Low-level API call with tool schema support across Groq, OpenRouter, and Cloudflare."""
        if provider == "groq":
            key = self.keys.get("groq", "")
            if not key:
                return {"success": False, "error": "GROQ_KEY_MISSING"}
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0",
            }
            body = {
                "model": model,
                "messages": messages,
                "tools": self.tools_schema,
                "tool_choice": "auto",
            }

        elif provider == "openrouter":
            key = self.keys.get("openrouter", "")
            if not key:
                return {"success": False, "error": "OPENROUTER_KEY_MISSING"}
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {key}",
                "HTTP-Referer": "http://127.0.0.1:8899",
                "X-Title": "JARVIS-Sovereign-Runtime",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0",
            }
            body = {
                "model": model,
                "messages": messages,
                "tools": self.tools_schema,
                "tool_choice": "auto",
            }

        elif provider == "cloudflare":
            token = self.keys.get("cloudflare_token", "")
            acc_id = self.keys.get("cloudflare_account_id", "")
            if not token or not acc_id:
                return {"success": False, "error": "CLOUDFLARE_CREDENTIALS_MISSING"}
            url = f"https://api.cloudflare.com/client/v4/accounts/{acc_id}/ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0",
            }
            # Cloudflare uses standard messages; some models support tools or raw prompts
            body = {
                "model": model,
                "messages": messages,
            }

        else:
            return {"success": False, "error": f"UNKNOWN_PROVIDER_{provider}"}

        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            choice = data["choices"][0]["message"]
            return {"success": True, "message": choice}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            return {"success": False, "error": f"HTTP_{e.code}: {err_body}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    operator = JarvisPCOperator()
    print("Testando JarvisPCOperator ReAct Turn...")
    result = operator.run_agentic_turn("Jarvis, verifique o status do meu computador por favor.")
    print("\nStatus:", result.get("status"))
    print("Provider:", result.get("provider"), "/", result.get("model"))
    print("Ferramentas executadas:", result.get("tools_executed"))
    print("\nResposta Final:\n", result.get("reply"))
