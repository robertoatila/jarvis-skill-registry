"""Adversarial integration checks with isolated state and real local effects."""
import hashlib
import hmac
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tooling.agentic.config import JarvisRuntimeConfig
from tooling.agentic.memory import MemoryFabric, MemoryItem, MemoryTier, MemoryStatus
from tooling.agentic.models import Mission, TaskNode, TaskStatus, VerificationRequirement, VerificationType
from tooling.agentic.dag import ExecutionDAG
from tooling.agentic.runtime import JarvisAgenticRuntime
from tooling.agentic.cognitive_governor import AutonomyLevel
from tooling.agentic.tool_router import ToolRouter


class TestCompletion(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def item(self, ident='mem-1', content='100'):
        return MemoryItem(ident, MemoryTier.SEMANTIC, 'limit', content, 'fixture:verified')

    def test_memory_conflicting_values_survive_restart(self):
        fabric = MemoryFabric(storage_dir=self.root)
        fabric.admit(self.item())
        fabric.admit(self.item('mem-2', '200'))
        self.assertEqual(fabric.get_by_id('mem-1').status, MemoryStatus.CONFLICT_DETECTED)
        self.assertEqual(fabric.query('limit')[0], [])
        fabric.save_snapshot()
        restored = MemoryFabric(storage_dir=self.root)
        self.assertTrue(restored.load_snapshot())
        self.assertEqual(restored.get_by_id('mem-1').content, '100')
        self.assertEqual(restored.get_by_id('mem-2').content, '200')

    def test_invalid_restore_is_transactional(self):
        fabric = MemoryFabric(storage_dir=self.root)
        fabric.admit(self.item())
        (self.root/'bad.json').write_text(json.dumps({'working': [], 'semantic': [dict(self.item().to_dict(), status='invented')]}), encoding='utf-8')
        self.assertFalse(fabric.load_snapshot('bad.json'))
        self.assertEqual(fabric.get_by_id('mem-1').content, '100')
        for name in ('../outside.json', 'C:/outside.json'):
            with self.assertRaises(ValueError): fabric.save_snapshot(name)
        with self.assertRaises(ValueError): MemoryItem.from_dict(dict(self.item().to_dict(), confidence=float('nan')))

    def test_memory_budget_includes_first_item_and_archived_exclusion(self):
        fabric = MemoryFabric(storage_dir=self.root)
        item = self.item(content='x'*100)
        fabric.admit(item)
        self.assertEqual(fabric.query('limit', token_budget=1)[0], [])
        item.status = MemoryStatus.ARCHIVED
        self.assertEqual(fabric.query('limit')[0], [])

    def runtime(self):
        return JarvisAgenticRuntime(config=JarvisRuntimeConfig(registry_root=self.root))

    def mission(self, action=None, requirements=None, state=TaskStatus.PENDING):
        task = TaskNode(task_id='tsk-fixture', title='Fixture', agent_profile='Quantum-ExecutorAgent',
                        action=action, risk_level='R1', write_scopes=['output.txt'], status=state,
                        verification_requirements=requirements or [VerificationRequirement(
                            check_type=VerificationType.ARTIFACT_HASH_MATCHES, target='output.txt',
                            expected=hashlib.sha256(b'hello').hexdigest())])
        dag = ExecutionDAG(); dag.add_node(task)
        return Mission(mission_id='mis-fixture', goal='Fixture', dag=dag), task

    def test_real_write_is_journaled_before_effect_and_uses_no_model_tokens(self):
        runtime = self.runtime()
        mission, task = self.mission({'adapter':'local.write_text', 'path':'output.txt', 'content':'hello'})
        execute = runtime.local_adapter.execute
        def checked(action):
            persisted = runtime.state_store.load_mission(mission.mission_id)
            self.assertEqual(persisted.dag.nodes[task.task_id].attempts[-1].execution_state.value, 'RUNNING')
            self.assertFalse((self.root/'output.txt').exists())
            return execute(action)
        with patch.object(runtime.local_adapter, 'execute', checked):
            result = runtime.execute_goal(mission)
        self.assertEqual(result['status'], 'SUCCESS')
        self.assertEqual((self.root/'output.txt').read_text(), 'hello')
        self.assertEqual(len(task.attempts), 1)
        self.assertEqual(task.attempts[0].budget_consumed['tokens'], 0)
        model_receipts = [r for r in mission.metadata['decision_receipts'] if r['decision_type'] == 'model_routing']
        self.assertTrue(model_receipts)
        self.assertEqual(model_receipts[0]['actual_outcome'], 'NOT_INVOKED')
        self.assertEqual(model_receipts[0]['actual_tokens'], 0)
        self.assertTrue((self.root/'state/memory/memory_snapshot.json').exists())

    def test_missing_action_cannot_execute_a_verifier_command(self):
        runtime = self.runtime()
        mission, task = self.mission(requirements=[VerificationRequirement(check_type=VerificationType.COMMAND_EXIT_ZERO, target='echo forbidden')])
        with patch.object(runtime.infra, 'run_command', side_effect=AssertionError('unexpected command')):
            result = runtime.execute_goal(mission)
        self.assertEqual(result['status'], 'FAILED')
        self.assertFalse(task.execution_result['executed'])

        self.assertEqual(runtime.resume_mission(mission.mission_id)['status'], 'FAILED')
        self.assertFalse((self.root/'output.txt').exists())
        self.assertEqual(task.artifacts, [])

    def test_empty_tool_catalog_cannot_execute_an_adapter(self):
        runtime = self.runtime()
        runtime.tool_router = ToolRouter([])
        mission, task = self.mission({'adapter':'local.write_text', 'path':'output.txt', 'content':'hello'})
        self.assertEqual(runtime.execute_goal(mission)['status'], 'FAILED')
        self.assertFalse((self.root/'output.txt').exists())
        self.assertFalse(task.execution_result['executed'])
        self.assertEqual(runtime.resume_mission(mission.mission_id)['status'], 'FAILED')
        self.assertFalse((self.root/'output.txt').exists())

    def test_ambiguous_write_is_not_repeated_on_resume(self):
        runtime = self.runtime()
        mission, task = self.mission({'adapter':'local.write_text', 'path':'output.txt', 'content':'hello'}, state=TaskStatus.RUNNING)
        (self.root/'output.txt').write_text('external change', encoding='utf-8')
        runtime.state_store.save_mission(mission)
        with patch.object(runtime.local_adapter, 'execute', side_effect=AssertionError('unsafe retry')):
            result = runtime.resume_mission(mission.mission_id)
        self.assertEqual(result['status'], 'FAILED')
        self.assertEqual((self.root/'output.txt').read_text(), 'external change')

    def test_signed_approval_survives_restart_and_is_consumed_once(self):
        key = b'fixture-secret-never-used-in-production'
        def verify(operator, payload, signature):
            return operator == 'operator:alice' and hmac.compare_digest(hmac.new(key, payload, 'sha256').hexdigest(), signature)
        config = JarvisRuntimeConfig(registry_root=self.root)
        runtime = JarvisAgenticRuntime(config=config, operator_verifier=verify)
        mission, task = self.mission({'adapter':'local.write_text', 'path':'output.txt', 'content':'hello'})
        task.risk_level = 'R4'
        result = runtime.policy.evaluate_policy(runtime.agents.get(task.agent_profile), 'local.write_text', 'general',
                   'output.txt', 'R4', task.task_id, write_scopes=task.write_scopes,
                   action_context=runtime.approval_context(task, mission.mission_id))
        request = runtime.policy.get_approval_request(result.approval_id)
        signature = hmac.new(key, runtime.policy.approval_payload(request, 'operator:alice'), 'sha256').hexdigest()
        self.assertTrue(runtime.policy.grant_approval(request.approval_id, 'operator:alice', signature))
        task.action['approval_id'] = request.approval_id
        altered = dict(task.action, content='tampered')
        original = task.action
        task.action = altered
        self.assertFalse(runtime.policy.is_approval_authorized(request.approval_id, task.task_id, task.agent_profile,
                         'write', 'general', 'output.txt', runtime.approval_context(task, mission.mission_id)))
        task.action = original
        restarted = JarvisAgenticRuntime(config=config, operator_verifier=verify, autonomy_ceiling=AutonomyLevel.A5_HIGH_RISK_APPROVAL)
        self.assertEqual(restarted.execute_goal(mission)['status'], 'SUCCESS')
        self.assertTrue((self.root/'state/approvals'/f'{request.approval_id}.used').exists())
        self.assertFalse(restarted.policy.is_approval_authorized(request.approval_id, task.task_id, task.agent_profile,
                         'write', 'general', 'output.txt', restarted.approval_context(task, mission.mission_id)))
