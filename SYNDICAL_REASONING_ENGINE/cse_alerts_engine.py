"""Prudent R2C engine for collective claims, alerts, expertise and escalation."""

from __future__ import annotations

import unicodedata

from .cse_alerts_models import (
    AlertEventKind,
    AlertHistoryLookup,
    AlertHistoryMetadata,
    AlertTimelineEvent,
    CSEAlertsExpertiseAnalysis,
    ClaimScope,
    ClaimSignal,
    EvidenceItem,
    EvidenceStrength,
    SeverityLevel,
)
from .cse_alerts_policy import (
    alert_hypotheses,
    articulate,
    competent_actors,
    contradictory_positions,
    document_requests,
    escalation_options,
    expertise_hypotheses,
    investigations,
    questions,
    resolutions,
    strategies,
)
from .engine import SyndicalReasoningEngine
from .models import ConfidenceLevel, SyndicalCaseInput, UrgencyLevel


R2C_DOMAINS = {"cse_alert", "cse_claim", "cse_expertise", "cse_escalation"}
STRONG_MARKERS = (
    "droit d alerte",
    "alerte economique",
    "alerte sociale",
    "atteinte aux droits",
    "expertise cse",
    "expertise economique",
    "expertise potentielle",
    "saisir l inspection",
    "defenseur des droits",
    "reclamations collectives",
    "plusieurs salaries signalent",
    "demande d enquete cse",
    "refus persistants",
)


def needs_cse_alerts_reasoning(case_or_question: SyndicalCaseInput | str) -> bool:
    if isinstance(case_or_question, SyndicalCaseInput):
        if set(case_or_question.suspected_domains).intersection(R2C_DOMAINS):
            return True
        text = _case_text(case_or_question)
        cse_context = "cse" in case_or_question.suspected_domains or "cse" in text
    else:
        text = _normalize(case_or_question)
        cse_context = "cse" in text
    isolated = any(marker in text for marker in ("un salarie", "une personne", "cas individuel", "isole"))
    collective = any(marker in text for marker in ("plusieurs", "collectif", "recurrent", "repete", "services", "elus"))
    if isolated and not collective:
        return False
    if any(marker in text for marker in STRONG_MARKERS):
        return cse_context or any(marker in text for marker in ("plusieurs salaries", "discrimination syndicale", "inspection du travail"))
    if not cse_context:
        return False
    if text.strip() in {"alerte", "alerte cse"}:
        return False
    escalation = any(marker in text for marker in ("expertise", "enquete", "inspection", "resolution", "refus persistant", "sans reponse"))
    return collective and escalation


class NullAlertHistoryLookup:
    def search_metadata(self, query: str) -> tuple[AlertHistoryMetadata, ...]:
        return ()


class CSEAlertsExpertiseReasoningEngine:
    def __init__(
        self,
        base_engine: SyndicalReasoningEngine | None = None,
        *,
        history_lookup: AlertHistoryLookup | None = None,
    ) -> None:
        self._base_engine = base_engine or SyndicalReasoningEngine()
        self._history_lookup = history_lookup or NullAlertHistoryLookup()

    def analyze(
        self, case: SyndicalCaseInput, *, scenario_code: str | None = None
    ) -> CSEAlertsExpertiseAnalysis:
        if not isinstance(case, SyndicalCaseInput):
            raise TypeError("case must be a SyndicalCaseInput")
        text = _case_text(case)
        history = tuple(
            sorted(
                self._history_lookup.search_metadata(case.question),
                key=lambda item: (item.meeting_date or "", item.title),
            )
        )
        claim = _claim(case, text)
        confidence = claim.confidence
        urgency = _urgency(case, text)
        cse_position, employer_position = contradictory_positions()
        return CSEAlertsExpertiseAnalysis(
            self._base_engine.analyze(case),
            claim,
            _timeline(claim, text, history, confidence),
            alert_hypotheses(text, confidence),
            expertise_hypotheses(text, confidence),
            investigations(text),
            escalation_options(urgency),
            competent_actors(),
            _evidence(case, history),
            questions(text),
            document_requests(),
            resolutions(text),
            history,
            cse_position,
            employer_position,
            strategies(urgency),
            articulate(text, claim.scope),
            _severity(text, claim),
            urgency,
            confidence,
            True,
            tuple(dict.fromkeys((*case.missing_information, *_missing(claim, history)))),
            scenario_code,
        )


def _claim(case: SyndicalCaseInput, text: str) -> ClaimSignal:
    isolated = any(marker in text for marker in ("un salarie", "une personne", "cas individuel", "isole"))
    collective = any(marker in text for marker in ("plusieurs", "collectif", "services", "representants", "elus"))
    if "sans indice collectif" in text or "aucun indice collectif" in text:
        collective = False
    repeated = any(marker in text for marker in ("repete", "recurrent", "persistant", "plusieurs fois"))
    if isolated and not collective:
        scope = ClaimScope.INDIVIDUAL_CLAIM
    elif collective:
        scope = ClaimScope.COLLECTIVE_CLAIM
    elif repeated:
        scope = ClaimScope.REPEATED_SIMILAR_CLAIMS
    elif "negociation" in text or "revendication" in text:
        scope = ClaimScope.COLLECTIVE_BARGAINING
    else:
        scope = ClaimScope.TO_INVESTIGATE
    rights = []
    for marker, right in (
        ("discrimination", "égalité et non-discrimination potentielles"),
        ("liberte", "libertés individuelles potentielles"),
        ("vie privee", "vie privée potentielle"),
        ("dignite", "dignité potentielle"),
        ("salaire", "rémunération"),
        ("horaire", "temps de travail"),
        ("classification", "classification"),
        ("sante mentale", "santé déclarée sans diagnostic"),
    ):
        if marker in text:
            rights.append(right)
    confidence = (
        ConfidenceLevel.HIGH
        if case.established_facts and case.available_pieces
        else ConfidenceLevel.MODERATE
        if case.declared_facts or case.available_pieces
        else ConfidenceLevel.LOW
    )
    count = 2 if collective else 1 if isolated else None
    return ClaimSignal(
        scope,
        case.person_capacity or "origine à confirmer",
        count,
        ("services concernés à préciser",) if collective else (),
        tuple(item.statement for item in case.declared_facts + case.established_facts),
        True if repeated else None,
        "durée à préciser",
        ("conséquences déclarées à objectiver",),
        tuple(rights),
        tuple(item.statement for item in case.established_facts),
        "réponse ou absence de réponse à documenter",
        "source ou règle commune à rechercher" if collective else None,
        "effet collectif potentiel à confirmer" if collective else None,
        confidence,
    )


def _timeline(
    claim: ClaimSignal,
    text: str,
    history: tuple[AlertHistoryMetadata, ...],
    confidence: ConfidenceLevel,
) -> tuple[AlertTimelineEvent, ...]:
    rows = [
        ("first_signal", AlertEventKind.FIRST_SIGNAL, claim.origin, "signalement déclaré", "à documenter"),
    ]
    if claim.scope is ClaimScope.COLLECTIVE_CLAIM:
        rows.append(("collective_extension", AlertEventKind.COLLECTIVE_EXTENSION, "salariés / élus", "dimension collective potentielle", "à confirmer"))
    if "cse" in text:
        rows.append(("cse_referral", AlertEventKind.CSE_REFERRAL, "CSE", "saisine déclarée", "à vérifier"))
    if "document" in text:
        rows.append(("document_request", AlertEventKind.DOCUMENT_REQUEST, "CSE", "demande de documents", "réponse à suivre"))
    if "resolution" in text:
        rows.append(("resolution", AlertEventKind.RESOLUTION, "CSE", "projet ou résolution à vérifier", "validité à confirmer"))
    if "enquete" in text:
        rows.append(("investigation", AlertEventKind.INVESTIGATION, "CSE", "enquête envisagée", "cadre à confirmer"))
    if "expert" in text:
        rows.append(("expert", AlertEventKind.EXPERT_REFERRAL, "CSE", "expertise envisagée", "conditions à vérifier"))
    if any(marker in text for marker in ("inspection", "defenseur des droits", "juge")):
        rows.append(("external", AlertEventKind.EXTERNAL_REFERRAL, "acteur extérieur à confirmer", "saisine envisagée", "compétence à vérifier"))
    if any(item.has_commitment for item in history) or "engagement" in text:
        rows.append(("commitment", AlertEventKind.EMPLOYER_COMMITMENT, "direction", "engagement potentiel", "source à vérifier"))
    if "corrige" in text or "mesure corrective" in text:
        rows.append(("corrective", AlertEventKind.CORRECTIVE_MEASURE, "direction", "correction déclarée", "efficacité à suivre"))
    return tuple(
        AlertTimelineEvent(event_id, None, False, actor, kind, source, confidence, consequence, None, status)
        for event_id, kind, actor, source, status in rows
        for consequence in ("prochaine étape à documenter",)
    )


def _evidence(case: SyndicalCaseInput, history: tuple[AlertHistoryMetadata, ...]) -> tuple[EvidenceItem, ...]:
    items = [
        EvidenceItem("déclaration", fact.statement, "dossier synthétique", EvidenceStrength.DECLARED, False, "à corroborer")
        for fact in case.declared_facts
    ]
    items.extend(
        EvidenceItem("fait établi dans le dossier synthétique", fact.statement, "dossier synthétique", EvidenceStrength.DOCUMENTED, True, "portée juridique non déduite")
        for fact in case.established_facts
    )
    items.extend(
        EvidenceItem("historique CSE metadata-only", item.title, "CSE Memory", EvidenceStrength.PARTIAL, False, "document source à vérifier")
        for item in history
    )
    return tuple(items)


def _severity(text: str, claim: ClaimSignal) -> SeverityLevel:
    if not claim.declared_facts:
        return SeverityLevel.UNDETERMINED
    if any(marker in text for marker in ("urgent", "represaille", "suppression de postes", "refus persistants")):
        return SeverityLevel.HIGH_TO_CONFIRM
    if claim.scope in {ClaimScope.COLLECTIVE_CLAIM, ClaimScope.REPEATED_SIMILAR_CLAIMS}:
        return SeverityLevel.MODERATE
    return SeverityLevel.LOW


def _urgency(case: SyndicalCaseInput, text: str) -> UrgencyLevel:
    if any(marker in text for marker in ("danger immediat", "protection immediate", "demain")):
        return UrgencyLevel.IMMEDIATE
    if any(marker in text for marker in ("urgent", "reunion extraordinaire", "refus persistants", "represaille")):
        return UrgencyLevel.URGENT
    return case.urgency


def _missing(claim: ClaimSignal, history: tuple[AlertHistoryMetadata, ...]) -> tuple[str, ...]:
    missing = ["dates certaines", "population exacte", "réponse écrite de l'employeur", "mécanisme juridique applicable"]
    if not claim.potentially_affected_rights:
        missing.append("droits ou règles potentiellement concernés")
    if not history:
        missing.append("historique CSE metadata-only")
    return tuple(missing)


def _case_text(case: SyndicalCaseInput) -> str:
    return _normalize(" ".join([case.question] + [item.statement for item in case.declared_facts + case.established_facts + case.hypotheses]))


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value))
    return " ".join(
        "".join(char for char in normalized if not unicodedata.combining(char))
        .lower()
        .replace("’", " ")
        .replace("'", " ")
        .replace("-", " ")
        .split()
    )
