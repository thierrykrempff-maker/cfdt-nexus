"""Deterministic articulation of R1E with R1A to R1D."""

from __future__ import annotations

import unicodedata

from .health_absence_models import HealthDomainArticulation
from .models import SyndicalCaseInput


def articulate_health_domains(case: SyndicalCaseInput) -> HealthDomainArticulation:
    text = _text(case)
    disciplinary = any(marker in text for marker in ("sanction", "disciplinaire", "avertissement"))
    harassment = "harcelement" in text
    contract_change = any(marker in text for marker in ("changement de poste", "retrait de mission", "mutation"))
    pay_time = any(marker in text for marker in ("ijss", "maintien", "subrogation", "bulletin", "astreinte", "horaire"))
    health_core = any(marker in text for marker in ("inaptitude", "reclassement", "accident", "arret", "reprise", "prevoyance", "mutuelle"))

    if disciplinary and "absence" in text:
        return HealthDomainArticulation("R1B_DISCIPLINARY", ("R1E_HEALTH_ABSENCE",), "La sanction est principale ; R1E vérifie la justification et le traitement administratif de l'absence.", "Aucune faute ni justification n'est présumée.")
    if harassment and "arret" in text:
        return HealthDomainArticulation("R1D_DISCRIMINATION_HARASSMENT", ("R1E_HEALTH_ABSENCE",), "R1D reste principal ; R1E traite l'arrêt sans diagnostic.", "Aucun lien médical ou causal n'est déduit.")
    if contract_change and not health_core:
        return HealthDomainArticulation("R1A_CONTRACT_CHANGE", ("R1E_HEALTH_ABSENCE",), "La modification du poste reste principale ; R1E examine reprise et aménagement.", "Aucune incapacité n'est déduite.")
    complements = []
    if contract_change or "reclassement" in text:
        complements.append("R1A_CONTRACT_CHANGE")
    if disciplinary:
        complements.append("R1B_DISCIPLINARY")
    if pay_time:
        complements.append("R1C_WORKING_TIME")
    if any(marker in text for marker in ("discrimination", "etat de sante", "handicap", "retrait de mission")):
        complements.append("R1D_DISCRIMINATION_HARASSMENT")
    return HealthDomainArticulation("R1E_HEALTH_ABSENCE", tuple(dict.fromkeys(complements)), "La demande porte principalement sur l'absence, la reprise, l'indemnisation potentielle ou la protection sociale.", "Aucune décision médicale, CPAM ou de paie n'est anticipée.")


def _text(case: SyndicalCaseInput) -> str:
    value = " ".join([case.question] + [item.statement for item in case.declared_facts + case.established_facts])
    normalized = unicodedata.normalize("NFKD", value)
    return " ".join("".join(c for c in normalized if not unicodedata.combining(c)).lower().replace("’", " ").replace("'", " ").split())
