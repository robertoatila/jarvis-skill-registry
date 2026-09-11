"""Capture one bounded local check and its exact exit code, without importing the server."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

directory = Path(__file__).resolve().parent
root = directory.parents[2]
name, *command = sys.argv[1:]
if not name.replace('-', '').replace('_', '').isalnum() or not command:
    raise SystemExit('Usage: record_check.py unique-name command [args]')
record_path = directory / (name + '.json')
if record_path.exists():
    raise SystemExit('Evidence already exists; use a new check name')
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
clock = time.monotonic()
try:
    result = subprocess.run(command, cwd=root, capture_output=True, text=True,
                            encoding='utf-8', errors='replace', timeout=120)
    code, stdout, stderr = result.returncode, result.stdout, result.stderr
except subprocess.TimeoutExpired as exc:
    code, stdout, stderr = 124, str(exc.stdout or ''), str(exc.stderr or '') + '\nCHECK_TIMEOUT'
record = dict(command=command, cwd=str(root), started_utc=started,
              duration_seconds=round(time.monotonic()-clock, 3), exit_code=code,
              stdout=stdout, stderr=stderr)
record_path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps({'evidence':str(record_path),'exit_code':code,
                  'sha256':hashlib.sha256(record_path.read_bytes()).hexdigest()}))
print(stdout)
print(stderr, file=sys.stderr)
sys.exit(code)
