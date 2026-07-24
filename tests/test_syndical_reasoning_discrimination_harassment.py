from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from SYNDICAL_REASONING_ENGINE import (
    AdverseMeasure,
    AvailablePiece,
    CaseFact,
    DiscriminationEvidenceCategory,
    DiscriminationHarassmentReasoningEngine,
    DiscriminationQuestionPriority,
    ProtectedCriterion,
    SituationType,
    SyndicalCaseInput,
    TimelineEventKind,
    UrgencyLevel,
    needs_discrimination_harassment_reasoning,
)


def analyze(question: str, *, facts=(), pieces=(), domains=("discrimination",)):
    return DiscriminationHarassmentReasoningEngine().analyze(
        SyndicalCaseInput(
            question,
            declared_facts=tuple(CaseFact(item) for item in facts),
            available_pieces=pieces,
            suspected_domains=domains,
        )
    )


@pytest.mark.parametrize(
    ("question", "expected"),
    (
        ("Critiques répétées, humiliations et isolement.", SituationType.POSSIBLE_MORAL_HARASSMENT),
        ("Messages répétés à connotation sexuelle.", SituationType.POSSIBLE_SEXUAL_HARASSMENT),
        ("Remarques sexistes répétées liées au sexe.", SituationType.SEXIST_BEHAVIOUR),
        ("Différence de rémunération liée au sexe.", SituationType.POSSIBLE_DISCRIMINATION),
        ("Évaluation défavorable après le signalement.", SituationType.POSSIBLE_RETALIATION),
        ("Retrait de missions après un mandat syndical.", SituationType.POSSIBLE_UNION_RIGHTS_INTERFERENCE),
        ("Une remarque déplacée unique.", SituationType.ISOLATED_INAPPROPRIATE_BEHAVIOUR),
        ("Sentiment sans fait précis.", SituationType.INSUFFICIENT_FACTS),
    ),
)
def test_prudent_hypotheses_are_detected(question, expected):
    result = analyze(question)
    assert expected in {item.situation for item in result.hypotheses}
    assert all(item.confidence.value in {"low", "moderate"} for item in result.hypotheses)
    rendered = str(result.to_dict()).lower()
    assert "harcèlement établi" not in rendered
    assert "discrimination établie" not in rendered


@pytest.mark.parametrize(
    ("question", "expected"),
    (
        ("Différence liée au sexe.", ProtectedCriterion.SEX),
        ("Retrait de mission pendant la grossesse.", ProtectedCriterion.PREGNANCY),
        ("Traitement lié à l'origine.", ProtectedCriterion.ORIGIN),
        ("Refus de formation en raison de l'âge.", ProtectedCriterion.AGE),
        ("Mutation liée au handicap.", ProtectedCriterion.DISABILITY),
        ("Après un retour d'arrêt maladie, retrait de missions.", ProtectedCriterion.HEALTH),
        ("Sanction après une activité syndicale.", ProtectedCriterion.UNION_ACTIVITY),
        ("Évaluation après un mandat d'élu CSE.", ProtectedCriterion.REPRESENTATIVE_MANDATE),
        ("Représailles après un signalement.", ProtectedCriterion.REPORTING_OR_TESTIMONY),
    ),
)
def test_protected_criteria_are_only_potential_hypotheses(question, expected):
    assert expected in analyze(question).protected_criteria


@pytest.mark.parametrize(
    ("question", "expected"),
    (
        ("Sanction liée au mandat.", AdverseMeasure.SANCTION),
        ("Refus de promotion lié au sexe.", AdverseMeasure.PROMOTION_REFUSAL),
        ("Stagnation de carrière syndicale.", AdverseMeasure.CAREER_SLOWDOWN),
        ("Retrait de missions après signalement.", AdverseMeasure.DUTY_REMOVAL),
        ("Baisse de prime liée à la grossesse.", AdverseMeasure.BONUS_REDUCTION),
        ("Refus de formation lié à l'âge.", AdverseMeasure.TRAINING_REFUSAL),
        ("Isolement après mandat.", AdverseMeasure.ISOLATION),
        ("Évaluation défavorable après signalement.", AdverseMeasure.NEGATIVE_APPRAISAL),
    ),
)
def test_adverse_measures_are_structured_without_causal_conclusion(question, expected):
    assert expected in analyze(question).adverse_measures


def test_timeline_separates_declared_established_and_repeated_events():
    result = analyze(
        "Chronologie à construire.",
        facts=("Depuis janvier, critiques répétées.", "Signalement le 12/03/2026."),
    )
    assert len(result.timeline) == 2
    assert result.timeline[0].kind in {TimelineEventKind.REPEATED_FACT, TimelineEventKind.CONTINUOUS_PERIOD}
    assert result.timeline[1].kind is TimelineEventKind.REPORT
    assert all(item.event_id and item.source for item in result.timeline)


def test_comparators_are_prudent_and_capture_objective_differences():
    result = analyze("Deux salariés de même classification ont une différence de rémunération.")
    comparator = result.comparators[0]
    assert comparator.objective_differences
    assert comparator.missing_data
    assert "ne démontre pas à elle seule" in " ".join(comparator.limitations)


def test_questions_have_four_priorities_and_skip_available_material():
    pieces = (
        AvailablePiece("m1", "messages", "Messages synthétiques"),
        AvailablePiece("a1", "appraisal", "Évaluation synthétique"),
        AvailablePiece("c1", "career_history", "Carrière synthétique"),
    )
    questions = analyze("Discrimination possible après mandat.", pieces=pieces).automatic_questions
    assert {item.priority for item in questions} == set(DiscriminationQuestionPriority)
    rendered = " ".join(item.question for item in questions)
    assert "messages, courriels" not in rendered
    assert "évaluations ont-elles évolué" not in rendered
    assert "historique de carrière" not in rendered


def test_evidence_has_scope_limits_and_lawful_acquisition_warning():
    evidence = analyze("Harcèlement moral possible.").evidence
    categories = {item.category for item in evidence}
    assert categories == set(DiscriminationEvidenceCategory)
    assert all(item.can_demonstrate and item.cannot_demonstrate_alone for item in evidence)
    assert all("licite" in item.acquisition_risk for item in evidence)


def test_contradictory_positions_and_five_strategies_are_complete():
    result = analyze("Après mandat, retrait progressif de missions et isolement.")
    assert result.employee_position.arguments
    assert result.employee_position.weaknesses
    assert result.employer_position.arguments
    assert result.employer_position.foreseeable_objections
    assert [item.level for item in result.strategies] == [1, 2, 3, 4, 5]
    assert all(item.competent_actor and item.next_step_if_unsuccessful for item in result.strategies)


def test_immediate_danger_is_separated_from_legal_qualification():
    result = analyze("Violence imminente et danger immédiat.")
    assert result.urgency is UrgencyLevel.IMMEDIATE
    assert SituationType.PROTECTION_URGENCY in {item.situation for item in result.hypotheses}
    assert result.strategies[0].urgency is UrgencyLevel.IMMEDIATE


def test_no_medical_diagnosis_or_personal_data_is_generated():
    rendered = str(analyze("Retour d'arrêt maladie et retrait de missions.").to_dict()).lower()
    for forbidden in (
        "diagnostic médical",
        "dépression diagnostiquée",
        "nir",
        "iban",
        "matricule",
        "c:\\",
        "/home/",
        "fulltext",
        "chunk_id",
    ):
        assert forbidden not in rendered


def test_contracts_are_immutable_and_public_detector_does_not_trigger_on_simple_conflict():
    result = analyze("Remarque sexiste répétée.")
    with pytest.raises(FrozenInstanceError):
        result.urgency = UrgencyLevel.IMMEDIATE
    assert needs_discrimination_harassment_reasoning("Un simple conflit professionnel.") is False
    assert needs_discrimination_harassment_reasoning("Critiques répétées et isolement.") is True
