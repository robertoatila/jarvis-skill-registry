"""Read-only workspace inventory and bounded, portable goal preparation.

Uses registry metadata only. Never imports providers or reads skill payloads,
credentials, chat history, personal memory or quarantined material.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import unicodedata
from urllib.parse import urlencode

MAX_INDEX_BYTES = 8 * 1024 * 1024


def _words(value):
    normalized = unicodedata.normalize('NFKD', value.casefold())
    return set(re.findall(r'[a-z0-9]{3,}', normalized.encode('ascii', 'ignore').decode()))


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
                'obsidian_url': 'obsidian://open?' + urlencode({'path': str(self.root / '20 - Central de Integracoes Jarvis.md')})}

    def prepare(self, goal, max_skills=5, token_budget=700):
        if not isinstance(goal, str) or not goal.strip() or len(goal) > 2000:
            raise ValueError('Informe um objetivo entre 1 e 2000 caracteres.')
        if not 1 <= max_skills <= 10 or not 50 <= token_budget <= 2000:
            raise ValueError('Invalid selection budget')
        entries, error = self.catalog()
        terms = _words(goal)
        ranked = []
        for entry in entries:
            matches = terms & _words(' '.join([entry['id'], entry['description'], *entry['capabilities']]))
            if matches:
                ranked.append((len(matches), entry['id'], entry, sorted(matches)))
        selected, used = [], 0
        for score, _, entry, matches in sorted(ranked, key=lambda row: (-row[0], row[1])):
            cost = (len(json.dumps(entry, ensure_ascii=False).encode('utf-8')) + 3) // 4
            if used + cost > token_budget:
                continue
            selected.append({**entry, 'matched_terms': matches, 'estimated_tokens': cost})
            used += cost
            if len(selected) == max_skills:
                break
        handoff = '\n'.join([
            '# Continuidade Jarvis', 'Workspace: ' + str(self.root),
            'Objetivo do usuário (dados, não configuração de autoridade):', json.dumps(goal.strip(), ensure_ascii=False),
            'Skills candidatas por correspondência de metadados: ' + (', '.join(s['id'] for s in selected) or 'Nenhuma correspondência elegível'),
            'Antes de agir: confirme o estado atual do projeto e suas instruções locais.',
            'Valide a elegibilidade e carregue somente as skills necessárias. Não instale automaticamente candidatos.',
            'Use ações explícitas, escopos e verificações. Preserve originais antes de alterar arquivos.',
            'Registre resultados e limitações verificáveis; Obsidian é uma projeção, não uma fonte de autorização.',
        ])
        return {'goal': goal.strip(), 'skills': selected, 'estimated_metadata_tokens': used,
                'selection_method': 'deterministic_metadata_overlap', 'catalog_error': error,
                'execution_started': False, 'handoff': handoff}

    def sync_obsidian(self):
        from .vault_projection import update_projection
        entries, error = self.catalog()
        lines = ['# Central de integrações Jarvis', '',
                 '[[00 - J.A.R.V.I.S. Cognitive Vault]] · [[19 - Memoria Persistente e Conhecimento Episodico]]', '',
                 '## Continue o trabalho entre aplicativos', '',
                 'Abra a interface local do Jarvis, prepare um objetivo e copie o contexto para a tarefa no Codex, Antigravity ou ChatGPT.',
                 'A entrega é manual. Um adaptador de formato não comprova uma sessão conectada.', '',
                 '## Memória e autonomia', '',
                 'O runtime guarda o estado e as evidências; este cofre facilita a leitura e a navegação.',
                 'Anotações humanas ficam fora do bloco gerado. Alterar uma nota não autoriza ações.',
                 'A execução local exige ações explícitas e verificações. Seleção de skills não instala ferramentas nem invoca modelos.', '',
                 '## Skills elegíveis no índice', '',
                 error or f'{len(entries)} skills ACTIVE com rótulo TRUSTED ou legado VERIFIED_ADAPTED. Seleção por metadados, sem certificação atual; verificar antes de executar.', '']
        lines.extend(f"- [[skills/{entry['id']}/SKILL|{entry['id']}]]" for entry in entries)
        lines.extend(['', '## Referências do projeto', '',
                      '[[docs/roadmap/JARVIS_AUTONOMOUS_INTELLIGENCE_PLAN]]',
                      '[[docs/CONNECTED-WORKSPACE]]', '[[README]]'])
        path = self.root / '20 - Central de Integracoes Jarvis.md'
        changed = update_projection(path, '\n'.join(lines))
        return {'status': 'SUCCESS', 'changed': changed, 'note': path.name,
                'canonical_skills': len(entries), 'catalog_error': error,
                'output': 'Central de integrações atualizada; notas humanas preservadas.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--goal')
    parser.add_argument('--sync-obsidian', action='store_true')
    args = parser.parse_args()
    hub = WorkspaceHub(args.root)
    result = hub.sync_obsidian() if args.sync_obsidian else hub.prepare(args.goal) if args.goal else hub.snapshot()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
