"""End-to-end generic conflict resolution and architecture boundaries."""

import ast
from datetime import datetime, timezone
from pathlib import Path

from NEXUS_CORE import (
    AcquisitionMethod,
    ConfidenceLevel,
    ConfidenceScore,
    EntityId,
    EntityReference,
    Evidence,
    EvidenceId,
    EvidenceQuality,
    Provenance,
    SourceReference,
    SourceType,
    TextEvidenceValue,
    ValidationStatus,
)
from NEXUS_CORE.conflict_resolution import (
    ConflictResolutionEngine,
    GenericConflictResolutionEngine,
    ResolutionCategory,
)
from NEXUS_CORE.reasoning import FactType, GenericReasoningPipeline


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "NEXUS_CORE" / "conflict_resolution"
NOW = datetime(2026, 7, 21, 15, 0, tzinfo=timezone.utc)
SUBJECT = EntityReference(EntityId("subject-conflict"), "person")


def evidence(identifier, value):
    return Evidence(
        EvidenceId(f"evidence-{identifier}"),
        SUBJECT,
        "status",
        TextEvidenceValue(value),
        None,
        None,
        Provenance(
            SourceReference(EntityId(f"source-{identifier}"), SourceType.SYNTHETIC_FIXTURE, "fixture"),
            AcquisitionMethod.GENERATED,
            NOW,
        ),
        ConfidenceScore(0.8, ConfidenceLevel.HIGH),
        EvidenceQuality.CONSISTENT,
        ValidationStatus.VALID,
        EntityId("producer-conflict-test"),
        (),
        NOW,
    )


def test_pipeline_classifies_conflict_without_arbitration_or_priority():
    reasoning = GenericReasoningPipeline().reason(
        EntityId("reasoning-resolution-engine"),
        (evidence("one", "alpha"), evidence("two", "beta")),
        SUBJECT,
        (FactType("status"),),
        NOW,
    )
    engine = GenericConflictResolutionEngine()
    resolution = engine.resolve(EntityId("resolution-report"), reasoning, NOW)
    categories = {item.category for item in resolution.classifications}
    assert ResolutionCategory.DOCUMENT_CONFLICT in categories
    assert ResolutionCategory.UNRESOLVED in categories
    assert all(not hasattr(item, "selected_evidence") for item in resolution.candidates)
    assert all(not hasattr(item, "preferred_evidence") for item in resolution.candidates)
    assert not hasattr(resolution, "legal_decision")
    assert isinstance(engine, ConflictResolutionEngine)


def test_package_has_no_domain_engine_network_database_or_automation_import():
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


def test_package_is_acyclic_and_python_3_10_compatible():
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
