"""No live provider traffic: HTTP and server boundary fixtures."""
import ast
import hashlib
import time
import json
import os
import unittest
import urllib.error
from types import SimpleNamespace, ModuleType
from pathlib import Path
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from unittest.mock import Mock, patch

from tooling.agentic.adapters.http_inference import HttpInferenceAdapter, _NoRedirect
from tooling.agentic.adapters.inference import InferenceRequest, InferenceFailure
from tooling.agentic.model_router import InferencePolicy
from tooling.agentic.models import FailureClass

# Load the actual handler class without running unrelated module-level engines,
# which synchronize a user-owned Vault on import.
server = ModuleType("isolated_chat_handler")
try:
    from tooling.http_security import LocalRequestGuard
except ImportError:
    class LocalRequestGuard: pass

server.__dict__.update(os=os, json=json, time=time, hashlib=hashlib, urllib=__import__("urllib"),
    datetime=datetime, timezone=timezone, BaseHTTPRequestHandler=BaseHTTPRequestHandler,
    LocalRequestGuard=LocalRequestGuard,
    get_configured_keys=Mock(), MEMORY_ENGINE=Mock(), NICHE_DISPATCHER=Mock(), live_github_search_api=Mock())
source = Path(__file__).resolve().parents[1] / "tooling" / "jarvis_server.py"
tree = ast.parse(source.read_text(encoding="utf-8"))
chat_boundary_node = next(
    node
    for node in tree.body
    if isinstance(node, ast.FunctionDef) and node.name == "execute_authorized_chat"
)
handler_node = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "JarvisHttpHandler")
exec(
    compile(
        ast.Module(body=[chat_boundary_node, handler_node], type_ignores=[]),
        str(source),
        "exec",
    ),
    server.__dict__,
)
JarvisHttpHandler = server.JarvisHttpHandler


class TestHttpInference(unittest.TestCase):
    def request(self, provider="openai", policy=None):
        return InferenceRequest("mission", "task", "agent", "session", "context",
            policy or InferencePolicy(local_only=False, network_allowed=True,
                                      allowed_models=(f"{provider}:chosen",)), 32)

    def response(self, payload):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = json.dumps(payload).encode()
        return response

    def test_local_only_denies_before_network(self):
        with patch("urllib.request.build_opener") as opener:
            with self.assertRaises(InferenceFailure) as raised:
                HttpInferenceAdapter("openai", "chosen", "credential")(self.request(policy=InferencePolicy()))
        self.assertEqual(raised.exception.failure_class, FailureClass.POLICY)
        opener.assert_not_called()

    def test_single_call_usage_and_explicit_model(self):
        opener = Mock()
        opener.open.return_value = self.response({"choices": [{"message": {"content": "answer"}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 3}})
        with patch("urllib.request.build_opener", return_value=opener):
            result = HttpInferenceAdapter("openai", "chosen", "credential")(self.request())
        self.assertEqual((result.prompt_tokens, result.completion_tokens), (12, 3))
        self.assertIsNone(result.confidence)
        self.assertEqual(result.evidence_refs, ())
        self.assertEqual(opener.open.call_count, 1)
        request = opener.open.call_args.args[0]
        self.assertEqual(json.loads(request.data)["model"], "chosen")
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 20)
        opener.open.return_value.read.assert_called_once_with(1048577)

    def test_gemini_key_is_header_and_usage_optional(self):
        opener = Mock()
        opener.open.return_value = self.response({"candidates": [{"content": {"parts": [{"text": "answer"}]}}]})
        with patch("urllib.request.build_opener", return_value=opener):
            result = HttpInferenceAdapter("gemini", "chosen", "credential")(self.request("gemini"))
        request = opener.open.call_args.args[0]
        self.assertNotIn("credential", request.full_url)
        self.assertEqual(request.get_header("X-goog-api-key"), "credential")
        self.assertIsNone(result.prompt_tokens)

    def test_http_auth_timeout_and_transient_do_not_retry(self):
        errors = [(urllib.error.HTTPError("https://provider", 401, "private", {}, None), FailureClass.AUTHORIZATION),
                  (urllib.error.HTTPError("https://provider", 429, "private", {}, None), FailureClass.TRANSIENT),
                  (TimeoutError("private"), FailureClass.TIMEOUT),
                  (urllib.error.URLError(TimeoutError("private")), FailureClass.TIMEOUT)]
        for error, category in errors:
            with self.subTest(category=category):
                opener = Mock()
                opener.open.side_effect = error
                with patch("urllib.request.build_opener", return_value=opener):
                    with self.assertRaises(InferenceFailure) as raised:
                        HttpInferenceAdapter("openai", "chosen", "credential")(self.request())
                self.assertEqual(raised.exception.failure_class, category)
                self.assertNotIn("private", str(raised.exception))
                self.assertEqual(opener.open.call_count, 1)

    def test_invalid_result_and_oversize_are_typed(self):
        for payload, limit in (({}, 100), ({"large": "x" * 200}, 20),
                               ({"choices": [{"message": {"content": "ok"}}], "usage": {"prompt_tokens": -1}}, 1000)):
            opener = Mock()
            opener.open.return_value = self.response(payload)
            with patch("urllib.request.build_opener", return_value=opener):
                with self.assertRaises(InferenceFailure) as raised:
                    HttpInferenceAdapter("openai", "chosen", "credential", max_response_bytes=limit)(self.request())
            self.assertEqual(raised.exception.failure_class, FailureClass.MALFORMED_RESULT)

    def test_redirect_is_denied(self):
        with self.assertRaises(InferenceFailure) as raised:
            _NoRedirect().redirect_request(None, None, 302, "redirect", {}, "https://other-host")
        self.assertEqual(raised.exception.failure_class, FailureClass.POLICY)


class TestServerChatBoundary(unittest.TestCase):
    def setUp(self):
        self.handler = SimpleNamespace(headers={"Authorization": "Bearer test-chat-grant"})
        self.environment = {"JARVIS_CHAT_ALLOW_CLOUD": "1", "JARVIS_CHAT_TOKEN": "test-chat-grant",
                            "JARVIS_CHAT_PROVIDERS": "openai"}

    def forward(self, provider="openai", model="chosen", key="", message="private prompt"):
        return JarvisHttpHandler.forward_external_llm(self.handler, provider, model, key, message)

    def test_default_denial_precedes_credentials_and_network(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(server, "get_configured_keys") as keys, \
             patch("urllib.request.build_opener") as opener:
            result = self.forward()
        self.assertEqual(result["trace"]["reason"], "CLOUD_DISABLED")
        keys.assert_not_called()
        opener.assert_not_called()

    def test_post_route_no_longer_memorizes_or_dispatches_before_permission(self):
        handler = object.__new__(JarvisHttpHandler)
        handler.client_address = ("127.0.0.1", 8899)
        handler.guard_local_request = Mock(return_value=True)
        handler.path = "/api/chat"
        handler.headers = {"Host": "127.0.0.1:8899"}
        handler.read_json_body = Mock(return_value={"message": "private", "provider": "openai", "model": "chosen"})
        handler.send_json = Mock()
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(server.MEMORY_ENGINE, "detect_and_memorize", side_effect=AssertionError("memorized")), \
             patch.object(server, "NICHE_DISPATCHER") as dispatcher:
            handler.do_POST()
        self.assertEqual(handler.send_json.call_args.args[0]["trace"]["reason"], "CLOUD_DISABLED")
        dispatcher.dispatch.assert_not_called()

    def test_auth_provider_and_model_constraints(self):
        for auth, provider, model, expected in (("", "openai", "chosen", "CHAT_AUTHORIZATION_REQUIRED"),
            ("Bearer test-chat-grant", "groq", "chosen", "PROVIDER_NOT_AUTHORIZED"),
            ("Bearer test-chat-grant", "openai", "", "EXPLICIT_MODEL_REQUIRED")):
            self.handler.headers["Authorization"] = auth
            with patch.dict(os.environ, self.environment, clear=True), \
                 patch.object(server, "get_configured_keys") as keys:
                result = self.forward(provider, model)
            self.assertEqual(result["trace"]["reason"], expected)
            keys.assert_not_called()

    def test_authorized_request_keeps_json_shape_and_unverified_status(self):
        opener = Mock()
        opener.open.return_value = TestHttpInference().response({"choices": [{"message": {"content": "reply"}}]})
        with patch.dict(os.environ, self.environment, clear=True), \
             patch.object(server, "get_configured_keys", return_value={"openai": "right-key", "groq": "wrong-key"}), \
             patch("urllib.request.build_opener", return_value=opener), \
             patch.object(server, "live_github_search_api", side_effect=AssertionError("search")), \
             patch.object(server.MEMORY_ENGINE, "get_prompt_context", side_effect=AssertionError("private memory")):
            result = self.forward()
        self.assertEqual(result["status"], "UNVERIFIED")
        self.assertEqual(result["reply"], "reply")
        self.assertFalse(result["live_search"])
        self.assertEqual(opener.open.call_args.args[0].get_header("Authorization"), "Bearer right-key")
        self.assertNotIn("private prompt", str(result["trace"]))
        self.assertNotIn("right-key", str(result))

    def test_provider_failure_never_switches_credentials(self):
        opener = Mock()
        opener.open.side_effect = TimeoutError()
        with patch.dict(os.environ, self.environment, clear=True), \
             patch.object(server, "get_configured_keys", return_value={"openai": "one", "groq": "two"}), \
             patch("urllib.request.build_opener", return_value=opener):
            result = self.forward()
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["trace"]["failure_class"], "TIMEOUT")
        self.assertEqual(result["trace"]["attempts"], 1)
        self.assertEqual(opener.open.call_count, 1)


if __name__ == "__main__":
    unittest.main()
