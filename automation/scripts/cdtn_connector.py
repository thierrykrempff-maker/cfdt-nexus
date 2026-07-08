#!/usr/bin/env python
"""Code du travail numerique connector for official practical explanations.

This connector is intentionally separate from the Nexus router. It only calls
public Code du travail numerique endpoints, stores a local cache under
local-index/cdtn/, and normalizes short official practical explanations as
source_layer=pratique_officielle.

It does not scrape HTML pages and it does not replace legal sources such as
INEOS agreements, the chemical industry collective agreement, Legifrance Code
du travail articles or JUDILIBRE case law.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]

ENV_API_BASE_URL = "CFDT_NEXUS_CDTN_API_BASE_URL"
ENV_TIMEOUT = "CFDT_NEXUS_CDTN_TIMEOUT"
ENV_CACHE_DIR = "CFDT_NEXUS_CDTN_CACHE_DIR"
ENV_CACHE_TTL = "CFDT_NEXUS_CDTN_CACHE_TTL_SECONDS"

DEFAULT_API_BASE_URL = "https://code.travail.gouv.fr"
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_CACHE_TTL_SECONDS = 24 * 60 * 60
DEFAULT_LIMIT = 4
PRESEARCH_ENDPOINT = "/api/presearch"
SUGGEST_ENDPOINT = "/api/suggest"
HEALTH_ENDPOINT = "/api/health"
SOURCE_LAYER = "pratique_officielle"

EXPLANATION_SOURCES = {
    "fiches_service_public",
    "fiches_ministere_travail",
    "contributions",
    "infographies",
}
ORIENTATION_SOURCES = {
    "themes",
    "outils",
    "modeles_de_courriers",
}

SOURCE_PROFILES: dict[str, dict[str, Any]] = {
    "fiches_service_public": {
        "label": "Service-Public.fr",
        "content_type": "fiche pratique officielle",
        "official_origin": "service-public.fr",
        "explanation_source": True,
    },
    "fiches_ministere_travail": {
        "label": "Ministere du Travail",
        "content_type": "fiche pratique ministerielle",
        "official_origin": "travail-emploi.gouv.fr / Code du travail numerique",
        "explanation_source": True,
    },
    "contributions": {
        "label": "Code du travail numerique",
        "content_type": "question-reponse pratique",
        "official_origin": "Code du travail numerique",
        "explanation_source": True,
    },
    "infographies": {
        "label": "Code du travail numerique",
        "content_type": "infographie officielle",
        "official_origin": "Code du travail numerique",
        "explanation_source": True,
        "warning": "Infographie: utile pour expliquer, mais le texte disponible par presearch peut contenir peu de detail.",
    },
    "themes": {
        "label": "Code du travail numerique",
        "content_type": "theme de navigation",
        "official_origin": "Code du travail numerique",
        "explanation_source": False,
        "warning": "Theme de navigation: utile pour orienter, mais pas une explication de fond.",
    },
    "outils": {
        "label": "Code du travail numerique",
        "content_type": "outil ou simulateur",
        "official_origin": "Code du travail numerique",
        "explanation_source": False,
        "warning": "Outil: utile pour orienter, mais pas une source explicative directe.",
    },
    "modeles_de_courriers": {
        "label": "Code du travail numerique",
        "content_type": "modele de document",
        "official_origin": "Code du travail numerique",
        "explanation_source": False,
        "warning": "Modele de courrier: utile pour agir, mais pas une explication juridique complete.",
    },
}

SCENARIOS: list[dict[str, str]] = [
    {
        "id": "astreinte_repos",
        "query": "astreinte repos",
        "theme": "Astreinte et repos",
    },
    {
        "id": "heures_supplementaires",
        "query": "heures supplementaires majoration",
        "theme": "Heures supplementaires",
    },
    {
        "id": "travail_dimanche",
        "query": "travail dimanche repos compensateur majoration",
        "theme": "Travail du dimanche",
    },
    {
        "id": "prime_remuneration",
        "query": "prime remuneration salaire variable bulletin",
        "theme": "Prime et remuneration",
    },
    {
        "id": "classification",
        "query": "classification coefficient convention collective fonctions reelles",
        "theme": "Classification professionnelle",
    },
    {
        "id": "cse_temps_reunion",
        "query": "CSE temps de reunion repos",
        "theme": "CSE et temps de reunion",
    },
]


class CdtnError(RuntimeError):
    """Base class for expected CDTN connector failures."""


class CdtnAPIError(CdtnError):
    """Raised when a public CDTN endpoint returns an unusable response."""


@dataclass(frozen=True)
class CdtnConfig:
    api_base_url: str = DEFAULT_API_BASE_URL
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    cache_dir: Path = ROOT / "local-index" / "cdtn"
    cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS

    @classmethod
    def from_env(cls) -> "CdtnConfig":
        timeout = parse_int(os.environ.get(ENV_TIMEOUT), DEFAULT_TIMEOUT_SECONDS)
        cache_ttl = parse_int(os.environ.get(ENV_CACHE_TTL), DEFAULT_CACHE_TTL_SECONDS)
        cache_dir = Path(os.environ.get(ENV_CACHE_DIR) or ROOT / "local-index" / "cdtn")
        return cls(
            api_base_url=(os.environ.get(ENV_API_BASE_URL) or DEFAULT_API_BASE_URL).strip().rstrip("/"),
            timeout_seconds=timeout,
            cache_dir=cache_dir,
            cache_ttl_seconds=cache_ttl,
        )

    def endpoint_url(self, endpoint: str, params: dict[str, Any] | None = None) -> str:
        endpoint = endpoint.strip()
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            url = endpoint
        else:
            if not endpoint.startswith("/"):
                endpoint = "/" + endpoint
            url = self.api_base_url + endpoint
        if params:
            clean_params = {key: value for key, value in params.items() if value not in (None, "")}
            if clean_params:
                url += "?" + urllib.parse.urlencode(clean_params, doseq=True)
        return url


class CdtnClient:
    def __init__(self, config: CdtnConfig | None = None) -> None:
        self.config = config or CdtnConfig.from_env()

    def used_endpoints(self) -> dict[str, str]:
        return {
            "api_base": self.config.api_base_url,
            "presearch": self.config.endpoint_url(PRESEARCH_ENDPOINT),
            "suggest": self.config.endpoint_url(SUGGEST_ENDPOINT),
            "health": self.config.endpoint_url(HEALTH_ENDPOINT),
        }

    def healthcheck(self) -> dict[str, Any]:
        return self._get_json(HEALTH_ENDPOINT)

    def suggest(self, query: str) -> list[str]:
        payload = self._get_json(SUGGEST_ENDPOINT, {"q": compact_text(query)})
        if isinstance(payload, list):
            return [compact_text(item) for item in payload if compact_text(item)]
        raise CdtnAPIError("Reponse /api/suggest inattendue: liste JSON attendue.")

    def presearch(self, query: str) -> dict[str, Any]:
        cleaned_query = compact_text(query)
        if not cleaned_query:
            raise CdtnAPIError("Parametre q vide: /api/presearch exige une question.")
        cache_key = stable_hash({"endpoint": PRESEARCH_ENDPOINT, "query": cleaned_query})
        cached = self.read_response_cache(cache_key)
        if cached is not None:
            return cached
        payload = self._get_json(PRESEARCH_ENDPOINT, {"q": cleaned_query})
        self.write_response_cache(cache_key, payload)
        return payload

    def search_sources(
        self,
        query: str,
        limit: int = DEFAULT_LIMIT,
        theme: str | None = None,
        include_orientation: bool = False,
    ) -> dict[str, Any]:
        cleaned_query = compact_text(query)
        if not cleaned_query:
            return unavailable_result("Question vide: aucune recherche pratique officielle.")
        try:
            payload = self.presearch(cleaned_query)
        except CdtnError as exc:
            return unavailable_result(str(exc), query=cleaned_query)

        hits = payload.get("results")
        if not isinstance(hits, list):
            return unavailable_result("Reponse CDTN sans liste results exploitable.", query=cleaned_query)

        accepted_sources = set(EXPLANATION_SOURCES)
        if include_orientation:
            accepted_sources.update(ORIENTATION_SOURCES)

        normalized: list[dict[str, Any]] = []
        for hit in hits:
            if not isinstance(hit, dict):
                continue
            source_key = compact_text(hit.get("source"))
            if source_key not in accepted_sources:
                continue
            normalized.append(normalize_hit(hit, cleaned_query, theme, self.config.api_base_url))
            if len(dedupe_sources(normalized)) >= max(1, limit):
                break
        normalized = dedupe_sources(normalized)[: max(1, limit)]
        warnings = endpoint_warnings(normalized, include_orientation)
        return {
            "available": True,
            "source_layer": SOURCE_LAYER,
            "endpoint": self.config.endpoint_url(PRESEARCH_ENDPOINT),
            "query": cleaned_query,
            "theme": theme,
            "presearch_class": payload.get("class"),
            "definition": payload.get("definition"),
            "source_count": len(normalized),
            "sources": normalized,
            "warnings": warnings,
            "assessment": assess_result(cleaned_query, normalized),
            "retrieved_at": utc_now(),
        }

    def endpoint_study(self, query: str = "astreinte repos") -> dict[str, Any]:
        result: dict[str, Any] = {
            "ok": False,
            "configuration": safe_configuration(self.config),
            "endpoints": self.used_endpoints(),
            "presearch_contract": {
                "method": "GET",
                "required_parameters": ["q"],
                "optional_parameters_observed": [],
                "authentication": "none",
                "result_limit_observed": 8,
                "content_contract": "short search result metadata only",
            },
        }
        try:
            health = self.healthcheck()
            result["health"] = {
                "ok": bool(health),
                "status": health.get("status"),
                "version": health.get("version"),
            }
        except CdtnError as exc:
            result["health"] = {"ok": False, "error": str(exc)}
        try:
            payload = self.presearch(query)
            hits = payload.get("results") if isinstance(payload, dict) else []
            first = hits[0] if isinstance(hits, list) and hits else {}
            result["presearch_sample"] = {
                "ok": isinstance(hits, list),
                "query": query,
                "top_level_keys": sorted(payload.keys()),
                "result_count": len(hits) if isinstance(hits, list) else 0,
                "first_result_keys": sorted(first.keys()) if isinstance(first, dict) else [],
                "first_result_source": first.get("source") if isinstance(first, dict) else None,
                "first_result_title": first.get("title") if isinstance(first, dict) else None,
            }
        except CdtnError as exc:
            result["presearch_sample"] = {"ok": False, "error": str(exc)}
        result["full_content_access"] = {
            "available_without_scraping": False,
            "tested_public_endpoint": self.config.endpoint_url("/api/items"),
            "observed_status": "404 on /api/items?source=...&slug=...",
            "recommendation": "Use title, description, URL and identifiers only until a stable public content API is documented.",
        }
        result["ok"] = bool(result.get("health", {}).get("ok") and result.get("presearch_sample", {}).get("ok"))
        return result

    def _get_json(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        url = self.config.endpoint_url(endpoint, params)
        request = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:  # noqa: S310
                status = getattr(response, "status", 200)
                body = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            detail = safe_http_error_body(exc)
            raise CdtnAPIError(f"CDTN HTTP {exc.code} sur {endpoint}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise CdtnAPIError(f"Connexion impossible a {endpoint}: {safe_reason(exc)}") from exc
        except TimeoutError as exc:
            raise CdtnAPIError(f"Timeout sur {endpoint}") from exc

        if status >= 400:
            raise CdtnAPIError(f"CDTN HTTP {status} sur {endpoint}")
        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise CdtnAPIError(f"Reponse non JSON sur {endpoint}") from exc

    def response_cache_path(self, cache_key: str) -> Path:
        return self.config.cache_dir / "responses" / f"{cache_key}.json"

    def read_response_cache(self, cache_key: str) -> dict[str, Any] | None:
        path = self.response_cache_path(cache_key)
        if not path.exists():
            return None
        if self.config.cache_ttl_seconds > 0 and time.time() - path.stat().st_mtime > self.config.cache_ttl_seconds:
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def write_response_cache(self, cache_key: str, payload: dict[str, Any]) -> None:
        try:
            path = self.response_cache_path(cache_key)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            return


def normalize_hit(hit: dict[str, Any], query: str, theme: str | None, api_base_url: str) -> dict[str, Any]:
    source_key = compact_text(hit.get("source"))
    profile = SOURCE_PROFILES.get(
        source_key,
        {
            "label": source_key or "Code du travail numerique",
            "content_type": source_key or "contenu pratique",
            "official_origin": "Code du travail numerique",
            "explanation_source": False,
        },
    )
    title = clean_text_value(hit.get("title")) or profile["label"]
    description = clean_text_value(hit.get("description"))
    slug = compact_text(hit.get("slug"))
    cdtn_id = compact_text(hit.get("cdtnId"))
    url = compact_text(hit.get("url")) or build_public_url(api_base_url, source_key, slug, hit)
    breadcrumbs = normalize_breadcrumbs(hit.get("breadcrumbs"))
    updated_at = compact_text(hit.get("date") or hit.get("date_publi"))
    reference = cdtn_id or (f"{source_key}:{slug}" if slug else source_key)
    source_warning = source_quality_warning(profile, description)
    return {
        "document": title,
        "document_type": "explication_pratique_officielle",
        "source_layer": SOURCE_LAYER,
        "source_layer_label": "Explication pratique officielle",
        "title": title,
        "theme": theme or theme_from_breadcrumbs(breadcrumbs),
        "summary": description,
        "explanation": description,
        "contenu_utile": description,
        "excerpt": description,
        "content_type": profile.get("content_type"),
        "source_officielle": profile.get("label"),
        "official_origin": profile.get("official_origin"),
        "source_key": source_key,
        "url": url,
        "url_or_id": url or reference,
        "official_id": reference,
        "reference": reference,
        "cdtn_id": cdtn_id or None,
        "slug": slug or None,
        "updated_at": updated_at or None,
        "retrieved_at": utc_now(),
        "breadcrumbs": breadcrumbs,
        "query": query,
        "score": hit.get("_score"),
        "algo": hit.get("algo"),
        "presearch_class": hit.get("class"),
        "full_content_available": False,
        "content_access": "presearch_description_only",
        "complementarity_with_legifrance": (
            "Aide a comprendre en langage clair; a afficher sous les articles Legifrance, accords, CCN et jurisprudence."
        ),
        "contradiction_risk": (
            "Faible si la couche reste separee; verifier les accords INEOS et textes opposables avant conclusion."
        ),
        "source_quality_warning": source_warning,
        "ranking_reasons": [
            "Resultat issu du endpoint public Code du travail numerique /api/presearch",
            f"Source officielle: {profile.get('label')}",
            "Normalise comme aide pratique, sans remplacer les sources juridiques opposables",
        ],
    }


def source_quality_warning(profile: dict[str, Any], description: str | None) -> str | None:
    warnings = []
    if profile.get("warning"):
        warnings.append(str(profile["warning"]))
    if not description:
        warnings.append("Resultat sans resume exploitable dans /api/presearch.")
    warnings.append("Le corps complet de la fiche n'est pas recupere par une API publique stable dans cette V1.")
    return " ".join(warnings) if warnings else None


def endpoint_warnings(sources: list[dict[str, Any]], include_orientation: bool) -> list[str]:
    warnings = [
        "La couche pratique_officielle explique en langage clair mais ne remplace pas les sources juridiques.",
        "/api/presearch fournit des titres, resumes, URL et identifiants; pas le corps complet stable des fiches.",
    ]
    if not include_orientation:
        warnings.append("Les outils, modeles et themes de navigation sont ecartes par defaut pour eviter de confondre orientation et explication.")
    if not sources:
        warnings.append("Aucun contenu explicatif officiel pertinent n'a ete retenu.")
    return warnings


def build_public_url(api_base_url: str, source_key: str, slug: str, hit: dict[str, Any]) -> str | None:
    if not slug:
        return None
    base = api_base_url.rstrip("/")
    clean_slug = slug.lstrip("/")
    if slug.startswith("/"):
        return base + slug
    if source_key == "fiches_ministere_travail":
        return f"{base}/fiche-ministere-travail/{clean_slug}"
    if source_key == "contributions":
        return f"{base}/contribution/{clean_slug}"
    if source_key == "themes":
        parent_slug = compact_text(hit.get("parentSlug")).lstrip("/")
        if parent_slug:
            return f"{base}/themes/{parent_slug}#{clean_slug}"
        return f"{base}/themes/{clean_slug}"
    if source_key == "modeles_de_courriers":
        return f"{base}/modeles-de-courriers/{clean_slug}"
    if source_key == "outils":
        return f"{base}/outils/{clean_slug}"
    if source_key == "infographies":
        return f"{base}/infographies/{clean_slug}"
    return None


def normalize_breadcrumbs(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    breadcrumbs = []
    for item in value:
        if not isinstance(item, dict):
            continue
        breadcrumbs.append(
            {
                "label": clean_text_value(item.get("label")),
                "position": item.get("position"),
                "slug": compact_text(item.get("slug")),
            }
        )
    return breadcrumbs


def theme_from_breadcrumbs(breadcrumbs: list[dict[str, Any]]) -> str | None:
    labels = [compact_text(item.get("label")) for item in breadcrumbs if compact_text(item.get("label"))]
    return " > ".join(labels) if labels else None


def assess_result(query: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
    if not sources:
        return {
            "relevance": "faible",
            "explanation_capacity": "aucune source pratique retenue",
            "complementarity": "aucune",
            "contradiction_risk": "non evalue",
        }
    avg_score = average_score(sources)
    relevance = "bonne" if avg_score is None or avg_score >= 45 else "moyenne"
    if any(not source.get("summary") for source in sources):
        relevance = "moyenne"
    topic_gap = topic_specific_gap(query, sources)
    if topic_gap:
        relevance = "moyenne"
    return {
        "relevance": relevance,
        "explanation_capacity": "resume court exploitable, pas de corps complet",
        "complementarity": "bonne pour vulgariser; a croiser avec Legifrance, accords, CCN et jurisprudence",
        "contradiction_risk": "maitrise si affichee comme couche pratique distincte",
        "topic_gap": topic_gap,
    }


def average_score(sources: list[dict[str, Any]]) -> float | None:
    scores = [float(source["score"]) for source in sources if isinstance(source.get("score"), (int, float))]
    if not scores:
        return None
    return sum(scores) / len(scores)


def topic_specific_gap(query: str, sources: list[dict[str, Any]]) -> str | None:
    normalized_query = normalize_text(query)
    corpus = " ".join(
        compact_text(source.get("title")) + " " + compact_text(source.get("summary")) for source in sources
    )
    normalized_corpus = normalize_text(corpus)
    if "classification" in normalized_query and not any(
        token in normalized_corpus for token in ["fonctions reelles", "fiche de poste", "coefficient"]
    ):
        return "Resultats utiles pour convention collective/salaire, mais peu centres sur fonctions reellement exercees."
    if "cse" in normalized_query and "repos" in normalized_query and "repos" not in normalized_corpus:
        return "Resultats CSE generaux: la question du temps de reunion pendant repos reste a traiter par Code du travail/jurisprudence."
    return None


def dedupe_sources(sources: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source in sources:
        key = compact_text(source.get("official_id") or source.get("url") or source.get("title"))
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(source)
    return result


def unavailable_result(warning: str, query: str | None = None) -> dict[str, Any]:
    return {
        "available": False,
        "source_layer": SOURCE_LAYER,
        "endpoint": DEFAULT_API_BASE_URL + PRESEARCH_ENDPOINT,
        "query": query,
        "source_count": 0,
        "sources": [],
        "warnings": [warning],
        "assessment": {
            "relevance": "indisponible",
            "explanation_capacity": "indisponible",
            "complementarity": "indisponible",
            "contradiction_risk": "indisponible",
        },
        "retrieved_at": utc_now(),
    }


def command_diagnose(args: argparse.Namespace) -> dict[str, Any]:
    client = CdtnClient()
    payload = client.endpoint_study(args.query)
    payload["notice"] = "Aucun secret n'est utilise par le connecteur CDTN."
    return payload


def command_search(args: argparse.Namespace) -> dict[str, Any]:
    client = CdtnClient()
    return client.search_sources(
        args.query,
        limit=args.limit,
        theme=args.theme,
        include_orientation=args.include_orientation,
    )


def command_suggest(args: argparse.Namespace) -> dict[str, Any]:
    client = CdtnClient()
    try:
        suggestions = client.suggest(args.query)
        return {
            "ok": True,
            "endpoint": client.config.endpoint_url(SUGGEST_ENDPOINT),
            "query": args.query,
            "suggestions": suggestions,
        }
    except CdtnError as exc:
        return {
            "ok": False,
            "endpoint": client.config.endpoint_url(SUGGEST_ENDPOINT),
            "query": args.query,
            "error": str(exc),
        }


def command_run_scenarios(args: argparse.Namespace) -> dict[str, Any]:
    client = CdtnClient()
    rows: list[dict[str, Any]] = []
    for scenario in SCENARIOS:
        result = client.search_sources(
            scenario["query"],
            limit=args.limit,
            theme=scenario["theme"],
            include_orientation=args.include_orientation,
        )
        rows.append(
            {
                "id": scenario["id"],
                "query": scenario["query"],
                "theme": scenario["theme"],
                "ok": bool(result.get("available") and result.get("sources")),
                "source_count": len(result.get("sources", [])),
                "assessment": result.get("assessment"),
                "sources": [safe_source_sample(source) for source in result.get("sources", [])],
                "warnings": result.get("warnings", []),
            }
        )
    return {
        "ok": all(row["ok"] for row in rows),
        "source_layer": SOURCE_LAYER,
        "configuration": safe_configuration(client.config),
        "endpoints": client.used_endpoints(),
        "scenario_results": rows,
        "limits": [
            "Pas de recuperation du corps complet par API publique stable.",
            "La couche pratique doit rester sous les sources juridiques opposables.",
        ],
    }


def safe_configuration(config: CdtnConfig) -> dict[str, Any]:
    return {
        "api_base_url": config.api_base_url,
        "timeout_seconds": config.timeout_seconds,
        "cache_dir": str(config.cache_dir),
        "cache_ttl_seconds": config.cache_ttl_seconds,
        "cache_ignored_by_git": "local-index" in config.cache_dir.parts,
        "uses_secret": False,
    }


def safe_source_sample(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": source.get("title"),
        "source_officielle": source.get("source_officielle"),
        "source_key": source.get("source_key"),
        "content_type": source.get("content_type"),
        "url_or_id": source.get("url_or_id"),
        "summary": short_excerpt(source.get("summary"), 220),
        "full_content_available": source.get("full_content_available"),
        "updated_at": source.get("updated_at"),
        "retrieved_at": source.get("retrieved_at"),
    }


def format_text(payload: dict[str, Any]) -> str:
    if "scenario_results" in payload:
        lines = ["CDTN PRATIQUE OFFICIELLE V1 - TESTS"]
        lines.append(f"Statut : {'OK' if payload.get('ok') else 'ERREUR'}")
        lines.append(f"Endpoint : {payload.get('endpoints', {}).get('presearch')}")
        for row in payload.get("scenario_results", []):
            assessment = row.get("assessment") or {}
            lines.append("")
            lines.append(f"{row.get('id')} - {row.get('theme')}")
            lines.append(f"- sources : {row.get('source_count')}")
            lines.append(f"- pertinence : {assessment.get('relevance')}")
            lines.append(f"- explication : {assessment.get('explanation_capacity')}")
            for source in row.get("sources", [])[:4]:
                lines.append(
                    "- "
                    + " | ".join(
                        compact_text(part)
                        for part in [
                            source.get("source_officielle"),
                            source.get("title"),
                            source.get("summary"),
                            source.get("url_or_id"),
                        ]
                        if compact_text(part)
                    )
                )
        return "\n".join(lines)

    if "presearch_contract" in payload:
        sample = payload.get("presearch_sample") or {}
        full = payload.get("full_content_access") or {}
        lines = [
            "CDTN PRATIQUE OFFICIELLE V1 - DIAGNOSTIC",
            f"Statut : {'OK' if payload.get('ok') else 'ERREUR'}",
            f"Endpoint presearch : {payload.get('endpoints', {}).get('presearch')}",
            "Parametres : q obligatoire",
            f"Cles top-level : {', '.join(sample.get('top_level_keys', []))}",
            f"Cles resultat : {', '.join(sample.get('first_result_keys', []))}",
            f"Contenu complet sans scraping : {'oui' if full.get('available_without_scraping') else 'non'}",
            f"Endpoint contenu teste : {full.get('tested_public_endpoint')}",
            f"Observation : {full.get('observed_status')}",
        ]
        return "\n".join(lines)

    lines = ["CDTN PRATIQUE OFFICIELLE V1 - RECHERCHE"]
    lines.append(f"Question : {payload.get('query')}")
    lines.append(f"Endpoint : {payload.get('endpoint')}")
    lines.append(f"Sources : {payload.get('source_count', len(payload.get('sources', [])))}")
    assessment = payload.get("assessment") or {}
    if assessment:
        lines.append(f"Pertinence : {assessment.get('relevance')}")
        lines.append(f"Explication : {assessment.get('explanation_capacity')}")
    for source in payload.get("sources", []):
        lines.append(
            "- "
            + " | ".join(
                compact_text(part)
                for part in [
                    source.get("source_officielle"),
                    source.get("title"),
                    source.get("summary"),
                    source.get("url_or_id"),
                ]
                if compact_text(part)
            )
        )
    for warning in payload.get("warnings", [])[:4]:
        lines.append(f"Avertissement : {warning}")
    return "\n".join(lines)


def emit(payload: dict[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_text(payload))


def clean_text_value(value: Any) -> str | None:
    if value is None:
        return None
    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def short_excerpt(value: Any, limit: int = 900) -> str:
    text = clean_text_value(value) or ""
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def compact_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_text(value: Any) -> str:
    text = compact_text(clean_text_value(value)).casefold()
    text = unicodedata.normalize("NFKD", text)
    return "".join(char for char in text if not unicodedata.combining(char))


def parse_int(value: str | None, default: int) -> int:
    try:
        parsed = int(str(value or "").strip())
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_reason(exc: urllib.error.URLError) -> str:
    reason = getattr(exc, "reason", exc)
    return str(reason).replace("\n", " ")[:240]


def safe_http_error_body(exc: urllib.error.HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8", errors="replace")
    except OSError:
        return exc.reason
    return compact_text(body)[:240] or exc.reason


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CFDT Nexus - connecteur Code du travail numerique")
    sub = parser.add_subparsers(dest="command", required=True)

    diagnose = sub.add_parser("diagnose")
    diagnose.add_argument("--query", default="astreinte repos")
    diagnose.add_argument("--format", choices=["text", "json"], default="text")

    suggest = sub.add_parser("suggest")
    suggest.add_argument("--query", required=True)
    suggest.add_argument("--format", choices=["text", "json"], default="text")

    search = sub.add_parser("search")
    search.add_argument("--query", required=True)
    search.add_argument("--theme")
    search.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    search.add_argument("--include-orientation", action="store_true")
    search.add_argument("--format", choices=["text", "json"], default="text")

    scenarios = sub.add_parser("run-scenarios")
    scenarios.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    scenarios.add_argument("--include-orientation", action="store_true")
    scenarios.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "diagnose":
        emit(command_diagnose(args), args.format)
    elif args.command == "suggest":
        emit(command_suggest(args), args.format)
    elif args.command == "search":
        emit(command_search(args), args.format)
    elif args.command == "run-scenarios":
        emit(command_run_scenarios(args), args.format)
    else:
        raise SystemExit(f"Commande inconnue: {args.command}")


if __name__ == "__main__":
    main()
