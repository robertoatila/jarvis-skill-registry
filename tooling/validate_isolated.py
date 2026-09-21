"""Run first-party tests in a disposable checkout with synthetic registry data.

Copies only public checked-in source/resources required by the first-party test
contracts. Private state, credentials and untracked local vault data are never
copied. The reported result is a fixture integration result, not a live
deployment audit.
"""
import argparse
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


PUBLIC_FOLDERS = (
    'tooling', 'tests', 'schemas', 'docs', 'examples', 'benchmarks', 'ui',
    '.github', '.obsidian', 'config', 'index', 'design-system', 'site',
    'evidence',
)
PUBLIC_ROOT_FILES = (
    'jarvis.py', 'run_tests.py', 'README.md', 'AGENTS.md', 'DESIGN.md', 'QUICKSTART.md',
    'CHANGELOG.md', '.env.example',
    '00 - J.A.R.V.I.S. Cognitive Vault.md',
    '06 - GitHub Starred Repositories.md',
    '21 - Repositorios 100k+ Estrelas e Radar de Sites Oficiais.md',
)
ALLOWED_SUFFIXES = ('.py', '.ps1', '.psm1', '.json', '.jsonl', '.md', '.txt', '.js', '.html', '.css', '.svg', '.png', '.webmanifest')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pattern', default='test_*.py')
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    report = Path(args.report).resolve()
    report.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='jarvis-validation-') as directory:
        sandbox = Path(directory)
        for folder in PUBLIC_FOLDERS:
            source_root = root / folder
            if not source_root.exists():
                continue
            for source in source_root.rglob('*'):
                if not source.is_file() or source.is_symlink() or '__pycache__' in source.parts:
                    continue
                if source.suffix.lower() not in ALLOWED_SUFFIXES:
                    continue
                destination = sandbox / source.relative_to(root)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
        for name in PUBLIC_ROOT_FILES:
            source = root / name
            if not source.is_file() or source.is_symlink():
                continue
            destination = sandbox / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)

        # The isolated runtime must use one coherent synthetic registry. Copying
        # the repository's real resources.jsonl while replacing skills/ with
        # synthetic fixtures creates a false catalog/directory mismatch and can
        # make valid fixture capabilities look quarantined or unresolved.
        skills = ['systematic-code-debugging', 'comprehensive-code-review', 'python-pro', 'ast-grep-search',
                  'osint', 'blackbird-osint-recon', 'fastapi-pro', 'swe-bench'] + [f'fixture-skill-{i}' for i in range(15)]
        for name in skills:
            target = sandbox/'skills'/name/'SKILL.md'
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f'---\nname: {name}\ndescription: Synthetic test fixture\n---\n'
                              + ('Fixture instruction for disclosure accounting only.\n' * 200), encoding='utf-8')

        resource_index = sandbox/'index'/'resources.jsonl'
        resource_index.parent.mkdir(parents=True, exist_ok=True)
        fixture_records = [
            {
                'canonical_name': name,
                'display_name': name,
                'capabilities': [name],
                'description': 'Synthetic isolated-validation skill fixture',
                'version': '1.0.0',
                'lifecycle_state': 'ACTIVE',
                'trust_level': 'TRUSTED',
            }
            for name in skills
        ]
        resource_index.write_text(
            ''.join(json.dumps(record, sort_keys=True) + '\n' for record in fixture_records),
            encoding='utf-8',
        )

        subprocess.run(['git', 'init', '--initial-branch=main', str(sandbox)], check=True, capture_output=True)
        subprocess.run(['git', '-C', str(sandbox), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                        'commit', '--allow-empty', '-m', 'Isolated validation fixture'], check=True, capture_output=True)
        # Applies to child Python examples as well. Tests may use local HTTP fixtures.
        (sandbox/'sitecustomize.py').write_text('''import sys
def audit(event, args):
    if event == 'socket.connect':
        host = args[1][0]
        if host not in ('127.0.0.1', '::1', 'localhost'):
            raise PermissionError('External network disabled in fixture validation')
sys.addaudithook(audit)
''', encoding='utf-8')
        env = dict(os.environ, JARVIS_REGISTRY_ROOT=str(sandbox), PYTHONDONTWRITEBYTECODE='1',
                   PYTHONIOENCODING='utf-8', PYTHONPATH=str(sandbox))
        command = [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', args.pattern, '-v']
        started = time.monotonic()
        result = subprocess.run(command, cwd=sandbox, env=env, capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=300)
        output = result.stdout + result.stderr
        report.with_suffix('.txt').write_text(output, encoding='utf-8')
        totals = re.findall(r'Ran (\d+) tests? in ', output)
        report.write_text(json.dumps({'command': command, 'exit_code': result.returncode,
            'duration_seconds': round(time.monotonic()-started, 3),
            'tests_run': int(totals[-1]) if totals else 0,
            'scope': 'first-party public source/resources; coherent synthetic skill registry; empty private state; external network denied',
            'log': report.with_suffix('.txt').name}, indent=2), encoding='utf-8')
        print(output[-16000:])
        return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
