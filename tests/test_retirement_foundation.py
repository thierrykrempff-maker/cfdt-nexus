"""Architecture tests for the Retirement & Penibility LOT 1 foundation."""

import ast
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest

from RETIREMENT_PENIBILITY_ENGINE import (
    C2PInformation,
    EVIDENCE_MATRIX,
    EVIDENCE_WEIGHTING_RULES,
    REASONING_PROTOCOL,
    RETIREMENT_FOUNDATION_CONTRACT,
    RETIREMENT_SOURCE_POLICY,
    CareerPeriod,
    EmployeeCareer,
    EvidenceGrade,
    EvidenceItem,
    ExposurePeriod,
    FiveShiftPeriod,
    MissingInformation,
    NightWorkPeriod,
    RetirementArchitectureOnlyError,
    RetirementPlatform,
    RetirementQuestion,
    RetirementReport,
    RetirementRequest,
    RetirementScenario,
)


def synthetic_request() -> RetirementRequest:
    career = EmployeeCareer(
        career_id="synthetic-case-001",
        generation_year=1970,
        career_periods=(CareerPeriod("period-1", "2000-01-01", "2001-12-31"),),
        night_work_periods=(NightWorkPeriod("night-1", "period-1", None, None),),
        five_shift_periods=(FiveShiftPeriod("shift-1", "period-1", None, None),),
        exposure_periods=(ExposurePeriod("exposure-1", "synthetic_factor", None, None, "synthetic_declaration"),),
        c2p_information=C2PInformation("unknown"),
        synthetic_only=True,
    )
    evidence = EvidenceItem("evidence-1", "employee_supplied_data", "employee_declaration", EvidenceGrade.D)
    return RetirementRequest(
        "request-1",
        RetirementQuestion("question-1", "Question synthétique", "synthetic-case-001", explicit_consent=True),
        career,
        (evidence,),
    )


def test_public_imports_and_contract_are_architecture_only() -> None:
    assert RETIREMENT_FOUNDATION_CONTRACT.status == "ARCHITECTURE_ONLY"
    assert RETIREMENT_FOUNDATION_CONTRACT.enabled is False
    assert RETIREMENT_FOUNDATION_CONTRACT.performs_calculation is False
    assert RETIREMENT_FOUNDATION_CONTRACT.performs_simulation is False
    assert RETIREMENT_FOUNDATION_CONTRACT.network_allowed is False
    assert RETIREMENT_FOUNDATION_CONTRACT.real_documents_allowed is False


def test_required_models_exist_are_documented_and_immutable() -> None:
    model_types = (
        EmployeeCareer,
        CareerPeriod,
        NightWorkPeriod,
        FiveShiftPeriod,
        ExposurePeriod,
        C2PInformation,
        RetirementScenario,
        EvidenceItem,
        MissingInformation,
        RetirementReport,
    )
    assert all(model.__doc__ for model in model_types)
    period = CareerPeriod("period-1", None, None)
    with pytest.raises(FrozenInstanceError):
        period.period_id = "changed"


def test_models_have_no_computed_retirement_date_field() -> None:
    model_types = (EmployeeCareer, RetirementScenario, RetirementReport)
    names = {item.name for model in model_types for item in fields(model)}
    assert "retirement_date" not in names
    assert "departure_date" not in names
    assert "pension_amount" not in names


def test_source_hierarchy_is_complete_and_ordered() -> None:
    assert tuple(item.priority for item in RETIREMENT_SOURCE_POLICY) == tuple(range(1, 11))
    assert tuple(item.source_id for item in RETIREMENT_SOURCE_POLICY) == (
        "carsat",
        "assurance_retraite_cnav",
        "code_securite_sociale",
        "code_travail",
        "c2p",
        "ineos_agreements",
        "inrs",
        "anact",
        "social_report",
        "employee_supplied_data",
    )
    assert all(
        item.authoritative or item.secondary or item.contextual or item.never_sufficient_alone
        for item in RETIREMENT_SOURCE_POLICY
    )
    assert RETIREMENT_SOURCE_POLICY[0].never_sufficient_alone is True
    assert RETIREMENT_SOURCE_POLICY[8].aggregate_only is True


def test_reasoning_protocol_has_fifteen_non_calculating_steps() -> None:
    assert len(REASONING_PROTOCOL) == 15
    assert tuple(item.ordinal for item in REASONING_PROTOCOL) == tuple(range(1, 16))
    assert REASONING_PROTOCOL[12].blocking_when_missing is True
    assert "without inferring eligibility" in REASONING_PROTOCOL[8].description


def test_evidence_matrix_contains_levels_a_to_d() -> None:
    assert {item.grade for item in EVIDENCE_MATRIX} == set(EvidenceGrade)
    weights = {grade: max(item.weight for item in EVIDENCE_MATRIX if item.grade is grade) for grade in EvidenceGrade}
    assert weights[EvidenceGrade.A] > weights[EvidenceGrade.B] > weights[EvidenceGrade.C] > weights[EvidenceGrade.D]
    assert any("must never be added" in rule for rule in EVIDENCE_WEIGHTING_RULES)
    assert any(item.document_type == "employee_declaration" and not item.authoritative for item in EVIDENCE_MATRIX)


def test_platform_exposes_declarations_and_refuses_execution() -> None:
    platform = RetirementPlatform()
    assert platform.status == "ARCHITECTURE_ONLY"
    assert platform.enabled is False
    assert platform.source_policy() is RETIREMENT_SOURCE_POLICY
    assert platform.reasoning_protocol() is REASONING_PROTOCOL
    assert platform.evidence_matrix()[0] is EVIDENCE_MATRIX
    with pytest.raises(RetirementArchitectureOnlyError, match="ARCHITECTURE_ONLY"):
        platform.assess(synthetic_request())


def test_foundation_has_no_network_scraping_or_download_imports() -> None:
    root = Path(__file__).parents[1] / "RETIREMENT_PENIBILITY_ENGINE"
    forbidden = {
        "aiohttp",
        "bs4",
        "html.parser",
        "http.client",
        "requests",
        "scrapy",
        "socket",
        "ssl",
        "urllib",
        "urllib.request",
        "xml.etree.ElementTree",
    }
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
        assert forbidden.isdisjoint(imports), path.name


def test_foundation_creates_no_connector_or_shared_component_dependency() -> None:
    root = Path(__file__).parents[1] / "RETIREMENT_PENIBILITY_ENGINE"
    source = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))
    assert "automation.official_knowledge.connectors" not in source
    assert "urlopen" not in source
    assert "RetirementPlatform" in source
