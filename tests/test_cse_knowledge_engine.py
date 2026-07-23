import ast
from pathlib import Path

import pytest

from CSE_KNOWLEDGE_ENGINE import (
    CSEKnowledgeAPI,
    CSEKnowledgeEngine,
    CSEKnowledgeQuery,
)
from DOCUMENT_INTELLIGENCE_CENTER import (
    DocumentDescriptor,
    DocumentGraph,
    DocumentKind,
    DocumentNavigationService,
    DocumentRelation,
    RelationKind,
)


def _document(
    document_id: str,
    title: str,
    kind: DocumentKind,
    *,
    date: str,
    family: str | None = None,
    nature: str | None = None,
    status: str = "ACTIVE",
    instance: str | None = None,
) -> DocumentDescriptor:
    return DocumentDescriptor(
        document_id=document_id,
        title=title,
        document_kind=kind,
        provenance="SYNTHETIC_METADATA",
        publication_date=date,
        family=family,
        nature=nature,
        status=status,
        instance=instance,
    )


def _engine() -> CSEKnowledgeEngine:
    documents = (
        _document(
            "minutes-cse-0001",
            "Réunion CSE janvier",
            DocumentKind.CSE_MINUTES,
            date="2025-01-15",
            family="Travail de nuit",
            instance="CSE",
        ),
        _document(
            "minutes-cse-0002",
            "Réunion CSE février",
            DocumentKind.CSE_MINUTES,
            date="2025-02-15",
            family="Travail de nuit",
            instance="CSE",
        ),
        _document(
            "minutes-cse-0003",
            "Réunion CSE mars",
            DocumentKind.CSE_MINUTES,
            date="2025-03-15",
            family="Classification",
            instance="CSE",
        ),
        _document(
            "decision-cse-001",
            "Décision sur les horaires de nuit",
            DocumentKind.OTHER,
            date="2025-01-15",
            family="Travail de nuit",
            nature="DECISION",
            status="CLOSED",
        ),
        _document(
            "commitment-cse-01",
            "Suivi des équipements de nuit",
            DocumentKind.OTHER,
            date="2025-01-15",
            family="Travail de nuit",
            nature="MANAGEMENT_COMMITMENT",
            status="OPEN",
        ),
        _document(
            "consultation-cse1",
            "Consultation sur les horaires",
            DocumentKind.OTHER,
            date="2025-01-15",
            family="Travail de nuit",
            nature="CONSULTATION",
            status="CLOSED",
        ),
        _document(
            "agreement-cse-001",
            "Accord classification",
            DocumentKind.AGREEMENT,
            date="2024-12-01",
            family="Classification",
        ),
    )
    relations = (
        DocumentRelation(
            "minutes-cse-0001",
            "decision-cse-001",
            RelationKind.DECIDES_ON,
            "SYNTHETIC_METADATA",
        ),
        DocumentRelation(
            "minutes-cse-0001",
            "commitment-cse-01",
            RelationKind.DISCUSSES,
            "SYNTHETIC_METADATA",
        ),
        DocumentRelation(
            "minutes-cse-0002",
            "commitment-cse-01",
            RelationKind.DISCUSSES,
            "SYNTHETIC_METADATA",
        ),
        DocumentRelation(
            "minutes-cse-0001",
            "consultation-cse1",
            RelationKind.REFERENCES,
            "SYNTHETIC_METADATA",
        ),
        DocumentRelation(
            "minutes-cse-0003",
            "agreement-cse-001",
            RelationKind.REFERENCES,
            "SYNTHETIC_METADATA",
        ),
    )
    navigation = DocumentNavigationService(DocumentGraph(documents, relations))
    return CSEKnowledgeEngine(navigation)


def test_engine_implements_public_protocol() -> None:
    assert isinstance(_engine(), CSEKnowledgeAPI)


def test_subject_search_returns_all_related_minutes() -> None:
    meetings = _engine().find_minutes_by_subject(
        CSEKnowledgeQuery(subject="travail de nuit")
    )
    assert tuple(item.meeting_document_id for item in meetings) == (
        "minutes-cse-0001",
        "minutes-cse-0002",
    )


def test_subject_search_uses_related_safe_metadata() -> None:
    meetings = _engine().find_minutes_by_subject(
        CSEKnowledgeQuery(subject="accord classification")
    )
    assert tuple(item.meeting_document_id for item in meetings) == (
        "minutes-cse-0003",
    )


def test_subject_search_is_not_semantic() -> None:
    assert (
        _engine().find_minutes_by_subject(
            CSEKnowledgeQuery(subject="rémunération")
        )
        == ()
    )


def test_decisions_are_derived_from_explicit_relations() -> None:
    decisions = _engine().find_decisions()
    assert len(decisions) == 1
    assert decisions[0].document_id == "decision-cse-001"
    assert decisions[0].category == "DECISION"
    assert decisions[0].meeting_document_ids == ("minutes-cse-0001",)


def test_management_commitments_are_grouped_across_meetings() -> None:
    commitments = _engine().track_management_commitments()
    assert len(commitments) == 1
    assert commitments[0].meeting_document_ids == (
        "minutes-cse-0001",
        "minutes-cse-0002",
    )


def test_past_consultations_are_metadata_only() -> None:
    consultations = _engine().past_consultations()
    assert tuple(item.document_id for item in consultations) == (
        "consultation-cse1",
    )
    assert not hasattr(consultations[0], "content")
    assert not hasattr(consultations[0], "canonical_url")


def test_recurring_subjects_count_unique_meetings() -> None:
    subjects = _engine().recurring_subjects()
    assert len(subjects) == 1
    assert subjects[0].label == "Travail de nuit"
    assert subjects[0].occurrence_count == 2


def test_recurring_subject_threshold_is_validated() -> None:
    with pytest.raises(ValueError, match="at least 2"):
        _engine().recurring_subjects(minimum_occurrences=1)


def test_agenda_combines_recurring_topics_and_open_commitments() -> None:
    agenda = _engine().prepare_agenda()
    assert tuple(item.category for item in agenda) == (
        "OPEN_MANAGEMENT_COMMITMENT",
        "RECURRING_SUBJECT",
    )
    assert agenda[0].priority == 1
    assert agenda[1].priority == 2


def test_meeting_summary_counts_typed_facts() -> None:
    summary = _engine().summarize_meetings(
        CSEKnowledgeQuery(subject="travail de nuit")
    )[0]
    assert summary.decision_count == 1
    assert summary.commitment_count == 1
    assert summary.consultation_count == 1


def test_date_period_limits_historical_consultation() -> None:
    query = CSEKnowledgeQuery(
        date_from="2025-02-01",
        date_to="2025-12-31",
    )
    assert _engine().past_consultations(query) == ()


def test_report_is_serializable_and_deterministic() -> None:
    query = CSEKnowledgeQuery(subject="Travail de nuit")
    first = _engine().build_report(query)
    second = _engine().build_report(query)
    assert first.to_json() == second.to_json()
    assert first.to_dict()["query"]["subject"] == "Travail de nuit"


@pytest.mark.parametrize(
    "unsafe_subject",
    (
        r"C:\private\minutes.pdf",
        "/home/user/minutes.pdf",
        "employee@example.test",
        "chunk_12345678",
        "<html>secret</html>",
    ),
)
def test_query_rejects_unsafe_metadata(unsafe_subject: str) -> None:
    with pytest.raises(ValueError):
        CSEKnowledgeQuery(subject=unsafe_subject)


def test_public_report_contains_no_content_or_local_path_fields() -> None:
    report = _engine().build_report(CSEKnowledgeQuery())
    serialized = report.to_json().lower()
    forbidden = (
        "canonical_url",
        '"content"',
        '"chunk"',
        "storage_id",
        r"c:\\",
        "/home/",
        "/tmp/",
    )
    assert all(value not in serialized for value in forbidden)


def test_engine_has_no_network_or_semantic_dependencies() -> None:
    package = Path(__file__).parents[1] / "CSE_KNOWLEDGE_ENGINE"
    forbidden_imports = {
        "aiohttp",
        "httpx",
        "openai",
        "requests",
        "socket",
        "urllib",
    }
    imported: set[str] = set()
    for source_file in package.glob("*.py"):
        tree = ast.parse(source_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
    assert imported.isdisjoint(forbidden_imports)


def test_engine_does_not_mutate_navigation_graph() -> None:
    engine = _engine()
    before = engine._navigation.statistics().to_json()
    engine.build_report(CSEKnowledgeQuery())
    after = engine._navigation.statistics().to_json()
    assert after == before
