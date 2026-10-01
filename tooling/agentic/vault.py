"""
vault.py // J.A.R.V.I.S. Cognitive Vault Integration Engine
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
Connects:
- Persistent episodic memory (state/jarvis_memory.local.json, ignored by Git)
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
from .vault_projection import update_projection


from .config import CONFIG

REGISTRY_ROOT = CONFIG.registry_root
MEMORY_FILE = REGISTRY_ROOT / "state" / "jarvis_memory.local.json"
NOTE_19_PATH = REGISTRY_ROOT / "19 - Memoria Persistente e Conhecimento Episodico.md"
NOTE_00_PATH = REGISTRY_ROOT / "00 - J.A.R.V.I.S. Cognitive Vault.md"


class CognitiveVaultBridge:
    """
    One-way projection from runtime memory into the Cognitive Vault.
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
        source_file = self.memory_file
        if not source_file.exists() and self.memory_file.name == "jarvis_memory.local.json":
            source_file = self.memory_file.with_name("jarvis_memory.json")
        if not source_file.exists():
            self._memory_data = {"version": "1.0.0", "profile": {}, "memories": []}
            return self._memory_data

        try:
            with open(source_file, "r", encoding="utf-8") as f:
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
            f"- User: {prof.get('user_name', 'Não informado')}",
            f"- Primary Stack: {prof.get('primary_stack', 'Não informada')}",
            "- Sovereign Constraints:"
        ]
        for r in rules[:4]:
            lines.append(f"  * {r}")

        if heuristics:
            lines.append("- Validated Heuristics (local learning records):")
            for hid, hdata in list(heuristics.items())[:3]:
                lines.append(f"  * [{hdata.get('skill', 'general')}] {hdata.get('approach', '')} -> {hdata.get('actual_result', '')}")

        return "\n".join(lines)

    def sync_to_obsidian(self) -> bool:
        """Update a redacted managed region in Note 19, preserving human-authored content."""
        try:
            lines = [
                "# 🧠 J.A.R.V.I.S. // Memória Persistente de Longo Prazo (Segundo Cérebro)",
                "",
                "> [!IMPORTANT] Projeção pública com dados privados omitidos",
                "> Perfil, fatos pessoais, contagens e heurísticas locais não são escritos nesta nota versionada.",
                "",
                "---",
                "",
                "## Limites da projeção",
                "",
                "- O armazenamento pessoal fica em `state/jarvis_memory.local.json`, fora do versionamento.",
                "- Esta nota pública não contém registros locais nem prova que o runtime os consultou.",
                "- O chat não salva fatos por padrão. Registre ou remova memórias por uma ação explícita.",
                "",
                "## Como usar",
                "",
                "Use a interface de Memória para registrar, revisar e excluir fatos. Confira o resultado antes de depender de uma memória.",
                "",
                "*Projeção versionada. Os dados privados permanecem locais.*",
                "",
                "Navegação: [[00 - J.A.R.V.I.S. Cognitive Vault]] · [[20 - Central de Integracoes Jarvis]]"
            ]

            update_projection(self.note_19_file, "\n".join(lines))
            return True
        except Exception as e:
            print(f"[JARVIS VAULT ERROR] Failed syncing to Obsidian Note 19: {e}")
            return False

    @staticmethod
    def sync_external_capabilities(root: Path, *, catalog=None) -> dict:
        """Project evidence-bound external capability state into a managed note."""
        from .vault_capabilities import VaultCapabilityProjector

        return VaultCapabilityProjector(Path(root), catalog=catalog).sync()

    @staticmethod
    def sync_registry(root: Path) -> dict:
        """Project registry navigation into the existing MOCs and Canvas."""
        from .workspace_hub import WorkspaceHub
        from .vault_projection import update_canvas_projection
        from .managed_vault_projector import ManagedVaultProjector
        root = Path(root).resolve()
        hub = WorkspaceHub(root)
        entries, error = hub.catalog()
        if error:
            raise ValueError(error)
        names = [
            '00 - J.A.R.V.I.S. Cognitive Vault.md',
            '01 - Arsenal Map of Content.md',
            '02 - Security & Quarantine Ledger.md',
            '03 - Platform Matrix.md',
            '04 - Autonomous Ingestion & Staging.md',
            '05 - Hyperion Forensic Baseline.md',
        ]
        links = [f'[[{Path(name).stem}]]' for name in names]
        atlas_config = root / 'config/vault/atlas.json'
        atlas_links = []
        if atlas_config.exists():
            from .vault_atlas import VaultAtlas, link
            atlas = VaultAtlas(root)
            if atlas.config.get('enabled'):
                atlas_links = [link(h['path']) for h in atlas.hubs]
                atlas_links += [link('JARVIS/Atlas/Skills.md')]
            else:
                atlas = None
        else:
            atlas = None
        arsenal = root / names[1]
        # Existing MOCs already contain the skill map; update only its status.
        # A new vault needs links on its first projection and subsequent refreshes.
        legacy_map = arsenal.exists() and not arsenal.read_text(encoding='utf-8-sig').lstrip().startswith('<!-- jarvis:projection:start -->')
        skill_links = [] if legacy_map else [f"- [[skills/{entry['id']}/SKILL|{entry['id']}]]" for entry in entries]
        sections = [
            ['# Navegação atual do cofre', *atlas_links, *links[1:], '[[19 - Memoria Persistente e Conhecimento Episodico]]',
             'Contexto compartilhável: use Planejar DAG no lançador de missões existente.'],
            ['# Catálogo por metadados', f'{len(entries)} registros ACTIVE com rótulo TRUSTED ou legado VERIFIED_ADAPTED.',
             'Sugestões não equivalem a autorização ou certificação atual.',
             *skill_links],
            ['# Governança atual', 'Entradas em quarentena e dispensas de revisão ficam fora desta projeção.',
             'Não foi realizada uma nova auditoria dos corpos das skills. Números e certificados históricos fora deste bloco não são verificações atuais.'],
            ['# Aplicativos e adaptadores', *[f"- {item['name']}: {item['status']}. Adaptador de formato: {'presente' if item['adapter_present'] else 'não detectado'}."
                                            for item in hub.snapshot()['connections']],
             'O plano é compartilhado manualmente; não há controle de sessões de aplicativos.'],
            ['# Ingestão e promoção', 'A sincronização lê o índice existente; não instala, promove nem executa candidatos.',
             'Mantenha revisão de origem e verificação antes de incorporar recursos.'],
            ['# Evidências', '[[reports/reanalysis/20260913/REVIEW]]',
             '[[reports/consolidation/20260914/REVIEW]]', 'Relatórios são evidências datadas, não certificação permanente.'],
        ]
        changed = []
        projector = ManagedVaultProjector(root, root / 'state')
        for name, lines in zip(names, sections):
            if projector.project_markdown(root / name, '\n\n'.join(lines + [links[0]]), kind='registry-navigation'):
                changed.append(name)
        nodes = [{'id': 'jarvis:projection:status', 'type': 'text',
                  'text': f'### Estado da projeção\n{len(entries)} registros elegíveis por metadados.\nSem certificação ou execução implícita.\n[[00 - J.A.R.V.I.S. Cognitive Vault]]',
                  'x': 0, 'y': 950, 'width': 360, 'height': 180}]
        edges = []
        if projector.project_canvas(root / 'JARVIS-Brain-Map.canvas', nodes, edges, kind='registry-navigation'):
            changed.append('JARVIS-Brain-Map.canvas')
        if atlas is not None:
            atlas.plan()
            changed.extend(atlas.apply()['changed_files'])
        return {'status': 'SUCCESS', 'changed_files': changed, 'canonical_skills': len(entries),
                'output': 'MOCs e Canvas existentes sincronizados; conteúdo humano preservado.'}


# Global singleton
class _LazyVault:
    """Importing runtime contracts must not read private vault contents."""
    _instance = None

    def __getattr__(self, name):
        if self._instance is None:
            self._instance = CognitiveVaultBridge()
        return getattr(self._instance, name)


COGNITIVE_VAULT = _LazyVault()

# Explicit v0.2 bidirectional coordinator; legacy CognitiveVaultBridge remains compatible.
from .bidirectional_vault import BidirectionalVaultBridge
