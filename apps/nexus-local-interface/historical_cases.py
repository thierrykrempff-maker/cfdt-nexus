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
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
VALIDATION_ROOT = (
    ROOT / "tests" / "fixtures" / "real_business_cases" / "v1_release_validation"
)
RESULTS_PATH = VALIDATION_ROOT / "v1-release-results.json"
RAW_ROOT = VALIDATION_ROOT / "raw"

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
        "categories": ("disciplinary", "health_safety"),
        "keywords": ("alcool", "courriels", "insultes", "disciplinaire"),
    },
    "REAL-02": {
        "fixture": "real-02-smoking_breaks_seveso_badge.response.json",
        "title": "Pauses cigarettes et utilisation du badgeage Seveso",
        "domain": "Discipline / preuve / données personnelles",
        "categories": ("disciplinary", "personal_data"),
        "keywords": ("badgeage", "pauses", "cigarettes", "seveso", "cnil"),
    },
    "REAL-03": {
        "fixture": "real-03-tag_installation.response.json",
        "title": "Tag sur installation et souffrance au travail",
        "domain": "Discipline / santé et sécurité",
        "categories": ("disciplinary", "health_safety", "organization"),
        "keywords": ("tag", "installation", "souffrance", "travail"),
    },
    "REAL-04": {
        "fixture": "real-04-forced_day_to_shift_laboratory.response.json",
        "title": "Passage forcé de jour vers horaires postés",
        "domain": "Temps et organisation du travail",
        "categories": ("working_time", "organization"),
        "keywords": ("horaires", "jour", "poste", "laboratoire"),
    },
    "REAL-05": {
        "fixture": "real-05-delegation_hours_cssct_incomplete.response.json",
        "title": "Heures de délégation CSSCT, cas incomplet",
        "domain": "CSE / CSSCT",
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
        "categories": ("health_safety",),
        "keywords": ("epi", "sécurité", "protection", "indisponible", "inadapté"),
    },
    "REAL-08": {
        "fixture": "real-08-temporary_day_to_three_shift_refusal.response.json",
        "title": "Passage temporaire de jour vers 3x8",
        "domain": "Temps et organisation du travail",
        "categories": ("working_time", "organization"),
        "keywords": ("horaires", "3x8", "jour", "temporaire", "refus"),
    },
    "REAL-09": {
        "fixture": "real-09-chemical_recipe_outdated_procedure.response.json",
        "title": "Erreur de fabrication et procédure obsolète",
        "domain": "Santé, sécurité et organisation du travail",
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
        "categories": ("disciplinary", "health_safety"),
        "keywords": ("alcool", "alcoolémie", "poste", "risque", "sécurité"),
    },
    "REAL-11": {
        "fixture": "real-11-insults_supervisor_fatigue_context.response.json",
        "title": "Insultes envers un responsable dans un contexte de fatigue",
        "domain": "Discipline / organisation du travail",
        "categories": ("disciplinary", "health_safety", "organization"),
        "keywords": ("insultes", "responsable", "fatigue", "organisation"),
    },
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
        "title": "Cas métier anonymisés et testés dans le cadre de la validation V1",
        "warning": (
            "Ces cas sont des exemples anonymisés utilisés pour tester CFDT Nexus. "
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
    detail = {
        **metadata,
        "average_score": catalog["score_average"],
        "score_explanation": catalog["score_explanation"],
        "special_notes": list(presentation.get("notes", ())),
        "public_summary": _public_summary(raw_case),
        "usage": (
            "Consultation, démonstration, formation, validation et comparaison "
            "manuelle uniquement."
        ),
        "automatic_reuse": False,
    }
    _validate_public_value(detail, f"detail.{short_id}")
    return detail
