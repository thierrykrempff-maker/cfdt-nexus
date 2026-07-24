"""Working-time evidence with explicit probative limits."""

from __future__ import annotations

from .working_time_models import EvidenceCategory, WorkingTimeEvidence


def working_time_evidence() -> tuple[WorkingTimeEvidence, ...]:
    evidence = (
        WorkingTimeEvidence("official_schedule", "Planning concerné", EvidenceCategory.ESSENTIAL, "Fixer l'horaire prévu.", "Les heures planifiées.", "Les heures réellement travaillées."),
        WorkingTimeEvidence("timeclock", "Badgeages concernés", EvidenceCategory.ESSENTIAL, "Tracer les passages enregistrés.", "Des horaires de pointage.", "La qualification juridique ou le travail effectif entre deux pointages."),
        WorkingTimeEvidence("company_agreement", "Accord applicable", EvidenceCategory.ESSENTIAL, "Identifier la règle locale.", "Les garanties conventionnelles applicables.", "Les faits réellement survenus."),
        WorkingTimeEvidence("payslip", "Bulletin synthétique concerné", EvidenceCategory.ESSENTIAL, "Repérer les rubriques présentes.", "Le traitement affiché sur une période.", "L'exactitude complète de la paie ou la cause d'une absence."),
        WorkingTimeEvidence("kelio_statement", "Relevé Kelio synthétique", EvidenceCategory.ESSENTIAL, "Comparer événements et compteurs.", "Les données enregistrées dans le compteur.", "Une créance ou une erreur de paie définitive."),
        WorkingTimeEvidence("event_timestamp", "Date et heure précises", EvidenceCategory.ESSENTIAL, "Reconstituer la chronologie.", "La séquence temporelle déclarée ou tracée.", "La qualification sans source applicable."),
        WorkingTimeEvidence("employment_contract", "Contrat", EvidenceCategory.USEFUL, "Identifier les clauses horaires.", "Le cadre contractualisé.", "L'organisation réellement appliquée."),
        WorkingTimeEvidence("amendment", "Avenant", EvidenceCategory.USEFUL, "Identifier une évolution acceptée.", "Une modification formalisée.", "Tous les usages et accords applicables."),
        WorkingTimeEvidence("service_note", "Note de service", EvidenceCategory.USEFUL, "Documenter une consigne.", "L'organisation annoncée.", "Son application individuelle effective."),
        WorkingTimeEvidence("intervention_sheet", "Feuille d'intervention", EvidenceCategory.USEFUL, "Tracer une intervention d'astreinte.", "L'existence et les horaires renseignés.", "Le paiement ou le repos effectivement accordé."),
        WorkingTimeEvidence("emails", "Courriels", EvidenceCategory.USEFUL, "Conserver les instructions et alertes.", "Une demande ou information datée.", "La totalité du temps travaillé."),
        WorkingTimeEvidence("counter_history", "Historique de compteur", EvidenceCategory.USEFUL, "Identifier les évolutions.", "Les mouvements enregistrés.", "La cause juridique ou technique d'un mouvement."),
        WorkingTimeEvidence("team_calendar", "Calendrier des équipes", EvidenceCategory.USEFUL, "Situer le salarié dans un cycle.", "L'équipe et le cycle prévus.", "Les remplacements réellement effectués."),
        WorkingTimeEvidence("call_log", "Relevé d'appels synthétique", EvidenceCategory.USEFUL, "Corroborer un rappel.", "L'existence et l'heure d'un appel.", "La durée complète de l'intervention."),
        WorkingTimeEvidence("witness_statements", "Témoignages", EvidenceCategory.COMPLEMENTARY, "Corroborer la pratique.", "Des observations factuelles.", "Le temps exact ou une règle applicable."),
        WorkingTimeEvidence("cse_minutes", "PV CSE metadata-only", EvidenceCategory.COMPLEMENTARY, "Identifier un contexte collectif.", "Un sujet ou une décision documentée.", "La situation individuelle."),
        WorkingTimeEvidence("usual_practice", "Pratique habituelle documentée", EvidenceCategory.COMPLEMENTARY, "Comparer la répétition.", "Une régularité factuelle.", "La conformité juridique."),
        WorkingTimeEvidence("prior_adjustments", "Historique de régularisations", EvidenceCategory.COMPLEMENTARY, "Identifier des corrections antérieures.", "Des traitements passés.", "Le traitement dû dans le cas présent."),
    )
    order = {EvidenceCategory.ESSENTIAL: 0, EvidenceCategory.USEFUL: 1, EvidenceCategory.COMPLEMENTARY: 2}
    return tuple(sorted(evidence, key=lambda item: (order[item.category], item.document_type)))
