"""Deterministic and cautious policies for R2C."""

from __future__ import annotations

from .cse_alerts_models import (
    AlertContradictoryAnalysis,
    AlertDocumentRequest,
    AlertDomainArticulation,
    AlertHypothesis,
    AlertMechanism,
    AlertQuestion,
    AlertResolutionDraft,
    AlertStrategy,
    ClaimScope,
    CompetentActor,
    DocumentPriority,
    EscalationKind,
    EscalationOption,
    ExpertiseHypothesis,
    ExpertiseKind,
    InvestigationKind,
    InvestigationProposal,
    QuestionPriority,
)
from .models import ConfidenceLevel, UrgencyLevel


def alert_hypotheses(text: str, confidence: ConfidenceLevel) -> tuple[AlertHypothesis, ...]:
    mechanisms: list[AlertMechanism] = []
    if any(word in text for word in ("discrimination", "harcelement", "liberte", "dignite", "vie privee", "surveillance", "represaille")):
        mechanisms.append(AlertMechanism.RIGHTS_OF_PERSONS)
    if any(word in text for word in ("baisse d activite", "perte de marche", "suppression de poste", "externalisation", "restructuration", "fermeture", "indicateur economique")):
        mechanisms.append(AlertMechanism.ECONOMIC)
    if any(word in text for word in ("interim", "sous effectif", "absenteisme", "turnover", "heures supplementaires", "surcharge", "contrats precaires")):
        mechanisms.append(AlertMechanism.SOCIAL)
    if any(word in text for word in ("refus persistant", "sans reponse", "entrave", "informations refusees")) or ("refus" in text and "persist" in text):
        mechanisms.append(AlertMechanism.DEGRADED_CSE_FUNCTIONING)
    if any(word in text for word in ("risque collectif", "sante mentale", "charge excessive")):
        mechanisms.append(AlertMechanism.COLLECTIVE_RISK)
    if not mechanisms:
        mechanisms.append(AlertMechanism.INVESTIGATION_FIRST)

    rows = []
    for mechanism in dict.fromkeys(mechanisms):
        actor = {
            AlertMechanism.RIGHTS_OF_PERSONS: "CSE, avec appui juridique à confirmer",
            AlertMechanism.ECONOMIC: "CSE",
            AlertMechanism.SOCIAL: "CSE",
            AlertMechanism.DEGRADED_CSE_FUNCTIONING: "CSE et conseil juridique",
            AlertMechanism.COLLECTIVE_RISK: "CSE, sans préjuger du futur domaine CSSCT",
        }.get(mechanism, "CSE ou délégué syndical selon le sujet")
        rows.append(
            AlertHypothesis(
                mechanism,
                "droit d'alerte potentiellement mobilisable ; mécanisme à confirmer"
                if mechanism not in {AlertMechanism.INVESTIGATION_FIRST, AlertMechanism.SIMPLE_CLAIM}
                else "faits nécessitant une investigation avant toute qualification",
                ("faits déclarés", "répétition ou dimension collective à vérifier"),
                ("faits précis", "population", "chronologie", "réponse employeur", "preuves"),
                actor,
                ("chronologie", "données pertinentes", "réponses écrites", "historique CSE"),
                ("documenter", "demander les informations", "faire relire juridiquement"),
                ("alerte non établie à ce stade", "aucune automaticité", "conditions à vérifier"),
                confidence,
                True,
            )
        )
    return tuple(rows)


def expertise_hypotheses(text: str, confidence: ConfidenceLevel) -> tuple[ExpertiseHypothesis, ...]:
    kinds: list[ExpertiseKind] = []
    if "expertise" in text or "expert" in text:
        if any(word in text for word in ("economique", "comptable", "baisse d activite")):
            kinds.append(ExpertiseKind.ECONOMIC_ACCOUNTING)
        if any(word in text for word in ("restructuration", "reorganisation", "concentration")):
            kinds.append(ExpertiseKind.RESTRUCTURING)
        if "projet important" in text:
            kinds.append(ExpertiseKind.IMPORTANT_PROJECT)
        if "risque grave" in text:
            kinds.append(ExpertiseKind.POTENTIAL_SERIOUS_RISK)
        if not kinds:
            kinds.append(ExpertiseKind.EXTERNAL_LEGAL_TECHNICAL_SUPPORT)
    return tuple(
        ExpertiseHypothesis(
            kind,
            "éclairer le CSE sur l'objet précisément délimité",
            "fondement potentiel à confirmer par un conseil juridique",
            ("question collective déclarée",),
            ("qualification, délai et conditions non vérifiés",),
            ("délibération", "documents du sujet", "calendrier", "règles applicables"),
            "délai potentiel à vérifier",
            "financement à vérifier ; aucune prise en charge certaine",
            "CSE selon conditions et vote à vérifier",
            ("contestation", "coût", "irrecevabilité ou délai"),
            True,
            confidence,
        )
        for kind in dict.fromkeys(kinds)
    )


def investigations(text: str) -> tuple[InvestigationProposal, ...]:
    if not any(word in text for word in ("enquete", "investigation", "faits repetes", "signalement", "plusieurs salaries")):
        return ()
    kind = InvestigationKind.JOINT if "conjointe" in text else InvestigationKind.CSE
    return (
        InvestigationProposal(
            kind,
            "établir les faits sans préjuger de leur qualification",
            ("élus mandatés à confirmer", "employeur si enquête conjointe"),
            "périmètre factuel et temporel à définir",
            ("chronologie", "pièces licitement accessibles"),
            ("personnes volontaires dans un cadre protecteur",),
            ("ne pas recueillir illégalement de preuve", "protéger les personnes", "tracer la méthode"),
            "accès strictement limité",
            "écoute contradictoire et absence de conclusion préétablie",
            "compte rendu synthétique et sécurisé",
            "point CSE et mesures à confirmer",
            ("ne remplace ni une enquête judiciaire ni un avis médical",),
        ),
    )


def competent_actors() -> tuple[CompetentActor, ...]:
    return (
        CompetentActor("CSE", "réclamations collectives et attributions légales à vérifier", ("question", "résolution", "demande d'information", "alerte potentielle"), ("ne tranche pas un litige individuel",)),
        CompetentActor("délégué syndical", "revendication et négociation collectives", ("négocier", "accompagner", "formaliser une revendication"), ("ne se substitue pas au CSE",)),
        CompetentActor("inspection du travail", "contrôle dans son champ légal", ("informer", "saisir avec faits documentés"), ("ne garantit pas une suite déterminée",), True),
        CompetentActor("Défenseur des droits", "discrimination et droits dans son champ", ("orienter", "saisir selon conditions"), ("compétence et recevabilité à vérifier",), True),
        CompetentActor("conseil juridique", "sécurisation de la qualification et de la procédure", ("relire", "orienter", "préparer un recours"), ("ne remplace pas la décision de l'instance",), True),
        CompetentActor("expert", "éclairage technique ou économique dans un cadre à confirmer", ("analyser", "présenter"), ("désignation et financement à vérifier",), True),
        CompetentActor("juge ou autorité compétente", "trancher dans son champ", ("être saisi selon procédure"), ("recours non automatique",), True),
    )


def document_requests() -> tuple[AlertDocumentRequest, ...]:
    rows = (
        ("description précise, population et chronologie", "délimiter les faits", DocumentPriority.ESSENTIAL, "élus / salariés / direction"),
        ("réponses de la direction", "vérifier les suites", DocumentPriority.ESSENTIAL, "direction"),
        ("documents du projet et décisions", "comprendre l'objet et le calendrier", DocumentPriority.ESSENTIAL, "direction"),
        ("données sociales ou économiques nécessaires", "mesurer les indices déclarés", DocumentPriority.ESSENTIAL, "direction"),
        ("accords applicables", "identifier la règle commune", DocumentPriority.ESSENTIAL, "parties compétentes"),
        ("anciens PV et engagements", "vérifier la récurrence", DocumentPriority.USEFUL, "CSE Memory metadata-only"),
        ("indicateurs, organigrammes, plannings et effectifs", "objectiver les tendances", DocumentPriority.USEFUL, "direction"),
        ("données d'intérim et de sous-traitance", "documenter la dimension sociale", DocumentPriority.USEFUL, "direction"),
        ("témoignages et statistiques anonymisées", "corroborer sans exposer les personnes", DocumentPriority.COMPLEMENTARY, "personnes autorisées"),
        ("jurisprudence et doctrine officielle", "sécuriser l'orientation", DocumentPriority.COMPLEMENTARY, "sources publiques"),
    )
    return tuple(
        AlertDocumentRequest(name, utility, priority, holder, "confidentialité et accès à vérifier", "ne prouve rien seul", "formaliser le refus et demander une réponse motivée")
        for name, utility, priority, holder in rows
    )


def questions(known: str) -> tuple[AlertQuestion, ...]:
    rows = (
        (QuestionPriority.CRITICAL, "Combien de salariés sont concernés ?", "mesurer la portée", ("population",)),
        (QuestionPriority.CRITICAL, "Quels faits précis et quelles preuves existent ?", "séparer déclaration et faits vérifiés", ("chronologie", "preuves")),
        (QuestionPriority.CRITICAL, "Existe-t-il un risque immédiat déclaré nécessitant une protection prudente ?", "évaluer l'urgence sans la conclure", ("signalement",)),
        (QuestionPriority.PRIORITY, "Le problème est-il ponctuel ou récurrent et possède-t-il une source commune ?", "distinguer individuel et collectif", ("historique",)),
        (QuestionPriority.PRIORITY, "La direction a-t-elle été informée et quelle réponse documentée a-t-elle apportée ?", "vérifier les suites", ("réponse employeur",)),
        (QuestionPriority.PRIORITY, "Le CSE a-t-il adopté une résolution ou évoqué une expertise ?", "retrouver la procédure", ("PV", "résolution")),
        (QuestionPriority.USEFUL, "Existe-t-il une dimension économique, sociale, de droits des personnes ou de négociation ?", "orienter sans qualification automatique", ("indicateurs",)),
        (QuestionPriority.USEFUL, "Quel acteur paraît compétent et un avis juridique a-t-il été sollicité ?", "sécuriser l'escalade", ("avis juridique",)),
        (QuestionPriority.COMPLEMENTARY, "Une réunion extraordinaire ou une saisine extérieure a-t-elle déjà été demandée ?", "éviter les doublons", ("demandes antérieures",)),
    )
    return tuple(AlertQuestion(priority, wording, purpose, docs) for priority, wording, purpose, docs in rows if wording.lower() not in known)


def resolutions(text: str) -> tuple[AlertResolutionDraft, ...]:
    resolution_type = (
        "expertise potentielle" if "expert" in text
        else "enquête" if "enquete" in text
        else "demande de documents" if "document" in text
        else "alerte potentielle" if "alerte" in text
        else "demande de suivi"
    )
    return (
        AlertResolutionDraft(
            resolution_type,
            ("faits déclarés à dater et confirmer",),
            ("qualification", "population", "conditions légales"),
            "obtenir une réponse et organiser un suivi",
            ("chronologie", "documents pertinents", "réponse écrite"),
            "projet de décision à relire et adapter avant tout vote",
            "CSE et acteur compétent à confirmer",
            "échéance à fixer après vérification",
            "inscription au PV et revue à l'échéance",
            ("aucun droit, délai, financement ou entrave n'est tenu pour acquis",),
        ),
    )


def escalation_options(urgency: UrgencyLevel) -> tuple[EscalationOption, ...]:
    rows = (
        (EscalationKind.INTERNAL_REMINDER, "interne", "obtenir une réponse traçable", "relance antérieure ou question précise", "demande et chronologie", "rapide", "peut rester sans suite", "retard", "réponse", "résolution"),
        (EscalationKind.CSE_RESOLUTION, "CSE", "formaliser la position", "inscription et règles de vote à vérifier", "projet de résolution", "trace collective", "validité à vérifier", "contestation", "décision tracée", "avis juridique"),
        (EscalationKind.EXTRAORDINARY_MEETING, "CSE selon conditions", "traiter une situation pressante", "conditions de demande à vérifier", "faits et urgence", "réactivité", "aucune automaticité", "refus ou report", "réunion potentielle", "conseil"),
        (EscalationKind.LABOUR_INSPECTORATE, "champ légal de l'inspection", "signaler des faits documentés", "démarches internes et faits selon situation", "chronologie", "regard extérieur", "suite non garantie", "mauvaise qualification", "orientation", "conseil juridique"),
        (EscalationKind.DEFENDER_OF_RIGHTS, "discrimination ou droits dans son champ", "obtenir une orientation externe", "faits et compétence à vérifier", "faits anonymisés et preuves licites", "spécialisation", "recevabilité à vérifier", "délai", "orientation", "conseil"),
        (EscalationKind.LEGAL_COUNSEL, "sécurisation juridique", "confirmer mécanisme et procédure", "dossier factuel", "chronologie et pièces", "réduit le risque juridique", "coût", "retard", "avis", "recours adapté"),
        (EscalationKind.COURT, "juridiction compétente à vérifier", "faire trancher un litige", "intérêt, recevabilité et procédure", "dossier complet", "décision contraignante potentielle", "coût et durée", "irrecevabilité", "décision", "suivi contentieux"),
    )
    return tuple(
        EscalationOption(kind, competence, objective, (prerequisite,), (pieces,), urgency, (advantage,), (limitation,), (risk,), result, alternative)
        for kind, competence, objective, prerequisite, pieces, advantage, limitation, risk, result, alternative in rows
    )


def contradictory_positions() -> tuple[AlertContradictoryAnalysis, AlertContradictoryAnalysis]:
    cse = AlertContradictoryAnalysis(
        ("dimension collective ou répétée à vérifier", "information ou réponse possiblement insuffisante"),
        ("chronologie et récurrence peuvent être documentées",),
        ("qualification et mécanisme restent incertains",),
        ("difficulté ponctuelle", "mesure corrective engagée", "absence de caractère collectif"),
        ("produire les données, cibler la demande, reconnaître la correction"),
        ("chronologie", "population", "réponses", "indicateurs"),
        ("droit d'alerte, expertise, financement, urgence et entrave"),
        ("calendrier de remise", "enquête conjointe", "suivi formalisé"),
    )
    employer = AlertContradictoryAnalysis(
        ("réponse déjà apportée possible", "projet non finalisé", "confidentialité invoquée possible"),
        ("documents datés et correction peuvent être produits",),
        ("une absence de donnée ou de réponse fragilise la position",),
        ("difficulté récurrente", "effet collectif", "information insuffisante"),
        ("motiver, transmettre de façon encadrée, proposer un calendrier"),
        ("réponses écrites", "données agrégées", "mesures correctives"),
        ("caractère suffisant des réponses et mécanisme applicable"),
        ("accès encadré", "complément ciblé", "point de suivi"),
    )
    return cse, employer


def strategies(urgency: UrgencyLevel) -> tuple[AlertStrategy, ...]:
    rows = (
        (1, "Documentation", "clarifier faits, portée et historique", "élus / syndicat", "dossier fiable", "ne règle pas le fond", "données lacunaires", "chronologie", "faits structurés", "action interne"),
        (2, "Action interne", "demander réponse, documents et suivi", "CSE", "trace la demande", "réponse partielle possible", "retard", "demande écrite", "réponse traçable", "investigation"),
        (3, "Investigation", "analyser et faire confirmer le mécanisme", "CSE / conseil", "éclaire la décision", "aucune qualification automatique", "coût et délai", "preuves licites", "hypothèses mieux étayées", "alerte ou expertise"),
        (4, "Alerte ou expertise potentielle", "formaliser sous réserve des conditions", "CSE", "mobilise le mécanisme adapté", "avis juridique requis", "contestation", "résolution et pièces", "démarche sécurisée", "recours"),
        (5, "Recours", "solliciter l'acteur extérieur compétent", "CSE / syndicat / personne recevable", "permet un examen externe", "procédure à vérifier", "irrecevabilité, coût, tension", "dossier complet", "orientation ou décision", "suivi"),
    )
    return tuple(AlertStrategy(level, name, objective, actor, urgency, (adv,), (limit,), (risk,), (pieces,), result, nxt) for level, name, objective, actor, adv, limit, risk, pieces, result, nxt in rows)


def articulate(text: str, scope: ClaimScope) -> AlertDomainArticulation:
    primary = "R2C_CSE_ALERTS_EXPERTISE"
    complements: list[str] = []
    if any(word in text for word in ("reorganisation", "projet important", "consultation")):
        primary = "R2A_CSE_CONSULTATION"
        complements.extend(("R2B_CSE_OPERATION", "R2C_CSE_ALERTS_EXPERTISE"))
    elif scope in {ClaimScope.INDIVIDUAL_REQUEST, ClaimScope.INDIVIDUAL_CLAIM, ClaimScope.INDIVIDUAL_LITIGATION}:
        if any(word in text for word in ("discrimination", "harcelement", "liberte", "dignite")):
            primary = "R1D_DISCRIMINATION_HARASSMENT"
        elif any(word in text for word in ("sanction", "disciplinaire")):
            primary = "R1B_DISCIPLINARY"
        elif any(word in text for word in ("maladie", "inaptitude", "absence")):
            primary = "R1E_HEALTH_ABSENCE"
        else:
            primary = "R1A_CONTRACT_CHANGE"
    elif any(word in text for word in ("horaire", "compteur", "heures supplementaires", "remuneration", "classification")):
        complements.append("R1C_WORKING_TIME")
    if any(word in text for word in ("discrimination", "harcelement", "liberte syndicale")):
        complements.append("R1D_DISCRIMINATION_HARASSMENT")
    if any(word in text for word in ("maladie", "inaptitude", "sante mentale")):
        complements.append("R1E_HEALTH_ABSENCE")
    if any(word in text for word in ("document", "ordre du jour", "reunion extraordinaire", "resolution")):
        complements.append("R2B_CSE_OPERATION")
    return AlertDomainArticulation(
        primary,
        tuple(dict.fromkeys(item for item in complements if item != primary)),
        "R2C structure réclamations, alertes, expertises et escalade ; R2A, R2B et R1A à R1E conservent leurs responsabilités.",
        "Aucune alerte, expertise, urgence, entrave, recevabilité, échéance ou voie de recours n'est automatiquement acquise.",
    )
