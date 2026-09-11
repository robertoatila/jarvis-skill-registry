"""
vault.py // J.A.R.V.I.S. Cognitive Vault Integration Engine
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
Connects:
- Persistent episodic memory (state/jarvis_memory.json)
- Validated heuristics from Phase 12 (LearningEngine)
- Obsidian Vault Notes ('00 - J.A.R.V.I.S. Cognitive Vault.md', Note 19)
- Context synthesis for agent goal planning
"""

from __future__ import annotations
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any
from datetime import datetime, timezone

from .learning import LEARNING_ENGINE, LearningEngine


REGISTRY_ROOT = Path("E:/.skill-registry").resolve()
MEMORY_FILE = REGISTRY_ROOT / "state" / "jarvis_memory.json"
NOTE_19_PATH = REGISTRY_ROOT / "19 - Memoria Persistente e Conhecimento Episodico.md"
NOTE_00_PATH = REGISTRY_ROOT / "00 - J.A.R.V.I.S. Cognitive Vault.md"


class CognitiveVaultBridge:
    """
    Bi-directional bridge between the Agentic Runtime and the Cognitive Vault.
    Provides verified contextual memory and validated heuristics for agent execution.
    """

    def __init__(
        self,
        memory_file: Path = MEMORY_FILE,
        note_19_file: Path = NOTE_19_PATH,
        learning_engine: Optional[LearningEngine] = None
    ):
        self.memory_file = memory_file
        self.note_19_file = note_19_file
        self.learning_engine = learning_engine or LEARNING_ENGINE
        self._memory_data: Dict[str, Any] = {}
        self.load_memory()

    def load_memory(self) -> Dict[str, Any]:
        if not self.memory_file.exists():
            self._memory_data = {"version": "1.0.0", "profile": {}, "memories": []}
            return self._memory_data

        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                self._memory_data = json.load(f)
        except Exception as e:
            print(f"[JARVIS VAULT ERROR] Failed reading memory file: {e}")
            self._memory_data = {"version": "1.0.0", "profile": {}, "memories": []}

        return self._memory_data

    def get_user_profile(self) -> Dict[str, Any]:
        return self._memory_data.get("profile", {})

    def get_memories(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        mems = self._memory_data.get("memories", [])
        if category:
            return [m for m in mems if m.get("category", "").lower() == category.lower()]
        return mems

    def build_agent_context(self, task_domain: str = "general") -> str:
        """
        Synthesizes a compact, token-efficient context prompt (< 300 words)
        injecting verified user rules, project constraints, and validated heuristics.
        """
        prof = self.get_user_profile()
        rules = prof.get("operational_rules", [])
        heuristics = self.learning_engine.get_validated_heuristics()

        lines = [
            "# J.A.R.V.I.S. Cognitive Context Baseline",
            f"- User: {prof.get('user_name', 'Ad')}",
            f"- Primary Stack: {prof.get('primary_stack', 'Java, Python, Vanilla CSS')}",
            "- Sovereign Constraints:"
        ]
        for r in rules[:4]:
            lines.append(f"  * {r}")

        if heuristics:
            lines.append("- Validated Heuristics (SSP-v13.2 Certified):")
            for hid, hdata in list(heuristics.items())[:3]:
                lines.append(f"  * [{hdata.get('skill', 'general')}] {hdata.get('approach', '')} -> {hdata.get('actual_result', '')}")

        return "\n".join(lines)

    def sync_to_obsidian(self) -> bool:
        """Synchronizes current memory state into Note 19 and Note 00."""
        try:
            prof = self.get_user_profile()
            mems = self.get_memories()
            heuristics = self.learning_engine.get_validated_heuristics()

            lines = [
                "# 🧠 J.A.R.V.I.S. // Memória Persistente de Longo Prazo (Segundo Cérebro)",
                "",
                "> [!NOTE] 🏛️ Conhecimento Episódico Soberano e Permanente",
                "> Hipocampo Neural sincronizado com o runtime agentic J.A.R.V.I.S.",
                "",
                "---",
                "",
                "## 👤 Perfil do Usuário & Regras Operacionais",
                f"- **Nome**: `{prof.get('user_name', 'Ad')}`",
                f"- **Stack**: `{prof.get('primary_stack', 'Java, Spring Boot, Python')}`",
                f"- **Total de Fatos**: **`{len(mems)}` registrados**",
                f"- **Heurísticas Validadas**: **`{len(heuristics)}` ativas**",
                "",
                "| ID | Categoria | Fato / Instrução | Importância |",
                "| :---: | :---: | :--- | :---: |"
            ]

            for m in mems:
                mid = m.get("id", "mem")
                cat = m.get("category", "general").upper()
                fact = m.get("fact", "").replace("|", "/")
                imp = m.get("importance", "MEDIUM")
                lines.append(f"| `{mid}` | `{cat}` | {fact} | `{imp}` |")

            if heuristics:
                lines.extend([
                    "",
                    "---",
                    "",
                    "## 💡 Heurísticas Validadas em Runtime",
                    "| ID | Skill | Abordagem Comprovada | Confiança |",
                    "| :---: | :---: | :--- | :---: |"
                ])
                for hid, h in heuristics.items():
                    sk = h.get("skill", "general")
                    app = h.get("approach", "").replace("|", "/")
                    conf = f"{int(h.get('confidence', 0.9) * 100)}%"
                    lines.append(f"| `{hid}` | `{sk}` | {app} | `{conf}` |")

            lines.extend([
                "",
                "---",
                "*Documento sincronizado automaticamente pelo motor de aprendizado J.A.R.V.I.S. SSP-v13.2.*"
            ])

            self.note_19_file.write_text("\n".join(lines), encoding="utf-8")
            return True
        except Exception as e:
            print(f"[JARVIS VAULT ERROR] Failed syncing to Obsidian Note 19: {e}")
            return False


# Global singleton
COGNITIVE_VAULT = CognitiveVaultBridge()
