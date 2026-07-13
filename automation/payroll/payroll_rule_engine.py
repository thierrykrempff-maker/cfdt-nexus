#!/usr/bin/env python
"""Select INEOS payroll and leave rules without calculating amounts.

This module is intentionally isolated from the Nexus router. It loads the
PayrollRule catalog, identifies relevant rules, lists required data and stops
before any automatic payroll calculation.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from automation.payroll import payroll_rule_validator as validator


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG_PATH = validator.DEFAULT_CATALOG_PATH
DEFAULT_SCHEMA_PATH = validator.DEFAULT_SCHEMA_PATH

SOURCE_HIERARCHY = [
    "accord_entreprise",
    "convention_collective",
    "code_travail",
    "jurisprudence",
    "pratique_officielle",
    "memoire_entreprise",
]
SOURCE_RANK = {layer: index for index, layer in enumerate(SOURCE_HIERARCHY)}
OPPOSABLE_SOURCE_LAYERS = {"accord_entreprise", "convention_collective", "code_travail"}

INACTIVE_STATUSES = {"expired", "superseded"}
HISTORICAL_LAYERS = {"memoire_entreprise"}
TOPIC_FIELDS = ("payroll_topic", "leave_topic", "work_time_topic")
CONTEXT_ONLY_TOPICS = {"5x8"}
GENERIC_CONFLICT_TOPICS = {
    "jour",
    "5x8",
    "poste_continu",
    "roulement",
    "personnel_jour",
    "personnel_poste",
}
GENERIC_CONSEQUENCES = {
    "",
    "droit_salarie",
    "obligation_employeur",
    "information",
    "controle",
    "avantage",
}
CALCULATION_BLOCKING_STATUSES = {"to_verify", "disputed", "expired", "superseded"}
BLOCKING_WARNING_FRAGMENTS = (
    "a verifier",
    "contestee",
    "non certaine",
    "non confirmee",
    "non opposee",
    "interdit",
)

DISCIPLINARY_ONLY_PATTERNS = [
    "mise a pied",
    "mettre a pied",
    "mis a pied",
    "suspension disciplinaire",
]

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "heures_supplementaires": [
        "heure supplementaire",
        "heures supplementaires",
        "heures sup",
        "heure sup",
        "heures en plus",
        "paiement des heures en plus",
        "overtime",
    ],
    "nuit": ["travail de nuit", "heures de nuit", "nuit", "nuits"],
    "dimanche": ["dimanche", "travail du dimanche"],
    "jour_ferie": ["jour ferie", "jour rouge", "ferie"],
    "5x8": ["5x8", "5 x 8", "poste continu", "personnel poste", "postes"],
    "rappel": ["rappel", "rappeler pendant conge", "rappel au travail"],
    "maintien": ["maintien", "maintenu au poste", "reste au travail"],
    "astreinte": ["astreinte", "astreintes"],
    "intervention": ["intervention", "intervenir", "sortie d astreinte"],
    "changement_roulement": [
        "changement de roulement",
        "changement roulement",
        "changer de roulement",
        "prevenance",
    ],
    "conges_payes": ["conge", "conges", "conge paye", "conges payes", "conge refuse", "conges refuse", "cp"],
    "prise_cp": ["conge refuse", "demande de conge", "pose de conge", "date de conge"],
    "fractionnement": ["fractionnement", "jours de fractionnement"],
    "rtt": ["rtt", "recuperation temps travail"],
    "cet": ["cet", "compte epargne temps"],
    "maladie": ["maladie", "arret maladie", "arret de travail", "maintien de salaire"],
    "absence_maladie": ["arret maladie", "arret de travail"],
    "treizieme_mois": ["13e mois", "treizieme mois", "13eme mois", "prime de treizieme"],
    "indemnite_kilometrique": [
        "indemnite kilometrique",
        "indemnites kilometriques",
        "kilometrique",
        "kilometres",
        "frais kilometriques",
        "trajet domicile usine",
        "deplacement domicile travail",
        "km",
        "distance",
    ],
    "rctp": ["rctp"],
    "rctr": ["rctr"],
    "rjfj": ["rjfj"],
    "rjfn": ["rjfn"],
    "jr": ["jours de remonte", "jour de remonte", "jr"],
    "recuperation_jour_ferie": [
        "recuperation jour ferie",
        "recup jour ferie",
        "recuperation ferie",
        "rjfj",
        "rjfn",
    ],
    "classification": ["classification", "coefficient", "changer mon coefficient"],
    "coefficient": ["coefficient", "changer mon coefficient"],
    "repos_compensateur": ["repos compensateur", "compensateur heures supplementaires"],
    "repos": ["repos quotidien", "repos entre deux postes", "repos entre deux journees"],
}

CONTEXT_TOPIC_KEYS = {
    "work_schedule",
    "regime_travail",
    "schedule",
    "employee_population",
    "population_salarie",
    "population",
    "employment_category",
    "categorie",
}

POPULATION_ALIASES: dict[str, set[str]] = {
    "tous": {"tous", "tout le monde"},
    "personnel_jour": {"personnel_jour", "personnel de jour", "jour", "salarie de jour"},
    "personnel_poste": {"personnel_poste", "personnel poste", "personnel poste", "poste", "postes", "postee", "poste"},
    "poste_continu": {"poste_continu", "poste continu", "continu", "5x8"},
    "ouvriers": {"ouvrier", "ouvriers"},
    "employes": {"employe", "employes"},
    "agents_maitrise": {"agent de maitrise", "agents de maitrise", "maitrise"},
    "cadres": {"cadre", "cadres"},
    "non_cadres": {"non cadre", "non cadres", "non_cadres"},
    "gn": {"gn"},
    "polyolefines": {"polyolefines", "polyolefine"},
}

EMPLOYMENT_CATEGORY_ALIASES: dict[str, set[str]] = {
    "tous": {"tous"},
    "ouvriers": {"ouvrier", "ouvriers"},
    "employes": {"employe", "employes"},
    "agents_maitrise": {"agent de maitrise", "agents de maitrise", "maitrise"},
    "cadres": {"cadre", "cadres"},
    "non_cadres": {"non cadre", "non cadres", "non_cadres", "non cadres"},
}

SCHEDULE_ALIASES: dict[str, set[str]] = {
    "tous": {"tous"},
    "jour": {"jour", "personnel de jour", "journee"},
    "5x8": {"5x8", "5 x 8"},
    "poste_continu": {"poste continu", "poste_continu", "continu"},
    "gn": {"gn"},
    "polyolefines": {"polyolefines", "polyolefine"},
    "roulement": {"roulement", "couleur"},
}

VARIABLE_ALIASES: dict[str, list[str]] = {
    "heures_validees": ["overtime_hours", "hours_worked", "heures_en_plus", "heures_travaillees"],
    "base_horaire": ["hourly_rate", "taux_horaire", "salaire_horaire"],
    "coefficient": ["coefficient", "classification_coefficient"],
    "heures_travaillees": ["hours_worked", "holiday_hours", "heures_jour_ferie"],
    "date_information": ["notice_date", "date_prevenance"],
    "date_changement": ["change_date", "date_changement"],
    "nombre_postes_remplaces": ["postes_remplaces", "nombre_postes", "replaced_shifts"],
    "date_premier_repos": ["date_premier_repos", "first_rest_date"],
    "date_demande": ["request_date", "date_demande"],
    "date_debut_conge": ["leave_start_date", "date_debut_conge"],
    "population_salarie": ["employee_population", "population"],
    "compteur_RJFJ_avant": ["compteur_RJFJ", "solde_RJFJ", "rjfj_counter"],
    "compteur_JR_avant": ["compteur_JR", "solde_JR", "jr_counter"],
    "solde_JR": ["compteur_JR", "jr_counter"],
    "solde_RJFJ": ["compteur_RJFJ", "rjfj_counter"],
    "solde_RJFN": ["compteur_RJFN", "rjfn_counter"],
    "compteur_RCTP": ["rctp_counter", "compteur_rctp"],
    "compteur_RCTR": ["rctr_counter", "compteur_rctr"],
    "anciennete": ["seniority", "anciennete"],
    "date_debut_arret": ["absence_start", "date_debut_arret", "date_debut_maladie"],
    "duree_arret": ["absence_duration", "duree_arret"],
    "salaire_reference": ["reference_salary", "salaire_reference", "appointements_bruts_novembre"],
    "distance_km": ["round_trip_km", "distance_km", "distance_aller_retour"],
    "nombre_trajets": ["nombre_trajets", "jours_travailles", "worked_days"],
    "valeur_applicable": ["taux_applicable", "valeur_applicable", "applicable_rate"],
    "presence": ["presence", "present_toute_annee"],
    "mois_paiement": ["mois_paiement", "payment_month"],
    "montant_deja_verse": ["montant_deja_verse", "already_paid"],
    "planning_astreinte": ["planning_astreinte", "on_call_schedule"],
    "heure_appel": ["callback_time", "heure_appel"],
    "heure_debut_intervention": ["intervention_start", "heure_debut_intervention"],
    "heure_fin_intervention": ["intervention_end", "heure_fin_intervention"],
    "temps_deplacement": ["travel_time", "temps_deplacement"],
}

DOCUMENT_ALIASES: dict[str, set[str]] = {
    "planning": {"planning", "planning fourni", "planification"},
    "releve_kelio": {"kelio", "releve kelio", "compteur kelio", "capture kelio"},
    "bulletin_de_paie": {"bulletin", "bulletin de paie", "fiche de paie", "payslip"},
    "contrat": {"contrat", "contrat de travail"},
    "arret_de_travail": {"arret de travail", "arret maladie", "certificat maladie"},
    "demande_conge": {"demande de conge", "formulaire conge"},
    "reponse_hierarchie": {"reponse hierarchie", "refus conge", "validation hierarchie"},
    "justificatifs_frais": {"justificatifs frais", "factures", "notes de frais"},
    "adresse_declaree": {"adresse declaree", "adresse domicile"},
}

DOCUMENTS_BY_VARIABLE: dict[str, list[str]] = {
    "heures_validees": ["planning", "releve_kelio"],
    "seuil_declenchement": ["planning", "accord_applicable"],
    "semaine_ou_cycle": ["planning", "releve_kelio"],
    "base_horaire": ["bulletin_de_paie"],
    "repos_compensateur": ["releve_kelio"],
    "night_hours": ["planning", "releve_kelio"],
    "sunday_hours": ["planning", "releve_kelio"],
    "date_jour_ferie": ["planning"],
    "heures_travaillees": ["planning", "releve_kelio"],
    "poste_planifie": ["planning"],
    "roulement_theorique": ["planning"],
    "compteurs_jour_ferie": ["releve_kelio"],
    "compteur_RJFJ_avant": ["releve_kelio"],
    "compteur_JR_avant": ["releve_kelio"],
    "compteur_RCTP": ["releve_kelio"],
    "compteur_RCTR": ["releve_kelio"],
    "solde_JR": ["releve_kelio"],
    "solde_RJFJ": ["releve_kelio"],
    "solde_RJFN": ["releve_kelio"],
    "date_information": ["planning"],
    "date_changement": ["planning"],
    "nombre_postes_remplaces": ["planning"],
    "date_premier_repos": ["planning"],
    "date_demande": ["demande_conge"],
    "date_debut_conge": ["demande_conge"],
    "population_salarie": ["bulletin_de_paie", "contrat"],
    "date_rappel": ["planning", "reponse_hierarchie"],
    "periode_conge": ["demande_conge"],
    "frais_engages": ["justificatifs_frais"],
    "justificatifs_frais": ["justificatifs_frais"],
    "anciennete": ["bulletin_de_paie", "contrat"],
    "date_debut_arret": ["arret_de_travail"],
    "duree_arret": ["arret_de_travail"],
    "ijss": ["bulletin_de_paie"],
    "complement_prevoyance": ["bulletin_de_paie"],
    "salaire_reference": ["bulletin_de_paie"],
    "presence": ["bulletin_de_paie"],
    "mois_paiement": ["bulletin_de_paie"],
    "montant_deja_verse": ["bulletin_de_paie"],
    "distance_km": ["adresse_declaree"],
    "nombre_trajets": ["planning"],
    "periode": ["planning", "bulletin_de_paie"],
    "type_rappel": ["bulletin_de_paie"],
    "valeur_applicable": ["bulletin_de_paie", "accord_applicable"],
    "adresse_depart": ["adresse_declaree"],
    "adresse_arrivee": ["adresse_declaree"],
    "distance_plus_courte": ["adresse_declaree"],
    "planning_astreinte": ["planning"],
    "heure_appel": ["planning", "releve_kelio"],
    "heure_debut_intervention": ["planning", "releve_kelio"],
    "heure_fin_intervention": ["planning", "releve_kelio"],
    "temps_deplacement": ["planning", "releve_kelio"],
}


@dataclass
class RuleEvaluation:
    rule: dict[str, Any]
    score: int = 0
    matched_topics: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    rejected: bool = False
    reject_reason: str | None = None
    reject_details: list[str] = field(default_factory=list)


def normalize_text(value: Any) -> str:
    """Return a lowercase ASCII-ish representation for deterministic matching."""
    if value is None:
        return ""
    if isinstance(value, dict):
        value = " ".join(normalize_text(item) for item in value.values())
    elif isinstance(value, (list, tuple, set)):
        value = " ".join(normalize_text(item) for item in value)
    text = str(value).lower().replace("'", " ").replace("’", " ")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_reference_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def load_validated_catalog(
    catalog_path: Path | str = DEFAULT_CATALOG_PATH,
    schema_path: Path | str = DEFAULT_SCHEMA_PATH,
) -> dict[str, Any]:
    """Load and validate the PayrollRule catalog.

    The returned structure is a deep copy so downstream selection cannot mutate
    the catalog loaded from disk.
    """
    schema = validator.load_schema(Path(schema_path))
    catalog = validator.load_catalog(Path(catalog_path))
    report = validator.validate_catalog(catalog, schema=schema)
    if not report["valid"]:
        raise ValueError(f"Invalid payroll catalog: {json.dumps(report, ensure_ascii=False)}")
    if not catalog.get("rules"):
        raise ValueError("Invalid payroll catalog: no rules available")
    return copy.deepcopy(catalog)


def get_rule_by_id(rules: list[dict[str, Any]], rule_id: str) -> dict[str, Any]:
    for rule in rules:
        if rule.get("rule_id") == rule_id:
            return copy.deepcopy(rule)
    raise KeyError(f"Unknown payroll rule_id: {rule_id}")


def context_text(context: dict[str, Any]) -> str:
    selected = {key: context.get(key) for key in CONTEXT_TOPIC_KEYS if key in context}
    return normalize_text(selected)


def is_disciplinary_only(text: str) -> bool:
    if not any(pattern in text for pattern in DISCIPLINARY_ONLY_PATTERNS):
        return False
    return not any(
        keyword in text
        for topic, keywords in TOPIC_KEYWORDS.items()
        if topic not in {"classification", "coefficient"}
        for keyword in keywords
    )


def classify_query(question: str, context: dict[str, Any] | None = None) -> list[str]:
    """Identify payroll, leave and working-time topics from text and context."""
    context = context or {}
    text = normalize_text(f"{question} {context_text(context)}")
    if is_disciplinary_only(text):
        return []

    topics: list[str] = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if topic == "changement_roulement":
            if any(keyword in text for keyword in keywords):
                topics.append(topic)
            elif "changement de couleur" in text or "changer de couleur" in text or "couleur" in text:
                if "5x8" in text or "poste" in text or normalize_text(context.get("work_schedule")) == "5x8":
                    topics.append(topic)
            continue
        if any(keyword in text for keyword in keywords):
            topics.append(topic)

    if "changement de couleur" in text or "changer de couleur" in text:
        if ("5x8" in text or "poste" in text) and "changement_roulement" not in topics:
            topics.append("changement_roulement")
    if "rjfj" in topics or "rjfn" in topics or "jr" in topics:
        for extra in ("recuperation_jour_ferie", "5x8"):
            if extra not in topics:
                topics.append(extra)
    if "rctp" in topics or "rctr" in topics:
        if "5x8" not in topics:
            topics.append("5x8")
    return topics


def flatten_values(values: Any) -> list[Any]:
    if values is None:
        return []
    if isinstance(values, (list, tuple, set)):
        flattened: list[Any] = []
        for item in values:
            flattened.extend(flatten_values(item))
        return flattened
    return [values]


def normalize_alias_values(values: Any, aliases: dict[str, set[str]]) -> set[str]:
    raw_values: set[str] = set()
    if values is None:
        return raw_values
    items = flatten_values(values)
    normalized_items = {normalize_text(item) for item in items if normalize_text(item)}
    for canonical, labels in aliases.items():
        normalized_labels = {normalize_text(label) for label in labels}
        if canonical in normalized_items or normalized_items & normalized_labels:
            raw_values.add(canonical)
    return raw_values


def is_specific(values: set[str]) -> bool:
    return bool(values) and "tous" not in values


def has_conflicting_values(values: set[str]) -> bool:
    values_without_all = {value for value in values if value != "tous"}
    return len(values_without_all) > 1


def context_population(context: dict[str, Any]) -> set[str]:
    values: list[Any] = []
    for key in ("employee_population", "population_salarie", "population"):
        if key in context:
            values.append(context[key])
    text = normalize_text(context)
    values.append(text)
    populations = normalize_alias_values(values, POPULATION_ALIASES)
    if "5x8" in text or "poste continu" in text:
        populations.add("personnel_poste")
    return populations


def context_employment_category(context: dict[str, Any]) -> set[str]:
    values: list[Any] = []
    for key in ("employment_category", "categorie", "category"):
        if key in context:
            values.append(context[key])
    return normalize_alias_values(values, EMPLOYMENT_CATEGORY_ALIASES)


def context_schedule(context: dict[str, Any]) -> set[str]:
    values: list[Any] = []
    for key in ("work_schedule", "regime_travail", "schedule"):
        if key in context:
            values.append(context[key])
    text = normalize_text(context)
    values.append(text)
    return normalize_alias_values(values, SCHEDULE_ALIASES)


def context_ambiguities(context: dict[str, Any]) -> list[dict[str, Any]]:
    ambiguities: list[dict[str, Any]] = []
    schedules = context_schedule(context)
    populations = context_population(context)
    categories = context_employment_category(context)
    if has_conflicting_values(schedules):
        ambiguities.append({"variable": "work_schedule", "reason": "conflicting_context_values", "value": sorted(schedules)})
    if has_conflicting_values(populations):
        ambiguities.append(
            {"variable": "employee_population", "reason": "conflicting_context_values", "value": sorted(populations)}
        )
    if has_conflicting_values(categories):
        ambiguities.append(
            {"variable": "employment_category", "reason": "conflicting_context_values", "value": sorted(categories)}
        )
    documents_present = detect_present_documents(context)
    data = selected_data_sources(context)
    has_kelio_document = "releve_kelio" in documents_present
    has_kelio_value = any("kelio" in normalize_text(key) for key in data)
    has_kelio_date = any(key in data and data[key] not in (None, "", []) for key in ("kelio_date", "date_releve_kelio"))
    if (has_kelio_document or has_kelio_value) and not has_kelio_date:
        ambiguities.append({"variable": "releve_kelio_date", "reason": "missing_kelio_statement_date", "value": None})
    return ambiguities


def context_reference_date(context: dict[str, Any]) -> date | None:
    for key in ("reference_date", "event_date", "date", "payroll_date"):
        parsed = parse_reference_date(context.get(key))
        if parsed:
            return parsed
    return None


def rule_topics(rule: dict[str, Any]) -> set[str]:
    topics: set[str] = set()
    for field_name in TOPIC_FIELDS:
        values = rule.get(field_name)
        if isinstance(values, list):
            topics.update(str(item) for item in values)
    return topics


def rule_haystack(rule: dict[str, Any]) -> str:
    return normalize_text(
        [
            rule.get("rule_id"),
            rule.get("title"),
            rule.get("description"),
            rule.get("required_variables"),
            rule.get("conditions"),
            rule.get("notes"),
        ]
    )


def rule_identity_haystack(rule: dict[str, Any]) -> str:
    return normalize_text([rule.get("rule_id"), rule.get("title")])


def topic_matches_rule_text(topic: str, rule: dict[str, Any]) -> bool:
    haystack = rule_haystack(rule)
    if topic in {"rctp", "rctr", "rjfj", "rjfn", "jr"}:
        identity = f" {rule_identity_haystack(rule)} "
        return f" {topic} " in identity or f"_{topic}_" in identity
    if topic in haystack:
        return True
    if topic == "treizieme_mois" and "13e mois" in haystack:
        return True
    if topic == "changement_roulement":
        return "changement" in haystack and "roulement" in haystack
    if topic == "indemnite_kilometrique":
        return "kilometrique" in haystack or "distance" in haystack
    return False


def is_counter_recovery_rule(rule: dict[str, Any]) -> bool:
    haystack = rule_identity_haystack(rule)
    return any(marker in haystack for marker in ("rjfj", "rjfn", " jr ", "regularisation", "prelevement"))


def score_rule_for_topics(rule: dict[str, Any], topics: list[str]) -> tuple[int, list[str]]:
    values = rule_topics(rule)
    matched: list[str] = []
    matched_primary = False
    score = 0
    has_specific_counter_topic = bool({"rjfj", "rjfn", "jr"} & set(topics))
    for topic in topics:
        if topic == "recuperation_jour_ferie" and has_specific_counter_topic and not is_counter_recovery_rule(rule):
            continue
        if topic in values:
            score += 30
            matched.append(topic)
            if topic not in CONTEXT_ONLY_TOPICS:
                matched_primary = True
        elif topic_matches_rule_text(topic, rule):
            score += 18
            matched.append(topic)
            if topic not in CONTEXT_ONLY_TOPICS:
                matched_primary = True
        elif topic == "5x8" and {"5x8", "poste_continu", "roulement"} & values:
            score += 12
            matched.append(topic)
        elif topic == "conges_payes" and rule.get("leave_topic"):
            score += 8
            matched.append(topic)
            matched_primary = True
    if matched and not matched_primary:
        return 0, []
    if matched:
        score += max(0, 5 - SOURCE_RANK.get(str(rule.get("source_layer")), 5))
        if rule.get("confidence") == "high":
            score += 3
        elif rule.get("confidence") == "medium":
            score += 1
        elif rule.get("confidence") == "low":
            score -= 1
    return score, list(dict.fromkeys(matched))


def population_compatible(rule: dict[str, Any], context_values: set[str]) -> bool:
    rule_values = set(rule.get("employee_population") or [])
    if not context_values or not rule_values or "tous" in rule_values:
        return True
    return bool(rule_values & context_values)


def schedule_compatible(rule: dict[str, Any], context_values: set[str]) -> bool:
    rule_values = set(rule.get("work_schedule") or [])
    if not context_values or not rule_values or "tous" in rule_values:
        return True
    return bool(rule_values & context_values)


def employment_category_compatible(rule: dict[str, Any], context_values: set[str]) -> bool:
    rule_values = set(rule.get("employment_category") or [])
    if not context_values or not rule_values or "tous" in rule_values:
        return True
    return bool(rule_values & context_values)


def site_compatible(rule: dict[str, Any], context: dict[str, Any]) -> bool:
    context_site = normalize_text(context.get("site"))
    if not context_site:
        return True
    rule_site = normalize_text(rule.get("site"))
    return not rule_site or rule_site in {"tous", context_site} or context_site in rule_site or rule_site in context_site


def date_compatible(rule: dict[str, Any], reference_date: date | None) -> bool:
    return rule_date_issue(rule, reference_date) is None


def rule_date_issue(rule: dict[str, Any], reference_date: date | None) -> str | None:
    if not reference_date:
        return None
    effective = parse_reference_date(rule.get("effective_date"))
    end = parse_reference_date(rule.get("end_date"))
    if effective and reference_date < effective:
        return "rule_not_yet_effective"
    if end and reference_date > end:
        return "date_out_of_period"
    return None


def evaluate_rule(
    rule: dict[str, Any],
    topics: list[str],
    context: dict[str, Any],
    reference_date: date | None = None,
) -> RuleEvaluation | None:
    score, matched_topics = score_rule_for_topics(rule, topics)
    if score <= 0:
        return None

    evaluation = RuleEvaluation(rule=rule, score=score, matched_topics=matched_topics)
    source_layer = str(rule.get("source_layer"))
    status = str(rule.get("status"))

    if source_layer in HISTORICAL_LAYERS or rule.get("historical_only") is True:
        evaluation.rejected = True
        evaluation.reject_reason = "historical_or_memory_source"
        evaluation.reject_details.append("Une memoire entreprise ne peut pas devenir une regle applicable.")
        return evaluation
    if status in INACTIVE_STATUSES:
        evaluation.rejected = True
        evaluation.reject_reason = f"status_{status}"
        evaluation.reject_details.append("La regle est expiree ou remplacee.")
        return evaluation
    if not population_compatible(rule, context_population(context)):
        evaluation.rejected = True
        evaluation.reject_reason = "population_incompatible"
        evaluation.reject_details.append("La population du contexte ne correspond pas a la regle.")
        return evaluation
    if not schedule_compatible(rule, context_schedule(context)):
        evaluation.rejected = True
        evaluation.reject_reason = "work_schedule_incompatible"
        evaluation.reject_details.append("Le regime de travail du contexte ne correspond pas a la regle.")
        return evaluation
    if not employment_category_compatible(rule, context_employment_category(context)):
        evaluation.rejected = True
        evaluation.reject_reason = "employment_category_incompatible"
        evaluation.reject_details.append("La categorie d'emploi du contexte ne correspond pas a la regle.")
        return evaluation
    if not site_compatible(rule, context):
        evaluation.rejected = True
        evaluation.reject_reason = "site_incompatible"
        evaluation.reject_details.append("Le site du contexte ne correspond pas a la regle.")
        return evaluation
    date_issue = rule_date_issue(rule, reference_date)
    if date_issue:
        evaluation.rejected = True
        evaluation.reject_reason = date_issue
        if date_issue == "rule_not_yet_effective":
            evaluation.reject_details.append("rule_not_yet_effective: la regle n'est pas encore applicable.")
        else:
            evaluation.reject_details.append("La date de reference est hors periode d'application.")
        return evaluation

    if status == "to_verify":
        evaluation.warnings.append("Regle a verifier humainement avant utilisation.")
    if status == "disputed":
        evaluation.warnings.append("Regle contestee: prudence renforcee.")
    if rule.get("confidence") == "low":
        evaluation.warnings.append("Confiance documentaire faible.")
    if is_specific(set(rule.get("employee_population") or [])) and not context_population(context):
        evaluation.warnings.append("Population non confirmee dans le contexte.")
    if is_specific(set(rule.get("employment_category") or [])) and not context_employment_category(context):
        evaluation.warnings.append("Categorie d'emploi non confirmee dans le contexte.")
    if rule.get("legal_priority") != "opposable":
        evaluation.warnings.append("Priorite juridique non opposee pour un calcul automatique.")
    if not rule.get("effective_date"):
        evaluation.warnings.append("Date d'effet non certaine.")
    if rule.get("calculation_allowed") is not True:
        evaluation.warnings.append("Calcul automatique interdit pour cette regle.")
    return evaluation


def summarize_rule(evaluation: RuleEvaluation) -> dict[str, Any]:
    rule = evaluation.rule
    return {
        "rule_id": rule.get("rule_id"),
        "title": rule.get("title"),
        "source_layer": rule.get("source_layer"),
        "source_document": rule.get("source_document"),
        "source_page": rule.get("source_page"),
        "status": rule.get("status"),
        "confidence": rule.get("confidence"),
        "population": rule.get("employee_population"),
        "work_schedule": rule.get("work_schedule"),
        "required_variables": list(rule.get("required_variables") or []),
        "matched_topics": evaluation.matched_topics,
        "score": evaluation.score,
        "warnings": evaluation.warnings,
    }


def summarize_rejection(evaluation: RuleEvaluation) -> dict[str, Any]:
    rule = evaluation.rule
    return {
        "rule_id": rule.get("rule_id"),
        "title": rule.get("title"),
        "matched_topics": evaluation.matched_topics,
        "reason": evaluation.reject_reason,
        "details": evaluation.reject_details,
    }


def selected_data_sources(context: dict[str, Any]) -> dict[str, Any]:
    variables = context.get("variables") if isinstance(context.get("variables"), dict) else {}
    merged = dict(variables)
    for key, value in context.items():
        if key not in {"variables", "documents", "pieces", "evidence"}:
            merged.setdefault(key, value)
    return merged


def is_missing_context_value(value: Any) -> bool:
    return value is None or value == "" or value == []


def comparable_value(value: Any) -> str:
    if isinstance(value, dict):
        value = {key: item for key, item in value.items() if key not in {"source", "label"}}
    return normalize_text(value)


def has_ambiguity_marker(value: Any) -> bool:
    raw = str(value or "").lower()
    normalized = normalize_text(value)
    return (
        "?" in raw
        or "environ" in normalized
        or "peut etre" in normalized
        or "peut-etre" in raw
        or "je crois" in normalized
        or "a confirmer" in normalized
        or "non confirme" in normalized
        or "incertain" in normalized
        or "unknown" in normalized
    )


def find_context_value(variable: str, context: dict[str, Any]) -> tuple[bool, Any, str | None]:
    data = selected_data_sources(context)
    keys = [variable] + VARIABLE_ALIASES.get(variable, [])
    found_values: list[tuple[str, Any]] = []
    for key in keys:
        if key in data and not is_missing_context_value(data[key]):
            found_values.append((key, data[key]))
    if not found_values:
        return False, None, None
    comparable_values = {comparable_value(value) for _, value in found_values}
    if len(comparable_values) > 1:
        return True, {"ambiguous": True, "reason": "conflicting_alias_values", "values": found_values}, "multiple_aliases"
    return True, found_values[0][1], found_values[0][0]


def is_ambiguous_value(value: Any) -> bool:
    if isinstance(value, dict):
        if value.get("ambiguous") is True or value.get("confirmed") is False:
            return True
        if normalize_text(value.get("status")) in {"a verifier", "to verify", "non confirme", "uncertain"}:
            return True
    return has_ambiguity_marker(value)


def detect_present_documents(context: dict[str, Any]) -> list[str]:
    raw_documents: list[Any] = []
    for key in ("documents", "pieces", "evidence"):
        value = context.get(key)
        if isinstance(value, dict):
            raw_documents.extend(key for key, present in value.items() if present)
            raw_documents.extend(value.values())
        elif isinstance(value, list):
            raw_documents.extend(value)
        elif value:
            raw_documents.append(value)
    for key, document_name in [
        ("payslip_available", "bulletin_de_paie"),
        ("bulletin_disponible", "bulletin_de_paie"),
        ("planning_available", "planning"),
        ("planning_fourni", "planning"),
        ("kelio_available", "releve_kelio"),
        ("compteur_kelio_disponible", "releve_kelio"),
    ]:
        if context.get(key):
            raw_documents.append(document_name)

    present: set[str] = set()
    normalized = {normalize_text(item) for item in raw_documents}
    for canonical, aliases in DOCUMENT_ALIASES.items():
        normalized_aliases = {normalize_text(alias) for alias in aliases}
        if canonical in normalized or normalized & normalized_aliases:
            present.add(canonical)
    return sorted(present)


def documents_needed_for(variable: str) -> list[str]:
    return DOCUMENTS_BY_VARIABLE.get(variable, ["piece_justificative_a_preciser"])


def rule_scope_topics(rule: dict[str, Any]) -> set[str]:
    topics: set[str] = set()
    for field_name in ("payroll_topic", "leave_topic"):
        for topic in rule.get(field_name) or []:
            normalized = str(topic)
            if normalized not in GENERIC_CONFLICT_TOPICS:
                topics.add(normalized)
    return topics


def rule_context_topics(rule: dict[str, Any]) -> set[str]:
    return {str(topic) for topic in rule.get("work_time_topic") or []}


def rule_values_overlap(first: set[str], second: set[str]) -> bool:
    if not first or not second or "tous" in first or "tous" in second:
        return True
    return bool(first & second)


def rule_periods_overlap(first: dict[str, Any], second: dict[str, Any]) -> bool:
    first_start = parse_reference_date(first.get("effective_date")) or date.min
    second_start = parse_reference_date(second.get("effective_date")) or date.min
    first_end = parse_reference_date(first.get("end_date")) or date.max
    second_end = parse_reference_date(second.get("end_date")) or date.max
    return first_start <= second_end and second_start <= first_end


def normalized_consequence(rule: dict[str, Any]) -> str:
    return normalize_text(rule.get("benefit_or_obligation"))


def formula_signature(rule: dict[str, Any]) -> str:
    formula = rule.get("calculation_formula") or {}
    return normalize_text(
        {
            "expression": formula.get("expression"),
            "sourced_values": formula.get("sourced_values"),
            "payroll_lines_to_check": rule.get("payroll_lines_to_check"),
        }
    )


def rules_have_incompatible_effect(first: dict[str, Any], second: dict[str, Any]) -> bool:
    first_consequence = normalized_consequence(first)
    second_consequence = normalized_consequence(second)
    if first_consequence != second_consequence:
        return False
    if first_consequence not in GENERIC_CONSEQUENCES:
        return True

    first_formula = formula_signature(first)
    second_formula = formula_signature(second)
    return bool(first_formula and second_formula and first_formula != second_formula)


def detect_rule_conflicts(selected_rules: list[dict[str, Any]]) -> dict[str, Any]:
    """Detect only structured conflicts between selected rules.

    Multiple rules are allowed when their business topic, scope or consequence differs.
    Work-time topics such as "jour" or "5x8" are context only here: they can
    confirm scope overlap, but never create a conflict on their own.
    """
    conflicts: list[tuple[str, str]] = []
    reasons: list[str] = []
    for index, first in enumerate(selected_rules):
        first_id = str(first.get("rule_id", "unknown_rule"))
        first_topics = rule_scope_topics(first)
        first_context_topics = rule_context_topics(first)
        for second in selected_rules[index + 1 :]:
            second_id = str(second.get("rule_id", "unknown_rule"))
            shared_topics = first_topics & rule_scope_topics(second)
            if not shared_topics:
                continue
            if not rule_values_overlap(set(first.get("employee_population") or []), set(second.get("employee_population") or [])):
                continue
            if not rule_values_overlap(set(first.get("employment_category") or []), set(second.get("employment_category") or [])):
                continue
            if not rule_values_overlap(set(first.get("work_schedule") or []), set(second.get("work_schedule") or [])):
                continue
            if not rule_periods_overlap(first, second):
                continue
            if not rules_have_incompatible_effect(first, second):
                continue
            conflicts.append((first_id, second_id))
            shared_context = first_context_topics & rule_context_topics(second)
            context_note = f", contexte {sorted(shared_context)[0]}" if shared_context else ""
            reasons.append(
                f"{first_id} / {second_id}: meme theme metier {sorted(shared_topics)[0]}{context_note} et effet incompatible"
            )

    conflicting_rule_ids = sorted({rule_id for pair in conflicts for rule_id in pair})
    return {
        "has_conflict": bool(conflicts),
        "conflicting_rule_ids": conflicting_rule_ids,
        "reason": "; ".join(reasons),
    }


def is_safe_for_calculation(rule: dict[str, Any], selection_context: dict[str, Any]) -> bool:
    """Return True only when a future calculation would be technically safe.

    This does not calculate anything. It only keeps the safety gate explicit.
    """
    if rule.get("calculation_allowed") is not True:
        return False
    if rule.get("status") in CALCULATION_BLOCKING_STATUSES:
        return False
    source_layer = str(rule.get("source_layer", ""))
    if source_layer not in OPPOSABLE_SOURCE_LAYERS:
        return False
    if rule.get("legal_priority") != "opposable":
        return False
    effective_date = parse_reference_date(rule.get("effective_date"))
    if not effective_date:
        return False
    end_date = parse_reference_date(rule.get("end_date"))
    reference_date = selection_context.get("reference_date") or date.today()
    if reference_date < effective_date:
        return False
    if end_date and reference_date > end_date:
        return False
    required_variables = set(rule.get("required_variables") or [])
    if required_variables & set(selection_context.get("missing_variables", set())):
        return False
    if required_variables & set(selection_context.get("ambiguous_variables", set())):
        return False
    if selection_context.get("context_has_ambiguities"):
        return False
    if selection_context.get("rule_conflict", {}).get("has_conflict"):
        return False
    warnings = selection_context.get("warnings_by_rule_id", {}).get(rule.get("rule_id"), [])
    warning_text = normalize_text(warnings)
    if any(fragment in warning_text for fragment in BLOCKING_WARNING_FRAGMENTS):
        return False
    rule_populations = set(rule.get("employee_population") or [])
    rule_categories = set(rule.get("employment_category") or [])
    if is_specific(rule_populations) and not selection_context.get("context_population_values"):
        return False
    if is_specific(rule_categories) and not selection_context.get("context_category_values"):
        return False
    return True


def collect_variables(selected_items: list[Any], context: dict[str, Any], reference_date: date | None = None) -> dict[str, Any]:
    selected_evaluations = [item for item in selected_items if isinstance(item, RuleEvaluation)]
    selected_rules = [item.rule for item in selected_evaluations] if selected_evaluations else selected_items
    required: list[str] = []
    for rule in selected_rules:
        for variable in rule.get("required_variables") or []:
            if variable not in required:
                required.append(variable)

    present: dict[str, Any] = {}
    missing: list[str] = []
    ambiguous: list[dict[str, Any]] = context_ambiguities(context)
    documents_present = detect_present_documents(context)
    documents_to_request: list[str] = []

    for variable in required:
        found, value, source_key = find_context_value(variable, context)
        if found and is_ambiguous_value(value):
            ambiguous.append({"variable": variable, "source_key": source_key, "value": value})
            for document_name in documents_needed_for(variable):
                if document_name not in documents_present and document_name not in documents_to_request:
                    documents_to_request.append(document_name)
            continue
        if found:
            present[variable] = {"value": value, "source_key": source_key}
            continue
        missing.append(variable)
        for document_name in documents_needed_for(variable):
            if document_name not in documents_present and document_name not in documents_to_request:
                documents_to_request.append(document_name)

    selection_context = {
        "missing_variables": set(missing),
        "ambiguous_variables": {item.get("variable") for item in ambiguous},
        "context_has_ambiguities": bool(ambiguous),
        "warnings_by_rule_id": {item.rule.get("rule_id"): item.warnings for item in selected_evaluations},
        "context_population_values": context_population(context),
        "context_category_values": context_employment_category(context),
        "reference_date": reference_date,
    }
    reference_date_for_calculation = reference_date or date.today()
    calculation_warnings: list[str] = []
    for rule in selected_rules:
        effective = parse_reference_date(rule.get("effective_date"))
        if effective and reference_date_for_calculation < effective:
            calculation_warnings.append(
                f"rule_not_yet_effective: {rule.get('rule_id')} applicable a partir de {effective.isoformat()}."
            )
    rule_conflict = detect_rule_conflicts(selected_rules)
    selection_context["reference_date"] = reference_date_for_calculation
    selection_context["rule_conflict"] = rule_conflict
    if rule_conflict["has_conflict"]:
        calculation_warnings.append(
            "rule_conflict: "
            + ", ".join(rule_conflict["conflicting_rule_ids"])
            + f" ({rule_conflict['reason']})"
        )
    calculation_ready = bool(selected_rules) and all(
        is_safe_for_calculation(rule, selection_context) for rule in selected_rules
    )
    return {
        "required": required,
        "present": present,
        "missing": missing,
        "ambiguous": ambiguous,
        "documents_present": documents_present,
        "documents_to_request": sorted(documents_to_request),
        "calculation_ready": calculation_ready,
        "calculation_warnings": calculation_warnings,
        "rule_conflict": rule_conflict,
    }


def confidence_level(selected_rules: list[dict[str, Any]], variables: dict[str, Any]) -> str:
    if not selected_rules:
        return "faible"
    if variables["missing"] or variables["ambiguous"]:
        return "faible"
    if any(rule.get("status") == "to_verify" or rule.get("confidence") == "low" for rule in selected_rules):
        return "moyenne"
    return "elevee"


def analyze_payroll_query(
    question: str,
    context: dict[str, Any] | None = None,
    *,
    rules: list[dict[str, Any]] | None = None,
    catalog_path: Path | str = DEFAULT_CATALOG_PATH,
    schema_path: Path | str = DEFAULT_SCHEMA_PATH,
) -> dict[str, Any]:
    """Prepare a structured payroll response without calculating."""
    context = copy.deepcopy(context or {})
    if rules is None:
        catalog = load_validated_catalog(catalog_path=catalog_path, schema_path=schema_path)
        rules_to_use = catalog["rules"]
        metadata = {key: catalog.get(key) for key in ("catalog_id", "version", "scope")}
    else:
        rules_to_use = copy.deepcopy(rules)
        metadata = {"catalog_id": "injected_rules", "version": "test", "scope": "in_memory"}

    topics = classify_query(question, context)
    reference_date = context_reference_date(context)
    evaluations: list[RuleEvaluation] = []
    for rule in rules_to_use:
        evaluation = evaluate_rule(rule, topics, context, reference_date=reference_date)
        if evaluation:
            evaluations.append(evaluation)

    candidate_rules = [
        {
            "rule_id": evaluation.rule.get("rule_id"),
            "title": evaluation.rule.get("title"),
            "score": evaluation.score,
            "matched_topics": evaluation.matched_topics,
        }
        for evaluation in sorted(evaluations, key=lambda item: item.score, reverse=True)
    ]
    selected_evaluations = [evaluation for evaluation in evaluations if not evaluation.rejected]
    selected_evaluations.sort(
        key=lambda item: (
            item.score,
            -SOURCE_RANK.get(str(item.rule.get("source_layer")), 99),
            str(item.rule.get("rule_id")),
        ),
        reverse=True,
    )
    rejected_evaluations = [evaluation for evaluation in evaluations if evaluation.rejected]

    selected_rules = [summarize_rule(evaluation) for evaluation in selected_evaluations]
    rejected_rules = [summarize_rejection(evaluation) for evaluation in rejected_evaluations]
    historical_rules = [
        summarize_rejection(evaluation)
        for evaluation in rejected_evaluations
        if evaluation.reject_reason == "historical_or_memory_source"
    ]
    variables = collect_variables(selected_evaluations, context, reference_date=reference_date)

    warnings: list[str] = []
    if not topics:
        warnings.append("Aucun theme paie, conges ou temps de travail reconnu.")
    if not selected_rules and candidate_rules:
        warnings.append("Des regles candidates existent mais aucune n'est applicable au contexte fourni.")
    if any(rule["status"] == "to_verify" for rule in selected_rules):
        warnings.append("Une ou plusieurs regles sont a verifier humainement avant utilisation.")
    if any(rule["confidence"] == "low" for rule in selected_rules):
        warnings.append("Une ou plusieurs sources ont une confiance faible.")
    future_rejections = [
        evaluation.rule.get("rule_id")
        for evaluation in rejected_evaluations
        if evaluation.reject_reason == "rule_not_yet_effective"
    ]
    if future_rejections:
        warnings.append("rule_not_yet_effective: " + ", ".join(str(rule_id) for rule_id in future_rejections))
    warnings.extend(variables.get("calculation_warnings", []))
    if selected_rules and not variables["calculation_ready"]:
        warnings.append("Calcul automatique refuse: variables incompletes ou regles non autorisees au calcul.")

    return {
        "catalog": metadata,
        "query_topics": topics,
        "candidate_rules": candidate_rules,
        "selected_rules": selected_rules,
        "rejected_rules": rejected_rules,
        "historical_rules": historical_rules,
        "source_hierarchy": SOURCE_HIERARCHY,
        "variables": {
            "required": variables["required"],
            "present": variables["present"],
            "missing": variables["missing"],
            "ambiguous": variables["ambiguous"],
        },
        "documents_present": variables["documents_present"],
        "documents_to_request": variables["documents_to_request"],
        "calculation_ready": variables["calculation_ready"],
        "rule_conflict": variables["rule_conflict"],
        "warnings": warnings,
        "confidence": confidence_level(selected_rules, variables),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Select payroll rules without calculating payroll amounts.")
    parser.add_argument("question", nargs="?", default="")
    parser.add_argument("--context-json", default="{}")
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG_PATH))
    args = parser.parse_args(argv)
    try:
        context = json.loads(args.context_json)
        if not isinstance(context, dict):
            raise ValueError("context-json must be a JSON object")
        report = analyze_payroll_query(args.question, context, catalog_path=args.catalog)
    except Exception as exc:  # pragma: no cover - CLI safety net
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
