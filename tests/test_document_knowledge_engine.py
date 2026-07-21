"""Architecture-only tests for the Document Knowledge Engine LOT 4."""

import ast
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from RETIREMENT_PENIBILITY_ENGINE.career_evidence_engine import CareerEvidenceEngine
from RETIREMENT_PENIBILITY_ENGINE.career_evidence_models import (
    CareerEvidenceItem,
    EvidenceAuthorityLevel,
    EvidenceConfidenceLevel,
    EvidenceId,
    EvidenceReference,
    EvidenceSourceType,
    EvidenceStatus,
)
from RETIREMENT_PENIBILITY_ENGINE.career_timeline_engine import CareerTimelineEngine
from RETIREMENT_PENIBILITY_ENGINE.career_timeline_models import CareerEvent, CareerEventType, EvidenceLevel
from RETIREMENT_PENIBILITY_ENGINE.document_knowledge_contract import (
    DOCUMENT_KNOWLEDGE_SAFETY_CONTRACT,
)
from RETIREMENT_PENIBILITY_ENGINE.document_knowledge_engine import DocumentKnowledgeEngine
from RETIREMENT_PENIBILITY_ENGINE.document_knowledge_models import (
    ApplicableDocument,
    ApplicablePassage,
    ContextualDocumentSet,
    DocumentPeriod,
    DocumentPriority,
    DocumentRelationship,
    DocumentRelationshipType,
    DocumentTimeline,
    DocumentValidity,
    DocumentVersion,
    KnowledgeRequest,
)
from RETIREMENT_PENIBILITY_ENGINE.document_knowledge_policy import (
    DOCUMENT_KNOWLEDGE_POLICY,
    DOCUMENT_SOURCE_IDS,
)
from RETIREMENT_PENIBILITY_ENGINE.document_provider_contract import DocumentKnowledgeProvider
from RETIREMENT_PENIBILITY_ENGINE.document_rule_models import ApplicableRule, RuleCandidate


def version(
    version_id: str,
    start: str,
    end: str | None,
    validity: DocumentValidity = DocumentValidity.SUPERSEDED,
) -> DocumentVersion:
    return DocumentVersion(
        version_id,
        "synthetic-agreement",
        f"Synthetic version {version_id}",
        DocumentPeriod(start, end),
        validity,
        version_date=start,
        provenance="synthetic-catalog",
    )


def test_public_contract_is_architecture_only_and_offline() -> None:
    contract = DOCUMENT_KNOWLEDGE_SAFETY_CONTRACT
    assert contract.status == "ARCHITECTURE_ONLY"
    assert contract.enabled is False
    assert contract.provider_implemented is False
    assert contract.corpus_access_allowed is False
    assert contract.network_allowed is False
    assert contract.pdf_allowed is False
    assert contract.artificial_intelligence_allowed is False
    assert contract.retirement_calculation_allowed is False


def test_required_models_are_immutable_and_documented() -> None:
    models = (
        KnowledgeRequest, ApplicableDocument, DocumentVersion, DocumentPeriod,
        ApplicablePassage, ContextualDocumentSet, DocumentTimeline,
        DocumentRelationship, ApplicableRule, RuleCandidate,
    )
    assert all(model.__doc__ for model in models)
    request = KnowledgeRequest("request-1", event_type="NIGHT_WORK")
    with pytest.raises(FrozenInstanceError):
        request.event_type = "RETIREMENT"


def test_night_work_selection_returns_expected_document_families_without_opening() -> None:
    report = DocumentKnowledgeEngine().select_documents(
        KnowledgeRequest("request-1", event_type="NIGHT_WORK", night_work=True)
    )
    assert report.required_document_families == (
        "INEOS_NIGHT_WORK_AGREEMENT",
        "CHEMICAL_INDUSTRY_COLLECTIVE_AGREEMENT",
        "INEOS_WORKING_TIME_AGREEMENT",
        "INEOS_END_OF_CAREER_AGREEMENT",
        "CARSAT_SOURCE",
        "INRS_SOURCE",
        "ANACT_SOURCE",
    )
    assert report.opened_document_ids == ()


def test_selection_supports_all_declared_context_criteria() -> None:
    request = KnowledgeRequest(
        "request-1",
        classification="synthetic-classification",
        job_position="synthetic-position",
        work_schedule="synthetic-schedule",
        five_shift_work=True,
        seniority_context=True,
        atmp_context=True,
        c2p_context=True,
        end_of_career_context=True,
        retirement_context=True,
    )
    families = set(DocumentKnowledgeEngine().select_documents(request).required_document_families)
    assert {
        "INEOS_WORKING_TIME_AGREEMENT", "CHEMICAL_INDUSTRY_COLLECTIVE_AGREEMENT",
        "SOCIAL_PROTECTION_SOURCE", "C2P_SOURCE", "INEOS_END_OF_CAREER_AGREEMENT",
        "CARSAT_SOURCE", "INEOS_AGREEMENTS_BIBLE",
    } <= families


def test_injected_metadata_candidates_are_grouped_by_priority() -> None:
    required = ApplicableDocument(
        "document-1", "Synthetic agreement", "agreement", "INEOS_AGREEMENTS_BIBLE",
        DocumentPriority.REQUIRED, "CONTRACTUAL", domains=("NIGHT_WORK",), provenance="synthetic",
    )
    contextual = ApplicableDocument(
        "document-2", "Synthetic context", "guide", "ANACT", DocumentPriority.CONTEXTUAL,
        "CONTEXTUAL", domains=("NIGHT_WORK",), provenance="synthetic",
    )
    report = DocumentKnowledgeEngine().select_documents(
        KnowledgeRequest("request-1", event_type="NIGHT_WORK"), (required, contextual)
    )
    assert report.selected_documents.required == (required,)
    assert report.selected_documents.contextual == (contextual,)
    assert required.individual_evidence_required is True


def test_version_resolver_selects_historical_versions() -> None:
    timeline = DocumentTimeline(
        "synthetic-agreement",
        versions=(
            version("2002", "2002-01-01", "2007-12-31"),
            version("2008", "2008-01-01", "2013-12-31"),
            version("2014", "2014-01-01", "2021-12-31"),
            version("2022", "2022-01-01", None, DocumentValidity.ACTIVE),
        ),
    )
    engine = DocumentKnowledgeEngine()
    assert engine.resolve_document_version(timeline, "2005-06-01").version_id == "2002"
    assert engine.resolve_document_version(timeline, "2010-06-01").version_id == "2008"
    assert engine.resolve_document_version(timeline, "2018-06-01").version_id == "2014"
    assert engine.resolve_document_version(timeline, "2024-06-01").version_id == "2022"


def test_repealed_version_is_never_resolved_as_applicable() -> None:
    timeline = DocumentTimeline(
        "synthetic-agreement",
        versions=(version("repealed", "2020-01-01", None, DocumentValidity.REPEALED),),
    )
    assert DocumentKnowledgeEngine().resolve_document_version(timeline, "2021-01-01") is None
    assert any(rule.rule_id == "repealed_rule_forbidden" for rule in DOCUMENT_KNOWLEDGE_POLICY)


def test_version_resolver_rejects_impossible_period() -> None:
    timeline = DocumentTimeline(
        "synthetic-agreement",
        versions=(version("invalid", "2022-01-01", "2021-01-01", DocumentValidity.ACTIVE),),
    )
    with pytest.raises(ValueError, match="Invalid period"):
        DocumentKnowledgeEngine().resolve_document_version(timeline, "2021-06-01")


def test_document_relationships_represent_version_history() -> None:
    relationship = DocumentRelationship(
        "relationship-1", "version-2022", "version-2014", DocumentRelationshipType.SUPERSEDES
    )
    timeline = DocumentTimeline("synthetic-agreement", relationships=(relationship,))
    assert timeline.relationships[0].relationship_type is DocumentRelationshipType.SUPERSEDES


def test_rule_models_are_declarative_and_require_individual_evidence() -> None:
    rule = ApplicableRule(
        "rule-1", "Synthetic collective rule", ("synthetic condition",), ("document-1",),
        DocumentPriority.HIGH, "NIGHT_WORK", DocumentPeriod("2020-01-01", None),
        DocumentValidity.ACTIVE, ("INEOS_AGREEMENTS_BIBLE",), "CONTRACTUAL", ("individual evidence",),
    )
    candidate = RuleCandidate("candidate-1", rule, ("NIGHT_WORK",), ("payslip",))
    assert candidate.official_validation_required is True
    assert candidate.rule.minimum_evidence == ("individual evidence",)


def test_provider_is_abstract_and_reuses_declared_source_ids() -> None:
    assert {
        "supported_source_ids", "find_document_candidates", "get_document_timeline",
        "find_rule_candidates",
    } <= set(DocumentKnowledgeProvider.__dict__)
    assert DOCUMENT_SOURCE_IDS == (
        "INEOS_AGREEMENTS_BIBLE", "CHEMICAL_INDUSTRY_COLLECTIVE_AGREEMENT",
        "CARSAT", "INRS", "ANACT", "CNIL", "CSE_MEMORY", "SOCIAL_PROTECTION",
    )


def test_context_builder_reuses_timeline_and_evidence_identifiers_only() -> None:
    timeline_engine = CareerTimelineEngine()
    timeline = timeline_engine.add_event(
        timeline_engine.create_empty_timeline("timeline-1", "synthetic-case"),
        CareerEvent(
            "event-1", "2020-01-01", "2020-12-31", CareerEventType.NIGHT_WORK,
            "Synthetic event", "synthetic-source", EvidenceLevel.B,
        ),
    )
    evidence_engine = CareerEvidenceEngine()
    bundle = evidence_engine.attach_evidence_to_event(
        evidence_engine.create_empty_bundle("bundle-1"),
        "event-1",
        CareerEvidenceItem(
            EvidenceReference(
                EvidenceId("evidence-1"), EvidenceSourceType.PAYSLIP,
                "Synthetic reference", "opaque-ref", "synthetic-provenance",
            ),
            EvidenceAuthorityLevel.CORROBORATING,
            EvidenceConfidenceLevel.UNKNOWN,
            EvidenceStatus.PROVIDED,
        ),
    )
    request = KnowledgeRequest("request-1", event_type="NIGHT_WORK")
    context = DocumentKnowledgeEngine().build_context(
        "context-1", timeline, bundle, "Synthetic employee question", request
    )
    assert context.timeline_id == "timeline-1"
    assert context.event_ids == ("event-1",)
    assert context.evidence_bundle_id == "bundle-1"
    assert context.evidence_ids == ("evidence-1",)
    assert context.synthetic_only is True


def test_passage_is_locator_only_without_document_text() -> None:
    passage = ApplicablePassage("passage-1", "document-1", "version-1", "article-ref", "synthetic")
    assert not hasattr(passage, "content")
    assert not hasattr(passage, "fulltext")
    assert not hasattr(passage, "pdf")


def test_policy_contains_all_required_safeguards() -> None:
    assert {rule.rule_id for rule in DOCUMENT_KNOWLEDGE_POLICY} == {
        "agreement_not_individual_evidence", "collective_agreement_defines_rule",
        "individual_evidence_required", "temporal_version_required",
        "repealed_rule_forbidden", "provenance_required",
    }


def test_lot_has_no_network_pdf_scraping_parsing_ai_or_connector_imports() -> None:
    root = Path(__file__).parents[1] / "RETIREMENT_PENIBILITY_ENGINE"
    paths = tuple(root.glob("document_*.py"))
    forbidden = {
        "aiohttp", "bs4", "html.parser", "http.client", "pypdf", "requests",
        "scrapy", "socket", "ssl", "urllib", "urllib.request", "xml.etree.ElementTree",
    }
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
        assert forbidden.isdisjoint(imports), path.name
        source = path.read_text(encoding="utf-8")
        assert "automation.official_knowledge.connectors" not in source
        assert "open(" not in source
        assert "urlopen(" not in source
