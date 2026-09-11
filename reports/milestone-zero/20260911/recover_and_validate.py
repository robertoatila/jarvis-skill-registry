"""Capture this Milestone Zero baseline and run isolated, selected unit suites.

Run once for recovery. Refuses to overwrite the recorded baseline or backups.
Does not launch the runtime, access providers, or execute catalogued skills.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True,
                          text=True, check=True).stdout

def main():
    if (OUT / 'baseline.json').exists():
        raise SystemExit('Baseline already exists; preserve it.')
    protected = ['README.md', '00 - J.A.R.V.I.S. Cognitive Vault.md',
                 'docs/architecture/JARVIS_ARCHITECTURE_REASSESSMENT.md',
                 'docs/AGENTIC_RUNTIME_ARCHITECTURE.md', 'docs/ARCHITECTURE.md',
                 'reports/JARVIS_RELEASE_CANDIDATE.md']
    backup = ROOT / 'backups' / 'milestone-zero-20260911'
    backup.mkdir(parents=True, exist_ok=False)
    manifest = []
    for rel in protected:
        src, dst = ROOT / rel, backup / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        assert sha(src) == sha(dst)
        manifest.append({'path': rel, 'sha256': sha(src), 'verified_copy': True})
    sources = sorted(set((ROOT / 'tooling/agentic').glob('*.py')) |
                     set((ROOT / 'tests').glob('test_agentic*.py')))
    baseline = dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),
                    head=git('rev-parse', 'HEAD').strip(), branch=git('branch', '--show-current').strip(),
                    status=git('status', '--short'), diff=git('diff'), diff_stat=git('diff', '--stat'),
                    recovery_note='Initial inspection was clean at 97ddce6; this evidence helper is newly untracked.',
                    backups=manifest, source_hashes={p.relative_to(ROOT).as_posix(): sha(p) for p in sources})
    (OUT / 'baseline.json').write_text(json.dumps(baseline, indent=2), encoding='utf-8')
    suites = ['contracts', 'foundation', 'dag', 'profiles', 'scheduler', 'composite', 'swe', 'verification']
    results = []
    with tempfile.TemporaryDirectory(prefix='jarvis-m0-') as tmp:
        env = dict(os.environ, JARVIS_REGISTRY_ROOT=tmp, PYTHONDONTWRITEBYTECODE='1')
        for name in suites:
            cmd = [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests',
                   '-p', f'test_agentic_{name}.py', '-v']
            run = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=90)
            output = run.stdout + run.stderr
            dest = OUT / f'tests-{name}.txt'
            dest.write_text(output, encoding='utf-8')
            import re
            match = re.search(r'Ran (\d+) tests?', output)
            count = int(match.group(1)) if match else 0
            results.append(dict(suite=name, command=cmd, exit_code=run.returncode,
                                tests=count, output=dest.name, sha256=sha(dest)))
            print(name, run.returncode, count)
    (OUT / 'tests.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    if any(r['exit_code'] or not r['tests'] for r in results):
        raise SystemExit(1)
    print('TOTAL', sum(r['tests'] for r in results))

if __name__ == '__main__':
    main()
