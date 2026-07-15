#!/usr/bin/env python
"""Tests for LOT 5B employee-case data reports."""

from __future__ import annotations

from copy import deepcopy
import inspect
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from automation.cases.employee_case import (  # noqa: E402
    CaseStatus,
    DocumentType,
    EmployeeCase,
    EmployeeDocument,
    ExpertAnalysis,
    ExpertStatus,
)
from automation.cases.employee_case_pipeline import EmployeeCasePipeline  # noqa: E402
from automation.cases.employee_case_report import (  # noqa: E402
    REPORT_VERSION,
    SECTION_ORDER,
    EmployeeCaseReportGenerator,
)


def document(identifier: str, kind: DocumentType) -> EmployeeDocument:
    return EmployeeDocument(identifier, kind, f"Piece fictive {identifier}", "2099-01", "fixture", "json")


def case(complete: bool = True) -> EmployeeCase:
    documents = [
        document("DOC_PAY_SYN", DocumentType.PAYSLIP),
        document("DOC_TIME_SYN", DocumentType.TIME_STATEMENT),
        document("DOC_PLAN_SYN", DocumentType.PLANNING),
    ]
    if complete:
        documents.append(document("DOC_AGR_SYN", DocumentType.COMPANY_AGREEMENT))
    return EmployeeCase(
        case_id="CASE_REPORT_SYN",
        title="Dossier rapport fictif",
        main_question="Quels controles documentaires mener ?",
        description="Situation fictive.",
        period="2099-01",
        population="population synthetique",
        detected_themes=["overtime"],
        urgent=False,
        status=CaseStatus.READY,
        documents=documents,
        employee_information={"contexte": "fait synthetique sans valeur"},
    )


def analysis(expert: str = "expert_paie", **overrides: object) -> ExpertAnalysis:
    values: dict[str, object] = {
        "expert": expert,
        "status": ExpertStatus.COMPLETED,
        "summary": "Controle documentaire synthetique.",
        "findings": ("Constat fourni par l'expert.",),
        "cited_rules_or_sources": ("Source fictive a verifier",),
        "documents_used": ("DOC_PAY_SYN",),
        "control_points": ("Rapprocher les pieces",),
        "risks": ("Piece a confirmer",),
        "confidence": "HIGH",
        "limits": ("Analyse limitee aux pieces transmises",),
        "period": "2099-01",
    }
    values.update(overrides)
    return ExpertAnalysis(**values)


def pipeline_result(complete: bool = True, analyses: list[ExpertAnalysis] | None = None) -> dict[str, object]:
    result = EmployeeCasePipeline().run(case(complete), analyses if analyses is not None else [analysis()])
    result["title"] = "Dossier rapport fictif"
    result["confidentiality"] = "restricted"
    result["assumptions"] = ["Documents declares synthetiques"]
    return result


def generate(result: dict[str, object] | None = None, analyses: list[ExpertAnalysis] | None = None) -> dict[str, object]:
    expert_values = analyses if analyses is not None else [analysis(), analysis("juriste_travail")]
    return EmployeeCaseReportGenerator().generate(result or pipeline_result(analyses=expert_values), expert_values)


def test_generate_complete_report() -> None:
    report = generate()
    assert report["report_type"] == "employee_case_analysis"
    assert len(report["sections"]) == 12
    assert report["sections"]["header"]["case_id"] == "CASE_REPORT_SYN"
    json.dumps(report, ensure_ascii=False)


def test_section_order_is_stable() -> None:
    report = generate()
    assert tuple(report["section_order"]) == SECTION_ORDER
    assert tuple(report["sections"]) == SECTION_ORDER


def test_report_with_blocked_theme_and_documents() -> None:
    analyses = [analysis(refusal_reason="Piece obligatoire absente.", confidence="LOW")]
    report = generate(pipeline_result(False, analyses), analyses)
    assert report["sections"]["executive_summary"]["blocked_themes"] == ["overtime"]
    assert "company_agreement" in report["sections"]["documents"]["blocking"]
    assert report["sections"]["theme_analysis"][0]["status"] == "blocked"


def test_report_with_missing_expert() -> None:
    report = EmployeeCaseReportGenerator().generate(pipeline_result(), [])
    assert report["sections"]["payroll_expert_summary"]["available"] is False
    assert report["sections"]["legal_expert_summary"]["status"] == "unavailable"


def test_report_preserves_contradictions() -> None:
    analyses = [analysis(), analysis("juriste_travail", period="2099-02")]
    result = pipeline_result(analyses=analyses)
    report = generate(result, analyses)
    assert "Experts cite different periods." in report["sections"]["contradictions"]["items"]


def test_low_confidence_explains_weaknesses() -> None:
    analyses = [analysis(confidence="LOW", refusal_reason="Impossible de conclure.")]
    report = generate(pipeline_result(False, analyses), analyses)
    confidence = report["sections"]["confidence"]
    assert confidence["global_level"] == "LOW"
    assert confidence["weakening_elements"]
    assert confidence["causes"]


def test_expert_summary_keeps_the_most_prudent_confidence() -> None:
    analyses = [analysis(confidence="VERY_HIGH"), analysis(confidence="LOW")]
    report = generate(pipeline_result(analyses=analyses), analyses)
    assert report["sections"]["payroll_expert_summary"]["confidence"] == "LOW"


def test_employee_view_is_simple_and_without_rules() -> None:
    view = generate()["employee_view"]
    assert view["audience"] == "employee"
    assert "rules_or_sources" not in view
    assert "control_points" not in view
    assert set(view) == {"audience", "header", "summary", "situation", "documents", "themes", "actions", "confidence", "limits"}


def test_expert_view_contains_sources_controls_and_limits() -> None:
    view = generate()["expert_view"]
    assert view["audience"] == "expert"
    assert view["rules_or_sources"] == ["Source fictive a verifier"]
    assert view["control_points"] == ["Rapprocher les pieces"]
    assert view["confidence"] and view["limits"]


def test_metadata_and_confidentiality() -> None:
    report = generate()
    metadata = report["sections"]["metadata"]
    assert metadata["report_version"] == REPORT_VERSION
    assert metadata["pipeline_version"] == "LOT_5A_V1"
    assert metadata["protocol_version"] == "PAYROLL_REASONING_PROTOCOL_V1"
    assert metadata["confidentiality"] == "restricted"
    assert metadata["synthetic_only"] is True


def test_generator_does_not_mutate_inputs() -> None:
    result = pipeline_result()
    analyses = [analysis()]
    original_result = deepcopy(result)
    original_analyses = deepcopy(analyses)
    EmployeeCaseReportGenerator().generate(result, analyses)
    assert result == original_result
    assert analyses == original_analyses


def test_generator_never_calculates_or_invokes_experts() -> None:
    from automation.cases import employee_case_report as module

    source = inspect.getsource(module)
    assert "payroll_rule_engine" not in source
    assert "analyze_payroll_query" not in source
    assert "requests." not in source and "urllib" not in source
    report = generate()
    assert report["calculation_performed"] is False
    assert report["expert_invocation_performed"] is False


def run_all() -> None:
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            func()
            print(f"OK {name}")


if __name__ == "__main__":
    run_all()
