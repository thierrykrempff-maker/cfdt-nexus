"""Deterministic, fact-preserving chronology for R1D."""

from __future__ import annotations

import hashlib
import re
import unicodedata

from .discrimination_models import (
    StatementNature,
    TemporalPrecision,
    TimelineEvent,
    TimelineEventKind,
)
from .models import ConfidenceLevel, FactStatus, SyndicalCaseInput


def build_discrimination_timeline(
    case: SyndicalCaseInput,
) -> tuple[TimelineEvent, ...]:
    facts = case.declared_facts + case.established_facts + case.hypotheses
    events = []
    for index, fact in enumerate(facts):
        normalized = _normalize(fact.statement)
        event_id = hashlib.sha256(
            f"r1d\x1f{index}\x1f{fact.status.value}\x1f{normalized}".encode("utf-8")
        ).hexdigest()[:16]
        period, precision = _period(fact.statement, case.fact_period)
        events.append(
            TimelineEvent(
                event_id=event_id,
                kind=_kind(normalized),
                period=period,
                precision=precision,
                factual_description=fact.statement,
                nature=_nature(fact.status, normalized),
                source="employee_statement"
                if fact.status is not FactStatus.ESTABLISHED
                else "verified_case_fact",
                evidence_refs=tuple(sorted(fact.evidence_refs)),
                confidence=(
                    ConfidenceLevel.MODERATE
                    if fact.status is FactStatus.ESTABLISHED
                    else ConfidenceLevel.LOW
                ),
            )
        )
    return tuple(events)


def _period(statement: str, fallback: str | None) -> tuple[str | None, TemporalPrecision]:
    exact = re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", statement)
    if exact:
        return exact.group(0), TemporalPrecision.CERTAIN
    normalized = _normalize(statement)
    approximate_markers = ("depuis", "vers", "environ", "debut", "fin", "apres", "avant")
    if any(marker in normalized for marker in approximate_markers):
        return statement, TemporalPrecision.APPROXIMATE
    if fallback:
        return fallback, TemporalPrecision.APPROXIMATE
    return None, TemporalPrecision.UNKNOWN


def _kind(text: str) -> TimelineEventKind:
    mappings = (
        (("repete", "chaque semaine", "plusieurs fois"), TimelineEventKind.REPEATED_FACT),
        (("depuis", "pendant plusieurs mois"), TimelineEventKind.CONTINUOUS_PERIOD),
        (("signale", "signalement", "alerte"), TimelineEventKind.REPORT),
        (("reponse de l employeur", "enquete interne"), TimelineEventKind.EMPLOYER_RESPONSE),
        (("apres le signalement", "peu apres"), TimelineEventKind.LATER_MEASURE),
        (("arret de travail",), TimelineEventKind.DECLARED_SICK_LEAVE),
        (("changement de poste", "mutation"), TimelineEventKind.JOB_CHANGE),
        (("retrait de mission", "retire ses missions"), TimelineEventKind.DUTY_REMOVAL),
        (("evaluation defavorable", "evaluation negative"), TimelineEventKind.APPRAISAL_DEGRADATION),
        (("perte de prime", "baisse de prime"), TimelineEventKind.BONUS_LOSS),
        (("refus de formation",), TimelineEventKind.TRAINING_REFUSAL),
        (("temoin", "present lors"), TimelineEventKind.WITNESS_EVENT),
    )
    for markers, kind in mappings:
        if any(marker in text for marker in markers):
            return kind
    return TimelineEventKind.FACT


def _nature(status: FactStatus, text: str) -> StatementNature:
    if status is FactStatus.ESTABLISHED:
        return StatementNature.ESTABLISHED
    if status is FactStatus.HYPOTHESIS:
        return StatementNature.HYPOTHESIS
    if any(marker in text for marker in ("je ressens", "sentiment", "impression")):
        return StatementNature.FEELING
    if any(marker in text for marker in ("je pense", "selon moi", "parce que")):
        return StatementNature.INTERPRETATION
    return StatementNature.FACT


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return " ".join(
        "".join(char for char in normalized if not unicodedata.combining(char))
        .lower()
        .replace("’", " ")
        .replace("'", " ")
        .split()
    )
