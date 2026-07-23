from DOCUMENT_INTELLIGENCE_CENTER import (
    DocumentKind,
    NavigationQuery,
    RelationKind,
)

from test_document_navigation_api import _service


def test_search_by_document_type() -> None:
    result = _service().search(
        NavigationQuery(document_kind=DocumentKind.AGREEMENT)
    )
    assert tuple(item.document_id for item in result.documents) == (
        "agreement-00000001",
        "agreement-00000002",
    )


def test_search_by_period_instance_and_status() -> None:
    service = _service()
    result = service.search(
        NavigationQuery(
            date_from="2025-01-15",
            date_to="2025-12-31",
            instance="CSE",
            status="ACTIVE",
        )
    )
    assert tuple(item.document_id for item in result.documents) == (
        "minutes-00000001",
    )


def test_search_by_agreement_family() -> None:
    result = _service().search(NavigationQuery(family="working-time"))
    assert len(result.documents) == 2
    assert all(item.family == "working-time" for item in result.documents)


def test_agreement_version_history_is_ordered() -> None:
    result = _service().agreement_versions(family="working-time")
    assert tuple(item.version for item in result.documents) == ("1", "2")
    assert result.relations[0].relation_kind is RelationKind.SUPERSEDES


def test_replaced_or_modified_documents_are_retrievable() -> None:
    result = _service().replaced_or_modified("agreement-00000002")
    assert {item.document_id for item in result.documents} == {
        "agreement-00000001",
        "agreement-00000002",
    }


def test_minutes_and_agreements_can_be_navigated_both_ways() -> None:
    service = _service()
    minutes = service.minutes_for_agreement("agreement-00000002")
    agreements = service.agreements_for_minutes("minutes-00000001")
    assert {item.document_id for item in minutes.documents} == {
        "agreement-00000002",
        "minutes-00000001",
    }
    assert {item.document_id for item in agreements.documents} == {
        "agreement-00000002",
        "minutes-00000001",
    }
