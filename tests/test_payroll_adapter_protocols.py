"""Public Protocol implementation, orchestration and architecture isolation."""

import ast
from datetime import datetime, timezone
from pathlib import Path

from NEXUS_ADAPTERS.payroll import PAYROLL_ADAPTATION, PayrollAdapter
from NEXUS_CORE import (
    AnalysisId,
    AnalysisQuestion,
    AnalysisRequest,
    AnalysisScope,
    CorrelationId,
    DomainSelection,
    EntityId,
    EvidenceProducer,
    FindingProducer,
    RecommendationProducer,
)
from NEXUS_CORE.orchestration import (
    EngineDescriptor,
    EngineRegistry,
    ExecutableEngine,
    ExecutionContext,
    ExecutionPlanner,
    ExecutionStatus,
    PipelineExecutor,
)
from NEXUS_CORE.reasoning import FactProducer

from test_payroll_adapter import NOW, SUBJECT, payroll_report


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "NEXUS_ADAPTERS" / "payroll"
CORE = ROOT / "NEXUS_CORE"


def request():
    return AnalysisRequest(
        AnalysisId("analysis-payroll-adapter"),
        CorrelationId("correlation-payroll-adapter"),
        AnalysisQuestion("PAYROLL_ADAPTATION"),
        AnalysisScope((SUBJECT,)),
        (DomainSelection.PAYROLL,),
    )


def test_adapter_implements_all_required_protocols():
    adapter = PayrollAdapter(payroll_report(), SUBJECT, NOW)
    assert isinstance(adapter, ExecutableEngine)
    assert isinstance(adapter, FactProducer)
    assert isinstance(adapter, EvidenceProducer)
    assert isinstance(adapter, FindingProducer)
    assert isinstance(adapter, RecommendationProducer)
    assert adapter.produce_evidence(request())
    assert adapter.produce_findings(request())
    assert adapter.produce_recommendations(request())


def test_adapter_executes_through_orchestration_framework():
    adapter = PayrollAdapter(payroll_report(), SUBJECT, NOW)
    registry = EngineRegistry()
    descriptor = EngineDescriptor(
        EntityId("adapter-payroll"), "PAYROLL_ADAPTER", (PAYROLL_ADAPTATION,)
    )
    registry.register(descriptor, adapter)
    plan = ExecutionPlanner().plan(
        EntityId("plan-payroll-adapter"), registry, (PAYROLL_ADAPTATION,), NOW
    )
    context = ExecutionContext(
        EntityId("execution-payroll-adapter"),
        plan.plan_id,
        plan.requested_capabilities,
        (),
        NOW,
    )
    execution = PipelineExecutor().execute(plan, registry, context, NOW)
    assert execution.summary.succeeded_count == 1
    assert execution.results[0].status is ExecutionStatus.SUCCEEDED
    assert execution.results[0].output_references


def test_adapter_is_explicit_and_core_never_imports_adapters():
    adapter_import_roots = set()
    for path in ADAPTER.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for item in ast.walk(tree):
            if isinstance(item, ast.Import):
                adapter_import_roots.update(alias.name.split(".")[0] for alias in item.names)
            elif isinstance(item, ast.ImportFrom) and item.level == 0 and item.module:
                adapter_import_roots.add(item.module.split(".")[0])
        source = path.read_text(encoding="utf-8")
        assert "eval(" not in source
        assert "exec(" not in source
    assert {"automation", "NEXUS_CORE"}.issubset(adapter_import_roots)

    for path in CORE.rglob("*.py"):
        assert "NEXUS_ADAPTERS" not in path.read_text(encoding="utf-8")


def test_adapter_sources_are_python_3_10_compatible():
    for path in ADAPTER.glob("*.py"):
        ast.parse(
            path.read_text(encoding="utf-8"),
            filename=str(path),
            feature_version=(3, 10),
        )
