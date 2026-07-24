from __future__ import annotations

from SYNDICAL_REASONING_ENGINE import (
    AvailablePiece,
    ChangeDimension,
    ContractChangeReasoningEngine,
    EvidencePriority,
    SyndicalCaseInput,
)


def analyze(question: str, *, pieces=()):
    return ContractChangeReasoningEngine().analyze(
        SyndicalCaseInput(question, available_pieces=pieces)
    )


def test_hours_change_keeps_competing_qualifications_open():
    result = analyze("Modification importante des horaires et du planning.")
    dimensions = {item.dimension for item in result.qualification_candidates}
    assert ChangeDimension.CONTRACT in dimensions
    assert ChangeDimension.WORKING_CONDITIONS in dimensions
    assert all(item.provisional for item in result.qualification_candidates)


def test_day_to_shift_detects_hours_team_and_contract_questions():
    result = analyze("Passage de jour vers une équipe postée avec changement d'équipe.")
    assert {
        ChangeDimension.DAY_TO_SHIFT,
        ChangeDimension.TEAM,
        ChangeDimension.WORKING_HOURS,
    } <= set(result.detected_dimensions)
    questions = " ".join(item.question for item in result.automatic_questions)
    assert "travail posté" in questions
    assert "horaires" in questions


def test_known_contract_and_amendment_remove_redundant_questions():
    pieces = (
        AvailablePiece("contract", "employment_contract", "Contrat synthétique"),
        AvailablePiece("amendment", "amendment", "Avenant synthétique"),
    )
    questions = analyze("Changement de poste", pieces=pieces).automatic_questions
    rendered = " ".join(item.question for item in questions)
    assert "Que prévoit précisément le contrat" not in rendered
    assert "Existe-t-il un avenant" not in rendered


def test_questions_are_prioritized_and_deterministic():
    first = analyze("Mutation interne et modification de rémunération.")
    second = analyze("Mutation interne et modification de rémunération.")
    assert first.automatic_questions == second.automatic_questions
    assert [item.priority for item in first.automatic_questions] == sorted(
        item.priority for item in first.automatic_questions
    )


def test_five_strategies_are_progressive():
    strategies = analyze("Suppression de poste dans une réorganisation.").strategies
    assert [item.order for item in strategies] == [1, 2, 3, 4, 5]
    assert [item.name for item in strategies] == [
        "Obtenir toutes les informations",
        "Demander et comparer les documents",
        "Rencontrer la direction",
        "Préparer une intervention CSE",
        "Préparer un recours adapté",
    ]
    assert all(item.advantages and item.limitations and item.risks for item in strategies)


def test_employee_and_employer_positions_are_balanced():
    result = analyze("Réorganisation avec modification de rémunération.")
    assert result.employee_position.favorable_arguments
    assert result.employee_position.weaknesses_or_points_to_prove
    assert result.employer_position.favorable_arguments
    assert result.employer_position.weaknesses_or_points_to_prove
    assert "pouvoir d'organisation" in " ".join(
        result.employer_position.favorable_arguments
    )


def test_evidence_is_classified_by_priority():
    evidence = analyze(
        "Passage en équipe postée avec modification de rémunération et réorganisation."
    ).evidence
    by_type = {item.document_type: item for item in evidence}
    assert by_type["employment_contract"].priority is EvidencePriority.ESSENTIAL
    assert by_type["schedule"].priority is EvidencePriority.ESSENTIAL
    assert by_type["payslip"].priority is EvidencePriority.ESSENTIAL
    assert by_type["cse_minutes"].priority is EvidencePriority.ESSENTIAL
    assert by_type["organization_chart"].priority is EvidencePriority.COMPLEMENTARY


def test_analysis_reuses_complete_r0_report():
    result = analyze("Changement de classification et de coefficient.")
    assert len(result.base_report.completed_steps) == 18
    assert result.base_report.action_options
    assert result.base_report.analysis_limits
