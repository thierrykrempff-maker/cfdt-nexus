"""Tests for the neutral, reference-only Nexus Evidence Graph."""

import ast
from dataclasses import FrozenInstanceError, fields
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from NEXUS_CORE import (
    AcquisitionMethod,
    ConfidenceLevel,
    ConfidenceScore,
    ConflictId,
    DocumentId,
    EntityId,
    EvidenceId,
    FindingId,
    Period,
    Provenance,
    SourceReference,
    SourceType,
)
from NEXUS_CORE.evidence_graph import (
    EvidenceCluster,
    EvidenceEdge,
    EvidenceGraph,
    EvidenceGraphBuilder,
    EvidenceGraphExporter,
    EvidenceNode,
    EvidenceRelation,
    EvidenceRelationType,
    GraphNodeType,
    GraphStatus,
)


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PACKAGE = ROOT / "NEXUS_CORE" / "evidence_graph"


def provenance() -> Provenance:
    return Provenance(
        SourceReference(
            EntityId("source-graph-fixture"), SourceType.SYNTHETIC_FIXTURE, "graph_fixture"
        ),
        AcquisitionMethod.GENERATED,
        datetime(2026, 7, 21, 13, 0, tzinfo=timezone.utc),
    )


def node(
    identifier: str,
    node_type: GraphNodeType = GraphNodeType.EVIDENCE,
    period: Period | None = None,
) -> EvidenceNode:
    references = {
        GraphNodeType.EVIDENCE: EvidenceId(f"evidence-{identifier}"),
        GraphNodeType.FINDING: FindingId(f"finding-{identifier}"),
        GraphNodeType.CONFLICT: ConflictId(f"conflict-{identifier}"),
        GraphNodeType.DOCUMENT: DocumentId(f"document-{identifier}"),
    }
    return EvidenceNode(EntityId(f"node-{identifier}"), node_type, references[node_type], period)


def edge(
    identifier: str,
    origin: EvidenceNode,
    destination: EvidenceNode,
    relation_type: EvidenceRelationType = EvidenceRelationType.SUPPORTS,
) -> EvidenceEdge:
    return EvidenceEdge(
        EntityId(f"edge-{identifier}"),
        origin.node_id,
        destination.node_id,
        relation_type,
        ConfidenceScore(0.75, ConfidenceLevel.HIGH),
        provenance(),
    )


def test_empty_graph_has_explicit_empty_status_and_statistics():
    graph = EvidenceGraph.empty(EntityId("graph-empty"))
    assert graph.status is GraphStatus.EMPTY
    assert graph.nodes == ()
    assert graph.statistics().node_count == 0


def test_add_node_returns_new_graph_and_preserves_original():
    graph = EvidenceGraph.empty(EntityId("graph-add-node"))
    first = node("one")
    updated = graph.add_node(first)
    assert graph.nodes == ()
    assert updated.find_node(first.node_id) == first
    assert updated.status is GraphStatus.ACTIVE


@pytest.mark.parametrize("node_type", list(GraphNodeType))
def test_nodes_reference_each_supported_core_type_without_copying_data(node_type):
    model = node(node_type.value, node_type)
    assert {item.name for item in fields(EvidenceNode)} == {
        "node_id",
        "node_type",
        "reference",
        "period",
    }
    assert model.node_type is node_type


def test_node_rejects_reference_of_wrong_type():
    with pytest.raises(TypeError, match="requires EvidenceId"):
        EvidenceNode(EntityId("node-wrong"), GraphNodeType.EVIDENCE, FindingId("finding-wrong"))


def test_add_relation_requires_existing_endpoints():
    origin = node("origin")
    destination = node("destination")
    graph = EvidenceGraph.empty(EntityId("graph-edge")).add_node(origin)
    with pytest.raises(ValueError, match="existing nodes"):
        graph.add_relation(edge("missing-destination", origin, destination))


def test_add_relation_preserves_confidence_provenance_and_optional_period():
    origin = node("origin")
    destination = node("destination")
    relation = EvidenceRelation(
        EvidenceRelationType.CORROBORATES,
        ConfidenceScore(0.9, ConfidenceLevel.VERIFIED),
        provenance(),
        Period(date(2025, 1, 1), date(2025, 12, 31)),
    )
    model = EvidenceEdge.from_relation(
        EntityId("edge-relation"), origin.node_id, destination.node_id, relation
    )
    graph = EvidenceGraph.empty(EntityId("graph-relation")).add_node(origin).add_node(destination)
    graph = graph.add_relation(model)
    assert graph.edges[0].confidence == relation.confidence
    assert graph.edges[0].provenance == relation.provenance
    assert graph.edges[0].period == relation.period


def test_duplicate_nodes_and_edges_are_idempotent():
    first = node("first")
    second = node("second")
    graph = EvidenceGraph.empty(EntityId("graph-idempotent")).add_node(first).add_node(first)
    model = edge("same", first, second)
    graph = graph.add_node(second).add_relation(model).add_relation(model)
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1


def test_search_by_type_and_period():
    january = node(
        "january",
        GraphNodeType.DOCUMENT,
        Period(date(2025, 1, 1), date(2025, 1, 31)),
    )
    february = node(
        "february",
        GraphNodeType.DOCUMENT,
        Period(date(2025, 2, 1), date(2025, 2, 28)),
    )
    graph = EvidenceGraph.empty(EntityId("graph-search")).add_node(january).add_node(february)
    assert graph.find_by_type(GraphNodeType.DOCUMENT) == (january, february)
    assert graph.find_by_period(Period(date(2025, 1, 15), date(2025, 1, 20))) == (january,)


def test_simple_traversal_is_stable_and_cycle_safe():
    first, second, third = node("first"), node("second"), node("third")
    graph = EvidenceGraph.empty(EntityId("graph-traverse"))
    for item in (first, second, third):
        graph = graph.add_node(item)
    graph = graph.add_relation(edge("one-two", first, second))
    graph = graph.add_relation(edge("two-one", second, first, EvidenceRelationType.REFERENCES))
    graph = graph.add_relation(edge("two-three", second, third))
    assert graph.traverse(first.node_id, max_depth=3) == (first, second, third)


def test_clusters_only_group_existing_references():
    first, second = node("cluster-one"), node("cluster-two")
    graph = EvidenceGraph.empty(EntityId("graph-cluster")).add_node(first).add_node(second)
    cluster = EvidenceCluster(
        EntityId("cluster-technical-1"), (first.node_id, second.node_id), "RELATED_PERIOD"
    )
    graph = graph.add_cluster(cluster)
    assert graph.clusters == (cluster,)


def test_json_export_is_deterministic_reference_only_and_uses_iso_dates():
    secret = "synthetic-content-that-must-not-be-copied"
    first = node(
        "json-one",
        GraphNodeType.EVIDENCE,
        Period(date(2025, 1, 1), date(2025, 1, 31)),
    )
    second = node("json-two", GraphNodeType.FINDING)
    graph = EvidenceGraph.empty(EntityId("graph-json")).add_node(first).add_node(second)
    graph = graph.add_relation(edge("json", first, second, EvidenceRelationType.SUPPORTS))
    exported = graph.export_json()
    assert exported == graph.export_json()
    assert '"relation_type":"supports"' in exported
    assert "2025-01-01" in exported
    assert secret not in exported
    assert "0x" not in exported


def test_statistics_are_deterministic_and_generic():
    first, second = node("stats-one"), node("stats-two", GraphNodeType.FINDING)
    graph = EvidenceGraph.empty(EntityId("graph-stats")).add_node(first).add_node(second)
    graph = graph.add_relation(edge("stats", first, second, EvidenceRelationType.CONTRADICTS))
    statistics = graph.statistics()
    assert statistics.node_count == 2
    assert statistics.edge_count == 1
    assert dict(statistics.edges_by_relation)[EvidenceRelationType.CONTRADICTS] == 1


def test_graph_models_are_immutable():
    graph = EvidenceGraph.empty(EntityId("graph-frozen"))
    with pytest.raises(FrozenInstanceError):
        graph.status = GraphStatus.ACTIVE


class Builder:
    def build(self, graph_id, results):
        return EvidenceGraph.empty(graph_id)


class Exporter:
    def export(self, graph):
        return graph.export_json()


def test_builder_and_exporter_protocols_are_structural():
    assert isinstance(Builder(), EvidenceGraphBuilder)
    assert isinstance(Exporter(), EvidenceGraphExporter)


def test_graph_package_depends_only_on_standard_library_and_nexus_core():
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
        "flask",
        "fastapi",
    }
    for path in GRAPH_PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        roots = set()
        for item in ast.walk(tree):
            if isinstance(item, ast.Import):
                roots.update(alias.name.split(".")[0] for alias in item.names)
            elif isinstance(item, ast.ImportFrom) and item.level == 0 and item.module:
                roots.add(item.module.split(".")[0])
        assert not roots & forbidden, path.name


def test_graph_internal_imports_are_acyclic_and_python_3_10_compatible():
    paths = tuple(sorted(GRAPH_PACKAGE.glob("*.py")))
    modules = {path.stem for path in paths}
    graph = {module: set() for module in modules}
    for path in paths:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path), feature_version=(3, 10))
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
