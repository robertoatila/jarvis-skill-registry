"""Read-only connection inventory; mission planning belongs to the existing planner.

Uses registry metadata only. Never imports providers or reads skill payloads,
credentials, chat history, personal memory or quarantined material.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urlencode

MAX_INDEX_BYTES = 8 * 1024 * 1024


class WorkspaceHub:
    def __init__(self, root, which=shutil.which):
        self.root = Path(root).resolve()
        self.which = which

    def _metadata(self, relative):
        path = self.root / relative
        for part in (path, *path.parents):
            if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
                raise ValueError('Linked metadata paths are not supported')
        if path.stat().st_size > MAX_INDEX_BYTES:
            raise ValueError('Metadata exceeds size limit')
        return path.read_text(encoding='utf-8-sig')

    def catalog(self):
        try:
            rows = [json.loads(line) for line in self._metadata('index/resources.jsonl').splitlines() if line.strip()]
            if any(not isinstance(row, dict) for row in rows):
                raise ValueError('Invalid resource record')
            denied = {str(row.get('canonical_name', '')).casefold() for row in rows
                      if str(row.get('lifecycle_state', '')).upper() == 'QUARANTINED'}
            entries = {}
            for row in rows:
                name = row.get('canonical_name')
                if not isinstance(name, str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,127}', name):
                    continue
                if name.casefold() in denied:
                    continue
                # Metadata eligibility is not permission to install or execute.
                if row.get('lifecycle_state') != 'ACTIVE' or row.get('trust_level') not in ('TRUSTED', 'VERIFIED_ADAPTED'):
                    continue
                entries[name] = {'id': name, 'description': str(row.get('description', ''))[:400],
                                 'capabilities': [str(c)[:80] for c in row.get('capabilities', [])[:20]]}
            return sorted(entries.values(), key=lambda entry: entry['id']), None
        except (OSError, ValueError, TypeError):
            return [], 'Índice indisponível ou inválido; nenhuma skill selecionada.'

    def snapshot(self):
        entries, error = self.catalog()
        connections = []
        for key, label, executable, adapter in (
            ('obsidian', 'Obsidian', 'obsidian', None),
            ('antigravity', 'Antigravity IDE', 'antigravity', 'gemini'),
            ('codex', 'Codex', 'codex', 'codex'),
            ('chatgpt', 'ChatGPT Desktop', None, 'chatgpt'),
        ):
            detected = bool(executable and self.which(executable))
            adapter_present = False
            if adapter:
                try:
                    adapter_present = bool(json.loads(self._metadata(f'adapters/{adapter}/adapter.json')).get('adapter_id'))
                except (OSError, ValueError, AttributeError):
                    pass
            connections.append({'id': key, 'name': label, 'command_detected': detected,
                                'adapter_present': adapter_present, 'session_verified': False,
                                'status': 'Comando localizado; sessão não verificada' if detected
                                else 'Sessão não verificada',
                                'detail': 'Projeção local de notas disponível' if key == 'obsidian'
                                else 'Contexto compartilhável disponível; entrega manual ao aplicativo'})
        return {'schema_version': '1.0', 'connections': connections,
                'eligible_skills': len(entries), 'catalog_error': error,
                'autonomy': {'mode': 'Execução local com ações explícitas',
                             'tools': ['local.read_file', 'local.write_text'],
                             'provider_invoked': False,
                             'note': 'Seleção por metadados. Planejamento livre por modelo e sessões dos aplicativos ainda exigem integração.'},
                'obsidian_url': 'obsidian://open?' + urlencode({'path': str(self.root / '00 - J.A.R.V.I.S. Cognitive Vault.md')})}

    def sync_obsidian(self):
        # Compatibility entry point: projection belongs to the existing vault bridge.
        from .vault import CognitiveVaultBridge
        return CognitiveVaultBridge.sync_registry(self.root)

    def reconcile_obsidian(self):
        """Run one explicit bidirectional Vault reconciliation cycle."""
        from .vault import BidirectionalVaultBridge
        return BidirectionalVaultBridge(self.root).reconcile_once()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument('--sync-obsidian', action='store_true')
    actions.add_argument('--reconcile-obsidian', action='store_true')
    args = parser.parse_args()
    hub = WorkspaceHub(args.root)
    if args.reconcile_obsidian:
        result = hub.reconcile_obsidian()
    elif args.sync_obsidian:
        result = hub.sync_obsidian()
    else:
        result = hub.snapshot()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
