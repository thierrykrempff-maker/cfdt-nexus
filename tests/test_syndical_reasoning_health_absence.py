from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from SYNDICAL_REASONING_ENGINE import (
    AvailablePiece,
    CompetentActor,
    HealthAbsenceReasoningEngine,
    HealthEvidenceCategory,
    HealthHypothesis,
    HealthQuestionPriority,
    HealthSituation,
    SyndicalCaseInput,
    UrgencyCategory,
    UrgencyLevel,
    needs_health_absence_reasoning,
)


def analyze(question: str, *, pieces=(), domains=("protection_sociale",)):
    return HealthAbsenceReasoningEngine().analyze(
        SyndicalCaseInput(question, available_pieces=pieces, suspected_domains=domains)
    )


@pytest.mark.parametrize(
    ("question", "expected"),
    (
        ("Arrêt maladie ordinaire.", HealthSituation.ORDINARY_SICK_LEAVE),
        ("Prolongation d'arrêt maladie.", HealthSituation.EXTENSION),
        ("Transmission tardive de l'arrêt.", HealthSituation.LATE_TRANSMISSION),
        ("Absence injustifiée potentielle.", HealthSituation.POTENTIALLY_UNJUSTIFIED_ABSENCE),
        ("Accident du travail déclaré.", HealthSituation.REPORTED_WORK_ACCIDENT),
        ("Accident de trajet déclaré.", HealthSituation.REPORTED_COMMUTING_ACCIDENT),
        ("Maladie professionnelle déclarée.", HealthSituation.REPORTED_OCCUPATIONAL_DISEASE),
        ("Rechute déclarée.", HealthSituation.REPORTED_RELAPSE),
        ("Réserves employeur.", HealthSituation.EMPLOYER_RESERVATIONS),
        ("IJSS et indemnités journalières.", HealthSituation.DAILY_ALLOWANCE),
        ("Subrogation à vérifier.", HealthSituation.SUBROGATION),
        ("Maintien de salaire.", HealthSituation.SALARY_MAINTENANCE),
        ("Garantie prévoyance.", HealthSituation.PROVIDENT_COVER),
        ("Mutuelle et dispense d'adhésion.", HealthSituation.MUTUAL_INSURANCE),
        ("Portabilité de la mutuelle.", HealthSituation.PORTABILITY),
        ("Visite de reprise.", HealthSituation.RETURN_VISIT),
        ("Visite de préreprise.", HealthSituation.PRE_RETURN_VISIT),
        ("Temps partiel thérapeutique.", HealthSituation.THERAPEUTIC_PART_TIME),
        ("Aménagement de poste.", HealthSituation.WORK_ADJUSTMENT),
        ("Inaptitude et reclassement.", HealthSituation.REPORTED_UNFITNESS),
        ("Congés et maladie : compteur de congés.", HealthSituation.LEAVE_COUNTER_IMPACT),
        ("Discrimination liée à l'état de santé.", HealthSituation.POSSIBLE_HEALTH_DISCRIMINATION),
    ),
)
def test_health_situations_are_detected_without_medical_inference(question, expected):
    result = analyze(question)
    assert expected in result.situations
    assert all(item.confidence.value in {"low", "moderate"} for item in result.qualifications)


def test_cpam_recognition_is_never_anticipated():
    result = analyze("Accident du travail déclaré, reconnaissance en attente de décision CPAM.")
    qualification = next(item for item in result.qualifications if item.hypothesis is HealthHypothesis.RECOGNITION_PENDING)
    assert qualification.competent_actor is CompetentActor.CPAM
    rendered = str(result.to_dict()).lower()
    assert "reconnaissance acquise" not in rendered
    assert "accident reconnu automatiquement" not in rendered


def test_ijss_salary_maintenance_and_subrogation_have_no_real_calculation():
    pieces = (
        AvailablePiece("a", "daily_allowance_statement", "Décompte synthétique"),
        AvailablePiece("p", "payslip", "Bulletin synthétique"),
    )
    result = analyze("IJSS, subrogation et maintien de salaire avec baisse de rémunération.", pieces=pieces)
    assert {HealthHypothesis.DAILY_ALLOWANCE_POTENTIALLY_MISSING, HealthHypothesis.SUBROGATION_TO_VERIFY, HealthHypothesis.SALARY_MAINTENANCE_POTENTIAL}.issubset({item.hypothesis for item in result.qualifications})
    assert all(item.calculation_performed is False for item in result.comparisons)
    for forbidden in ("net à payer calculé", "montant dû", "taux appliqué", "payroll_total"):
        assert forbidden not in str(result.to_dict()).lower()


def test_actor_policy_keeps_competences_separate():
    actors = {item.actor: item for item in analyze("Inaptitude et IJSS.").actors}
    assert "instruire et décider le caractère professionnel" in actors[CompetentActor.CPAM].responsibilities
    assert "rendre les avis relevant de la santé au travail" in actors[CompetentActor.OCCUPATIONAL_PHYSICIAN].responsibilities
    assert "organiser la reprise et le reclassement" in actors[CompetentActor.EMPLOYER].responsibilities
    assert "poser un diagnostic" in actors[CompetentActor.UNION_REPRESENTATIVE].prohibited_conclusions


def test_questions_have_four_priorities_and_skip_known_documents():
    pieces = (
        AvailablePiece("leave", "sick_leave_notice", "Arrêt synthétique"),
        AvailablePiece("cpam", "cpam_decision", "Décision synthétique"),
        AvailablePiece("ijss", "daily_allowance_statement", "Décompte synthétique"),
        AvailablePiece("pay", "payslip", "Bulletin synthétique"),
        AvailablePiece("opinion", "occupational_health_opinion", "Avis minimal synthétique"),
        AvailablePiece("redeployment", "redeployment_proposal", "Proposition synthétique"),
        AvailablePiece("provident", "provident_notice", "Notice synthétique"),
    )
    questions = analyze("Arrêt maladie et reprise.", pieces=pieces).automatic_questions
    assert {item.priority for item in questions} == set(HealthQuestionPriority)
    rendered = " ".join(item.question for item in questions)
    for absent in ("arrêt ou une prolongation", "décision CPAM", "décompte", "maintien, la subrogation", "visite de préreprise", "postes de reclassement", "notice et un dossier"):
        assert absent not in rendered


def test_evidence_is_minimal_metadata_only_and_has_limits():
    evidence = analyze("Arrêt maladie.").evidence
    assert {item.category for item in evidence} == set(HealthEvidenceCategory)
    assert all(item.utility and item.can_demonstrate and item.limitation for item in evidence)
    assert all(item.confidentiality == "strictly_minimal_health_metadata" for item in evidence)


def test_document_comparisons_are_prudent_and_actor_specific():
    pieces = (
        AvailablePiece("leave", "sick_leave_notice", "Arrêt synthétique"),
        AvailablePiece("pay", "payslip", "Bulletin synthétique"),
    )
    comparison = next(item for item in analyze("Arrêt maladie et bulletin.", pieces=pieces).comparisons if item.comparison_code == "leave_payslip")
    assert comparison.observed_gaps == ("écart apparent à vérifier",)
    assert comparison.actor_to_contact is CompetentActor.PAYROLL
    assert comparison.calculation_performed is False


def test_financial_and_medical_urgencies_are_distinct():
    financial = analyze("Absence totale de revenu et salaire non versé.")
    assert financial.urgency is UrgencyLevel.URGENT
    assert UrgencyCategory.FINANCIAL in financial.urgency_categories
    medical = analyze("Danger immédiat et urgence médicale déclarée.")
    assert medical.urgency is UrgencyLevel.IMMEDIATE
    assert UrgencyCategory.MEDICAL in medical.urgency_categories


def test_positions_and_five_strategies_are_complete():
    result = analyze("Inaptitude déclarée et reclassement.")
    assert result.employee_position.arguments
    assert result.employer_or_body_position.arguments
    assert result.employee_position.undecidable_points
    assert [item.level for item in result.strategies] == [1, 2, 3, 4, 5]
    assert all(item.actor and item.required_pieces and item.next_step_if_unsuccessful for item in result.strategies)


def test_contracts_are_immutable_and_detector_requires_employment_context_for_generic_word():
    result = analyze("Arrêt maladie.")
    with pytest.raises(FrozenInstanceError):
        result.urgency = UrgencyLevel.IMMEDIATE
    assert needs_health_absence_reasoning("Une maladie touche cette plante.") is False
    assert needs_health_absence_reasoning("Une maladie entraîne une absence du salarié.") is True


def test_no_detailed_health_or_personal_data_is_generated():
    rendered = str(analyze("Retour d'arrêt maladie et restriction déclarée.").to_dict()).lower()
    for forbidden in ("diagnostic détaillé", "pathologie:", "traitement médical", "numéro de sécurité sociale", "matricule", "iban", "fulltext", "chunk_id", "local_path", "c:\\"):
        assert forbidden not in rendered
