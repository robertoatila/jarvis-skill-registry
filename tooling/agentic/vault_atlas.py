"""Deterministic, provenance-bound navigation for the existing Cognitive Vault.

No network, embeddings, keyword inference, execution or deletion. Generated
navigation is not a claim that two source notes are semantically equivalent.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import html
import json
import os
from pathlib import Path, PurePosixPath
import re

from .managed_vault_projector import ManagedVaultProjector
from .vault_projection import START, END, _reject_linked_path, _write_verified
from .vault_projection_receipts import ProjectionReceiptStore

MASTER = '00 - J.A.R.V.I.S. Cognitive Vault.md'
ARSENAL = '01 - Arsenal Map of Content.md'
CONFIG = 'config/vault/atlas.json'
RELATIONS = {'uses_skill', 'belongs_to_project', 'supported_by', 'produced_by',
             'documents', 'references', 'involves_person', 'supersedes'}
SKIP = {'.git', '.obsidian', 'node_modules', '__pycache__', 'backups', 'state',
        '.jarvis-profile', 'staging_all_skills_chatgpt', 'staging_chatgpt_bundle',
        'temp_chatgpt_clean'}
MAX_BYTES = 16 * 1024 * 1024


class AtlasReceiptStore(ProjectionReceiptStore):
    """Use the canonical receipt contract with individual storage for scale."""

    def record(self, receipt):
        self.record_individual(receipt)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(root, relative):
    if not isinstance(relative, str) or not relative or '\\' in relative:
        raise ValueError('Expected a canonical relative path')
    path = PurePosixPath(relative)
    if path.is_absolute() or '..' in path.parts or ':' in relative or path.as_posix() != relative:
        raise ValueError('Path must stay inside the Vault')
    target = root / relative
    _reject_linked_path(target, 'Linked atlas paths are not supported')
    return target


def read(root, relative):
    path = safe_path(root, relative)
    if path.stat().st_size > MAX_BYTES:
        raise ValueError(f'Input exceeds atlas bound: {relative}')
    return path.read_bytes()


def literal(value):
    """Untrusted source prose must not create links, tags, HTML or markers."""
    return html.escape(str(value), quote=True).replace('[', '&#91;').replace(']', '&#93;').replace('#', '&#35;').replace('|', '&#124;').replace('\n', ' ').replace('\r', ' ')


def link(path, label=None):
    if any(c in path for c in '[]|#\n\r'):
        raise ValueError('Unrepresentable wikilink path')
    return f'[[{path}|{literal(label or Path(path).stem)}]]'


def slug(value):
    # Stable collision-resistant portable names, including Windows reserved names.
    return re.sub(r'[^a-z0-9-]+', '-', value.lower()).strip('-')[:70] + '-' + digest(value.encode())[:10]


def validate_region(text):
    if START in text or END in text:
        if text.count(START) != 1 or text.count(END) != 1 or text.index(START) > text.index(END):
            raise ValueError('Ambiguous atlas projection markers')


class VaultAtlas:
    def __init__(self, root):
        self.root = Path(root).absolute()
        _reject_linked_path(self.root, 'Linked atlas root')
        self.inputs = {}
        raw = self.source(CONFIG)
        self.config = json.loads(raw)
        if self.config.get('schema_version') != 1 or self.config.get('generated_root') != 'JARVIS/Atlas':
            raise ValueError('Unsupported atlas configuration')
        self.page_size = self.config['page_size']
        if not isinstance(self.page_size, int) or not 10 <= self.page_size <= 200:
            raise ValueError('Invalid atlas page size')
        self.generated = self.config['generated_root']
        self.hubs = self.config['hubs']
        paths = [h['path'] for h in self.hubs]
        if len(set(paths)) != len(paths) or len({h['id'] for h in self.hubs}) != len(paths):
            raise ValueError('Duplicate atlas hub')
        for path in paths:
            safe_path(self.root, path)
            if not path.endswith('.md') or '/' in path or not re.match(r'\d\d - ', path):
                raise ValueError('Atlas hub must be a numbered root note')
        self.outputs = {}
        self.warnings = []

    def source(self, relative):
        raw = read(self.root, relative)
        self.inputs[relative] = digest(raw)
        return raw

    def inventory(self):
        notes = {}
        counts = Counter()
        skipped = []
        for base, dirs, files in os.walk(self.root, followlinks=False):
            keep = []
            for name in sorted(dirs):
                path = Path(base) / name
                rel = path.relative_to(self.root).as_posix()
                if name in SKIP or rel == self.generated or path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
                    skipped.append(rel)
                else:
                    keep.append(name)
            dirs[:] = keep
            for name in sorted(files):
                path = Path(base) / name
                rel = path.relative_to(self.root).as_posix()
                counts[rel.split('/')[0] if '/' in rel else '(root)'] += 1
                if path.suffix.lower() != '.md' or rel in {h['path'] for h in self.hubs}:
                    continue
                # Imported payloads are indexed by path only, never interpreted.
                if any(c in rel for c in '[]|#\n\r'):
                    self.warnings.append({'path': rel, 'reason': 'unrepresentable wikilink'})
                    continue
                if rel.startswith(('skills/', 'staging/', 'archives/')):
                    safe_path(self.root, rel)
                    notes[rel] = ''
                    continue
                notes[rel] = self.source(rel).decode('utf-8-sig')
        return notes, dict(counts), skipped

    def page(self, path, title, parent, lines, tag='hub'):
        self.outputs[path] = '\n'.join([
            f'# {title}', '', f'#jarvis/{tag}', '',
            '> Navegação derivada de fontes locais. Não certifica conteúdo nem autoriza execução.', '',
            '↑ ' + link(parent), '', *lines, '',
        ])

    def collection(self, paths, parent, key):
        paths = sorted(set(paths), key=str.casefold)
        pages = []
        for i in range(0, len(paths), self.page_size):
            path = f'{self.generated}/Collections/{key}-{i // self.page_size + 1:03}.md'
            self.page(path, f'{key} · {i // self.page_size + 1}', parent,
                      ['Classificação: índice por caminho ou tipo declarado; não é uma relação causal.', '',
                       *['- ' + link(p, p) for p in paths[i:i+self.page_size]]])
            pages.append('- ' + link(path))
        return pages

    def external(self, parent):
        source = 'cache/starred_catalog.json'
        if not (self.root / source).exists():
            self.warnings.append({'path': source, 'reason': 'absent; external catalog not projected'})
            return [], 0
        raw = self.source(source)
        rows = json.loads(raw)
        if not isinstance(rows, list):
            raise ValueError('Starred cache must be an array')
        records = defaultdict(list)
        languages = defaultdict(list)
        owners = defaultdict(list)
        for row in rows:
            name = row.get('full_name') if isinstance(row, dict) else None
            if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+', name) or name.split('/')[1] in {'.', '..'}:
                raise ValueError('Invalid starred owner/repository')
            language = row.get('language') or 'Unknown'
            if not isinstance(language, str) or len(language) > 100:
                raise ValueError('Invalid declared language')
            records[name.casefold()].append(row)
        for name, variants in records.items():
            path = f'{self.generated}/GitHub/{slug(name)}.md'
            owners[name.split('/')[0]].append(path)
            for language in sorted({row.get('language') or 'Unknown' for row in variants}):
                languages[language].append(path)
            if len(variants) > 1:
                self.warnings.append({'path': source, 'identity': name, 'reason': 'duplicate identity; all source variants retained in one note', 'variants': len(variants)})
        language_paths = {name: f'{self.generated}/Languages/{slug(name)}.md' for name in languages}
        owner_paths = {name: f'{self.generated}/Owners/{slug(name)}.md' for name, paths in owners.items() if len(paths) >= 3}
        for name, variants in records.items():
            owner = name.split('/')[0]
            path = f'{self.generated}/GitHub/{slug(name)}.md'
            langs = sorted({row.get('language') or 'Unknown' for row in variants})
            lines = [f'Fonte: [GitHub · {literal(name)}](https://github.com/{name})', '',
                     f'Proveniência: `{source}` · identidade normalizada `{name}`', '',
                     'Estado: **referência externa; não revisada nem executada**.', '',
                     'Linguagens declaradas no cache: ' + ' · '.join(link(language_paths[x], x) for x in langs)]
            if owner in owner_paths:
                lines += ['Proprietário declarado: ' + link(owner_paths[owner], owner)]
            for row in sorted(variants, key=lambda r: json.dumps(r, sort_keys=True)):
                record_hash = digest(json.dumps(row, sort_keys=True, ensure_ascii=False).encode())
                lines += ['', '## Registro de origem', '', f'SHA-256: `{record_hash}`',
                          literal(row.get('description') or 'Sem descrição no cache.'), '',
                          'Metadados preservados (não são links inferidos):', '',
                          literal(json.dumps(row, ensure_ascii=False, sort_keys=True))]
            self.page(path, literal(name), language_paths[langs[0]], lines, 'external')
        for language, paths in sorted(languages.items()):
            self.page(language_paths[language], 'Linguagem · ' + literal(language), parent,
                      [f'{len(paths)} registros com este valor explícito no cache. Unknown significa ausência de classificação.', '',
                       *self.collection(paths, language_paths[language], 'language-' + slug(language))])
        for owner, path in sorted(owner_paths.items()):
            self.page(path, 'Proprietário · ' + literal(owner), parent,
                      [f'{len(owners[owner])} registros com o mesmo proprietário; não implica integração entre eles.', '',
                       *self.collection(owners[owner], path, 'owner-' + slug(owner))])
        return ['## Linguagens declaradas', '', *['- ' + link(p, name) for name, p in sorted(language_paths.items())],
                '', '## Proprietários com três ou mais registros', '',
                *self.collection(list(owner_paths.values()), parent, 'owners')], len(records)

    def plan(self):
        notes, counts, skipped = self.inventory()
        relations = []
        for source, text in notes.items():
            # Narrow JSON-in-YAML contract; never interpret arbitrary YAML or prose.
            fm = re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)', text, re.S)
            if not fm:
                continue
            declarations = re.findall(r'^jarvis_relations:\s*(.+)$', fm[1], re.M)
            if len(declarations) > 1:
                raise ValueError(f'Duplicate relationship declaration: {source}')
            if not declarations:
                continue
            data = json.loads(declarations[0])
            if not isinstance(data, list):
                raise ValueError(f'Expected a relation array: {source}')
            for rel in data:
                if not isinstance(rel, dict) or rel.get('type') not in RELATIONS:
                    raise ValueError(f'Unknown relationship type: {source}')
                target = rel.get('target')
                safe_path(self.root, target)
                if target not in notes or target == source:
                    raise ValueError(f'Unresolved or self relationship: {source} -> {target}')
                relations.append((source, rel['type'], target))
        external_count = 0
        for hub in self.hubs:
            paths = []
            for path, text in notes.items():
                fm = re.match(r'\A---\r?\n(.*?)\r?\n---', text, re.S)
                kind = re.search(r'^type:\s*[\"\']?([a-z-]+)[\"\']?\s*$', fm[1], re.M) if fm else None
                if any(path.startswith(prefix) for prefix in hub['prefixes']) or (kind and kind[1] in hub['types']):
                    paths.append(path)
            anchors = [p for p in self.config.get('anchors', {}).get(hub['id'], []) if p in notes]
            lines = [f'## Fontes existentes · {len(set(paths))}', '',
                     *['- ' + link(p) for p in anchors], '',
                     *self.collection(paths, hub['path'], hub['id'])]
            if not paths and not anchors:
                lines += ['Nenhuma nota deste tipo foi encontrada. Não foram inventadas pessoas, execuções ou resultados.']
            if hub['id'] == 'external':
                extra, external_count = self.external(hub['path'])
                lines += ['', *extra]
            if hub['id'] == 'relations':
                lines += ['', 'Relações explícitas em `jarvis_relations`; o autor declara a relação, não a automação.', '',
                          *[f'- {link(s)} — `{r}` → {link(t)}' for s, r, t in sorted(set(relations))]]
            self.page(hub['path'], hub['title'], MASTER, lines)
        # Keep the canonical Arsenal; the Atlas supplements it with all on-disk paths.
        skills = [p for p in notes if p.startswith('skills/') and p.endswith('/SKILL.md')]
        self.page(f'{self.generated}/Skills.md', 'Skills presentes no Vault', ARSENAL,
                  ['Este índice não promove candidatos nem substitui a elegibilidade do runtime.', '',
                   *self.collection(skills, f'{self.generated}/Skills.md', 'skills')])
        for body in self.outputs.values():
            for target in re.findall(r'\[\[([^|\]]+)\|', body):
                if target not in self.outputs and not safe_path(self.root, target).is_file():
                    raise ValueError(f'Generated link has no target: {target}')
        # Preflight every target before any write, then capture optimistic revisions.
        self.originals = {}
        for relative, body in self.outputs.items():
            path = safe_path(self.root, relative)
            raw = path.read_bytes() if path.exists() else None
            validate_region(raw.decode('utf-8') if raw else '')
            if START in body or END in body:
                raise ValueError('Reserved projection marker in generated body')
            self.originals[relative] = raw
        self.report = {'schema_version': 1, 'source_notes': len(notes), 'files_by_area': counts,
                       'skipped_scan_paths': skipped, 'external_records': external_count,
                       'explicit_relations': len(set(relations)), 'skill_paths': len(skills),
                       'planned_notes': len(self.outputs), 'warnings': self.warnings,
                       'input_hashes': self.inputs, 'deletions': 0,
                       'classification': 'navigation and declared metadata; not inferred semantic truth'}
        return self.report

    def apply(self):
        if not hasattr(self, 'report'):
            self.plan()
        for path, expected in self.inputs.items():
            if digest(read(self.root, path)) != expected:
                raise RuntimeError('Atlas source changed; rebuild the plan')
        for relative, original in self.originals.items():
            path = safe_path(self.root, relative)
            if (path.read_bytes() if path.exists() else None) != original:
                raise RuntimeError('Atlas target changed; rebuild the plan')
        projector = ManagedVaultProjector(self.root, self.root / 'state',
                                         receipt_store=AtlasReceiptStore(self.root / 'state'))
        projector.receipts._load()  # Corrupted state must fail before note writes.
        changed = []
        for relative, body in self.outputs.items():
            if projector.project_markdown(self.root / relative, body, kind='cognitive-atlas'):
                changed.append(relative)
        return {**self.report, 'changed_files': changed, 'status': 'SUCCESS'}


def apply_graph(root, profile):
    root = Path(root).absolute()
    settings = json.loads(read(root, f'config/vault/graph-{profile}.json'))
    path = safe_path(root, '.obsidian/graph.json')
    original = path.read_bytes() if path.exists() else None
    current = json.loads(original) if original else {}
    current.update(settings)  # Preserve unknown plugin/version fields.
    return _write_verified(path, (json.dumps(current, ensure_ascii=False, indent=2) + '\n').encode(), original)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--apply', action='store_true', help='Explicitly write the preflighted projection')
    parser.add_argument('--graph', choices=['universe', 'core', 'external'])
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    atlas = VaultAtlas(args.root)
    result = atlas.plan()
    if args.apply:
        result = atlas.apply()
        if args.graph:
            result['graph_changed'] = apply_graph(args.root, args.graph)
    elif args.graph:
        result['graph_planned'] = args.graph
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('input_hashes','changed_files','files_by_area','skipped_scan_paths')}, ensure_ascii=False, indent=2))
    if 'changed_files' in result:
        print(f"Changed notes: {len(result['changed_files'])}")


if __name__ == '__main__':
    main()
