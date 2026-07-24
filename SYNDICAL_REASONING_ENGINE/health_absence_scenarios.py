"""Fifteen anonymous synthetic R1E scenarios."""

from __future__ import annotations

from .models import CaseFact, SyndicalCaseInput


def _case(question: str, fact: str, domains=("protection_sociale",)) -> SyndicalCaseInput:
    return SyndicalCaseInput(question, declared_facts=(CaseFact(fact),), suspected_domains=domains)


def health_absence_scenarios() -> dict[str, SyndicalCaseInput]:
    return {
        "sick_leave_maintenance": _case("Forte baisse de rémunération pendant un arrêt maladie : IJSS, subrogation, maintien et prévoyance.", "Le traitement reste à rapprocher sans calcul."),
        "missing_ijss": _case("La CPAM indique un paiement IJSS non retrouvé clairement.", "Le décompte et le bulletin restent à comparer."),
        "work_accident_pending": _case("Accident du travail déclaré, reconnaissance en attente de décision CPAM.", "La reconnaissance n'est pas acquise."),
        "employer_reservations": _case("L'employeur émet des réserves sur un accident du travail déclaré.", "La CPAM reste compétente pour instruire."),
        "return_without_visit": _case("Reprise après arrêt sans visite de reprise.", "Le caractère requis de la visite reste à vérifier."),
        "therapeutic_part_time": _case("Temps partiel thérapeutique : salaire, IJSS et horaires incompris.", "Aucun montant réel ne doit être calculé."),
        "adjustment_refused": _case("Aménagement de poste recommandé ou demandé non mis en œuvre.", "Avis, faisabilité et justification restent à distinguer."),
        "unfitness_redeployment": _case("Inaptitude déclarée et proposition de reclassement estimée inadaptée.", "L'avis minimal et la proposition doivent être examinés."),
        "no_redeployment_offer": _case("Après inaptitude déclarée, l'employeur affirme qu'aucun reclassement n'existe.", "Les recherches doivent être documentées."),
        "provident_not_opened": _case("Arrêt long et aucun dossier prévoyance ne semble ouvert.", "La garantie potentielle et les conditions restent à vérifier."),
        "mutual_portability": _case("Un ancien salarié interroge la portabilité de la mutuelle.", "Les conditions et délais doivent être vérifiés."),
        "leave_and_sickness": _case("Congés et maladie : acquisition, report ou compteur contesté.", "Le compteur et les règles applicables sont à vérifier."),
        "absence_discipline": _case("Sanction pour absence dont la justification est discutée.", "R1B reste principal et R1E complémentaire.", ("disciplinary_procedure", "absence")),
        "duties_removed_after_leave": _case("Retrait de missions après retour d'arrêt maladie, discrimination liée à l'état de santé évoquée.", "R1A, R1D et R1E doivent être articulés.", ("contrat_travail", "discrimination", "protection_sociale")),
        "possible_occupational_unfitness": _case("Inaptitude d'origine professionnelle possible et reclassement.", "L'origine reste une donnée à vérifier."),
    }
