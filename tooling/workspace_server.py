"""Serve the connected workspace without starting legacy autonomous workers.

Run: python -m tooling.workspace_server --root E:/.skill-registry
"""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

from tooling.http_security import LocalRequestGuard
from tooling.agentic.workspace_hub import WorkspaceHub


def make_handler(root):
    root = Path(root).resolve()
    ui = Path(__file__).resolve().parents[1] / 'ui'
    hub = WorkspaceHub(root)

    class Handler(LocalRequestGuard, BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Do not write user goals from request URLs into logs.

        def do_GET(self):
            if not self.guard_local_request():
                return
            parsed = urlsplit(self.path)
            try:
                if parsed.path == '/':
                    source = (ui / 'index.html').read_text(encoding='utf-8')
                    start = source.index('    <section class="workspace-hub"')
                    end = source.index('    <!-- Top Telemetry Cards', start)
                    body = ('<!doctype html><html lang="pt-BR"><meta charset="utf-8">'
                            '<meta name="viewport" content="width=device-width, initial-scale=1">'
                            '<title>Jarvis — Workspace conectado</title><link rel="stylesheet" href="/workspace.css">'
                            '<body class="workspace-standalone"><main><h1>Jarvis</h1>' + source[start:end]
                            + '</main><script src="/workspace.js"></script></body></html>')
                    content_type = 'text/html; charset=utf-8'
                elif parsed.path in ('/workspace.css', '/workspace.js'):
                    body = (ui / parsed.path[1:]).read_text(encoding='utf-8')
                    content_type = 'text/css' if parsed.path.endswith('.css') else 'application/javascript'
                elif parsed.path in ('/api/workspace', '/api/workspace/prepare'):
                    result = hub.prepare(parse_qs(parsed.query).get('goal', [''])[0]) if parsed.path.endswith('/prepare') else hub.snapshot()
                    body = json.dumps(result, ensure_ascii=False)
                    content_type = 'application/json; charset=utf-8'
                else:
                    self.send_error(404)
                    return
            except ValueError:
                self.send_error(400, 'Invalid goal')
                return
            payload = body.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(payload)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(payload)
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--port', type=int, default=8900)
    args = parser.parse_args()
    with ThreadingHTTPServer(('127.0.0.1', args.port), make_handler(args.root)) as server:
        print(f'Jarvis workspace: http://127.0.0.1:{server.server_port}', flush=True)
        server.serve_forever()


if __name__ == '__main__':
    main()
