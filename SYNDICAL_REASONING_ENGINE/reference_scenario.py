"""Synthetic reference scenario for LOT R0."""

from __future__ import annotations

from .models import (
    AvailablePiece,
    CaseFact,
    ConfidentialityLevel,
    FactStatus,
    SourceReference,
    SourceVerification,
    SyndicalCaseInput,
    UrgencyLevel,
)


REFERENCE_QUESTION = (
    "Un salarié de jour travaillant au laboratoire est informé qu'il doit "
    "rejoindre une équipe postée. Il affirme ne pas avoir donné son accord. "
    "Le CSE n'aurait pas été informé. Il souhaite savoir si l'employeur peut "
    "prendre cette décision et comment réagir."
)


def build_reference_case() -> SyndicalCaseInput:
    return SyndicalCaseInput(
        question=REFERENCE_QUESTION,
        declared_facts=(
            CaseFact("Le salarié déclare travailler actuellement de jour."),
            CaseFact("Il déclare avoir été informé d'un passage en équipe postée."),
            CaseFact("Il déclare ne pas avoir donné son accord."),
        ),
        hypotheses=(
            CaseFact(
                "Le projet pourrait avoir une dimension collective.",
                FactStatus.HYPOTHESIS,
            ),
            CaseFact(
                "Le CSE pourrait ne pas avoir été informé.",
                FactStatus.HYPOTHESIS,
            ),
        ),
        person_capacity="salarié accompagné par un délégué syndical",
        workplace_context="laboratoire — exemple entièrement synthétique",
        suspected_domains=(
            "employment_contract",
            "working_time",
            "payroll",
            "health_safety",
            "cse_consultation",
        ),
        available_pieces=(
            AvailablePiece(
                "synthetic-contract-reference",
                "employment_contract",
                "Contrat synthétique à vérifier",
                ConfidentialityLevel.INTERNAL,
                False,
            ),
        ),
        available_sources=(
            SourceReference(
                "synthetic-labour-code",
                "Code du travail — référence à vérifier",
                "labour_code",
                "Législateur",
                "https://www.legifrance.gouv.fr",
                SourceVerification.UNVERIFIED,
            ),
        ),
        urgency=UrgencyLevel.PROMPT,
        confidentiality=ConfidentialityLevel.INTERNAL,
        desired_outcome="comprendre la décision et préparer une réaction graduée",
        missing_information=(
            "date d'effet envisagée",
            "contenu exact de la décision",
            "accords INEOS applicables",
            "information remise au CSE",
            "effets précis sur la rémunération et les contraintes personnelles",
        ),
    )
