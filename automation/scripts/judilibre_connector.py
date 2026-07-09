#!/usr/bin/env python
"""PISTE / JUDILIBRE connector for official court decisions.

This connector is intentionally separate from the Legifrance connector. It uses
the same OAuth application credentials by default, stores only local private
cache files under local-index/judilibre/, and never prints credentials or tokens.
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

ENV_CLIENT_ID = "CFDT_NEXUS_JUDILIBRE_CLIENT_ID"
ENV_CLIENT_SECRET = "CFDT_NEXUS_JUDILIBRE_CLIENT_SECRET"
FALLBACK_ENV_CLIENT_ID = "CFDT_NEXUS_LEGIFRANCE_CLIENT_ID"
FALLBACK_ENV_CLIENT_SECRET = "CFDT_NEXUS_LEGIFRANCE_CLIENT_SECRET"
ENV_TOKEN_URL = "CFDT_NEXUS_JUDILIBRE_TOKEN_URL"
ENV_API_BASE_URL = "CFDT_NEXUS_JUDILIBRE_API_BASE_URL"
ENV_SCOPE = "CFDT_NEXUS_JUDILIBRE_SCOPE"
ENV_TIMEOUT = "CFDT_NEXUS_JUDILIBRE_TIMEOUT"
ENV_CACHE_DIR = "CFDT_NEXUS_JUDILIBRE_CACHE_DIR"
ENV_CACHE_TTL = "CFDT_NEXUS_JUDILIBRE_CACHE_TTL_SECONDS"

DEFAULT_TOKEN_URL = "https://oauth.piste.gouv.fr/api/oauth/token"
DEFAULT_API_BASE_URL = "https://api.piste.gouv.fr/cassation/judilibre/v1.0"
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_CACHE_TTL_SECONDS = 24 * 60 * 60
DEFAULT_SCOPE = "openid"
JUDILIBRE_LABEL = "JUDILIBRE"
DEFENSE_DEFAULT_LIMIT = 2
DEFENSE_MIN_SCORE = 34

SCENARIOS: list[dict[str, str]] = [
    {"id": "astreinte_repos", "query": "astreinte repos", "theme": "Astreinte et repos"},
    {
        "id": "temps_travail_effectif",
        "query": "temps de travail effectif",
        "theme": "Temps de travail effectif",
    },
    {
        "id": "heures_supplementaires",
        "query": "heures supplementaires",
        "theme": "Heures supplementaires",
    },
    {
        "id": "classification_fonctions_reelles",
        "query": "classification fonctions reelles",
        "theme": "Classification et fonctions reelles",
    },
    {
        "id": "prime_salaire_variable",
        "query": "prime salaire variable",
        "theme": "Prime et salaire variable",
    },
    {
        "id": "cse_temps_reunion",
        "query": "CSE temps de reunion",
        "theme": "CSE et temps de reunion",
    },
]


class JudilibreError(RuntimeError):
    """Base class for expected JUDILIBRE connector failures."""


class JudilibreConfigurationError(JudilibreError):
    """Raised when credentials or endpoint configuration are missing."""


class JudilibreAPIError(JudilibreError):
    """Raised when PISTE / JUDILIBRE returns an unusable response."""


@dataclass(frozen=True)
class JudilibreConfig:
    client_id: str | None
    client_secret: str | None
    token_url: str = DEFAULT_TOKEN_URL
    api_base_url: str = DEFAULT_API_BASE_URL
    scope: str = DEFAULT_SCOPE
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    cache_dir: Path = ROOT / "local-index" / "judilibre"
    cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS
    client_id_source: str | None = None
    client_secret_source: str | None = None

    @classmethod
    def from_env(cls) -> "JudilibreConfig":
        client_id, client_id_source = read_config_value(ENV_CLIENT_ID, FALLBACK_ENV_CLIENT_ID)
        client_secret, client_secret_source = read_config_value(ENV_CLIENT_SECRET, FALLBACK_ENV_CLIENT_SECRET)
        timeout = parse_int(os.environ.get(ENV_TIMEOUT), DEFAULT_TIMEOUT_SECONDS)
        cache_ttl = parse_int(os.environ.get(ENV_CACHE_TTL), DEFAULT_CACHE_TTL_SECONDS)
        cache_dir = Path(os.environ.get(ENV_CACHE_DIR) or ROOT / "local-index" / "judilibre")
        return cls(
            client_id=client_id,
            client_secret=client_secret,
            token_url=os.environ.get(ENV_TOKEN_URL, DEFAULT_TOKEN_URL).strip(),
            api_base_url=os.environ.get(ENV_API_BASE_URL, DEFAULT_API_BASE_URL).strip().rstrip("/"),
            scope=clean_env(os.environ.get(ENV_SCOPE)) or DEFAULT_SCOPE,
            timeout_seconds=timeout,
            cache_dir=cache_dir,
            cache_ttl_seconds=cache_ttl,
            client_id_source=client_id_source,
            client_secret_source=client_secret_source,
        )

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    @property
    def missing_variables(self) -> list[str]:
        missing = []
        if not self.client_id:
            missing.append(f"{ENV_CLIENT_ID} ou {FALLBACK_ENV_CLIENT_ID}")
        if not self.client_secret:
            missing.append(f"{ENV_CLIENT_SECRET} ou {FALLBACK_ENV_CLIENT_SECRET}")
        return missing

    def endpoint_url(self, endpoint: str) -> str:
        endpoint = endpoint.strip()
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        return self.api_base_url + endpoint


def read_config_value(primary: str, fallback: str) -> tuple[str | None, str | None]:
    value = clean_env(os.environ.get(primary))
    if value:
        return value, primary
    value = clean_env(os.environ.get(fallback))
    if value:
        return value, fallback
    return None, None


def clean_env(value: str | None) -> str | None:
    cleaned = (value or "").strip()
    return cleaned or None


def parse_int(value: str | None, default: int) -> int:
    try:
        parsed = int(str(value or "").strip())
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class JudilibreClient:
    def __init__(self, config: JudilibreConfig | None = None) -> None:
        self.config = config or JudilibreConfig.from_env()

    @property
    def token_cache_path(self) -> Path:
        return self.config.cache_dir / "oauth-token.private.json"

    @property
    def response_cache_path(self) -> Path:
        return self.config.cache_dir / "responses.private.json"

    def ensure_configured(self) -> None:
        if not self.config.configured:
            missing = ", ".join(self.config.missing_variables)
            raise JudilibreConfigurationError(
                f"Connecteur JUDILIBRE non configure: variable(s) manquante(s) {missing}."
            )

    def authenticate(self, force_refresh: bool = False) -> dict[str, Any]:
        self.ensure_configured()
        if not force_refresh:
            cached = self._read_token_cache()
            if cached and float(cached.get("expires_at", 0)) > time.time() + 60:
                return {**cached, "from_cache": True}

        assert self.config.client_id is not None
        assert self.config.client_secret is not None
        form = {
            "grant_type": "client_credentials",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "scope": self.config.scope or DEFAULT_SCOPE,
        }
        request = urllib.request.Request(
            self.config.token_url,
            data=urllib.parse.urlencode(form).encode("utf-8"),
            headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:  # noqa: S310
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise JudilibreAPIError(f"OAuth JUDILIBRE refuse: HTTP {exc.code} {exc.reason}.") from exc
        except urllib.error.URLError as exc:
            raise JudilibreAPIError(f"OAuth JUDILIBRE indisponible: {safe_reason(exc)}.") from exc
        except json.JSONDecodeError as exc:
            raise JudilibreAPIError("OAuth JUDILIBRE: reponse JSON illisible.") from exc

        token = payload.get("access_token")
        if not token:
            raise JudilibreAPIError("OAuth JUDILIBRE: access_token absent de la reponse.")
        expires_in = int(payload.get("expires_in") or 3600)
        cached = {
            "access_token": token,
            "token_type": payload.get("token_type") or "Bearer",
            "expires_in": expires_in,
            "expires_at": time.time() + max(60, expires_in - 60),
            "created_at": utc_now(),
            "from_cache": False,
        }
        self._write_token_cache(cached)
        return cached

    def auth_diagnostic(self, force_refresh: bool = False) -> dict[str, Any]:
        token = self.authenticate(force_refresh=force_refresh)
        return {
            "ok": True,
            "token_type": token.get("token_type"),
            "expires_in": token.get("expires_in"),
            "from_cache": bool(token.get("from_cache")),
        }

    def healthcheck(self) -> dict[str, Any]:
        return self._get_json("/healthcheck")

    def search_decision_hits(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        cleaned_query = (query or "").strip()
        if not cleaned_query:
            return []
        page_size = max(1, min(limit, 10))
        cache_key = self._cache_key("search", {"query": cleaned_query, "page_size": page_size})
        cached = self._read_response_cache(cache_key)
        if cached is not None:
            return cached
        if not self.config.configured:
            cached_by_query = self._find_cached_search_by_query(cleaned_query)
            if cached_by_query is not None:
                return cached_by_query[:page_size]

        payload = self._get_json("/search", {"query": cleaned_query, "page_size": page_size})
        hits = payload.get("results") if isinstance(payload, dict) else []
        if not isinstance(hits, list):
            raise JudilibreAPIError("JUDILIBRE search: champ results absent ou invalide.")
        normalized = [normalize_search_hit(hit, cleaned_query) for hit in hits if isinstance(hit, dict)]
        normalized = [hit for hit in normalized if hit.get("official_id")]
        self._write_response_cache(cache_key, normalized)
        return normalized

    def decision_source(self, decision_id: str, search_hit: dict[str, Any] | None = None) -> dict[str, Any]:
        cleaned_id = (decision_id or "").strip()
        if not cleaned_id:
            raise JudilibreAPIError("Identifiant de decision JUDILIBRE absent.")
        cache_key = self._cache_key("decision", {"id": cleaned_id})
        cached = self._read_response_cache(cache_key)
        if cached is not None:
            return merge_search_context(cached, search_hit)

        payload = self._get_json("/decision", {"id": cleaned_id})
        source = normalize_decision_payload(payload, search_hit)
        self._write_response_cache(cache_key, source)
        return source

    def search_sources(self, query: str, limit: int = DEFENSE_DEFAULT_LIMIT, theme: str | None = None) -> dict[str, Any]:
        try:
            retention_limit = max(1, min(limit, DEFENSE_DEFAULT_LIMIT))
            hits = self.search_decision_hits(query, limit=max(retention_limit * 4, 6))
            candidates: list[dict[str, Any]] = []
            warnings: list[str] = []
            for hit in hits:
                if theme and not hit.get("theme"):
                    hit["theme"] = theme
                try:
                    candidates.append(self.decision_source(str(hit["official_id"]), hit))
                except JudilibreError as exc:
                    warnings.append(str(exc))
                    candidates.append(hit)
            if not hits:
                warnings.append("JUDILIBRE: aucune decision remontee pour cette recherche.")
            selected = select_defense_decisions(candidates, query, theme, retention_limit)
            if any(source.get("cache_stale") for source in candidates):
                warnings.append(
                    "JUDILIBRE: decisions issues du cache local officiel car l'API n'est pas configuree dans ce processus."
                )
            if candidates and not selected["retained"]:
                warnings.append("JUDILIBRE: aucune decision juridiquement assez proche n'a ete retenue.")
            return {
                "available": True,
                "sources": selected["retained"],
                "rejected_sources": selected["rejected"],
                "candidate_count": len(candidates),
                "warnings": warnings,
                "search_hits": len(hits),
                "query": query,
                "theme": theme,
                "endpoints": self.used_endpoints(),
            }
        except JudilibreError as exc:
            return {
                "available": False,
                "sources": [],
                "rejected_sources": [],
                "candidate_count": 0,
                "warnings": [str(exc)],
                "search_hits": 0,
                "query": query,
                "theme": theme,
                "endpoints": self.used_endpoints(),
            }

    def test_connection(self, query: str = "temps de travail", limit: int = 1) -> dict[str, Any]:
        result: dict[str, Any] = {
            "ok": False,
            "configuration": safe_configuration(self.config),
            "endpoints": self.used_endpoints(),
            "steps": {},
        }
        result["steps"]["oauth"] = self.auth_diagnostic(force_refresh=False)
        health = self.healthcheck()
        result["steps"]["healthcheck"] = {"ok": bool(health), "keys": list(health.keys())[:8]}
        hits = self.search_decision_hits(query, limit=limit)
        result["steps"]["search"] = {"ok": bool(hits), "query": query, "hit_count": len(hits)}
        if hits:
            source = self.decision_source(str(hits[0]["official_id"]), hits[0])
            result["steps"]["decision"] = {
                "ok": bool(source.get("decision_text_length")),
                "official_id": source.get("official_id"),
                "text_length": source.get("decision_text_length"),
            }
            result["source_sample"] = safe_source_sample(source)
        result["ok"] = all(step.get("ok", False) for step in result["steps"].values())
        return result

    def used_endpoints(self) -> dict[str, str]:
        return {
            "oauth_token": self.config.token_url,
            "api_base": self.config.api_base_url,
            "healthcheck": self.config.endpoint_url("/healthcheck"),
            "search": self.config.endpoint_url("/search"),
            "decision": self.config.endpoint_url("/decision"),
        }

    def _get_json(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        token = self.authenticate()
        url = self.config.endpoint_url(endpoint)
        if params:
            clean_params = {key: value for key, value in params.items() if value not in (None, "")}
            url = url + "?" + urllib.parse.urlencode(clean_params, doseq=True)
        request = urllib.request.Request(
            url,
            headers={
                "Authorization": f"{token.get('token_type') or 'Bearer'} {token['access_token']}",
                "Accept": "application/json",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:  # noqa: S310
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise JudilibreAPIError(f"API JUDILIBRE refuse: HTTP {exc.code} {exc.reason}.") from exc
        except urllib.error.URLError as exc:
            raise JudilibreAPIError(f"API JUDILIBRE indisponible: {safe_reason(exc)}.") from exc
        except json.JSONDecodeError as exc:
            raise JudilibreAPIError("API JUDILIBRE: reponse JSON illisible.") from exc

    def _read_token_cache(self) -> dict[str, Any] | None:
        return read_json_file(self.token_cache_path)

    def _write_token_cache(self, payload: dict[str, Any]) -> None:
        write_json_file(self.token_cache_path, payload)

    def _cache_key(self, kind: str, payload: dict[str, Any]) -> str:
        raw = json.dumps({"kind": kind, "payload": payload}, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _read_response_cache(self, key: str) -> Any | None:
        cache = read_json_file(self.response_cache_path) or {}
        item = cache.get(key)
        if not item:
            return None
        if float(item.get("expires_at", 0)) <= time.time():
            if self.config.configured:
                return None
            return mark_stale_cache(item.get("value"), item)
        return mark_fresh_cache(item.get("value"), item)

    def _write_response_cache(self, key: str, value: Any) -> None:
        cache = read_json_file(self.response_cache_path) or {}
        cache[key] = {
            "expires_at": time.time() + self.config.cache_ttl_seconds,
            "stored_at": utc_now(),
            "value": value,
        }
        write_json_file(self.response_cache_path, cache)

    def _find_cached_search_by_query(self, query: str) -> list[dict[str, Any]] | None:
        cache = read_json_file(self.response_cache_path) or {}
        normalized_query = normalize_text(query)
        matches: list[tuple[str, list[dict[str, Any]]]] = []
        for item in cache.values():
            value = item.get("value") if isinstance(item, dict) else None
            if not isinstance(value, list):
                continue
            first_query = None
            for entry in value:
                if isinstance(entry, dict) and entry.get("query"):
                    first_query = entry.get("query")
                    break
            if normalize_text(first_query) != normalized_query:
                continue
            marked = mark_stale_cache(value, item)
            if isinstance(marked, list):
                matches.append((str(item.get("stored_at") or ""), marked))
        if not matches:
            return None
        matches.sort(key=lambda row: row[0], reverse=True)
        return matches[0][1]


def normalize_search_hit(hit: dict[str, Any], query: str) -> dict[str, Any]:
    official_id = clean_text_value(hit.get("id"))
    source = base_source(hit, official_id, query)
    source["excerpt"] = short_excerpt(excerpt_from_hit(hit))
    source["decision_text_length"] = 0
    source["source_quality_warning"] = "Decision reperee par recherche JUDILIBRE, texte complet non encore recupere."
    return source


def normalize_decision_payload(payload: dict[str, Any], search_hit: dict[str, Any] | None = None) -> dict[str, Any]:
    official_id = clean_text_value(payload.get("id")) or clean_text_value((search_hit or {}).get("official_id"))
    source = base_source(payload, official_id, (search_hit or {}).get("query"))
    for key in ["score", "theme", "summary", "excerpt"]:
        if not source.get(key) and (search_hit or {}).get(key):
            source[key] = (search_hit or {}).get(key)
    text = clean_text_value(payload.get("text"))
    summary = clean_text_value(payload.get("summary")) or clean_text_value((search_hit or {}).get("summary"))
    summary_missing = not summary
    if summary_missing:
        summary = "Resume officiel non fourni par JUDILIBRE pour cette decision: lire l'extrait et le texte complet."
    source["summary"] = short_excerpt(summary, 700)
    source["resume_court"] = source["summary"]
    source["principle_summary"] = source["summary"]
    source["excerpt"] = short_excerpt(text or source.get("excerpt") or summary)
    source["decision_text_length"] = len(text or "")
    warnings = []
    if summary_missing:
        warnings.append("Resume officiel absent de la reponse JUDILIBRE.")
    if not text:
        warnings.append("Texte complet absent de la reponse JUDILIBRE.")
    source["source_quality_warning"] = " ".join(warnings) or None
    return source


def base_source(payload: dict[str, Any], official_id: str | None, query: str | None = None) -> dict[str, Any]:
    chamber = normalize_chamber(clean_text_value(payload.get("chamber")))
    jurisdiction = normalize_jurisdiction(clean_text_value(payload.get("jurisdiction")))
    decision_date = clean_text_value(payload.get("decision_date"))
    case_number = clean_case_number(payload.get("number") or payload.get("numbers"))
    theme = best_theme(payload)
    document = ", ".join(part for part in [jurisdiction, chamber, decision_date, case_number] if part)
    return {
        "document": document or JUDILIBRE_LABEL,
        "document_type": "jurisprudence",
        "source_layer": "jurisprudence",
        "source_layer_label": "Jurisprudence",
        "juridiction": jurisdiction,
        "chamber": chamber,
        "decision_date": decision_date,
        "case_number": case_number,
        "theme": theme,
        "summary": short_excerpt(clean_text_value(payload.get("summary")), 700),
        "resume_court": short_excerpt(clean_text_value(payload.get("summary")), 700),
        "solution": clean_text_value(payload.get("solution")),
        "publication": clean_text_value(payload.get("publication")),
        "decision_type": clean_text_value(payload.get("type")),
        "article": f"pourvoi {case_number}" if case_number else None,
        "article_or_section": f"pourvoi {case_number}" if case_number else None,
        "official_id": official_id,
        "judilibre_id": official_id,
        "retrieved_at": utc_now(),
        "url": f"https://www.courdecassation.fr/decision/{official_id}" if official_id else None,
        "chunk_id": official_id,
        "score": payload.get("score"),
        "query": query,
        "ranking_reasons": [
            "Source officielle JUDILIBRE via API PISTE",
            "Recherche par mots-cles",
        ],
    }


def merge_search_context(source: dict[str, Any], search_hit: dict[str, Any] | None) -> dict[str, Any]:
    if not search_hit:
        return source
    merged = dict(source)
    for key in ["score", "theme", "query"]:
        if not merged.get(key) and search_hit.get(key):
            merged[key] = search_hit[key]
    if not merged.get("ranking_reasons"):
        merged["ranking_reasons"] = search_hit.get("ranking_reasons", [])
    return merged


def mark_fresh_cache(value: Any, item: dict[str, Any]) -> Any:
    return mark_cache_value(value, item, stale=False)


def mark_stale_cache(value: Any, item: dict[str, Any]) -> Any:
    return mark_cache_value(value, item, stale=True)


def mark_cache_value(value: Any, item: dict[str, Any], stale: bool) -> Any:
    stored_at = item.get("stored_at")
    if isinstance(value, list):
        return [mark_cache_value(entry, item, stale) if isinstance(entry, dict) else entry for entry in value]
    if isinstance(value, dict):
        marked = dict(value)
        marked["cache_stale"] = stale
        marked["cache_stored_at"] = stored_at
        marked["cache_source"] = "local-index/judilibre/responses.private.json"
        return marked
    return value


def select_defense_decisions(
    candidates: list[dict[str, Any]],
    query: str,
    theme: str | None,
    limit: int,
) -> dict[str, list[dict[str, Any]]]:
    scored: list[dict[str, Any]] = []
    for index, source in enumerate(candidates, start=1):
        audit = defense_relevance(source, query, theme)
        scored.append(enrich_decision_for_defense(source, audit, index))

    scored = sorted(
        scored,
        key=lambda item: (
            float(item.get("jurisprudence_relevance_score") or 0),
            str(item.get("decision_date") or ""),
        ),
        reverse=True,
    )
    retained: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source in scored:
        official_id = str(source.get("official_id") or source.get("judilibre_id") or "").strip()
        if official_id and official_id in seen:
            source["exclusion_reason"] = "doublon de decision deja retenue ou analysee"
            rejected.append(safe_rejected_source(source))
            continue
        if source.get("defense_retained") and len(retained) < limit:
            retained.append(source)
            if official_id:
                seen.add(official_id)
        else:
            if not source.get("exclusion_reason"):
                source["exclusion_reason"] = (
                    "decision moins utile que les decisions retenues pour cette question"
                    if len(retained) >= limit
                    else "pertinence metier insuffisante"
                )
            rejected.append(safe_rejected_source(source))
    return {"retained": retained, "rejected": rejected}


def defense_relevance(source: dict[str, Any], query: str, theme: str | None) -> dict[str, Any]:
    profile = query_profile(query, theme)
    text = decision_context_text(source)
    title = normalize_text(source.get("document"))
    summary_text = normalize_text(
        " ".join(
            str(source.get(key) or "")
            for key in ["summary", "resume_court", "principle_summary", "solution", "excerpt", "theme"]
        )
    )
    score = 0
    reasons: list[str] = []
    limits: list[str] = []

    notion_hits = [term for term in profile["notions"] if term in text]
    fact_hits = [term for term in profile["facts"] if term in text]
    dispute_hits = [term for term in profile["litige"] if term in text]
    if notion_hits:
        score += min(28, len(notion_hits) * 9)
        reasons.append("meme notion juridique: " + ", ".join(notion_hits[:4]))
    if fact_hits:
        score += min(22, len(fact_hits) * 7)
        reasons.append("faits proches: " + ", ".join(fact_hits[:4]))
    if dispute_hits:
        score += min(18, len(dispute_hits) * 6)
        reasons.append("type de litige proche: " + ", ".join(dispute_hits[:3]))
    if profile["core"] and any(term in title or term in summary_text for term in profile["core"]):
        score += 12
        reasons.append("question juridique proche du coeur du dossier")

    chamber = normalize_text(source.get("chamber"))
    if "social" in chamber:
        score += 8
        reasons.append("chambre sociale")
    else:
        limits.append("chambre non sociale ou non determinee")

    case_number = clean_text_value(source.get("case_number"))
    if case_number:
        score += 6
        reasons.append("numero de pourvoi present")
    else:
        limits.append("numero de pourvoi absent")

    year = decision_year(source.get("decision_date"))
    if year is None:
        limits.append("date non determinee")
    elif year >= 2010:
        score += 6
        reasons.append(f"decision recente ou encore utile a verifier: {year}")
    elif year >= 2000:
        score += 2
        limits.append(f"decision ancienne a contextualiser: {year}")
    else:
        score -= 4
        limits.append(f"decision tres ancienne a justifier avant utilisation: {year}")

    if has_exploitable_solution(source):
        score += 10
        reasons.append("solution ou resume exploitable")
    else:
        score -= 12
        limits.append("solution non identifiable dans les donnees disponibles")

    if source.get("decision_text_length"):
        score += 5
        reasons.append("texte complet recupere")
    else:
        limits.append("texte complet non disponible dans cette reponse")

    official_id = clean_text_value(source.get("official_id") or source.get("judilibre_id"))
    if not official_id:
        score -= 20
        limits.append("identifiant officiel absent")

    retained = score >= DEFENSE_MIN_SCORE and bool(official_id) and has_exploitable_solution(source)
    exclusion = None if retained else "; ".join(limits[:3]) or "pertinence metier insuffisante"
    return {
        "score": round(score, 2),
        "retained": retained,
        "reasons": unique_text(reasons, limit=8),
        "limits": unique_text(limits, limit=8),
        "exclusion_reason": exclusion,
        "profile": profile,
    }


def enrich_decision_for_defense(source: dict[str, Any], audit: dict[str, Any], candidate_rank: int) -> dict[str, Any]:
    enriched = dict(source)
    profile = audit.get("profile") or {}
    excerpt = short_excerpt(
        source.get("summary")
        or source.get("resume_court")
        or source.get("principle_summary")
        or source.get("solution")
        or source.get("excerpt"),
        700,
    )
    non_determined = "non determine a partir des donnees disponibles"
    enriched.update(
        {
            "candidate_rank": candidate_rank,
            "jurisprudence_relevance_score": audit["score"],
            "defense_retained": audit["retained"],
            "selection_reasons": audit["reasons"],
            "selection_limits": audit["limits"],
            "exclusion_reason": audit["exclusion_reason"],
            "question_juridique": profile.get("question") or non_determined,
            "faits_utiles": source.get("faits_utiles") or non_determined,
            "position_salarie_representants": source.get("position_salarie_representants") or non_determined,
            "position_employeur": source.get("position_employeur") or non_determined,
            "solution_retenue": decision_solution_text(source, excerpt) or non_determined,
            "principe_apport_utile": excerpt or non_determined,
            "ressemblance_avec_dossier": defense_similarity(profile, audit),
            "difference_avec_dossier": defense_differences(audit),
            "utilite_defense": defense_use(profile, audit),
            "limite_utilisation": defense_limit(source, audit),
        }
    )
    ranking = list(enriched.get("ranking_reasons") or [])
    ranking.extend(audit["reasons"])
    if audit["limits"]:
        ranking.append("Limites selection: " + "; ".join(audit["limits"][:3]))
    enriched["ranking_reasons"] = unique_text(ranking, limit=10)
    return enriched


def safe_rejected_source(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "official_id": source.get("official_id") or source.get("judilibre_id"),
        "document": source.get("document"),
        "juridiction": source.get("juridiction"),
        "chamber": source.get("chamber"),
        "decision_date": source.get("decision_date"),
        "case_number": source.get("case_number"),
        "theme": source.get("theme"),
        "jurisprudence_relevance_score": source.get("jurisprudence_relevance_score"),
        "exclusion_reason": source.get("exclusion_reason"),
        "selection_reasons": source.get("selection_reasons", []),
    }


def decision_solution_text(source: dict[str, Any], excerpt: str | None) -> str | None:
    solution = clean_text_value(source.get("solution"))
    if solution and len(solution) > 30:
        return solution
    if solution and excerpt:
        return f"{solution}: {excerpt}"
    return solution or excerpt


def query_profile(query: str, theme: str | None = None) -> dict[str, Any]:
    text = normalize_text(f"{query} {theme or ''}")
    profiles = [
        (
            "astreinte",
            {
                "question": "Effets d'une intervention d'astreinte sur le repos, le temps de travail et la remuneration.",
                "core": ["astreinte"],
                "notions": ["astreinte", "intervention", "temps de travail effectif", "repos"],
                "facts": ["nuit", "intervention", "repos", "reprise", "appel"],
                "litige": ["salaire", "remuneration", "heures supplementaires", "repos compensateur"],
            },
        ),
        (
            "sanction",
            {
                "question": "Preuve de la faute, procedure disciplinaire et proportionnalite de la sanction.",
                "core": ["sanction", "disciplinaire", "faute"],
                "notions": ["sanction", "disciplinaire", "faute", "procedure", "entretien prealable"],
                "facts": ["erreur", "formation", "consigne", "procedure", "preuve"],
                "litige": ["licenciement", "mise a pied", "avertissement", "grief"],
            },
        ),
        (
            "classification",
            {
                "question": "Comparaison entre fonctions reellement exercees, qualification et classification applicable.",
                "core": ["classification", "qualification", "fonctions"],
                "notions": ["classification", "coefficient", "qualification", "fonctions", "emploi"],
                "facts": ["fonctions", "responsabilite", "autonomie", "fiche de poste", "emploi occupe"],
                "litige": ["rappel de salaire", "classification", "coefficient"],
            },
        ),
        (
            "cse",
            {
                "question": "Droits d'information-consultation du CSE et preuve des impacts collectifs.",
                "core": ["cse", "consultation", "information"],
                "notions": ["cse", "comite social", "consultation", "information", "reorganisation"],
                "facts": ["suppression de poste", "horaires", "conditions de travail", "reorganisation", "effectif"],
                "litige": ["consultation", "expertise", "entrave", "information"],
            },
        ),
        (
            "prime",
            {
                "question": "Droit au paiement d'une prime, d'une remuneration variable ou d'heures dues.",
                "core": ["prime", "salaire", "remuneration", "heures supplementaires"],
                "notions": ["prime", "salaire", "remuneration", "variable", "heures supplementaires", "majoration"],
                "facts": ["bulletin", "objectif", "temps de travail", "pointage", "paiement"],
                "litige": ["rappel de salaire", "paiement", "creance salariale"],
            },
        ),
    ]
    for marker, profile in profiles:
        if marker in text or any(term in text for term in profile["core"]):
            return profile
    terms = significant_terms(text)
    return {
        "question": "Portee utile de la decision pour le dossier Nexus.",
        "core": terms[:4],
        "notions": terms[:6],
        "facts": terms[:6],
        "litige": terms[:4],
    }


def decision_context_text(source: dict[str, Any]) -> str:
    return normalize_text(
        " ".join(
            str(source.get(key) or "")
            for key in [
                "document",
                "theme",
                "summary",
                "resume_court",
                "principle_summary",
                "solution",
                "excerpt",
                "decision_type",
                "publication",
                "chamber",
                "query",
            ]
        )
    )


def has_exploitable_solution(source: dict[str, Any]) -> bool:
    marker = "resume officiel non fourni"
    values = [
        clean_text_value(source.get("solution")),
        clean_text_value(source.get("summary")),
        clean_text_value(source.get("resume_court")),
        clean_text_value(source.get("principle_summary")),
        clean_text_value(source.get("excerpt")),
    ]
    return any(value and len(value) >= 80 and marker not in normalize_text(value) for value in values)


def decision_year(value: Any) -> int | None:
    match = re.search(r"(19|20)\d{2}", str(value or ""))
    return int(match.group(0)) if match else None


def defense_similarity(profile: dict[str, Any], audit: dict[str, Any]) -> list[str]:
    values = []
    if audit.get("reasons"):
        values.extend(str(reason) for reason in audit["reasons"][:3])
    if not values and profile.get("question"):
        values.append("Question rapprochee: " + str(profile["question"]))
    return values or ["non determine a partir des donnees disponibles"]


def defense_differences(audit: dict[str, Any]) -> list[str]:
    values = list(audit.get("limits") or [])
    values.append("Comparer les faits exacts de la decision avec les pieces du dossier Nexus avant utilisation.")
    return unique_text(values, limit=5)


def defense_use(profile: dict[str, Any], audit: dict[str, Any]) -> str:
    question = str(profile.get("question") or "le dossier")
    if audit.get("retained"):
        return (
            "Appui prudent: utiliser cette decision pour comparer les faits et soutenir l'argumentation sur "
            + question
        )
    return "Decision non retenue comme appui principal de defense."


def defense_limit(source: dict[str, Any], audit: dict[str, Any]) -> str:
    limits = list(audit.get("limits") or [])
    if source.get("cache_stale"):
        limits.append("decision lue depuis le cache local: verifier la version live JUDILIBRE avant production externe")
    if not limits:
        limits.append("decision isolee: ne pas la presenter comme jurisprudence constante sans verification complementaire")
    return "; ".join(unique_text(limits, limit=4))


def significant_terms(text: str) -> list[str]:
    stopwords = {
        "avec",
        "dans",
        "pour",
        "apres",
        "avant",
        "comme",
        "comment",
        "quels",
        "quelle",
        "salari",
        "salarie",
        "employeur",
        "direction",
        "travail",
    }
    terms = re.split(r"[^a-z0-9]+", normalize_text(text))
    return [term for term in dict.fromkeys(terms) if len(term) >= 4 and term not in stopwords]


def unique_text(values: Iterable[Any], limit: int | None = None) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        key = normalize_text(text)
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
        if limit is not None and len(result) >= limit:
            break
    return result


def excerpt_from_hit(hit: dict[str, Any]) -> str:
    highlights = clean_text_value(hit.get("highlights"))
    if highlights:
        return highlights
    summary = clean_text_value(hit.get("summary"))
    if summary:
        return summary
    titles = clean_text_value(hit.get("titlesAndSummaries"))
    if titles:
        return titles
    return clean_text_value(hit) or ""


def best_theme(payload: dict[str, Any]) -> str | None:
    themes = clean_text_value(payload.get("themes"))
    if themes:
        return short_excerpt(themes, 240)
    files = clean_text_value(payload.get("files"))
    if files:
        return short_excerpt(files, 240)
    return None


def normalize_jurisdiction(value: str | None) -> str | None:
    normalized = normalize_text(value)
    if normalized == "cc":
        return "Cour de cassation"
    if normalized == "ca":
        return "Cour d'appel"
    if value:
        return value
    return None


def normalize_chamber(value: str | None) -> str | None:
    normalized = normalize_text(value)
    labels = {
        "soc": "Chambre sociale",
        "cr": "Chambre criminelle",
        "civ1": "Premiere chambre civile",
        "civ2": "Deuxieme chambre civile",
        "civ3": "Troisieme chambre civile",
        "comm": "Chambre commerciale",
    }
    return labels.get(normalized, value)


def clean_case_number(value: Any) -> str | None:
    if isinstance(value, list):
        values = [clean_text_value(item) for item in value]
        return " ".join(item for item in values if item) or None
    return clean_text_value(value)


def clean_text_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = strip_markup(value)
        return cleaned or None
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        values = [clean_text_value(item) for item in value]
        return " ".join(item for item in values if item) or None
    if isinstance(value, dict):
        for key in ["text", "value", "title", "summary", "label", "name"]:
            cleaned = clean_text_value(value.get(key))
            if cleaned:
                return cleaned
        values = [clean_text_value(item) for item in value.values()]
        return " ".join(item for item in values if item) or None
    return strip_markup(value) or None


def strip_markup(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def short_excerpt(value: Any, limit: int = 900) -> str:
    text = strip_markup(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def normalize_text(value: Any) -> str:
    text = strip_markup(value).casefold()
    text = unicodedata.normalize("NFKD", text)
    return "".join(char for char in text if not unicodedata.combining(char))


def read_json_file(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_json_file(path: Path, payload: Any) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        return


def safe_reason(exc: urllib.error.URLError) -> str:
    reason = getattr(exc, "reason", exc)
    return str(reason).replace("\n", " ")[:240]


def safe_configuration(config: JudilibreConfig) -> dict[str, Any]:
    return {
        "client_id_present": bool(config.client_id),
        "client_secret_present": bool(config.client_secret),
        "client_id_source": config.client_id_source,
        "client_secret_source": config.client_secret_source,
        "missing_variables": config.missing_variables,
        "token_url": config.token_url,
        "api_base_url": config.api_base_url,
        "scope": config.scope,
        "timeout_seconds": config.timeout_seconds,
        "cache_dir": str(config.cache_dir),
        "cache_ttl_seconds": config.cache_ttl_seconds,
        "cache_ignored_by_git": "local-index" in config.cache_dir.parts,
    }


def safe_source_sample(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "document": source.get("document"),
        "source_layer": source.get("source_layer"),
        "juridiction": source.get("juridiction"),
        "chamber": source.get("chamber"),
        "decision_date": source.get("decision_date"),
        "case_number": source.get("case_number"),
        "official_id": source.get("official_id"),
        "jurisprudence_relevance_score": source.get("jurisprudence_relevance_score"),
        "selection_reasons": source.get("selection_reasons", []),
        "limite_utilisation": source.get("limite_utilisation"),
        "decision_text_length": source.get("decision_text_length"),
        "retrieved_at": source.get("retrieved_at"),
    }


def emit(payload: dict[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(format_text(payload))


def format_text(payload: dict[str, Any]) -> str:
    lines = ["DIAGNOSTIC JUDILIBRE"]
    if "configuration" in payload:
        config = payload["configuration"]
        lines.extend(
            [
                f"Client ID present : {'oui' if config.get('client_id_present') else 'non'}",
                f"Client Secret present : {'oui' if config.get('client_secret_present') else 'non'}",
                "Variables manquantes : " + (", ".join(config.get("missing_variables", [])) or "aucune"),
                f"Token URL : {config.get('token_url')}",
                f"API base : {config.get('api_base_url')}",
                f"Cache local : {config.get('cache_dir')}",
            ]
        )
    if payload.get("ok") is not None:
        lines.append(f"Statut : {'OK' if payload.get('ok') else 'ERREUR'}")
    if payload.get("error"):
        lines.append(f"Erreur : {payload['error']}")
    if payload.get("steps"):
        for name, step in payload["steps"].items():
            lines.append(f"- {name} : {'OK' if step.get('ok') else 'ERREUR'}")
    if payload.get("source_sample"):
        source = payload["source_sample"]
        lines.append(
            "Decision test : "
            + " | ".join(str(value) for value in source.values() if value not in (None, ""))
        )
    if payload.get("query"):
        lines.append(f"Requete : {payload['query']}")
        lines.append(f"Candidats : {payload.get('candidate_count', 0)}")
        lines.append(f"Decisions retenues : {payload.get('source_count', 0)}")
        for source in payload.get("sources", [])[:2]:
            lines.append(
                "- retenue : "
                + " | ".join(
                    str(value)
                    for value in [
                        source.get("official_id"),
                        source.get("document"),
                        source.get("jurisprudence_relevance_score"),
                    ]
                    if value not in (None, "")
                )
            )
        for source in payload.get("rejected_sources", [])[:4]:
            lines.append(
                "- ecartee : "
                + " | ".join(
                    str(value)
                    for value in [
                        source.get("official_id"),
                        source.get("jurisprudence_relevance_score"),
                        source.get("exclusion_reason"),
                    ]
                    if value not in (None, "")
                )
            )
    if payload.get("scenario_results"):
        for row in payload["scenario_results"]:
            lines.append(
                f"- {row['id']} : {row.get('candidate_count', 0)} candidat(s), {row['source_count']} decision(s), "
                + ", ".join(item.get("official_id") or "id absent" for item in row.get("sources", [])[:2])
            )
    return "\n".join(lines)


def command_diagnose(_args: argparse.Namespace) -> dict[str, Any]:
    config = JudilibreConfig.from_env()
    cache_path = config.cache_dir / "responses.private.json"
    cache_available = cache_path.exists() and cache_path.stat().st_size > 0
    return {
        "ok": config.configured or cache_available,
        "configuration": safe_configuration(config),
        "endpoints": JudilibreClient(config).used_endpoints(),
        "cache_available": cache_available,
        "api_configured": config.configured,
        "notice": "Aucun secret ni token n'est affiche par cette commande.",
    }


def command_healthcheck(_args: argparse.Namespace) -> dict[str, Any]:
    client = JudilibreClient()
    try:
        health = client.healthcheck()
        return {
            "ok": True,
            "configuration": safe_configuration(client.config),
            "endpoints": client.used_endpoints(),
            "healthcheck": health,
        }
    except JudilibreError as exc:
        return {
            "ok": False,
            "configuration": safe_configuration(client.config),
            "endpoints": client.used_endpoints(),
            "error": str(exc),
        }


def command_test_connection(args: argparse.Namespace) -> dict[str, Any]:
    client = JudilibreClient()
    try:
        return client.test_connection(args.query, limit=args.limit)
    except JudilibreError as exc:
        return {
            "ok": False,
            "configuration": safe_configuration(client.config),
            "endpoints": client.used_endpoints(),
            "error": str(exc),
            "notice": "Aucun secret ni token n'est affiche par cette commande.",
        }


def command_search(args: argparse.Namespace) -> dict[str, Any]:
    client = JudilibreClient()
    result = client.search_sources(args.query, limit=args.limit, theme=args.theme)
    return {
        "ok": result.get("available") and bool(result.get("sources")),
        "configuration": safe_configuration(client.config),
        "endpoints": client.used_endpoints(),
        "query": args.query,
        "candidate_count": result.get("candidate_count", 0),
        "source_count": len(result.get("sources", [])),
        "sources": result.get("sources", []),
        "rejected_sources": result.get("rejected_sources", []),
        "warnings": result.get("warnings", []),
    }


def command_decision(args: argparse.Namespace) -> dict[str, Any]:
    client = JudilibreClient()
    try:
        source = client.decision_source(args.decision_id)
        return {
            "ok": True,
            "configuration": safe_configuration(client.config),
            "endpoints": client.used_endpoints(),
            "source": source,
        }
    except JudilibreError as exc:
        return {
            "ok": False,
            "configuration": safe_configuration(client.config),
            "endpoints": client.used_endpoints(),
            "error": str(exc),
        }


def command_run_scenarios(args: argparse.Namespace) -> dict[str, Any]:
    client = JudilibreClient()
    rows: list[dict[str, Any]] = []
    for scenario in SCENARIOS:
        result = client.search_sources(scenario["query"], limit=args.limit, theme=scenario["theme"])
        sources = result.get("sources", [])
        rows.append(
            {
                "id": scenario["id"],
                "query": scenario["query"],
                "theme": scenario["theme"],
                "ok": bool(result.get("available") and sources),
                "candidate_count": result.get("candidate_count", 0),
                "source_count": len(sources),
                "sources": [safe_source_sample(source) for source in sources[: args.limit]],
                "rejected_sources": result.get("rejected_sources", []),
                "warnings": result.get("warnings", []),
            }
        )
    return {
        "ok": all(row["ok"] for row in rows),
        "configuration": safe_configuration(client.config),
        "endpoints": client.used_endpoints(),
        "scenario_results": rows,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CFDT Nexus - connecteur JUDILIBRE PISTE")
    sub = parser.add_subparsers(dest="command", required=True)

    diagnose = sub.add_parser("diagnose")
    diagnose.add_argument("--format", choices=["text", "json"], default="text")

    healthcheck = sub.add_parser("healthcheck")
    healthcheck.add_argument("--format", choices=["text", "json"], default="text")

    test = sub.add_parser("test-connection")
    test.add_argument("--query", default="temps de travail")
    test.add_argument("--limit", type=int, default=1)
    test.add_argument("--format", choices=["text", "json"], default="text")

    search = sub.add_parser("search")
    search.add_argument("--query", required=True)
    search.add_argument("--theme")
    search.add_argument("--limit", type=int, default=3)
    search.add_argument("--format", choices=["text", "json"], default="text")

    decision = sub.add_parser("decision")
    decision.add_argument("--decision-id", required=True)
    decision.add_argument("--format", choices=["text", "json"], default="text")

    scenarios = sub.add_parser("run-scenarios")
    scenarios.add_argument("--limit", type=int, default=2)
    scenarios.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "diagnose":
        emit(command_diagnose(args), args.format)
    elif args.command == "healthcheck":
        emit(command_healthcheck(args), args.format)
    elif args.command == "test-connection":
        emit(command_test_connection(args), args.format)
    elif args.command == "search":
        emit(command_search(args), args.format)
    elif args.command == "decision":
        emit(command_decision(args), args.format)
    elif args.command == "run-scenarios":
        emit(command_run_scenarios(args), args.format)
    else:
        raise SystemExit(f"Commande inconnue: {args.command}")


if __name__ == "__main__":
    main()
