"""Eighteen anonymous, synthetic R2B scenarios."""

from __future__ import annotations

from .models import CaseFact, SyndicalCaseInput, UrgencyLevel


def _case(question: str, *facts: str) -> SyndicalCaseInput:
    return SyndicalCaseInput(
        question,
        declared_facts=tuple(CaseFact(item) for item in facts),
        person_capacity="élu ou délégué syndical fictif",
        workplace_context="instance synthétique sans donnée réelle",
        suspected_domains=("cse", "cse_operation"),
        urgency=UrgencyLevel.PROMPT,
        desired_outcome="préparer le fonctionnement et le suivi de manière prudente",
        missing_information=("dates certaines", "documents et versions", "régime applicable"),
    )


def cse_operation_scenarios() -> dict[str, SyndicalCaseInput]:
    return {
        "agenda_refusal": _case("Le secrétaire demande un point sur une réorganisation mais il n'apparaît pas à l'ordre du jour.", "Le refus apparent doit être documenté."),
        "apparently_late_convocation": _case("Une convocation CSE arrive tardivement et la date de réunion est proche.", "Le type de réunion reste à confirmer."),
        "incomplete_documents": _case("Les documents CSE sont incomplets, sans données d'effectifs ni calendrier.", "Une présentation générale est déclarée."),
        "documents_day_before": _case("Les documents sont transmis la veille de la réunion CSE.", "Le temps d'analyse est à vérifier."),
        "unanswered_question": _case("Une question CSE importante reste sans réponse pendant plusieurs réunions.", "Une absence persistante de réponse est déclarée."),
        "oral_unrecorded_response": _case("La direction donne une réponse orale non formalisée dans le PV CSE.", "La réponse doit être confirmée."),
        "opinion_with_reservations": _case("Le CSE prépare un avis avec réserves car certains documents restent incomplets.", "Certains éléments sont disponibles."),
        "unable_to_opine": _case("Les élus évoquent une impossibilité de rendre un avis faute de documents.", "La validité de la démarche reste à confirmer."),
        "unmet_commitment": _case("Un ancien PV CSE metadata-only signale un engagement potentiel non tenu.", "Le document source doit être vérifié."),
        "recurring_subject": _case("Le même sujet CSE revient plusieurs réunions sans réponse claire.", "Le suivi paraît récurrent."),
        "confidentiality_claim": _case("La direction refuse un document CSE en invoquant la confidentialité et le secret des affaires.", "Le motif doit être examiné."),
        "cse_union_confusion": _case("Un sujet de négociation syndicale est adressé au CSE.", "L'acteur compétent doit être distingué."),
        "vote_resolution": _case("Le CSE prépare un vote et une résolution pour demander des documents et un suivi.", "La procédure et la majorité restent à confirmer."),
        "apparently_regular": _case("Convocation CSE, documents, réunion, questions et avis rendu sont documentés.", "Les éléments favorables sont déclarés."),
        "recurring_dysfunction": _case("Plusieurs réunions CSE montrent des refus récurrents et des réponses absentes.", "Le risque d'entrave reste à vérifier."),
        "extraordinary_meeting": _case("Les élus demandent une réunion extraordinaire CSE sur un sujet urgent.", "Les conditions applicables restent à vérifier."),
        "unvalidated_minutes": _case("Un PV CSE non validé bloque le suivi d'un engagement.", "Le statut de la source doit être vérifié."),
        "individual_collective_context": _case("La sanction d'un salarié est évoquée en réunion CSE dans un contexte collectif.", "R1B reste principal sur la sanction."),
    }
