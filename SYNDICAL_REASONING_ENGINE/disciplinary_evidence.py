"""Evidence requirements for disciplinary reasoning."""

from __future__ import annotations

from .contract_change_models import EvidencePriority, EvidenceRequirement
from .disciplinary_models import (
    DisciplinaryQualification,
    DisciplinaryQualificationCandidate,
)


def disciplinary_evidence(
    candidates: tuple[DisciplinaryQualificationCandidate, ...],
) -> tuple[EvidenceRequirement, ...]:
    qualifications = {item.qualification for item in candidates}
    evidence = [
        EvidenceRequirement("meeting_invitation", "Convocation", EvidencePriority.ESSENTIAL, "Vérifier date, objet et forme de la convocation."),
        EvidenceRequirement("sanction_letter", "Courrier de sanction ou décision", EvidencePriority.ESSENTIAL, "Identifier mesure, motifs et notification."),
        EvidenceRequirement("interview_record", "Notes ou compte rendu d'entretien", EvidencePriority.USEFUL, "Conserver les explications contradictoires."),
        EvidenceRequirement("internal_rules", "Règlement intérieur applicable", EvidencePriority.ESSENTIAL, "Vérifier sanctions et garanties prévues."),
        EvidenceRequirement("witness_statements", "Témoignages datés", EvidencePriority.USEFUL, "Établir ou contester les faits."),
        EvidenceRequirement("contemporaneous_writings", "Mails et écrits contemporains", EvidencePriority.USEFUL, "Reconstituer la chronologie."),
        EvidenceRequirement("schedules", "Plannings et badgeages", EvidencePriority.USEFUL, "Vérifier présence, horaires et contexte."),
        EvidenceRequirement("lawful_video_reference", "Éléments vidéo juridiquement pertinents", EvidencePriority.COMPLEMENTARY, "Identifier l'existence et la licéité avant toute utilisation."),
        EvidenceRequirement("company_agreements", "Accords INEOS applicables", EvidencePriority.USEFUL, "Vérifier les garanties locales."),
        EvidenceRequirement("cse_minutes", "PV CSE pertinents", EvidencePriority.COMPLEMENTARY, "Rechercher un contexte collectif sans exposer de contenu brut."),
        EvidenceRequirement("disciplinary_file", "Dossier disciplinaire communiqué", EvidencePriority.ESSENTIAL, "Recenser les pièces effectivement invoquées."),
    ]
    if DisciplinaryQualification.PROTECTED_EMPLOYEE in qualifications:
        evidence.extend(
            (
                EvidenceRequirement("mandate_evidence", "Justificatif du mandat et de ses dates", EvidencePriority.ESSENTIAL, "Qualifier la protection potentielle."),
                EvidenceRequirement("administrative_authorization", "Décision ou saisine de l'inspection du travail", EvidencePriority.ESSENTIAL, "Vérifier l'étape administrative éventuelle."),
            )
        )
    order = {
        EvidencePriority.ESSENTIAL: 0,
        EvidencePriority.USEFUL: 1,
        EvidencePriority.COMPLEMENTARY: 2,
    }
    unique = {item.document_type: item for item in evidence}
    return tuple(sorted(unique.values(), key=lambda item: (order[item.priority], item.document_type)))
