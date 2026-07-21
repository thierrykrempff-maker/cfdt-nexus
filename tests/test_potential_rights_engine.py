"""Architecture-only tests for the Potential Rights Engine LOT 6."""

import ast
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest

from RETIREMENT_PENIBILITY_ENGINE.career_evidence_models import (
    CareerEvidenceItem,
    EvidenceAuthorityLevel,
    EvidenceBundle,
    EvidenceConfidenceLevel,
    EvidenceId,
    EvidenceReference,
    EvidenceSourceType,
    EvidenceStatus,
)
from RETIREMENT_PENIBILITY_ENGINE.career_timeline_models import CareerEvent, CareerEventType, CareerTimeline, EvidenceLevel
from RETIREMENT_PENIBILITY_ENGINE.document_knowledge_models import KnowledgeContext, KnowledgeRequest
from RETIREMENT_PENIBILITY_ENGINE.potential_rights_contract import (
    POTENTIAL_RIGHTS_SAFETY_CONTRACT,
    PotentialRightsEngine,
    PotentialRightsPort,
)
from RETIREMENT_PENIBILITY_ENGINE.potential_rights_models import (
    CaseMaturityIndicatorType,
    CaseMaturityLevel,
    PotentialRightCategory,
    PotentialRightsReport,
    PotentialRightsReportView,
    PotentialRightStatus,
)
from RETIREMENT_PENIBILITY_ENGINE.potential_rights_policy import (
    ALLOWED_PRUDENT_PHRASES,
    FORBIDDEN_ASSERTIVE_PHRASES,
    POTENTIAL_RIGHTS_POLICY,
)
from RETIREMENT_PENIBILITY_ENGINE.rule_reasoning_models import (
    ReasoningReport,
    ReasoningReportView,
)


def evidence(
    source_type: EvidenceSourceType = EvidenceSourceType.CARSAT_NOTIFICATION,
    status: EvidenceStatus = EvidenceStatus.VERIFIED,
    reference: str = "opaque-reference",
    provenance: str = "synthetic-evidence-source",
) -> CareerEvidenceItem:
    return CareerEvidenceItem(
        EvidenceReference(
            EvidenceId("evidence-1"), source_type, "Synthetic reference",
            reference, provenance,
        ),
        EvidenceAuthorityLevel.AUTHORITATIVE_OFFICIAL
        if source_type is EvidenceSourceType.CARSAT_NOTIFICATION
        else EvidenceAuthorityLevel.CORROBORATING,
        EvidenceConfidenceLevel.UNKNOWN,
        status,
    )


def reasoning_report(
    schemes: tuple[str, ...] = (),
    missing: tuple[str, ...] = (),
    official: bool = False,
    conflicts: tuple[str, ...] = (),
    versions: tuple[str, ...] = (),
    provenance: tuple[str, ...] = ("synthetic-reasoning-source",),
) -> ReasoningReport:
    return ReasoningReport(
        view=ReasoningReportView.EXPERT_VIEW,
        schemes_to_examine=schemes,
        main_reasons=("Synthetic factual reason",) if schemes else (),
        confirmed_elements=(),
        elements_to_verify=missing,
        missing_documents=missing,
        recommended_actions=(),
        official_validation_required=official,
        warnings=("Non-decisional synthetic report",),
        examined_rules=("Synthetic rule",) if schemes else (),
        document_versions=versions,
        conflicts=conflicts,
        provenance=provenance,
    )


def context(
    report: ReasoningReport | None = None,
    supplied_evidence: tuple[CareerEvidenceItem, ...] = (),
    with_event: bool = False,
):
    events = ()
    if with_event:
        events = (
            CareerEvent(
                "event-1", "2020-01-01", "2020-12-31", CareerEventType.NIGHT_WORK,
                "Synthetic event", "synthetic-source", EvidenceLevel.B,
            ),
        )
    timeline = CareerTimeline("timeline-1", "synthetic-case", events=events)
    bundle = EvidenceBundle("bundle-1", evidence=supplied_evidence)
    knowledge = KnowledgeContext(
        "knowledge-1", timeline.timeline_id, tuple(item.event_id for item in events),
        bundle.bundle_id, tuple(str(item.reference.evidence_id) for item in supplied_evidence),
        "Synthetic question", KnowledgeRequest("knowledge-request-1"),
    )
    return PotentialRightsEngine().create_context(
        "potential-context-1", timeline, bundle, knowledge, report or reasoning_report()
    )


def test_contract_is_architecture_only_and_non_decisional() -> None:
    contract = POTENTIAL_RIGHTS_SAFETY_CONTRACT
    assert contract.status == "ARCHITECTURE_ONLY"
    assert contract.enabled is False
    assert contract.entitlement_attribution_allowed is False
    assert contract.legal_decision_allowed is False
    assert contract.network_allowed is False
    assert contract.retirement_calculation_allowed is False
    assert contract.c2p_calculation_allowed is False
    assert contract.percentage_scoring_allowed is False


def test_public_methods_are_declared() -> None:
    assert {
        "create_context", "identify_potential_rights", "calculate_case_maturity",
        "identify_missing_requirements", "identify_official_validations",
        "generate_recommendations", "analyze", "generate_report",
    } <= set(PotentialRightsPort.__dict__)


def test_empty_case_has_unknown_maturity_and_no_rights() -> None:
    analysis = PotentialRightsEngine().analyze(context())
    assert analysis.potential_rights == ()
    assert analysis.maturity.level is CaseMaturityLevel.UNKNOWN


def test_complete_documentary_case_is_complete() -> None:
    report = reasoning_report(
        schemes=("Long Career",), versions=("Synthetic version (ACTIVE)",)
    )
    analysis = PotentialRightsEngine().analyze(
        context(report, (evidence(),), with_event=True)
    )
    assert analysis.maturity.level is CaseMaturityLevel.COMPLETE
    assert analysis.potential_rights[0].category is PotentialRightCategory.LONG_CAREER


def test_partial_case_is_partially_complete() -> None:
    report = reasoning_report(
        schemes=("C2P Early Retirement",),
        missing=("Synthetic official document",),
        official=True,
    )
    non_official = evidence(EvidenceSourceType.PAYSLIP, EvidenceStatus.PROVIDED)
    analysis = PotentialRightsEngine().analyze(context(report, (non_official,), with_event=True))
    assert analysis.maturity.level is CaseMaturityLevel.PARTIALLY_COMPLETE


def test_case_with_scheme_but_no_evidence_is_insufficient() -> None:
    report = reasoning_report(schemes=("Progressive Retirement",))
    analysis = PotentialRightsEngine().analyze(context(report))
    assert analysis.maturity.level is CaseMaturityLevel.INSUFFICIENT


def test_missing_evidence_and_official_validation_are_explicit() -> None:
    report = reasoning_report(
        schemes=("Career Correction",), missing=("Synthetic career statement",), official=True
    )
    analysis = PotentialRightsEngine().analyze(context(report))
    assert analysis.missing_requirements[0].description == "Synthetic career statement"
    assert analysis.official_validations[0].completed is False
    assert analysis.potential_rights[0].status is PotentialRightStatus.OFFICIAL_VALIDATION_REQUIRED


def test_contradictory_evidence_remains_visible() -> None:
    report = reasoning_report(schemes=("ATMP Recognition",), conflicts=("Synthetic contradiction",))
    analysis = PotentialRightsEngine().analyze(
        context(report, (evidence(status=EvidenceStatus.CONTRADICTED),))
    )
    assert analysis.potential_rights[0].status is PotentialRightStatus.CONFLICTED
    indicator = next(
        item for item in analysis.maturity.indicators
        if item.indicator_type is CaseMaturityIndicatorType.CONTRADICTORY_EVIDENCE
    )
    assert indicator.state.value == "CONFLICTED"


def test_recommendations_use_prudent_actions() -> None:
    report = reasoning_report(
        schemes=("Legal Retirement Age",), missing=("Synthetic document",), official=True
    )
    analysis = PotentialRightsEngine().analyze(context(report))
    actions = tuple(item.action for item in analysis.recommendations)
    assert "Fournir ou faire vérifier la référence documentaire manquante." in actions
    assert "Demander une validation à l’organisme officiel compétent." in actions


def test_employee_view_is_clear_and_contains_no_technical_details() -> None:
    engine = PotentialRightsEngine()
    case = context(reasoning_report(schemes=("Ineos End Of Career Measure",), official=True))
    report = engine.generate_report(case, engine.analyze(case), PotentialRightsReportView.EMPLOYEE_VIEW)
    assert report.schemes_to_examine == ("Ineos End Of Career",)
    assert report.official_validation_required if hasattr(report, "official_validation_required") else report.summary.official_validation_required
    assert report.rules == report.evidence == report.document_versions == ()
    assert all(phrase.lower() not in repr(report).lower() for phrase in FORBIDDEN_ASSERTIVE_PHRASES)


def test_expert_view_contains_indicators_provenance_and_redacts_secrets() -> None:
    unsafe = evidence(reference=r"C:\private\secret.pdf", provenance="token=synthetic-secret")
    report_input = reasoning_report(
        schemes=("Night Work Prevention",),
        versions=(r"C:\private\agreement.txt",),
        conflicts=("diagnosis secret",),
        provenance=(r"C:\private\source.json",),
    )
    engine = PotentialRightsEngine()
    case = context(report_input, (unsafe,), with_event=True)
    report = engine.generate_report(case, engine.analyze(case), PotentialRightsReportView.EXPERT_VIEW)
    rendered = repr(report)
    assert report.rules == ("Synthetic rule",)
    assert report.detailed_indicators
    assert report.score_justification
    assert "C:\\private" not in rendered
    assert "token=" not in rendered
    assert "diagnosis" not in rendered.lower()
    assert "[REDACTED]" in rendered


def test_all_maturity_indicators_are_explainable() -> None:
    maturity = PotentialRightsEngine().calculate_case_maturity(
        context(reasoning_report(schemes=("Other Scheme",)))
    )
    assert {item.indicator_type for item in maturity.indicators} == set(CaseMaturityIndicatorType)
    assert all(item.explanation and item.provenance for item in maturity.indicators)


def test_category_catalog_and_policy_are_complete() -> None:
    assert len(PotentialRightCategory) == 12
    assert {item.value for item in CaseMaturityLevel} == {
        "COMPLETE", "MOSTLY_COMPLETE", "PARTIALLY_COMPLETE", "INSUFFICIENT", "UNKNOWN",
    }
    assert len(POTENTIAL_RIGHTS_POLICY) == 8
    assert len(ALLOWED_PRUDENT_PHRASES) == 3


def test_models_are_immutable_and_have_no_calculation_outputs() -> None:
    analysis = PotentialRightsEngine().analyze(context())
    with pytest.raises(FrozenInstanceError):
        analysis.maturity.level = CaseMaturityLevel.COMPLETE
    names = {item.name for item in fields(PotentialRightsReport)}
    assert "retirement_date" not in names
    assert "pension_amount" not in names
    assert "c2p_points" not in names
    assert "percentage" not in names


def test_lot_has_no_network_document_ai_or_connector_imports() -> None:
    root = Path(__file__).parents[1] / "RETIREMENT_PENIBILITY_ENGINE"
    paths = tuple(root.glob("potential_rights_*.py"))
    forbidden = {
        "aiohttp", "bs4", "html.parser", "http.client", "openai", "pypdf",
        "requests", "scrapy", "socket", "ssl", "urllib", "urllib.request",
        "xml.etree.ElementTree",
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
        assert "open(" not in source
