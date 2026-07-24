"""Balanced employee and employer position analysis."""

from __future__ import annotations

from .contract_change_models import ChangeDimension, PositionAnalysis
from .models import SyndicalCaseInput


def analyze_positions(
    case: SyndicalCaseInput,
    dimensions: tuple[ChangeDimension, ...],
) -> tuple[PositionAnalysis, PositionAnalysis]:
    employee_arguments = [
        "Le salarié peut demander la qualification exacte et le fondement du changement.",
        "Une clause contractualisée ou un impact substantiel doit être vérifié avant conclusion.",
    ]
    employee_strengths = [
        "Une décision écrite, le contrat et les avenants permettent une comparaison objective."
    ]
    employee_weaknesses = [
        "L'absence de contrat, d'avenant ou de décision écrite empêche une qualification certaine."
    ]
    employer_arguments = [
        "L'employeur peut invoquer son pouvoir d'organisation pour certains changements.",
        "Il peut invoquer une clause contractuelle ou un accord applicable, sous réserve de leur validité et de leur portée.",
    ]
    employer_foundations = [
        "Nécessité d'organisation, caractère temporaire ou absence d'altération d'un élément contractualisé."
    ]
    employer_to_prove = [
        "Le périmètre exact du changement, son fondement, sa proportionnalité et le respect des procédures."
    ]
    if ChangeDimension.REMUNERATION in dimensions:
        employee_arguments.append("Toute incidence sur la rémunération doit être identifiée précisément.")
        employer_to_prove.append("L'absence de perte ou la base conventionnelle de chaque modification de rémunération.")
    if ChangeDimension.REORGANIZATION in dimensions:
        employee_arguments.append("La dimension collective peut appeler une information ou consultation du CSE.")
        employer_to_prove.append("Le respect des attributions et du calendrier d'information-consultation du CSE.")
    if not case.established_facts:
        employee_weaknesses.append("Les éléments sont à ce stade déclarés, non établis.")
    return (
        PositionAnalysis(tuple(employee_arguments), tuple(employee_strengths), tuple(employee_weaknesses)),
        PositionAnalysis(tuple(employer_arguments), tuple(employer_foundations), tuple(employer_to_prove)),
    )
