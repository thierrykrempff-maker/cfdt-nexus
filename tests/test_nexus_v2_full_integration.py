import ast
from pathlib import Path

import pytest

from CSE_DECISION_TRACKER import CSEDecisionTracker
from CSE_KNOWLEDGE_ENGINE import CSEKnowledgeEngine
from CSE_MEETING_ENGINE import (
    CSEMeetingPreparationEngine,
    MeetingPreparationQuery,
)
from DOCUMENT_INTELLIGENCE_CENTER import (
    DocumentIngestionService,
    DocumentKind,
    DocumentMetadataInput,
    ExplicitDocumentLink,
    MetadataStatus,
    RelationKind,
)


V2_PACKAGES = (
    "DOCUMENT_INTELLIGENCE_CENTER",
    "CSE_KNOWLEDGE_ENGINE",
    "CSE_DECISION_TRACKER",
    "CSE_MEETING_ENGINE",
)


def _metadata(
    document_id: str,
    title: str,
    kind: DocumentKind,
    *,
    date: str,
    family: str | None = None,
    nature: str | None = None,
    status: MetadataStatus = MetadataStatus.ACTIVE,
    instance: str | None = None,
    due_date: str | None = None,
    links: tuple[ExplicitDocumentLink, ...] = (),
) -> DocumentMetadataInput:
    return DocumentMetadataInput(
        pseudonymous_id=document_id,
        document_kind=kind,
        normalized_title=title,
        logical_provenance="SYNTHETIC_INTEGRATION_METADATA",
        document_date=date,
        effective_to=due_date,
        family=family,
        nature=nature,
        status=status,
        instance=instance,
        explicit_links=links,
    )


def _inputs() -> tuple[DocumentMetadataInput, ...]:
    agreement = _metadata(
        "agreement-flow-01",
        "Accord travail de nuit",
        DocumentKind.AGREEMENT,
        date="2024-01-01",
        family="Travail de nuit",
        nature="AGREEMENT",
    )
    open_decision = _metadata(
        "decision-flow-open",
        "Décision ouverte sur les horaires",
        DocumentKind.OTHER,
        date="2025-01-15",
        family="Travail de nuit",
        nature="DECISION",
        status=MetadataStatus("OPEN"),
    )
    closed_decision = _metadata(
        "decision-flow-done",
        "Décision clôturée sur les horaires",
        DocumentKind.OTHER,
        date="2025-01-15",
        family="Travail de nuit",
        nature="DECISION",
        status=MetadataStatus("CLOSED"),
    )
    commitment = _metadata(
        "commitment-flow-1",
        "Engagement Direction à échéance",
        DocumentKind.OTHER,
        date="2025-01-15",
        family="Travail de nuit",
        nature="MANAGEMENT_COMMITMENT",
        status=MetadataStatus("OPEN"),
        due_date="2025-05-31",
    )
    elected_action = _metadata(
        "elected-flow-001",
        "Action des élus en cours",
        DocumentKind.OTHER,
        date="2025-01-15",
        family="Travail de nuit",
        nature="ELECTED_ACTION",
        status=MetadataStatus("IN_PROGRESS"),
        due_date="2025-05-15",
    )
    consultation = _metadata(
        "consult-flow-001",
        "Consultation en cours",
        DocumentKind.OTHER,
        date="2025-01-15",
        family="Travail de nuit",
        nature="CONSULTATION",
        status=MetadataStatus("OPEN"),
    )
    first_minutes = _metadata(
        "minutes-flow-001",
        "PV CSE janvier",
        DocumentKind.CSE_MINUTES,
        date="2025-01-15",
        family="Travail de nuit",
        nature="MEETING_MINUTES",
        instance="CSE",
        links=(
            ExplicitDocumentLink(
                "agreement-flow-01",
                RelationKind.REFERENCES,
            ),
            ExplicitDocumentLink(
                "decision-flow-open",
                RelationKind.DECIDES_ON,
            ),
            ExplicitDocumentLink(
                "decision-flow-done",
                RelationKind.DECIDES_ON,
            ),
            ExplicitDocumentLink(
                "commitment-flow-1",
                RelationKind.DISCUSSES,
            ),
            ExplicitDocumentLink(
                "elected-flow-001",
                RelationKind.IMPLEMENTS,
            ),
            ExplicitDocumentLink(
                "consult-flow-001",
                RelationKind.REFERENCES,
            ),
        ),
    )
    second_minutes = _metadata(
        "minutes-flow-002",
        "PV CSE mars",
        DocumentKind.CSE_MINUTES,
        date="2025-03-15",
        family="Travail de nuit",
        nature="MEETING_MINUTES",
        instance="CSE",
        links=(
            ExplicitDocumentLink(
                "agreement-flow-01",
                RelationKind.DISCUSSES,
            ),
        ),
    )
    orphan = _metadata(
        "orphan-flow-0001",
        "Document orphelin synthétique",
        DocumentKind.STUDY,
        date="2025-02-01",
        family="Autre sujet",
        nature="STUDY",
    )
    return (
        agreement,
        open_decision,
        closed_decision,
        commitment,
        elected_action,
        consultation,
        first_minutes,
        second_minutes,
        orphan,
    )


def _stack(*, reverse: bool = False):
    service = DocumentIngestionService()
    values = tuple(reversed(_inputs())) if reverse else _inputs()
    result = service.ingest_batch(values)
    assert result.rejected == 0
    navigation = __import__(
        "DOCUMENT_INTELLIGENCE_CENTER",
        fromlist=["DocumentNavigationService"],
    ).DocumentNavigationService(service.graph)
    knowledge = CSEKnowledgeEngine(navigation)
    tracker = CSEDecisionTracker(knowledge, navigation)
    meeting = CSEMeetingPreparationEngine(knowledge, tracker, navigation)
    query = MeetingPreparationQuery(
        meeting_date="2025-06-01",
        subject="travail de nuit",
    )
    return service, navigation, knowledge, tracker, meeting, query


def test_full_flow_places_open_decision_in_preparation_dossier() -> None:
    *_unused, meeting, query = _stack()
    dossier = meeting.prepare_dossier(query)
    assert tuple(item.document_id for item in dossier.open_decisions) == (
        "decision-flow-open",
    )


def test_due_management_commitment_appears_in_agenda() -> None:
    *_unused, meeting, query = _stack()
    categories = {item.category for item in meeting.prepare_agenda(query)}
    assert "DUE_MANAGEMENT_COMMITMENT" in categories


def test_closed_decision_is_not_reported_as_open() -> None:
    *_unused, meeting, query = _stack()
    identifiers = {
        item.document_id for item in meeting.open_decisions(query)
    }
    assert "decision-flow-done" not in identifiers


def test_recurring_subject_comes_from_explicit_metadata() -> None:
    *_unused, meeting, query = _stack()
    subjects = meeting.recurring_subjects(query)
    assert tuple(item.label for item in subjects) == ("Travail de nuit",)
    assert subjects[0].occurrence_count == 2


def test_agreement_linked_to_minutes_is_joined_to_meeting() -> None:
    *_unused, meeting, query = _stack()
    assert tuple(
        item.document_id for item in meeting.related_agreements(query)
    ) == ("agreement-flow-01",)


def test_ongoing_consultation_is_counted() -> None:
    *_unused, meeting, query = _stack()
    assert meeting.indicators(query).ongoing_consultation_count == 1


def test_forbidden_inherited_metadata_is_rejected_before_exposure() -> None:
    service = DocumentIngestionService()
    values = (
        _metadata(
            "consult-unsafe-v2",
            "/Users/private/consultation",
            DocumentKind.OTHER,
            date="2025-01-01",
            family="Synthétique",
            nature="CONSULTATION",
            status=MetadataStatus("OPEN"),
        ),
        _metadata(
            "minutes-unsafe-v2",
            "PV synthétique",
            DocumentKind.CSE_MINUTES,
            date="2025-01-01",
            family="Synthétique",
            nature="MEETING_MINUTES",
            instance="CSE",
            links=(
                ExplicitDocumentLink(
                    "consult-unsafe-v2",
                    RelationKind.REFERENCES,
                ),
            ),
        ),
    )
    service.ingest_batch(values)
    navigation = __import__(
        "DOCUMENT_INTELLIGENCE_CENTER",
        fromlist=["DocumentNavigationService"],
    ).DocumentNavigationService(service.graph)
    knowledge = CSEKnowledgeEngine(navigation)
    meeting = CSEMeetingPreparationEngine(
        knowledge,
        CSEDecisionTracker(knowledge, navigation),
        navigation,
    )
    with pytest.raises(ValueError, match="local path"):
        meeting.prepare_dossier(
            MeetingPreparationQuery(meeting_date="2025-06-01")
        )


def test_identical_executions_produce_identical_json() -> None:
    *_unused, meeting, query = _stack()
    assert (
        meeting.prepare_dossier(query).to_json()
        == meeting.prepare_dossier(query).to_json()
    )


def test_insertion_order_does_not_change_final_result() -> None:
    *_first, first_meeting, first_query = _stack()
    *_second, second_meeting, second_query = _stack(reverse=True)
    assert (
        first_meeting.prepare_dossier(first_query).to_json()
        == second_meeting.prepare_dossier(second_query).to_json()
    )


def test_orphan_document_does_not_disrupt_engines() -> None:
    _service, navigation, *_rest, meeting, query = _stack()
    assert "orphan-flow-0001" in navigation.orphan_document_ids()
    assert meeting.prepare_dossier(query).indicators.agenda_item_count > 0


def test_cross_package_imports_use_only_public_package_apis() -> None:
    root = Path(__file__).parents[1]
    violations: list[str] = []
    for package_name in V2_PACKAGES[1:]:
        for source_file in (root / package_name).glob("*.py"):
            tree = ast.parse(source_file.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom) or not node.module:
                    continue
                for dependency in V2_PACKAGES:
                    if node.module.startswith(f"{dependency}."):
                        violations.append(
                            f"{source_file.name}:{node.lineno}:{node.module}"
                        )
    assert violations == []


def test_documentary_layer_does_not_import_business_layers() -> None:
    root = Path(__file__).parents[1]
    forbidden = {
        "CSE_DECISION_TRACKER",
        "CSE_KNOWLEDGE_ENGINE",
        "CSE_MEETING_ENGINE",
        "NEXUS_CORE",
        "NEXUS_RUNTIME_INTEGRATION",
        "automation.experts",
    }
    imports: set[str] = set()
    for source_file in (root / "DOCUMENT_INTELLIGENCE_CENTER").glob("*.py"):
        tree = ast.parse(source_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
            elif isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
    assert all(
        not any(name == item or name.startswith(f"{item}.") for item in forbidden)
        for name in imports
    )


def test_v2_modules_have_no_forbidden_runtime_or_network_imports() -> None:
    root = Path(__file__).parents[1]
    forbidden_roots = {
        "NEXUS_CORE",
        "NEXUS_RUNTIME_INTEGRATION",
        "aiohttp",
        "httpx",
        "openai",
        "requests",
        "socket",
        "urllib",
    }
    imported: set[str] = set()
    for package_name in V2_PACKAGES:
        for source_file in (root / package_name).glob("*.py"):
            tree = ast.parse(source_file.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module.split(".")[0])
                elif isinstance(node, ast.Import):
                    imported.update(
                        alias.name.split(".")[0] for alias in node.names
                    )
    assert imported.isdisjoint(forbidden_roots)


def test_v2_modules_have_no_implicit_clock_random_uuid_or_environment() -> None:
    root = Path(__file__).parents[1]
    forbidden_calls = {
        "datetime.now",
        "date.today",
        "os.getenv",
        "time.time",
        "uuid.uuid1",
        "uuid.uuid4",
    }
    found: set[str] = set()
    for package_name in V2_PACKAGES:
        for source_file in (root / package_name).glob("*.py"):
            tree = ast.parse(source_file.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                function = node.func
                if isinstance(function, ast.Attribute) and isinstance(
                    function.value,
                    ast.Name,
                ):
                    name = f"{function.value.id}.{function.attr}"
                    if name in forbidden_calls:
                        found.add(name)
    assert found == set()
