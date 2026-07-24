from __future__ import annotations

import pytest

from SYNDICAL_REASONING_ENGINE import (
    DisciplinaryQualification,
    DisciplinaryReasoningEngine,
    EvidencePriority,
    SyndicalCaseInput,
)


def analyze(question: str):
    return DisciplinaryReasoningEngine().analyze(SyndicalCaseInput(question))


@pytest.mark.parametrize(
    ("question", "expected"),
    (
        ("Un rappel à l'ordre m'est adressé.", DisciplinaryQualification.INFORMAL_REMINDER),
        ("Je conteste un avertissement.", DisciplinaryQualification.WARNING),
        ("Un blâme est annoncé.", DisciplinaryQualification.REPRIMAND),
        ("Mise à pied disciplinaire.", DisciplinaryQualification.DISCIPLINARY_SUSPENSION),
        ("Mutation disciplinaire.", DisciplinaryQualification.DISCIPLINARY_TRANSFER),
        ("Rétrogradation disciplinaire.", DisciplinaryQualification.DISCIPLINARY_DEMOTION),
        ("Licenciement pour faute simple.", DisciplinaryQualification.DISMISSAL_SIMPLE_MISCONDUCT),
        ("Licenciement pour faute grave.", DisciplinaryQualification.DISMISSAL_GROSS_MISCONDUCT),
        ("Licenciement pour faute lourde.", DisciplinaryQualification.DISMISSAL_WILFUL_MISCONDUCT),
        ("Insuffisance professionnelle.", DisciplinaryQualification.PROFESSIONAL_INSUFFICIENCY),
        ("Insuffisance de résultats.", DisciplinaryQualification.INSUFFICIENT_RESULTS),
        ("Abandon de poste allégué.", DisciplinaryQualification.JOB_ABANDONMENT),
        ("Refus d'une modification du contrat.", DisciplinaryQualification.REFUSAL_CONTRACT_CHANGE),
        ("Sanction d'un salarié protégé.", DisciplinaryQualification.PROTECTED_EMPLOYEE),
    ),
)
def test_required_qualifications_are_detected_as_provisional_candidates(question, expected):
    candidates = analyze(question).qualification_candidates
    assert expected in {item.qualification for item in candidates}
    assert all(item.provisional for item in candidates)


def test_fault_dismissal_keeps_multiple_qualifications_open():
    candidates = {
        item.qualification
        for item in analyze("Licenciement pour faute grave envisagé.").qualification_candidates
    }
    assert {
        DisciplinaryQualification.DISMISSAL_SIMPLE_MISCONDUCT,
        DisciplinaryQualification.DISMISSAL_GROSS_MISCONDUCT,
        DisciplinaryQualification.DISMISSAL_WILFUL_MISCONDUCT,
    } <= candidates


def test_questions_are_prioritized_and_cover_procedure():
    questions = analyze("Mise à pied disciplinaire contestée.").automatic_questions
    assert [item.priority for item in questions] == sorted(item.priority for item in questions)
    rendered = " ".join(item.question for item in questions)
    for expected in ("date précise des faits", "convoqué", "assisté", "témoins", "proportionnée", "règlement intérieur"):
        assert expected in rendered


def test_positions_are_independent_balanced_and_neutral():
    result = analyze("Le salarié reconnaît une faute mais conteste la sanction.")
    assert result.employee_position.favorable_arguments
    assert result.employee_position.strengths
    assert result.employee_position.weaknesses_or_points_to_prove
    assert result.employer_position.favorable_arguments
    assert result.employer_position.strengths
    assert result.employer_position.weaknesses_or_points_to_prove
    serialized = str(result.to_dict()).lower()
    assert "sanction justifiée" not in serialized
    assert "sanction injustifiée" not in serialized


def test_evidence_is_classified_and_covers_required_pieces():
    evidence = analyze("Mise à pied disciplinaire.").evidence
    by_type = {item.document_type: item for item in evidence}
    assert by_type["meeting_invitation"].priority is EvidencePriority.ESSENTIAL
    assert by_type["sanction_letter"].priority is EvidencePriority.ESSENTIAL
    assert by_type["internal_rules"].priority is EvidencePriority.ESSENTIAL
    assert by_type["witness_statements"].priority is EvidencePriority.USEFUL
    assert by_type["lawful_video_reference"].priority is EvidencePriority.COMPLEMENTARY


def test_strategies_are_progressive_and_complete():
    strategies = analyze("Avertissement contesté.").strategies
    assert [item.order for item in strategies] == list(range(1, len(strategies) + 1))
    assert [item.name for item in strategies] == [
        "Demander et sécuriser les pièces",
        "Assister et préparer le salarié",
        "Demander des explications motivées",
        "Solliciter un réexamen par la direction",
        "Contester formellement la sanction",
        "Préparer un recours adapté",
    ]
    assert all(
        item.objective and item.advantages and item.limitations
        and item.risks and item.required_pieces and item.urgency
        for item in strategies
    )


def test_protected_employee_has_specific_checks_and_strategy_without_conclusion():
    result = analyze("Licenciement disciplinaire d'un représentant du personnel salarié protégé.")
    assert result.protected_employee.protection_possible is True
    assert "inspection du travail" in " ".join(result.protected_employee.checks)
    assert "Vérifier la saisine de l'inspection du travail" in {
        item.name for item in result.strategies
    }
    assert all(item.provisional for item in result.qualification_candidates)


def test_analysis_reuses_r0_report_and_is_deterministic():
    case = SyndicalCaseInput("Insuffisance professionnelle alléguée.")
    engine = DisciplinaryReasoningEngine()
    first = engine.analyze(case)
    second = engine.analyze(case)
    assert first == second
    assert len(first.base_report.completed_steps) == 18
    assert first.base_report.analysis_limits
