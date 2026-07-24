"""Deterministic articulation of R1D with R1A, R1B and R1C."""

from __future__ import annotations

import unicodedata

from .discrimination_models import DomainArticulation
from .models import SyndicalCaseInput


def articulate_discrimination_domains(case: SyndicalCaseInput) -> DomainArticulation:
    text = _case_text(case)
    sanction = any(marker in text for marker in ("sanction", "disciplinaire", "avertissement", "mise a pied"))
    retaliation = any(marker in text for marker in ("apres signalement", "apres avoir signale", "represailles"))
    harassment = any(marker in text for marker in ("harcelement", "humiliation repetee", "critiques repetees", "messages repetes a connotation sexuelle"))
    contract_change = any(
        marker in text
        for marker in ("mutation", "changement de poste", "modification imposee des fonctions")
    )
    union = any(marker in text for marker in ("mandat", "representant", "syndical", "elu"))
    working_time = any(marker in text for marker in ("horaire", "travail de nuit", "planning", "temps de travail"))

    if sanction and retaliation and not harassment:
        return DomainArticulation(
            "R1B_DISCIPLINARY",
            ("R1D_DISCRIMINATION_HARASSMENT",),
            "La sanction reste l'objet principal ; R1D examine prudemment une représaille possible.",
            "La proximité temporelle ne démontre pas seule un lien causal.",
        )
    if contract_change and union and not harassment:
        complements = ["R1D_DISCRIMINATION_HARASSMENT"]
        if working_time:
            complements.append("R1C_WORKING_TIME")
        return DomainArticulation(
            "R1A_CONTRACT_CHANGE",
            tuple(complements),
            "La modification du poste reste principale ; R1D examine un traitement syndical défavorable possible.",
            "Aucun motif discriminatoire n'est présumé.",
        )
    if working_time and not harassment and not any(
        marker in text for marker in ("discrimination", "inegalite", "traitement defavorable")
    ):
        return DomainArticulation(
            "R1C_WORKING_TIME",
            ("R1D_DISCRIMINATION_HARASSMENT",),
            "L'organisation du temps reste principale ; R1D vérifie seulement une différence ciblée éventuelle.",
            "Une différence d'horaire ne constitue pas automatiquement une discrimination.",
        )
    complements = []
    if sanction:
        complements.append("R1B_DISCIPLINARY")
    if contract_change:
        complements.append("R1A_CONTRACT_CHANGE")
    if working_time:
        complements.append("R1C_WORKING_TIME")
    return DomainArticulation(
        "R1D_DISCRIMINATION_HARASSMENT",
        tuple(complements),
        "Les indices de harcèlement, discrimination, égalité ou représailles constituent l'objet principal prudent.",
        "Aucune discrimination ni aucun harcèlement n'est tenu pour établi automatiquement.",
    )


def _case_text(case: SyndicalCaseInput) -> str:
    value = " ".join(
        [case.question]
        + [item.statement for item in case.declared_facts]
        + [item.statement for item in case.established_facts]
    )
    normalized = unicodedata.normalize("NFKD", value)
    return " ".join(
        "".join(char for char in normalized if not unicodedata.combining(char))
        .lower()
        .replace("’", " ")
        .replace("'", " ")
        .split()
    )
