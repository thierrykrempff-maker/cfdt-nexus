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

    def search_sources(self, query: str, limit: int = 3, theme: str | None = None) -> dict[str, Any]:
        try:
            hits = self.search_decision_hits(query, limit=max(limit, 3))
            sources: list[dict[str, Any]] = []
            warnings: list[str] = []
            for hit in hits:
                if theme and not hit.get("theme"):
                    hit["theme"] = theme
                try:
                    sources.append(self.decision_source(str(hit["official_id"]), hit))
                except JudilibreError as exc:
                    warnings.append(str(exc))
                    sources.append(hit)
                if len(sources) >= limit:
                    break
            if not hits:
                warnings.append("JUDILIBRE: aucune decision remontee pour cette recherche.")
            return {
                "available": True,
                "sources": sources,
                "warnings": warnings,
                "search_hits": len(hits),
                "endpoints": self.used_endpoints(),
            }
        except JudilibreError as exc:
            return {
                "available": False,
                "sources": [],
                "warnings": [str(exc)],
                "search_hits": 0,
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
            return None
        return item.get("value")

    def _write_response_cache(self, key: str, value: Any) -> None:
        cache = read_json_file(self.response_cache_path) or {}
        cache[key] = {
            "expires_at": time.time() + self.config.cache_ttl_seconds,
            "stored_at": utc_now(),
            "value": value,
        }
        write_json_file(self.response_cache_path, cache)


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
    if payload.get("scenario_results"):
        for row in payload["scenario_results"]:
            lines.append(
                f"- {row['id']} : {row['source_count']} decision(s), "
                + ", ".join(item.get("official_id") or "id absent" for item in row.get("sources", [])[:2])
            )
    return "\n".join(lines)


def command_diagnose(_args: argparse.Namespace) -> dict[str, Any]:
    config = JudilibreConfig.from_env()
    return {
        "ok": config.configured,
        "configuration": safe_configuration(config),
        "endpoints": JudilibreClient(config).used_endpoints(),
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
        "source_count": len(result.get("sources", [])),
        "sources": result.get("sources", []),
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
                "source_count": len(sources),
                "sources": [safe_source_sample(source) for source in sources[: args.limit]],
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
