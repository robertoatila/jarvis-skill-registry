"""Independent negative cases for the September 13 reanalysis."""
import io
import unittest
import tempfile
import hashlib
import hmac
import ast
import json
import urllib.parse
import threading
import http.client
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timezone, timedelta
from pathlib import Path
from tooling.http_security import validate_local_request, confined_asset, read_json_request, LocalRequestGuard
from tooling.agentic.policy import PolicyEngine, PolicyDecision
from tooling.agentic.config import JarvisRuntimeConfig
from tooling.agentic.profiles import AgentProfile, AgentConstraints
from tooling.agentic.adapters.local import LocalActionAdapter, LocalAction, LocalActionError
from tooling.agentic.models import TaskNode, ApprovalStatus
from tooling.agentic.admission import AdmissionGate, AdmissionDecision
from tooling.agentic.context_governor import ContextCompactor

class TestReanalysisSecurity(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.policy=PolicyEngine(JarvisRuntimeConfig(registry_root=self.root))
        self.agent=AgentProfile(agent_id='test-agent',name='Fixture',domain='tests',allowed_tools=['*'],constraints=AgentConstraints(read_only=False))

    def test_operator_label_is_not_authentication(self):
        req=self.policy.evaluate_policy(self.agent,'install_package','general',risk_level='R4')
        self.assertFalse(self.policy.grant_approval(req.approval_id,'operator:alice'))

    def test_scope_prefix_sibling_is_not_authorized(self):
        result=self.policy.evaluate_policy(self.agent,'write','general','reports-other/result','R1',write_scopes=['reports'])
        self.assertEqual(result.decision,PolicyDecision.DENY)

    def test_local_adapter_name_cannot_bypass_read_only_policy(self):
        self.agent.constraints.read_only=True
        result=self.policy.evaluate_policy(self.agent,'local.write_text','general','reports/result','R1',write_scopes=['reports'])
        self.assertEqual(result.decision,PolicyDecision.DENY)

    def test_existing_file_requires_before_hash(self):
        target=self.root/'out.txt';target.write_text('original')
        with self.assertRaises(LocalActionError):
            LocalActionAdapter(self.root).execute(LocalAction('local.write_text','out.txt',content='replacement'))
        self.assertEqual(target.read_text(),'original')

    def test_authoritative_state_cannot_be_an_adapter_target(self):
        with self.assertRaises(LocalActionError):
            LocalActionAdapter(self.root).execute(LocalAction('local.write_text','state/missions/forged.json',content='{}'))

    def test_local_dashboard_rejects_foreign_origin_rebinding_and_remote_client(self):
        self.assertTrue(validate_local_request('127.0.0.1','localhost:8899','http://localhost:8899',8899))
        for client,host,origin in [('127.0.0.1','localhost:8899','https://evil.example'),('127.0.0.1','evil.example:8899',''),('192.0.2.2','localhost:8899','')]:
            self.assertFalse(validate_local_request(client,host,origin,8899))

    def test_static_assets_cannot_escape(self):
        for path in ('../secret','%2e%2e/secret','..%5csecret','C:/secret'):
            with self.assertRaises(ValueError):confined_asset(self.root,path)
        self.assertEqual(confined_asset(self.root,'icon.svg'),self.root/'icon.svg')

    def test_bad_json_never_becomes_default_action(self):
        for body in (b'[]',b'null',b'{broken',b''):
            with self.assertRaises(ValueError):read_json_request({'Content-Type':'application/json','Content-Length':str(len(body))},io.BytesIO(body))
        with self.assertRaises(ValueError):read_json_request({'Content-Type':'application/json','Content-Length':'1048577'},io.BytesIO())

    def test_signature_binds_operator_target_and_expiry(self):
        key = b'test-only-credential'
        def verify(operator, payload, signature):
            return operator == 'operator:alice' and hmac.compare_digest(hmac.new(key, payload, 'sha256').hexdigest(), signature)
        engine = PolicyEngine(JarvisRuntimeConfig(registry_root=self.root), operator_verifier=verify)
        result = engine.evaluate_policy(self.agent, 'install_package', 'general', risk_level='R4')
        request = engine.get_approval_request(result.approval_id)
        signature = hmac.new(key, engine.approval_payload(request, 'operator:alice'), 'sha256').hexdigest()
        self.assertFalse(engine.grant_approval(request.approval_id, 'operator:bob', signature))
        request.resource = 'altered-target'
        self.assertFalse(engine.grant_approval(request.approval_id, 'operator:alice', signature))
        request.resource = ''
        self.assertTrue(engine.grant_approval(request.approval_id, 'operator:alice', signature))
        self.assertFalse(engine.grant_approval(request.approval_id, 'operator:alice', signature))
        request.status = ApprovalStatus.PENDING_ACK
        request.expires_utc = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        self.assertFalse(engine.grant_approval(request.approval_id, 'operator:alice', signature))

    def test_verified_overwrite_preserves_original_backup(self):
        target = self.root / 'out.txt'
        target.write_bytes(b'original')
        adapter = LocalActionAdapter(self.root)
        result = adapter.execute(LocalAction('local.write_text', 'out.txt', content='replacement',
                    expected_before_sha256=hashlib.sha256(b'original').hexdigest()))
        self.assertTrue(result.success)
        self.assertEqual(target.read_bytes(), b'replacement')
        self.assertEqual([p.read_bytes() for p in (self.root/'backups/local-adapter').glob('*.bak')], [b'original'])
        with self.assertRaises(LocalActionError):
            adapter.execute(LocalAction('local.write_text', 'out.txt', content='stale',
                        expected_before_sha256=hashlib.sha256(b'original').hexdigest()))
        self.assertEqual(target.read_bytes(), b'replacement')

    def test_new_file_and_scope_descendant_remain_allowed(self):
        result = self.policy.evaluate_policy(self.agent, 'local.write_text', 'general', 'reports/out.txt', 'R1', write_scopes=['reports'])
        self.assertEqual(result.decision, PolicyDecision.ALLOW)
        adapter = LocalActionAdapter(self.root)
        self.assertTrue(adapter.execute(LocalAction('local.write_text', 'reports/out.txt', content='new')).success)
        self.assertEqual(adapter.execute(LocalAction('local.read_file', 'reports/out.txt')).content, 'new')

    def test_protected_paths_cannot_use_case_or_dot_aliases(self):
        for path in ('STATE/missions/x', './state/missions/x', 'state./missions/x', 'config/api_keys.json', '.env.local', 'backups/x', 'out.txt:stream'):
            with self.subTest(path=path), self.assertRaises(LocalActionError):
                LocalActionAdapter(self.root).execute(LocalAction('local.write_text', path, content='x'))

    def test_approval_flag_does_not_admit_high_risk_task(self):
        gate = AdmissionGate(policy_engine=self.policy)
        for risk, decision in [('R4', AdmissionDecision.REQUIRE_APPROVAL), ('R5', AdmissionDecision.BLOCKED)]:
            task = TaskNode(task_id='tsk-test', title='Fixture', risk_level=risk, approval_status=ApprovalStatus.APPROVED)
            result = gate.evaluate_task(task, agent_profile=self.agent)
            self.assertFalse(result.admitted)
            self.assertEqual(result.decision, decision)

    def test_actual_dashboard_methods_reject_before_dispatch(self):
        # Load only actual handler methods, avoiding module startup and private state.
        tree = ast.parse((Path(__file__).resolve().parents[1]/'tooling/jarvis_server.py').read_text(encoding='utf-8-sig'))
        handler = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'JarvisHttpHandler')
        methods = [n for n in handler.body if isinstance(n, ast.FunctionDef) and n.name in ('do_GET', 'do_POST', 'do_OPTIONS')]
        namespace = {}
        exec(compile(ast.Module(body=methods, type_ignores=[]), '<dashboard-methods>', 'exec'), namespace)
        class DeniedRequest:
            def guard_local_request(self): return False
            def __getattr__(self, name): raise AssertionError('Reached dispatch: '+name)
        self.assertEqual(len(methods), 3)
        for method in methods:
            namespace[method.name](DeniedRequest())

    def test_compaction_retains_commented_constraints_and_late_decisions(self):
        compactor = ContextCompactor()
        critical = ['# risk: unresolved', '// UNCERTAINTY: unknown', '# decision: defer', '# authority: read only', '# constraint: no network']
        cleaned, decisions, uncertainties = compactor.compact_stage_1_scrub('ordinary\n'+'\n'.join(critical))
        truncated = compactor.compact_stage_2_truncate(cleaned, max_items=1)
        summary = compactor.compact_stage_3_synthesize(truncated, decisions, uncertainties)
        for line in critical:
            self.assertIn(line, truncated)
            self.assertIn(line, summary)
        for stage in ('STRUCTURED_ATTEMPT', 'SUMMARY', 'REFERENCE'):
            result = compactor.compact({'authority': 'read-only', 'pending_verification': ['hash'], 'write_scopes': []}, stage)
            self.assertEqual(result['authority'], 'read-only')
            self.assertEqual(result['pending_verification'], ['hash'])

    def test_real_http_requests_enforce_origin_json_and_asset_boundaries(self):
        tree = ast.parse((Path(__file__).resolve().parents[1]/'tooling/jarvis_server.py').read_text(encoding='utf-8-sig'))
        handler = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'JarvisHttpHandler')
        names = {
            'do_GET', 'do_POST', 'do_OPTIONS', 'end_headers', 'send_json', 'read_json_body',
            '_handle_runtime_observability_get', '_valid_runtime_mission_id',
        }
        handler.body = [n for n in handler.body if isinstance(n, ast.FunctionDef) and n.name in names]
        namespace = {'LocalRequestGuard': LocalRequestGuard, 'BaseHTTPRequestHandler': BaseHTTPRequestHandler,
                     'urllib': urllib, 'json': json, 'confined_asset': confined_asset,
                     'read_json_request': read_json_request, 'UI_DIR': self.root}
        exec(compile(ast.Module(body=[handler], type_ignores=[]), '<actual-http-handler>', 'exec'), namespace)
        cls = namespace['JarvisHttpHandler']
        cls.log_message = lambda *args: None
        server = HTTPServer(('127.0.0.1', 0), cls)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            def request(method, path, body=None, headers=None):
                conn = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=3)
                try:
                    conn.request(method, path, body=body, headers=headers or {})
                    response = conn.getresponse()
                    return response.status, dict(response.getheaders()), response.read()
                finally: conn.close()
            status, headers, body = request('GET', '/api/agentic/status')
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)['status'], 'NOT_VERIFIED')
            self.assertNotIn('Access-Control-Allow-Origin', headers)
            self.assertEqual(request('GET', '/api/agentic/status', headers={'Origin':'https://foreign.invalid'})[0], 403)
            self.assertEqual(request('GET', '/assets/%2e%2e/private.json')[0], 403)
            self.assertEqual(request('POST', '/api/agentic/execute', b'[]', {'Content-Type':'application/json'})[0], 400)
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=3)
