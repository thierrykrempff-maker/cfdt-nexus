"""Minimal deterministic chronology without medical detail."""

from __future__ import annotations

import hashlib
import re
import unicodedata

from .health_absence_models import (
    CompetentActor,
    EventStatus,
    HealthEventKind,
    HealthTimelineEvent,
)
from .models import ConfidenceLevel, FactStatus, SyndicalCaseInput


def build_health_timeline(case: SyndicalCaseInput) -> tuple[HealthTimelineEvent, ...]:
    events = []
    for index, fact in enumerate(case.declared_facts + case.established_facts + case.hypotheses):
        text = _normalize(fact.statement)
        event_id = hashlib.sha256(f"r1e\x1f{index}\x1f{text}".encode()).hexdigest()[:16]
        events.append(
            HealthTimelineEvent(
                event_id,
                _kind(text),
                _period(fact.statement, case.fact_period),
                bool(re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", fact.statement)),
                _actor(text),
                _document(text),
                EventStatus.DOCUMENTED if fact.status is FactStatus.ESTABLISHED else (EventStatus.HYPOTHESIS if fact.status is FactStatus.HYPOTHESIS else EventStatus.DECLARED),
                ConfidenceLevel.MODERATE if fact.status is FactStatus.ESTABLISHED else ConfidenceLevel.LOW,
                ("traitement juridique, administratif ou de paie à vérifier",),
                None,
            )
        )
    return tuple(events)


def _kind(text: str) -> HealthEventKind:
    mappings = (
        (("prolongation",), HealthEventKind.EXTENSION),
        (("transmis a l employeur", "envoye a l employeur"), HealthEventKind.EMPLOYER_TRANSMISSION),
        (("teletransmis", "transmis a la cpam"), HealthEventKind.CPAM_TRANSMISSION),
        (("accident declare", "declaration d accident"), HealthEventKind.ACCIDENT_REPORT),
        (("reserve employeur", "employeur emet des reserves"), HealthEventKind.EMPLOYER_RESERVATIONS),
        (("instruction cpam",), HealthEventKind.CPAM_REVIEW),
        (("decision cpam", "reconnaissance acceptee", "refus cpam"), HealthEventKind.CPAM_DECISION),
        (("ijss versee", "paiement cpam"), HealthEventKind.DAILY_ALLOWANCE_PAYMENT),
        (("maintien",), HealthEventKind.SALARY_MAINTENANCE),
        (("regularisation",), HealthEventKind.PAYROLL_ADJUSTMENT),
        (("visite de prereprise",), HealthEventKind.PRE_RETURN_VISIT),
        (("visite de reprise",), HealthEventKind.RETURN_VISIT),
        (("avis du medecin du travail", "avis d inaptitude"), HealthEventKind.OCCUPATIONAL_HEALTH_OPINION),
        (("amenagement",), HealthEventKind.WORK_ADJUSTMENT),
        (("recherche de reclassement",), HealthEventKind.REDEPLOYMENT_SEARCH),
        (("proposition de reclassement",), HealthEventKind.REDEPLOYMENT_PROPOSAL),
        (("reprend", "reprise"), HealthEventKind.RETURN_TO_WORK),
        (("licenciement", "rupture"), HealthEventKind.CONTRACT_TERMINATION),
        (("dossier prevoyance",), HealthEventKind.PROVIDENT_REQUEST),
        (("reponse assureur",), HealthEventKind.INSURER_RESPONSE),
        (("arret",), HealthEventKind.INITIAL_LEAVE),
    )
    for markers, kind in mappings:
        if any(marker in text for marker in markers):
            return kind
    return HealthEventKind.DECLARED_HEALTH_EVENT


def _actor(text: str) -> CompetentActor:
    if "cpam" in text or "ijss" in text:
        return CompetentActor.CPAM
    if "medecin du travail" in text or "inaptitude" in text:
        return CompetentActor.OCCUPATIONAL_PHYSICIAN
    if "prevoyance" in text or "assureur" in text:
        return CompetentActor.PROVIDENT_BODY
    if "employeur" in text or "reclassement" in text:
        return CompetentActor.EMPLOYER
    return CompetentActor.EMPLOYEE


def _document(text: str) -> str | None:
    for marker, document in (
        ("arret", "sick_leave_notice"),
        ("decision cpam", "cpam_decision"),
        ("ijss", "daily_allowance_statement"),
        ("bulletin", "payslip"),
        ("avis", "occupational_health_opinion"),
        ("reclassement", "redeployment_document"),
        ("prevoyance", "provident_notice"),
    ):
        if marker in text:
            return document
    return None


def _period(statement: str, fallback: str | None) -> str | None:
    match = re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", statement)
    return match.group(0) if match else fallback


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return " ".join("".join(c for c in normalized if not unicodedata.combining(c)).lower().replace("’", " ").replace("'", " ").split())
