"""Prudent, deterministic R2A analysis of CSE information and consultation."""

from __future__ import annotations

import unicodedata

from .cse_consultation_models import (
    CSEConsultationAnalysis,
    CSEMemoryLookup,
    CSEMemoryMetadata,
    CSEProjectFacts,
    CSEQualification,
    CSEQuestion,
    CSEStrategy,
    CollectiveDimension,
    ConfidenceLevel,
    ContradictoryPosition,
    EventNature,
    ProjectTimelineEvent,
    ProjectType,
    QuestionPriority,
    UrgencyLevel,
)
from .cse_consultation_policy import (
    articulate,
    collective_dimension,
    consultation_status,
    document_requests,
    mechanism,
    obstruction_assessment,
)
from .engine import SyndicalReasoningEngine
from .models import SyndicalCaseInput


PROJECT_MARKERS = {
    ProjectType.REORGANIZATION: ("reorganisation", "organisation de service", "restructure"),
    ProjectType.JOB_CHANGES: ("suppression de poste", "creation de poste", "transfert de salarie"),
    ProjectType.WORKING_TIME: ("changement d horaires", "change de cycle", "equipe postee", "travail poste"),
    ProjectType.OUTSOURCING: ("externalisation", "sous traitance", "prestataire", "transfert d activite"),
    ProjectType.RELOCATION: ("demenagement", "implantation"),
    ProjectType.MONITORING_TOOL: ("outil de controle", "logiciel de suivi", "surveillance"),
    ProjectType.WORK_METHOD: ("procedure de travail", "methodes de travail", "qualification", "classification"),
    ProjectType.STAFFING: ("effectifs", "interim", "fermeture"),
    ProjectType.ECONOMIC_PROJECT: ("projet economique", "emploi et competences"),
}

R2A_DOMAINS = {"cse_consultation", "reorganisation", "collective_project", "dialogue_social"}


def needs_cse_consultation_reasoning(case_or_question: SyndicalCaseInput | str) -> bool:
    if isinstance(case_or_question, SyndicalCaseInput):
        if set(case_or_question.suspected_domains).intersection(R2A_DOMAINS):
            return True
        text = _case_text(case_or_question)
    else:
        text = _normalize(case_or_question)
    collective = any(
        marker in text
        for marker in (
            "cse", "consultation", "reorganisation", "plusieurs salarie",
            "plusieurs postes", "plusieurs equipes", "externalisation",
            "nouvel outil", "logiciel de suivi", "ordre du jour", "plusieurs equipes",
        )
    )
    return collective and any(
        marker in text
        for marker in ("projet", "decision", "mise en oeuvre", "information", "avis", "poste", "horaire", "cycle", "outil", "service")
    )


class NullCSEMemoryLookup:
    def search_metadata(self, query: str) -> tuple[CSEMemoryMetadata, ...]:
        return ()


class CSEConsultationReasoningEngine:
    def __init__(
        self,
        base_engine: SyndicalReasoningEngine | None = None,
        *,
        memory_lookup: CSEMemoryLookup | None = None,
    ) -> None:
        self._base_engine = base_engine or SyndicalReasoningEngine()
        self._memory_lookup = memory_lookup or NullCSEMemoryLookup()

    def analyze(
        self, case: SyndicalCaseInput, *, scenario_code: str | None = None
    ) -> CSEConsultationAnalysis:
        if not isinstance(case, SyndicalCaseInput):
            raise TypeError("case must be a SyndicalCaseInput")
        text = _case_text(case)
        project = _project_facts(case, text)
        dimension = collective_dimension(text, project)
        status = consultation_status(project)
        confidence = _confidence(case, dimension)
        urgency = _urgency(case, text)
        memory = tuple(
            sorted(
                self._memory_lookup.search_metadata(case.question),
                key=lambda item: (item.year or 0, item.document_id),
            )
        )
        return CSEConsultationAnalysis(
            self._base_engine.analyze(case),
            project,
            dimension,
            _timeline(project, confidence),
            _qualifications(case, project, dimension, confidence, urgency),
            mechanism(project, dimension),
            status,
            _questions(project, dimension, memory),
            document_requests(project),
            memory,
            _cse_position(case, memory),
            _employer_position(case),
            obstruction_assessment(project, status),
            _strategies(urgency),
            articulate(dimension, text),
            tuple(dict.fromkeys((*case.missing_information, *_missing(project)))),
            urgency,
            confidence,
            scenario_code,
        )


def _project_facts(case: SyndicalCaseInput, text: str) -> CSEProjectFacts:
    project_type = next(
        (kind for kind, markers in PROJECT_MARKERS.items() if any(marker in text for marker in markers)),
        ProjectType.UNKNOWN,
    )
    employees = None
    if any(marker in text for marker in ("plusieurs salarie", "plusieurs postes", "plusieurs equipes", "effectifs")):
        employees = 2
    elif any(marker in text for marker in ("un seul salarie", "cas individuel isole", "une personne")):
        employees = 1
    consultation = _boolean(text, ("cse a ete consulte", "consultation realisee"), ("sans consultation", "cse n a pas ete consulte", "absence de consultation"))
    information = _boolean(text, ("cse a ete informe", "information du cse", "cse a ete consulte"), ("sans information", "cse n a pas ete informe"))
    opinion = _boolean(text, ("avis rendu", "cse a rendu un avis", "rendu un avis"), ("aucun avis", "avant avis"))
    started = _boolean(text, ("mise en oeuvre a commence", "debut de mise en oeuvre", "deja mis en oeuvre"), ("mise en oeuvre n a pas commence", "avant mise en oeuvre"))
    decided = _boolean(text, ("decision deja prise", "decision definitive"), ("projet non finalise", "decision envisagee"))
    documents = tuple(item.document_type for item in case.available_pieces)
    if not documents and any(
        marker in text
        for marker in ("recu les documents", "documents transmis", "a recu les documents")
    ):
        documents = ("documents de consultation déclarés",)
    return CSEProjectFacts(
        project_type=project_type,
        signal_origin="question et faits déclarés",
        employees_affected=employees,
        affected_services=("service concerné à confirmer",) if "service" in text else (),
        decision_envisaged=True if "projet" in text or "annonce" in text else None,
        decision_already_taken=decided,
        implementation_started=started,
        cse_information_known=information,
        cse_consultation_known=consultation,
        opinion_rendered=opinion,
        transmitted_documents=documents,
        missing_documents=case.missing_information,
        employment_impacts=("effectifs ou postes à documenter",) if any(x in text for x in ("effectif", "poste", "emploi")) else (),
        schedule_impacts=("horaires ou cycles à documenter",) if any(x in text for x in ("horaire", "cycle", "equipe")) else (),
        remuneration_impacts=("conséquences de paie à analyser par R1C",) if any(x in text for x in ("remuneration", "paie", "prime")) else (),
        working_condition_impacts=("organisation et charge de travail à documenter",) if any(x in text for x in ("organisation", "outil", "methode")) else (),
        health_safety_signals=("signal santé-sécurité à orienter sans analyse CSSCT",) if any(x in text for x in ("sante", "securite", "risque")) else (),
        potentially_applicable_agreements=("accord INEOS à vérifier",) if "accord" in text or "ineos" in text else (),
        recurring_consultation=True if "consultation recurrente" in text else None,
    )


def _timeline(project: CSEProjectFacts, confidence: ConfidenceLevel) -> tuple[ProjectTimelineEvent, ...]:
    events = []
    if project.announcement_date or project.decision_envisaged:
        events.append(ProjectTimelineEvent("announcement", project.announcement_date, bool(project.announcement_date), "direction à confirmer", EventNature.MANAGEMENT_ANNOUNCEMENT, None, confidence, ("début de chronologie à confirmer",)))
    if project.cse_information_known:
        events.append(ProjectTimelineEvent("cse_information", None, False, "direction / CSE", EventNature.OFFICIAL_INFORMATION, None, confidence))
    if project.transmitted_documents:
        events.append(ProjectTimelineEvent("documents", None, False, "direction", EventNature.DOCUMENT_TRANSMISSION, ", ".join(project.transmitted_documents), confidence))
    if project.cse_consultation_known:
        events.append(ProjectTimelineEvent("cse_meeting", None, False, "CSE", EventNature.CSE_MEETING, None, confidence))
    if project.opinion_rendered:
        events.append(ProjectTimelineEvent("opinion", None, False, "CSE", EventNature.CSE_OPINION, None, confidence))
    if project.decision_already_taken:
        events.append(ProjectTimelineEvent("decision", None, False, "direction", EventNature.FORMALISED_DECISION, None, confidence))
    if project.implementation_started:
        events.append(ProjectTimelineEvent("implementation", project.implementation_date, bool(project.implementation_date), "direction", EventNature.IMPLEMENTATION, None, confidence))
    return tuple(events)


def _qualifications(case, project, dimension, confidence, urgency):
    facts = tuple(item.statement for item in case.declared_facts + case.established_facts) or ("Situation déclarée à documenter.",)
    labels = []
    if dimension is CollectiveDimension.ISOLATED_INDIVIDUAL:
        labels.append("mesure individuelle ; dimension collective non démontrée")
    else:
        labels.extend(("dimension collective possible", "consultation potentiellement requise"))
    if project.implementation_started and not project.opinion_rendered:
        labels.append("mise en œuvre anticipée apparente")
    if project.cse_consultation_known is False:
        labels.append("information ou consultation à vérifier")
    if not labels:
        labels.append("éléments insuffisants pour conclure")
    return tuple(
        CSEQualification(
            label,
            facts,
            ("qualification juridique non établie",),
            _missing(project),
            ("Code du travail", "accords INEOS", "Convention collective Chimie", "PV et ordre du jour", "jurisprudence"),
            ("présentation du projet", "chronologie", "impacts", "documents CSE"),
            ("simple ajustement opérationnel", "projet non finalisé", "information déjà transmise"),
            confidence,
            urgency,
            ("compétence du CSE à confirmer", "démarche graduée à préparer"),
        )
        for label in labels
    )


def _questions(project, dimension, memory):
    candidates = [
        (QuestionPriority.CRITICAL, "Combien de salariés et quels services sont concernés ?", "qualifier la dimension collective", project.employees_affected is not None and project.affected_services),
        (QuestionPriority.CRITICAL, "La décision est-elle déjà prise et la mise en œuvre a-t-elle commencé ?", "reconstituer le caractère préalable", project.decision_already_taken is not None and project.implementation_started is not None),
        (QuestionPriority.PRIORITY, "Le CSE a-t-il été informé ou consulté, à quelle date et sur quel ordre du jour ?", "identifier le mécanisme et sa chronologie", project.cse_information_known is not None and project.cse_consultation_known is not None),
        (QuestionPriority.PRIORITY, "Quels documents et données d'impact ont été transmis ?", "apprécier le caractère précis et suffisant des informations", bool(project.transmitted_documents)),
        (QuestionPriority.USEFUL, "Le projet modifie-t-il les postes, horaires, classifications, rémunérations ou effectifs ?", "identifier les domaines complémentaires", bool(project.employment_impacts or project.schedule_impacts or project.remuneration_impacts)),
        (QuestionPriority.USEFUL, "Un accord INEOS ou une négociation syndicale traite-t-il du sujet ?", "distinguer consultation et négociation", bool(project.potentially_applicable_agreements)),
        (QuestionPriority.COMPLEMENTARY, "Le sujet a-t-il déjà été évoqué dans un ancien PV et l'engagement est-il confirmé dans la source ?", "exploiter prudemment l'historique metadata-only", bool(memory)),
        (QuestionPriority.COMPLEMENTARY, "Existe-t-il une échéance ou une mise en œuvre imminente ?", "évaluer l'urgence", False),
    ]
    return tuple(CSEQuestion(priority, question, purpose) for priority, question, purpose, answered in candidates if not answered)


def _cse_position(case, memory):
    evidence = tuple(item.document_type for item in case.available_pieces)
    if memory:
        evidence += tuple(f"métadonnée historique: {item.title}" for item in memory)
    return ContradictoryPosition(
        ("dimension collective et conséquences à objectiver", "information précise et chronologie à vérifier"),
        ("faits convergents pouvant être documentés",),
        ("compétence et calendrier non déduits automatiquement",),
        evidence,
        ("projet complet", "impacts", "ordre du jour et avis"),
        ("simple ajustement", "consultation déjà réalisée"),
        ("demander les pièces et confronter la chronologie",),
        ("obligation de consultation", "qualification d'entrave"),
    )


def _employer_position(case):
    return ContradictoryPosition(
        ("mesure individuelle ou ajustement opérationnel possible", "projet possiblement non finalisé", "pouvoir de direction invoqué"),
        ("documents et consultation déjà réalisés s'ils sont vérifiables",),
        ("une affirmation non documentée reste insuffisante",),
        tuple(item.document_type for item in case.available_pieces),
        ("décision formalisée", "impacts", "réponses aux questions"),
        ("effets collectifs", "mise en œuvre irréversible"),
        ("documenter le périmètre, le calendrier et les mesures d'accompagnement",),
        ("régularité définitive", "absence d'impact significatif"),
    )


def _strategies(urgency):
    rows = (
        (1, "Sécurisation", "établir les faits et dater le projet", "élu ou délégué syndical", "chronologie fiable", "ne règle pas le fond", "perte de pièces", ("annonces", "ordre du jour", "PV"), "dossier factuel", "demande d'information"),
        (2, "Demande d'information", "obtenir projet, impacts et calendrier", "CSE", "éclaire l'analyse", "réponse possiblement incomplète", "retard", ("questions écrites",), "informations traçables", "action CSE"),
        (3, "Action CSE", "inscrire le sujet, demander réponses et préparer l'avis", "CSE", "formalise la démarche", "compétence à confirmer", "délai", ("ordre du jour", "documents"), "avis ou réserves", "action syndicale"),
        (4, "Action syndicale ou institutionnelle", "articuler négociation, inspection ou conseil", "organisation syndicale", "mobilise l'acteur compétent", "proportionnalité nécessaire", "crispation", ("accords", "dossier factuel"), "orientation qualifiée", "recours"),
        (5, "Recours", "examiner une contestation juridiquement fondée", "conseil juridique", "préserve les droits possibles", "aucune automaticité", "coût et aléa", ("preuves", "chronologie", "sources"), "décision éclairée", "suivi"),
    )
    return tuple(CSEStrategy(level, name, objective, urgency, actor, (advantage,), (limitation,), (risk,), pieces, result, next_step) for level, name, objective, actor, advantage, limitation, risk, pieces, result, next_step in rows)


def _missing(project):
    missing = []
    if project.employees_affected is None:
        missing.append("nombre de salariés concernés")
    if project.decision_already_taken is None:
        missing.append("état exact de la décision")
    if project.implementation_started is None:
        missing.append("date et état de mise en œuvre")
    if project.cse_information_known is None:
        missing.append("information du CSE")
    if project.cse_consultation_known is None:
        missing.append("consultation du CSE")
    if not project.transmitted_documents:
        missing.append("documents transmis")
    return tuple(missing)


def _confidence(case, dimension):
    if case.established_facts and case.available_pieces:
        return ConfidenceLevel.HIGH
    if case.declared_facts or dimension is CollectiveDimension.IDENTIFIED_COLLECTIVE_PROJECT:
        return ConfidenceLevel.MODERATE
    return ConfidenceLevel.LOW


def _urgency(case, text):
    if any(marker in text for marker in ("demain", "immediat", "irreversible")):
        return UrgencyLevel.IMMEDIATE
    if any(marker in text for marker in ("mise en oeuvre a commence", "deja mis en oeuvre", "refus de documents")):
        return UrgencyLevel.URGENT
    if "annonce" in text or "projet" in text:
        return max(case.urgency, UrgencyLevel.PROMPT, key=lambda item: list(UrgencyLevel).index(item))
    return case.urgency


def _boolean(text, yes_markers, no_markers):
    if any(marker in text for marker in no_markers):
        return False
    if any(marker in text for marker in yes_markers):
        return True
    return None


def _case_text(case):
    return _normalize(" ".join([case.question] + [item.statement for item in case.declared_facts + case.established_facts + case.hypotheses]))


def _normalize(value):
    normalized = unicodedata.normalize("NFKD", str(value))
    return " ".join("".join(char for char in normalized if not unicodedata.combining(char)).lower().replace("’", " ").replace("'", " ").replace("-", " ").split())
