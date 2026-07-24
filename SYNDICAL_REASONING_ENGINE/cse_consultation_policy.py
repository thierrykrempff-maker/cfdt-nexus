"""Deterministic and prudent R2A policies."""

from __future__ import annotations

from .cse_consultation_models import (
    CSEProjectFacts,
    CollectiveDimension,
    ConsultationAssessment,
    DocumentPriority,
    DocumentRequest,
    DomainArticulation,
    MechanismAnalysis,
    ObstructionAssessment,
    ObstructionRisk,
    ParticipationMechanism,
)


COLLECTIVE_MARKERS = (
    "plusieurs salarie", "equipes", "collectif", "service", "reorganisation",
    "effectifs", "postes", "externalisation", "sous traitance", "activite",
    "nouvel outil", "logiciel", "cycle", "horaires", "organisation",
)


def collective_dimension(text: str, project: CSEProjectFacts) -> CollectiveDimension:
    if project.employees_affected == 1 and any(
        marker in text for marker in ("isole", "sans autre indice collectif")
    ):
        return CollectiveDimension.ISOLATED_INDIVIDUAL
    if project.employees_affected is not None and project.employees_affected > 1:
        return CollectiveDimension.IDENTIFIED_COLLECTIVE_PROJECT
    if project.cse_consultation_known is True:
        return CollectiveDimension.COLLECTIVE_PROJECT_NOT_DEMONSTRATED
    if any(marker in text for marker in ("plusieurs changements", "cas similaires", "repetition")):
        return CollectiveDimension.REPEATED_INDIVIDUAL_CASES
    if any(marker in text for marker in ("politique generale", "regle generale", "pratique generale")):
        return CollectiveDimension.GENERAL_PRACTICE
    if any(marker in text for marker in COLLECTIVE_MARKERS):
        return CollectiveDimension.COLLECTIVE_PROJECT_NOT_DEMONSTRATED
    return CollectiveDimension.ISOLATED_INDIVIDUAL


def mechanism(project: CSEProjectFacts, dimension: CollectiveDimension) -> MechanismAnalysis:
    if dimension is CollectiveDimension.ISOLATED_INDIVIDUAL:
        return MechanismAnalysis(
            ParticipationMechanism.MANAGEMENT_POWER,
            "employeur, avec contrôle individuel R1A",
            "avant toute modification individuelle lorsqu'un accord est requis",
            ("décision individuelle", "contrat et avenants"),
            ("portée exacte de la décision", "existence d'indices collectifs"),
        )
    if project.recurring_consultation:
        kind = ParticipationMechanism.RECURRING_CONSULTATION
    elif project.potentially_applicable_agreements:
        kind = ParticipationMechanism.COLLECTIVE_BARGAINING
    elif project.decision_envisaged is not False:
        kind = ParticipationMechanism.CONSULTATION
    else:
        kind = ParticipationMechanism.TO_BE_CONFIRMED
    actor = "CSE" if kind is not ParticipationMechanism.COLLECTIVE_BARGAINING else "organisations syndicales"
    return MechanismAnalysis(
        kind,
        actor,
        "avant la décision définitive et la mise en œuvre, sous réserve des textes applicables",
        ("présentation complète du projet", "calendrier", "impacts", "population concernée"),
        ("compétence exacte", "délai applicable", "qualité des informations", "accord applicable"),
    )


def consultation_status(project: CSEProjectFacts) -> ConsultationAssessment:
    if project.cse_consultation_known is True and project.opinion_rendered is True and project.implementation_started is not True:
        return ConsultationAssessment.APPARENTLY_REGULAR
    if project.implementation_started is True and project.opinion_rendered is not True:
        return ConsultationAssessment.POSSIBLE_EARLY_IMPLEMENTATION
    if project.cse_consultation_known is False:
        return ConsultationAssessment.APPARENT_ABSENCE
    if project.cse_information_known is True and not project.transmitted_documents:
        return ConsultationAssessment.POSSIBLY_INSUFFICIENT_INFORMATION
    if project.decision_already_taken is True and project.cse_consultation_known is not True:
        return ConsultationAssessment.POTENTIALLY_LATE
    if project.cse_consultation_known is None:
        return ConsultationAssessment.INSUFFICIENT_DATA
    return ConsultationAssessment.TO_DOCUMENT


def document_requests(project: CSEProjectFacts) -> tuple[DocumentRequest, ...]:
    definitions = (
        ("présentation complète du projet", DocumentPriority.ESSENTIAL, "qualifier le projet", "Quel est le projet exact ?", "ne prouve pas seule sa régularité", "direction", "permettre une analyse utile"),
        ("calendrier", DocumentPriority.ESSENTIAL, "reconstituer la chronologie", "Quand la décision et la mise en œuvre interviennent-elles ?", "peut évoluer", "direction", "vérifier le caractère préalable"),
        ("population et services concernés", DocumentPriority.ESSENTIAL, "mesurer la dimension collective", "Qui est concerné ?", "ne décrit pas tous les impacts", "direction / RH", "délimiter le périmètre"),
        ("impacts emploi, horaires, postes et rémunération", DocumentPriority.ESSENTIAL, "identifier les conséquences", "Quels éléments changent ?", "reste prospectif", "direction / RH", "éclairer l'avis"),
        ("organigramme avant et après", DocumentPriority.ESSENTIAL, "comparer l'organisation", "Quelles structures changent ?", "ne décrit pas le travail réel", "direction", "objectiver la réorganisation"),
        ("analyse de charge et plan de formation", DocumentPriority.USEFUL, "apprécier l'accompagnement", "Comment les changements sont-ils préparés ?", "doit être confronté aux faits", "direction", "évaluer les mesures prévues"),
        ("accords applicables", DocumentPriority.USEFUL, "identifier le cadre négocié", "Une règle conventionnelle s'applique-t-elle ?", "version et champ à vérifier", "direction / organisations syndicales", "articuler consultation et négociation"),
        ("anciens PV et engagements", DocumentPriority.COMPLEMENTARY, "retrouver l'historique", "Le sujet a-t-il déjà été traité ?", "le document source doit être consulté", "secrétariat du CSE", "vérifier les précédents"),
    )
    present = {item.lower() for item in project.transmitted_documents}
    return tuple(
        DocumentRequest(*item)
        for item in definitions
        if item[0].lower() not in present
    )


def obstruction_assessment(project: CSEProjectFacts, status: ConsultationAssessment) -> ObstructionAssessment:
    indicators = []
    if status in {ConsultationAssessment.APPARENT_ABSENCE, ConsultationAssessment.POSSIBLE_EARLY_IMPLEMENTATION, ConsultationAssessment.POTENTIALLY_LATE}:
        indicators.append(status.value)
    if project.cse_information_known is True and not project.transmitted_documents:
        indicators.append("information possiblement insuffisante")
    risk = ObstructionRisk.POSSIBLE_INDICATORS if indicators else ObstructionRisk.INSUFFICIENT_DATA
    return ObstructionAssessment(
        risk,
        tuple(indicators),
        ("chronologie certaine", "documents transmis", "décision formalisée", "réponses de la direction", "qualification non établie"),
        ("projet non finalisé", "simple ajustement opérationnel", "information déjà transmise par un autre canal"),
        ("demander les informations", "inscrire le sujet à l'ordre du jour", "formaliser les questions"),
        "CSE, inspection du travail ou conseil juridique selon les faits",
        True,
    )


def articulate(dimension: CollectiveDimension, text: str) -> DomainArticulation:
    complements = []
    if any(marker in text for marker in ("poste", "mutation", "transfert")):
        complements.append("R1A_CONTRACT_CHANGE")
    if any(marker in text for marker in ("sanction", "refus")):
        complements.append("R1B_DISCIPLINARY")
    if any(marker in text for marker in ("horaire", "cycle", "equipe", "remuneration", "paie")):
        complements.append("R1C_WORKING_TIME")
    if any(marker in text for marker in ("discrimination", "harcelement")):
        complements.append("R1D_DISCRIMINATION_HARASSMENT")
    if any(marker in text for marker in ("arret", "maladie", "inaptitude", "reclassement")):
        complements.append("R1E_HEALTH_ABSENCE")
    if dimension is CollectiveDimension.ISOLATED_INDIVIDUAL:
        primary = "R1A_CONTRACT_CHANGE"
        complements = ["R2A_CSE_CONSULTATION", *complements]
    else:
        primary = "R2A_CSE_CONSULTATION"
    return DomainArticulation(
        primary,
        tuple(dict.fromkeys(complements)),
        "La primauté dépend d'indices collectifs objectivables ; aucun cas individuel n'est automatiquement transformé en projet collectif.",
        "Les compétences du CSE, des organisations syndicales et d'une future CSSCT restent distinctes.",
    )
