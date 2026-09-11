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
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any
from datetime import datetime, timezone

from ..models import Mission, MissionStatus, MissionBudget, TaskNode


class N8nAdapter:
    """
    Bi-directional bridge between n8n workflows and J.A.R.V.I.S. Autonomous Runtime.
    """

    def __init__(self, webhook_secret: str = "sovereign-jarvis-n8n-secret"):
        self.webhook_secret = webhook_secret

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

    def parse_inbound_trigger(self, event_data: Dict[str, Any], signature_hex: Optional[str] = None) -> Mission:
        """
        Parses an incoming n8n webhook event into an executable J.A.R.V.I.S. Mission.
        Enforces signature check if provided.
        """
        payload = event_data.get("payload", {})
        if signature_hex:
            if not self.verify_signature(payload, signature_hex):
                raise PermissionError("Invalid HMAC-SHA256 signature on n8n inbound webhook.")

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
        """Builds a verified, schema-compliant outbound event for n8n."""
        payload = {
            "goal": goal,
            "status": status,
            "evidence": evidence or {}
        }
        sig = self.sign_payload(payload)

        return {
            "event_type": event_type,
            "mission_id": mission_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "signature_sha256": sig,
            "payload": payload
        }

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
