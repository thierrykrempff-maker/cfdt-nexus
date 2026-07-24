from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from SYNDICAL_REASONING_ENGINE import (
    AvailablePiece,
    EvidenceCategory,
    PayImpactLikelihood,
    QuestionPriority,
    SyndicalCaseInput,
    WorkingTimeReasoningEngine,
    WorkingTimeSituation,
)


def analyze(question: str, *, pieces=(), domains=("temps_travail",)):
    return WorkingTimeReasoningEngine().analyze(
        SyndicalCaseInput(
            question,
            available_pieces=pieces,
            suspected_domains=domains,
        )
    )


@pytest.mark.parametrize(
    ("question", "expected"),
    (
        ("Temps de travail effectif à vérifier.", WorkingTimeSituation.EFFECTIVE_WORK),
        ("Temps de pause ordinaire.", WorkingTimeSituation.BREAK),
        ("Pause interrompue avec intervention.", WorkingTimeSituation.INTERRUPTED_BREAK),
        ("Temps d'habillage et de déshabillage.", WorkingTimeSituation.DRESSING_TIME),
        ("Temps de douche juridiquement pertinent.", WorkingTimeSituation.SHOWER_TIME),
        ("Déplacement professionnel.", WorkingTimeSituation.BUSINESS_TRAVEL),
        ("Trajet domicile-travail.", WorkingTimeSituation.COMMUTE),
        ("Astreinte planifiée.", WorkingTimeSituation.ON_CALL),
        ("Intervention pendant une astreinte.", WorkingTimeSituation.ON_CALL_INTERVENTION),
        ("Trajet d'intervention.", WorkingTimeSituation.INTERVENTION_TRAVEL),
        ("Travail de nuit.", WorkingTimeSituation.NIGHT_WORK),
        ("Travail posté en équipes successives.", WorkingTimeSituation.SHIFT_WORK),
        ("Organisation 5x8.", WorkingTimeSituation.FIVE_SHIFT),
        ("Travail du dimanche.", WorkingTimeSituation.SUNDAY_WORK),
        ("Travail un jour férié.", WorkingTimeSituation.PUBLIC_HOLIDAY),
        ("Heures supplémentaires.", WorkingTimeSituation.OVERTIME),
        ("Heures complémentaires.", WorkingTimeSituation.ADDITIONAL_HOURS),
        ("Annualisation et modulation.", WorkingTimeSituation.ANNUALIZATION),
        ("Repos quotidien.", WorkingTimeSituation.DAILY_REST),
        ("Repos hebdomadaire.", WorkingTimeSituation.WEEKLY_REST),
        ("Repos compensateur.", WorkingTimeSituation.COMPENSATORY_REST),
        ("Récupération informelle.", WorkingTimeSituation.INFORMAL_RECOVERY),
        ("RTT et congés payés.", WorkingTimeSituation.RTT),
        ("Formation hors horaire.", WorkingTimeSituation.OFF_HOURS_TRAINING),
    ),
)
def test_required_situations_are_detected_prudently(question, expected):
    result = analyze(question)
    assert expected in result.situations
    assert all(item.confidence.value in {"low", "moderate"} for item in result.qualifications)


def test_close_notions_remain_distinct():
    on_call = analyze("Astreinte sans intervention.")
    assert WorkingTimeSituation.ON_CALL in on_call.situations
    assert WorkingTimeSituation.EFFECTIVE_WORK not in on_call.situations
    commute = analyze("Trajet domicile-travail habituel.")
    assert WorkingTimeSituation.COMMUTE in commute.situations
    assert WorkingTimeSituation.BUSINESS_TRAVEL not in commute.situations
    recovery = analyze("Récupération informelle.")
    assert WorkingTimeSituation.INFORMAL_RECOVERY in recovery.situations
    assert WorkingTimeSituation.COMPENSATORY_REST not in recovery.situations
    occasional = analyze("Une heure ponctuelle la nuit.")
    assert WorkingTimeSituation.OCCASIONAL_NIGHT_HOURS in occasional.situations
    assert WorkingTimeSituation.NIGHT_WORK not in occasional.situations


def test_break_requires_freedom_and_interruption_information():
    result = analyze("Pause interrompue, salarié joignable et à disposition.")
    assert WorkingTimeSituation.EFFECTIVE_WORK in result.situations
    qualification = next(
        item for item in result.qualifications
        if item.qualification is WorkingTimeSituation.BREAK
    )
    assert "liberté pendant la pause" in qualification.missing_information
    assert "interruptions réelles" in qualification.missing_information


def test_questions_have_four_levels_and_skip_available_documents():
    pieces = (
        AvailablePiece("contract", "employment_contract", "Contrat synthétique"),
        AvailablePiece("schedule", "official_schedule", "Planning synthétique"),
        AvailablePiece("clock", "timeclock", "Badgeages synthétiques"),
        AvailablePiece("kelio", "kelio_statement", "Kelio synthétique"),
        AvailablePiece("pay", "payslip", "Nibelis synthétique"),
        AvailablePiece("amendment", "amendment", "Avenant synthétique"),
    )
    questions = analyze("Pause interrompue en travail posté.", pieces=pieces).automatic_questions
    assert {item.priority for item in questions} == set(QuestionPriority)
    rendered = " ".join(item.question for item in questions)
    for already_answered in (
        "Quel est l'horaire contractuel",
        "Existe-t-il un cycle ou un planning officiel",
        "Existe-t-il des badgeages",
        "présents dans Kelio",
        "bulletin Nibelis",
        "Existe-t-il un avenant",
    ):
        assert already_answered not in rendered


def test_evidence_explains_utility_scope_and_limit():
    evidence = analyze("Écart Kelio et Nibelis.").evidence
    by_type = {item.document_type: item for item in evidence}
    assert by_type["official_schedule"].category is EvidenceCategory.ESSENTIAL
    assert by_type["employment_contract"].category is EvidenceCategory.USEFUL
    assert by_type["witness_statements"].category is EvidenceCategory.COMPLEMENTARY
    assert all(item.utility and item.can_demonstrate and item.cannot_demonstrate_alone for item in evidence)


def test_document_comparison_never_concludes_to_payroll_error():
    pieces = (
        AvailablePiece("kelio", "kelio_statement", "Kelio synthétique"),
        AvailablePiece("pay", "payslip", "Nibelis synthétique"),
    )
    result = analyze("Écart Kelio / Nibelis : prime absente.", pieces=pieces)
    comparison = next(item for item in result.comparisons if item.comparison_code == "event_nibelis")
    assert comparison.observed_differences == ("incohérence apparente à vérifier",)
    assert "erreur de saisie" in comparison.alternative_explanations
    assert "traitement potentiellement incomplet" == comparison.potential_impact
    assert all(item.calculation_performed is False for item in result.potential_pay_impacts)
    assert all(item.likelihood is not PayImpactLikelihood.CERTAIN_FROM_DATA for item in result.potential_pay_impacts)


def test_positions_are_balanced_and_strategies_are_complete():
    result = analyze("Heures supplémentaires non retrouvées dans Kelio et bulletin.")
    assert result.employee_position.arguments
    assert result.employee_position.weaknesses
    assert result.employer_position.arguments
    assert result.employer_position.risks_or_objections
    assert [item.level for item in result.strategies] == [1, 2, 3, 4, 5]
    assert all(
        item.objective and item.advantages and item.limitations and item.risks
        and item.required_pieces and item.expected_result and item.next_step_if_unsuccessful
        for item in result.strategies
    )


def test_contracts_are_immutable_and_no_payroll_amount_is_produced():
    result = analyze("Prime de poste apparemment absente.")
    with pytest.raises(FrozenInstanceError):
        result.organization.regime = "changed"
    payload = result.to_dict()
    rendered = str(payload).lower()
    assert "calculation_performed': false" in rendered
    for forbidden in ("amount", "montant calculé", "payroll_total", "taux appliqué"):
        assert forbidden not in rendered
