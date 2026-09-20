"""
n8n.py // J.A.R.V.I.S. n8n Automation & Webhook Bridge Adapter
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
Supports:
- Inbound HMAC-SHA256 verified webhook triggers from n8n
- Outbound event dispatching (MISSION_TRIGGER, MISSION_COMPLETED, ALERT_DISPATCH)
- Programmatic n8n Workflow JSON synthesis for J.A.R.V.I.S. integration nodes
"""

from __future__ import annotations
import hmac
import hashlib
import json
import os
import secrets
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any
from datetime import datetime, timezone

from ..models import Mission, MissionStatus, MissionBudget, TaskNode


class N8nAdapter:
    """
    Bi-directional bridge between n8n workflows and J.A.R.V.I.S. Autonomous Runtime.
    """

    LEGACY_DEFAULT_SECRET = "sovereign-jarvis-n8n-secret"

    def __init__(self, webhook_secret: Optional[str] = None, replay_window_seconds: int = 300):
        secret = (webhook_secret or os.environ.get("JARVIS_N8N_WEBHOOK_SECRET", "")).strip()
        if len(secret) < 16 or secret == self.LEGACY_DEFAULT_SECRET:
            raise ValueError(
                "JARVIS_N8N_WEBHOOK_SECRET must be explicit, at least 16 characters, "
                "and different from the legacy default."
            )
        if replay_window_seconds < 30 or replay_window_seconds > 3600:
            raise ValueError("replay_window_seconds must be between 30 and 3600 seconds")
        self.webhook_secret = secret
        self.replay_window_seconds = replay_window_seconds
        self._seen_nonces: Dict[str, float] = {}

    def sign_payload(self, payload_dict: Dict[str, Any]) -> str:
        """Computes HMAC-SHA256 hex digest for outbound payload."""
        data_str = json.dumps(payload_dict, sort_keys=True, ensure_ascii=False)
        return hmac.new(
            self.webhook_secret.encode("utf-8"),
            data_str.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    def verify_signature(self, payload_dict: Dict[str, Any], signature_hex: str) -> bool:
        """Verifies HMAC-SHA256 signature against webhook secret in constant time."""
        expected = self.sign_payload(payload_dict)
        return hmac.compare_digest(expected, signature_hex)

    def sign_event(self, event_data: Dict[str, Any]) -> str:
        """Signs security-relevant envelope fields, not only the nested payload."""
        return self.sign_payload(self._signature_envelope(event_data))

    def verify_event_signature(self, event_data: Dict[str, Any], signature_hex: str) -> bool:
        if not signature_hex:
            return False
        expected = self.sign_event(event_data)
        return hmac.compare_digest(expected, signature_hex)

    def _signature_envelope(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "event_type": event_data.get("event_type"),
            "mission_id": event_data.get("mission_id"),
            "timestamp_utc": event_data.get("timestamp_utc"),
            "nonce": event_data.get("nonce"),
            "payload": event_data.get("payload", {}),
        }

    def _validate_fresh_nonce(self, event_data: Dict[str, Any]) -> str:
        raw_timestamp = event_data.get("timestamp_utc")
        nonce = event_data.get("nonce")
        if not isinstance(raw_timestamp, str) or not raw_timestamp.strip():
            raise PermissionError("Missing timestamp_utc on n8n inbound webhook.")
        if not isinstance(nonce, str) or not (16 <= len(nonce) <= 128):
            raise PermissionError("Missing or invalid nonce on n8n inbound webhook.")

        try:
            timestamp = datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))
        except ValueError as exc:
            raise PermissionError("Invalid timestamp_utc on n8n inbound webhook.") from exc
        if timestamp.tzinfo is None:
            raise PermissionError("timestamp_utc must include timezone information.")

        now = datetime.now(timezone.utc)
        age_seconds = abs((now - timestamp.astimezone(timezone.utc)).total_seconds())
        if age_seconds > self.replay_window_seconds:
            raise PermissionError("Stale n8n inbound webhook timestamp.")

        cutoff = now.timestamp() - self.replay_window_seconds
        self._seen_nonces = {
            key: seen_at for key, seen_at in self._seen_nonces.items() if seen_at >= cutoff
        }
        if nonce in self._seen_nonces:
            raise PermissionError("Replay detected for n8n inbound webhook nonce.")
        return nonce

    def parse_inbound_trigger(self, event_data: Dict[str, Any], signature_hex: Optional[str] = None) -> Mission:
        """
        Parses an incoming n8n webhook event into an executable J.A.R.V.I.S. Mission.
        Signature, timestamp and nonce are mandatory. Unsigned or replayed triggers fail closed.
        """
        if not signature_hex:
            raise PermissionError("Missing HMAC-SHA256 signature on n8n inbound webhook.")
        if not self.verify_event_signature(event_data, signature_hex):
            raise PermissionError("Invalid HMAC-SHA256 signature on n8n inbound webhook.")

        nonce = self._validate_fresh_nonce(event_data)
        self._seen_nonces[nonce] = datetime.now(timezone.utc).timestamp()

        payload = event_data.get("payload", {})
        goal_text = payload.get("goal") or event_data.get("goal") or "Autonomous Task via n8n"
        mission_id = event_data.get("mission_id") or f"MIS-n8n-{int(datetime.now(timezone.utc).timestamp())}"

        budget = MissionBudget(
            max_iterations=payload.get("max_iterations", 10),
            max_token_budget=payload.get("token_budget", 50_000)
        )

        return Mission(
            mission_id=mission_id,
            goal=goal_text,
            status=MissionStatus.PENDING,
            budget=budget,
            metadata={"origin": "n8n_webhook", "event_type": event_data.get("event_type", "MISSION_TRIGGER")}
        )

    def build_outbound_notification(
        self,
        event_type: str,
        mission_id: str,
        status: str,
        goal: str,
        evidence: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Builds an authenticated outbound event with freshness and replay fields."""
        payload = {
            "goal": goal,
            "status": status,
            "evidence": evidence or {}
        }
        event = {
            "event_type": event_type,
            "mission_id": mission_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "nonce": secrets.token_hex(16),
            "payload": payload
        }
        event["signature_sha256"] = self.sign_event(event)
        return event

    def generate_workflow_template(
        self,
        workflow_name: str = "JARVIS Autonomous Pipeline",
        jarvis_api_url: str = "http://localhost:8899"
    ) -> Dict[str, Any]:
        """Generates a valid, copy-paste ready n8n Workflow JSON connecting to J.A.R.V.I.S."""
        return {
            "name": workflow_name,
            "nodes": [
                {
                    "parameters": {
                        "httpMethod": "POST",
                        "path": "jarvis-trigger",
                        "responseMode": "onReceived"
                    },
                    "name": "Webhook Trigger",
                    "type": "n8n-nodes-base.webhook",
                    "typeVersion": 1,
                    "position": [250, 300]
                },
                {
                    "parameters": {
                        "url": f"{jarvis_api_url}/api/quantum-agents/execute",
                        "method": "POST",
                        "sendBody": True,
                        "bodyParameters": {
                            "parameters": [
                                {"name": "agent_id", "value": "Quantum-AuditAgent"},
                                {"name": "task", "value": "Auditoria de Integridade via n8n"}
                            ]
                        }
                    },
                    "name": "J.A.R.V.I.S. API Dispatcher",
                    "type": "n8n-nodes-base.httpRequest",
                    "typeVersion": 4.1,
                    "position": [450, 300]
                }
            ],
            "connections": {
                "Webhook Trigger": {
                    "main": [
                        [{"node": "J.A.R.V.I.S. API Dispatcher", "type": "main", "index": 0}]
                    ]
                }
            }
        }
