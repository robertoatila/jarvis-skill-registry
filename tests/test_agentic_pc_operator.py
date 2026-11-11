from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest import mock

from tooling.agentic.pc_operator import JarvisPCOperator


class TestJarvisPCOperator(unittest.TestCase):
    def setUp(self):
        self.operator = JarvisPCOperator()

    def test_tools_schema_contains_core_capabilities(self):
        schema = self.operator.tools_schema
        tool_names = [t["function"]["name"] for t in schema]
        self.assertIn("run_powershell", tool_names)
        self.assertIn("query_arsenal", tool_names)
        self.assertIn("get_pc_telemetry", tool_names)
        self.assertIn("read_pc_file", tool_names)
        self.assertIn("write_pc_file", tool_names)
        self.assertIn("system_control", tool_names)
        self.assertIn("dispatch_squad_agent", tool_names)

    def test_execute_read_and_write_file(self):
        test_file = Path("state/test_agentic_scratch.txt")
        try:
            write_res = self.operator.execute_tool("write_pc_file", {"path": str(test_file), "content": "J.A.R.V.I.S. Sovereign Memory Test"})
            self.assertIn("gravado com sucesso", write_res)

            read_res = self.operator.execute_tool("read_pc_file", {"path": str(test_file)})
            self.assertIn("J.A.R.V.I.S. Sovereign Memory Test", read_res)
        finally:
            if test_file.exists():
                test_file.unlink()

    def test_execute_telemetry_returns_data(self):
        res = self.operator.execute_tool("get_pc_telemetry", {"detailed": False})
        data = json.loads(res)
        self.assertTrue(isinstance(data, dict))

    def test_execute_arsenal_query_returns_json(self):
        res = self.operator.execute_tool("query_arsenal", {"topic": "agent", "limit": 2})
        data = json.loads(res)
        self.assertIn("topic", data)

    def test_dispatch_squad_agent_resolves_profile(self):
        res = self.operator.execute_tool("dispatch_squad_agent", {
            "agent_id": "Quantum-SWEOrchestrator",
            "mission": "Analisar integridade do repositório"
        })
        data = json.loads(res)
        self.assertIn(data.get("status"), ["MISSION_SCHEDULED", "AGENT_NOT_FOUND"])

    def test_react_turn_produces_completed_result_with_mock(self):
        mock_msg = {
            "role": "assistant",
            "content": "J.A.R.V.I.S. operacional, senhor Roberto."
        }
        with mock.patch.object(self.operator, "_call_llm_with_tools", return_value={"success": True, "message": mock_msg}):
            res = self.operator.run_agentic_turn("Olá Jarvis")
            self.assertEqual(res["status"], "COMPLETED")
            self.assertEqual(res["reply"], "J.A.R.V.I.S. operacional, senhor Roberto.")


if __name__ == "__main__":
    unittest.main()
