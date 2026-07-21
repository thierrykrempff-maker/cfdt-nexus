"""Deterministic reporting, confidentiality and architecture boundaries."""

import ast
from datetime import datetime, timezone
from pathlib import Path

from NEXUS_CORE import EntityId
from NEXUS_CORE.orchestration import (
    EngineCapability,
    EngineDescriptor,
    EngineRegistry,
    ExecutionContext,
    ExecutionPlanner,
    ExecutionReporter,
    ExecutionResult,
    ExecutionStatus,
    JsonExecutionReporter,
    PipelineExecutor,
)


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "NEXUS_CORE" / "orchestration"
NOW = datetime(2026, 7, 21, 16, 0, tzinfo=timezone.utc)
CAPABILITY = EngineCapability("REPORTING_TEST")


class Engine:
    def execute(self, context):
        return ExecutionResult(
            EntityId("result-reporting-test"),
            EntityId("engine-reporting-test"),
            ExecutionStatus.SUCCEEDED,
            (CAPABILITY,),
            (EntityId("output-technical-only"),),
            3,
        )


def report():
    registry = EngineRegistry()
    descriptor = EngineDescriptor(
        EntityId("engine-reporting-test"), "REPORTING_ENGINE", (CAPABILITY,)
    )
    registry.register(descriptor, Engine())
    plan = ExecutionPlanner().plan(EntityId("plan-reporting"), registry, (CAPABILITY,), NOW)
    context = ExecutionContext(
        EntityId("execution-reporting"), plan.plan_id, (CAPABILITY,), (), NOW
    )
    return PipelineExecutor().execute(plan, registry, context, NOW)


def test_json_is_deterministic_iso_and_explicitly_versioned():
    value = report()
    reporter = JsonExecutionReporter()
    first = reporter.render(value)
    assert first == reporter.render(value)
    assert "2026-07-21T16:00:00+00:00" in first
    assert '"schema_version":"1.0"' in first
    assert isinstance(reporter, ExecutionReporter)


def test_report_serialization_contains_only_technical_references():
    rendered = JsonExecutionReporter().render(report())
    assert "output-technical-only" in rendered
    assert "personal_value" not in rendered
    assert "business_result" not in rendered
    assert "legal_decision" not in rendered


def test_orchestration_has_no_domain_network_database_or_automation_import():
    forbidden = {
        "automation",
        "RETIREMENT_PENIBILITY_ENGINE",
        "CCSEMEMORYENGINE",
        "PROTECTION_SOCIALE_ENGINE",
        "requests",
        "urllib",
        "http",
        "socket",
        "ssl",
        "sqlite3",
        "sqlalchemy",
    }
    for path in PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        roots = set()
        for item in ast.walk(tree):
            if isinstance(item, ast.Import):
                roots.update(alias.name.split(".")[0] for alias in item.names)
            elif isinstance(item, ast.ImportFrom) and item.level == 0 and item.module:
                roots.add(item.module.split(".")[0])
            elif isinstance(item, ast.Call) and isinstance(item.func, ast.Name):
                assert item.func.id not in {"__import__", "eval", "exec"}
        assert not roots & forbidden, path.name


def test_orchestration_is_acyclic_and_python_3_10_compatible():
    paths = tuple(sorted(PACKAGE.glob("*.py")))
    modules = {path.stem for path in paths}
    graph = {module: set() for module in modules}
    for path in paths:
        tree = ast.parse(
            path.read_text(encoding="utf-8"),
            filename=str(path),
            feature_version=(3, 10),
        )
        for item in ast.walk(tree):
            if isinstance(item, ast.ImportFrom) and item.level == 1 and item.module:
                target = item.module.split(".")[0]
                if target in modules:
                    graph[path.stem].add(target)

    visited = set()
    visiting = set()

    def visit(module):
        assert module not in visiting, f"import cycle involving {module}"
        if module in visited:
            return
        visiting.add(module)
        for dependency in graph[module]:
            visit(dependency)
        visiting.remove(module)
        visited.add(module)

    for module in graph:
        visit(module)
