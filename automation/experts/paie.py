#!/usr/bin/env python
"""Expert Paie V0 for local Nexus analyses."""

from __future__ import annotations

from typing import Any

from .utils import collect_issue_values, has_any, normalize, route_domains, source_documents, unique

try:  # Used when automation/ is inserted directly in sys.path by the local UI.
    from payroll import payroll_referential_integration, payroll_rule_engine
except Exception:  # pragma: no cover - fallback for package-style imports.
    try:
        from automation.payroll import payroll_referential_integration, payroll_rule_engine  # type: ignore[no-redef]
    except Exception:  # pragma: no cover - handled as a safe runtime fallback.
        payroll_rule_engine = None  # type: ignore[assignment]
        payroll_referential_integration = None  # type: ignore[assignment]


PAIE_KEYWORDS = [
    "paie",
    "bulletin",
    "salaire",
    "coefficient",
    "classification",
    "heures supplementaires",
    "heure supplementaire",
    "heures de nuit",
    "nuit",
    "dimanche",
    "jour ferie",
    "jours feries",
    "astreinte",
    "intervention",
    "prime",
    "majoration",
    "recuperation",
    "repos compensateur",
    "compteur",
    "pointage",
]

PAYROLL_RULE_EXCLUDED_TOPICS = {"classification", "coefficient"}
PAYROLL_RULE_DISPLAY_LIMIT = 6
PAYROLL_RULE_GENERIC_TOPICS = {"5x8", "jour", "poste", "poste_continu", "roulement", "conges_payes", "maintien"}
PAYROLL_RULE_FOCUS_DOCUMENTS = {
    "prise_cp": ["demande_conge", "reponse_hierarchie"],
    "maladie": ["arret_de_travail", "bulletin_de_paie", "contrat"],
    "rjfj": ["releve_kelio"],
    "heures_supplementaires": ["planning", "bulletin_de_paie", "releve_kelio"],
    "changement_roulement": ["planning"],
    "treizieme_mois": ["bulletin_de_paie"],
}


def applies(answer: dict[str, Any]) -> bool:
    domains = route_domains(answer)
    query = answer.get("query", "")
    if "paie_remuneration" in domains:
        return True
    if has_any(query, ["bulletin", "paie", "salaire", "majoration", "prime", "compteur", "pointage"]):
        return True
    if has_any(query, ["coefficient", "classification"]) and has_any(query, ["bulletin", "salaire", "paie"]):
        return True
    topics = payroll_rule_topics(answer)
    if topics and set(topics) - PAYROLL_RULE_EXCLUDED_TOPICS:
        return True
    return False


def payroll_rule_topics(answer: dict[str, Any]) -> list[str]:
    if payroll_rule_engine is None:
        return []
    try:
        return list(payroll_rule_engine.classify_query(answer.get("query", ""), payroll_rule_context(answer)))
    except Exception:
        return []


def payroll_rule_context(answer: dict[str, Any]) -> dict[str, Any]:
    context: dict[str, Any] = {}
    for key in ("payroll_rule_context", "payroll_context", "context"):
        value = answer.get(key)
        if isinstance(value, dict):
            context.update(value)

    for key in ("reference_date", "employee_population", "employment_category", "work_schedule", "site"):
        if key in answer and key not in context:
            context[key] = answer[key]

    variables = answer.get("variables")
    if isinstance(variables, dict):
        existing_variables = context.get("variables") if isinstance(context.get("variables"), dict) else {}
        context["variables"] = {**existing_variables, **variables}

    documents = answer.get("documents") or answer.get("documents_present") or answer.get("pieces_presentes")
    if documents and "documents" not in context:
        context["documents"] = documents
    return context


def limited_dicts(values: list[dict[str, Any]], limit: int = PAYROLL_RULE_DISPLAY_LIMIT) -> list[dict[str, Any]]:
    return values[:limit]


def safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def safe_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    return []


def safe_string_list(value: Any) -> list[str]:
    return [str(item) for item in safe_list(value) if str(item or "").strip()]


def safe_rule_dicts(value: Any) -> list[dict[str, Any]]:
    return [dict(item) for item in safe_list(value) if isinstance(item, dict)]


def safe_warning_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item or "").strip()]
    if value in (None, "", [], {}):
        return []
    if isinstance(value, (str, int, float, bool)):
        return [str(value)]
    return []


def safe_confidence(value: Any) -> str:
    confidence = str(value or "").strip().lower()
    allowed = {"faible", "moyenne", "elevee", "low", "medium", "high"}
    return confidence if confidence in allowed else "faible"


def normalize_payroll_rule(rule: dict[str, Any]) -> dict[str, Any]:
    rule = safe_dict(rule)
    return {
        "rule_id": rule.get("rule_id"),
        "title": rule.get("title"),
        "source_layer": rule.get("source_layer"),
        "source_document": rule.get("source_document"),
        "source_page": rule.get("source_page"),
        "status": rule.get("status"),
        "confidence": rule.get("confidence"),
        "population": rule.get("population"),
        "work_schedule": rule.get("work_schedule"),
        "matched_topics": safe_string_list(rule.get("matched_topics")),
        "required_variables": safe_string_list(rule.get("required_variables")),
        "warnings": safe_warning_list(rule.get("warnings")),
    }


def normalize_rejected_rule(rule: dict[str, Any]) -> dict[str, Any]:
    rule = safe_dict(rule)
    return {
        "rule_id": rule.get("rule_id"),
        "title": rule.get("title"),
        "matched_topics": safe_string_list(rule.get("matched_topics")),
        "reason": rule.get("reason"),
        "details": safe_string_list(rule.get("details")),
    }


def normalize_candidate_rule(rule: dict[str, Any]) -> dict[str, Any]:
    rule = safe_dict(rule)
    return {
        "rule_id": rule.get("rule_id"),
        "title": rule.get("title"),
        "score": rule.get("score"),
        "matched_topics": safe_string_list(rule.get("matched_topics")),
    }


def payroll_rule_display_focuses(query_topics: list[str], query: str) -> list[str]:
    text = normalize(query)
    topics = set(query_topics)
    focuses: list[str] = []
    if topics & {"maladie", "absence_maladie", "prevoyance"}:
        focuses.append("maladie")
    if topics & {"rjfj", "rjfn", "recuperation_jour_ferie"} or has_any(text, ["rjfj", "rjfn", " jr "]):
        focuses.append("rjfj")
    if "heures_supplementaires" in topics:
        focuses.append("heures_supplementaires")
    if "treizieme_mois" in topics:
        focuses.append("treizieme_mois")
    if "changement_roulement" in topics:
        focuses.append("changement_roulement")
    if "conges_payes" in topics and "maladie" not in focuses and "rjfj" not in focuses:
        if has_any(text, ["refus", "refuse", "demande", "pose", "ordre", "depart", "report"]):
            focuses.append("prise_cp")
        elif has_any(text, ["dixieme", "indemnite", "maintien de salaire", "calcul"]):
            focuses.append("indemnite_conges")
        elif has_any(text, ["acquisition", "acquis", "2 5", "2,5"]):
            focuses.append("acquisition_cp")
        else:
            focuses.append("conges_payes_direct")
    for topic in ["nuit", "dimanche", "jour_ferie", "astreinte", "intervention"]:
        if topic in topics:
            focuses.append(topic)
    precise = [topic for topic in query_topics if topic not in PAYROLL_RULE_GENERIC_TOPICS]
    return unique(focuses or precise, limit=8)


def payroll_rule_matches_focus(rule: dict[str, Any], focuses: list[str]) -> bool:
    rule = safe_dict(rule)
    if not focuses:
        return True
    rule_id = normalize(rule.get("rule_id", ""))
    title = normalize(rule.get("title", ""))
    matched_topics = set(safe_string_list(rule.get("matched_topics")))
    text = f"{rule_id} {title} {' '.join(matched_topics)}"
    for focus in focuses:
        if focus == "maladie" and ("maladie" in text or "prevoyance" in text or "absence_maladie" in matched_topics):
            return True
        if focus == "prise_cp" and (
            "leave_cp_request" in rule_id
            or "leave cp request" in rule_id
            or "delai" in title
            or "demande de conge" in title
        ):
            return True
        if focus == "indemnite_conges" and ("indemnite" in text or "dixieme" in text):
            return True
        if focus == "acquisition_cp" and "acquisition" in text:
            return True
        if focus == "conges_payes_direct" and (rule_id.startswith("leave_cp") or rule_id.startswith("leave cp")):
            return True
        if focus == "rjfj" and any(token in rule_id for token in ["rjfj", "rjfn", "jr_regularisation", "jr regularisation"]):
            return True
        if focus == "heures_supplementaires" and ("hsup" in rule_id or "heures_supplementaires" in matched_topics):
            return True
        if focus == "treizieme_mois" and ("13e" in rule_id or "treizieme" in text):
            return True
        if focus == "changement_roulement" and ("changement_roulement" in text or "changement roulement" in text):
            return True
        if focus in matched_topics and focus not in PAYROLL_RULE_GENERIC_TOPICS:
            return True
    return False


def payroll_rule_present_documents(context: dict[str, Any]) -> set[str]:
    if payroll_rule_engine is None:
        return set()
    detector = getattr(payroll_rule_engine, "detect_present_documents", None)
    if not callable(detector):
        return set()
    try:
        return set(detector(context))
    except Exception:
        return set()


def payroll_rule_documents_for_variables(variables: list[str]) -> list[str]:
    values: list[str] = []
    if payroll_rule_engine is None:
        return values
    finder = getattr(payroll_rule_engine, "documents_needed_for", None)
    for variable in variables:
        if callable(finder):
            try:
                values.extend(str(item) for item in finder(variable))
                continue
            except Exception:
                pass
        values.append("piece_justificative_a_preciser")
    return unique(values, limit=12)


def filtered_payroll_variables(
    variables: dict[str, Any],
    displayed_rules: list[dict[str, Any]],
) -> dict[str, Any]:
    variables = safe_dict(variables)
    required = unique(
        variable
        for rule in displayed_rules
        for variable in safe_string_list(rule.get("required_variables"))
    )
    present_values = variables.get("present") if isinstance(variables.get("present"), dict) else {}
    present = {
        key: value
        for key, value in present_values.items()
        if key in required
    }
    missing = [item for item in safe_string_list(variables.get("missing")) if item in required]
    ambiguous = []
    for item in safe_list(variables.get("ambiguous")):
        variable = item.get("variable") if isinstance(item, dict) else item
        if variable in required:
            ambiguous.append(item)
    return {"present": present, "missing": missing, "ambiguous": ambiguous}


def filtered_payroll_documents(
    filtered_variables: dict[str, Any],
    focuses: list[str],
    context: dict[str, Any],
) -> list[str]:
    variables = list(filtered_variables.get("missing", []))
    for item in filtered_variables.get("ambiguous", []):
        if isinstance(item, dict) and item.get("variable"):
            variables.append(str(item["variable"]))
    values = payroll_rule_documents_for_variables(variables)
    for focus in focuses:
        values.extend(PAYROLL_RULE_FOCUS_DOCUMENTS.get(focus, []))
    present_documents = payroll_rule_present_documents(context)
    if "demande_conge" in present_documents and "reponse_hierarchie" in values:
        values.remove("demande_conge")
    return unique((item for item in values if item not in present_documents), limit=10)


def payroll_rules_filtered_for_display(
    report: dict[str, Any],
    query: str,
    context: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], list[str], list[str]]:
    report = safe_dict(report)
    query_topics = safe_string_list(report.get("query_topics"))
    focuses = payroll_rule_display_focuses(query_topics, query)
    selected = safe_rule_dicts(report.get("selected_rules"))
    candidates = safe_rule_dicts(report.get("candidate_rules"))
    displayed = [rule for rule in selected if payroll_rule_matches_focus(rule, focuses)]
    filtered_out = [rule for rule in selected if rule not in displayed]
    displayed_ids = {rule.get("rule_id") for rule in displayed}
    displayed_candidates = [
        rule
        for rule in candidates
        if rule.get("rule_id") in displayed_ids or payroll_rule_matches_focus(rule, focuses)
    ]
    rejected = safe_rule_dicts(report.get("rejected_rules"))
    rejected.extend(
        {
            "rule_id": rule.get("rule_id"),
            "title": rule.get("title"),
            "matched_topics": rule.get("matched_topics", []),
            "reason": "faible_pertinence_affichage",
            "details": ["Regle ecartee de l'affichage LOT 3 car elle ne correspond pas au sujet principal."],
        }
        for rule in filtered_out
    )
    variables = filtered_payroll_variables(report.get("variables"), displayed)
    documents = filtered_payroll_documents(variables, focuses, context)
    warnings: list[str] = safe_warning_list(report.get("warnings"))
    if not query_topics:
        warnings.append("Aucun theme paie, conges ou temps de travail reconnu.")
    if not displayed and displayed_candidates:
        warnings.append("Des regles candidates existent mais aucune n'est applicable au contexte fourni.")
    if any(rule.get("status") == "to_verify" for rule in displayed):
        warnings.append("Une ou plusieurs regles affichees sont a verifier humainement avant utilisation.")
    if any(rule.get("confidence") == "low" for rule in displayed):
        warnings.append("Une ou plusieurs regles affichees ont une confiance faible.")
    if displayed and report.get("calculation_ready") is not True:
        warnings.append("Calcul automatique refuse: variables incompletes ou regles non autorisees au calcul.")
    if filtered_out:
        warnings.append(
            "Regles ecartees de l'affichage LOT 3 pour faible pertinence: "
            + ", ".join(str(rule.get("rule_id")) for rule in filtered_out[:6])
        )
    return displayed, displayed_candidates, rejected, variables, documents, unique(warnings, limit=8)


def normalize_payroll_rule_analysis(report: dict[str, Any]) -> dict[str, Any]:
    return normalize_filtered_payroll_rule_analysis(report, "", {})


def normalize_filtered_payroll_rule_analysis(
    report: dict[str, Any],
    query: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    report = safe_dict(report)
    selected, candidates, rejected, variables, documents, warnings = payroll_rules_filtered_for_display(report, query, context)
    return {
        "engine_available": True,
        "query_topics": safe_string_list(report.get("query_topics")),
        "candidate_rules": [normalize_candidate_rule(rule) for rule in limited_dicts(candidates)],
        "selected_rules": [normalize_payroll_rule(rule) for rule in limited_dicts(selected)],
        "rejected_rules": [normalize_rejected_rule(rule) for rule in limited_dicts(rejected)],
        "variables": variables,
        "documents_to_request": documents,
        "calculation_ready": report.get("calculation_ready") is True,
        "warnings": warnings,
        "confidence": safe_confidence(report.get("confidence")),
    }


def payroll_rule_error_analysis(message: str) -> dict[str, Any]:
    return {
        "engine_available": False,
        "query_topics": [],
        "candidate_rules": [],
        "selected_rules": [],
        "rejected_rules": [],
        "variables": {"present": {}, "missing": [], "ambiguous": []},
        "documents_to_request": [],
        "calculation_ready": False,
        "warnings": [f"PayrollRuleEngine indisponible: {message}"],
        "confidence": "faible",
    }


def payroll_rule_analysis(answer: dict[str, Any]) -> dict[str, Any] | None:
    if payroll_rule_engine is None:
        return payroll_rule_error_analysis("module non charge")
    try:
        context = payroll_rule_context(answer)
        report = payroll_rule_engine.analyze_payroll_query(answer.get("query", ""), context)
    except Exception as exc:
        return payroll_rule_error_analysis(str(exc))
    try:
        analysis = normalize_filtered_payroll_rule_analysis(report, answer.get("query", ""), context)
    except Exception as exc:
        return payroll_rule_error_analysis(f"payroll_rule_normalization_error: {exc}")
    if not analysis["query_topics"] and not analysis["candidate_rules"] and not analysis["selected_rules"]:
        analysis["warnings"] = unique(analysis["warnings"], limit=6)
    return analysis


def payroll_rule_source_items(analysis: dict[str, Any] | None) -> list[str]:
    if not analysis or not analysis.get("engine_available"):
        return []
    values = []
    for rule in analysis.get("selected_rules", []):
        values.append(
            "PayrollRule: "
            + str(rule.get("title") or rule.get("rule_id"))
            + f" ({rule.get('rule_id')}) - statut {rule.get('status')}, confiance {rule.get('confidence')}"
        )
    return values


def payroll_rule_data_items(analysis: dict[str, Any] | None) -> list[str]:
    if not analysis:
        return []
    variables = analysis.get("variables", {})
    values = [f"Variable PayrollRule manquante: {item}" for item in variables.get("missing", [])]
    values.extend(f"Variable PayrollRule ambigue: {item.get('variable')}" for item in variables.get("ambiguous", []) if isinstance(item, dict))
    return values


def payroll_rule_limit_items(analysis: dict[str, Any] | None) -> list[str]:
    if not analysis:
        return []
    values = list(analysis.get("warnings", []))
    if analysis.get("calculation_ready") is not True:
        values.append("PayrollRuleEngine: calcul automatique non disponible avec le catalogue actuel.")
    return values


def is_incomplete_prime_query(answer: dict[str, Any]) -> bool:
    query = normalize(answer.get("query", ""))
    return "prime" in query and not has_any(
        query,
        [
            "nuit",
            "dimanche",
            "jour ferie",
            "astreinte",
            "montant",
            "taux",
            "periode",
            "bulletin",
            "coefficient",
        ],
    )


def excludes_astreinte(answer: dict[str, Any]) -> bool:
    query = normalize(answer.get("query", ""))
    return has_any(query, ["sans astreinte", "pas d astreinte", "aucune astreinte", "hors astreinte", "non astreinte"])


def is_astreinte_context(answer: dict[str, Any]) -> bool:
    if excludes_astreinte(answer):
        return False
    domains = route_domains(answer)
    query = answer.get("query", "")
    return "astreinte" in domains or has_any(query, ["astreinte"])


def object_of_control(answer: dict[str, Any]) -> str:
    query = answer.get("query", "")
    if is_incomplete_prime_query(answer):
        return "Controle d'une prime non identifiee : Nexus doit d'abord connaitre le libelle, la periode et la regle applicable."
    if is_astreinte_context(answer):
        return "Controle paie d'une intervention pendant astreinte, avec heures, majorations, recuperation et compteurs."
    if has_any(query, ["nuit", "dimanche", "jour ferie", "majoration"]):
        return "Controle des heures de nuit, dimanche ou jour ferie et des majorations correspondantes sur le bulletin."
    if has_any(query, ["coefficient", "classification", "salaire de base"]):
        return "Controle du salaire de base au regard du coefficient, de la classification et des textes applicables."
    if has_any(query, ["prime"]):
        return "Controle d'une prime ou d'un element variable de remuneration."
    return "Controle paie methodologique a partir du bulletin, du pointage, des compteurs et des sources locales."


def bulletin_elements(answer: dict[str, Any]) -> list[str]:
    query = answer.get("query", "")
    elements: list[str] = []
    if has_any(query, ["salaire de base", "coefficient", "classification"]):
        elements.extend(["salaire de base", "coefficient ou classification affichee", "taux ou appointement mensuel"])
    if has_any(query, ["nuit"]):
        elements.extend(["heures de nuit", "majoration nuit", "base et taux appliques"])
    if has_any(query, ["dimanche"]):
        elements.extend(["heures du dimanche", "majoration dimanche", "base et taux appliques"])
    if has_any(query, ["jour ferie", "jours feries"]):
        elements.extend(["heures de jour ferie", "majoration jour ferie", "repos ou recuperation associee"])
    if is_astreinte_context(answer):
        elements.extend(
            [
                "indemnite ou prime d'astreinte",
                "heures d'intervention",
                "majorations eventuelles nuit, dimanche ou jour ferie",
                "recuperation ou repos compensateur",
                "compteurs horaires",
            ]
        )
    if has_any(query, ["prime"]):
        elements.extend(["libelle exact de la prime", "base de calcul", "montant verse", "periode rattachee"])
    if not elements:
        elements.extend(["rubriques du bulletin concernees", "base de calcul", "taux", "montant verse"])
    return unique(elements, limit=10)


def available_rules(answer: dict[str, Any]) -> list[str]:
    sources = source_documents(answer)
    if not sources:
        return ["Aucune source locale principale n'est disponible dans la reponse Nexus."]
    return ["Source locale a verifier: " + source for source in sources]


def data_needed(answer: dict[str, Any]) -> list[str]:
    query = answer.get("query", "")
    values = [
        "periode de paie controlee",
        "bulletin de paie detaille de la periode",
        "pointage ou releve horaire valide",
        "compteurs horaires avant et apres paie",
        "regle locale applicable a la rubrique controlee",
        "taux ou montant applique sur le bulletin",
    ]
    if has_any(query, ["nuit", "dimanche", "jour ferie"]) or is_astreinte_context(answer):
        values.extend(
            [
                "heure de debut et de fin de chaque sequence",
                "qualification des plages nuit, dimanche ou jour ferie",
                "detail des majorations ou recuperations appliquees",
            ]
        )
    if is_astreinte_context(answer):
        values.extend(
            [
                "declenchement de l'astreinte",
                "duree d'intervention retenue",
                "temps annexes retenus ou exclus par la source applicable",
            ]
        )
    if has_any(query, ["prime"]):
        values.extend(["libelle exact de la prime", "condition d'ouverture de la prime", "assiette ou formule de calcul"])
    if has_any(query, ["coefficient", "classification", "salaire de base"]):
        values.extend(["coefficient applicable", "classification retenue", "grille ou texte de remuneration applicable"])
    return unique(values, limit=14)


def control_method(answer: dict[str, Any]) -> list[str]:
    query = answer.get("query", "")
    steps = [
        "Identifier la rubrique controlee, la periode et la source locale applicable.",
        "Rapprocher pointage, planning, compteurs et bulletin sans additionner des elements de nature differente.",
        "Verifier la base, le taux, le nombre d'heures ou le montant retenu sur le bulletin.",
        "Comparer le resultat attendu au bulletin uniquement apres validation des donnees et du texte applicable.",
    ]
    if has_any(query, ["nuit", "dimanche", "jour ferie"]):
        steps.insert(2, "Isoler les heures situees sur les plages nuit, dimanche ou jour ferie avant de chercher la majoration.")
    if is_astreinte_context(answer):
        steps.insert(2, "Separarer indemnite d'astreinte, temps d'intervention, majorations et recuperations.")
    if is_incomplete_prime_query(answer):
        steps.insert(0, "Demander d'abord quelle prime est visee et sur quel bulletin elle apparait.")
    return unique(steps, limit=8)


def potential_anomalies(answer: dict[str, Any]) -> list[str]:
    query = answer.get("query", "")
    anomalies = [
        "rubrique absente ou libellee de facon ambigue",
        "nombre d'heures payees different du pointage valide",
        "taux ou base non justifie par la source applicable",
        "ecart entre compteur, bulletin et recapitulatif paie",
    ]
    if has_any(query, ["nuit"]):
        anomalies.append("heures de nuit non isolees ou non majorees selon la source applicable")
    if has_any(query, ["dimanche"]):
        anomalies.append("majoration dimanche absente ou calculee sur une mauvaise base")
    if has_any(query, ["jour ferie"]):
        anomalies.append("traitement jour ferie confondu avec dimanche, nuit ou recuperation")
    if is_astreinte_context(answer):
        anomalies.extend(
            [
                "intervention d'astreinte payee sans coherence avec le declenchement et les horaires",
                "recuperation ou repos compensateur absent du compteur",
            ]
        )
    if is_incomplete_prime_query(answer):
        anomalies.append("impossible d'identifier l'anomalie tant que la prime n'est pas nommee")
    return unique(anomalies, limit=10)


def calculation_detail(answer: dict[str, Any]) -> str:
    return (
        "Non produit : Nexus ne dispose pas simultanement des heures validees, du taux ou montant applicable, "
        "de la base de calcul et de la valeur portee au bulletin."
    )


def documents_needed(answer: dict[str, Any]) -> list[str]:
    values = [
        "bulletin de paie de la periode controlee",
        "detail de paie ou recapitulatif des elements variables",
        "pointage ou releve horaire valide",
        "planning de la periode",
        "compteurs horaires et recuperations",
    ]
    values.extend(str(item) for item in answer.get("documents_to_request", []))
    values.extend(collect_issue_values(answer, "documents"))
    return unique(values, limit=12)


def confidence(answer: dict[str, Any]) -> str:
    if is_incomplete_prime_query(answer):
        return "faible"
    if not answer.get("sources"):
        return "faible"
    return "moyen"


def limits(answer: dict[str, Any]) -> list[str]:
    items = [
        "L'expert paie V0 ne calcule pas sans bulletin, pointage, taux applicable et source de calcul.",
        "Il ne lit aucun document externe et n'envoie aucune donnee hors du poste local.",
        "Les sources retrouvees doivent etre relues pour confirmer leur champ d'application.",
    ]
    if is_incomplete_prime_query(answer):
        items.append("La question est trop incomplete pour identifier la rubrique ou la regle de prime.")
    return unique(items, limit=8)


def enrich(answer: dict[str, Any]) -> dict[str, Any]:
    if not applies(answer):
        return {
            "active": False,
            "name": "Expert Paie V0",
            "reason": "Question hors perimetre paie pour cette orchestration.",
        }
    rule_analysis = payroll_rule_analysis(answer)
    referential_analysis = (
        payroll_referential_integration.build_analysis(answer, rule_analysis or {})
        if payroll_referential_integration is not None
        else None
    )
    rules_available = available_rules(answer)
    rules_available.extend(payroll_rule_source_items(rule_analysis))
    data = data_needed(answer)
    data.extend(payroll_rule_data_items(rule_analysis))
    documents = documents_needed(answer)
    if rule_analysis:
        documents.extend(str(item) for item in rule_analysis.get("documents_to_request", []))
    if referential_analysis:
        documents.extend(str(item) for item in referential_analysis.get("documents_missing", []))
    limit_values = limits(answer)
    limit_values.extend(payroll_rule_limit_items(rule_analysis))
    if referential_analysis:
        limit_values.extend(str(item) for item in referential_analysis.get("refusal_reasons", []))
    return {
        "active": True,
        "name": "Expert Paie V0",
        "objet_du_controle": object_of_control(answer),
        "elements_du_bulletin_concernes": bulletin_elements(answer),
        "regles_ou_sources_disponibles": unique(rules_available, limit=14),
        "donnees_necessaires_au_calcul": unique(data, limit=18),
        "methode_de_controle": control_method(answer),
        "anomalies_potentielles": potential_anomalies(answer),
        "calcul_detaille": calculation_detail(answer),
        "documents_necessaires": unique(documents, limit=16),
        "sources_utilisees": source_documents(answer),
        "niveau_de_confiance": (
            str(referential_analysis.get("confidence"))
            if referential_analysis and referential_analysis.get("confidence")
            else confidence(answer)
        ),
        "limites": unique(limit_values, limit=12),
        "payroll_rule_analysis": rule_analysis,
        "payroll_referential_analysis": referential_analysis,
        "reponse_salarie": referential_analysis.get("employee_response") if referential_analysis else None,
        "reponse_expert": referential_analysis.get("expert_response") if referential_analysis else None,
    }
