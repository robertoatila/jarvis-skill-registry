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

def validate_authorized_request(client, host, origin, port, fetch_site='', token='', expected_token=''):
    """Validates private LAN or local requests equipped with a sovereign companion token."""
    try:
        ip = ipaddress.ip_address(client)
        if ip.is_loopback:
            return validate_local_request(client, host, origin, port, fetch_site)

        # Non-loopback requests strictly require private network + matching token
        if not (ip.is_private or ip.is_link_local):
            return False

        if not token or not expected_token:
            return False

        import secrets
        if not secrets.compare_digest(str(token).strip(), str(expected_token).strip()):
            return False

        if fetch_site == 'cross-site':
            return False

        parsed = urlsplit('http://' + host)
        if (parsed.port or 80) != port:
            return False

        if origin:
            source = urlsplit(origin)
            if source.scheme not in ('http', 'https') or (source.port or 80) != port:
                return False

        return True
    except (ValueError, TypeError):
        return False

def confined_asset(root, url_path):
    # Preserve the caller's lexical root representation in the returned Path
    # (notably Windows 8.3 aliases such as RUNNER~1), while performing the
    # security decision against fully resolved canonical paths.
    lexical_root = Path(root).absolute()
    resolved_root = lexical_root.resolve()
    decoded = unquote(url_path).replace('\\', '/')
    if decoded.startswith('/') or ':' in decoded or '..' in decoded.split('/'):
        raise ValueError('Invalid static asset path')
    lexical_path = lexical_root / decoded
    resolved_path = lexical_path.resolve()
    if not resolved_path.is_relative_to(resolved_root):
        raise ValueError('Static asset escapes root')
    return lexical_path

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
        client_ip = self.client_address[0]
        host = self.headers.get('Host', '')
        origin = self.headers.get('Origin', '')
        port = self.server.server_port
        fetch_site = self.headers.get('Sec-Fetch-Site', '')

        if validate_local_request(client_ip, host, origin, port, fetch_site):
            return True

        # Check for remote companion token authorization if server allows remote
        remote_auth = getattr(self.server, 'remote_auth', None)
        if remote_auth:
            token = None
            if hasattr(self, 'path') and '?' in self.path:
                from urllib.parse import parse_qs, urlsplit
                qs = parse_qs(urlsplit(self.path).query)
                if 'token' in qs and qs['token']:
                    token = qs['token'][0]
            if not token:
                token = self.headers.get('X-Jarvis-Token')
            if not token:
                auth_hdr = self.headers.get('Authorization', '')
                if auth_hdr.startswith('Bearer '):
                    token = auth_hdr[7:].strip()
            if not token:
                cookie_hdr = self.headers.get('Cookie', '')
                for part in cookie_hdr.split(';'):
                    if '=' in part:
                        k, v = part.strip().split('=', 1)
                        if k == 'jarvis_token':
                            token = v
                            break

            expected_token = getattr(remote_auth, 'active_token', None)
            if expected_token and validate_authorized_request(
                client_ip, host, origin, port, fetch_site, token=token, expected_token=expected_token
            ):
                return True

        self.send_error(403, 'Local same-origin or authorized companion token required')
        return False
