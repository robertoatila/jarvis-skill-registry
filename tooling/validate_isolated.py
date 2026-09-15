"""Run first-party tests in a disposable checkout with synthetic registry data.

Never copies private state, configuration credentials, vault notes or skill bodies.
The reported result is a fixture integration result, not a live deployment audit.
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
        for folder in ('tooling', 'tests', 'schemas', 'docs', 'examples', 'benchmarks', 'ui', '.github'):
            for source in (root / folder).rglob('*'):
                if not source.is_file() or source.is_symlink() or '__pycache__' in source.parts:
                    continue
                if source.suffix.lower() not in ('.py', '.ps1', '.psm1', '.json', '.md', '.js', '.html', '.css', '.svg', '.png'):
                    continue
                destination = sandbox / source.relative_to(root)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
        for name in ('run_tests.py', 'README.md'):
            shutil.copyfile(root/name, sandbox/name)
        skills = ['systematic-code-debugging', 'comprehensive-code-review', 'python-pro', 'ast-grep-search',
                  'osint', 'blackbird-osint-recon', 'fastapi-pro', 'swe-bench'] + [f'fixture-skill-{i}' for i in range(15)]
        for name in skills:
            target = sandbox/'skills'/name/'SKILL.md'
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f'---\nname: {name}\ndescription: Synthetic test fixture\n---\n'
                              + ('Fixture instruction for disclosure accounting only.\n' * 200), encoding='utf-8')
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
            'scope': 'first-party source; synthetic skill catalog; empty private state; external network denied',
            'log': report.with_suffix('.txt').name}, indent=2), encoding='utf-8')
        print(output[-16000:])
        return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
