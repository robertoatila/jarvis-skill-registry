"""Preserve human notes while updating one explicitly managed Markdown region."""
from pathlib import Path
import hashlib
import os
import tempfile
import uuid
import json

START = '<!-- jarvis:projection:start -->'
END = '<!-- jarvis:projection:end -->'


def update_projection(path: Path, body: str) -> bool:
    """Back up exact original bytes; reject damaged markers and linked paths."""
    path = Path(path).absolute()
    for part in (path, *path.parents):
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise ValueError('Linked vault paths are not supported')
    if START in body or END in body:
        raise ValueError('Reserved projection markers in source content')
    original = path.read_bytes() if path.exists() else None
    current = original.decode('utf-8') if original is not None else ''
    region = START + '\n' + body.rstrip() + '\n' + END
    if START in current or END in current:
        if current.count(START) != 1 or current.count(END) != 1:
            raise ValueError('Ambiguous projection markers')
        first, last = current.index(START), current.index(END)
        if last < first:
            raise ValueError('Reversed projection markers')
        updated = current[:first] + region + current[last + len(END):]
    else:
        updated = current + ('\n\n' if current else '') + region + '\n'
    payload = updated.encode('utf-8')
    return _write_verified(path, payload, original)


def _write_verified(path, payload, original):
    if payload == original:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    if original is not None:
        backup_dir = path.parent / 'backups' / 'vault-projection'
        for part in (backup_dir, *backup_dir.parents):
            if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
                raise ValueError('Linked backup paths are not supported')
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / (uuid.uuid4().hex + '.bak')
        with backup.open('xb') as stream:
            stream.write(original)
            stream.flush()
            os.fsync(stream.fileno())
        if hashlib.sha256(backup.read_bytes()).digest() != hashlib.sha256(original).digest():
            raise OSError('Backup verification failed')
    fd, temporary = tempfile.mkstemp(prefix='.projection-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if (path.read_bytes() if path.exists() else None) != original:
            raise RuntimeError('Note changed during projection; retry from fresh content')
        if original is None:
            os.link(temporary, path)
        else:
            os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return True


def update_canvas_projection(path: Path, nodes: list, edges: list) -> bool:
    """Replace only Jarvis-owned nodes/edges; preserve other Canvas fields."""
    path = Path(path).absolute()
    for part in (path, *path.parents):
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise ValueError('Linked canvas paths are not supported')
    original = path.read_bytes() if path.exists() else None
    data = json.loads(original) if original is not None else {'nodes': [], 'edges': []}
    if not isinstance(data, dict):
        raise ValueError('Invalid Canvas object')
    for key, generated in (('nodes', nodes), ('edges', edges)):
        items = data.get(key)
        if not isinstance(items, list) or any(not isinstance(item, dict) or not isinstance(item.get('id'), str) for item in items):
            raise ValueError('Invalid Canvas collection')
        if any(not item.get('id', '').startswith('jarvis:projection:') for item in generated):
            raise ValueError('Generated Canvas IDs must have an ownership prefix')
        data[key] = [item for item in items if not item['id'].startswith('jarvis:projection:')] + generated
    return _write_verified(path, (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode('utf-8'), original)
