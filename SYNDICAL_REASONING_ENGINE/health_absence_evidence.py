"""Metadata-only evidence policy for R1E."""

from __future__ import annotations

from .health_absence_models import CompetentActor, EvidenceCategory, HealthEvidence


def health_absence_evidence() -> tuple[HealthEvidence, ...]:
    rows = (
        ("minimal_leave_notice", "Justificatif minimal et dates", EvidenceCategory.ESSENTIAL, "Vérifier la période déclarée.", "Présence et période du justificatif.", "Ne révèle ni ne prouve un diagnostic.", CompetentActor.EMPLOYEE),
        ("payslip", "Bulletin synthétique concerné", EvidenceCategory.ESSENTIAL, "Repérer les rubriques et décalages.", "Traitement de paie observé.", "Ne démontre pas seul un droit ni une erreur.", CompetentActor.PAYROLL),
        ("daily_allowance_statement", "Décompte IJSS", EvidenceCategory.ESSENTIAL, "Tracer les périodes et versements administratifs.", "Éléments indiqués par la CPAM.", "Ne démontre pas le traitement employeur.", CompetentActor.CPAM),
        ("cpam_decision", "Décision CPAM lorsqu'elle existe", EvidenceCategory.ESSENTIAL, "Connaître le statut administratif.", "Décision notifiée.", "Ne remplace pas l'analyse contractuelle.", CompetentActor.CPAM),
        ("occupational_health_opinion", "Avis minimal du médecin du travail", EvidenceCategory.ESSENTIAL, "Identifier aptitude, inaptitude ou restrictions déclarées.", "Existence et portée administrative de l'avis.", "Aucun détail médical ne doit être reproduit.", CompetentActor.OCCUPATIONAL_PHYSICIAN),
        ("redeployment_proposal", "Proposition de reclassement", EvidenceCategory.ESSENTIAL, "Examiner la procédure et le poste proposé.", "Contenu de la proposition.", "Ne démontre pas seule l'exhaustivité des recherches.", CompetentActor.EMPLOYER),
        ("provident_notice", "Notice de prévoyance applicable", EvidenceCategory.ESSENTIAL, "Identifier une garantie potentielle.", "Conditions contractuelles publiées.", "Ne promet pas une prise en charge.", CompetentActor.PROVIDENT_BODY),
        ("employment_contract", "Contrat ou avenant", EvidenceCategory.USEFUL, "Vérifier le cadre contractuel.", "Fonctions et clauses documentées.", "Ne tranche pas une décision CPAM.", CompetentActor.HR),
        ("ineos_agreement", "Accord INEOS applicable", EvidenceCategory.USEFUL, "Vérifier les garanties conventionnelles.", "Règles documentées.", "L'applicabilité individuelle reste à vérifier.", CompetentActor.HR),
        ("schedule", "Planning synthétique", EvidenceCategory.USEFUL, "Comparer absence et temps planifié.", "Dates de travail planifiées.", "Ne démontre pas un paiement.", CompetentActor.EMPLOYER),
        ("payroll_history", "Historique synthétique des paiements", EvidenceCategory.USEFUL, "Repérer un décalage ou une régularisation.", "Évolution des rubriques.", "Aucun montant n'est calculé par R1E.", CompetentActor.PAYROLL),
        ("hr_exchange", "Échanges RH", EvidenceCategory.USEFUL, "Tracer demandes et réponses.", "Chronologie administrative.", "Ne tranche pas le fond médical.", CompetentActor.HR),
        ("cse_metadata", "PV CSE metadata-only", EvidenceCategory.COMPLEMENTARY, "Identifier un sujet collectif.", "Date et thème.", "Aucun contenu brut ni situation individuelle.", CompetentActor.CSE),
        ("practice_history", "Historique de pratique anonymisé", EvidenceCategory.COMPLEMENTARY, "Contextualiser.", "Pratique déclarée.", "Ne crée pas un droit individuel.", CompetentActor.HR),
    )
    return tuple(
        HealthEvidence(code, label, category, utility, demonstration, limit, "strictly_minimal_health_metadata", provider)
        for code, label, category, utility, demonstration, limit, provider in rows
    )
