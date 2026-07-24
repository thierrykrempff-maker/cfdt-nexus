"""Prudent R1E reasoning without diagnosis, real payroll calculation or CPAM decision."""

from __future__ import annotations

import unicodedata

from .engine import SyndicalReasoningEngine
from .health_absence_actors import health_actor_policy
from .health_absence_articulation import articulate_health_domains
from .health_absence_comparison import compare_health_documents
from .health_absence_evidence import health_absence_evidence
from .health_absence_models import (
    CompetentActor,
    HealthAbsenceAnalysis,
    HealthHypothesis,
    HealthPosition,
    HealthQualification,
    HealthSituation,
    UrgencyCategory,
)
from .health_absence_questions import build_health_questions
from .health_absence_strategies import build_health_strategies
from .health_absence_timeline import build_health_timeline
from .models import ConfidenceLevel, SyndicalCaseInput, UrgencyLevel


SITUATION_MARKERS = {
    HealthSituation.ORDINARY_SICK_LEAVE: ("arret maladie", "absence maladie"),
    HealthSituation.EXTENSION: ("prolongation",),
    HealthSituation.LATE_TRANSMISSION: ("transmission tardive", "envoye en retard"),
    HealthSituation.POTENTIALLY_UNJUSTIFIED_ABSENCE: ("absence injustifiee", "justification discutee", "justification est discutee"),
    HealthSituation.REPORTED_WORK_ACCIDENT: ("accident du travail", "at/mp"),
    HealthSituation.REPORTED_COMMUTING_ACCIDENT: ("accident de trajet",),
    HealthSituation.REPORTED_OCCUPATIONAL_DISEASE: ("maladie professionnelle",),
    HealthSituation.REPORTED_RELAPSE: ("rechute",),
    HealthSituation.CPAM_REVIEW: ("instruction cpam", "decision cpam", "reconnaissance en attente"),
    HealthSituation.EMPLOYER_RESERVATIONS: ("reserves employeur", "emet des reserves"),
    HealthSituation.DAILY_ALLOWANCE: ("ijss", "indemnites journalieres", "paiement cpam"),
    HealthSituation.SUBROGATION: ("subrogation",),
    HealthSituation.SALARY_MAINTENANCE: ("maintien de salaire", "maintien employeur", "maintien et prevoyance"),
    HealthSituation.WAITING_PERIOD: ("carence",),
    HealthSituation.EMPLOYER_SUPPLEMENT: ("complement employeur",),
    HealthSituation.PROVIDENT_COVER: ("prevoyance", "incapacite", "invalidite"),
    HealthSituation.MUTUAL_INSURANCE: ("mutuelle", "dispense d adhesion"),
    HealthSituation.PORTABILITY: ("portabilite",),
    HealthSituation.RETURN_TO_WORK: ("reprise", "retour d arret"),
    HealthSituation.PRE_RETURN_VISIT: ("visite de prereprise",),
    HealthSituation.RETURN_VISIT: ("visite de reprise",),
    HealthSituation.THERAPEUTIC_PART_TIME: ("temps partiel therapeutique",),
    HealthSituation.WORK_ADJUSTMENT: ("amenagement de poste", "amenagement d horaire"),
    HealthSituation.DECLARED_RESTRICTION: ("restriction",),
    HealthSituation.REPORTED_UNFITNESS: ("inaptitude",),
    HealthSituation.REDEPLOYMENT: ("reclassement",),
    HealthSituation.FAMILY_LEAVE: ("conge maternite", "conge paternite", "conge parental", "proche aidant", "presence parentale", "enfant malade"),
    HealthSituation.LEAVE_COUNTER_IMPACT: ("conges et maladie", "compteur de conges", "report de conges"),
    HealthSituation.SENIORITY_IMPACT: ("anciennete",),
    HealthSituation.POTENTIAL_PAY_IMPACT: ("baisse de remuneration", "bulletin", "salaire non verse", "prime"),
    HealthSituation.POSSIBLE_HEALTH_DISCRIMINATION: ("discrimination", "etat de sante", "handicap"),
}

HEALTH_DOMAINS = {"protection_sociale", "maladie", "absence", "sante", "inaptitude", "at_mp", "reclassement"}
DIRECT_CONTEXT = ("arret maladie", "accident du travail", "accident de trajet", "maladie professionnelle", "ijss", "subrogation", "inaptitude", "reclassement", "temps partiel therapeutique", "visite de reprise", "prevoyance", "mutuelle", "portabilite")


def needs_health_absence_reasoning(case_or_question: SyndicalCaseInput | str) -> bool:
    if isinstance(case_or_question, SyndicalCaseInput):
        text = _case_text(case_or_question)
        if set(case_or_question.suspected_domains).intersection(HEALTH_DOMAINS):
            return True
    else:
        text = _normalize(str(case_or_question))
    if any(marker in text for marker in DIRECT_CONTEXT):
        return True
    health_word = any(marker in text for marker in ("maladie", "sante", "handicap"))
    employment_context = any(marker in text for marker in ("absence", "travail", "employeur", "salarie", "poste", "paie", "conge"))
    return health_word and employment_context


class HealthAbsenceReasoningEngine:
    def __init__(self, base_engine: SyndicalReasoningEngine | None = None) -> None:
        self._base_engine = base_engine or SyndicalReasoningEngine()

    def analyze(self, case: SyndicalCaseInput, *, scenario_code: str | None = None) -> HealthAbsenceAnalysis:
        if not isinstance(case, SyndicalCaseInput):
            raise TypeError("case must be a SyndicalCaseInput")
        text = _case_text(case)
        situations = _situations(text)
        urgency, urgency_categories = _urgency(case, text)
        confidence = ConfidenceLevel.MODERATE if case.established_facts and len(case.available_pieces) >= 2 else ConfidenceLevel.LOW
        qualifications = _qualifications(case, situations, urgency, confidence)
        comparisons = compare_health_documents(case)
        employee, other = _positions(case)
        return HealthAbsenceAnalysis(
            self._base_engine.analyze(case),
            situations,
            build_health_timeline(case),
            qualifications,
            health_actor_policy(),
            build_health_questions(case, urgent=urgency in {UrgencyLevel.URGENT, UrgencyLevel.IMMEDIATE}),
            health_absence_evidence(),
            comparisons,
            employee,
            other,
            urgency_categories,
            build_health_strategies(urgency),
            articulate_health_domains(case),
            tuple(sorted(set(case.missing_information) | {"dates exactes", "statut des transmissions", "décision administrative disponible", "traitement de paie observé"})),
            urgency,
            confidence,
            scenario_code,
        )


def _situations(text: str) -> tuple[HealthSituation, ...]:
    selected = {situation for situation, markers in SITUATION_MARKERS.items() if any(marker in text for marker in markers)}
    if not selected:
        selected.add(HealthSituation.ORDINARY_SICK_LEAVE)
    return tuple(sorted(selected, key=lambda item: item.value))


def _qualifications(case, situations, urgency, confidence):
    selected = set(situations)
    hypotheses = set()
    if HealthSituation.ORDINARY_SICK_LEAVE in selected:
        hypotheses.add(HealthHypothesis.JUSTIFIED_SICK_LEAVE)
    if HealthSituation.LATE_TRANSMISSION in selected:
        hypotheses.add(HealthHypothesis.TRANSMISSION_TO_VERIFY)
    if HealthSituation.POTENTIALLY_UNJUSTIFIED_ABSENCE in selected:
        hypotheses.add(HealthHypothesis.POTENTIALLY_UNJUSTIFIED_ABSENCE)
    if selected.intersection({HealthSituation.REPORTED_WORK_ACCIDENT, HealthSituation.REPORTED_COMMUTING_ACCIDENT, HealthSituation.REPORTED_OCCUPATIONAL_DISEASE}):
        hypotheses.add(HealthHypothesis.RECOGNITION_PENDING)
    if HealthSituation.REPORTED_COMMUTING_ACCIDENT in selected:
        hypotheses.add(HealthHypothesis.COMMUTING_ACCIDENT_POSSIBLE)
    if HealthSituation.REPORTED_OCCUPATIONAL_DISEASE in selected:
        hypotheses.add(HealthHypothesis.OCCUPATIONAL_DISEASE_PENDING)
    if HealthSituation.SALARY_MAINTENANCE in selected:
        hypotheses.add(HealthHypothesis.SALARY_MAINTENANCE_POTENTIAL)
    if HealthSituation.SUBROGATION in selected:
        hypotheses.add(HealthHypothesis.SUBROGATION_TO_VERIFY)
    if HealthSituation.DAILY_ALLOWANCE in selected:
        hypotheses.add(HealthHypothesis.DAILY_ALLOWANCE_POTENTIALLY_MISSING)
    if HealthSituation.POTENTIAL_PAY_IMPACT in selected:
        hypotheses.add(HealthHypothesis.PAYROLL_TIMING_DIFFERENCE)
    if HealthSituation.PROVIDENT_COVER in selected:
        hypotheses.add(HealthHypothesis.PROVIDENT_COVER_POTENTIAL)
    if HealthSituation.RETURN_VISIT in selected or HealthSituation.RETURN_TO_WORK in selected:
        hypotheses.add(HealthHypothesis.RETURN_VISIT_POTENTIALLY_REQUIRED)
    if HealthSituation.WORK_ADJUSTMENT in selected:
        hypotheses.add(HealthHypothesis.ADJUSTMENT_TO_EXAMINE)
    if HealthSituation.REDEPLOYMENT in selected:
        hypotheses.add(HealthHypothesis.REDEPLOYMENT_TO_EXAMINE)
    if HealthSituation.REPORTED_UNFITNESS in selected:
        hypotheses.add(HealthHypothesis.UNFITNESS_PROCEDURE_INCOMPLETE)
    if HealthSituation.POSSIBLE_HEALTH_DISCRIMINATION in selected:
        hypotheses.add(HealthHypothesis.POSSIBLE_HEALTH_DISCRIMINATION)
    if HealthSituation.POTENTIALLY_UNJUSTIFIED_ABSENCE in selected:
        hypotheses.add(HealthHypothesis.POSSIBLE_ABSENCE_DISCIPLINE)
    if not hypotheses:
        hypotheses.add(HealthHypothesis.INSUFFICIENT_DATA)
    facts = tuple(item.statement for item in case.declared_facts + case.established_facts) or ("Situation déclarée à documenter.",)
    return tuple(
        HealthQualification(
            hypothesis,
            facts,
            ("Aucune décision administrative, médicale ou de paie n'est déduite.",),
            ("dates", "documents minimaux", "réponse de l'acteur compétent"),
            ("accords applicables", "Code du travail", "Code de la sécurité sociale", "source officielle compétente"),
            _actor_for(hypothesis),
            ("chronologie", "justificatifs minimaux", "décisions existantes"),
            ("décalage de traitement", "transmission incomplète", "condition non démontrée"),
            confidence,
            urgency,
            ("droit potentiel ou régularisation possible à vérifier", "orientation vers l'acteur compétent"),
        )
        for hypothesis in sorted(hypotheses, key=lambda item: item.value)
    )


def _actor_for(hypothesis):
    if hypothesis in {HealthHypothesis.RECOGNITION_PENDING, HealthHypothesis.COMMUTING_ACCIDENT_POSSIBLE, HealthHypothesis.OCCUPATIONAL_DISEASE_PENDING, HealthHypothesis.DAILY_ALLOWANCE_POTENTIALLY_MISSING}:
        return CompetentActor.CPAM
    if hypothesis in {HealthHypothesis.RETURN_VISIT_POTENTIALLY_REQUIRED, HealthHypothesis.ADJUSTMENT_TO_EXAMINE, HealthHypothesis.UNFITNESS_PROCEDURE_INCOMPLETE}:
        return CompetentActor.OCCUPATIONAL_PHYSICIAN
    if hypothesis is HealthHypothesis.PROVIDENT_COVER_POTENTIAL:
        return CompetentActor.PROVIDENT_BODY
    if hypothesis in {HealthHypothesis.SALARY_MAINTENANCE_POTENTIAL, HealthHypothesis.SUBROGATION_TO_VERIFY, HealthHypothesis.PAYROLL_TIMING_DIFFERENCE}:
        return CompetentActor.PAYROLL
    return CompetentActor.EMPLOYER


def _positions(case):
    available = tuple(sorted(item.document_type for item in case.available_pieces))
    common_missing = ("chronologie", "transmissions", "décisions existantes", "règles applicables")
    employee = HealthPosition(
        ("Les dates, transmissions et traitements observés doivent être rapprochés.",),
        ("maintien potentiel", "instruction CPAM", "reprise ou reclassement à vérifier"),
        ("La demande est identifiée.",),
        ("Les droits et montants ne sont pas calculables sans données.",),
        available,
        common_missing,
        ("décalage administratif", "pièce manquante"),
        ("demander une réponse écrite", "produire les pièces minimales"),
        ("décision CPAM", "avis médical", "garantie assurantielle"),
        CompetentActor.UNION_REPRESENTATIVE,
    )
    other = HealthPosition(
        ("Un décalage, une condition non remplie ou une décision en attente peut expliquer le traitement.",),
        ("instruction administrative", "vérification paie", "recherche de reclassement"),
        ("Les démarches documentées peuvent objectiver le traitement.",),
        ("Une explication non tracée reste à vérifier.",),
        available,
        common_missing,
        ("urgence financière", "protection contractuelle"),
        ("tracer les critères et démarches",),
        ("fond médical", "issue d'un recours"),
        CompetentActor.EMPLOYER,
    )
    return employee, other


def _urgency(case, text):
    categories = set()
    if any(marker in text for marker in ("danger immediat", "detresse", "urgence medicale")):
        categories.update({UrgencyCategory.HUMAN, UrgencyCategory.MEDICAL})
    if any(marker in text for marker in ("absence totale de revenu", "ijss bloquees", "salaire non verse")):
        categories.add(UrgencyCategory.FINANCIAL)
    if any(marker in text for marker in ("rupture imminente", "licenciement imminent", "reclassement imminent")):
        categories.add(UrgencyCategory.CONTRACTUAL)
    if any(marker in text for marker in ("delai de recours", "fin de portabilite", "delai de declaration")):
        categories.update({UrgencyCategory.ADMINISTRATIVE, UrgencyCategory.LITIGATION})
    if categories.intersection({UrgencyCategory.HUMAN, UrgencyCategory.MEDICAL}):
        return UrgencyLevel.IMMEDIATE, tuple(sorted(categories, key=lambda item: item.value))
    if categories:
        return UrgencyLevel.URGENT, tuple(sorted(categories, key=lambda item: item.value))
    return case.urgency, ()


def _case_text(case):
    return _normalize(" ".join([case.question] + [item.statement for item in case.declared_facts + case.established_facts + case.hypotheses]))


def _normalize(value):
    normalized = unicodedata.normalize("NFKD", value)
    return " ".join("".join(c for c in normalized if not unicodedata.combining(c)).lower().replace("’", " ").replace("'", " ").split())
