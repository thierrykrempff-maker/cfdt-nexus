"""Read-only public projection of the tested V1 business cases.

The source fixtures remain the single source of the tested analyses.  This
module deliberately exposes only presentation metadata and the validated
``public_summary`` fields.  It is not imported by the analysis runtime and
cannot inject a historical case into a new employee request.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from NEXUS_RUNTIME_INTEGRATION.source_extraction import (
    DocumentAvailability,
    build_source_extraction_report,
)
from SYNDICAL_REASONING_ENGINE import CaseFactualCore, source_topic_relevance


ROOT = Path(__file__).resolve().parents[2]
VALIDATION_ROOT = (
    ROOT / "tests" / "fixtures" / "real_business_cases" / "v1_release_validation"
)
RESULTS_PATH = VALIDATION_ROOT / "v1-release-results.json"
RAW_ROOT = VALIDATION_ROOT / "raw"
SOURCE_BASELINE_ROOT = (
    ROOT
    / "tests"
    / "fixtures"
    / "real_business_cases"
    / "source_to_facts_baseline"
    / "raw"
)

PUBLIC_SUMMARY_FIELDS = (
    "situation",
    "strengths",
    "weaknesses",
    "priority_questions",
    "documents",
    "rule_to_facts",
    "syndical_position",
    "strategy",
    "limits",
    "next_actions",
    "avoid",
    "useful_wording",
    "urgency",
    "urgency_reason",
    "sources",
)
FORBIDDEN_PUBLIC_KEYS = frozenset(
    {
        "evaluation_expectations",
        "evaluation_only",
        "known_outcome",
        "logs",
        "diagnostics",
        "fingerprint",
        "request",
        "raw_request",
        "detailed_analysis",
        "technical_score",
        "chunk_id",
        "storage_id",
    }
)
SENSITIVE_TEXT_PATTERNS = (
    re.compile(r"[A-Za-z]:\\"),
    re.compile(r"(?<!\w)/(?:tmp|home|Users)/", re.IGNORECASE),
    re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"\b(?:\+33|0)[1-9](?:[\s.-]?\d{2}){4}\b"),
)

FILTERS = (
    {"id": "all", "label": "Tous"},
    {"id": "disciplinary", "label": "Disciplinaire"},
    {"id": "working_time", "label": "Temps de travail"},
    {"id": "health_safety", "label": "Santé et sécurité"},
    {"id": "personal_data", "label": "Données personnelles"},
    {"id": "cse_cssct", "label": "CSE / CSSCT"},
    {"id": "organization", "label": "Organisation du travail"},
    {"id": "suspended", "label": "Cas suspendus"},
)

CASE_PRESENTATION = {
    "REAL-01": {
        "fixture": "real-01-insulting_emails_alcohol.response.json",
        "title": "Courriels insultants et alcool",
        "domain": "Discipline / santé et sécurité",
        "capacity": "Préparer une défense disciplinaire sans confondre faits reconnus et allégations.",
        "categories": ("disciplinary", "health_safety"),
        "keywords": ("alcool", "courriels", "insultes", "disciplinaire"),
    },
    "REAL-02": {
        "fixture": "real-02-smoking_breaks_seveso_badge.response.json",
        "title": "Pauses cigarettes et utilisation du badgeage Seveso",
        "domain": "Discipline / preuve / données personnelles",
        "capacity": "Distinguer les pauses, le temps de travail et la licéité de l’usage du badgeage.",
        "categories": ("disciplinary", "personal_data"),
        "keywords": ("badgeage", "pauses", "cigarettes", "seveso", "cnil"),
    },
    "REAL-03": {
        "fixture": "real-03-tag_installation.response.json",
        "title": "Tag sur installation et souffrance au travail",
        "domain": "Discipline / santé et sécurité",
        "capacity": "Relier un grief disciplinaire au contexte de travail et aux obligations de prévention.",
        "categories": ("disciplinary", "health_safety", "organization"),
        "keywords": ("tag", "installation", "souffrance", "travail"),
    },
    "REAL-04": {
        "fixture": "real-04-forced_day_to_shift_laboratory.response.json",
        "title": "Passage forcé de jour vers horaires postés",
        "domain": "Temps et organisation du travail",
        "capacity": "Défendre un salarié face à un changement imposé d’horaires et d’organisation.",
        "categories": ("working_time", "organization"),
        "keywords": ("horaires", "jour", "poste", "laboratoire"),
    },
    "REAL-05": {
        "fixture": "real-05-delegation_hours_cssct_incomplete.response.json",
        "title": "Heures de délégation CSSCT, cas incomplet",
        "domain": "CSE / CSSCT",
        "capacity": "Suspendre l’analyse lorsque les faits indispensables sur le mandat ne sont pas disponibles.",
        "categories": ("cse_cssct", "suspended"),
        "keywords": ("cssct", "délégation", "heures", "incomplet"),
        "notes": (
            "Récit incomplet.",
            "Analyse volontairement suspendue.",
            "Aucune conclusion automatique sur une éventuelle entrave.",
            "Des informations complémentaires sont nécessaires.",
        ),
    },
    "REAL-06": {
        "fixture": "real-06-annual_leave_ten_percent_unresolved.response.json",
        "title": "Règle des 10 % sur les congés, ambiguïté non résolue",
        "domain": "Temps de travail / congés",
        "capacity": "Refuser de choisir arbitrairement entre plusieurs sens possibles d’une règle imprécise.",
        "categories": ("working_time", "suspended"),
        "keywords": ("congés", "10 %", "dix pour cent", "ambiguïté"),
        "notes": (
            "Le sens de la règle des 10 % n’est pas défini.",
            "Une clarification est obligatoire.",
            "Aucune hypothèse juridique n’est choisie automatiquement.",
        ),
    },
    "REAL-07": {
        "fixture": "real-07-safety_ppe_unavailable_or_unsuitable.response.json",
        "title": "EPI indisponible ou inadapté",
        "domain": "Santé et sécurité",
        "capacity": "Examiner un manquement EPI en contrôlant aussi leur disponibilité et leur adaptation.",
        "categories": ("health_safety",),
        "keywords": ("epi", "sécurité", "protection", "indisponible", "inadapté"),
    },
    "REAL-08": {
        "fixture": "real-08-temporary_day_to_three_shift_refusal.response.json",
        "title": "Passage temporaire de jour vers 3x8",
        "domain": "Temps et organisation du travail",
        "capacity": "Qualifier un passage temporaire en 3x8 et préparer une réponse syndicale proportionnée.",
        "categories": ("working_time", "organization"),
        "keywords": ("horaires", "3x8", "jour", "temporaire", "refus"),
    },
    "REAL-09": {
        "fixture": "real-09-chemical_recipe_outdated_procedure.response.json",
        "title": "Erreur de fabrication et procédure obsolète",
        "domain": "Santé, sécurité et organisation du travail",
        "capacity": "Identifier qu’une procédure interne absente empêche de conclure sur une erreur technique.",
        "categories": ("health_safety", "organization"),
        "keywords": ("procédure", "fabrication", "recette", "obsolète"),
        "notes": (
            "La compréhension factuelle est validée.",
            "Une source interne essentielle est absente.",
            "Aucune procédure ou instruction n’a été fabriquée.",
            "L’analyse reste limitée tant que la version applicable n’est pas disponible.",
        ),
    },
    "REAL-10": {
        "fixture": "real-10-positive_alcohol_test_high_risk_position.response.json",
        "title": "Alcoolémie sur poste à risque",
        "domain": "Discipline / santé et sécurité",
        "capacity": "Contrôler la fiabilité d’un test, la procédure suivie et la proportionnalité de la sanction.",
        "categories": ("disciplinary", "health_safety"),
        "keywords": ("alcool", "alcoolémie", "poste", "risque", "sécurité"),
    },
    "REAL-11": {
        "fixture": "real-11-insults_supervisor_fatigue_context.response.json",
        "title": "Insultes envers un responsable dans un contexte de fatigue",
        "domain": "Discipline / organisation du travail",
        "capacity": "Construire une défense qui tient compte du grief comme du contexte de fatigue et d’organisation.",
        "categories": ("disciplinary", "health_safety", "organization"),
        "keywords": ("insultes", "responsable", "fatigue", "organisation"),
    },
}

CASE_EVENT_CATEGORIES = {
    "REAL-01": "INSULTING_EMAILS",
    "REAL-02": "BREAKS_AND_BADGE_CONTROL",
    "REAL-03": "INSULTING_TAG",
    "REAL-04": "WORK_SCHEDULE_CHANGE",
    "REAL-05": "CSSCT_MEETING_TIME",
    "REAL-06": "AMBIGUOUS_TEN_PERCENT_RULE",
    "REAL-07": "PPE_AVAILABILITY_OR_SUITABILITY",
    "REAL-08": "WORK_SCHEDULE_CHANGE",
    "REAL-09": "TECHNICAL_ERROR_AND_OUTDATED_PROCEDURE",
    "REAL-10": "POSITIVE_ALCOHOL_TEST",
    "REAL-11": "INSULTING_BEHAVIOR",
}


# Curated public excerpts are limited to collective texts already present in the
# local documentary index.  They repair the presentation of the historical
# dossiers without changing their facts, scores, status or validated analysis.
# No technical identifier or local path is retained here.
CASE_SOURCE_PRESENTATION = {
    "REAL-01": (
        {
            "title": "INEOS Sarralbe — Règlement intérieur, procédure disciplinaire",
            "nature": "Règlement intérieur",
            "status": "RETRIEVED",
            "reference": "Page 10 · Art. 34 à 36",
            "excerpt": (
                "Aucune sanction ne peut être infligée sans que le salarié soit "
                "informé par écrit des griefs retenus. L’échelle des sanctions doit "
                "être appliquée proportionnellement à la gravité de la faute."
            ),
            "practical_use": (
                "Encadre la procédure, la connaissance exacte du grief et la "
                "proportionnalité d’une éventuelle sanction."
            ),
            "reserve": "Vérifier la version applicable à la date des faits.",
        },
    ),
    "REAL-02": (
        {
            "title": "INEOS Sarralbe — Règlement intérieur, horaires et pauses",
            "nature": "Règlement intérieur",
            "status": "RETRIEVED",
            "reference": "Page 6 · Art. 22 et 23",
            "excerpt": (
                "Le personnel doit se trouver à son poste, en tenue de travail, aux "
                "heures fixées pour le début et la fin du travail. L’usage des "
                "distributeurs à boissons ne doit pas conduire à une perte de temps "
                "excessive, sans rapport avec le temps normal de consommation."
            ),
            "practical_use": (
                "Permet de distinguer la règle interne sur les horaires et les pauses "
                "de la question séparée de l’utilisation des données du tourniquet."
            ),
            "reserve": (
                "Ce passage ne suffit pas à autoriser l’utilisation disciplinaire du "
                "badgeage de sécurité."
            ),
        },
    ),
    "REAL-03": (
        {
            "title": "INEOS Sarralbe — Règlement intérieur",
            "nature": "Règlement intérieur",
            "status": "RETRIEVED",
            "reference": "Page 10 · Art. 35 et 36",
            "excerpt": (
                "Les sanctions sont prises proportionnellement à la gravité de la "
                "faute. Le règlement cite notamment les injures et la dégradation "
                "volontaire parmi les faits pouvant être considérés comme graves."
            ),
            "practical_use": (
                "Relie le grief réel — inscription grossière et éventuelle "
                "dégradation — à l’échelle disciplinaire sans changer la "
                "qualification du grief."
            ),
            "reserve": (
                "Il faut encore établir le contenu exact, la visibilité, le dommage "
                "et le caractère volontaire de la dégradation."
            ),
        },
        {
            "title": "Convention collective Chimie — Conditions de travail",
            "nature": "Convention collective",
            "status": "RETRIEVED",
            "reference": "Page 146 · Art. 1",
            "excerpt": (
                "La charge de travail doit rester compatible avec la santé des "
                "salariés et les effectifs doivent être suffisants pour éviter toute "
                "charge excessive."
            ),
            "practical_use": (
                "Donne un cadre collectif pour vérifier le contexte de travail "
                "allégué, sans lui attribuer automatiquement une qualification "
                "juridique."
            ),
            "reserve": "Le contexte doit être étayé par des faits et signalements précis.",
        },
    ),
    "REAL-04": (
        {
            "title": "INEOS Sarralbe — Avenant horaires LABO du 12 juin 2012",
            "nature": "Accord d’entreprise",
            "status": "RETRIEVED",
            "reference": "Page 2",
            "excerpt": (
                "Une organisation en trois équipes sur deux postes, matin et "
                "après-midi, sept jours par semaine, est créée. Le cycle est de neuf "
                "semaines, sans coupure le week-end et sans travail de nuit."
            ),
            "practical_use": (
                "Décrit précisément le cycle local susceptible d’être proposé au "
                "laboratoire : week-ends inclus, sans poste de nuit."
            ),
            "reserve": "Vérifier que cet avenant et ce cycle sont bien ceux proposés.",
        },
        {
            "title": "INEOS Sarralbe — Avenant horaires 5x8 du 12 juin 2012",
            "nature": "Accord d’entreprise",
            "status": "RETRIEVED",
            "reference": "Page 2",
            "excerpt": (
                "Le personnel posté continu travaille en 5x8 sur trois postes matin, "
                "après-midi et nuit, sept jours par semaine, selon un cycle de cinq "
                "semaines."
            ),
            "practical_use": (
                "Évite de confondre le cycle LABO sans nuit avec le régime 5x8 qui "
                "comprend un poste de nuit."
            ),
            "reserve": "Source de comparaison : ne pas l’appliquer sans vérifier le cycle annoncé.",
        },
        {
            "title": "Convention collective Chimie — Charge de travail et effectifs",
            "nature": "Convention collective",
            "status": "RETRIEVED",
            "reference": "Page 146 · Art. 1",
            "excerpt": (
                "Les normes de travail sont établies en prenant en compte un effectif "
                "suffisant pour éviter toute charge excessive et permettre "
                "l’utilisation réelle des temps de repos."
            ),
            "practical_use": (
                "Fonde la demande d’une étude des effectifs et de la charge du service "
                "de jour après le départ d’une personne."
            ),
            "reserve": "La charge réelle et les effectifs avant/après restent à documenter.",
        },
    ),
    "REAL-07": (
        {
            "title": "INEOS Sarralbe — Règlement intérieur",
            "nature": "Règlement intérieur",
            "status": "RETRIEVED",
            "reference": "Page 2 · Art. 4",
            "excerpt": (
                "Tout membre du personnel doit utiliser les équipements de protection "
                "individuelle mis à sa disposition conformément à leur destination. "
                "Le règlement cite notamment le casque, les lunettes, les gants, les "
                "chaussures et le harnais de sécurité."
            ),
            "practical_use": (
                "Établit l’obligation d’utiliser les EPI prévus tout en imposant de "
                "vérifier qu’ils ont réellement été mis à disposition et sont adaptés."
            ),
            "reserve": "La consigne propre à l’opération et l’EPI disponible restent à vérifier.",
        },
    ),
    "REAL-08": (
        {
            "title": "INEOS Sarralbe — Avenant horaires 5x8 du 12 juin 2012",
            "nature": "Accord d’entreprise",
            "status": "RETRIEVED",
            "reference": "Page 2",
            "excerpt": (
                "L’organisation 5x8 repose sur cinq équipes couvrant trois postes — "
                "matin, après-midi et nuit — sept jours par semaine, selon un cycle de "
                "cinq semaines."
            ),
            "practical_use": (
                "Décrit le régime posté auquel la mesure temporaire doit être comparée."
            ),
            "reserve": (
                "La durée temporaire, le planning individuel et le fondement contractuel "
                "doivent encore être établis."
            ),
        },
        {
            "title": "INEOS Sarralbe — Avenant horaires LABO du 12 juin 2012",
            "nature": "Accord d’entreprise",
            "status": "RETRIEVED",
            "reference": "Page 2",
            "excerpt": (
                "Le cycle LABO décrit une organisation sur deux postes, matin et "
                "après-midi, sept jours par semaine, sans travail de nuit."
            ),
            "practical_use": (
                "Permet de comparer deux organisations postées distinctes au lieu de "
                "les présenter comme équivalentes."
            ),
            "reserve": "Vérifier le roulement réellement proposé au salarié.",
        },
        {
            "title": "Convention collective Chimie — Charge de travail et effectifs",
            "nature": "Convention collective",
            "status": "RETRIEVED",
            "reference": "Page 146 · Art. 1",
            "excerpt": (
                "La charge de travail doit rester compatible avec la santé et les "
                "effectifs doivent permettre d’éviter une charge excessive."
            ),
            "practical_use": (
                "Justifie l’examen des effets concrets du changement temporaire sur la "
                "fatigue, les repos et les équipes concernées."
            ),
            "reserve": "Les conséquences concrètes du planning doivent être objectivées.",
        },
    ),
    "REAL-10": (
        {
            "title": "INEOS Sarralbe — Règlement intérieur, contrôle d’alcoolémie",
            "nature": "Règlement intérieur",
            "status": "RETRIEVED",
            "reference": "Pages 3 et 4 · Art. 10",
            "excerpt": (
                "Le contrôle d’alcoolémie est limité notamment aux travaux à risque et "
                "aux conducteurs. Il doit être réalisé en présence d’un tiers, après "
                "information sur la possibilité d’une contre-expertise immédiate par "
                "prise de sang."
            ),
            "practical_use": (
                "Permet de contrôler le poste concerné, la présence du tiers et "
                "l’effectivité de la contre-expertise avant d’apprécier la sanction."
            ),
            "reserve": "L’appareil, l’heure, l’unité et la traçabilité du test restent à vérifier.",
        },
        {
            "title": "INEOS Sarralbe — Règlement intérieur, procédure disciplinaire",
            "nature": "Règlement intérieur",
            "status": "RETRIEVED",
            "reference": "Page 10 · Art. 34 et 35",
            "excerpt": (
                "Le salarié doit être informé par écrit des griefs retenus et pouvoir "
                "présenter ses explications. Toute sanction doit rester "
                "proportionnelle à la gravité de la faute."
            ),
            "practical_use": (
                "Sépare la validité du contrôle de la procédure disciplinaire et de la "
                "proportionnalité de la mesure envisagée."
            ),
            "reserve": "Vérifier les dates et la mesure réellement envisagée.",
        },
    ),
    "REAL-11": (
        {
            "title": "INEOS Sarralbe — Règlement intérieur",
            "nature": "Règlement intérieur",
            "status": "RETRIEVED",
            "reference": "Page 10 · Art. 35 et 36",
            "excerpt": (
                "Le règlement prévoit une échelle de sanctions proportionnelle à la "
                "gravité de la faute et cite les injures parmi les faits susceptibles "
                "d’être considérés comme graves."
            ),
            "practical_use": (
                "Établit le cadre disciplinaire applicable aux propos sans neutraliser "
                "l’examen du contexte, des antécédents et de la proportionnalité."
            ),
            "reserve": "Les mots exacts, le contexte et la diffusion doivent être établis.",
        },
        {
            "title": "Convention collective Chimie — Charge de travail et effectifs",
            "nature": "Convention collective",
            "status": "RETRIEVED",
            "reference": "Page 146 · Art. 1",
            "excerpt": (
                "Les normes de travail ne doivent pas imposer une fatigue excessive. "
                "La charge doit rester compatible avec la santé et les effectifs "
                "doivent être suffisants pour éviter une charge excessive."
            ),
            "practical_use": (
                "Permet de vérifier séparément si la fatigue et l’organisation du "
                "travail ont contribué au contexte, sans excuser automatiquement les "
                "propos."
            ),
            "reserve": "Le lien entre organisation, fatigue et incident doit être documenté.",
        },
    ),
}


CASE_MISSING_DOCUMENTS = {
    "REAL-02": (
        {
            "document": "Information des salariés sur la finalité du badgeage",
            "reason": (
                "Vérifier si le tourniquet de sécurité peut aussi servir au contrôle "
                "du temps ou à une procédure disciplinaire."
            ),
            "priority": "BLOCKING",
        },
        {
            "document": "Ressource CNIL applicable au contrôle de l’activité",
            "reason": (
                "Contrôler la finalité déclarée, l’information, les destinataires et "
                "la durée de conservation sans présenter un catalogue metadata-only "
                "comme une règle extraite."
            ),
            "priority": "HIGH",
        },
    ),
}

CASE_KEEP_BASELINE_SOURCES = frozenset({"REAL-01", "REAL-02", "REAL-03"})


CASE_UNION_ADVICE = {
    "REAL-01": (
        "Faire établir séparément les courriels reconnus, leur contenu exact, leurs destinataires et les éléments seulement allégués.",
        "Préparer avec le salarié une chronologie courte avant l’entretien et exiger que le grief ne soit pas élargi oralement.",
        "Discuter la proportionnalité au regard du contexte, des antécédents et de la diffusion réellement prouvée.",
    ),
    "REAL-02": (
        "Demander le relevé précis des pauses reprochées et la méthode de calcul retenue par la direction.",
        "Séparer la finalité de sécurité du tourniquet de toute réutilisation pour contrôler l’activité ou sanctionner.",
        "Exiger l’information remise aux salariés et l’avis du CSE avant d’admettre la licéité de cette preuve.",
    ),
    "REAL-03": (
        "Faire préciser les mots, le support, la visibilité, le nettoyage et l’existence d’un dommage matériel.",
        "Ne pas laisser qualifier les faits de harcèlement en l’absence d’agissements répétés dirigés contre une personne.",
        "Documenter séparément la charge ou l’ambiance de travail alléguée, sans en faire une justification automatique du geste.",
    ),
    "REAL-04": (
        "Demander le projet d’avenant écrit, le cycle exact, sa durée et un délai réel de réflexion avant toute signature.",
        "Comparer le cycle proposé au contrat et à l’avenant LABO, notamment pour les week-ends, jours fériés et repos.",
        "Exiger l’étude des effectifs et de la charge du service de jour ainsi que les éléments d’information ou de consultation du CSE.",
        "Faire confirmer par écrit le motif juridique et les conséquences envisagées en cas de refus, sans accepter la formule « accepter ou être licencié » comme une réponse suffisante.",
    ),
    "REAL-05": (
        "Ne pas conclure avant d’identifier le mandat exact, la nature de la réunion et le moment où elle s’est tenue.",
        "Récupérer la convocation, le canal interne invoqué et la conséquence concrète du refus.",
        "Distinguer strictement temps de réunion de l’instance et crédit d’heures de délégation.",
    ),
    "REAL-06": (
        "Ne pas conclure ni appliquer une règle des 10 % tant que son texte, son objet et son mode de calcul ne sont pas identifiés.",
        "Demander un exemple chiffré et le document collectif ou la pratique qui fonde cette règle.",
        "Maintenir le dossier suspendu plutôt que choisir arbitrairement entre congés, rémunération ou autre mécanisme.",
    ),
    "REAL-07": (
        "Identifier l’EPI exactement exigé pour l’opération et la consigne qui imposait son port.",
        "Vérifier la mise à disposition, la taille, la compatibilité avec les lunettes de vue et les signalements antérieurs.",
        "Distinguer un refus injustifié d’un équipement disponible d’une impossibilité liée à un EPI absent ou inadapté.",
    ),
    "REAL-08": (
        "Obtenir par écrit la durée de l’affectation temporaire, le cycle 3x8 et le délai de prévenance.",
        "Comparer le planning proposé au contrat et aux deux organisations locales sans assimiler LABO et 5x8.",
        "Documenter les effets sur les repos, la fatigue, la vie personnelle et les contreparties avant de conseiller un refus ou une négociation.",
    ),
    "REAL-09": (
        "Obtenir la procédure en vigueur à la date de fabrication, son historique de versions et sa preuve de diffusion.",
        "Comparer les instructions réellement accessibles au salarié avec l’opération exécutée et les validations demandées.",
        "Ne pas conclure à une faute technique tant que la procédure applicable reste absente.",
    ),
    "REAL-10": (
        "Récupérer le procès-verbal du contrôle avec l’heure, l’unité, l’appareil et sa traçabilité.",
        "Vérifier la présence d’un tiers et la proposition effective d’une contre-expertise immédiate.",
        "Séparer la sécurité immédiate, la validité du contrôle et la proportionnalité de la sanction.",
    ),
    "REAL-11": (
        "Fixer les mots exacts, les témoins, le contexte et ce que le salarié reconnaît ou conteste.",
        "Documenter les horaires, les repos, la charge et les alertes antérieures sans présenter la fatigue comme une excuse automatique.",
        "Comparer la sanction envisagée aux antécédents et aux précédents réellement comparables.",
    ),
}

PATH_LABELS = {
    "QUESTION_SALARIE": "Question salarié",
    "ASSISTANCE_ENTRETIEN_DISCIPLINAIRE": "Assistance entretien disciplinaire",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _case_short_id(case_id: str) -> str:
    match = re.match(r"^(REAL-\d{2})", case_id)
    if not match:
        raise ValueError("Identifiant de cas V1 invalide.")
    return match.group(1)


def _state_for(short_id: str, result: dict[str, Any]) -> str:
    if short_id in {"REAL-05", "REAL-06"}:
        return "SUSPENDU"
    if short_id == "REAL-09":
        return "LIMITÉ PAR SOURCE ABSENTE"
    if result.get("analysis_suspended"):
        return "SUSPENDU"
    return "ANALYSÉ"


def _test_status_for(state: str) -> str:
    if state == "SUSPENDU":
        return "VALIDÉ — SUSPENSION ATTENDUE"
    if state == "LIMITÉ PAR SOURCE ABSENTE":
        return "VALIDÉ — LIMITE DOCUMENTÉE"
    return "VALIDÉ"


def _validate_public_value(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).lower() in FORBIDDEN_PUBLIC_KEYS:
                raise ValueError(f"Champ public interdit: {path}.{key}")
            _validate_public_value(nested, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, nested in enumerate(value):
            _validate_public_value(nested, f"{path}[{index}]")
        return
    if isinstance(value, str):
        for pattern in SENSITIVE_TEXT_PATTERNS:
            if pattern.search(value):
                raise ValueError(f"Contenu public sensible détecté: {path}")


def _public_summary(raw_case: dict[str, Any]) -> dict[str, Any]:
    source = raw_case.get("response", {}).get("public_summary", {})
    if not isinstance(source, dict):
        raise ValueError("Synthèse publique V1 absente.")
    projected = {
        field: deepcopy(source[field])
        for field in PUBLIC_SUMMARY_FIELDS
        if field in source
    }
    _validate_public_value(projected, "public_summary")
    return projected


def _normalized_sentence(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return re.sub(r"[^\w%]+", " ", text.casefold()).strip()


def _presentation_fragments(value: Any) -> list[str]:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    normalized = _normalized_sentence(text)
    removable_prefixes = (
        "le salarié reconnaît certains éléments mais conteste leur portée",
        "la salariée reconnaît certains éléments mais conteste leur portée",
        "un élément défavorable est reconnu",
    )
    if any(normalized.startswith(prefix) for prefix in removable_prefixes):
        _separator, found, remainder = text.partition(":")
        if found and remainder.strip():
            return [
                item.strip()
                for item in re.split(r"(?<=[.!?])\s+", remainder.strip())
                if item.strip()
            ]
    return [text] if text else []


def _unique_sentences(
    values: Iterable[Any],
    *,
    excluded: Iterable[Any] = (),
    limit: int = 6,
) -> list[str]:
    """Keep concise public sentences without repeating another dossier section."""

    excluded_keys = {
        _normalized_sentence(item)
        for item in excluded
        if _normalized_sentence(item)
    }
    selected: list[str] = []
    selected_keys: list[str] = []
    for value in values:
        for text in _presentation_fragments(value):
            key = _normalized_sentence(text)
            if not key or key in excluded_keys:
                continue
            if key.startswith(
                "la défense peut s appuyer sur les faits encore non établis"
            ):
                continue
            if any(
                key == previous
                or (len(key) > 45 and key in previous)
                or (len(previous) > 45 and previous in key)
                for previous in selected_keys
            ):
                continue
            selected.append(text)
            selected_keys.append(key)
            if len(selected) >= limit:
                return selected
    return selected


def _source_title(source: Mapping[str, Any]) -> str:
    provider = str(source.get("provider") or "").strip()
    title = str(source.get("title") or "").strip()
    if provider and title and provider.casefold() not in title.casefold():
        return f"{provider} — {title}"
    return title or provider


def _semantic_title_tokens(value: Any) -> set[str]:
    ignored = {
        "avec",
        "dans",
        "document",
        "entre",
        "pour",
        "selon",
        "source",
        "titre",
    }
    return {
        token.rstrip("s")
        for token in _normalized_sentence(value).split()
        if len(token) > 3 and token not in ignored
    }


def _comparison_for_source(
    summary: Mapping[str, Any], title: str
) -> Mapping[str, Any] | None:
    title_key = _normalized_sentence(title)
    for item in summary.get("rule_to_facts", ()):
        if not isinstance(item, Mapping):
            continue
        reference = _normalized_sentence(item.get("source"))
        if title_key and title_key in reference:
            return item
    return None


def _relevant_historical_source(
    short_id: str,
    summary: Mapping[str, Any],
    source: Mapping[str, Any],
) -> tuple[bool, str | None]:
    title = str(source.get("title") or "").strip()
    comparison = _comparison_for_source(summary, title)
    if comparison is None:
        return False, "aucune clause ou comparaison traçable n'est associée à cette source"
    return source_topic_relevance(
        CASE_EVENT_CATEGORIES[short_id],
        source_title=title,
        source_reference=(
            source.get("reference") or comparison.get("source") or ""
        ),
        source_excerpt=comparison.get("rule") or "",
    )


def _filter_historical_source_relevance(
    short_id: str, summary: Mapping[str, Any]
) -> dict[str, Any]:
    """Remove obsolete keyword-only matches from every public case projection."""

    output = deepcopy(dict(summary))
    kept: list[dict[str, Any]] = []
    rejected_titles: set[str] = set()
    for raw in output.get("sources", ()):
        if not isinstance(raw, Mapping):
            continue
        source = dict(raw)
        relevant, _reason = _relevant_historical_source(short_id, output, source)
        if relevant:
            kept.append(source)
        else:
            title = _normalized_sentence(source.get("title"))
            if title:
                rejected_titles.add(title)
    output["sources"] = kept

    def mentions_rejected(value: Any) -> bool:
        text = _normalized_sentence(value)
        return any(title in text for title in rejected_titles)

    output["rule_to_facts"] = [
        dict(item)
        for item in output.get("rule_to_facts", ())
        if isinstance(item, Mapping) and not mentions_rejected(item.get("source"))
    ]
    for field in (
        "next_actions",
        "avoid",
        "limits",
        "syndical_position",
        "useful_wording",
    ):
        value = output.get(field)
        if isinstance(value, list):
            output[field] = [item for item in value if not mentions_rejected(item)]
    strategy = output.get("strategy")
    if isinstance(strategy, Mapping):
        filtered_strategy: dict[str, Any] = {}
        for key, value in strategy.items():
            if isinstance(value, list):
                filtered_strategy[str(key)] = [
                    item for item in value if not mentions_rejected(item)
                ]
            else:
                filtered_strategy[str(key)] = value
        output["strategy"] = filtered_strategy
    return output


def _determinant_sources(
    short_id: str,
    summary: Mapping[str, Any],
) -> list[dict[str, str]]:
    selected = [
        dict(item) for item in CASE_SOURCE_PRESENTATION.get(short_id, ())
    ]
    seen = {
        _normalized_sentence(item.get("title"))
        for item in selected
        if item.get("title")
    }
    if selected and short_id not in CASE_KEEP_BASELINE_SOURCES:
        return selected[:5]
    for source in summary.get("sources", ()):
        if not isinstance(source, Mapping):
            continue
        title = _source_title(source)
        if (
            selected
            and short_id in CASE_KEEP_BASELINE_SOURCES
            and not any(
                marker in _normalized_sentence(title)
                for marker in ("legifrance", "légifrance")
            )
        ):
            continue
        key = _normalized_sentence(title)
        if not key or key in seen:
            continue
        seen.add(key)
        comparison = next(
            (
                item
                for item in summary.get("rule_to_facts", ())
                if isinstance(item, Mapping)
                and key in _normalized_sentence(item.get("source"))
            ),
            {},
        )
        rule = str(comparison.get("rule") or "").strip()
        next_action = str(comparison.get("next_action") or "").strip()
        references: list[str] = []
        explicit_reference = str(source.get("reference") or "").strip()
        if explicit_reference:
            references.append(explicit_reference)
        page_match = re.search(r"\b(Page\s+\d+)\b", next_action, re.IGNORECASE)
        article_match = re.search(
            r"\b(Art(?:icle)?\.?\s*[A-Z]?\d+[\w.-]*)\b",
            rule,
            re.IGNORECASE,
        )
        for match in (page_match, article_match):
            if match and match.group(1) not in references:
                references.append(match.group(1))
        selected.append(
            {
                "title": title,
                "nature": str(source.get("nature") or "Nature à confirmer"),
                "status": str(source.get("status") or "DISPONIBLE"),
                "reference": " · ".join(references),
                "excerpt": rule,
                "practical_use": str(source.get("link_to_facts") or "").strip(),
                "reserve": (
                    "Version ou champ d'application à confirmer."
                    if str(comparison.get("confidence") or "").upper() != "HIGH"
                    else ""
                ),
            }
        )
        if len(selected) >= 5:
            break
    return selected


def _documents_still_needed(
    short_id: str,
    summary: Mapping[str, Any],
    sources: Iterable[Mapping[str, Any]],
) -> list[dict[str, str]]:
    source_keys = [
        _normalized_sentence(source.get("title"))
        for source in sources
        if source.get("title")
    ]
    source_tokens = [
        _semantic_title_tokens(source.get("title"))
        for source in sources
        if source.get("title")
    ]
    selected = [
        dict(item) for item in CASE_MISSING_DOCUMENTS.get(short_id, ())
    ]
    seen = {
        _normalized_sentence(item.get("document"))
        for item in selected
        if item.get("document")
    }
    for document in summary.get("documents", ()):
        if not isinstance(document, Mapping):
            continue
        title = str(document.get("document") or "").strip()
        key = _normalized_sentence(title)
        if not key or key in seen:
            continue
        exact_or_contained = any(
            len(key) > 15
            and (key in source_key or source_key in key)
            for source_key in source_keys
        )
        document_tokens = _semantic_title_tokens(title)
        semantically_resolved = any(
            len(document_tokens & tokens) >= 2
            and len(document_tokens & tokens) / max(len(document_tokens), 1) >= 0.5
            for tokens in source_tokens
        )
        if exact_or_contained or semantically_resolved:
            continue
        seen.add(key)
        selected.append(
            {
                "document": title,
                "reason": str(document.get("utility") or "").strip(),
                "priority": str(document.get("priority") or "").strip(),
            }
        )
        if len(selected) >= 5:
            break
    return selected


def _question_answer_exchange(
    summary: Mapping[str, Any],
    *,
    state: str,
) -> list[dict[str, Any]]:
    situation = _unique_sentences(summary.get("situation", ()), limit=3)
    established = _unique_sentences(
        summary.get("strengths", ()),
        excluded=situation,
        limit=4,
    )
    disputed = _unique_sentences(
        [*summary.get("weaknesses", ()), *summary.get("limits", ())],
        excluded=[*situation, *established],
        limit=4,
    )
    rows = [
        {
            "question": "Quelle situation avez-vous prise en charge ?",
            "answers": situation,
            "answer_status": "Éléments relatés dans le dossier",
        },
        {
            "question": "Quels faits avez-vous retenus sans les déformer ?",
            "answers": established,
            "answer_status": "Faits ou points d’appui identifiés",
        },
        {
            "question": "Quels points restaient discutés ou incomplets ?",
            "answers": disputed,
            "answer_status": (
                "Informations indispensables avant de reprendre l’analyse"
                if state == "SUSPENDU"
                else "Points à vérifier avant toute position définitive"
            ),
        },
    ]
    return [row for row in rows if row["answers"]]


def _open_questions(
    summary: Mapping[str, Any],
    *,
    state: str,
) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in summary.get("priority_questions", ()):
        if not isinstance(item, Mapping):
            continue
        question = str(item.get("question") or "").strip()
        key = _normalized_sentence(question)
        if not key or key in seen:
            continue
        seen.add(key)
        target = str(item.get("target") or "DOSSIER").replace("_", " ").title()
        selected.append(
            {
                "question": question,
                "asked_to": target,
                "reason": str(item.get("reason") or "").strip(),
                "answer": (
                    "Réponse indispensable avant de reprendre l’analyse."
                    if state == "SUSPENDU"
                    else "Réponse à obtenir ou à confirmer dans le dossier réel."
                ),
            }
        )
        if len(selected) >= 6:
            break
    return selected


def _union_advice(
    short_id: str,
    summary: Mapping[str, Any],
    *,
    state: str,
) -> list[str]:
    tailored = CASE_UNION_ADVICE.get(short_id)
    if tailored:
        return _unique_sentences(tailored, limit=5)
    strategy = summary.get("strategy") or {}
    candidates: list[Any] = []
    if isinstance(strategy, Mapping):
        candidates.extend(strategy.get("during", ()))
        candidates.extend(strategy.get("position", ()))
    candidates.extend(summary.get("next_actions", ()))
    candidates.extend(summary.get("avoid", ()))
    priority_questions = [
        item.get("question")
        for item in summary.get("priority_questions", ())
        if isinstance(item, Mapping)
    ]
    requested_documents = [
        item.get("document")
        for item in summary.get("documents", ())
        if isinstance(item, Mapping)
    ]
    if state == "SUSPENDU":
        candidates = [
            "Ne pas conclure ni engager le salarié tant que les informations bloquantes ne sont pas obtenues.",
            *candidates,
        ]
    return _unique_sentences(
        candidates,
        excluded=[
            *summary.get("syndical_position", ()),
            *priority_questions,
            *requested_documents,
        ],
        limit=7,
    )


def _union_conclusion(
    short_id: str,
    summary: Mapping[str, Any],
    *,
    state: str,
    notes: Iterable[str],
) -> dict[str, Any]:
    if state == "SUSPENDU":
        headline = "Dossier suspendu : compléter les faits avant de prendre position."
    elif state == "LIMITÉ PAR SOURCE ABSENTE":
        headline = (
            "Position provisoire : obtenir la procédure interne applicable avant de conclure."
        )
    else:
        headline = "Position syndicale préparée, à confronter aux pièces et aux réponses obtenues."
    position = _unique_sentences(summary.get("syndical_position", ()), limit=3)
    exchange_answers = [
        answer
        for row in _question_answer_exchange(summary, state=state)
        for answer in row["answers"]
    ]
    limits = _unique_sentences(
        notes,
        excluded=[*position, *exchange_answers],
        limit=4,
    )
    return {
        "headline": headline,
        "position": position,
        "limits": limits,
        "advice": _union_advice(short_id, summary, state=state),
        "warning": (
            "Conseils de préparation syndicale : ils ne préjugent ni de la décision "
            "de l’employeur, ni de l’issue d’un contentieux."
        ),
    }


def _union_case_file(
    short_id: str,
    summary: Mapping[str, Any],
    *,
    state: str,
    notes: Iterable[str],
) -> dict[str, Any]:
    presentation = CASE_PRESENTATION[short_id]
    sources = _determinant_sources(short_id, summary)
    case_file = {
        "public_reference": f"Dossier {short_id[-2:]}",
        "capacity": presentation["capacity"],
        "question_answer_exchange": _question_answer_exchange(
            summary,
            state=state,
        ),
        "open_questions": _open_questions(summary, state=state),
        "determinant_sources": sources,
        "documents_still_needed": _documents_still_needed(
            short_id,
            summary,
            sources,
        ),
        "conclusion": _union_conclusion(
            short_id,
            summary,
            state=state,
            notes=notes,
        ),
    }
    _validate_public_value(case_file, f"union_case_file.{short_id}")
    return case_file


def _catalog() -> dict[str, Any]:
    results = _load_json(RESULTS_PATH)
    product_version = str(results["product_version"])
    cases: list[dict[str, Any]] = []
    for result in results["cases"]:
        short_id = _case_short_id(str(result["case_id"]))
        presentation = CASE_PRESENTATION[short_id]
        state = _state_for(short_id, result)
        path = str(result["employee_path"])
        item = {
            "id": short_id,
            "title": presentation["title"],
            "domain": presentation["domain"],
            "capacity": presentation["capacity"],
            "categories": list(presentation["categories"]),
            "keywords": list(presentation["keywords"]),
            "employee_path": path,
            "path_label": PATH_LABELS[path],
            "test_status": _test_status_for(state),
            "score": int(result["total_score"]),
            "validated_version": product_version,
            "state": state,
        }
        _validate_public_value(item, f"case.{short_id}")
        cases.append(item)
    return {
        "title": "Onze dossiers syndicaux concrets issus de la validation V1",
        "introduction": (
            "Onze situations concrètes pour comprendre ce que CFDT Nexus apporte "
            "au délégué syndical."
        ),
        "warning": (
            "Ces dossiers sont des exemples anonymisés issus des tests de CFDT Nexus. "
            "Ils ne constituent ni une jurisprudence, ni une garantie de résultat. "
            "Chaque situation réelle doit être analysée à partir de ses propres faits, "
            "documents et sources applicables."
        ),
        "score_average": float(results["score_average_lot3"]),
        "score_explanation": (
            "Le score mesure la qualité de compréhension, des questions, des sources, "
            "de la comparaison règle–faits et de l’utilité pratique. Il ne garantit "
            "pas l’issue réelle d’un dossier."
        ),
        "product_version": product_version,
        "filters": deepcopy(list(FILTERS)),
        "cases": cases,
    }


def list_historical_cases(
    query: str = "", category: str = "all"
) -> dict[str, Any]:
    """Return the public catalog with deterministic optional filtering."""

    catalog = _catalog()
    normalized_query = query.strip().casefold()
    normalized_category = category.strip().casefold() or "all"
    valid_categories = {item["id"] for item in FILTERS}
    if normalized_category not in valid_categories:
        raise ValueError("Filtre historique inconnu.")

    filtered = []
    for item in catalog["cases"]:
        if (
            normalized_category != "all"
            and normalized_category not in item["categories"]
        ):
            continue
        searchable = " ".join(
            [
                item["id"],
                item["title"],
                item["domain"],
                item["path_label"],
                *item["keywords"],
            ]
        ).casefold()
        if normalized_query and normalized_query not in searchable:
            continue
        filtered.append(item)
    catalog["cases"] = filtered
    catalog["result_count"] = len(filtered)
    return catalog


def get_historical_case(case_id: str) -> dict[str, Any]:
    """Return one safe public summary without any technical fixture metadata."""

    short_id = case_id.strip().upper()
    catalog = _catalog()
    metadata = next(
        (item for item in catalog["cases"] if item["id"] == short_id),
        None,
    )
    if metadata is None:
        raise KeyError("Cas historique inconnu.")
    presentation = CASE_PRESENTATION[short_id]
    raw_case = _load_json(RAW_ROOT / str(presentation["fixture"]))
    public_summary = _filter_historical_source_relevance(
        short_id,
        _public_summary(raw_case),
    )
    notes = list(presentation.get("notes", ()))
    detail = {
        **metadata,
        "average_score": catalog["score_average"],
        "score_explanation": catalog["score_explanation"],
        "special_notes": notes,
        "public_summary": public_summary,
        "union_case_file": _union_case_file(
            short_id,
            public_summary,
            state=metadata["state"],
            notes=notes,
        ),
        "source_status_at_test": _source_status_at_test(
            public_summary
        ),
        "usage": (
            "Consultation, démonstration, formation, validation et comparaison "
            "manuelle uniquement."
        ),
        "automatic_reuse": False,
    }
    _validate_public_value(detail, f"detail.{short_id}")
    return detail


def _source_status_at_test(summary: Mapping[str, Any]) -> dict[str, Any]:
    sources = [
        {
            "provider": str(item.get("provider") or ""),
            "title": str(item.get("title") or ""),
            "nature": str(item.get("nature") or ""),
            "status": str(item.get("status") or "DISPONIBLE"),
        }
        for item in summary.get("sources", ())
        if isinstance(item, Mapping)
    ]
    missing = [
        str(item.get("document") or "")
        for item in summary.get("documents", ())
        if isinstance(item, Mapping) and item.get("document")
    ]
    return {
        "retrieved_sources": sources,
        "sources_to_obtain": missing,
        "captured_during_v1_validation": True,
    }


def _source_refresh_input(short_id: str) -> tuple[CaseFactualCore, list[str], list[Any]]:
    presentation = CASE_PRESENTATION[short_id]
    raw = _load_json(SOURCE_BASELINE_ROOT / str(presentation["fixture"]))
    answer = raw.get("response", {}).get("answer", {})
    core_payload = answer.get("case_factual_core")
    if not isinstance(core_payload, dict):
        raise ValueError("Noyau factuel historique absent.")
    plans = answer.get("source_search_plan") or ()
    queries = [
        str(item.get("query") or "")
        for item in plans
        if isinstance(item, Mapping) and item.get("query")
    ]
    preparation = answer.get("actionable_preparation") or {}
    documents = (
        preparation.get("documents_to_request")
        if isinstance(preparation, Mapping)
        else ()
    )
    source_requirements = answer.get("missing_source_requirements") or ()
    return (
        CaseFactualCore(**core_payload),
        queries,
        [*(documents or ()), *source_requirements],
    )


def _default_historical_source_fetcher(queries: Iterable[str]) -> list[dict[str, Any]]:
    """Search only the existing local agreements index; never rerun an analysis."""

    from automation.scripts.assistant_ds_router import normalize_source, search_bible

    sources: list[dict[str, Any]] = []
    for query in dict.fromkeys(item.strip() for item in queries if item.strip()):
        result = search_bible(query, 8)
        for source in result.get("sources_used", ())[:8]:
            if isinstance(source, dict):
                sources.append(normalize_source(source, "bible_accords"))
    return sources


def refresh_historical_case_sources(
    case_id: str,
    *,
    source_fetcher: Callable[[Iterable[str]], list[dict[str, Any]]] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Refresh documentary availability without changing the historical analysis."""

    detail = get_historical_case(case_id)
    short_id = detail["id"]
    core, queries, documents = _source_refresh_input(short_id)
    fetcher = source_fetcher or _default_historical_source_fetcher
    sources = fetcher(tuple(queries))
    report = build_source_extraction_report(core, sources, documents).to_dict()
    at_test = detail["source_status_at_test"]
    former_titles = {
        str(item.get("title") or "").casefold()
        for item in at_test["retrieved_sources"]
        if isinstance(item, Mapping)
    }
    newly_found = [
        item
        for item in report["sources"]
        if str(item.get("title") or "").casefold() not in former_titles
    ]
    absent_statuses = {
        DocumentAvailability.ABSENT.value,
        DocumentAvailability.CONNECTOR_UNAVAILABLE.value,
        DocumentAvailability.NEEDS_CLARIFICATION.value,
        DocumentAvailability.TITLE_ONLY.value,
    }
    still_absent = [
        item
        for item in report["document_resolutions"]
        if item.get("availability_status") in absent_statuses
    ]
    refreshed_at = now or datetime.now(timezone.utc)
    result = {
        "id": short_id,
        "score": detail["score"],
        "state": detail["state"],
        "validated_version": detail["validated_version"],
        "last_refreshed_at": refreshed_at.isoformat(),
        "source_status_at_test": at_test,
        "current_documentary_analysis": report,
        "newly_found": newly_found,
        "still_absent": still_absent,
        "analysis_unchanged": True,
        "score_unchanged": True,
        "automatic_reuse": False,
    }
    _validate_public_value(result, f"refresh.{short_id}")
    return result
