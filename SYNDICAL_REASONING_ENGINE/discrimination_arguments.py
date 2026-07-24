"""Balanced employee and employer positions for R1D."""

from __future__ import annotations

from .discrimination_models import (
    ComparatorAssessment,
    ContradictoryPosition,
    QualificationHypothesis,
)
from .models import SyndicalCaseInput


def analyze_discrimination_positions(
    case: SyndicalCaseInput,
    hypotheses: tuple[QualificationHypothesis, ...],
    comparators: tuple[ComparatorAssessment, ...],
) -> tuple[ContradictoryPosition, ContradictoryPosition]:
    facts = tuple(item.statement for item in case.declared_facts + case.established_facts)
    situations = tuple(item.situation.value for item in hypotheses)
    comparator_limits = tuple(
        limitation for item in comparators for limitation in item.limitations
    )
    available = tuple(sorted(item.document_type for item in case.available_pieces))
    employee = ContradictoryPosition(
        arguments=(
            "Les faits déclarés doivent être examinés dans leur chronologie.",
            "Les indices concordants, leur répétition et les mesures défavorables peuvent justifier une investigation.",
        ),
        strengths=facts or ("La demande est formulée et doit être accueillie avec prudence.",),
        weaknesses=("Le lien causal et la qualification ne sont pas automatiquement démontrés.",),
        evidence=available,
        missing_evidence=tuple(sorted(set(case.missing_information) | {"chronologie complète", "comparateurs homogènes", "réponses de l'employeur"})),
        foreseeable_objections=("justification organisationnelle", "situations non comparables", "fait isolé"),
        possible_responses=("documenter les dates", "objectiver les comparaisons", "recueillir les réponses écrites"),
        unresolved_points=(
            "Le lien avec un critère protégé reste à établir.",
            f"Hypothèses concurrentes examinées : {', '.join(situations)}.",
        ),
    )
    employer = ContradictoryPosition(
        arguments=(
            "Une mesure peut reposer sur une justification objective étrangère à tout critère protégé.",
            "Des différences de fonctions, d'ancienneté, de résultats ou de contraintes peuvent limiter un comparateur.",
            "Des mesures de prévention ou d'enquête effectivement prises doivent être examinées.",
        ),
        strengths=("Les explications vérifiables et cohérentes dans le temps peuvent objectiver une décision.",),
        weaknesses=("Une explication tardive, variable ou non documentée peut être insuffisante.",),
        evidence=available,
        missing_evidence=("motifs contemporains de la décision", "critères appliqués à tous", "mesures de prévention"),
        foreseeable_objections=("proximité temporelle avec un signalement", "écarts répétés", "absence de réponse"),
        possible_responses=("produire les critères objectifs", "justifier la comparabilité", "tracer les mesures prises"),
        unresolved_points=comparator_limits or ("La comparabilité reste à instruire.",),
    )
    return employee, employer
