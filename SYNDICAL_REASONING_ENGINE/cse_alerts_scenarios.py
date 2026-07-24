"""Twenty anonymous, synthetic and metadata-only R2C scenarios."""

from __future__ import annotations

from .models import CaseFact, SyndicalCaseInput, UrgencyLevel


def _case(question: str, *facts: str) -> SyndicalCaseInput:
    return SyndicalCaseInput(
        question,
        declared_facts=tuple(CaseFact(item) for item in facts),
        person_capacity="élu ou délégué syndical fictif",
        workplace_context="instance synthétique sans donnée réelle",
        suspected_domains=("cse", "cse_alert"),
        urgency=UrgencyLevel.PROMPT,
        desired_outcome="documenter et orienter prudemment sans qualification automatique",
        missing_information=("dates certaines", "population exacte", "preuves et règles applicables"),
    )


def cse_alerts_scenarios() -> dict[str, SyndicalCaseInput]:
    return {
        "similar_counter_claims": _case("Plusieurs salariés signalent au CSE la même anomalie de compteur.", "Articulation R1C et R2C requise."),
        "collective_union_discrimination": _case("Plusieurs représentants signalent une évolution de carrière défavorable et une discrimination syndicale potentielle au CSE.", "Articulation R1D et R2C requise."),
        "individual_rights": _case("Un élu signale au CSE une atteinte possible aux droits d'une personne.", "Aucune atteinte n'est établie."),
        "potential_economic_alert": _case("Le CSE apprend une baisse d'activité et des suppressions de postes sans informations détaillées ; une alerte économique est évoquée.", "Les données restent absentes."),
        "temporary_work_increase": _case("Les élus CSE signalent une hausse importante de l'intérim mais les données sont partielles.", "Une tendance sociale reste à confirmer."),
        "recurring_understaffing": _case("Plusieurs services signalent au CSE un sous-effectif récurrent, une charge excessive et des heures supplémentaires.", "Les chiffres restent à obtenir."),
        "potential_economic_expertise": _case("Le CSE s'interroge sur une expertise économique potentielle.", "Objet, fondement et financement restent à confirmer."),
        "important_project": _case("Une réorganisation et un projet important sont annoncés au CSE ; une expertise potentielle est évoquée.", "R2A reste principal et le fond CSSCT est exclu."),
        "disputed_expertise": _case("La direction conteste au CSE le principe et le financement d'une expertise.", "Aucun financement n'est tenu pour acquis."),
        "documents_refused": _case("La direction refuse de façon persistante des documents demandés par le CSE en invoquant la confidentialité.", "Le motif et les alternatives doivent être examinés."),
        "unmet_commitment": _case("Un ancien PV CSE metadata-only mentionne un engagement non tenu.", "Le document source doit être vérifié."),
        "investigation_request": _case("Le CSE demande une enquête sur des faits répétés concernant plusieurs salariés.", "Le cadre et les précautions restent à définir."),
        "labour_inspectorate": _case("Les démarches internes du CSE sont restées sans réponse et les élus envisagent l'inspection du travail.", "La compétence et les pièces doivent être vérifiées."),
        "defender_of_rights": _case("Une discrimination potentielle concerne plusieurs salariés et le CSE envisage le Défenseur des droits.", "La recevabilité reste à confirmer."),
        "isolated_individual": _case("Un salarié présente au CSE une réclamation individuelle isolée sans indice collectif.", "Le domaine R1 reste principal."),
        "corrected_situation": _case("La direction reconnaît l'erreur collective signalée au CSE et met en place une mesure corrective.", "Une escalade inutile doit être évitée."),
        "insufficient_alert": _case("Les élus CSE expriment une inquiétude et parlent d'alerte sans fait ni donnée précise.", "L'alerte n'est pas établie."),
        "extraordinary_meeting": _case("Les élus CSE envisagent une réunion extraordinaire sur une situation urgente et répétée.", "Les conditions restent à vérifier."),
        "expertise_resolution": _case("Le CSE souhaite préparer une résolution prudente relative à une expertise potentielle.", "Une relecture juridique est requise."),
        "possible_obstruction": _case("Le CSE décrit des refus persistants et l'impossibilité d'exercer ses attributions ; un risque d'entrave est évoqué.", "Une revue juridique est indispensable."),
    }
