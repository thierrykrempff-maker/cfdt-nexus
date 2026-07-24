"""Central deterministic policies for R2B CSE operation."""

from __future__ import annotations

from .cse_operation_models import (
    ActorRole,
    CSEDocument,
    CSEMeetingFacts,
    CSEOperationStrategy,
    Commitment,
    CommitmentStatus,
    DeadlineAssessment,
    DocumentPriority,
    DocumentRequest,
    DocumentStatus,
    DomainArticulation,
    OpinionDraft,
    OpinionType,
    OperationAssessment,
    Reservation,
    ResolutionDraft,
)
from .models import ConfidenceLevel, UrgencyLevel


def actor_roles() -> tuple[ActorRole, ...]:
    return (
        ActorRole("président du CSE", ("convoquer", "participer à l'établissement de l'ordre du jour"), ("proposer un point",), ("organiser la réunion",), False, ("secrétaire",), ("questions et résolutions",), ("réponse et suivi",)),
        ActorRole("secrétaire du CSE", ("préparer l'ordre du jour", "préparer le procès-verbal"), ("inscrire et formuler un point",), (), False, ("président", "élus"), ("documents de séance",), ("engagements",)),
        ActorRole("élus titulaires", ("préparer les questions", "délibérer"), ("question", "réserve", "résolution"), (), True, ("experts",), ("convocation et documents",), ("réponses",)),
        ActorRole("élus suppléants", ("contribuer selon leur situation",), ("question",), (), False, ("titulaires",), ("informations applicables",), ("suivi",)),
        ActorRole("représentant syndical", ("porter la position syndicale auprès du CSE",), ("question",), (), False, ("organisation syndicale",), ("informations applicables",), ("engagements",)),
        ActorRole("délégué syndical", ("négocier dans le champ syndical",), ("négociation",), ("signer un accord selon mandat",), False, ("CSE",), ("informations utiles à la négociation",), ("direction",)),
        ActorRole("direction / RH", ("présenter et répondre",), ("calendrier",), ("décisions relevant de l'employeur",), False, ("CSE",), ("questions et avis",), ("engagements déclarés",)),
        ActorRole("commission ou représentant de proximité", ("préparer un éclairage dans son champ",), ("question",), (), False, ("CSE",), ("mandat et informations",), ("recommandations",)),
        ActorRole("expert ou service juridique", ("apporter un avis dans son champ",), (), (), False, ("CSE",), ("documents nécessaires",), ()),
        ActorRole("inspection du travail", ("informer ou intervenir dans son champ légal",), (), (), False, ("CSE ou organisation syndicale",), ("faits documentés",), ()),
        ActorRole("salarié demandeur", ("signaler des faits",), ("question ou pièce",), (), False, ("élu ou syndicat",), ("suivi non confidentiel",), ()),
    )


def document_requests(documents: tuple[CSEDocument, ...]) -> tuple[DocumentRequest, ...]:
    received = {item.document_type.lower() for item in documents if item.status is DocumentStatus.RECEIVED}
    rows = (
        ("document de projet", "comprendre l'objet", "Quel est le projet ?", DocumentPriority.ESSENTIAL, "direction", "avant la réunion", "confidentialité à examiner sans renoncer à la demande", "ne prouve pas seul les impacts", "formaliser la pièce manquante"),
        ("calendrier", "reconstituer les étapes", "Quelles sont les échéances ?", DocumentPriority.ESSENTIAL, "direction", "avant la réunion", "aucune donnée personnelle attendue", "peut évoluer", "demander une date de remise"),
        ("données d'impact", "préparer les questions et l'avis", "Quels effets sont anticipés ?", DocumentPriority.ESSENTIAL, "direction / RH", "avant l'avis", "agrégées lorsque possible", "prospectives", "demander un complément ou un report"),
        ("organigramme et effectifs", "comparer avant et après", "Quel périmètre est concerné ?", DocumentPriority.ESSENTIAL, "direction / RH", "avant l'avis", "données agrégées", "ne décrit pas le travail réel", "demander une version anonymisée"),
        ("horaires, postes et critères", "identifier les changements", "Quelles règles changent ?", DocumentPriority.ESSENTIAL, "direction / RH", "avant l'avis", "sans données individuelles inutiles", "à confronter aux accords", "formuler des questions ciblées"),
        ("analyse de charge et plan de formation", "évaluer l'accompagnement", "Les moyens sont-ils adaptés ?", DocumentPriority.USEFUL, "direction", "pour la réunion", "agrégée", "hypothèses à vérifier", "inscrire le suivi"),
        ("accords, bilans et indicateurs", "identifier les cadres et précédents", "Quel cadre est applicable ?", DocumentPriority.USEFUL, "direction / organisations syndicales", "pour l'analyse", "version à vérifier", "champ à confirmer", "demander la référence exacte"),
        ("anciens PV et engagements", "retrouver l'historique", "Le sujet a-t-il déjà été traité ?", DocumentPriority.COMPLEMENTARY, "secrétariat du CSE", None, "document source à vérifier", "la métadonnée ne prouve pas l'engagement", "consulter la source"),
    )
    return tuple(DocumentRequest(*row) for row in rows if row[0].lower() not in received)


def deadline_assessments(meeting: CSEMeetingFacts, urgency: UrgencyLevel) -> tuple[DeadlineAssessment, ...]:
    rows = (
        ("convocation", meeting.convocation_date, "réception de la convocation", "délai à confirmer", "règlement, accord et Code du travail applicables", meeting.scheduled_date, "type de réunion et point de départ à vérifier", None, "vérifier immédiatement le régime applicable"),
        ("transmission documentaire", None, "mise à disposition effective", "temps utile à confirmer", "procédure de consultation applicable", meeting.scheduled_date, "complétude et accessibilité à vérifier", None, "tracer la réception et demander les compléments"),
        ("avis", meeting.scheduled_date, "début de la procédure à confirmer", "délai potentiel à vérifier", "source juridique et accord applicables", None, "calcul dépendant de la procédure applicable, à vérifier", None, "identifier le point de départ et la source"),
        ("procès-verbal et engagement", None, "réunion ou engagement source", "échéance potentielle", "règlement et engagement documenté", None, "date et statut à confirmer", None, "programmer le suivi"),
    )
    return tuple(DeadlineAssessment(label, start, trigger, duration, source, theoretical, uncertainty, days, urgency, action, False) for label, start, trigger, duration, source, theoretical, uncertainty, days, action in rows)


def operation_assessment(meeting: CSEMeetingFacts, text: str) -> OperationAssessment:
    if meeting.opinion_rendered and not meeting.anomalies:
        return OperationAssessment.APPARENTLY_REGULAR
    recurrent = any(marker in text for marker in ("plusieurs reunions", "recurrent", "systematiquement", "persistante"))
    obstruction = recurrent and any(marker in text for marker in ("refus", "sans reponse", "non tenu", "retire"))
    if obstruction:
        return OperationAssessment.POSSIBLE_OBSTRUCTION_RISK
    if recurrent:
        return OperationAssessment.POSSIBLE_RECURRING_DYSFUNCTION
    if meeting.anomalies:
        return OperationAssessment.ISOLATED_DIFFICULTY
    return OperationAssessment.INSUFFICIENT_DATA


def opinion_drafts(meeting: CSEMeetingFacts) -> tuple[OpinionDraft, ...]:
    received = tuple(item.title for item in meeting.documents if item.status is DocumentStatus.RECEIVED)
    missing = tuple(item.document_type for item in meeting.documents if item.status is not DocumentStatus.RECEIVED)
    if missing:
        types = (OpinionType.UNABLE_TO_OPINE, OpinionType.REQUEST_DEFERRAL, OpinionType.FAVORABLE_WITH_RESERVATIONS)
    else:
        types = (OpinionType.FAVORABLE_WITH_RESERVATIONS, OpinionType.FAVORABLE, OpinionType.UNFAVORABLE)
    return tuple(
        OpinionDraft(
            kind,
            meeting.agenda_items[0].title if meeting.agenda_items else "objet à confirmer",
            received,
            missing or ("informations restant à débattre",),
            ("éléments documentés à recenser",),
            tuple(meeting.reservations) or ("risques et réserves à débattre",),
            ("réponses écrites", "calendrier de suivi"),
            ("indicateurs", "point de suivi au prochain ordre du jour"),
            "trame proposée aux élus, sans décision à leur place",
            ("position", "réserves", "suivi"),
            "nouvelle présentation à envisager si les informations restent insuffisantes",
            ("validité, majorité et procédure à confirmer",),
        )
        for kind in types
    )


def reservations(meeting: CSEMeetingFacts) -> tuple[Reservation, ...]:
    missing = tuple(item.document_type for item in meeting.documents if item.status is not DocumentStatus.RECEIVED)
    if not missing:
        missing = ("informations restant à confirmer",)
    return tuple(
        Reservation(
            "information préparatoire",
            "élément déclaré dans le dossier",
            item,
            "analyse ou suivi incomplet",
            f"transmettre ou expliquer l'absence de {item}",
            meeting.scheduled_date,
            "réponse écrite et version du document",
        )
        for item in missing[:3]
    )


def resolution(meeting: CSEMeetingFacts) -> tuple[ResolutionDraft, ...]:
    return (
        ResolutionDraft(
            ("demande et pièces disponibles à vérifier",),
            "proposer au vote une demande documentée et un suivi",
            "secrétaire ou mandaté à confirmer",
            meeting.scheduled_date,
            None,
            "inscription au PV et point de suivi",
            True,
        ),
    )


def strategies(urgency: UrgencyLevel) -> tuple[CSEOperationStrategy, ...]:
    rows = (
        (1, "Préparation", "clarifier le point, les pièces et les questions", "élus / secrétaire", "réunion structurée", "ne règle pas le fond", "lacune documentaire", ("historique", "projet"), "dossier préparatoire", "demande formelle"),
        (2, "Demande formelle", "demander inscription, documents, réponse et calendrier", "secrétaire / CSE", "trace la demande", "réponse possiblement partielle", "retard", ("demande écrite",), "réponse traçable", "action en réunion"),
        (3, "Action en réunion", "questionner, réserver, résoudre ou demander un report", "élus titulaires", "porte le débat", "vote et compétence à confirmer", "blocage", ("ordre du jour", "documents"), "position formalisée", "suivi"),
        (4, "Suivi", "contrôler le PV et les engagements", "secrétaire / élus", "préserve la continuité", "dépend des preuves", "oubli", ("PV", "engagements"), "actions relancées", "appui extérieur"),
        (5, "Recours ou appui", "solliciter conseil ou inspection dans le champ pertinent", "CSE / syndicat", "sécurise l'analyse", "aucune automaticité", "coût et tension", ("chronologie", "demandes"), "orientation qualifiée", "suivi adapté"),
    )
    return tuple(CSEOperationStrategy(level, name, objective, actor, urgency, (adv,), (limit,), (risk,), pieces, result, nxt) for level, name, objective, actor, adv, limit, risk, pieces, result, nxt in rows)


def articulate(text: str) -> DomainArticulation:
    complements = []
    primary = "R2B_CSE_OPERATION"
    if any(marker in text for marker in ("reorganisation", "consultation", "projet collectif", "avis sur le projet")):
        primary = "R2A_CSE_CONSULTATION"
        complements.append("R2B_CSE_OPERATION")
    if any(marker in text for marker in ("poste individuel", "un salarie", "mutation")):
        complements.append("R1A_CONTRACT_CHANGE")
    if any(marker in text for marker in ("sanction", "disciplinaire")):
        complements.append("R1B_DISCIPLINARY")
    if any(marker in text for marker in ("horaire", "cycle", "paie", "remuneration")):
        complements.append("R1C_WORKING_TIME")
    if any(marker in text for marker in ("discrimination", "harcelement", "liberte syndicale")):
        complements.append("R1D_DISCRIMINATION_HARASSMENT")
    if any(marker in text for marker in ("absence", "maladie", "inaptitude")):
        complements.append("R1E_HEALTH_ABSENCE")
    return DomainArticulation(
        primary,
        tuple(dict.fromkeys(complements)),
        "R2B traite le fonctionnement ; R2A qualifie le projet et R1A à R1E conservent leurs responsabilités.",
        "Aucune compétence, validité, majorité, échéance ou entrave n'est déduite automatiquement.",
    )
