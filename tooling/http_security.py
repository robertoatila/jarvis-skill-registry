"""Local dashboard request boundary, independent of runtime startup side effects."""
import ipaddress
import json
from pathlib import Path
from urllib.parse import urlsplit, unquote

MAX_BODY_BYTES = 1024 * 1024

def validate_local_request(client, host, origin, port, fetch_site=''):
    try:
        if not ipaddress.ip_address(client).is_loopback:
            return False
        parsed = urlsplit('http://' + host)
        if parsed.hostname not in ('localhost', '127.0.0.1', '::1') or parsed.username or parsed.password:
            return False
        if parsed.path or parsed.query or parsed.fragment or (parsed.port or 80) != port:
            return False
        if fetch_site == 'cross-site':
            return False
        if origin:
            source = urlsplit(origin)
            if source.scheme != 'http' or source.netloc != parsed.netloc or source.path or source.query or source.fragment:
                return False
        return True
    except (ValueError, TypeError):
        return False

def confined_asset(root, url_path):
    root = Path(root).resolve()
    decoded = unquote(url_path).replace('\\', '/')
    if decoded.startswith('/') or ':' in decoded or '..' in decoded.split('/'):
        raise ValueError('Invalid static asset path')
    path = (root / decoded).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Static asset escapes root')
    return path

def read_json_request(headers, stream):
    if headers.get('Transfer-Encoding'):
        raise ValueError('Transfer encoding is not supported')
    if headers.get('Content-Type','').split(';',1)[0].strip().lower() != 'application/json':
        raise ValueError('Content-Type must be application/json')
    size = int(headers.get('Content-Length','0'))
    if size <= 0 or size > MAX_BODY_BYTES:
        raise ValueError('Invalid request body size')
    raw = stream.read(size)
    if len(raw) != size:
        raise ValueError('Incomplete request body')
    body = json.loads(raw.decode('utf-8'))
    if not isinstance(body, dict):
        raise ValueError('JSON body must be an object')
    return body

class LocalRequestGuard:
    def guard_local_request(self):
        allowed = validate_local_request(self.client_address[0], self.headers.get('Host',''),
            self.headers.get('Origin',''), self.server.server_port, self.headers.get('Sec-Fetch-Site',''))
        if not allowed:
            self.send_error(403, 'Local same-origin request required')
        return allowed
