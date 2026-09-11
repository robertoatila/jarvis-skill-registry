"""
test_agentic_composite.py // Unit and Integration Tests for Phase 04 (Composite Skills + Dependency Graph)
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
"""

import unittest
import tempfile
import json
from pathlib import Path

from tooling.agentic.composite import (
    CompositeSkill,
    SubSkillReference,
    SkillDependencyGraph,
    ProgressiveDisclosureReader,
    SKILLS_DIR
)
from tooling.agentic.dag import CycleDetectedError


class TestCompositeSkills(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.skills_dir = Path(self.tmp.name) / "skills"
        skill = self.skills_dir / "security-research-audit"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: security-research-audit\ndescription: Audits software components\n---\n# Golden rules\nLocal test fixture only.\n", encoding="utf-8")

    def test_composite_skill_dag_expansion(self):
        comp = CompositeSkill(
            composite_id="sec-audit-pipeline",
            name="Security Audit Pipeline",
            sub_skills=[
                SubSkillReference(skill_id="security-research-audit", alias="audit", write_scopes=["reports/sec.json"]),
                SubSkillReference(skill_id="comprehensive-code-review", alias="review", read_scopes=["reports/sec.json"]),
                SubSkillReference(skill_id="bash-defensive-patterns", alias="remediate", write_scopes=["scripts/"])
            ],
            dependency_graph=[
                ("audit", "review"),
                ("review", "remediate")
            ]
        )

        dag = comp.expand_to_dag(task_prefix="p1")
        self.assertEqual(len(dag.nodes), 3)
        self.assertEqual(dag.topological_sort(), ["p1_audit", "p1_review", "p1_remediate"])
        self.assertEqual(dag.nodes["p1_audit"].write_scopes, ["reports/sec.json"])
        self.assertEqual(dag.nodes["p1_review"].read_scopes, ["reports/sec.json"])

    def test_skill_dependency_graph_transitive_resolution(self):
        graph = SkillDependencyGraph()
        # skill-C requires skill-B, skill-B requires skill-A
        graph.register_dependency("skill-C", "skill-B")
        graph.register_dependency("skill-B", "skill-A")

        # Resolving skill-C must yield [skill-A, skill-B, skill-C]
        resolved = graph.resolve_transitive_dependencies(["skill-C"])
        self.assertEqual(resolved, ["skill-A", "skill-B", "skill-C"])

    def test_skill_dependency_cycle_detection(self):
        graph = SkillDependencyGraph()
        graph.register_dependency("A", "B")
        graph.register_dependency("B", "C")

        with self.assertRaises(CycleDetectedError) as ctx:
            graph.register_dependency("C", "A")

        self.assertIn("A", ctx.exception.cycle_path)

    def test_progressive_disclosure_levels(self):
        # Level 0
        l0 = ProgressiveDisclosureReader.read_level_0("security-research-audit", self.skills_dir)
        self.assertTrue(l0["found"])
        self.assertEqual(l0["disclosure_level"], 0)
        self.assertNotIn("full_instructions", l0)
        self.assertIn("Audits software components", l0["description"])

        # Level 1
        l1 = ProgressiveDisclosureReader.read_level_1("security-research-audit", self.skills_dir)
        self.assertEqual(l1["disclosure_level"], 1)
        self.assertNotIn("full_instructions", l1)
        self.assertIn("has_scripts", l1)

        # Level 2
        l2 = ProgressiveDisclosureReader.read_level_2("security-research-audit", self.skills_dir)
        self.assertEqual(l2["disclosure_level"], 2)
        self.assertIn("full_instructions", l2)
        self.assertIn("Golden rules", l2["full_instructions"])

    def test_bad_aliases_and_unknown_endpoints_are_rejected(self):
        for subs, edges in (([SubSkillReference("a", alias="same"), SubSkillReference("b", alias="same")], []),
                            ([SubSkillReference("a")], [("a", "missing")])):
            with self.assertRaises(ValueError):
                CompositeSkill("c", "Composite", sub_skills=subs, dependency_graph=edges)

    def test_rejected_skill_cycle_preserves_previous_graph(self):
        graph = SkillDependencyGraph()
        graph.register_dependency("B", "A")
        with self.assertRaises(CycleDetectedError):
            graph.register_dependency("A", "B")
        self.assertEqual(graph.resolve_transitive_dependencies(["B"]), ["A", "B"])

    def test_composite_restore_is_deterministic_and_does_not_alias_scopes(self):
        comp = CompositeSkill("c", "Composite", sub_skills=[SubSkillReference("b", write_scopes=["out"]), SubSkillReference("a")], dependency_graph=[("a", "b")])
        target = Path(self.tmp.name) / "composite.json"
        comp.save(target)
        restored = CompositeSkill.load(target)
        self.assertEqual(comp.to_dict(), restored.to_dict())
        dag = comp.expand_to_dag()
        dag.nodes["b"].write_scopes.append("other")
        self.assertEqual(comp.sub_skills[0].write_scopes, ["out"])
        data = json.loads(target.read_text()); data["schema_version"] = "99"
        target.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(ValueError):
            CompositeSkill.load(target)

    def test_disclosure_rejects_traversal_before_reading(self):
        for invalid in ("../outside", "..", "a/b", "a\\b", "C:\\secret", ".", ""):
            for reader in (ProgressiveDisclosureReader.read_level_0, ProgressiveDisclosureReader.read_level_1, ProgressiveDisclosureReader.read_level_2):
                with self.subTest(invalid=invalid, reader=reader.__name__), self.assertRaises(ValueError):
                    reader(invalid, self.skills_dir)

    def test_disclosure_stops_at_end_of_frontmatter(self):
        from unittest.mock import patch
        import io
        class MetadataOnly(io.StringIO):
            def readline(self, *args):
                if self.tell() == len("---\nname: fixture\n---\n"):
                    raise AssertionError("Body was read during catalog discovery")
                return super().readline(*args)
        with patch("builtins.open", return_value=MetadataOnly("---\nname: fixture\n---\nDO NOT READ")):
            result = ProgressiveDisclosureReader.read_level_0("security-research-audit", self.skills_dir)
        self.assertTrue(result["found"])


if __name__ == "__main__":
    unittest.main()
