"""Offline architecture tests for the Career Evidence Engine LOT 3."""

import ast
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from RETIREMENT_PENIBILITY_ENGINE.career_document_search_contract import CareerDocumentSearchProvider
from RETIREMENT_PENIBILITY_ENGINE.career_evidence_contract import (
    CAREER_EVIDENCE_SAFETY_CONTRACT,
    CareerEvidenceEngine,
)
from RETIREMENT_PENIBILITY_ENGINE.career_evidence_models import (
    CareerEvidenceItem,
    DocumentPassageReference,
    DocumentSearchRequest,
    DocumentSearchResult,
    EvidenceAuthorityLevel,
    EvidenceClaim,
    EvidenceClaimType,
    EvidenceConfidenceLevel,
    EvidenceConflict,
    EvidenceGap,
    EvidenceId,
    EvidenceReference,
    EvidenceRelationType,
    EvidenceReportView,
    EvidenceResolutionState,
    EvidenceSourceType,
    EvidenceStatus,
)
from RETIREMENT_PENIBILITY_ENGINE.career_evidence_policy import CAREER_EVIDENCE_POLICY
from RETIREMENT_PENIBILITY_ENGINE.career_evidence_resolver import CareerEvidenceResolver


def evidence(
    evidence_id: str,
    source_type: EvidenceSourceType = EvidenceSourceType.PAYSLIP,
    authority: EvidenceAuthorityLevel = EvidenceAuthorityLevel.CORROBORATING,
    status: EvidenceStatus = EvidenceStatus.PROVIDED,
    title: str = "Synthetic reference",
    reference: str = "opaque-reference",
    provenance: str = "synthetic-source",
) -> CareerEvidenceItem:
    return CareerEvidenceItem(
        EvidenceReference(
            EvidenceId(evidence_id),
            source_type,
            title,
            reference,
            provenance,
            version_date="2020-01-01",
        ),
        authority,
        EvidenceConfidenceLevel.UNKNOWN,
        status,
    )


def test_public_imports_and_safety_contract() -> None:
    assert CAREER_EVIDENCE_SAFETY_CONTRACT.status == "ARCHITECTURE_ONLY"
    assert CAREER_EVIDENCE_SAFETY_CONTRACT.enabled is False
    assert CAREER_EVIDENCE_SAFETY_CONTRACT.real_documents_allowed is False
    assert CAREER_EVIDENCE_SAFETY_CONTRACT.network_allowed is False
    assert CAREER_EVIDENCE_SAFETY_CONTRACT.retirement_calculation_allowed is False
    assert CAREER_EVIDENCE_SAFETY_CONTRACT.c2p_calculation_allowed is False


def test_required_enums_are_complete_and_distinct() -> None:
    assert len(EvidenceSourceType) == 19
    assert {item.value for item in EvidenceAuthorityLevel} == {
        "AUTHORITATIVE_OFFICIAL", "AUTHORITATIVE_EMPLOYER", "CONTRACTUAL",
        "CORROBORATING", "CONTEXTUAL", "DECLARATIVE_ONLY",
    }
    assert "HIGH" in {item.value for item in EvidenceConfidenceLevel}
    assert {item.value for item in EvidenceStatus} >= {
        "PROVIDED", "VERIFIED", "UNVERIFIED", "CONTRADICTED", "SUPERSEDED",
        "EXPIRED", "MISSING", "RESTRICTED", "REJECTED",
    }


def test_models_are_immutable() -> None:
    item = evidence("evidence-1")
    with pytest.raises(FrozenInstanceError):
        item.status = EvidenceStatus.VERIFIED


def test_create_empty_graph() -> None:
    bundle = CareerEvidenceEngine().create_empty_bundle("bundle-1")
    assert bundle.bundle_id == "bundle-1"
    assert bundle.evidence == bundle.relations == bundle.conflicts == ()
    assert bundle.synthetic_only is True


def test_attach_evidence_to_existing_event_identifier() -> None:
    engine = CareerEvidenceEngine()
    empty = engine.create_empty_bundle("bundle-1")
    attached = engine.attach_evidence_to_event(empty, "event-from-lot-2", evidence("evidence-1"))
    assert empty.evidence == ()
    assert attached.relations[0].target_kind == "CAREER_EVENT"
    assert attached.relations[0].target_id == "event-from-lot-2"
    assert attached.relations[0].relation_type is EvidenceRelationType.SUPPORTS


def test_attach_evidence_to_existing_period_identifier() -> None:
    engine = CareerEvidenceEngine()
    bundle = engine.attach_evidence_to_period(
        engine.create_empty_bundle("bundle-1"), "period-from-lot-2", evidence("evidence-1")
    )
    assert bundle.relations[0].target_kind == "CAREER_PERIOD"
    assert bundle.relations[0].target_id == "period-from-lot-2"


def test_multiple_evidence_items_and_provenance_are_preserved() -> None:
    engine = CareerEvidenceEngine()
    bundle = engine.create_empty_bundle("bundle-1")
    bundle = engine.attach_evidence_to_event(bundle, "event-1", evidence("payslip", provenance="synthetic-payroll"))
    bundle = engine.attach_evidence_to_event(
        bundle,
        "event-1",
        evidence("schedule", EvidenceSourceType.WORK_SCHEDULE, provenance="synthetic-schedule"),
        EvidenceRelationType.CORROBORATES,
    )
    assert len(bundle.evidence) == 2
    assert {item.reference.provenance for item in bundle.evidence} == {
        "synthetic-payroll", "synthetic-schedule",
    }


def test_collective_rule_remains_distinct_from_individual_fact() -> None:
    agreement = evidence(
        "agreement", EvidenceSourceType.INEOS_AGREEMENT, EvidenceAuthorityLevel.CONTRACTUAL
    )
    payslip = evidence("payslip")
    assert CareerEvidenceResolver.classify_item(agreement) == "COLLECTIVE_RULE"
    assert CareerEvidenceResolver.classify_item(payslip) == "INDIVIDUAL_EVIDENCE"
    assert any(rule.rule_id == "collective_rule_not_individual_fact" for rule in CAREER_EVIDENCE_POLICY)


def test_employee_declaration_alone_requires_official_validation() -> None:
    engine = CareerEvidenceEngine()
    declaration = evidence(
        "declaration",
        EvidenceSourceType.EMPLOYEE_DECLARATION,
        EvidenceAuthorityLevel.DECLARATIVE_ONLY,
    )
    bundle = engine.attach_evidence_to_event(engine.create_empty_bundle("bundle-1"), "event-1", declaration)
    resolution = engine.resolve_evidence_state(bundle, "event-1")
    assert resolution.state is EvidenceResolutionState.REQUIRES_OFFICIAL_VALIDATION


def test_incompatible_claims_are_detected_and_both_evidence_items_remain() -> None:
    engine = CareerEvidenceEngine()
    bundle = engine.create_empty_bundle("bundle-1")
    bundle = engine.attach_evidence_to_event(bundle, "event-1", evidence("left"))
    bundle = engine.attach_evidence_to_event(bundle, "event-1", evidence("right"))
    bundle = engine.register_claim(
        bundle,
        EvidenceClaim("claim-left", "CAREER_EVENT", "event-1", EvidenceClaimType.INDIVIDUAL_FACT, "Schedule A", (EvidenceId("left"),)),
    )
    bundle = engine.register_claim(
        bundle,
        EvidenceClaim("claim-right", "CAREER_EVENT", "event-1", EvidenceClaimType.INDIVIDUAL_FACT, "Schedule B", (EvidenceId("right"),)),
    )
    resolution = engine.resolve_evidence_state(bundle, "event-1")
    assert resolution.state is EvidenceResolutionState.CONFLICTED
    assert {str(item.reference.evidence_id) for item in resolution.ordered_evidence} == {"left", "right"}
    assert len(resolution.conflicts) == 1


def test_explicit_conflict_and_superseded_document_remain_traceable() -> None:
    engine = CareerEvidenceEngine()
    old = evidence("old", status=EvidenceStatus.SUPERSEDED)
    current = evidence("current")
    bundle = engine.attach_evidence_to_event(engine.create_empty_bundle("bundle-1"), "event-1", old)
    bundle = engine.attach_evidence_to_event(bundle, "event-1", current)
    bundle = engine.register_conflict(
        bundle,
        EvidenceConflict("conflict-1", "event-1", (EvidenceId("old"), EvidenceId("current")), (), "Synthetic incompatibility"),
    )
    resolution = engine.resolve_evidence_state(bundle, "event-1")
    assert len(resolution.ordered_evidence) == 2
    assert any(item.status is EvidenceStatus.SUPERSEDED for item in resolution.ordered_evidence)
    assert resolution.state is EvidenceResolutionState.CONFLICTED


def test_remove_is_logical_and_does_not_delete_provenance() -> None:
    engine = CareerEvidenceEngine()
    bundle = engine.attach_evidence_to_event(engine.create_empty_bundle("bundle-1"), "event-1", evidence("evidence-1"))
    removed = engine.remove_evidence(bundle, EvidenceId("evidence-1"))
    assert len(removed.evidence) == 1
    assert removed.evidence[0].status is EvidenceStatus.REJECTED
    assert removed.evidence[0].reference.provenance == "synthetic-source"


def test_missing_evidence_is_linked_without_inferring_absence_of_right() -> None:
    engine = CareerEvidenceEngine()
    bundle = engine.register_missing_evidence(
        engine.create_empty_bundle("bundle-1"),
        EvidenceGap("gap-1", "CAREER_EVENT", "event-1", EvidenceSourceType.C2P_NOTIFICATION, "Synthetic notification missing"),
    )
    assert bundle.gaps[0].subject_id == "event-1"
    assert bundle.relations[0].relation_type is EvidenceRelationType.MISSING_FOR
    assert any(rule.rule_id == "absence_is_not_disproof" for rule in CAREER_EVIDENCE_POLICY)


def test_document_passage_is_a_reference_not_document_content() -> None:
    engine = CareerEvidenceEngine()
    bundle = engine.attach_evidence_to_event(engine.create_empty_bundle("bundle-1"), "event-1", evidence("agreement"))
    passage = DocumentPassageReference("passage-1", "document-1", "article-ref", provenance="synthetic-index")
    bundle = engine.attach_document_passage(bundle, EvidenceId("agreement"), passage)
    assert bundle.passages == (passage,)
    assert not hasattr(passage, "fulltext")
    assert not hasattr(passage, "document_content")


def test_employee_view_is_clear_and_hides_internal_and_sensitive_details() -> None:
    engine = CareerEvidenceEngine()
    medical = evidence(
        "internal-medical-id",
        EvidenceSourceType.MEDICAL_OR_ATMP_NOTIFICATION,
        EvidenceAuthorityLevel.AUTHORITATIVE_OFFICIAL,
        title="diagnosis secret",
        reference=r"C:\private\medical.pdf",
        provenance="synthetic-medical-source",
    )
    bundle = engine.attach_evidence_to_event(engine.create_empty_bundle("bundle-1"), "internal-event-id", medical)
    report = engine.generate_evidence_report(bundle, "internal-event-id", EvidenceReportView.EMPLOYEE_VIEW)
    rendered = repr(report)
    assert report.subject_id == "career subject"
    assert "Restricted documentary reference" in report.supporting_evidence
    assert "internal-medical-id" not in rendered
    assert "C:\\private" not in rendered
    assert "diagnosis" not in rendered.lower()


def test_expert_view_includes_sanitized_sources_conflicts_and_reasons() -> None:
    engine = CareerEvidenceEngine()
    item = evidence("evidence-1", reference=r"C:\secret\source.pdf", provenance="synthetic-provenance")
    bundle = engine.attach_evidence_to_event(engine.create_empty_bundle("bundle-1"), "event-1", item)
    report = engine.generate_evidence_report(bundle, "event-1", EvidenceReportView.EXPERT_VIEW)
    rendered = repr(report)
    assert report.resolution_reasons
    assert report.provenance == ("synthetic-provenance",)
    assert "C:\\secret" not in rendered
    assert "[REDACTED]" in rendered


def test_document_search_contract_is_abstract_and_metadata_only() -> None:
    expected = {
        "search_ineos_agreements", "search_collective_agreement", "search_carsat_sources",
        "search_c2p_sources", "search_document_passages",
    }
    assert expected <= set(CareerDocumentSearchProvider.__dict__)
    request = DocumentSearchRequest(event_type="NIGHT_WORK", keywords=("synthetic",))
    result = DocumentSearchResult("document-1", "Synthetic", "agreement", None, None, "unscored", "unknown", "synthetic")
    assert request.event_type == "NIGHT_WORK"
    assert not hasattr(result, "content")


def test_graph_relations_catalog_is_complete() -> None:
    assert {item.value for item in EvidenceRelationType} == {
        "SUPPORTS", "PARTIALLY_SUPPORTS", "CONTRADICTS", "REPLACES",
        "CORROBORATES", "CONTEXTUALIZES", "REQUIRES", "MISSING_FOR",
        "DERIVED_FROM", "GOVERNED_BY",
    }


def test_lot_has_no_network_scraping_download_or_retirement_engine_imports() -> None:
    root = Path(__file__).parents[1] / "RETIREMENT_PENIBILITY_ENGINE"
    paths = tuple(root.glob("career_evidence_*.py")) + (root / "career_document_search_contract.py",)
    forbidden = {
        "aiohttp", "bs4", "html.parser", "http.client", "requests", "scrapy",
        "socket", "ssl", "urllib", "urllib.request", "xml.etree.ElementTree",
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
        assert "urlopen(" not in source
