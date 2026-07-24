"""Balanced working-time positions without payroll calculation."""

from __future__ import annotations

from .models import SyndicalCaseInput
from .working_time_models import (
    DocumentComparison,
    PotentialPayImpact,
    WorkingTimePosition,
    WorkingTimeSituation,
)


def analyze_working_time_positions(
    case: SyndicalCaseInput,
    situations: tuple[WorkingTimeSituation, ...],
    comparisons: tuple[DocumentComparison, ...],
    impacts: tuple[PotentialPayImpact, ...],
) -> tuple[WorkingTimePosition, WorkingTimePosition]:
    piece_labels = tuple(sorted(item.title for item in case.available_pieces))
    missing = tuple(
        sorted(
            {
                item
                for comparison in comparisons
                for item in comparison.additional_pieces
            }
        )
    )
    inconsistencies = tuple(
        item
        for comparison in comparisons
        for item in comparison.observed_differences
    )
    potential = tuple(sorted({item.impact_type for item in impacts}))
    employee = WorkingTimePosition(
        (
            "Le planning, les traces horaires et les compteurs doivent être rapprochés période par période.",
            "Une disponibilité imposée, une interruption ou une intervention réelle peut modifier la qualification du temps.",
        ),
        inconsistencies,
        potential,
        ("chronologie et pièces concordantes lorsqu'elles sont disponibles",),
        ("un compteur isolé ou un récit ne démontre pas seul une erreur",),
        piece_labels,
        missing,
        ("qualification, période ou règle applicable encore incertaine",),
    )
    employer = WorkingTimePosition(
        (
            "L'employeur peut invoquer le cycle, l'annualisation, la clôture de paie ou une compensation différée.",
            "Il peut distinguer l'astreinte sans intervention, le trajet habituel et une pause réellement libre.",
        ),
        inconsistencies,
        (
            "annualisation ou modulation à vérifier",
            "régularisation ou compensation déjà intégrée à vérifier",
        ),
        ("documents d'organisation et règles applicables s'ils sont produits",),
        ("les données du salarié peuvent être partielles ou porter sur une période différente",),
        piece_labels,
        missing,
        tuple(
            sorted(
                {
                    explanation
                    for comparison in comparisons
                    for explanation in comparison.alternative_explanations
                }
            )
        ),
    )
    return employee, employer
