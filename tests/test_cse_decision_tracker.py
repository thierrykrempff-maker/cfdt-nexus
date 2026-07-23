import ast
from pathlib import Path

import pytest

from CSE_DECISION_TRACKER import (
    CSEDecisionTracker,
    CSEDecisionTrackerAPI,
    DecisionTrackerQuery,
    TrackingStatus,
)
from CSE_DECISION_TRACKER.policy import normalize_status
from CSE_KNOWLEDGE_ENGINE import CSEKnowledgeEngine
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
    due_date: str | None = None,
) -> DocumentDescriptor:
    return DocumentDescriptor(
        document_id=document_id,
        title=title,
        document_kind=kind,
        provenance="SYNTHETIC_METADATA",
        publication_date=date,
        effective_to=due_date,
        family=family,
        nature=nature,
        status=status,
        instance=instance,
    )


def _tracker() -> CSEDecisionTracker:
    documents = (
        _document(
            "minutes-track-001",
            "Réunion CSE janvier",
            DocumentKind.CSE_MINUTES,
            date="2025-01-15",
            family="Travail de nuit",
            instance="CSE",
        ),
        _document(
            "minutes-track-002",
            "Réunion CSE février",
            DocumentKind.CSE_MINUTES,
            date="2025-02-15",
            family="Travail de nuit",
            instance="CSE",
        ),
        _document(
            "minutes-track-003",
            "Réunion CSE mars",
            DocumentKind.CSE_MINUTES,
            date="2025-03-15",
            family="Classification",
            instance="CSE",
        ),
        _document(
            "decision-track-01",
            "Décision horaires équipe A",
            DocumentKind.OTHER,
            date="2025-01-15",
            family="Horaires postés",
            nature="DECISION",
            status="CLOSED",
        ),
        _document(
            "decision-track-02",
            "Décision horaires équipe B",
            DocumentKind.OTHER,
            date="2025-02-15",
            family="Horaires postés",
            nature="DECISION",
            status="OPEN",
        ),
        _document(
            "decision-track-03",
            "Décision classification",
            DocumentKind.OTHER,
            date="2025-03-15",
            family="Classification",
            nature="DECISION",
            status="UNKNOWN",
        ),
        _document(
            "commitment-track1",
            "Engagement Direction sur les horaires",
            DocumentKind.OTHER,
            date="2025-02-15",
            family="Horaires postés",
            nature="MANAGEMENT_COMMITMENT",
            status="ACTIVE",
            due_date="2025-06-30",
        ),
        _document(
            "elected-action-01",
            "Action des élus sur les horaires",
            DocumentKind.OTHER,
            date="2025-02-15",
            family="Horaires postés",
            nature="ELECTED_ACTION",
            status="IN_PROGRESS",
            due_date="2025-04-30",
        ),
    )
    relations = (
        DocumentRelation(
            "minutes-track-001",
            "decision-track-01",
            RelationKind.DECIDES_ON,
            "SYNTHETIC_METADATA",
        ),
        DocumentRelation(
            "minutes-track-002",
            "decision-track-02",
            RelationKind.DECIDES_ON,
            "SYNTHETIC_METADATA",
        ),
        DocumentRelation(
            "minutes-track-003",
            "decision-track-03",
            RelationKind.DECIDES_ON,
            "SYNTHETIC_METADATA",
        ),
        DocumentRelation(
            "minutes-track-002",
            "commitment-track1",
            RelationKind.DISCUSSES,
            "SYNTHETIC_METADATA",
        ),
        DocumentRelation(
            "minutes-track-002",
            "elected-action-01",
            RelationKind.IMPLEMENTS,
            "SYNTHETIC_METADATA",
        ),
        DocumentRelation(
            "decision-track-01",
            "elected-action-01",
            RelationKind.IMPLEMENTS,
            "SYNTHETIC_METADATA",
        ),
        DocumentRelation(
            "decision-track-02",
            "commitment-track1",
            RelationKind.RELATED_TO,
            "SYNTHETIC_METADATA",
        ),
    )
    navigation = DocumentNavigationService(DocumentGraph(documents, relations))
    return CSEDecisionTracker(
        CSEKnowledgeEngine(navigation),
        navigation,
    )


def test_tracker_implements_public_protocol() -> None:
    assert isinstance(_tracker(), CSEDecisionTrackerAPI)


def test_decisions_are_detected_from_explicit_relations() -> None:
    decisions = _tracker().detect_decisions()
    assert tuple(item.document_id for item in decisions) == (
        "decision-track-01",
        "decision-track-02",
        "decision-track-03",
    )
    assert all(item.category == "DECISION" for item in decisions)


def test_management_commitment_is_tracked() -> None:
    commitments = _tracker().track_management_commitments()
    assert len(commitments) == 1
    assert commitments[0].document_id == "commitment-track1"
    assert commitments[0].status is TrackingStatus.OPEN


def test_elected_action_is_tracked() -> None:
    actions = _tracker().track_elected_actions()
    assert len(actions) == 1
    assert actions[0].document_id == "elected-action-01"
    assert actions[0].status is TrackingStatus.IN_PROGRESS


@pytest.mark.parametrize(
    ("raw_status", "expected"),
    (
        ("OPEN", TrackingStatus.OPEN),
        ("ACTIVE", TrackingStatus.OPEN),
        ("IN_PROGRESS", TrackingStatus.IN_PROGRESS),
        ("PENDING", TrackingStatus.IN_PROGRESS),
        ("CLOSED", TrackingStatus.CLOSED),
        ("COMPLETED", TrackingStatus.CLOSED),
        ("CANCELLED", TrackingStatus.CANCELLED),
        ("unmapped", TrackingStatus.UNKNOWN),
    ),
)
def test_statuses_are_normalized_explicitly(
    raw_status: str,
    expected: TrackingStatus,
) -> None:
    assert normalize_status(raw_status) is expected


def test_follow_up_links_are_preserved() -> None:
    decisions = _tracker().detect_decisions()
    assert decisions[0].follow_up_document_ids == ("elected-action-01",)
    assert decisions[1].follow_up_document_ids == ("commitment-track1",)


def test_decision_without_follow_up_is_identified() -> None:
    assert _tracker().decisions_without_follow_up() == (
        "decision-track-03",
    )


def test_recurring_decisions_use_controlled_family() -> None:
    recurring = _tracker().recurring_decisions()
    assert len(recurring) == 1
    assert recurring[0].label == "Horaires postés"
    assert recurring[0].occurrence_count == 2
    assert recurring[0].decision_document_ids == (
        "decision-track-01",
        "decision-track-02",
    )


def test_closure_rate_is_computed_on_decisions_only() -> None:
    statistics = _tracker().statistics()
    assert statistics.decision_count == 3
    assert statistics.closed_count == 1
    assert statistics.closure_rate == 33.33


def test_statistics_cover_all_statuses_and_categories() -> None:
    statistics = _tracker().statistics()
    assert statistics.commitment_count == 1
    assert statistics.elected_action_count == 1
    assert statistics.open_count == 2
    assert statistics.in_progress_count == 1
    assert statistics.unknown_count == 1
    assert statistics.decisions_without_follow_up_count == 1
    assert statistics.recurring_decision_group_count == 1


def test_overdue_action_uses_injected_reference_date() -> None:
    tracker = _tracker()
    before = tracker.track_elected_actions(
        DecisionTrackerQuery(as_of_date="2025-04-01")
    )
    after = tracker.track_elected_actions(
        DecisionTrackerQuery(as_of_date="2025-05-01")
    )
    assert before[0].overdue is False
    assert after[0].overdue is True
    assert tracker.statistics(
        DecisionTrackerQuery(as_of_date="2025-05-01")
    ).overdue_action_count == 1


def test_no_clock_based_delay_without_reference_date() -> None:
    assert _tracker().track_elected_actions()[0].overdue is False


def test_follow_up_agenda_excludes_closed_items() -> None:
    agenda = _tracker().prepare_follow_up_agenda(
        DecisionTrackerQuery(as_of_date="2025-05-01")
    )
    identifiers = tuple(item.document_id for item in agenda.items)
    assert agenda.title == "Suivi des décisions précédentes"
    assert "decision-track-01" not in identifiers
    assert "decision-track-02" in identifiers
    assert identifiers[0] == "elected-action-01"


def test_subject_filter_is_delegated_to_knowledge_engine() -> None:
    decisions = _tracker().detect_decisions(
        DecisionTrackerQuery(subject="classification")
    )
    assert tuple(item.document_id for item in decisions) == (
        "decision-track-03",
    )


def test_report_is_deterministic_idempotent_and_serializable() -> None:
    tracker = _tracker()
    query = DecisionTrackerQuery(as_of_date="2025-05-01")
    first = tracker.build_report(query)
    second = tracker.build_report(query)
    assert first == second
    assert first.to_json() == second.to_json()
    assert first.to_dict()["statistics"]["decision_count"] == 3


def test_report_is_metadata_only() -> None:
    serialized = _tracker().build_report(DecisionTrackerQuery()).to_json().lower()
    forbidden = (
        "canonical_url",
        '"content"',
        '"chunk"',
        "storage_id",
        r"c:\\",
        "/home/",
        "/tmp/",
        "<html",
    )
    assert all(value not in serialized for value in forbidden)


@pytest.mark.parametrize(
    "unsafe_subject",
    (
        r"D:\private\pv.pdf",
        "/Users/private/pv.pdf",
        "person@example.test",
        "chunk_12345678",
        "<html>document</html>",
    ),
)
def test_query_rejects_unsafe_metadata(unsafe_subject: str) -> None:
    with pytest.raises(ValueError):
        DecisionTrackerQuery(subject=unsafe_subject)


def test_invalid_reference_date_is_rejected() -> None:
    with pytest.raises(ValueError, match="ISO date"):
        DecisionTrackerQuery(as_of_date="15/05/2025")


def test_tracker_does_not_mutate_document_graph() -> None:
    tracker = _tracker()
    before = tracker._navigation.statistics().to_json()
    tracker.build_report(DecisionTrackerQuery(as_of_date="2025-05-01"))
    assert tracker._navigation.statistics().to_json() == before


def test_tracker_has_no_network_or_semantic_dependency() -> None:
    package = Path(__file__).parents[1] / "CSE_DECISION_TRACKER"
    forbidden_imports = {
        "aiohttp",
        "httpx",
        "openai",
        "requests",
        "socket",
        "urllib",
    }
    imports: set[str] = set()
    for source_file in package.glob("*.py"):
        tree = ast.parse(source_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
    assert imports.isdisjoint(forbidden_imports)


def test_v2_2a_knowledge_report_remains_unchanged() -> None:
    tracker = _tracker()
    before = tracker._knowledge_engine.build_report(
        tracker._knowledge_query(DecisionTrackerQuery())
    ).to_json()
    tracker.build_report(DecisionTrackerQuery(as_of_date="2025-05-01"))
    after = tracker._knowledge_engine.build_report(
        tracker._knowledge_query(DecisionTrackerQuery())
    ).to_json()
    assert after == before
