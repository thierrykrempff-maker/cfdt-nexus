"""Evidence classification for change-of-work cases."""

from __future__ import annotations

from .contract_change_models import (
    ChangeDimension,
    EvidencePriority,
    EvidenceRequirement,
)


def required_evidence(
    dimensions: tuple[ChangeDimension, ...],
) -> tuple[EvidenceRequirement, ...]:
    evidence = [
        EvidenceRequirement("employment_contract", "Contrat de travail", EvidencePriority.ESSENTIAL, "Identifier les clauses initiales."),
        EvidenceRequirement("amendment", "Avenants", EvidencePriority.ESSENTIAL, "Vérifier les modifications déjà acceptées ou proposées."),
        EvidenceRequirement("employer_instruction", "Décision, note de service ou courriel", EvidencePriority.ESSENTIAL, "Établir le contenu et la date de la décision."),
        EvidenceRequirement("job_description", "Fiche de poste", EvidencePriority.USEFUL, "Comparer les missions avant et après."),
        EvidenceRequirement("organization_chart", "Organigramme", EvidencePriority.COMPLEMENTARY, "Situer le poste et l'équipe."),
        EvidenceRequirement("company_agreement", "Accord d'entreprise applicable", EvidencePriority.USEFUL, "Identifier les garanties locales."),
        EvidenceRequirement("collective_agreement", "Convention collective Chimie", EvidencePriority.USEFUL, "Contrôler qualification et classification."),
    ]
    if {
        ChangeDimension.WORKING_HOURS,
        ChangeDimension.DAY_TO_SHIFT,
        ChangeDimension.TEAM,
    }.intersection(dimensions):
        evidence.append(
            EvidenceRequirement("schedule", "Plannings avant et après", EvidencePriority.ESSENTIAL, "Mesurer les changements d'horaires et de cycle.")
        )
    if ChangeDimension.REORGANIZATION in dimensions:
        evidence.append(
            EvidenceRequirement("cse_minutes", "Information, ordre du jour et PV CSE", EvidencePriority.ESSENTIAL, "Vérifier le projet collectif et la consultation.")
        )
    if ChangeDimension.REMUNERATION in dimensions:
        evidence.append(
            EvidenceRequirement("payslip", "Bulletins de paie comparables", EvidencePriority.ESSENTIAL, "Identifier les éléments de rémunération affectés.")
        )
    by_type = {item.document_type: item for item in evidence}
    order = {
        EvidencePriority.ESSENTIAL: 0,
        EvidencePriority.USEFUL: 1,
        EvidencePriority.COMPLEMENTARY: 2,
    }
    return tuple(
        sorted(by_type.values(), key=lambda item: (order[item.priority], item.document_type))
    )
