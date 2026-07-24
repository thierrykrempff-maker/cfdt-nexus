"""Prudent R1D reasoning for discrimination, harassment and equal treatment."""

from __future__ import annotations

import unicodedata

from .discrimination_arguments import analyze_discrimination_positions
from .discrimination_articulation import articulate_discrimination_domains
from .discrimination_comparators import assess_comparators
from .discrimination_evidence import discrimination_evidence
from .discrimination_models import (
    AdverseMeasure,
    DiscriminationHarassmentAnalysis,
    ProtectedCriterion,
    QualificationHypothesis,
    SituationType,
)
from .discrimination_questions import build_discrimination_questions
from .discrimination_strategies import build_discrimination_strategies
from .discrimination_timeline import build_discrimination_timeline
from .engine import SyndicalReasoningEngine
from .models import ConfidenceLevel, SyndicalCaseInput, UrgencyLevel


CRITERION_MARKERS = {
    ProtectedCriterion.SEX: ("sexe", "femme", "homme"),
    ProtectedCriterion.PREGNANCY: ("grossesse", "enceinte", "maternite"),
    ProtectedCriterion.FAMILY_SITUATION: ("situation familiale", "parent", "enfant"),
    ProtectedCriterion.ORIGIN: ("origine", "nationalite", "ethnique"),
    ProtectedCriterion.AGE: ("age", "trop vieux", "trop jeune"),
    ProtectedCriterion.DISABILITY: ("handicap", "travailleur handicape"),
    ProtectedCriterion.HEALTH: ("etat de sante", "arret maladie", "retour d arret"),
    ProtectedCriterion.UNION_ACTIVITY: ("activite syndicale", "syndical", "delegue syndical"),
    ProtectedCriterion.OPINIONS: ("opinions",),
    ProtectedCriterion.BELIEFS: ("convictions", "religion"),
    ProtectedCriterion.SEXUAL_ORIENTATION: ("orientation sexuelle",),
    ProtectedCriterion.GENDER_IDENTITY: ("identite de genre",),
    ProtectedCriterion.PLACE_OF_RESIDENCE: ("lieu de residence", "adresse"),
    ProtectedCriterion.PHYSICAL_APPEARANCE: ("apparence physique",),
    ProtectedCriterion.ECONOMIC_VULNERABILITY: ("vulnerabilite economique",),
    ProtectedCriterion.REPRESENTATIVE_MANDATE: ("mandat", "elu cse", "representant du personnel"),
    ProtectedCriterion.REPORTING_OR_TESTIMONY: ("signalement", "temoigne", "lanceur d alerte"),
}

MEASURE_MARKERS = {
    AdverseMeasure.SANCTION: ("sanction", "avertissement", "mise a pied"),
    AdverseMeasure.PROMOTION_REFUSAL: ("refus de promotion", "promotion refusee"),
    AdverseMeasure.CAREER_SLOWDOWN: ("stagnation de carriere", "ralentissement de carriere"),
    AdverseMeasure.JOB_CHANGE: ("changement de poste",),
    AdverseMeasure.DUTY_REMOVAL: ("retrait de mission", "perd ses dossiers", "retrait de fonction", "perd progressivement dossiers"),
    AdverseMeasure.BONUS_REDUCTION: ("baisse de prime", "perte de prime"),
    AdverseMeasure.LOWER_PAY: ("remuneration moindre", "difference de remuneration", "salaire inferieur"),
    AdverseMeasure.TRAINING_REFUSAL: ("refus de formation",),
    AdverseMeasure.UNFAVOURABLE_SCHEDULE: ("horaires defavorables", "horaire cible"),
    AdverseMeasure.ISOLATION: ("isolement", "isole"),
    AdverseMeasure.DISMISSAL: ("licenciement", "rupture du contrat"),
    AdverseMeasure.TRANSFER: ("mutation",),
    AdverseMeasure.NEGATIVE_APPRAISAL: ("evaluation defavorable", "evaluation negative"),
    AdverseMeasure.NO_PAY_RISE: ("absence d augmentation", "pas d augmentation"),
    AdverseMeasure.HARSHER_DISCIPLINE: ("sanction plus severe", "sanctionne lourdement"),
}

DIRECT_MARKERS = (
    "discrimination",
    "harcelement",
    "agissement sexiste",
    "egalite de traitement",
    "egalite de remuneration",
    "represailles",
    "traitement defavorable",
)

R1D_DOMAINS = {
    "discrimination",
    "harcelement",
    "egalite_traitement",
    "egalite_professionnelle",
    "droit_syndical",
}


def needs_discrimination_harassment_reasoning(
    case_or_question: SyndicalCaseInput | str,
) -> bool:
    if isinstance(case_or_question, SyndicalCaseInput):
        text = _case_text(case_or_question)
        if set(case_or_question.suspected_domains).intersection(R1D_DOMAINS):
            return True
    else:
        text = _normalize(str(case_or_question))
    if any(marker in text for marker in DIRECT_MARKERS):
        return True
    has_criterion = any(
        marker in text for markers in CRITERION_MARKERS.values() for marker in markers
    )
    has_measure = any(
        marker in text for markers in MEASURE_MARKERS.values() for marker in markers
    )
    repeated_hostility = any(
        marker in text
        for marker in (
            "critiques repetees",
            "humiliations repetees",
            "denigrement repete",
            "messages repetes a connotation sexuelle",
        )
    )
    return repeated_hostility or (has_criterion and has_measure)


class DiscriminationHarassmentReasoningEngine:
    """R1D specialization with no automatic finding and no medical diagnosis."""

    def __init__(self, base_engine: SyndicalReasoningEngine | None = None) -> None:
        self._base_engine = base_engine or SyndicalReasoningEngine()

    def analyze(
        self,
        case: SyndicalCaseInput,
        *,
        scenario_code: str | None = None,
    ) -> DiscriminationHarassmentAnalysis:
        if not isinstance(case, SyndicalCaseInput):
            raise TypeError("case must be a SyndicalCaseInput")
        text = _case_text(case)
        criteria = _criteria(text)
        measures = _measures(text)
        urgency = _urgency(case, text)
        confidence = _confidence(case)
        hypotheses = _hypotheses(case, text, criteria, measures, urgency, confidence)
        comparators = assess_comparators(case)
        employee, employer = analyze_discrimination_positions(case, hypotheses, comparators)
        return DiscriminationHarassmentAnalysis(
            base_report=self._base_engine.analyze(case),
            timeline=build_discrimination_timeline(case),
            hypotheses=hypotheses,
            protected_criteria=criteria,
            adverse_measures=measures,
            comparators=comparators,
            automatic_questions=build_discrimination_questions(
                case,
                criteria,
                measures,
                immediate_danger=urgency is UrgencyLevel.IMMEDIATE,
            ),
            evidence=discrimination_evidence(),
            employee_position=employee,
            employer_position=employer,
            strategies=build_discrimination_strategies(urgency),
            articulation=articulate_discrimination_domains(case),
            missing_information=tuple(
                sorted(
                    set(case.missing_information)
                    | {
                        "chronologie détaillée",
                        "réponse de l'employeur",
                        "comparateurs homogènes",
                        "preuves licites disponibles",
                    }
                )
            ),
            urgency=urgency,
            confidence=confidence,
            scenario_code=scenario_code,
        )


def _criteria(text: str) -> tuple[ProtectedCriterion, ...]:
    return tuple(
        sorted(
            (
                criterion
                for criterion, markers in CRITERION_MARKERS.items()
                if any(marker in text for marker in markers)
            ),
            key=lambda item: item.value,
        )
    )


def _measures(text: str) -> tuple[AdverseMeasure, ...]:
    return tuple(
        sorted(
            (
                measure
                for measure, markers in MEASURE_MARKERS.items()
                if any(marker in text for marker in markers)
            ),
            key=lambda item: item.value,
        )
    )


def _hypotheses(
    case: SyndicalCaseInput,
    text: str,
    criteria: tuple[ProtectedCriterion, ...],
    measures: tuple[AdverseMeasure, ...],
    urgency: UrgencyLevel,
    confidence: ConfidenceLevel,
) -> tuple[QualificationHypothesis, ...]:
    selected = set()
    repeated = any(marker in text for marker in ("repete", "progressif", "plusieurs fois", "chaque semaine"))
    sexual = any(marker in text for marker in ("connotation sexuelle", "propos sexuels", "geste impose", "sollicitation sexuelle"))
    sexist = any(marker in text for marker in ("sexiste", "remarques liees au sexe"))
    harassment = "harcelement" in text or (
        repeated
        and any(marker in text for marker in ("critique", "humiliation", "denigrement", "isolement", "retrait de mission"))
    )
    retaliation = any(marker in text for marker in ("represailles", "apres le signalement", "apres avoir signale", "peu apres avoir signale"))
    union = any(marker in text for marker in ("syndical", "mandat", "representant", "elu cse"))
    isolated = any(marker in text for marker in ("unique", "isole", "une remarque")) and not repeated
    if sexual:
        selected.add(SituationType.POSSIBLE_SEXUAL_HARASSMENT)
    if sexist:
        selected.add(SituationType.SEXIST_BEHAVIOUR)
    if harassment and not sexual:
        selected.add(SituationType.POSSIBLE_MORAL_HARASSMENT)
    if criteria and measures:
        selected.update({SituationType.DIFFERENCE_IN_TREATMENT, SituationType.POSSIBLE_DISCRIMINATION})
    elif any(
        marker in text
        for marker in (
            "difference de traitement",
            "difference de remuneration",
            "faits similaires",
            "egalite",
        )
    ):
        selected.add(SituationType.DIFFERENCE_IN_TREATMENT)
    if retaliation:
        selected.add(SituationType.POSSIBLE_RETALIATION)
    if union and measures:
        selected.add(SituationType.POSSIBLE_UNION_RIGHTS_INTERFERENCE)
    if isolated:
        selected.update({SituationType.PROFESSIONAL_CONFLICT, SituationType.ISOLATED_INAPPROPRIATE_BEHAVIOUR})
    if any(marker in text for marker in ("management difficile", "dysfonctionnement managerial", "surcharge", "sous charge")):
        selected.add(SituationType.MANAGEMENT_DYSFUNCTION)
    if urgency is UrgencyLevel.IMMEDIATE:
        selected.add(SituationType.PROTECTION_URGENCY)
    if not selected:
        selected.add(SituationType.INSUFFICIENT_FACTS)

    facts = tuple(item.statement for item in case.declared_facts + case.established_facts)
    return tuple(
        QualificationHypothesis(
            situation=situation,
            supporting_facts=facts or ("Question déclarative à documenter.",),
            weakening_facts=(
                "Aucune qualification définitive ne peut être déduite du seul récit.",
            ),
            missing_elements=(
                "dates et répétition",
                "preuves disponibles",
                "réponse de l'employeur",
                "comparateurs pertinents",
            ),
            legal_criteria_to_check=_criteria_for(situation),
            required_evidence=("chronologie", "écrits", "décisions", "comparaisons"),
            alternative_explanations=(
                "conflit professionnel",
                "justification organisationnelle objective",
                "situations non comparables",
            ),
            confidence=confidence,
            urgency=urgency,
            possible_consequences=(
                "mesure de protection à envisager indépendamment de la qualification finale",
                "analyse contradictoire et conseil compétent si nécessaire",
            ),
        )
        for situation in sorted(selected, key=lambda item: item.value)
    )


def _criteria_for(situation: SituationType) -> tuple[str, ...]:
    if situation is SituationType.POSSIBLE_MORAL_HARASSMENT:
        return ("agissements et répétition à documenter", "dégradation possible des conditions de travail", "effets déclarés sans diagnostic")
    if situation is SituationType.POSSIBLE_SEXUAL_HARASSMENT:
        return ("nature sexuelle ou sexiste des propos ou comportements", "répétition ou pression grave", "absence de consentement")
    if situation in {SituationType.POSSIBLE_DISCRIMINATION, SituationType.POSSIBLE_UNION_RIGHTS_INTERFERENCE}:
        return ("critère protégé potentiel", "mesure défavorable", "lien causal à examiner", "justification objective possible")
    if situation is SituationType.POSSIBLE_RETALIATION:
        return ("signalement ou témoignage antérieur", "mesure postérieure", "proximité temporelle", "motif objectif possible")
    return ("faits précis", "contexte", "explications alternatives")


def _urgency(case: SyndicalCaseInput, text: str) -> UrgencyLevel:
    if any(marker in text for marker in ("danger immediat", "violence imminente", "menace imminente", "risque suicidaire", "suicide")):
        return UrgencyLevel.IMMEDIATE
    if any(marker in text for marker in ("propos sexuels", "geste impose", "represailles en cours", "licenciement imminent", "sanction imminente")):
        return UrgencyLevel.URGENT
    if case.urgency in {UrgencyLevel.IMMEDIATE, UrgencyLevel.URGENT}:
        return case.urgency
    if any(marker in text for marker in ("harcelement", "isolement brutal", "retrait immediat")):
        return UrgencyLevel.PROMPT
    return case.urgency


def _confidence(case: SyndicalCaseInput) -> ConfidenceLevel:
    if case.established_facts and len(case.available_pieces) >= 2:
        return ConfidenceLevel.MODERATE
    return ConfidenceLevel.LOW


def _case_text(case: SyndicalCaseInput) -> str:
    return _normalize(
        " ".join(
            [case.question]
            + [item.statement for item in case.declared_facts]
            + [item.statement for item in case.established_facts]
            + [item.statement for item in case.hypotheses]
        )
    )


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return " ".join(
        "".join(char for char in normalized if not unicodedata.combining(char))
        .lower()
        .replace("’", " ")
        .replace("'", " ")
        .split()
    )
