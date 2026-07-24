"""Observable confidence and caution rules."""

from __future__ import annotations

from .models import (
    ConfidenceLevel,
    SourceAssessment,
    SourceVerification,
    SyndicalCaseInput,
    UrgencyLevel,
)


def determine_confidence(
    case: SyndicalCaseInput,
    sources: tuple[SourceAssessment, ...],
    contradictions: int,
) -> ConfidenceLevel:
    score = 0
    score += min(len(case.established_facts), 3)
    score += min(sum(item.verified for item in case.available_pieces), 2)
    score += min(
        sum(
            item.source.verification is SourceVerification.VERIFIED
            for item in sources
        ),
        3,
    )
    score -= min(len(case.missing_information), 3)
    score -= min(contradictions * 2, 4)
    if not case.fact_period:
        score -= 1
    if score >= 5:
        return ConfidenceLevel.HIGH
    if score >= 2:
        return ConfidenceLevel.MODERATE
    return ConfidenceLevel.LOW


def caution_alerts(case: SyndicalCaseInput, domains: tuple[str, ...]) -> tuple[str, ...]:
    alerts = []
    if case.urgency in {UrgencyLevel.URGENT, UrgencyLevel.IMMEDIATE}:
        alerts.append("Vérifier immédiatement les délais et mesures de protection.")
    domain_alerts = {
        "health_safety": "Évaluer sans délai tout danger grave ou urgence médicale.",
        "disciplinary": "Préserver les délais de contestation et le contradictoire.",
        "discrimination_harassment": "Protéger la personne et préserver les preuves sans exposition inutile.",
        "personal_data": "Limiter strictement les données personnelles utilisées.",
        "cse_consultation": "Vérifier si une information ou consultation du CSE est obligatoire.",
        "employment_contract": "Distinguer modification du contrat et changement des conditions de travail.",
    }
    for domain in domains:
        if domain in domain_alerts:
            alerts.append(domain_alerts[domain])
    if case.confidentiality.value in {"confidential", "restricted"}:
        alerts.append("Ne diffuser que les métadonnées et éléments strictement nécessaires.")
    return tuple(dict.fromkeys(alerts))
