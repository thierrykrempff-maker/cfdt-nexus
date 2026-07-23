import ast
from pathlib import Path

import pytest

from CSE_DECISION_TRACKER import CSEDecisionTracker
from CSE_KNOWLEDGE_ENGINE import CSEKnowledgeEngine
from CSE_MEETING_ENGINE import (
    AgendaPriority,
    CSEMeetingPreparationAPI,
    CSEMeetingPreparationEngine,
    MeetingPreparationQuery,
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


def _engine() -> CSEMeetingPreparationEngine:
    documents = (
        _document(
            "minutes-meeting-01",
            "Réunion CSE janvier",
            DocumentKind.CSE_MINUTES,
            date="2025-01-15",
            family="Travail de nuit",
            instance="CSE",
        ),
        _document(
            "minutes-meeting-02",
            "Réunion CSE mars",
            DocumentKind.CSE_MINUTES,
            date="2025-03-15",
            family="Travail de nuit",
            instance="CSE",
        ),
        _document(
            "minutes-meeting-03",
            "Réunion CSE classification",
            DocumentKind.CSE_MINUTES,
            date="2025-04-15",
            family="Classification",
            instance="CSE",
        ),
        _document(
            "decision-meeting1",
            "Décision horaires clôturée",
            DocumentKind.OTHER,
            date="2025-01-15",
            family="Travail de nuit",
            nature="DECISION",
            status="CLOSED",
        ),
        _document(
            "decision-meeting2",
            "Décision horaires à suivre",
            DocumentKind.OTHER,
            date="2025-03-15",
            family="Travail de nuit",
            nature="DECISION",
            status="OPEN",
        ),
        _document(
            "commitment-due-01",
            "Engagement Direction à échéance",
            DocumentKind.OTHER,
            date="2025-03-15",
            family="Travail de nuit",
            nature="MANAGEMENT_COMMITMENT",
            status="OPEN",
            due_date="2025-05-31",
        ),
        _document(
            "commitment-future1",
            "Engagement Direction ultérieur",
            DocumentKind.OTHER,
            date="2025-03-15",
            family="Travail de nuit",
            nature="MANAGEMENT_COMMITMENT",
            status="OPEN",
            due_date="2025-12-31",
        ),
        _document(
            "elected-meeting-01",
            "Action ouverte des élus",
            DocumentKind.OTHER,
            date="2025-03-15",
            family="Travail de nuit",
            nature="ELECTED_ACTION",
            status="IN_PROGRESS",
            due_date="2025-05-15",
        ),
        _document(
            "consult-meeting-01",
            "Consultation horaires en cours",
            DocumentKind.OTHER,
            date="2025-03-15",
            family="Travail de nuit",
            nature="CONSULTATION",
            status="OPEN",
        ),
        _document(
            "agreement-meeting1",
            "Accord sur le travail de nuit",
            DocumentKind.AGREEMENT,
            date="2024-10-01",
            family="Travail de nuit",
            status="ACTIVE",
        ),
    )
    relations = (
        DocumentRelation(
            "minutes-meeting-01",
            "decision-meeting1",
            RelationKind.DECIDES_ON,
            "SYNTHETIC_METADATA",
        ),
        DocumentRelation(
            "minutes-meeting-02",
            "decision-meeting2",
            RelationKind.DECIDES_ON,
            "SYNTHETIC_METADATA",
        ),
        DocumentRelation(
            "minutes-meeting-02",
            "commitment-due-01",
            RelationKind.DISCUSSES,
            "SYNTHETIC_METADATA",
        ),
        DocumentRelation(
            "minutes-meeting-02",
            "commitment-future1",
            RelationKind.DISCUSSES,
            "SYNTHETIC_METADATA",
        ),
        DocumentRelation(
            "minutes-meeting-02",
            "elected-meeting-01",
            RelationKind.IMPLEMENTS,
            "SYNTHETIC_METADATA",
        ),
        DocumentRelation(
            "minutes-meeting-02",
            "consult-meeting-01",
            RelationKind.REFERENCES,
            "SYNTHETIC_METADATA",
        ),
        DocumentRelation(
            "minutes-meeting-01",
            "agreement-meeting1",
            RelationKind.REFERENCES,
            "SYNTHETIC_METADATA",
        ),
        DocumentRelation(
            "minutes-meeting-02",
            "agreement-meeting1",
            RelationKind.DISCUSSES,
            "SYNTHETIC_METADATA",
        ),
        DocumentRelation(
            "decision-meeting2",
            "commitment-due-01",
            RelationKind.RELATED_TO,
            "SYNTHETIC_METADATA",
        ),
    )
    navigation = DocumentNavigationService(DocumentGraph(documents, relations))
    knowledge = CSEKnowledgeEngine(navigation)
    tracker = CSEDecisionTracker(knowledge, navigation)
    return CSEMeetingPreparationEngine(knowledge, tracker, navigation)


def _query() -> MeetingPreparationQuery:
    return MeetingPreparationQuery(
        meeting_date="2025-06-01",
        subject="travail de nuit",
    )


def test_engine_implements_public_protocol() -> None:
    assert isinstance(_engine(), CSEMeetingPreparationAPI)


def test_previous_minutes_for_same_subject_are_retrieved() -> None:
    previous = _engine().previous_minutes(_query())
    assert tuple(item.document_id for item in previous) == (
        "minutes-meeting-01",
        "minutes-meeting-02",
    )
    assert all(item.document_kind == "CSE_MINUTES" for item in previous)


def test_closed_decision_is_excluded_from_open_decisions() -> None:
    decisions = _engine().open_decisions(_query())
    assert tuple(item.document_id for item in decisions) == (
        "decision-meeting2",
    )


def test_only_commitments_due_by_meeting_are_selected() -> None:
    commitments = _engine().due_commitments(_query())
    assert tuple(item.document_id for item in commitments) == (
        "commitment-due-01",
    )


def test_open_elected_actions_are_selected() -> None:
    actions = _engine().open_elected_actions(_query())
    assert tuple(item.document_id for item in actions) == (
        "elected-meeting-01",
    )
    assert actions[0].overdue is True


def test_ongoing_consultations_are_selected() -> None:
    consultations = _engine().ongoing_consultations(_query())
    assert tuple(item.document_id for item in consultations) == (
        "consult-meeting-01",
    )


def test_recurring_subjects_are_restricted_to_query_history() -> None:
    recurring = _engine().recurring_subjects(_query())
    assert len(recurring) == 1
    assert recurring[0].label == "Travail de nuit"
    assert recurring[0].occurrence_count == 2


def test_related_agreements_are_deduplicated() -> None:
    agreements = _engine().related_agreements(_query())
    assert tuple(item.document_id for item in agreements) == (
        "agreement-meeting1",
    )
    assert agreements[0].document_kind == "AGREEMENT"


def test_agenda_contains_all_expected_operational_categories() -> None:
    agenda = _engine().prepare_agenda(_query())
    assert {item.category for item in agenda} == {
        "DUE_MANAGEMENT_COMMITMENT",
        "ONGOING_CONSULTATION",
        "OPEN_DECISION",
        "OPEN_ELECTED_ACTION",
        "RECURRING_SUBJECT",
    }


def test_required_follow_up_points_are_prioritized() -> None:
    agenda = _engine().prepare_agenda(_query())
    assert agenda[0].priority is AgendaPriority.REQUIRED_FOLLOW_UP
    assert agenda[1].priority is AgendaPriority.REQUIRED_FOLLOW_UP
    assert agenda[-1].priority is AgendaPriority.NORMAL


def test_agenda_points_keep_related_agreement_identity() -> None:
    agenda = _engine().prepare_agenda(_query())
    assert all(
        item.agreement_document_ids == ("agreement-meeting1",)
        for item in agenda
    )


def test_indicators_are_computed_from_dossier_metadata() -> None:
    indicators = _engine().indicators(_query())
    assert indicators.previous_minutes_count == 2
    assert indicators.related_agreement_count == 1
    assert indicators.open_decision_count == 1
    assert indicators.due_commitment_count == 1
    assert indicators.open_elected_action_count == 1
    assert indicators.ongoing_consultation_count == 1
    assert indicators.recurring_subject_count == 1
    assert indicators.agenda_item_count == 5


def test_dossier_contains_every_preparation_view() -> None:
    dossier = _engine().prepare_dossier(_query())
    assert len(dossier.agenda) == 5
    assert len(dossier.open_decisions) == 1
    assert len(dossier.due_commitments) == 1
    assert len(dossier.open_elected_actions) == 1
    assert len(dossier.ongoing_consultations) == 1
    assert len(dossier.previous_minutes) == 2
    assert len(dossier.related_agreements) == 1


def test_dossier_is_deterministic_idempotent_and_serializable() -> None:
    engine = _engine()
    first = engine.prepare_dossier(_query())
    second = engine.prepare_dossier(_query())
    assert first == second
    assert first.to_json() == second.to_json()
    assert first.to_dict()["query"]["meeting_date"] == "2025-06-01"


def test_history_date_filter_is_respected() -> None:
    query = MeetingPreparationQuery(
        meeting_date="2025-06-01",
        subject="travail de nuit",
        history_date_from="2025-03-01",
    )
    assert tuple(
        item.document_id for item in _engine().previous_minutes(query)
    ) == ("minutes-meeting-02",)


def test_no_due_commitment_without_explicit_deadline() -> None:
    query = MeetingPreparationQuery(
        meeting_date="2025-01-01",
        subject="travail de nuit",
    )
    assert _engine().due_commitments(query) == ()


def test_invalid_meeting_date_is_rejected() -> None:
    with pytest.raises(ValueError, match="ISO date"):
        MeetingPreparationQuery(meeting_date="1 June 2025")


@pytest.mark.parametrize(
    "unsafe_subject",
    (
        r"C:\private\pv.pdf",
        "/Users/private/pv.pdf",
        "person@example.test",
        "chunk_12345678",
        "<html>document</html>",
    ),
)
def test_query_rejects_unsafe_metadata(unsafe_subject: str) -> None:
    with pytest.raises(ValueError):
        MeetingPreparationQuery(
            meeting_date="2025-06-01",
            subject=unsafe_subject,
        )


def test_dossier_exposes_metadata_only() -> None:
    serialized = _engine().prepare_dossier(_query()).to_json().lower()
    forbidden = (
        "canonical_url",
        '"content"',
        '"chunk"',
        "storage_id",
        r"c:\\",
        "/home/",
        "/users/",
        "/tmp/",
        "<html",
    )
    assert all(value not in serialized for value in forbidden)


def test_inherited_unsafe_metadata_is_rejected_before_exposure() -> None:
    documents = (
        _document(
            "minutes-unsafe-01",
            "Réunion CSE synthétique",
            DocumentKind.CSE_MINUTES,
            date="2025-01-01",
            family="Synthétique",
            instance="CSE",
        ),
        _document(
            "consult-unsafe-01",
            "/Users/private/consultation",
            DocumentKind.OTHER,
            date="2025-01-01",
            family="Synthétique",
            nature="CONSULTATION",
            status="OPEN",
        ),
    )
    relations = (
        DocumentRelation(
            "minutes-unsafe-01",
            "consult-unsafe-01",
            RelationKind.REFERENCES,
            "SYNTHETIC_METADATA",
        ),
    )
    navigation = DocumentNavigationService(DocumentGraph(documents, relations))
    knowledge = CSEKnowledgeEngine(navigation)
    engine = CSEMeetingPreparationEngine(
        knowledge,
        CSEDecisionTracker(knowledge, navigation),
        navigation,
    )
    with pytest.raises(ValueError, match="local path"):
        engine.ongoing_consultations(
            MeetingPreparationQuery(meeting_date="2025-06-01")
        )


def test_engine_has_no_network_or_semantic_dependency() -> None:
    package = Path(__file__).parents[1] / "CSE_MEETING_ENGINE"
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


def test_engine_does_not_mutate_graph_or_existing_engines() -> None:
    engine = _engine()
    before_graph = engine._navigation.statistics().to_json()
    before_knowledge = engine._knowledge_engine.build_report(
        engine._knowledge_query(_query())
    ).to_json()
    engine.prepare_dossier(_query())
    assert engine._navigation.statistics().to_json() == before_graph
    assert (
        engine._knowledge_engine.build_report(
            engine._knowledge_query(_query())
        ).to_json()
        == before_knowledge
    )
