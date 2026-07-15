#!/usr/bin/env python
"""Tests for the LOT 5A synthetic employee-case pipeline."""

from __future__ import annotations

import inspect
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
from automation.cases.employee_case_pipeline import (  # noqa: E402
    DOCUMENT_REQUIREMENTS,
    PIPELINE_STEPS,
    EmployeeCasePipeline,
    load_fixture_cases,
)


FIXTURES = ROOT / "automation" / "cases" / "fixtures" / "employee-cases.synthetic.json"


def fixtures() -> dict[str, EmployeeCase]:
    return {item.case_id: item for item in load_fixture_cases(FIXTURES)}


def document(identifier: str, kind: DocumentType) -> EmployeeDocument:
    return EmployeeDocument(identifier, kind, f"Document fictif {identifier}", "2099-01", "fixture", "json")


def simple_case(themes: list[str] | None = None) -> EmployeeCase:
    return EmployeeCase(
        case_id="CASE_TEST_SYN",
        title="Dossier fictif",
        main_question="Quels controles mener ?",
        description="Exemple synthetique.",
        period="2099-01",
        population="population synthetique",
        detected_themes=themes or ["overtime"],
        urgent=False,
        status=CaseStatus.READY,
        documents=[
            document("DOC_PAY_SYN", DocumentType.PAYSLIP),
            document("DOC_TIME_SYN", DocumentType.TIME_STATEMENT),
            document("DOC_PLAN_SYN", DocumentType.PLANNING),
            document("DOC_AGR_SYN", DocumentType.COMPANY_AGREEMENT),
        ],
    )


def expert(name: str = "expert_paie", **overrides: object) -> ExpertAnalysis:
    values: dict[str, object] = {
        "expert": name,
        "status": ExpertStatus.COMPLETED,
        "summary": "Analyse synthetique recue.",
        "findings": ("controle commun",),
        "cited_rules_or_sources": ("source commune",),
        "documents_used": ("DOC_PAY_SYN",),
        "control_points": ("Verifier les pieces",),
        "confidence": "HIGH",
        "period": "2099-01",
    }
    values.update(overrides)
    return ExpertAnalysis(**values)


def test_fixture_contains_six_synthetic_cases() -> None:
    values = fixtures()
    assert len(values) == 6
    assert all(item.synthetic_only for item in values.values())


def test_create_and_run_valid_case() -> None:
    result = EmployeeCasePipeline().run(simple_case(), [expert()])
    assert result["final_status"] == "completed"
    assert result["diagnostic"]["calculation_performed"] is False


def test_reject_non_synthetic_case() -> None:
    case = simple_case()
    case.synthetic_only = False
    result = EmployeeCasePipeline().run(case)
    assert result["final_status"] == "blocked"
    assert result["blocked_at"] == "validate_case"


def test_reject_non_synthetic_document() -> None:
    case = simple_case()
    case.documents[0] = EmployeeDocument(
        "DOC_REAL", DocumentType.PAYSLIP, "Document interdit", "2099", "fixture", "json", synthetic_only=False
    )
    result = EmployeeCasePipeline().run(case)
    assert result["blocked_at"] == "validate_documents"


def test_reject_duplicate_document_identifier() -> None:
    case = simple_case()
    case.documents.append(document("DOC_PAY_SYN", DocumentType.PLANNING))
    result = EmployeeCasePipeline().run(case)
    assert result["final_status"] == "blocked"
    assert "Duplicate" in result["error"]


def test_document_classification() -> None:
    case = simple_case()
    result = EmployeeCasePipeline().run(case, [expert()])
    assert set(result["contexts"]["expert_paie"]["documents_present"]) == {
        "payslip", "time_statement", "planning", "company_agreement"
    }


def test_completeness_matrix_covers_six_themes_and_four_levels() -> None:
    assert set(DOCUMENT_REQUIREMENTS) == {
        "overtime", "on_call", "sickness_maintenance", "paid_leave", "classification", "holidays_and_rest"
    }
    levels = {level for requirements in DOCUMENT_REQUIREMENTS.values() for level in requirements.values()}
    assert levels == {"required", "recommended", "optional", "not_relevant"}


def test_incomplete_on_call_theme_is_blocked() -> None:
    case = fixtures()["CASE_ONCALL_SYN_002"]
    result = EmployeeCasePipeline().run(case, [expert()])
    assert "on_call" in result["diagnostic"]["themes_blocked"]
    assert result["diagnostic"]["missing_documents"]


def test_other_complete_theme_continues_when_one_theme_is_blocked() -> None:
    case = simple_case(["overtime", "classification"])
    result = EmployeeCasePipeline().run(case, [expert()])
    assert result["diagnostic"]["themes_analyzed"] == ["overtime"]
    assert result["diagnostic"]["themes_blocked"] == ["classification"]


def test_payroll_expert_context_is_minimal_and_non_calculating() -> None:
    context = EmployeeCasePipeline().run(simple_case(), [expert()])["contexts"]["expert_paie"]
    assert context["synthetic_only"] is True
    assert "question" in context and "documents_missing" in context and "requests" in context
    assert "parameter_value" not in repr(context) and "calculation" not in context


def test_legal_expert_context_is_distinct() -> None:
    contexts = EmployeeCasePipeline().run(simple_case(), [expert()])["contexts"]
    assert contexts["juriste_travail"]["requests"] != contexts["expert_paie"]["requests"]
    assert "definitive legal opinion" in contexts["juriste_travail"]["requests"][0]


def test_aggregate_two_expert_analyses_without_invention() -> None:
    result = EmployeeCasePipeline().run(simple_case(), [expert(), expert("juriste_travail")])
    diagnostic = result["diagnostic"]
    assert diagnostic["convergent_findings"] == ["controle commun"]
    assert "no new conclusion" in diagnostic["general_summary"]


def test_detect_different_expert_periods() -> None:
    result = EmployeeCasePipeline().run(
        simple_case(), [expert(), expert("juriste_travail", period="2099-02")]
    )
    assert "Experts cite different periods." in result["diagnostic"]["contradictions"]


def test_detect_expert_using_absent_document() -> None:
    result = EmployeeCasePipeline().run(simple_case(), [expert(documents_used=("DOC_UNKNOWN_SYN",))])
    assert any("absent from the case" in item for item in result["diagnostic"]["contradictions"])


def test_detect_synthetic_document_fact_contradiction() -> None:
    result = EmployeeCasePipeline().run(fixtures()["CASE_SICK_SYN_003"], [expert()])
    assert any("absence_period" in item for item in result["diagnostic"]["contradictions"])


def test_preserve_expert_refusal() -> None:
    refusal = expert(status=ExpertStatus.REFUSED, refusal_reason="Impossible de conclure.", confidence="LOW")
    result = EmployeeCasePipeline().run(simple_case(), [refusal])
    assert result["diagnostic"]["expert_refusals"] == ["Impossible de conclure."]


def test_global_confidence_uses_most_prudent_level() -> None:
    result = EmployeeCasePipeline().run(
        simple_case(), [expert(confidence="VERY_HIGH"), expert("juriste_travail", confidence="LOW")]
    )
    assert result["diagnostic"]["global_confidence"] == "LOW"
    assert "Expert confidence levels are incompatible." in result["diagnostic"]["contradictions"]


def test_sensitive_probe_is_detected_without_stored_sensitive_value() -> None:
    case = fixtures()["CASE_PRIVACY_SYN_006"]
    result = EmployeeCasePipeline().run(case)
    assert result["final_status"] == "blocked"
    assert result["blocked_at"] == "check_confidentiality"
    assert "personne.alpha" + "@" + "entreprise.invalid" not in FIXTURES.read_text(encoding="utf-8")


def test_safe_fallback_when_experts_are_unavailable() -> None:
    result = EmployeeCasePipeline().run(simple_case())
    assert result["diagnostic"]["global_confidence"] == "UNKNOWN"
    assert result["diagnostic"]["expert_refusals"] == ["Expert unavailable."]


def test_pipeline_step_order_and_statuses() -> None:
    result = EmployeeCasePipeline().run(simple_case(), [expert()])
    assert len(PIPELINE_STEPS) == 12
    assert tuple(result["steps"]) == PIPELINE_STEPS
    assert set(result["steps"].values()).issubset({"completed", "warning"})


def test_pipeline_has_no_payroll_calculation_or_external_api() -> None:
    from automation.cases import employee_case_pipeline as module

    source = inspect.getsource(module)
    assert "payroll_rule_engine" not in source
    assert "requests." not in source and "urllib" not in source
    result = EmployeeCasePipeline().run(simple_case(), [expert()])
    assert result["diagnostic"]["calculation_performed"] is False
    assert result["diagnostic"]["legal_opinion_produced"] is False


def test_lot4_referentials_are_not_written_or_imported_as_values() -> None:
    from automation.cases import employee_case_pipeline as module

    source = inspect.getsource(module)
    assert "payroll-parameters.example.json" not in source
    assert "database/payroll/referentials" not in source


def run_all() -> None:
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            func()
            print(f"OK {name}")


if __name__ == "__main__":
    run_all()
