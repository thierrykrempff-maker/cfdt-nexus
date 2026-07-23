import json

import pytest

from DOCUMENT_INTELLIGENCE_CENTER import (
    DocumentDescriptor,
    DocumentGraph,
    DocumentKind,
    DocumentNavigationService,
    NavigationQuery,
)

from test_document_navigation_api import _service


def test_shortest_path_is_deterministic() -> None:
    path = _service().shortest_path(
        "agreement-00000001",
        "guide-00000000001",
    )
    assert path.document_ids == (
        "agreement-00000001",
        "agreement-00000002",
        "minutes-00000001",
        "guide-00000000001",
    )
    assert path.length == 3
    assert json.loads(path.to_json())["found"] is True


def test_unreachable_path_is_empty() -> None:
    path = _service().shortest_path(
        "agreement-00000001",
        "orphan-000000001",
    )
    assert path.found is False
    assert path.length == 0


def test_orphans_and_connected_components_are_detected() -> None:
    service = _service()
    assert service.orphan_document_ids() == ("orphan-000000001",)
    assert service.connected_components() == (
        (
            "agreement-00000001",
            "agreement-00000002",
            "guide-00000000001",
            "minutes-00000001",
        ),
        ("orphan-000000001",),
    )


def test_graph_statistics_are_complete_and_serializable() -> None:
    statistics = _service().statistics()
    assert statistics.node_count == 5
    assert statistics.relation_count == 3
    assert statistics.density == 0.15
    assert statistics.agreement_families == ("working-time",)
    assert statistics.agreement_version_count == 2
    assert dict(statistics.documents_by_type)["AGREEMENT"] == 2
    assert json.loads(statistics.to_json())["node_count"] == 5


def test_navigation_rejects_non_pseudonymized_identifiers() -> None:
    graph = DocumentGraph(
        (
            DocumentDescriptor(
                document_id="raw-id",
                title="Document synthétique",
                document_kind=DocumentKind.OTHER,
                provenance="SYNTHETIC_METADATA",
            ),
        )
    )
    service = DocumentNavigationService(graph)
    with pytest.raises(ValueError, match="pseudonymized"):
        service.get_document("raw-id")


def test_navigation_rejects_sensitive_metadata_in_public_projection() -> None:
    graph = DocumentGraph(
        (
            DocumentDescriptor(
                document_id="document-00000001",
                title=r"C:\private\document.pdf",
                document_kind=DocumentKind.OTHER,
                provenance="SYNTHETIC_METADATA",
            ),
        )
    )
    with pytest.raises(ValueError, match="local path"):
        DocumentNavigationService(graph).get_document("document-00000001")


def test_navigation_query_rejects_sensitive_filter_value() -> None:
    with pytest.raises(ValueError, match="local path"):
        NavigationQuery(family=r"C:\private\agreements")
