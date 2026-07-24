"""Deterministic articulation policy for R1A, R1B and R1C."""

from __future__ import annotations

import unicodedata

from .disciplinary_engine import needs_disciplinary_reasoning
from .models import SyndicalCaseInput
from .working_time_models import DomainArticulation


def articulate_syndical_domains(
    case: SyndicalCaseInput,
    *,
    working_time_relevant: bool,
) -> DomainArticulation:
    text = _normalize(
        " ".join(
            [case.question]
            + [item.statement for item in case.declared_facts]
            + [item.statement for item in case.established_facts]
        )
    )
    disciplinary = needs_disciplinary_reasoning(case)
    contract_change = any(
        marker in text
        for marker in (
            "modification",
            "modifie",
            "changement",
            "change",
            "passage de jour",
            "impose",
            "nouvelle organisation",
            "mutation",
            "avenant",
        )
    ) and any(
        marker in text
        for marker in (
            "horaire",
            "planning",
            "equipe",
            "poste",
            "cycle",
            "contrat",
            "organisation",
            "classification",
            "qualification",
        )
    )
    if disciplinary:
        complements = []
        if working_time_relevant:
            complements.append("R1C_WORKING_TIME")
        if contract_change:
            complements.append("R1A_CONTRACT_CHANGE")
        return DomainArticulation(
            "R1B_DISCIPLINARY",
            tuple(complements),
            "La procédure ou sanction reste principale ; les horaires et le contrat fournissent un contexte complémentaire.",
            "Aucune analyse complémentaire ne modifie la qualification disciplinaire provisoire.",
        )
    if contract_change:
        return DomainArticulation(
            "R1A_CONTRACT_CHANGE",
            ("R1C_WORKING_TIME",) if working_time_relevant else (),
            "La modification imposée reste principale ; R1C décrit les effets temporels et contreparties possibles.",
            "Aucune incidence de paie ni violation n'est tenue pour démontrée.",
        )
    if working_time_relevant:
        return DomainArticulation(
            "R1C_WORKING_TIME",
            (),
            "La demande porte principalement sur le temps, les repos, les compteurs ou les contreparties.",
            "Les écarts sont des anomalies à vérifier, jamais des erreurs certaines.",
        )
    return DomainArticulation(
        "R0_GENERAL",
        (),
        "Aucun indicateur spécialisé suffisant n'est détecté.",
        "Le rapport transverse prudent est conservé.",
    )


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return " ".join(
        "".join(char for char in normalized if not unicodedata.combining(char))
        .lower()
        .replace("’", " ")
        .replace("'", " ")
        .split()
    )
