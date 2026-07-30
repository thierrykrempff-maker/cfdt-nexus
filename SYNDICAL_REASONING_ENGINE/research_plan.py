"""Deterministic legal-issue identification and research planning.

This module plans searches from canonical facts.  It performs no I/O, network
access, document retrieval or legal qualification.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import unicodedata

from .factual_core import CaseFactualCore
from .factual_models import CanonicalFact, FactCategory
from .legal_issue_models import (
    IssueCategory,
    LegalIssue,
    PlanningStatus,
    ResearchExclusion,
    ResearchPlan,
    ResearchQuery,
    ResearchTarget,
    SourceFamily,
)


PLAN_VERSION = "2.0"


@dataclass(frozen=True, slots=True)
class _IssueRule:
    code: str
    category: IssueCategory
    title: str
    question: str
    fact_markers: tuple[str, ...]


_RULES: dict[str, tuple[_IssueRule, ...]] = {
    "INSULTING_EMAILS": (
        _IssueRule("email-ground", IssueCategory.DISCIPLINARY_GROUNDS, "Grief disciplinaire", "Les courriels envoyés à un collègue peuvent-ils constituer un grief disciplinaire ?", ("courriel", "insult")),
        _IssueRule("email-private-life", IssueCategory.PRIVATE_LIFE, "Vie personnelle", "Les faits relevaient-ils de la vie personnelle du salarié ?", ("alcool", "courriel")),
        _IssueRule("email-company-link", IssueCategory.DISCIPLINARY_GROUNDS, "Lien avec l’entreprise", "Quel lien concret existe entre les messages et l’entreprise ?", ("collègue", "mandat", "courriel")),
        _IssueRule("email-digital-proof", IssueCategory.DATA_PROTECTION, "Preuve numérique", "L’utilisation de la messagerie ou de données numériques pose-t-elle une question de preuve ou de protection des données ?", ("courriel", "preuve", "diffusion")),
        _IssueRule("email-procedure", IssueCategory.DISCIPLINARY_PROCEDURE, "Procédure disciplinaire", "La procédure disciplinaire suivie respecte-t-elle les règles applicables ?", ("convoqué", "procédure", "sanction")),
        _IssueRule("email-proportionality", IssueCategory.DISCIPLINARY_GROUNDS, "Proportionnalité", "La mesure envisagée est-elle proportionnée aux faits qui pourront être établis ?", ("antécédent", "caractère insultant", "mesure")),
    ),
    "BREAKS_AND_BADGE_CONTROL": (
        _IssueRule("break-duration", IssueCategory.BREAK_TIME, "Durée et nature des pauses", "Quelles pauses sont reconnues et quelle durée demeure à établir ?", ("pause",)),
        _IssueRule("break-internal-rule", IssueCategory.INTERNAL_PROCEDURE, "Règles internes sur les pauses", "Quelles règles internes encadrent les pauses cigarette sur le poste concerné ?", ("pause", "règles écrites")),
        _IssueRule("break-working-time", IssueCategory.WORKING_TIME, "Temps de travail effectif", "Dans quelles conditions ces pauses interrompent-elles le temps de travail effectif ?", ("pause", "temps de travail")),
        _IssueRule("badge-purpose", IssueCategory.EMPLOYEE_MONITORING, "Finalité du badgeage", "Le tourniquet peut-il être utilisé pour reconstituer les pauses au regard de sa finalité déclarée ?", ("tourniquet", "badgeage", "finalité")),
        _IssueRule("badge-proof", IssueCategory.DATA_PROTECTION, "Licéité de la preuve", "Les données de badgeage peuvent-elles être utilisées comme preuve dans ce dossier ?", ("badgeage", "données", "preuve")),
        _IssueRule("badge-information", IssueCategory.DATA_PROTECTION, "Information des salariés", "Les salariés et leurs représentants ont-ils été informés de cet usage des données ?", ("information", "consultation", "données")),
        _IssueRule("break-safety", IssueCategory.HEALTH_SAFETY, "Sécurité du site", "L’organisation des pauses est-elle compatible avec les contraintes de sécurité du site ?", ("seveso", "évacuation", "sécurité")),
        _IssueRule("break-cse", IssueCategory.CSE_INFORMATION_CONSULTATION, "Précédent CSE", "Le CSE a-t-il été informé, consulté ou saisi d’un précédent comparable ?", ("cse", "consultation")),
    ),
    "INSULTING_TAG": (
        _IssueRule("tag-ground", IssueCategory.DISCIPLINARY_GROUNDS, "Qualification du grief", "Quels faits matériels peuvent être attribués au salarié sans présumer leur qualification ?", ("tag", "inscription", "propos", "grossier", "harcèlement", "menace")),
        _IssueRule("tag-proof", IssueCategory.DISCIPLINARY_GROUNDS, "Preuve et attribution", "Quelles preuves permettent d’attribuer l’inscription au salarié ?", ("preuve", "photo", "témoin", "conteste", "visé")),
        _IssueRule("tag-procedure", IssueCategory.DISCIPLINARY_PROCEDURE, "Procédure", "La procédure engagée correspond-elle à la mesure réellement envisagée ?", ("sanction", "procédure", "recadrage")),
        _IssueRule("tag-health", IssueCategory.HEALTH_SAFETY, "Contexte de travail", "Le contexte de travail ou les risques psychosociaux doivent-ils être documentés séparément du grief ?", ("souffrance", "psychosociaux", "travail")),
    ),
    "WORK_SCHEDULE_CHANGE": (
        _IssueRule("shift-contract", IssueCategory.CONTRACT_CHANGE, "Contrat de travail", "Le contrat ou ses avenants permettent-ils le cycle proposé ?", ("contrat", "avenant", "horaire")),
        _IssueRule("shift-duration", IssueCategory.SHIFT_CHANGE, "Durée du changement", "Le passage en horaires postés est-il temporaire ou permanent ?", ("temporaire", "permanent", "durée")),
        _IssueRule("shift-cycle", IssueCategory.WORKING_TIME, "Cycle proposé", "Quel cycle, quels horaires et quels repos seraient effectivement appliqués ?", ("cycle", "poste", "horaire", "repos", "week-end", "jour férié", "nuit")),
        _IssueRule("shift-personal", IssueCategory.CONTRACT_CHANGE, "Conséquences personnelles", "Quelles conséquences personnelles concrètes le changement aurait-il pour la salariée ?", ("contrainte", "transport", "familial", "santé", "pleurs")),
        _IssueRule("shift-agreement", IssueCategory.COLLECTIVE_AGREEMENT, "Accord local applicable", "Quel accord local encadre le travail posté et le passage depuis un horaire de jour ?", ("accord", "travail posté", "laboratoire")),
        _IssueRule("shift-cse", IssueCategory.CSE_INFORMATION_CONSULTATION, "Rôle du CSE", "Le projet implique-t-il une information ou une consultation du CSE ?", ("cse", "effectif", "organisation")),
        _IssueRule("shift-consent", IssueCategory.CONTRACT_CHANGE, "Modification contractuelle", "Le changement relève-t-il des conditions de travail ou requiert-il l’accord du salarié ?", ("volontaire", "accepté", "imposer", "conteste", "refus", "production", "alternative", "suite définitive")),
    ),
    "CSSCT_MEETING_TIME": (
        _IssueRule("cssct-meeting", IssueCategory.CSSCT, "Temps de réunion", "Le temps concerné correspond-il à une réunion CSSCT convoquée ?", ("réunion cssct", "convocation", "récit", "refus")),
        _IssueRule("cssct-travel", IssueCategory.CSSCT, "Temps de déplacement", "Un temps de déplacement distinct doit-il être identifié ?", ("déplacement", "horaires")),
        _IssueRule("cssct-credit", IssueCategory.CSSCT, "Crédit d’heures", "Les heures relevaient-elles du crédit d’heures ou du temps de réunion ?", ("crédit d'heures", "heures", "qualification exacte", "retenue")),
        _IssueRule("cssct-use", IssueCategory.INTERNAL_PROCEDURE, "Conditions d’utilisation", "Quel canal et quel délai de prévenance étaient effectivement applicables ?", ("canal", "délai", "fichier")),
        _IssueRule("cssct-rules", IssueCategory.CSSCT, "Règles spécifiques CSSCT", "Quels textes et pratiques encadrent cette réunion CSSCT ?", ("accord cse", "règlement intérieur du cse", "pratique")),
    ),
    "CSE_MEETING_REST_TIME": (
        _IssueRule("cse-rest-status", IssueCategory.CSE_INFORMATION_CONSULTATION, "Nature de la réunion CSE", "La participation correspond-elle à une réunion CSE et en quelle qualité le salarié y assiste-t-il ?", ("cse", "réunion", "élu", "mandat", "convocation")),
        _IssueRule("cse-rest-working-time", IssueCategory.WORKING_TIME, "Temps de réunion pendant un repos", "Comment le temps de réunion CSE organisé pendant un repos doit-il être décompté et rémunéré ?", ("réunion", "repos", "payé", "temps")),
        _IssueRule("cse-rest-protection", IssueCategory.WORKING_TIME, "Protection du repos", "Le repos prévu doit-il être déplacé ou compensé compte tenu des horaires réellement accomplis ?", ("repos", "5x8", "horaire", "planning")),
        _IssueRule("cse-rest-local-rule", IssueCategory.COLLECTIVE_AGREEMENT, "Règle locale applicable", "Quel accord ou usage encadre le temps de réunion CSE lorsqu'il tombe sur un jour de repos ?", ("accord", "usage", "cse", "repos")),
    ),
    "UNPAID_OVERTIME": (
        _IssueRule("overtime-reality", IssueCategory.WORKING_TIME, "Réalité des heures", "Quelles heures supplémentaires sont établies par les pointages, plannings ou autres éléments concordants ?", ("heures supplémentaires", "pointage", "planning", "heures en plus")),
        _IssueRule("overtime-employer", IssueCategory.WORKING_TIME, "Connaissance de l'employeur", "Les heures ont-elles été demandées, validées ou rendues nécessaires par les tâches confiées ?", ("employeur", "demande", "validation", "charge", "nécessaires")),
        _IssueRule("overtime-pay", IssueCategory.PAYROLL, "Paiement et majorations", "Les heures établies ont-elles été payées ou compensées avec les majorations applicables ?", ("paie", "bulletin", "non payé", "majoration", "compensation")),
        _IssueRule("overtime-local-rule", IssueCategory.COLLECTIVE_AGREEMENT, "Règle locale de temps de travail", "Quel accord local encadre le décompte, la validation et la compensation des heures supplémentaires ?", ("accord", "temps de travail", "pointage")),
    ),
    "CLASSIFICATION_ACTUAL_DUTIES": (
        _IssueRule("classification-real-work", IssueCategory.CLASSIFICATION, "Fonctions réellement exercées", "Quelles tâches, responsabilités, autonomie et technicité sont effectivement exercées ?", ("tâches", "fonctions", "responsabilités", "autonomie", "technicité", "travail réel")),
        _IssueRule("classification-criteria", IssueCategory.CLASSIFICATION, "Critères conventionnels", "À quel niveau les fonctions réelles correspondent-elles dans la grille conventionnelle applicable ?", ("classification", "coefficient", "niveau", "groupe")),
        _IssueRule("classification-duration", IssueCategory.CLASSIFICATION, "Période concernée", "Depuis quand les fonctions correspondant à un niveau différent sont-elles exercées de manière vérifiable ?", ("depuis", "durée", "réellement")),
        _IssueRule("classification-pay", IssueCategory.PAYROLL, "Conséquences salariales", "Une reclassification établie emporterait-elle une régularisation de salaire ou de coefficient ?", ("salaire", "coefficient", "régularisation")),
    ),
    "NIGHT_WORK_FATIGUE": (
        _IssueRule("night-fatigue-schedule", IssueCategory.WORKING_TIME, "Cycles et repos", "Les cycles de nuit et les repos effectivement accordés respectent-ils les règles applicables ?", ("nuit", "cycle", "repos", "travail posté")),
        _IssueRule("night-fatigue-prevention", IssueCategory.HEALTH_SAFETY, "Prévention de la fatigue", "L'évaluation des risques et les mesures collectives traitent-elles la fatigue liée au travail de nuit ou posté ?", ("fatigue", "sécurité", "danger", "prévention", "duerp")),
        _IssueRule("night-fatigue-organization", IssueCategory.HEALTH_SAFETY, "Organisation du travail", "Les effectifs, rotations, pauses et charges de travail aggravent-ils un risque professionnel objectivable ?", ("organisation", "effectif", "rotation", "pause", "charge")),
        _IssueRule("night-fatigue-cse", IssueCategory.CSE_INFORMATION_CONSULTATION, "Alerte collective", "Le CSE ou la CSSCT ont-ils été saisis des risques liés aux nuits et à l'organisation ?", ("cse", "cssct", "alerte", "signalement")),
    ),
    "AMBIGUOUS_TEN_PERCENT_RULE": (
        _IssueRule("ten-percent-leave", IssueCategory.LEAVE, "Interprétation congés", "L’expression « règle des 10 % » désigne-t-elle une règle relative aux congés payés ?", ("10 %", "congé", "période de référence", "dixième")),
        _IssueRule("ten-percent-pay", IssueCategory.PAYROLL, "Interprétation indemnité", "L’expression désigne-t-elle une méthode de calcul d’une indemnité ou d’un élément de rémunération ?", ("10 %", "perte financière", "indemnité", "dixième")),
        _IssueRule("ten-percent-practice", IssueCategory.COLLECTIVE_AGREEMENT, "Interprétation accord ou pratique", "L’expression désigne-t-elle une règle conventionnelle ou une pratique interne ?", ("10 %", "accord", "pratique", "appliquée", "disparition")),
    ),
    "PPE_AVAILABILITY_OR_SUITABILITY": (
        _IssueRule("ppe-wearing", IssueCategory.PPE, "Obligation de port", "Quelle consigne imposait le port de l’EPI pour l’opération concernée ?", ("epi", "port", "consigne")),
        _IssueRule("ppe-available", IssueCategory.PPE, "Disponibilité réelle", "L’équipement requis était-il réellement disponible au moment des faits ?", ("disponibilité", "stock", "remise", "absence", "visière", "gants")),
        _IssueRule("ppe-fit", IssueCategory.PPE, "Adaptation de l’EPI", "L’équipement fourni était-il adapté au salarié et au risque ?", ("adaptation", "lunettes", "équipement")),
        _IssueRule("ppe-stop", IssueCategory.HEALTH_SAFETY, "Arrêt de l’opération", "Quelles consignes permettaient ou imposaient d’arrêter l’opération en l’absence d’EPI adapté ?", ("arrêt", "opération", "instruction")),
        _IssueRule("ppe-duerp", IssueCategory.HEALTH_SAFETY, "Évaluation du risque", "Le DUERP et l’analyse de l’opération identifient-ils le risque et les protections nécessaires ?", ("duerp", "analyse risque", "risque chimique")),
        _IssueRule("ppe-cssct", IssueCategory.CSSCT, "Rôle de la CSSCT", "La CSSCT a-t-elle examiné ce risque ou l’indisponibilité des équipements ?", ("cssct", "signalement")),
        _IssueRule("ppe-prevention", IssueCategory.HEALTH_SAFETY, "Références de prévention", "Quelles recommandations institutionnelles éclairent le choix et la disponibilité des EPI ?", ("prévention", "équipement", "risque")),
    ),
    "TECHNICAL_ERROR_AND_OUTDATED_PROCEDURE": (
        _IssueRule("procedure-applicable", IssueCategory.INTERNAL_PROCEDURE, "Procédure applicable", "Quelle version de la procédure interne était applicable au moment des faits ?", ("procédure", "version", "recette", "fournisseur", "dosage")),
        _IssueRule("procedure-access", IssueCategory.INTERNAL_PROCEDURE, "Accessibilité", "La procédure correcte était-elle accessible et portée à la connaissance du salarié ?", ("accessible", "formation", "terminal")),
        _IssueRule("procedure-proof", IssueCategory.DISCIPLINARY_GROUNDS, "Erreur et preuve", "Les éléments techniques permettent-ils d’attribuer l’erreur au salarié plutôt qu’à l’organisation ?", ("erreur", "historique", "preuve", "catalyseur", "cristallisé", "perte d'exploitation")),
        _IssueRule("procedure-risk", IssueCategory.HEALTH_SAFETY, "Risque opérationnel", "L’obsolescence alléguée de la procédure a-t-elle créé un risque devant être traité séparément ?", ("obsolète", "risque chimique", "mise à jour")),
    ),
    "POSITIVE_ALCOHOL_TEST": (
        _IssueRule("alcohol-safety", IssueCategory.HEALTH_SAFETY, "Mise en sécurité", "Quelles mesures immédiates de mise en sécurité ont été prises avant toute décision disciplinaire ?", ("mise en sécurité", "chariot", "poste", "haleine", "équilibre")),
        _IssueRule("alcohol-test", IssueCategory.ALCOHOL_TEST, "Contrôle", "Dans quelles conditions exactes le contrôle d’alcoolémie a-t-il été réalisé ?", ("éthylotest", "contrôle", "résultat")),
        _IssueRule("alcohol-device", IssueCategory.ALCOHOL_TEST, "Fiabilité de l’appareil", "La fiabilité, l’unité et la calibration de l’appareil sont-elles documentées ?", ("appareil", "calibration", "unité")),
        _IssueRule("alcohol-counter", IssueCategory.ALCOHOL_TEST, "Contre-expertise", "Une possibilité réelle de contestation ou de contre-expertise a-t-elle été offerte ?", ("contre-expertise", "contestation")),
        _IssueRule("alcohol-rule", IssueCategory.INTERNAL_PROCEDURE, "Règlement intérieur", "Le règlement intérieur autorise-t-il ce contrôle pour le poste et selon quelles garanties ?", ("règlement intérieur", "poste à risque")),
        _IssueRule("alcohol-procedure", IssueCategory.DISCIPLINARY_PROCEDURE, "Procédure disciplinaire", "La procédure distingue-t-elle la mise en sécurité, la preuve et la sanction ?", ("procédure", "sanction")),
        _IssueRule("alcohol-proportion", IssueCategory.DISCIPLINARY_GROUNDS, "Proportionnalité", "La mesure envisagée tient-elle compte des faits établis, de l’ancienneté et des antécédents ?", ("ancienneté", "antécédent", "mesure")),
        _IssueRule("alcohol-support", IssueCategory.HEALTH_SAFETY, "Prévention et accompagnement", "Quelles mesures de prévention ou d’accompagnement ont été proposées sans exposer de données médicales ?", ("médical", "social", "prévention", "difficultés personnelles")),
    ),
    "INSULTING_BEHAVIOR": (
        _IssueRule("insult-ground", IssueCategory.DISCIPLINARY_GROUNDS, "Propos reprochés", "Quels propos exacts et quel contexte professionnel peuvent être établis ?", ("propos", "insult", "injur")),
        _IssueRule("insult-proof", IssueCategory.DISCIPLINARY_GROUNDS, "Preuve", "Quels témoins ou documents permettent d’établir les propos sans extrapolation ?", ("témoin", "preuve", "publicité")),
        _IssueRule("insult-procedure", IssueCategory.DISCIPLINARY_PROCEDURE, "Procédure", "La procédure suivie correspond-elle au grief et à la mesure envisagée ?", ("procédure", "sanction", "faute grave")),
        _IssueRule("insult-fatigue", IssueCategory.WORKING_TIME, "Fatigue et repos", "Le planning et les repos doivent-ils être examinés comme contexte distinct du grief ?", ("fatigue", "repos", "planning", "poste de nuit", "postes de nuit", "fuite", "absence non remplacée")),
        _IssueRule("insult-proportion", IssueCategory.DISCIPLINARY_GROUNDS, "Proportionnalité", "La mesure envisagée est-elle proportionnée aux faits établis et au contexte ?", ("ancienneté", "antécédent", "contexte")),
    ),
}


_SOURCE_PRIORITY = {
    SourceFamily.INEOS_AGREEMENT: 1,
    SourceFamily.INEOS_INTERNAL_RULE: 2,
    SourceFamily.INEOS_PROCEDURE: 2,
    SourceFamily.INTERNAL_PRACTICE: 2,
    SourceFamily.EMPLOYMENT_CONTRACT: 2,
    SourceFamily.CCNIC_IDCC_44: 3,
    SourceFamily.LABOUR_CODE: 4,
    SourceFamily.REGULATION: 4,
    SourceFamily.CASE_LAW: 5,
    SourceFamily.OFFICIAL_GUIDANCE: 6,
    SourceFamily.CSE_MINUTES: 7,
    SourceFamily.CSSCT_MINUTES: 7,
    SourceFamily.OTHER: 7,
}


_TARGETS: dict[IssueCategory, tuple[SourceFamily, ...]] = {
    IssueCategory.DISCIPLINARY_PROCEDURE: (SourceFamily.INEOS_INTERNAL_RULE, SourceFamily.LABOUR_CODE),
    IssueCategory.DISCIPLINARY_GROUNDS: (SourceFamily.INEOS_INTERNAL_RULE, SourceFamily.LABOUR_CODE, SourceFamily.CASE_LAW),
    IssueCategory.PRIVATE_LIFE: (SourceFamily.EMPLOYMENT_CONTRACT, SourceFamily.CASE_LAW),
    IssueCategory.WORKING_TIME: (SourceFamily.INEOS_AGREEMENT, SourceFamily.CCNIC_IDCC_44, SourceFamily.LABOUR_CODE),
    IssueCategory.BREAK_TIME: (SourceFamily.INEOS_AGREEMENT, SourceFamily.INEOS_INTERNAL_RULE, SourceFamily.LABOUR_CODE),
    IssueCategory.SHIFT_CHANGE: (SourceFamily.INEOS_AGREEMENT, SourceFamily.EMPLOYMENT_CONTRACT, SourceFamily.CCNIC_IDCC_44),
    IssueCategory.CONTRACT_CHANGE: (SourceFamily.EMPLOYMENT_CONTRACT, SourceFamily.INEOS_AGREEMENT, SourceFamily.CASE_LAW),
    IssueCategory.PAYROLL: (SourceFamily.INEOS_AGREEMENT, SourceFamily.CCNIC_IDCC_44, SourceFamily.LABOUR_CODE),
    IssueCategory.HEALTH_SAFETY: (SourceFamily.INEOS_PROCEDURE, SourceFamily.LABOUR_CODE, SourceFamily.OFFICIAL_GUIDANCE),
    IssueCategory.PPE: (SourceFamily.INEOS_PROCEDURE, SourceFamily.LABOUR_CODE, SourceFamily.OFFICIAL_GUIDANCE),
    IssueCategory.ALCOHOL_TEST: (SourceFamily.INEOS_INTERNAL_RULE, SourceFamily.INEOS_PROCEDURE, SourceFamily.CASE_LAW),
    IssueCategory.DATA_PROTECTION: (SourceFamily.INEOS_INTERNAL_RULE, SourceFamily.OFFICIAL_GUIDANCE, SourceFamily.CASE_LAW),
    IssueCategory.EMPLOYEE_MONITORING: (SourceFamily.INEOS_INTERNAL_RULE, SourceFamily.OFFICIAL_GUIDANCE, SourceFamily.CSE_MINUTES),
    IssueCategory.CSE_INFORMATION_CONSULTATION: (SourceFamily.LABOUR_CODE, SourceFamily.CSE_MINUTES),
    IssueCategory.CSSCT: (SourceFamily.INEOS_AGREEMENT, SourceFamily.LABOUR_CODE, SourceFamily.CSSCT_MINUTES),
    IssueCategory.COLLECTIVE_AGREEMENT: (SourceFamily.INEOS_AGREEMENT, SourceFamily.CCNIC_IDCC_44),
    IssueCategory.CLASSIFICATION: (SourceFamily.INEOS_AGREEMENT, SourceFamily.CCNIC_IDCC_44),
    IssueCategory.LEAVE: (SourceFamily.INEOS_AGREEMENT, SourceFamily.CCNIC_IDCC_44, SourceFamily.LABOUR_CODE),
    IssueCategory.INTERNAL_PROCEDURE: (SourceFamily.INEOS_PROCEDURE, SourceFamily.INEOS_INTERNAL_RULE),
    IssueCategory.OTHER: (SourceFamily.LABOUR_CODE,),
}


_FAMILY_LABELS = {
    SourceFamily.INEOS_AGREEMENT: ("accord d’entreprise INEOS", "clause applicable"),
    SourceFamily.INEOS_INTERNAL_RULE: ("règlement ou règle interne", "article ou règle applicable"),
    SourceFamily.INEOS_PROCEDURE: ("procédure INEOS", "version, étape et consigne applicables"),
    SourceFamily.CCNIC_IDCC_44: ("CCNIC IDCC 44", "article conventionnel applicable"),
    SourceFamily.LABOUR_CODE: ("Code du travail", "article applicable"),
    SourceFamily.REGULATION: ("texte réglementaire", "article applicable"),
    SourceFamily.CASE_LAW: ("décision judiciaire comparable", "motif et faits comparables"),
    SourceFamily.OFFICIAL_GUIDANCE: ("recommandation officielle spécialisée", "recommandation pertinente"),
    SourceFamily.CSE_MINUTES: ("PV CSE", "discussion ou précédent interne"),
    SourceFamily.CSSCT_MINUTES: ("PV CSSCT", "discussion, alerte ou précédent interne"),
    SourceFamily.INTERNAL_PRACTICE: ("pratique interne", "élément matériel de pratique"),
    SourceFamily.EMPLOYMENT_CONTRACT: ("contrat ou avenant", "clause contractuelle applicable"),
    SourceFamily.OTHER: ("autre source identifiée", "référence vérifiable"),
}


_NEGATIVE_TERMS: dict[IssueCategory, tuple[str, ...]] = {
    IssueCategory.BREAK_TIME: ("télétravail", "forfait jours", "restauration", "indemnité repas"),
    IssueCategory.EMPLOYEE_MONITORING: ("télétravail", "géolocalisation hors site"),
    IssueCategory.PRIVATE_LIFE: ("alcool sur le lieu de travail", "alcoolémie au poste"),
    IssueCategory.PPE: ("avantage en nature", "mutuelle"),
    IssueCategory.ALCOHOL_TEST: ("alcool consommé au domicile sans prise de poste",),
    IssueCategory.CSSCT: ("congés payés", "rémunération variable"),
}


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", str(value))
    return " ".join(
        "".join(char for char in decomposed if not unicodedata.combining(char))
        .casefold()
        .replace("’", " ")
        .replace("'", " ")
        .replace("-", " ")
        .split()
    )


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:20]
    return f"{prefix}-{digest}"


def _matching_facts(core: CaseFactualCore, markers: tuple[str, ...]) -> tuple[CanonicalFact, ...]:
    facts = tuple(
        fact
        for fact in core.canonical_facts
        if fact.category is not FactCategory.MISSING_INFORMATION
    )
    normalized_markers = tuple(_normalize(marker) for marker in markers)
    matches = tuple(
        fact
        for fact in facts
        if any(marker in _normalize(fact.canonical_text) for marker in normalized_markers)
    )
    return matches or facts[:1]


def _planning_event_category(core: CaseFactualCore) -> str:
    """Keep the factual category while accepting equivalent schedule wording."""

    if core.event_category != "GENERAL_EMPLOYEE_QUESTION":
        return core.event_category
    text = _normalize(" ".join(fact.canonical_text for fact in core.canonical_facts))
    if (
        any(marker in text for marker in ("passage poste", "travail poste", "horaire poste"))
        and any(marker in text for marker in ("jour", "horaire", "cycle"))
    ):
        return "WORK_SCHEDULE_CHANGE"
    return core.event_category


def _scope(core: CaseFactualCore) -> tuple[str, str]:
    text = _normalize(" ".join(fact.canonical_text for fact in core.canonical_facts))
    if "laboratoire" in text:
        establishment = "INEOS_SARRALBE_LABORATORY"
    elif any(marker in text for marker in ("site", "seveso", "usine")):
        establishment = "CURRENT_INEOS_ESTABLISHMENT"
    else:
        establishment = "ESTABLISHMENT_NOT_ESTABLISHED"
    if "cariste" in text:
        population = "FORKLIFT_OPERATORS"
    elif "laboratoire" in text:
        population = "LABORATORY_EMPLOYEES"
    elif any(marker in text for marker in ("elu", "cssct", "cse")):
        population = "EMPLOYEE_REPRESENTATIVES"
    else:
        population = "EMPLOYEE_POPULATION_TO_CONFIRM"
    return establishment, population


def _generic_issue_rules(
    core: CaseFactualCore,
    event_rules: tuple[_IssueRule, ...],
) -> tuple[_IssueRule, ...]:
    """Add cross-domain issues only when their factual prerequisites coexist."""

    if any("proportion" in rule.code for rule in event_rules):
        return ()
    facts = tuple(
        fact
        for fact in core.canonical_facts
        if fact.category is not FactCategory.MISSING_INFORMATION
    )
    text = _normalize(" ".join(fact.canonical_text for fact in core.canonical_facts))
    employer_alleges_conduct = any(
        fact.category is FactCategory.ALLEGED
        and (
            fact.allegation_author == "EMPLOYER"
            or "employeur allegue" in _normalize(fact.canonical_text)
        )
        for fact in facts
    )
    has_individual_context = any(
        marker in text for marker in ("anciennete", "antecedent")
    )
    has_rule_knowledge_context = any(
        marker in text
        for marker in ("consigne", "instruction", "reglement", "formation", "information")
    )
    if not (
        employer_alleges_conduct
        and has_individual_context
        and has_rule_knowledge_context
    ):
        return ()
    return (
        _IssueRule(
            "generic-disciplinary-proportionality",
            IssueCategory.DISCIPLINARY_GROUNDS,
            "Proportionnalité d’une éventuelle sanction",
            (
                "Si le comportement reproché est établi, quelle mesure ou sanction serait "
                "proportionnée compte tenu des circonstances, de l’ancienneté, des "
                "antécédents, des moyens réellement disponibles et de l’organisation ?"
            ),
            (
                "manquement",
                "reproché",
                "employeur allègue",
                "absence",
                "ancienneté",
                "antécédent",
                "consigne",
                "instruction",
                "formation",
                "information",
                "disponibilité",
                "indisponibilité",
                "stock",
                "arrêter",
                "reporter",
            ),
        ),
    )


def identify_legal_issues(core: CaseFactualCore) -> tuple[LegalIssue, ...]:
    """Create distinct, non-conclusive legal questions from canonical facts."""

    event_rules = _RULES.get(_planning_event_category(core), ())
    rules = (*event_rules, *_generic_issue_rules(core, event_rules))
    blocked = bool(core.blocking_ambiguities)
    missing = tuple(
        fact
        for fact in core.canonical_facts
        if fact.category is FactCategory.MISSING_INFORMATION
    )
    issues: list[LegalIssue] = []
    for rule in rules:
        associated = _matching_facts(core, rule.fact_markers)
        issue_id = _stable_id("issue", core.origin_session_id, rule.code)
        formulations = tuple(
            dict.fromkeys(
                formulation.text
                for fact in associated
                for formulation in fact.original_formulations
            )
        )
        source_families = _TARGETS[rule.category]
        issues.append(
            LegalIssue(
                issue_id=issue_id,
                case_session_id=core.origin_session_id,
                title=rule.title,
                legal_question=rule.question,
                issue_category=rule.category,
                associated_fact_ids=tuple(fact.fact_id for fact in associated),
                blocking_fact_ids=(
                    tuple(fact.fact_id for fact in missing) if blocked else ()
                ),
                missing_information_ids=tuple(fact.fact_id for fact in missing),
                urgency=(
                    "HIGH"
                    if rule.category
                    in {
                        IssueCategory.DISCIPLINARY_PROCEDURE,
                        IssueCategory.HEALTH_SAFETY,
                        IssueCategory.ALCOHOL_TEST,
                    }
                    else "MEDIUM"
                ),
                status=(
                    PlanningStatus.BLOCKED_BY_MISSING_FACTS
                    if blocked
                    else PlanningStatus.READY
                ),
                confidence="LOW" if blocked else "MEDIUM",
                original_formulations=formulations,
                created_from_rules=(rule.code,),
                requires_external_search=any(
                    family
                    in {
                        SourceFamily.CCNIC_IDCC_44,
                        SourceFamily.LABOUR_CODE,
                        SourceFamily.REGULATION,
                        SourceFamily.CASE_LAW,
                        SourceFamily.OFFICIAL_GUIDANCE,
                    }
                    for family in source_families
                ),
                requires_internal_search=any(
                    family
                    in {
                        SourceFamily.INEOS_AGREEMENT,
                        SourceFamily.INEOS_INTERNAL_RULE,
                        SourceFamily.INEOS_PROCEDURE,
                        SourceFamily.INTERNAL_PRACTICE,
                        SourceFamily.EMPLOYMENT_CONTRACT,
                    }
                    for family in source_families
                ),
                requires_cse_search=any(
                    family in {SourceFamily.CSE_MINUTES, SourceFamily.CSSCT_MINUTES}
                    for family in source_families
                ),
            )
        )
    return tuple(issues)


def _purpose(issue: LegalIssue, family: SourceFamily) -> str:
    label, _ = _FAMILY_LABELS[family]
    if family is SourceFamily.CASE_LAW:
        return f"Rechercher des décisions factuellement comparables pour éclairer : {issue.legal_question}"
    if family in {SourceFamily.CSE_MINUTES, SourceFamily.CSSCT_MINUTES}:
        return f"Rechercher uniquement un précédent ou un contexte interne concernant : {issue.title}"
    return f"Vérifier dans {label} les règles ou éléments répondant précisément à : {issue.legal_question}"


def _families_for_issue(issue: LegalIssue) -> tuple[SourceFamily, ...]:
    families = list(_TARGETS[issue.issue_category])
    if "email-company-link" in issue.created_from_rules:
        families.append(SourceFamily.CSE_MINUTES)
    if "generic-disciplinary-proportionality" in issue.created_from_rules:
        families.extend(
            (
                SourceFamily.EMPLOYMENT_CONTRACT,
                SourceFamily.INTERNAL_PRACTICE,
                SourceFamily.CSE_MINUTES,
            )
        )
    return tuple(dict.fromkeys(families))


def _concepts(issue: LegalIssue, family: SourceFamily) -> tuple[str, ...]:
    words = [
        word
        for word in _normalize(f"{issue.title} {issue.legal_question}").split()
        if len(word) > 3
        and word
        not in {
            "dans",
            "quelle",
            "quelles",
            "peuvent",
            "doit",
            "elle",
            "sont",
            "cette",
            "pour",
            "avec",
        }
    ]
    concepts = list(dict.fromkeys(words))[:8]
    if family is SourceFamily.CASE_LAW:
        concepts.append("faits comparables")
    elif family is SourceFamily.OFFICIAL_GUIDANCE:
        concepts.append("recommandation officielle")
    return tuple(dict.fromkeys(concepts))


def _document_types(family: SourceFamily) -> tuple[str, ...]:
    return {
        SourceFamily.INEOS_AGREEMENT: ("COMPANY_AGREEMENT",),
        SourceFamily.INEOS_INTERNAL_RULE: ("INTERNAL_RULE", "INTERNAL_CHARTER"),
        SourceFamily.INEOS_PROCEDURE: ("INTERNAL_PROCEDURE", "WORK_INSTRUCTION"),
        SourceFamily.CCNIC_IDCC_44: ("COLLECTIVE_AGREEMENT",),
        SourceFamily.LABOUR_CODE: ("STATUTE",),
        SourceFamily.REGULATION: ("REGULATION",),
        SourceFamily.CASE_LAW: ("COURT_DECISION",),
        SourceFamily.OFFICIAL_GUIDANCE: ("OFFICIAL_GUIDANCE", "REFERENTIAL"),
        SourceFamily.CSE_MINUTES: ("CSE_MINUTES",),
        SourceFamily.CSSCT_MINUTES: ("CSSCT_MINUTES",),
        SourceFamily.INTERNAL_PRACTICE: ("INTERNAL_PRACTICE_EVIDENCE",),
        SourceFamily.EMPLOYMENT_CONTRACT: ("EMPLOYMENT_CONTRACT", "AMENDMENT"),
        SourceFamily.OTHER: ("VERIFIABLE_DOCUMENT",),
    }[family]


def _exclusions(issues: tuple[LegalIssue, ...]) -> tuple[ResearchExclusion, ...]:
    categories = {issue.issue_category for issue in issues}
    selected_families = {
        family for issue in issues for family in _families_for_issue(issue)
    }
    exclusions: list[ResearchExclusion] = []
    if not categories & {IssueCategory.DATA_PROTECTION, IssueCategory.EMPLOYEE_MONITORING}:
        exclusions.append(ResearchExclusion(SourceFamily.OFFICIAL_GUIDANCE, "CNIL exclue : aucune surveillance ni donnée personnelle n’est en cause."))
    if not categories & {IssueCategory.HEALTH_SAFETY, IssueCategory.PPE, IssueCategory.ALCOHOL_TEST}:
        exclusions.append(ResearchExclusion(SourceFamily.OFFICIAL_GUIDANCE, "CARSAT et INRS exclues : aucun besoin de prévention n’est identifié."))
    if not categories & {IssueCategory.PAYROLL, IssueCategory.LEAVE}:
        exclusions.append(ResearchExclusion(SourceFamily.OFFICIAL_GUIDANCE, "CPAM exclue : aucun arrêt, IJ, AT/MP ou besoin assurantiel n’est identifié."))
    if SourceFamily.CSE_MINUTES not in selected_families:
        exclusions.append(
            ResearchExclusion(SourceFamily.CSE_MINUTES, "PV CSE exclus : aucune question ou recherche contextuelle CSE n’est identifiée.")
        )
    if SourceFamily.CSSCT_MINUTES not in selected_families:
        exclusions.append(
            ResearchExclusion(SourceFamily.CSSCT_MINUTES, "PV CSSCT exclus : aucune question CSSCT n’est identifiée.")
        )
    return tuple(exclusions)


def build_research_plan(
    core: CaseFactualCore,
    *,
    created_at: str | None = None,
) -> ResearchPlan:
    """Build a serializable issue-led plan without executing any search."""

    issues = identify_legal_issues(core)
    event_category = _planning_event_category(core)
    establishment, population = _scope(core)
    targets: list[ResearchTarget] = []
    ready_queries: list[ResearchQuery] = []
    blocked_queries: list[ResearchQuery] = []
    for issue in issues:
        families = _families_for_issue(issue)
        for family in families:
            target_id = _stable_id("target", issue.issue_id, family.value)
            label, expected = _FAMILY_LABELS[family]
            mandatory = family in {
                SourceFamily.INEOS_INTERNAL_RULE,
                SourceFamily.INEOS_PROCEDURE,
                SourceFamily.EMPLOYMENT_CONTRACT,
            } or (
                issue.issue_category is IssueCategory.COLLECTIVE_AGREEMENT
                and family is SourceFamily.INEOS_AGREEMENT
            )
            target = ResearchTarget(
                target_id=target_id,
                issue_id=issue.issue_id,
                source_family=family,
                source_priority=_SOURCE_PRIORITY[family],
                purpose=_purpose(issue, family),
                mandatory=mandatory,
                expected_reference_type=label,
                expected_evidence=expected,
                fallback_allowed=not mandatory,
                exclusion_reasons=(
                    (
                        "Écarter cette cible si aucune surveillance, consultation de messagerie, "
                        "traçage ou donnée personnelle n’est matériellement en cause.",
                    )
                    if (
                        family is SourceFamily.OFFICIAL_GUIDANCE
                        and issue.issue_category is IssueCategory.DATA_PROTECTION
                    )
                    else ()
                ),
            )
            targets.append(target)
            concepts = _concepts(issue, family)
            conditional = (
                issue.status is PlanningStatus.BLOCKED_BY_MISSING_FACTS
                and event_category == "AMBIGUOUS_TEN_PERCENT_RULE"
            )
            status = (
                PlanningStatus.CONDITIONAL_QUERY
                if conditional
                else issue.status
            )
            query = ResearchQuery(
                query_id=_stable_id("query", issue.issue_id, target_id),
                issue_id=issue.issue_id,
                target_id=target_id,
                query_text=" ".join(concepts),
                concepts=concepts,
                factual_scope=issue.original_formulations,
                temporal_scope="FACT_PERIOD_TO_CONFIRM",
                establishment_scope=establishment,
                employee_population_scope=population,
                document_types=_document_types(family),
                expected_reference=label,
                expected_excerpt=expected,
                negative_terms=_NEGATIVE_TERMS.get(issue.issue_category, ()),
                priority=target.source_priority,
                mandatory=mandatory,
                reason=target.purpose,
                status=status,
            )
            if issue.status is PlanningStatus.BLOCKED_BY_MISSING_FACTS:
                blocked_queries.append(query)
            else:
                ready_queries.append(query)

    targets.sort(key=lambda item: (item.source_priority, item.issue_id, item.target_id))
    ready_queries.sort(key=lambda item: (item.priority, item.issue_id, item.target_id))
    blocked_queries.sort(key=lambda item: (item.priority, item.issue_id, item.target_id))
    if not issues:
        completeness = PlanningStatus.NOT_RELEVANT
    elif core.blocking_ambiguities:
        completeness = PlanningStatus.BLOCKED_BY_MISSING_FACTS
    elif any(issue.missing_information_ids for issue in issues):
        completeness = PlanningStatus.PARTIALLY_READY
    else:
        completeness = PlanningStatus.READY
    warnings = tuple(core.blocking_ambiguities)
    if event_category == "TECHNICAL_ERROR_AND_OUTDATED_PROCEDURE":
        warnings += (
            "La procédure interne est une cible obligatoire et ne peut pas être remplacée par une source générique.",
        )
    return ResearchPlan(
        plan_id=_stable_id("plan", core.origin_session_id, PLAN_VERSION),
        case_session_id=core.origin_session_id,
        issues=issues,
        targets=tuple(targets),
        queries=tuple(ready_queries),
        blocked_queries=tuple(blocked_queries),
        exclusions=_exclusions(issues),
        warnings=warnings,
        completeness_status=completeness,
        created_at=created_at,
        version=PLAN_VERSION,
    )


__all__ = (
    "PLAN_VERSION",
    "build_research_plan",
    "identify_legal_issues",
)
