"""Prudent R1C analysis of working time and potential pay effects."""

from __future__ import annotations

import unicodedata

from .engine import SyndicalReasoningEngine
from .models import ConfidenceLevel, SyndicalCaseInput, UrgencyLevel
from .working_time_arguments import analyze_working_time_positions
from .working_time_articulation import articulate_syndical_domains
from .working_time_comparison import compare_documents
from .working_time_evidence import working_time_evidence
from .working_time_models import (
    BreakObservation,
    OnCallObservation,
    PayImpactLikelihood,
    PotentialPayImpact,
    RestObservation,
    ScheduleKind,
    ScheduleObservation,
    WorkingOrganization,
    WorkingTimeAnalysis,
    WorkingTimeQualification,
    WorkingTimeSituation,
)
from .working_time_questions import build_working_time_questions
from .working_time_strategies import build_working_time_strategies


SITUATION_MARKERS = {
    WorkingTimeSituation.EFFECTIVE_WORK: ("temps de travail effectif", "a disposition"),
    WorkingTimeSituation.BREAK: ("pause",),
    WorkingTimeSituation.INTERRUPTED_BREAK: ("pause interrompue", "intervient pendant sa pause", "joignable pendant sa pause"),
    WorkingTimeSituation.DRESSING_TIME: ("habillage", "deshabillage"),
    WorkingTimeSituation.SHOWER_TIME: ("douche",),
    WorkingTimeSituation.BUSINESS_TRAVEL: ("deplacement professionnel", "mission"),
    WorkingTimeSituation.COMMUTE: ("trajet domicile", "domicile travail"),
    WorkingTimeSituation.ON_CALL: ("astreinte",),
    WorkingTimeSituation.ON_CALL_INTERVENTION: ("intervention", "rappel nocturne", "rappele pendant"),
    WorkingTimeSituation.INTERVENTION_TRAVEL: ("trajet d intervention", "deplacement lie a l intervention"),
    WorkingTimeSituation.NIGHT_WORK: ("travail de nuit", "regulierement des heures de nuit"),
    WorkingTimeSituation.OCCASIONAL_NIGHT_HOURS: ("heure ponctuelle la nuit", "heures ponctuelles la nuit"),
    WorkingTimeSituation.SHIFT_WORK: ("travail poste", "salarie poste", "en poste"),
    WorkingTimeSituation.SUCCESSIVE_TEAMS: ("equipes successives",),
    WorkingTimeSituation.FIVE_SHIFT: ("5x8",),
    WorkingTimeSituation.SUNDAY_WORK: ("dimanche",),
    WorkingTimeSituation.PUBLIC_HOLIDAY: ("jour ferie", "jours feries"),
    WorkingTimeSituation.OVERTIME: ("heures supplementaires",),
    WorkingTimeSituation.ADDITIONAL_HOURS: ("heures complementaires",),
    WorkingTimeSituation.SCHEDULE_OVERRUN: ("depassement d horaire", "heures non retrouvees"),
    WorkingTimeSituation.ANNUALIZATION: ("annualisation",),
    WorkingTimeSituation.MODULATION: ("modulation",),
    WorkingTimeSituation.WORK_CYCLE: ("cycle",),
    WorkingTimeSituation.DAILY_REST: ("repos quotidien", "repos suivant"),
    WorkingTimeSituation.WEEKLY_REST: ("repos hebdomadaire",),
    WorkingTimeSituation.COMPENSATORY_REST: ("repos compensateur",),
    WorkingTimeSituation.INFORMAL_RECOVERY: ("recuperation", "recup"),
    WorkingTimeSituation.RTT: ("rtt",),
    WorkingTimeSituation.PAID_LEAVE: ("conge paye", "conges payes"),
    WorkingTimeSituation.RECALL_DURING_REST: ("rappel pendant", "rappele pendant", "rappel sur repos"),
    WorkingTimeSituation.OFF_HOURS_TRAINING: ("formation hors horaire",),
    WorkingTimeSituation.REPRESENTATIVE_MEETING_ON_REST: ("reunion cse sur", "reunion cse pendant", "reunion syndicale sur"),
    WorkingTimeSituation.POTENTIAL_PAY_IMPACT: ("prime", "majoration", "bulletin", "nibelis", "paie", "indemnite"),
}

WORKING_TIME_DOMAINS = {"temps_travail", "working_time", "paie_remuneration", "astreinte", "repos"}
WORKING_TIME_MARKERS = tuple(marker for markers in SITUATION_MARKERS.values() for marker in markers) + (
    "kelio",
    "badgeage",
    "planning",
    "horaire",
)


def needs_working_time_reasoning(case_or_question: SyndicalCaseInput | str) -> bool:
    if isinstance(case_or_question, SyndicalCaseInput):
        text = " ".join(
            [case_or_question.question]
            + [item.statement for item in case_or_question.declared_facts]
            + [item.statement for item in case_or_question.established_facts]
        )
        if set(case_or_question.suspected_domains).intersection(WORKING_TIME_DOMAINS):
            return True
    else:
        text = str(case_or_question)
    normalized = _normalize(text)
    return any(marker in normalized for marker in WORKING_TIME_MARKERS)


class WorkingTimeReasoningEngine:
    """R1C specialization; it never calculates payroll."""

    def __init__(self, base_engine: SyndicalReasoningEngine | None = None) -> None:
        self._base_engine = base_engine or SyndicalReasoningEngine()

    def analyze(
        self,
        case: SyndicalCaseInput,
        *,
        scenario_code: str | None = None,
    ) -> WorkingTimeAnalysis:
        if not isinstance(case, SyndicalCaseInput):
            raise TypeError("case must be a SyndicalCaseInput")
        situations = self._situations(case)
        comparisons = compare_documents(case)
        impacts = self._pay_impacts(situations, comparisons)
        articulation = articulate_syndical_domains(case, working_time_relevant=True)
        employee, employer = analyze_working_time_positions(case, situations, comparisons, impacts)
        confidence = self._confidence(case, comparisons)
        return WorkingTimeAnalysis(
            self._base_engine.analyze(case),
            situations,
            self._organization(situations),
            self._schedules(case),
            self._on_call(situations),
            self._rests(situations),
            self._breaks(situations),
            self._qualifications(case, situations, confidence),
            build_working_time_questions(case, situations),
            working_time_evidence(),
            comparisons,
            employee,
            employer,
            impacts,
            build_working_time_strategies(case),
            articulation,
            tuple(sorted(item.source_id for item in case.available_internal_sources + case.available_sources)),
            tuple(sorted(set(case.missing_information) | set(self._default_missing(situations)))),
            case.urgency,
            confidence,
            scenario_code,
        )

    @staticmethod
    def _situations(case: SyndicalCaseInput) -> tuple[WorkingTimeSituation, ...]:
        text = _case_text(case)
        selected = {
            situation
            for situation, markers in SITUATION_MARKERS.items()
            if any(marker in text for marker in markers)
        }
        if WorkingTimeSituation.INTERRUPTED_BREAK in selected:
            selected.add(WorkingTimeSituation.BREAK)
            selected.add(WorkingTimeSituation.EFFECTIVE_WORK)
        if WorkingTimeSituation.ON_CALL_INTERVENTION in selected:
            selected.add(WorkingTimeSituation.ON_CALL)
        if WorkingTimeSituation.RECALL_DURING_REST in selected:
            selected.add(WorkingTimeSituation.DAILY_REST)
            selected.add(WorkingTimeSituation.ON_CALL_INTERVENTION)
        if WorkingTimeSituation.FIVE_SHIFT in selected:
            selected.update({WorkingTimeSituation.SHIFT_WORK, WorkingTimeSituation.WORK_CYCLE})
            if "nuit" in text:
                selected.add(WorkingTimeSituation.NIGHT_WORK)
        if not selected:
            selected.add(WorkingTimeSituation.EFFECTIVE_WORK)
        return tuple(sorted(selected, key=lambda item: item.value))

    @staticmethod
    def _organization(situations: tuple[WorkingTimeSituation, ...]) -> WorkingOrganization:
        selected = set(situations)
        return WorkingOrganization(
            "5x8" if WorkingTimeSituation.FIVE_SHIFT in selected else ("shift" if WorkingTimeSituation.SHIFT_WORK in selected else None),
            "cycle à documenter" if WorkingTimeSituation.WORK_CYCLE in selected else None,
            True if WorkingTimeSituation.SHIFT_WORK in selected else None,
            True if WorkingTimeSituation.FIVE_SHIFT in selected else None,
            True if WorkingTimeSituation.ANNUALIZATION in selected else None,
        )

    @staticmethod
    def _schedules(case: SyndicalCaseInput) -> tuple[ScheduleObservation, ...]:
        by_type = {item.document_type: item for item in case.available_pieces}
        result = []
        for kind, document_type, label in (
            (ScheduleKind.THEORETICAL, "official_schedule", "horaire théorique à rapprocher"),
            (ScheduleKind.DECLARED, "event_record", "horaire déclaré à vérifier"),
            (ScheduleKind.OBSERVED, "timeclock", "horaire constaté par indice technique"),
        ):
            piece = by_type.get(document_type)
            result.append(ScheduleObservation(kind, label, (piece.piece_id,) if piece else ()))
        return tuple(result)

    @staticmethod
    def _on_call(situations: tuple[WorkingTimeSituation, ...]) -> OnCallObservation | None:
        selected = set(situations)
        if WorkingTimeSituation.ON_CALL not in selected:
            return None
        return OnCallObservation(True, WorkingTimeSituation.ON_CALL_INTERVENTION in selected, False, False)

    @staticmethod
    def _rests(situations: tuple[WorkingTimeSituation, ...]) -> tuple[RestObservation, ...]:
        return tuple(
            RestObservation(item, WorkingTimeSituation.RECALL_DURING_REST in situations, False)
            for item in situations
            if item in {WorkingTimeSituation.DAILY_REST, WorkingTimeSituation.WEEKLY_REST, WorkingTimeSituation.COMPENSATORY_REST}
        )

    @staticmethod
    def _breaks(situations: tuple[WorkingTimeSituation, ...]) -> tuple[BreakObservation, ...]:
        if WorkingTimeSituation.BREAK not in situations:
            return ()
        interrupted = WorkingTimeSituation.INTERRUPTED_BREAK in situations
        return (BreakObservation(interrupted, None, True if interrupted else None),)

    @staticmethod
    def _qualifications(
        case: SyndicalCaseInput,
        situations: tuple[WorkingTimeSituation, ...],
        confidence: ConfidenceLevel,
    ) -> tuple[WorkingTimeQualification, ...]:
        facts = tuple(item.statement for item in case.declared_facts + case.established_facts)
        return tuple(
            WorkingTimeQualification(
                situation,
                facts or ("situation décrite dans la question, à vérifier",),
                ("règle applicable, période ou traces encore incomplètes",),
                _missing_for(situation),
                ("accord INEOS applicable", "Convention Chimie", "Code du travail", "jurisprudence comparable"),
                confidence,
                _consequences_for(situation),
                UrgencyLevel.URGENT if situation in {WorkingTimeSituation.DAILY_REST, WorkingTimeSituation.RECALL_DURING_REST} else case.urgency,
            )
            for situation in situations
        )

    @staticmethod
    def _pay_impacts(
        situations: tuple[WorkingTimeSituation, ...],
        comparisons: tuple[DocumentComparison, ...],
    ) -> tuple[PotentialPayImpact, ...]:
        selected = set(situations)
        impacts = []
        mapping = (
            (WorkingTimeSituation.OVERTIME, "heures supplémentaires potentielles"),
            (WorkingTimeSituation.NIGHT_WORK, "majoration ou contrepartie de nuit potentielle"),
            (WorkingTimeSituation.OCCASIONAL_NIGHT_HOURS, "traitement d'heures ponctuelles de nuit à vérifier"),
            (WorkingTimeSituation.SUNDAY_WORK, "majoration du dimanche potentielle"),
            (WorkingTimeSituation.PUBLIC_HOLIDAY, "traitement du jour férié à vérifier"),
            (WorkingTimeSituation.ON_CALL, "indemnité d'astreinte potentielle"),
            (WorkingTimeSituation.ON_CALL_INTERVENTION, "paiement du temps d'intervention potentiel"),
            (WorkingTimeSituation.INTERVENTION_TRAVEL, "traitement du déplacement d'intervention à vérifier"),
            (WorkingTimeSituation.COMPENSATORY_REST, "repos compensateur potentiel"),
            (WorkingTimeSituation.SHIFT_WORK, "prime de poste potentielle"),
        )
        for situation, label in mapping:
            if situation in selected:
                impacts.append(PotentialPayImpact(label, PayImpactLikelihood.POSSIBLE, "La situation est détectée mais la règle et les données restent à vérifier.", ("période", "accord applicable", "planning", "bulletin"), False))
        if any(item.observed_differences for item in comparisons):
            impacts.append(PotentialPayImpact("régularisation possible", PayImpactLikelihood.NOT_DEMONSTRATED, "Une incohérence apparente existe entre des métadonnées.", ("pièces concordantes", "explication de clôture", "validation"), False))
        if not impacts and WorkingTimeSituation.POTENTIAL_PAY_IMPACT in selected:
            impacts.append(PotentialPayImpact("prime ou majoration potentielle", PayImpactLikelihood.IMPOSSIBLE_WITHOUT_DATA, "Aucun calcul ni droit certain n'est possible avec les informations disponibles.", ("rubrique", "période", "règle", "événement"), False))
        return tuple(impacts)

    @staticmethod
    def _confidence(
        case: SyndicalCaseInput,
        comparisons: tuple[DocumentComparison, ...],
    ) -> ConfidenceLevel:
        if len(case.available_pieces) >= 3 and any(item.reliability is ConfidenceLevel.MODERATE for item in comparisons):
            return ConfidenceLevel.MODERATE
        return ConfidenceLevel.LOW

    @staticmethod
    def _default_missing(
        situations: tuple[WorkingTimeSituation, ...],
    ) -> tuple[str, ...]:
        missing = {"période exacte", "planning officiel", "traces horaires", "règle applicable"}
        if WorkingTimeSituation.ON_CALL in situations:
            missing.update({"durée d'intervention", "trajet d'intervention", "repos suivant"})
        return tuple(sorted(missing))


def _missing_for(situation: WorkingTimeSituation) -> tuple[str, ...]:
    if situation in {WorkingTimeSituation.BREAK, WorkingTimeSituation.INTERRUPTED_BREAK}:
        return ("liberté pendant la pause", "obligation de rester sur place", "interruptions réelles")
    if situation in {WorkingTimeSituation.ON_CALL, WorkingTimeSituation.ON_CALL_INTERVENTION}:
        return ("planning d'astreinte", "durée d'intervention", "trajet", "repos suivant")
    return ("période exacte", "horaire prévu", "horaire constaté", "règle applicable")


def _consequences_for(situation: WorkingTimeSituation) -> tuple[str, ...]:
    if situation in {WorkingTimeSituation.DAILY_REST, WorkingTimeSituation.WEEKLY_REST, WorkingTimeSituation.RECALL_DURING_REST}:
        return ("repos à vérifier ou restaurer", "mesure immédiate de prévention potentielle")
    if situation == WorkingTimeSituation.BREAK:
        return ("qualification de la pause à vérifier",)
    return ("contrepartie, compteur ou traitement potentiel à vérifier",)


def _case_text(case: SyndicalCaseInput) -> str:
    return _normalize(
        " ".join(
            [case.question]
            + [item.statement for item in case.declared_facts]
            + [item.statement for item in case.established_facts]
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
