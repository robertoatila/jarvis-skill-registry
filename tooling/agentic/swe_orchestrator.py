"""
swe_orchestrator.py // J.A.R.V.I.S. Software Engineering Multi-Agent Orchestrator
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
Stages supplied source and performs local syntax and placeholder checks.
These checks do not certify functionality, security, or production readiness.
"""

from __future__ import annotations
import ast
import json
import os
import py_compile
import re
import tempfile
import hashlib
import uuid
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple, Any
from datetime import datetime, timezone

from .models import TaskNode, TaskStatus, VerificationRequirement, VerificationType, VerificationStatus, Mission
from .dag import ExecutionDAG, save_json_atomic
from .scheduler import WaveScheduler
from .profiles import AgentProfileRegistry


REGISTRY_ROOT = Path(__file__).resolve().parents[2]
STAGING_DIR = REGISTRY_ROOT / "staging" / "orchestration"


@dataclass
class SWEOrchestrationResult:
    target: str
    status: str  # PASS, FAIL
    composite_score: float
    total_stages: int
    passed_stages: int
    artifacts: List[str]
    evidence: Dict[str, Any]
    report_markdown: str


class SoftwareEngineeringOrchestrator:
    """
    Local source-validation adapter with staged artifacts and explicit evidence.
    Agent profile names annotate responsibilities; no model call is implied.
    """

    def __init__(self, registry_root: Path = REGISTRY_ROOT):
        self.registry_root = Path(registry_root).resolve()
        self.staging_dir = self.registry_root / "staging" / "orchestration"
        if not self.staging_dir.resolve().is_relative_to(self.registry_root):
            raise ValueError("Staging directory escapes registry root")
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        self.profile_registry = AgentProfileRegistry()

    def inspect_code_integrity(self, file_path: Path) -> Dict[str, Any]:
        """Performs static AST inspection to detect syntax errors, placeholders, and dangerous patterns."""
        if not file_path.exists():
            return {"valid": False, "error": f"File not found: {file_path}", "score": 0.0}

        content = file_path.read_text(encoding="utf-8", errors="replace")

        # 1. Check for prohibited placeholder patterns
        prohibited = [
            (r"TODO:\s*implement", "Unimplemented TODO placeholder found"),
            (r"raise\s+NotImplementedError", "NotImplementedError placeholder found"),
            (r"mock_\w+\s*=\s*True", "Production mock flag detected")
        ]
        violations = []
        for pat, desc in prohibited:
            if re.search(pat, content, re.IGNORECASE):
                violations.append(desc)

        # 2. AST parsing if python
        ast_valid = True
        ast_error = None
        compilation = {"status": "NOT_EXECUTED", "reason": "Not Python source"}
        if file_path.suffix == ".py":
            try:
                ast.parse(content, filename=str(file_path))
            except SyntaxError as se:
                ast_valid = False
                ast_error = f"SyntaxError at line {se.lineno}: {se.msg}"
            if ast_valid:
                try:
                    compile(content, str(file_path), "exec")
                    compilation = {"status": "PASS", "producer": "python.compile", "source_sha256": hashlib.sha256(file_path.read_bytes()).hexdigest()}
                except (SyntaxError, ValueError) as exc:
                    ast_valid = False
                    ast_error = f"CompilationError: {exc}"
                    compilation = {"status": "FAIL", "error": str(exc)}

        # 3. Score calculation
        base_score = 100.0
        if not ast_valid:
            base_score -= 50.0
        base_score -= (len(violations) * 20.0)
        base_score = max(0.0, base_score)

        return {
            "valid": ast_valid and (len(violations) == 0),
            "ast_valid": ast_valid,
            "ast_error": ast_error,
            "violations": violations,
            "score": round(base_score, 2),
            "bytes": len(content),
            "lines": len(content.splitlines())
            ,"compilation": compilation,
            "scope": "python_syntax_and_placeholder_scan",
            "functional_tests": "NOT_EXECUTED",
            "security_certification": "NOT_EXECUTED",
            "typecheck": "NOT_EXECUTED"
        }

    def execute_pipeline(self, target_slug: str, source_code: str) -> SWEOrchestrationResult:
        """
        Executes a 4-stage verifiable SWE pipeline:
        Stage 1: Architecture Planning
        Stage 2: Synthesis & Staging
        Stage 3: Automated Compilation & Integrity Testing
        Stage 4: Security & Governance Audit
        """
        now_utc = datetime.now(timezone.utc).isoformat()
        if not isinstance(target_slug, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}", target_slug):
            raise ValueError("Target must be a nonempty local slug; supply source separately")
        if not isinstance(source_code, str) or not source_code.strip():
            raise ValueError("Explicit nonempty source_code is required")
        clean_slug = target_slug
        target_dir = self.staging_dir / (clean_slug + "-" + uuid.uuid4().hex)
        target_dir.mkdir(parents=True, exist_ok=False)

        target_file = target_dir / "implementation.py"
        target_file.write_text(source_code, encoding="utf-8")

        # 1. Build DAG
        dag = ExecutionDAG()

        # Node 1: Plan
        n1 = TaskNode(
            task_id=f"{clean_slug}_plan",
            title="Architecture & Interface Planning",
            agent_profile="Quantum-SynthesisAgent",
            required_skills=["ai-engineer"],
            write_scopes=[str(target_dir / "plan.json")]
        )
        # Node 2: Synthesize
        n2 = TaskNode(
            task_id=f"{clean_slug}_synthesize",
            title="Synthesis & Implementation",
            agent_profile="Quantum-SynthesisAgent",
            required_skills=["ai-engineer"],
            dependencies=[n1.task_id],
            write_scopes=[str(target_file)]
        )
        # Node 3: Test
        n3 = TaskNode(
            task_id=f"{clean_slug}_test",
            title="Automated AST & Compilation Test",
            agent_profile="Quantum-AuditAgent",
            required_skills=["comprehensive-code-review"],
            dependencies=[n2.task_id],
            verification_requirements=[
                VerificationRequirement(check_type=VerificationType.FILE_EXISTS, target=str(target_file))
            ]
        )
        # Node 4: Audit
        n4 = TaskNode(
            task_id=f"{clean_slug}_audit",
            title="Security & Governance Audit",
            agent_profile="Quantum-AuditAgent",
            required_skills=["security-research-audit"],
            dependencies=[n3.task_id]
        )

        for n in [n1, n2, n3, n4]:
            dag.add_node(n)

        # 2. Schedule via WaveScheduler
        scheduler = WaveScheduler()
        waves = scheduler.schedule(dag)

        # 3. Real Execution of stages
        artifacts = []
        evidence = {}
        evidence["scope"] = "local_source_validation"
        evidence["source_origin"] = "caller_supplied_source_code"
        evidence["functional_tests"] = "NOT_EXECUTED"
        evidence["security_certification"] = "NOT_EXECUTED"
        evidence["model_or_remote_agent_calls"] = 0
        passed_stages = 0

        # Stage 1: Plan
        plan_doc = {
            "target": target_slug,
            "clean_slug": clean_slug,
            "created_utc": now_utc,
            "stages": [n.task_id for n in [n1, n2, n3, n4]],
            "policy": "SSP-v13.2"
        }
        plan_path = target_dir / "plan.json"
        plan_path.write_text(json.dumps(plan_doc, indent=2), encoding="utf-8")
        artifacts.append(str(plan_path))
        dag.mark_task_status(n1.task_id, TaskStatus.VERIFIED)
        passed_stages += 1

        # Stage 2: Synthesis
        artifacts.append(str(target_file))
        dag.mark_task_status(n2.task_id, TaskStatus.VERIFIED)
        passed_stages += 1

        # Stage 3: Compilation & Integrity Inspection
        inspection = self.inspect_code_integrity(target_file)
        evidence["inspection"] = inspection

        if inspection["valid"]:
            requirement = n3.verification_requirements[0]
            requirement.status = VerificationStatus.VERIFIED
            requirement.evidence = {"producer": "SoftwareEngineeringOrchestrator", "type": "file_exists",
                                    "path": str(target_file), "sha256": hashlib.sha256(target_file.read_bytes()).hexdigest(),
                                    "size": target_file.stat().st_size, "verified": target_file.is_file()}
            dag.mark_task_status(n3.task_id, TaskStatus.VERIFIED, result=inspection)
            passed_stages += 1
        else:
            dag.mark_task_status(n3.task_id, TaskStatus.FAILED, result=inspection)

        # Stage 4: Audit
        audit_passed = inspection["valid"] and (inspection["score"] >= 80.0)
        audit_verdict = {
            "clean_slug": clean_slug,
            "audit_passed": audit_passed,
            "score": inspection["score"],
            "violations": inspection.get("violations", []),
            "ast_error": inspection.get("ast_error")
        }
        evidence["audit"] = audit_verdict

        if audit_passed:
            dag.mark_task_status(n4.task_id, TaskStatus.VERIFIED, result=audit_verdict)
            passed_stages += 1
        else:
            dag.mark_task_status(n4.task_id, TaskStatus.FAILED, result=audit_verdict)

        overall_status = "PASS" if passed_stages == 4 else "FAIL"

        report_md = f"""# J.A.R.V.I.S. SWE Orchestration Laudo // {target_slug}
- **Status**: **{overall_status}**
- **Composite Score**: `{inspection['score']} / 100`
- **Etapas Concluídas**: `{passed_stages} / 4`
- **Artefatos**:
  - `{plan_path.name}`
  - `{target_file.name}`
- **Inspeção AST**: `{'PASS' if inspection.get('ast_valid') else 'FAIL'}`
- **Violações**: `{len(inspection.get('violations', []))}`
- **Escopo**: validação local de sintaxe e busca limitada de placeholders em código fornecido.
- **Compilação**: `{inspection['compilation']['status']}`.
- **Testes funcionais / typecheck / certificação de segurança**: `NOT_EXECUTED`.
- **Chamadas a modelos ou agentes remotos**: `0`.
"""
        report_path = target_dir / "orchestration_report.md"
        report_path.write_text(report_md, encoding="utf-8")
        artifacts.append(str(report_path))
        dag_path = target_dir / "execution-dag.json"
        dag.save(dag_path)
        artifacts.append(str(dag_path))
        evidence["artifacts"] = [
            {"path": art, "type": Path(art).suffix, "sha256": hashlib.sha256(Path(art).read_bytes()).hexdigest(),
             "producer": "SoftwareEngineeringOrchestrator", "verification": "file_exists_and_sha256_recorded"}
            for art in artifacts
        ]
        evidence_path = target_dir / "evidence.json"
        save_json_atomic(evidence_path, {"schema_version": "1.0.0", **evidence})
        artifacts.append(str(evidence_path))

        return SWEOrchestrationResult(
            target=target_slug,
            status=overall_status,
            composite_score=inspection["score"],
            total_stages=4,
            passed_stages=passed_stages,
            artifacts=artifacts,
            evidence=evidence,
            report_markdown=report_md
        )


if __name__ == "__main__":
    import argparse
    import sys
    parser = argparse.ArgumentParser(description="Validate explicitly supplied local Python source")
    parser.add_argument("target")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--registry-root", type=Path, default=REGISTRY_ROOT)
    args = parser.parse_args()
    orch = SoftwareEngineeringOrchestrator(args.registry_root)
    res = orch.execute_pipeline(args.target, args.source.read_text(encoding="utf-8-sig"))
    print(json.dumps({
        "status": res.status,
        "composite_score": res.composite_score,
        "total_stages": res.total_stages,
        "passed_stages": res.passed_stages,
        "artifacts": res.artifacts,
        "scope": res.evidence["scope"],
        "evidence": res.evidence
    }))
    sys.exit(0 if res.status == "PASS" else 1)
