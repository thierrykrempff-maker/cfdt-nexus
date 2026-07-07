#!/usr/bin/env python
"""PISTE / Legifrance connector for official Code du travail sources.

The connector is intentionally separated from the Nexus router. It only handles
OAuth2, HTTP calls, response parsing and source normalization. It never embeds
credentials and never fabricates a legal source when the API is unavailable.
"""

from __future__ import annotations

import base64
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

ENV_CLIENT_ID = "CFDT_NEXUS_LEGIFRANCE_CLIENT_ID"
ENV_CLIENT_SECRET = "CFDT_NEXUS_LEGIFRANCE_CLIENT_SECRET"
ENV_TOKEN_URL = "CFDT_NEXUS_LEGIFRANCE_TOKEN_URL"
ENV_API_BASE_URL = "CFDT_NEXUS_LEGIFRANCE_API_BASE_URL"
ENV_SCOPE = "CFDT_NEXUS_LEGIFRANCE_SCOPE"
ENV_TIMEOUT = "CFDT_NEXUS_LEGIFRANCE_TIMEOUT"
ENV_SEARCH_ENDPOINT = "CFDT_NEXUS_LEGIFRANCE_SEARCH_ENDPOINT"
ENV_ARTICLE_ENDPOINT = "CFDT_NEXUS_LEGIFRANCE_ARTICLE_ENDPOINT"
ENV_CACHE_DIR = "CFDT_NEXUS_LEGIFRANCE_CACHE_DIR"
ENV_CACHE_TTL = "CFDT_NEXUS_LEGIFRANCE_CACHE_TTL_SECONDS"

DEFAULT_TOKEN_URL = "https://oauth.piste.gouv.fr/api/oauth/token"
DEFAULT_API_BASE_URL = "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app"
DEFAULT_SEARCH_ENDPOINT = "/search"
DEFAULT_ARTICLE_ENDPOINT = "/consult/getArticle"
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_CACHE_TTL_SECONDS = 24 * 60 * 60
CODE_DU_TRAVAIL_LEGITEXT = "LEGITEXT000006072050"
CODE_DU_TRAVAIL_LABEL = "Code du travail"


class LegifranceError(RuntimeError):
    """Base class for expected Legifrance connector failures."""


class LegifranceConfigurationError(LegifranceError):
    """Raised when credentials or endpoint configuration are missing."""


class LegifranceAPIError(LegifranceError):
    """Raised when PISTE / Legifrance returns an unusable response."""


@dataclass(frozen=True)
class LegifranceConfig:
    client_id: str | None
    client_secret: str | None
    token_url: str = DEFAULT_TOKEN_URL
    api_base_url: str = DEFAULT_API_BASE_URL
    scope: str | None = None
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    search_endpoint: str = DEFAULT_SEARCH_ENDPOINT
    article_endpoint: str = DEFAULT_ARTICLE_ENDPOINT
    cache_dir: Path = ROOT / "local-index" / "legifrance"
    cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS

    @classmethod
    def from_env(cls) -> "LegifranceConfig":
        timeout = parse_int(os.environ.get(ENV_TIMEOUT), DEFAULT_TIMEOUT_SECONDS)
        cache_ttl = parse_int(os.environ.get(ENV_CACHE_TTL), DEFAULT_CACHE_TTL_SECONDS)
        cache_dir = Path(os.environ.get(ENV_CACHE_DIR) or ROOT / "local-index" / "legifrance")
        return cls(
            client_id=clean_env(os.environ.get(ENV_CLIENT_ID)),
            client_secret=clean_env(os.environ.get(ENV_CLIENT_SECRET)),
            token_url=os.environ.get(ENV_TOKEN_URL, DEFAULT_TOKEN_URL).strip(),
            api_base_url=os.environ.get(ENV_API_BASE_URL, DEFAULT_API_BASE_URL).strip().rstrip("/"),
            scope=clean_env(os.environ.get(ENV_SCOPE)),
            timeout_seconds=timeout,
            search_endpoint=os.environ.get(ENV_SEARCH_ENDPOINT, DEFAULT_SEARCH_ENDPOINT).strip(),
            article_endpoint=os.environ.get(ENV_ARTICLE_ENDPOINT, DEFAULT_ARTICLE_ENDPOINT).strip(),
            cache_dir=cache_dir,
            cache_ttl_seconds=cache_ttl,
        )

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    @property
    def missing_variables(self) -> list[str]:
        missing = []
        if not self.client_id:
            missing.append(ENV_CLIENT_ID)
        if not self.client_secret:
            missing.append(ENV_CLIENT_SECRET)
        return missing

    def endpoint_url(self, endpoint: str) -> str:
        endpoint = endpoint.strip()
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        return self.api_base_url + endpoint


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


def configured_from_env() -> bool:
    return LegifranceConfig.from_env().configured


def status_from_env() -> dict[str, Any]:
    config = LegifranceConfig.from_env()
    return {
        "detected": True,
        "available": config.configured,
        "missing_variables": config.missing_variables,
        "token_url": config.token_url,
        "api_base_url": config.api_base_url,
        "search_endpoint": config.search_endpoint,
        "article_endpoint": config.article_endpoint,
        "cache_dir": str(config.cache_dir),
        "cache_ignored_by_git": "local-index" in config.cache_dir.parts,
    }


class LegifranceClient:
    def __init__(self, config: LegifranceConfig | None = None) -> None:
        self.config = config or LegifranceConfig.from_env()

    def ensure_configured(self) -> None:
        if not self.config.configured:
            missing = ", ".join(self.config.missing_variables)
            raise LegifranceConfigurationError(
                f"Connecteur Legifrance non configure: variable(s) manquante(s) {missing}."
            )

    @property
    def token_cache_path(self) -> Path:
        return self.config.cache_dir / "oauth-token.private.json"

    @property
    def response_cache_path(self) -> Path:
        return self.config.cache_dir / "responses.private.json"

    def authenticate(self, force_refresh: bool = False) -> dict[str, Any]:
        self.ensure_configured()
        if not force_refresh:
            cached = self._read_token_cache()
            if cached and float(cached.get("expires_at", 0)) > time.time() + 60:
                return {**cached, "from_cache": True}

        assert self.config.client_id is not None
        assert self.config.client_secret is not None
        credentials = f"{self.config.client_id}:{self.config.client_secret}".encode("utf-8")
        auth_header = base64.b64encode(credentials).decode("ascii")
        form: dict[str, str] = {"grant_type": "client_credentials"}
        if self.config.scope:
            form["scope"] = self.config.scope
        body = urllib.parse.urlencode(form).encode("utf-8")
        request = urllib.request.Request(
            self.config.token_url,
            data=body,
            headers={
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:  # noqa: S310
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise LegifranceAPIError(f"OAuth Legifrance refuse: HTTP {exc.code} {exc.reason}.") from exc
        except urllib.error.URLError as exc:
            raise LegifranceAPIError(f"OAuth Legifrance indisponible: {safe_reason(exc)}.") from exc
        except json.JSONDecodeError as exc:
            raise LegifranceAPIError("OAuth Legifrance: reponse JSON illisible.") from exc

        token = payload.get("access_token")
        if not token:
            raise LegifranceAPIError("OAuth Legifrance: access_token absent de la reponse.")
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

    def search_article_hits(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        self.ensure_configured()
        cleaned_query = (query or "").strip()
        if not cleaned_query:
            return []
        cache_key = self._cache_key("search", {"query": cleaned_query, "limit": limit})
        cached = self._read_response_cache(cache_key)
        if cached is not None:
            return cached

        payload = build_search_payload(cleaned_query, limit)
        response = self._post_json(self.config.search_endpoint, payload)
        hits = extract_article_hits(response)
        deduped = dedupe_hits(hits)[: max(1, limit)]
        self._write_response_cache(cache_key, deduped)
        return deduped

    def article_source(self, article_id: str, search_hit: dict[str, Any] | None = None) -> dict[str, Any]:
        self.ensure_configured()
        cleaned_id = (article_id or "").strip()
        if not cleaned_id:
            raise LegifranceAPIError("Identifiant d'article Legifrance absent.")
        cache_key = self._cache_key("article", {"id": cleaned_id})
        cached = self._read_response_cache(cache_key)
        if cached is not None:
            return merge_search_context(cached, search_hit)

        response = self._post_json(self.config.article_endpoint, {"id": cleaned_id})
        source = normalize_article_source(response, cleaned_id, search_hit)
        self._write_response_cache(cache_key, source)
        return source

    def search_code_sources(self, query: str, limit: int = 3) -> dict[str, Any]:
        try:
            hits = self.search_article_hits(query, limit=max(limit * 2, limit))
            sources: list[dict[str, Any]] = []
            warnings: list[str] = []
            for hit in hits:
                article_id = hit.get("official_id")
                if not article_id:
                    continue
                try:
                    sources.append(self.article_source(str(article_id), hit))
                except LegifranceError as exc:
                    fallback = source_from_search_hit(hit)
                    if fallback:
                        warnings.append(str(exc))
                        sources.append(fallback)
                if len(sources) >= limit:
                    break
            return {
                "available": True,
                "sources": sources,
                "warnings": warnings,
                "search_hits": len(hits),
                "endpoints": self.used_endpoints(),
            }
        except LegifranceError as exc:
            return {
                "available": False,
                "sources": [],
                "warnings": [str(exc)],
                "search_hits": 0,
                "endpoints": self.used_endpoints(),
            }

    def test_connection(self, query: str, limit: int = 3, article_id: str | None = None) -> dict[str, Any]:
        result: dict[str, Any] = {
            "ok": False,
            "endpoints": self.used_endpoints(),
            "configuration": safe_configuration(self.config),
            "steps": {},
        }
        result["steps"]["oauth"] = self.auth_diagnostic(force_refresh=False)
        hits = self.search_article_hits(query, limit=limit)
        result["steps"]["minimal_call"] = {
            "ok": True,
            "endpoint": self.config.endpoint_url(self.config.search_endpoint),
            "kind": "search",
        }
        selected_id = article_id or (str(hits[0].get("official_id")) if hits else None)
        result["steps"]["search_article"] = {
            "ok": bool(hits),
            "query": query,
            "hit_count": len(hits),
            "selected_official_id": selected_id,
        }
        if not selected_id:
            raise LegifranceAPIError("Recherche Legifrance sans article exploitable.")
        source = self.article_source(selected_id, hits[0] if hits else None)
        result["steps"]["retrieve_article"] = {
            "ok": True,
            "article": source.get("article"),
            "official_id": source.get("official_id"),
            "text_length": len(str(source.get("excerpt") or "")),
        }
        result["steps"]["vigour"] = {
            "ok": source.get("is_in_force") is not None,
            "etat": source.get("etat"),
            "is_in_force": source.get("is_in_force"),
            "date_debut": source.get("date_debut") or source.get("version_start_date"),
            "date_fin": source.get("date_fin") or source.get("version_end_date"),
        }
        result["source_sample"] = {
            "document": source.get("document"),
            "source_layer": source.get("source_layer"),
            "article": source.get("article"),
            "official_id": source.get("official_id"),
            "etat": source.get("etat"),
            "is_in_force": source.get("is_in_force"),
            "retrieved_at": source.get("retrieved_at"),
        }
        result["ok"] = all(step.get("ok", False) for step in result["steps"].values())
        return result

    def used_endpoints(self) -> dict[str, str]:
        return {
            "oauth_token": self.config.token_url,
            "api_base": self.config.api_base_url,
            "search": self.config.endpoint_url(self.config.search_endpoint),
            "article": self.config.endpoint_url(self.config.article_endpoint),
        }

    def _post_json(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        token = self.authenticate()
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            self.config.endpoint_url(endpoint),
            data=data,
            headers={
                "Authorization": f"{token.get('token_type') or 'Bearer'} {token['access_token']}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:  # noqa: S310
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise LegifranceAPIError(f"API Legifrance refuse: HTTP {exc.code} {exc.reason}.") from exc
        except urllib.error.URLError as exc:
            raise LegifranceAPIError(f"API Legifrance indisponible: {safe_reason(exc)}.") from exc
        except json.JSONDecodeError as exc:
            raise LegifranceAPIError("API Legifrance: reponse JSON illisible.") from exc

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


def safe_reason(exc: urllib.error.URLError) -> str:
    reason = getattr(exc, "reason", exc)
    return str(reason).replace("\n", " ")[:240]


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
        # Cache is useful but must never block an answer or leak credentials in logs.
        return


def build_search_payload(query: str, limit: int) -> dict[str, Any]:
    page_size = max(1, min(limit, 10))
    return {
        "recherche": {
            "champs": [
                {
                    "typeChamp": "ALL",
                    "criteres": [
                        {
                            "typeRecherche": "UN_DES_MOTS",
                            "valeur": query,
                            "operateur": "ET",
                        }
                    ],
                    "operateur": "ET",
                }
            ],
            "filtres": [
                {"facette": "NATURE", "valeurs": ["CODE"]},
                {"facette": "CODE", "valeurs": [CODE_DU_TRAVAIL_LEGITEXT]},
            ],
            "pageNumber": 1,
            "pageSize": page_size,
            "sort": "PERTINENCE",
        },
        "fond": "CODE_DATE",
    }


def extract_article_hits(payload: Any) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for node in iter_dicts(payload):
        official_id = first_article_id(node)
        if not official_id:
            continue
        article = first_article_number(node)
        title = first_text_value(node, ["title", "titre", "label", "libelle"])
        snippet = first_text_value(node, ["snippet", "extrait", "resume", "texte", "text"])
        score = node.get("score") or node.get("pertinence") or node.get("rank")
        hits.append(
            {
                "official_id": official_id,
                "article": article,
                "title": strip_markup(title),
                "excerpt": short_excerpt(strip_markup(snippet), 500),
                "score": score,
            }
        )
    return hits


def iter_dicts(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from iter_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_dicts(child)


def first_article_id(value: Any) -> str | None:
    keys = ["id", "cid", "articleId", "idArticle", "legiArticleId", "official_id"]
    if isinstance(value, dict):
        for key in keys:
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.startswith("LEGIARTI"):
                return candidate
        for candidate in value.values():
            found = first_article_id(candidate)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = first_article_id(item)
            if found:
                return found
    elif isinstance(value, str):
        match = re.search(r"LEGIARTI\d+", value)
        if match:
            return match.group(0)
    return None


def first_article_number(value: Any) -> str | None:
    if isinstance(value, dict):
        for key in ["num", "numero", "article", "articleNumber", "title", "titre", "label"]:
            candidate = value.get(key)
            if isinstance(candidate, str):
                number = extract_article_number(candidate)
                if number:
                    return number
        for child in value.values():
            found = first_article_number(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = first_article_number(child)
            if found:
                return found
    elif isinstance(value, str):
        return extract_article_number(value)
    return None


def extract_article_number(text: str) -> str | None:
    match = re.search(r"\b([LRD]\.?\s*\d{1,4}-\d{1,4}(?:-\d+)?)\b", strip_markup(text), flags=re.IGNORECASE)
    if not match:
        return None
    return re.sub(r"\s+", " ", match.group(1)).replace(". ", ".").upper()


def first_text_value(value: Any, keys: list[str]) -> str | None:
    if isinstance(value, dict):
        lower_keys = {key.lower() for key in keys}
        for key, candidate in value.items():
            if key.lower() in lower_keys and isinstance(candidate, str) and candidate.strip():
                return candidate
        for child in value.values():
            found = first_text_value(child, keys)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = first_text_value(child, keys)
            if found:
                return found
    return None


def best_article_text(payload: Any) -> str | None:
    preferred = first_text_value(payload, ["texte", "text", "contenu", "content", "html", "articleText"])
    if preferred and len(strip_markup(preferred)) >= 40:
        return preferred
    candidates: list[str] = []
    for text in iter_strings(payload):
        cleaned = strip_markup(text)
        if len(cleaned) >= 80 and re.search(r"\b(article|salarie|travail|employeur|duree|repos|contrat)\b", cleaned, re.IGNORECASE):
            candidates.append(cleaned)
    if not candidates:
        return preferred
    return max(candidates, key=len)


def iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from iter_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_strings(child)


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


def first_date_value(payload: Any, keys: list[str]) -> str | None:
    value = first_text_value(payload, keys)
    if value:
        return value[:10]
    return None


def first_state_value(payload: Any) -> str | None:
    return first_text_value(payload, ["etat", "etatArticle", "etatVersion", "state", "status"])


def is_in_force(etat: str | None, end_date: str | None) -> bool | None:
    normalized = normalize_text(etat)
    if "abroge" in normalized or "perime" in normalized or "annule" in normalized:
        return False
    if "vigueur" in normalized and "non vigueur" not in normalized:
        return True
    if end_date:
        if end_date.startswith("2999") or end_date.startswith("9999"):
            return True
        try:
            return datetime.fromisoformat(end_date[:10]).date() >= datetime.now().date()
        except ValueError:
            return None
    return None


def normalize_text(value: Any) -> str:
    text = strip_markup(value).casefold()
    text = unicodedata.normalize("NFKD", text)
    return "".join(char for char in text if not unicodedata.combining(char))


def normalize_article_source(payload: Any, requested_id: str, search_hit: dict[str, Any] | None = None) -> dict[str, Any]:
    official_id = first_article_id(payload) or requested_id
    article = first_article_number(payload) or (search_hit or {}).get("article") or official_id
    text = best_article_text(payload) or (search_hit or {}).get("excerpt") or ""
    etat = first_state_value(payload)
    start_date = first_date_value(
        payload,
        ["dateDebut", "dateDebutVersion", "dateDebutVigueur", "startDate", "versionStartDate"],
    )
    end_date = first_date_value(
        payload,
        ["dateFin", "dateFinVersion", "dateFinVigueur", "endDate", "versionEndDate"],
    )
    in_force = is_in_force(etat, end_date)
    warning = None
    if in_force is None:
        warning = "Etat de vigueur non determine automatiquement: verifier la fiche Legifrance."
    if not text:
        warning = "Texte de l'article non extrait: verifier la fiche Legifrance."
    return {
        "document": CODE_DU_TRAVAIL_LABEL,
        "document_type": "code_travail",
        "source_layer": "code_travail",
        "source_layer_label": "Code du travail",
        "article": article,
        "article_or_section": article,
        "official_id": official_id,
        "legifrance_id": official_id,
        "etat": etat,
        "is_in_force": in_force,
        "date_debut": start_date,
        "date_fin": end_date,
        "version_start_date": start_date,
        "version_end_date": end_date,
        "retrieved_at": utc_now(),
        "url": f"https://www.legifrance.gouv.fr/codes/article_lc/{official_id}",
        "excerpt": short_excerpt(text),
        "chunk_id": official_id,
        "score": (search_hit or {}).get("score"),
        "ranking_reasons": [
            "Source officielle Legifrance via API PISTE",
            "Recherche limitee au Code du travail",
        ],
        "source_quality_warning": warning,
    }


def source_from_search_hit(hit: dict[str, Any]) -> dict[str, Any] | None:
    official_id = hit.get("official_id")
    if not official_id:
        return None
    return {
        "document": CODE_DU_TRAVAIL_LABEL,
        "document_type": "code_travail",
        "source_layer": "code_travail",
        "source_layer_label": "Code du travail",
        "article": hit.get("article") or official_id,
        "article_or_section": hit.get("article") or official_id,
        "official_id": official_id,
        "legifrance_id": official_id,
        "etat": None,
        "is_in_force": None,
        "retrieved_at": utc_now(),
        "url": f"https://www.legifrance.gouv.fr/codes/article_lc/{official_id}",
        "excerpt": short_excerpt(hit.get("excerpt") or hit.get("title") or ""),
        "chunk_id": official_id,
        "score": hit.get("score"),
        "ranking_reasons": [
            "Article remonte par la recherche officielle Legifrance",
            "Contenu complet non recupere automatiquement",
        ],
        "source_quality_warning": "Article retrouve par recherche, mais contenu ou vigueur non confirmes par getArticle.",
    }


def merge_search_context(source: dict[str, Any], search_hit: dict[str, Any] | None) -> dict[str, Any]:
    if not search_hit:
        return source
    merged = dict(source)
    if not merged.get("score"):
        merged["score"] = search_hit.get("score")
    if not merged.get("article") and search_hit.get("article"):
        merged["article"] = search_hit["article"]
        merged["article_or_section"] = search_hit["article"]
    return merged


def dedupe_hits(hits: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for hit in hits:
        official_id = str(hit.get("official_id") or "")
        if not official_id or official_id in seen:
            continue
        seen.add(official_id)
        result.append(hit)
    return result


def safe_configuration(config: LegifranceConfig) -> dict[str, Any]:
    return {
        "client_id_present": bool(config.client_id),
        "client_secret_present": bool(config.client_secret),
        "missing_variables": config.missing_variables,
        "token_url": config.token_url,
        "api_base_url": config.api_base_url,
        "search_endpoint": config.search_endpoint,
        "article_endpoint": config.article_endpoint,
        "timeout_seconds": config.timeout_seconds,
        "cache_dir": str(config.cache_dir),
        "cache_ttl_seconds": config.cache_ttl_seconds,
    }
