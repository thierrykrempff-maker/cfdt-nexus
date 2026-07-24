"""Context-aware source hierarchy without document retrieval."""

from __future__ import annotations

from .models import SourceAssessment, SourceReference, SourceVerification


SOURCE_BASE_RANKS = {
    "ineos_agreement": 10,
    "internal_documented_practice": 15,
    "collective_agreement_chemistry": 20,
    "labour_code": 25,
    "regulation": 30,
    "case_law": 35,
    "local_law": 38,
    "official_administration": 40,
    "defenseur_droits": 42,
    "cnil": 42,
    "ministere_travail": 44,
    "service_public": 48,
    "dreets": 48,
    "inrs": 50,
    "anact": 52,
    "carsat": 52,
    "cpam": 52,
    "urssaf": 52,
    "agirc_arrco": 52,
    "cse_minutes": 60,
    "employee_statement": 80,
    "other": 90,
}


def rank_sources(
    sources: tuple[SourceReference, ...],
    domains: tuple[str, ...],
) -> tuple[SourceAssessment, ...]:
    """Rank only supplied sources and explain contextual adjustments."""

    ranked = []
    for source in sources:
        rank = SOURCE_BASE_RANKS.get(source.source_type, SOURCE_BASE_RANKS["other"])
        rationale = ["base authority and applicability"]
        if source.internal and source.source_type == "ineos_agreement":
            rationale.append("enterprise agreement requires comparison with superior norms")
        if source.source_type == "case_law":
            rationale.append("case law requires fact-specific analysis")
        if source.verification is not SourceVerification.VERIFIED:
            rank += 20
            rationale.append("source is not verified")
        if "health_safety" in domains and source.source_type == "inrs":
            rank -= 5
            rationale.append("prevention source is directly relevant")
        if "personal_data" in domains and source.source_type == "cnil":
            rank -= 5
            rationale.append("data-protection authority is directly relevant")
        ranked.append(SourceAssessment(source, max(rank, 1), "; ".join(rationale)))
    return tuple(sorted(ranked, key=lambda item: (item.rank, item.source.source_id)))


def hierarchy_labels(assessments: tuple[SourceAssessment, ...]) -> tuple[str, ...]:
    if not assessments:
        return ("Aucune source fournie ou vérifiée.",)
    return tuple(
        f"{item.rank:02d} — {item.source.title} ({item.source.verification.value})"
        for item in assessments
    )
