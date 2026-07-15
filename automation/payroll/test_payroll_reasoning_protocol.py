#!/usr/bin/env python
"""Tests for LOT 4G payroll reasoning protocol."""

from __future__ import annotations

import inspect
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from automation.payroll import payroll_reasoning_protocol as protocol  # noqa: E402


def complete_question(**overrides: object) -> protocol.PayrollQuestion:
    values: dict[str, object] = {
        "question": "Verifier les heures supplementaires.",
        "question_type": "controle",
        "subject": "heures_supplementaires",
        "scope": protocol.QuestionScope.EMPLOYEE,
        "population": "salarie concerne",
        "period": "juin 2026",
        "payroll_period": "paie de juin 2026",
        "available_documents": frozenset(
            {protocol.DocumentCategory.KELIO, protocol.DocumentCategory.PAYSLIP, protocol.DocumentCategory.AGREEMENT}
        ),
        "sources": ("accord applicable", "bulletin synthetique"),
        "rules": ("regle candidate",),
        "variables": ("heures constatees",),
        "kelio_counters": ("compteur candidat",),
        "nibelis_rubrics": ("rubrique candidate",),
        "parameters": ("parametre candidat",),
    }
    values.update(overrides)
    return protocol.PayrollQuestion(**values)


def test_each_protocol_step_exists_in_required_order() -> None:
    assert len(protocol.PROTOCOL_STEPS) == 12
    assert protocol.PROTOCOL_STEPS == tuple(protocol.ReasoningStep)
    assert protocol.PROTOCOL_STEPS[0] is protocol.ReasoningStep.UNDERSTAND_REQUEST
    assert protocol.PROTOCOL_STEPS[-1] is protocol.ReasoningStep.PRODUCE_RESPONSE


def test_all_confidence_levels_are_defined() -> None:
    assert {level.value for level in protocol.ConfidenceLevel} == {
        "VERY_HIGH", "HIGH", "MEDIUM", "LOW", "UNKNOWN"
    }


def test_all_document_categories_are_known() -> None:
    assert {item.value for item in protocol.DocumentCategory} == {
        "agreement", "collective_agreement", "labour_code", "kelio", "nibelis",
        "payslip", "hr_letter", "manager_decision", "other",
    }


def test_refusal_policy_handles_missing_period_source_and_population() -> None:
    question = complete_question(period=None, population=None, sources=())
    codes = {item.code for item in protocol.apply_refusal_policy(question, protocol.evidence_for(question.subject))}
    assert {"missing_period", "missing_population", "missing_source"}.issubset(codes)


def test_refusal_policy_handles_missing_indispensable_documents() -> None:
    question = complete_question(available_documents=frozenset())
    assessment = protocol.assess(question)
    assert {"missing_payslip", "missing_kelio", "missing_agreement"}.issubset(
        {item.code for item in assessment.refusals}
    )
    assert not assessment.can_conclude


def test_refusal_policy_handles_contradictory_documents() -> None:
    assessment = protocol.assess(complete_question(contradictory_documents=True))
    assert "contradictory_documents" in {item.code for item in assessment.refusals}
    assert protocol.render_response(complete_question(), assessment, protocol.Audience.EMPLOYEE)["message"] == (
        "Impossible de conclure avec certitude."
    )


def test_employee_response_is_distinct_from_expert_response() -> None:
    question = complete_question()
    assessment = protocol.assess(question)
    employee = protocol.render_response(question, assessment, protocol.Audience.EMPLOYEE)
    expert = protocol.render_response(question, assessment, protocol.Audience.EXPERT)
    assert employee != expert
    assert "explanation" in employee and "retrieval" not in employee
    assert "sources" in expert and "control_points" in expert and "limits" in expert


def test_confidence_depends_on_documents_sources_referentials_and_missing_data() -> None:
    assert protocol.assess(complete_question()).confidence is protocol.ConfidenceLevel.VERY_HIGH
    assert protocol.assess(complete_question(missing_information=("validation manager",))).confidence is protocol.ConfidenceLevel.MEDIUM
    assert protocol.assess(complete_question(sources=())).confidence is protocol.ConfidenceLevel.LOW
    unknown = complete_question(question="", subject="")
    assert protocol.assess(unknown).confidence is protocol.ConfidenceLevel.UNKNOWN


def test_subject_evidence_sequence_is_explicit() -> None:
    assert protocol.requested_evidence_sequence("heures_supplementaires") == (
        "planning", "Kelio", "bulletin", "accord"
    )


def test_assessment_lists_all_retrieval_families() -> None:
    assessment = protocol.assess(complete_question())
    assert set(assessment.retrieval) == {
        "rules", "variables", "kelio_counters", "nibelis_rubrics", "parameters"
    }


def test_assessment_exposes_understanding_and_control_dimensions() -> None:
    assessment = protocol.assess(complete_question(urgent=True))
    assert assessment.understanding == {
        "question_type": "controle",
        "subject": "heures_supplementaires",
        "scope": "employee",
        "population": "salarie concerne",
        "period": "juin 2026",
        "payroll_period": "paie de juin 2026",
        "urgent": True,
    }
    assert set(assessment.controls) == {"coherences", "incoherences", "missing_data", "risks"}


def test_no_step_triggers_a_calculation_or_imports_the_engine() -> None:
    source = inspect.getsource(protocol)
    assert "payroll_rule_engine" not in source
    assert "automation.experts" not in source
    assessment = protocol.assess(complete_question())
    assert not any(key in assessment.as_dict() for key in ("amount", "result", "calculated_value"))


def run_all() -> None:
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            func()
            print(f"OK {name}")


if __name__ == "__main__":
    run_all()
