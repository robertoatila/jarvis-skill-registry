"""Bounded single-call provider transport. No provider/key/model fallback."""
import json
import socket
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from .inference import InferenceFailure, InferenceRequest, InferenceResult
from ..models import FailureClass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise InferenceFailure(FailureClass.POLICY, "PROVIDER_REDIRECT_DENIED")


class HttpInferenceAdapter:
    def __init__(self, provider, model, api_key, *, timeout=20.0, max_response_bytes=1048576):
        catalog = json.loads((Path(__file__).resolve().parents[3] / "config" / "chat-providers.json").read_text())
        if provider not in catalog or not isinstance(model, str) or not model.strip() or not isinstance(api_key, str) or not api_key:
            raise ValueError("PROVIDER_MODEL_AND_CREDENTIAL_REQUIRED")
        if not 0 < timeout <= 60 or type(max_response_bytes) is not int or not 0 < max_response_bytes <= 4194304:
            raise ValueError("INVALID_TRANSPORT_BOUNDS")
        self.provider, self.model, self._key = provider, model, api_key
        self.spec = catalog[provider]
        self.timeout, self.max_response_bytes = timeout, max_response_bytes
        self.model_id = f"{provider}:{model}"

    def __call__(self, request: InferenceRequest) -> InferenceResult:
        policy = request.policy
        if policy.local_only or not policy.network_allowed:
            raise InferenceFailure(FailureClass.POLICY, "NETWORK_DENIED")
        if policy.allowed_models is None or self.model_id not in policy.allowed_models:
            raise InferenceFailure(FailureClass.AUTHORIZATION, "MODEL_NOT_AUTHORIZED")
        headers = {"Content-Type": "application/json"}
        if self.spec["format"] == "generate_content":
            url = self.spec["endpoint"].format(model=urllib.parse.quote(self.model.removeprefix("models/"), safe=""))
            headers["x-goog-api-key"] = self._key
            payload = {"contents": [{"parts": [{"text": request.context}]}],
                       "generationConfig": {"maxOutputTokens": request.max_output_tokens}}
        else:
            url = self.spec["endpoint"]
            headers["Authorization"] = f"Bearer {self._key}"
            payload = {"model": self.model, "messages": [{"role": "user", "content": request.context}],
                       "max_tokens": request.max_output_tokens}
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
        try:
            with urllib.request.build_opener(_NoRedirect()).open(req, timeout=self.timeout) as response:
                raw = response.read(self.max_response_bytes + 1)
            if len(raw) > self.max_response_bytes:
                raise InferenceFailure(FailureClass.MALFORMED_RESULT, "RESPONSE_TOO_LARGE")
            data = json.loads(raw)
            if self.spec["format"] == "generate_content":
                text = "".join(part.get("text", "") for part in data["candidates"][0]["content"]["parts"])
                usage = data.get("usageMetadata", {})
                prompt, completion = usage.get("promptTokenCount"), usage.get("candidatesTokenCount")
            else:
                text = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                prompt, completion = usage.get("prompt_tokens"), usage.get("completion_tokens")
            if not isinstance(text, str) or not text.strip():
                raise ValueError("EMPTY_OUTPUT")
            for count in (prompt, completion):
                if count is not None and (type(count) is not int or count < 0):
                    raise ValueError("INVALID_USAGE")
            return InferenceResult(text=text, prompt_tokens=prompt, completion_tokens=completion)
        except urllib.error.HTTPError as error:
            category = FailureClass.AUTHORIZATION if error.code in (401, 403) else (
                FailureClass.TRANSIENT if error.code == 429 or error.code >= 500 else FailureClass.PERMANENT)
            raise InferenceFailure(category, f"PROVIDER_HTTP_{error.code}") from None
        except (TimeoutError, socket.timeout):
            raise InferenceFailure(FailureClass.TIMEOUT, "PROVIDER_TIMEOUT_OUTCOME_UNKNOWN") from None
        except urllib.error.URLError as error:
            if isinstance(error.reason, (TimeoutError, socket.timeout)):
                raise InferenceFailure(FailureClass.TIMEOUT, "PROVIDER_TIMEOUT_OUTCOME_UNKNOWN") from None
            raise InferenceFailure(FailureClass.EXTERNAL_SERVICE, "PROVIDER_CONNECTION_ERROR") from None
        except (ValueError, KeyError, IndexError, TypeError, AttributeError):
            raise InferenceFailure(FailureClass.MALFORMED_RESULT, "INVALID_PROVIDER_RESPONSE") from None
