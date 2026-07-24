"""Prudent R2B engine for agendas, meetings, documents, opinions and follow-up."""

from __future__ import annotations

import unicodedata

from .cse_operation_models import (
    AgendaItem,
    CSEDocument,
    CSEHistoryLookup,
    CSEHistoryMetadata,
    CSEMeetingFacts,
    CSEOperationAnalysis,
    CSEQuestion,
    Commitment,
    CommitmentStatus,
    ConfidenceLevel,
    ContradictoryPosition,
    DocumentStatus,
    ItemStatus,
    MeetingEventKind,
    MeetingTimelineEvent,
    MeetingType,
    QuestionCategory,
    UrgencyLevel,
)
from .cse_operation_policy import (
    actor_roles,
    articulate,
    deadline_assessments,
    document_requests,
    opinion_drafts,
    operation_assessment,
    reservations,
    resolution,
    strategies,
)
from .engine import SyndicalReasoningEngine
from .models import SyndicalCaseInput


R2B_DOMAINS = {"cse_operation", "cse_meeting", "cse_agenda", "cse_functioning"}
STRONG_MARKERS = (
    "ordre du jour", "convocation cse", "reunion cse", "avis cse",
    "resolution cse", "vote cse", "pv cse", "proces verbal cse",
    "point refuse", "documents transmis la veille", "reunion extraordinaire",
)


def needs_cse_operation_reasoning(case_or_question: SyndicalCaseInput | str) -> bool:
    if isinstance(case_or_question, SyndicalCaseInput):
        if set(case_or_question.suspected_domains).intersection(R2B_DOMAINS):
            return True
        text = _case_text(case_or_question)
        cse_context = "cse" in case_or_question.suspected_domains or "cse" in text
    else:
        text = _normalize(case_or_question)
        cse_context = "cse" in text
    if any(marker in text for marker in STRONG_MARKERS):
        return True
    if not cse_context:
        return False
    return any(
        marker in text
        for marker in (
            "secretaire", "elu", "convocation", "document", "question sans reponse",
            "avis", "reserve", "resolution", "vote", "engagement", "proces verbal",
            "reunion ordinaire", "reunion extraordinaire", "confidentialite",
        )
    )


class NullCSEHistoryLookup:
    def search_metadata(self, query: str) -> tuple[CSEHistoryMetadata, ...]:
        return ()


class CSEOperationReasoningEngine:
    def __init__(
        self,
        base_engine: SyndicalReasoningEngine | None = None,
        *,
        history_lookup: CSEHistoryLookup | None = None,
    ) -> None:
        self._base_engine = base_engine or SyndicalReasoningEngine()
        self._history_lookup = history_lookup or NullCSEHistoryLookup()

    def analyze(
        self, case: SyndicalCaseInput, *, scenario_code: str | None = None
    ) -> CSEOperationAnalysis:
        if not isinstance(case, SyndicalCaseInput):
            raise TypeError("case must be a SyndicalCaseInput")
        text = _case_text(case)
        meeting = _meeting(case, text)
        history = tuple(
            sorted(
                self._history_lookup.search_metadata(case.question),
                key=lambda item: (item.meeting_date or "", item.title),
            )
        )
        urgency = _urgency(case, text)
        confidence = _confidence(case, meeting)
        commitments = _commitments(text, history, confidence)
        return CSEOperationAnalysis(
            self._base_engine.analyze(case),
            meeting,
            _timeline(meeting, confidence, commitments),
            actor_roles(),
            _agenda_proposals(meeting, text),
            _questions(meeting, history),
            document_requests(meeting.documents),
            deadline_assessments(meeting, urgency),
            opinion_drafts(meeting),
            reservations(meeting),
            resolution(meeting),
            commitments,
            history,
            _elected_position(meeting, history),
            _employer_position(meeting),
            operation_assessment(meeting, text),
            strategies(urgency),
            articulate(text),
            tuple(dict.fromkeys((*case.missing_information, *_missing(meeting)))),
            urgency,
            confidence,
            scenario_code,
        )


def _meeting(case: SyndicalCaseInput, text: str) -> CSEMeetingFacts:
    if "extraordinaire" in text:
        meeting_type = MeetingType.EXTRAORDINARY
    elif "demande des elus" in text:
        meeting_type = MeetingType.ELECTED_MEMBERS_REQUEST
    elif "projet" in text or "reorganisation" in text:
        meeting_type = MeetingType.PROJECT_RELATED
    elif "reunion" in text or "ordre du jour" in text:
        meeting_type = MeetingType.ORDINARY
    else:
        meeting_type = MeetingType.UNKNOWN
    status = (
        ItemStatus.APPARENTLY_REFUSED
        if any(marker in text for marker in ("point refuse", "n apparait pas", "refus d inscription"))
        else ItemStatus.DEFERRED
        if "report" in text
        else ItemStatus.INCLUDED
        if any(marker in text for marker in ("point inscrit", "ordre du jour valide"))
        else ItemStatus.REQUESTED
    )
    agenda = (
        AgendaItem(
            "point CSE synthétique à préciser",
            "contexte déclaré, non établi",
            ("Quel est le périmètre ?", "Quel calendrier et quels impacts ?"),
            ("document de projet", "données d'impact"),
            "information, débat ou avis à confirmer",
            None,
            "réponse écrite et point de suivi",
            status,
        ),
    )
    documents = list(
        CSEDocument(item.document_type, item.title, DocumentStatus.RECEIVED)
        for item in case.available_pieces
    )
    if "documents incomplets" in text or "sans donnees" in text:
        documents.append(CSEDocument("données d'impact", "données synthétiques attendues", DocumentStatus.PARTIAL, utility="évaluer les impacts", limitation="incomplet"))
    if "veille" in text:
        documents.append(CSEDocument("document de projet", "support synthétique fictif", DocumentStatus.RECEIVED, received_on="veille de la réunion", utility="préparer le débat", limitation="temps d'analyse à vérifier"))
    if "confidentialite" in text or "secret des affaires" in text:
        documents.append(CSEDocument("document demandé", "document synthétique non transmis", DocumentStatus.CONFIDENTIALITY_TO_EXAMINE, confidentiality_claimed=True, utility="répondre aux questions", limitation="motif et modalités à examiner"))
    anomalies = []
    for marker, label in (
        ("refus", "refus apparent à documenter"),
        ("tardiv", "délai potentiellement court"),
        ("veille", "temps d'analyse potentiellement court"),
        ("sans reponse", "absence de réponse déclarée"),
        ("non tenu", "engagement potentiellement non tenu"),
        ("pv non valide", "PV en attente"),
    ):
        if marker in text:
            anomalies.append(label)
    return CSEMeetingFacts(
        meeting_type,
        scheduled_date="date proche à confirmer" if "date proche" in text else None,
        convocation_date="date de réception à confirmer" if "convocation" in text else None,
        convocation_author="président du CSE à confirmer" if "convocation" in text else None,
        agenda_items=agenda,
        refused_items=(agenda[0].title,) if status is ItemStatus.APPARENTLY_REFUSED else (),
        documents=tuple(documents),
        opinion_requested=True if "avis" in text else None,
        opinion_rendered=True if any(marker in text for marker in ("avis rendu", "avis documente")) else False if "impossibilite de rendre" in text else None,
        reservations=("informations incomplètes",) if "reserve" in text or "incomplet" in text else (),
        resolution_declared=True if "resolution" in text else None,
        vote_declared=True if "vote" in text else None,
        minutes_status="en attente de validation" if "pv non valide" in text else "documenté" if "pv valide" in text else None,
        anomalies=tuple(anomalies),
        actions_already_taken=tuple(item.statement for item in case.established_facts),
    )


def _agenda_proposals(meeting: CSEMeetingFacts, text: str) -> tuple[AgendaItem, ...]:
    title = meeting.agenda_items[0].title
    if "reorganisation" in text:
        title = "Information et consultation potentielles sur le projet de réorganisation"
    elif "engagement" in text:
        title = "Suivi de l'engagement déclaré et vérification de son échéance"
    elif "document" in text:
        title = "Documents préparatoires, compléments et calendrier de réponse"
    return (
        AgendaItem(
            title,
            "faits et procédure à documenter",
            ("Quel est l'état exact ?", "Quelles pièces manquent ?", "Quelle prochaine échéance ?"),
            ("pièces préparatoires applicables",),
            "réponse, avis ou décision à préciser",
            meeting.scheduled_date,
            "inscription au PV et relance planifiée",
            meeting.agenda_items[0].status,
        ),
    )


def _questions(meeting, history):
    known_docs = bool(meeting.documents)
    rows = (
        (QuestionCategory.FACTUAL, 1, "Quel est le calendrier, le périmètre et le nombre de salariés concernés ?", "établir les faits", ("calendrier", "effectifs"), False),
        (QuestionCategory.PROCEDURAL, 1, "Quel mécanisme est prévu et quelle base est invoquée ?", "distinguer information, consultation et négociation", ("ordre du jour",), False),
        (QuestionCategory.PROCEDURAL, 1, "Quels documents sont disponibles, dans quelle version et depuis quelle date ?", "évaluer la préparation", ("liste des documents",), known_docs),
        (QuestionCategory.IMPACT, 2, "Quels impacts sur l'emploi, la charge, les horaires, la rémunération, la formation et l'égalité ?", "préparer le débat", ("données d'impact",), False),
        (QuestionCategory.FOLLOW_UP, 2, "Qui est responsable, quelle échéance et quel indicateur permettront le suivi ?", "suivre les engagements", ("PV", "engagement"), False),
        (QuestionCategory.FOLLOW_UP, 3, "Le sujet figure-t-il dans un ancien PV et le document source confirme-t-il la réponse ?", "vérifier l'historique", ("ancien PV",), bool(history)),
    )
    return tuple(CSEQuestion(category, priority, question, purpose, docs) for category, priority, question, purpose, docs, answered in rows if not answered)


def _timeline(meeting, confidence, commitments):
    events = []
    if meeting.agenda_items:
        events.append(MeetingTimelineEvent("agenda_request", None, False, "secrétaire ou élu à confirmer", MeetingEventKind.AGENDA_REQUEST, None, confidence))
    if meeting.convocation_date:
        events.append(MeetingTimelineEvent("convocation", meeting.convocation_date, False, meeting.convocation_author or "président à confirmer", MeetingEventKind.CONVOCATION, "convocation", confidence, meeting.scheduled_date, "temps de préparation à vérifier"))
    if meeting.documents:
        events.append(MeetingTimelineEvent("documents", None, False, "direction", MeetingEventKind.DOCUMENT_TRANSMISSION, ", ".join(item.document_type for item in meeting.documents), confidence, meeting.scheduled_date, "complétude à vérifier"))
    if meeting.scheduled_date or meeting.meeting_type is not MeetingType.UNKNOWN:
        events.append(MeetingTimelineEvent("meeting", meeting.scheduled_date, bool(meeting.scheduled_date), "CSE", MeetingEventKind.MEETING, None, confidence))
    if meeting.vote_declared:
        events.append(MeetingTimelineEvent("vote", None, False, "élus titulaires à confirmer", MeetingEventKind.VOTE, None, confidence))
    if meeting.opinion_rendered:
        events.append(MeetingTimelineEvent("opinion", None, False, "CSE", MeetingEventKind.OPINION, None, confidence))
    if meeting.resolution_declared:
        events.append(MeetingTimelineEvent("resolution", None, False, "CSE", MeetingEventKind.RESOLUTION, None, confidence))
    if meeting.minutes_status:
        events.append(MeetingTimelineEvent("minutes", None, False, "secrétaire", MeetingEventKind.MINUTES_DRAFT, "procès-verbal", confidence))
    if commitments:
        events.append(MeetingTimelineEvent("commitment", commitments[0].declared_on, False, commitments[0].author, MeetingEventKind.COMMITMENT_FOLLOW_UP, commitments[0].source_meeting, confidence, commitments[0].target_date, "engagement à confirmer dans la source"))
    return tuple(events)


def _commitments(text, history, confidence):
    results = []
    for item in history:
        if item.has_commitment:
            results.append(Commitment("engagement potentiel à vérifier dans le document source", "direction à confirmer", item.meeting_date, item.title, True, item.target_date, "responsable à confirmer", "preuve de réalisation", CommitmentStatus.TO_CONFIRM, "relance après vérification", None, confidence))
    if "engagement" in text and not results:
        results.append(Commitment("engagement déclaré à confirmer", "direction à confirmer", None, None, "oral" not in text, None, "responsable à confirmer", "confirmation écrite", CommitmentStatus.TO_CONFIRM, "demander inscription au PV", None, confidence))
    return tuple(results)


def _elected_position(meeting, history):
    return ContradictoryPosition(
        ("sujet potentiellement lié aux attributions", "besoin d'information et de suivi à documenter"),
        ("demandes, réserves et historique peuvent être tracés",),
        ("délais, compétence et complétude restent à confirmer",),
        tuple(item.title for item in meeting.documents) + tuple(item.title for item in history),
        ("ordre du jour", "versions", "réponses écrites"),
        ("information déjà suffisante", "demande hors périmètre"),
        ("cibler les questions et pièces manquantes",),
        ("report limité", "remise documentaire échelonnée", "suivi planifié"),
        ("régularité", "majorité", "qualification d'entrave"),
    )


def _employer_position(meeting):
    return ContradictoryPosition(
        ("documents déjà transmis selon l'employeur", "confidentialité ou impossibilité matérielle possibles", "réponse ultérieure annoncée possible"),
        ("pièces datées et réponses écrites si disponibles",),
        ("affirmations non documentées et pièces partielles",),
        tuple(item.title for item in meeting.documents),
        ("justification du refus", "version et date", "calendrier de réponse"),
        ("temps utile insuffisant", "impact collectif non traité"),
        ("formaliser les limites et proposer un calendrier",),
        ("accès encadré", "complément ciblé", "nouvelle présentation"),
        ("caractère suffisant", "délai applicable"),
    )


def _missing(meeting):
    result = []
    if meeting.scheduled_date is None:
        result.append("date de réunion")
    if meeting.convocation_date is None:
        result.append("date de convocation")
    if not meeting.documents:
        result.append("documents préparatoires")
    if meeting.opinion_requested is None:
        result.append("avis demandé ou non")
    if meeting.minutes_status is None:
        result.append("statut du procès-verbal")
    return tuple(result)


def _urgency(case, text):
    if any(marker in text for marker in ("demain", "immediat", "la veille")):
        return UrgencyLevel.IMMEDIATE
    if any(marker in text for marker in ("extraordinaire", "tardiv", "echeance proche", "refus")):
        return UrgencyLevel.URGENT
    return case.urgency


def _confidence(case, meeting):
    if case.established_facts and meeting.documents:
        return ConfidenceLevel.HIGH
    if case.declared_facts or meeting.documents:
        return ConfidenceLevel.MODERATE
    return ConfidenceLevel.LOW


def _case_text(case):
    return _normalize(" ".join([case.question] + [item.statement for item in case.declared_facts + case.established_facts + case.hypotheses]))


def _normalize(value):
    normalized = unicodedata.normalize("NFKD", str(value))
    return " ".join("".join(char for char in normalized if not unicodedata.combining(char)).lower().replace("’", " ").replace("'", " ").replace("-", " ").split())
