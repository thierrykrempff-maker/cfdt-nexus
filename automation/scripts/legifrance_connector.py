#!/usr/bin/env python
"""PISTE / Legifrance connector for official Code du travail sources.

The connector is intentionally separated from the Nexus router. It only handles
OAuth2, HTTP calls, response parsing and source normalization. It never embeds
credentials and never fabricates a legal source when the API is unavailable.
"""

from __future__ import annotations

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
JURISPRUDENCE_LABEL = "Jurisprudence Cour de cassation"

CODE_TRAVAIL_MINI_INDEX: list[dict[str, Any]] = [
    {
        "topic": "temps_travail_effectif",
        "article": "L3121-1",
        "article_id": "LEGIARTI000033020517",
        "keywords": ["temps de travail", "travail effectif", "intervention", "reunion"],
    },
    {
        "topic": "discipline_definition_sanction",
        "article": "L1331-1",
        "article_id": None,
        "search_query": "Article L1331-1 Code du travail sanction disciplinaire",
        "keywords": ["sanction", "disciplinaire", "procedure disciplinaire", "faits reproches"],
    },
    {
        "topic": "discipline_information_griefs",
        "article": "L1332-1",
        "article_id": None,
        "search_query": "Article L1332-1 Code du travail griefs sanction disciplinaire",
        "keywords": ["sanction", "disciplinaire", "griefs", "procedure disciplinaire"],
    },
    {
        "topic": "discipline_entretien_prealable",
        "article": "L1332-2",
        "article_id": None,
        "search_query": "Article L1332-2 Code du travail entretien sanction disciplinaire",
        "keywords": ["sanction", "disciplinaire", "entretien", "convocation", "procedure disciplinaire"],
    },
    {
        "topic": "discipline_prescription_faits",
        "article": "L1332-4",
        "article_id": None,
        "search_query": "Article L1332-4 Code du travail sanction disciplinaire deux mois",
        "keywords": ["sanction", "disciplinaire", "prescription", "deux mois", "faits reproches"],
    },
    {
        "topic": "cse_attributions_generales",
        "article": "L2312-8",
        "article_id": None,
        "search_query": "Article L2312-8 Code du travail CSE organisation gestion marche generale entreprise",
        "keywords": ["cse", "consultation", "reorganisation", "organisation du travail", "emploi"],
    },
    {
        "topic": "cse_avis_information",
        "article": "L2312-15",
        "article_id": None,
        "search_query": "Article L2312-15 Code du travail CSE avis informations delai examen",
        "keywords": ["cse", "consultation", "avis", "documents", "informations", "delai"],
    },
    {
        "topic": "astreinte_definition",
        "article": "L3121-9",
        "article_id": "LEGIARTI000033020484",
        "keywords": ["astreinte", "intervention", "domicile", "appel"],
    },
    {
        "topic": "astreinte_intervention",
        "article": "L3121-10",
        "article_id": "LEGIARTI000033020479",
        "keywords": ["astreinte", "intervention", "temps de travail effectif", "nuit"],
    },
    {
        "topic": "astreinte_compensation",
        "article": "L3121-11",
        "article_id": "LEGIARTI000033020471",
        "keywords": ["astreinte", "compensation", "contrepartie", "indemnisation"],
    },
    {
        "topic": "heures_supplementaires",
        "article": "L3121-28",
        "article_id": "LEGIARTI000033020373",
        "keywords": ["heures supplementaires", "majoration", "paie", "bulletin", "heure"],
    },
    {
        "topic": "repos_quotidien",
        "article": "L3131-1",
        "article_id": "LEGIARTI000033020918",
        "keywords": ["repos quotidien", "repos", "reprise", "nuit", "5x8", "cse"],
    },
    {
        "topic": "repos_hebdomadaire_interdiction",
        "article": "L3132-1",
        "article_id": "LEGIARTI000006902580",
        "keywords": ["repos hebdomadaire", "repos", "semaine", "dimanche", "cse"],
    },
    {
        "topic": "repos_hebdomadaire_duree",
        "article": "L3132-2",
        "article_id": "LEGIARTI000006902581",
        "keywords": ["repos hebdomadaire", "repos", "24 heures", "35 heures", "dimanche"],
    },
    {
        "topic": "repos_dominical",
        "article": "L3132-3",
        "article_id": "LEGIARTI000020967733",
        "keywords": ["dimanche", "repos dominical", "repos hebdomadaire"],
    },
    {
        "topic": "dimanche_compensation_majoration",
        "article": "L3132-27",
        "article_id": "LEGIARTI000020968006",
        "keywords": ["dimanche", "repos compensateur", "majoration", "salaire", "paie"],
    },
]

JURISPRUDENCE_MINI_INDEX: list[dict[str, Any]] = [
    {
        "topic": "astreinte_repos",
        "label": "Astreinte, intervention et repos",
        "query": "astreinte intervention repos quotidien chambre sociale",
        "keywords": ["astreinte", "intervention", "repos", "reprise", "nuit", "poste"],
    },
    {
        "topic": "repos_temps_travail",
        "label": "Repos quotidien et temps de travail",
        "query": "repos quotidien repos hebdomadaire temps travail chambre sociale",
        "keywords": ["repos quotidien", "repos hebdomadaire", "repos", "5x8", "nuit"],
    },
    {
        "topic": "temps_travail_effectif",
        "label": "Temps de travail effectif",
        "query": "temps travail effectif intervention chambre sociale",
        "keywords": ["temps de travail", "travail effectif", "intervention", "reunion"],
    },
    {
        "topic": "heures_supplementaires",
        "label": "Heures supplementaires et preuve",
        "query": "heures supplementaires preuve salaire bulletin chambre sociale",
        "keywords": ["heures supplementaires", "majoration", "bulletin", "paie", "heures"],
    },
    {
        "topic": "travail_dimanche",
        "label": "Travail du dimanche",
        "query": "dimanche repos compensateur majoration salaire chambre sociale",
        "keywords": ["dimanche", "repos compensateur", "majoration dimanche"],
    },
    {
        "topic": "prime_variable",
        "label": "Primes et elements variables de paie",
        "query": "prime remuneration variable salaire bulletin chambre sociale",
        "keywords": ["prime", "variable", "remuneration", "salaire", "bulletin"],
    },
    {
        "topic": "classification_fonctions_reelles",
        "label": "Classification et fonctions reellement exercees",
        "query": "classification fonctions reellement exercees coefficient chambre sociale",
        "keywords": ["classification", "coefficient", "fiche de poste", "fonctions", "responsabilites"],
    },
    {
        "topic": "cse_temps_reunion_mandat",
        "label": "CSE, mandat et temps de reunion",
        "query": "comite social economique reunion temps travail chambre sociale",
        "keywords": ["cse", "reunion", "mandat", "delegation", "elu", "representant"],
    },
]

FRENCH_MONTHS = {
    "janvier": "01",
    "fevrier": "02",
    "février": "02",
    "mars": "03",
    "avril": "04",
    "mai": "05",
    "juin": "06",
    "juillet": "07",
    "aout": "08",
    "août": "08",
    "septembre": "09",
    "octobre": "10",
    "novembre": "11",
    "decembre": "12",
    "décembre": "12",
}


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
        form: dict[str, str] = {
            "grant_type": "client_credentials",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "scope": self.config.scope or "openid",
        }
        body = urllib.parse.urlencode(form).encode("utf-8")
        request = urllib.request.Request(
            self.config.token_url,
            data=body,
            headers={
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

    def search_jurisprudence_hits(self, query: str, limit: int = 6) -> list[dict[str, Any]]:
        self.ensure_configured()
        cleaned_query = (query or "").strip()
        if not cleaned_query:
            return []
        cache_key = self._cache_key("juri_search", {"query": cleaned_query, "limit": limit})
        cached = self._read_response_cache(cache_key)
        if cached is not None:
            return cached

        payload = build_jurisprudence_search_payload(cleaned_query, limit)
        response = self._post_json(self.config.search_endpoint, payload)
        hits = extract_jurisprudence_hits(response)
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
        current_id = current_version_id(response)
        if current_id and current_id != cleaned_id:
            response = self._post_json(self.config.article_endpoint, {"id": current_id})
            cleaned_id = current_id
        source = normalize_article_source(response, cleaned_id, search_hit)
        self._write_response_cache(cache_key, source)
        return source

    def search_code_sources(self, query: str, limit: int = 3) -> dict[str, Any]:
        try:
            hits = mini_index_hits(query, limit=max(limit * 2, limit))
            sources: list[dict[str, Any]] = []
            warnings: list[str] = []
            for hit in hits:
                candidate_hits = [hit]
                if not hit.get("official_id") and hit.get("search_query"):
                    resolved_hits = self.search_article_hits(str(hit["search_query"]), limit=3)
                    article = normalize_text(hit.get("article"))
                    exact_hits = [
                        {
                            **resolved,
                            "topic": hit.get("topic"),
                            "reason": hit.get("reason"),
                        }
                        for resolved in resolved_hits
                        if article and article in normalize_text(resolved.get("article"))
                    ]
                    candidate_hits = exact_hits or [
                        {
                            **resolved,
                            "topic": hit.get("topic"),
                            "reason": hit.get("reason"),
                        }
                        for resolved in resolved_hits[:1]
                    ]
                    if not candidate_hits:
                        warnings.append(f"article {hit.get('article')} non resolu par la recherche officielle.")
                for candidate in candidate_hits:
                    article_id = candidate.get("official_id")
                    if not article_id:
                        continue
                    try:
                        sources.append(self.article_source(str(article_id), candidate))
                    except LegifranceError as exc:
                        warnings.append(str(exc))
                    usable_sources = [source for source in dedupe_hits(sources) if is_usable_code_source(source)]
                    if len(usable_sources) >= limit:
                        break
                usable_sources = [source for source in dedupe_hits(sources) if is_usable_code_source(source)]
                if len(usable_sources) >= limit:
                    break
            usable_sources = []
            for source in dedupe_hits(sources):
                quality_warning = code_source_quality_warning(source)
                if quality_warning:
                    article = source.get("article") or source.get("article_or_section") or source.get("official_id")
                    warnings.append(f"source Code du travail ignoree ({article}): {quality_warning}")
                    continue
                usable_sources.append(source)
            sources = usable_sources[: max(1, limit)]
            if not hits:
                warnings.append("Mini-index Code du travail V1: aucun article cible selectionne pour cette question.")
            if is_cse_meeting_query(query):
                warnings.append(
                    "Mini-index Code du travail V1: aucun article CSE specifique n'est encore valide ; "
                    "les articles remontes portent sur temps de travail et repos."
                )
            warnings = list(dict.fromkeys(warnings))
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

    def search_jurisprudence_sources(self, query: str, limit: int = 3) -> dict[str, Any]:
        try:
            topics = jurisprudence_mini_index_hits(query, limit=4)
            sources: list[dict[str, Any]] = []
            warnings: list[str] = []
            for topic in topics:
                try:
                    hits = self.search_jurisprudence_hits(str(topic["query"]), limit=8)
                except LegifranceError as exc:
                    warnings.append(str(exc))
                    continue
                for hit in hits:
                    source = normalize_jurisprudence_source(hit, topic)
                    if source:
                        sources.append(source)
                    if len(dedupe_hits(sources)) >= limit:
                        break
                if len(dedupe_hits(sources)) >= limit:
                    break
            sources = dedupe_hits(sources)[: max(1, limit)]
            if not topics:
                warnings.append("Mini-index jurisprudence V1: aucun theme cible selectionne pour cette question.")
            if topics and not sources:
                warnings.append(
                    "Jurisprudence Legifrance: aucune decision Cour de cassation chambre sociale fiable "
                    "n'a ete remontee par la recherche officielle."
                )
            if "astreinte" in normalize_text(query):
                warnings.append(
                    "Mini-index jurisprudence V1: aucun arret Cour de cassation chambre sociale specifique "
                    "a l'astreinte salarie n'est encore valide ; les decisions remontees portent sur repos "
                    "ou temps de travail effectif."
                )
            return {
                "available": True,
                "sources": sources,
                "warnings": warnings,
                "search_hits": len(sources),
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
            "jurisprudence_search": self.config.endpoint_url(self.config.search_endpoint),
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


def build_jurisprudence_search_payload(query: str, limit: int) -> dict[str, Any]:
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
            "pageNumber": 1,
            "pageSize": page_size,
            "sort": "PERTINENCE",
        },
        "fond": "JURI",
    }


def mini_index_hits(query: str, limit: int) -> list[dict[str, Any]]:
    text = normalize_text(query)
    selected: list[dict[str, Any]] = []

    def add(article: str, reason: str, score: int) -> None:
        for item in CODE_TRAVAIL_MINI_INDEX:
            if item["article"] == article:
                selected.append(
                    {
                        "official_id": item.get("article_id"),
                        "article": item["article"],
                        "title": CODE_DU_TRAVAIL_LABEL,
                        "excerpt": "",
                        "score": score,
                        "topic": item["topic"],
                        "reason": reason,
                        "search_query": item.get("search_query"),
                    }
                )
                return

    if any(term in text for term in ["sanction", "disciplinaire", "procedure disciplinaire", "entretien disciplinaire"]):
        add("L1331-1", "disciplinaire: definition de la sanction", 98)
        add("L1332-1", "disciplinaire: information ecrite des griefs", 96)
        add("L1332-2", "disciplinaire: procedure et entretien", 94)
        add("L1332-4", "disciplinaire: delai pour engager les poursuites", 86)
    if re.search(r"\bcse\b|comite social economique", text) and any(
        term in text
        for term in [
            "reorganisation",
            "consultation",
            "information consultation",
            "suppression de poste",
            "changement des horaires",
            "changement d horaires",
            "modification des taches",
            "documents",
            "pv",
        ]
    ):
        add("L2312-8", "CSE: information-consultation sur l'organisation et la marche generale", 99)
        add("L2312-15", "CSE: informations et delai d'examen suffisants", 95)
    if "astreinte" in text:
        add("L3121-9", "astreinte: definition legale", 100)
        add("L3121-10", "astreinte: intervention et temps de travail effectif", 96)
        add("L3121-11", "astreinte: contreparties", 86)
    if any(term in text for term in ["repos quotidien", "reprise", "interrompu", "nuit", "5x8"]) or (
        "poste" in text and any(term in text for term in ["repos", "reprise", "nuit", "astreinte"])
    ):
        add("L3131-1", "repos quotidien", 92)
    if any(term in text for term in ["repos hebdomadaire", "repos compensateur", "dimanche", "hebdomadaire"]):
        add("L3132-1", "repos hebdomadaire", 88)
        add("L3132-2", "duree minimale du repos hebdomadaire", 86)
    if "dimanche" in text:
        add("L3132-3", "repos dominical", 96)
        add("L3132-27", "dimanche: repos compensateur et majoration", 94)
    if any(term in text for term in ["heure supplementaire", "heures supplementaires", "majoration", "paie", "bulletin"]):
        add("L3121-28", "heures supplementaires et majoration", 84)
    if any(term in text for term in ["temps de travail", "travail effectif", "intervention", "reunion"]):
        add("L3121-1", "temps de travail effectif", 82)
    if is_cse_meeting_query(query):
        add("L3121-1", "CSE pendant repos: qualifier le temps de travail", 90)
        add("L3131-1", "CSE pendant repos: verifier le repos quotidien", 89)
        add("L3132-1", "CSE pendant repos: verifier le repos hebdomadaire", 82)

    if not selected:
        for item in CODE_TRAVAIL_MINI_INDEX:
            if any(normalize_text(keyword) in text for keyword in item.get("keywords", [])):
                selected.append(
                    {
                        "official_id": item["article_id"],
                        "article": item["article"],
                        "title": CODE_DU_TRAVAIL_LABEL,
                        "excerpt": "",
                        "score": 60,
                        "topic": item["topic"],
                        "reason": "mot-cle du mini-index Code du travail",
                    }
                )

    return dedupe_hits(sorted(selected, key=lambda item: int(item.get("score") or 0), reverse=True))[: max(1, limit)]


def jurisprudence_mini_index_hits(query: str, limit: int) -> list[dict[str, Any]]:
    text = normalize_text(query)
    selected: list[dict[str, Any]] = []

    def add(topic: str, reason: str, score: int) -> None:
        for item in JURISPRUDENCE_MINI_INDEX:
            if item["topic"] == topic:
                selected.append({**item, "reason": reason, "score": score})
                return

    if "astreinte" in text:
        add("repos_temps_travail", "astreinte: verifier surtout repos et reprise du poste en V1", 100)
        add("temps_travail_effectif", "astreinte: qualifier le temps d'intervention en V1", 96)
    if any(term in text for term in ["repos", "reprise", "nuit", "5x8", "hebdomadaire", "quotidien"]):
        add("repos_temps_travail", "repos quotidien ou hebdomadaire", 94)
    if any(term in text for term in ["temps de travail", "travail effectif", "intervention", "reunion"]):
        add("temps_travail_effectif", "qualification du temps de travail effectif", 88)
    if any(term in text for term in ["heure supplementaire", "heures supplementaires", "majoration", "bulletin", "paie"]):
        add("heures_supplementaires", "heures supplementaires, preuve ou bulletin", 86)
    if "dimanche" in text:
        add("travail_dimanche", "travail du dimanche, compensation ou majoration", 84)
    if any(term in text for term in ["prime", "remuneration variable", "variable", "salaire"]):
        add("prime_variable", "prime ou element variable de remuneration", 82)
    if any(term in text for term in ["classification", "coefficient", "fiche de poste", "fonctions", "responsabilite"]):
        add("classification_fonctions_reelles", "classification et fonctions reellement exercees", 90)
    if any(term in text for term in ["cse", "comite social economique", "delegation", "mandat", "elu"]):
        add("cse_temps_reunion_mandat", "CSE, mandat et temps de reunion", 110)

    if not selected:
        for item in JURISPRUDENCE_MINI_INDEX:
            if any(normalize_text(keyword) in text for keyword in item.get("keywords", [])):
                selected.append({**item, "reason": "mot-cle du mini-index jurisprudence", "score": 60})

    return dedupe_topic_hits(sorted(selected, key=lambda item: int(item.get("score") or 0), reverse=True))[: max(1, limit)]


def is_cse_meeting_query(query: str) -> bool:
    text = normalize_text(query)
    return "cse" in text and any(term in text for term in ["reunion", "repos", "5x8", "delegation", "elu"])


def current_version_id(payload: Any) -> str | None:
    article = payload.get("article") if isinstance(payload, dict) else None
    if not isinstance(article, dict):
        return None
    versions = article.get("articleVersions")
    if not isinstance(versions, list):
        return None
    for version in reversed(versions):
        if not isinstance(version, dict):
            continue
        etat = normalize_text(version.get("etat"))
        candidate = version.get("id")
        if candidate and "vigueur" in etat:
            return str(candidate)
    return None


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


def extract_jurisprudence_hits(payload: Any) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    results = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(results, list):
        return hits
    for node in results:
        if not isinstance(node, dict):
            continue
        title = first_jurisprudence_title(node)
        official_id = first_jurisprudence_id(node)
        if not title or not official_id or not is_cassation_sociale_title(title):
            continue
        principle = best_jurisprudence_principle(node)
        excerpt = best_jurisprudence_excerpt(node, principle)
        metadata = parse_jurisprudence_title(title)
        hits.append(
            {
                "official_id": official_id,
                "document": title,
                "title": title,
                "juridiction": metadata.get("juridiction") or "Cour de cassation",
                "chamber": metadata.get("chamber") or "Chambre sociale",
                "decision_date": metadata.get("decision_date"),
                "case_number": metadata.get("case_number"),
                "solution": clean_text_value(node.get("solution")),
                "theme": clean_text_value(node.get("themes")) or clean_text_value(node.get("motsCles")),
                "principle_summary": principle,
                "excerpt": excerpt,
                "score": node.get("score") or node.get("pertinence"),
                "raw_origin": node.get("origin"),
                "publication": "Publié au bulletin" if "publie au bulletin" in normalize_text(title) else None,
            }
        )
    return hits


def normalize_jurisprudence_source(hit: dict[str, Any], topic: dict[str, Any]) -> dict[str, Any] | None:
    official_id = hit.get("official_id")
    if not official_id:
        return None
    title = strip_markup(hit.get("title") or hit.get("document") or JURISPRUDENCE_LABEL)
    decision_date = hit.get("decision_date")
    case_number = hit.get("case_number")
    location_parts = [part for part in [decision_date, f"pourvoi {case_number}" if case_number else None] if part]
    principle = short_excerpt(hit.get("principle_summary") or hit.get("excerpt") or "", 500)
    warning = None
    if not hit.get("principle_summary"):
        warning = "Principe resume non fourni distinctement par la recherche Legifrance: verifier la decision complete."
    ranking_reasons = [
        "Source officielle Legifrance via API PISTE",
        "Recherche jurisprudence fond JURI",
        "Filtre Nexus: Cour de cassation, chambre sociale",
        "Mini-index jurisprudence V1",
    ]
    if topic.get("label"):
        ranking_reasons.append("theme: " + str(topic["label"]))
    if topic.get("reason"):
        ranking_reasons.append(str(topic["reason"]))
    return {
        "document": title,
        "document_type": "jurisprudence",
        "source_layer": "jurisprudence",
        "source_layer_label": "Jurisprudence",
        "juridiction": hit.get("juridiction") or "Cour de cassation",
        "chamber": hit.get("chamber") or "Chambre sociale",
        "decision_date": decision_date,
        "case_number": case_number,
        "theme": topic.get("label") or hit.get("theme"),
        "principle_summary": principle,
        "solution": hit.get("solution"),
        "article": " | ".join(location_parts) if location_parts else case_number,
        "article_or_section": " | ".join(location_parts) if location_parts else case_number,
        "official_id": official_id,
        "legifrance_id": official_id,
        "retrieved_at": utc_now(),
        "url": f"https://www.legifrance.gouv.fr/juri/id/{official_id}",
        "excerpt": short_excerpt(hit.get("excerpt") or principle),
        "chunk_id": official_id,
        "score": hit.get("score") or topic.get("score"),
        "ranking_reasons": ranking_reasons,
        "source_quality_warning": warning,
    }


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


def first_jurisprudence_id(value: Any) -> str | None:
    if isinstance(value, dict):
        for key in ["id", "cid", "jurisprudenceId", "idDecision", "official_id"]:
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.startswith("JURITEXT"):
                return candidate
        for child in value.values():
            found = first_jurisprudence_id(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = first_jurisprudence_id(child)
            if found:
                return found
    elif isinstance(value, str):
        match = re.search(r"JURITEXT\d+", value)
        if match:
            return match.group(0)
    return None


def first_jurisprudence_title(value: dict[str, Any]) -> str | None:
    titles = value.get("titles")
    if isinstance(titles, list):
        for title in titles:
            if isinstance(title, dict):
                candidate = title.get("title")
                if isinstance(candidate, str) and candidate.strip():
                    return strip_markup(candidate)
            elif isinstance(title, str) and title.strip():
                return strip_markup(title)
    return clean_text_value(value.get("title") or value.get("titre"))


def is_cassation_sociale_title(title: str) -> bool:
    normalized = normalize_text(title)
    return "cour de cassation" in normalized and "chambre sociale" in normalized


def parse_jurisprudence_title(title: str) -> dict[str, Any]:
    cleaned = strip_markup(title)
    return {
        "juridiction": "Cour de cassation" if "cour de cassation" in normalize_text(cleaned) else first_title_part(cleaned),
        "chamber": parse_chamber(cleaned),
        "decision_date": parse_french_date(cleaned),
        "case_number": parse_case_number(cleaned),
    }


def first_title_part(title: str) -> str | None:
    part = strip_markup(title).split(",", 1)[0].strip()
    return part or None


def parse_chamber(title: str) -> str | None:
    match = re.search(r"Chambre\s+sociale", strip_markup(title), flags=re.IGNORECASE)
    if match:
        return "Chambre sociale"
    return None


def parse_french_date(text: str) -> str | None:
    match = re.search(
        r"\b(\d{1,2})\s+([A-Za-zÀ-ÖØ-öø-ÿ]+)\s+(\d{4})\b",
        strip_markup(text),
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    day, month, year = match.groups()
    month_number = FRENCH_MONTHS.get(month.casefold())
    if not month_number:
        return None
    return f"{year}-{month_number}-{int(day):02d}"


def parse_case_number(text: str) -> str | None:
    matches = re.findall(r"\b\d{2}-\d{2}\.\d{3}\b", strip_markup(text))
    if not matches:
        return None
    return " ".join(matches)


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


def clean_text_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = strip_markup(value)
        return cleaned or None
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        parts = [clean_text_value(item) for item in value]
        joined = " ".join(part for part in parts if part)
        return strip_markup(joined) or None
    if isinstance(value, dict):
        for key in ["text", "texte", "value", "valeur", "title", "titre", "resume", "label"]:
            cleaned = clean_text_value(value.get(key))
            if cleaned:
                return cleaned
        parts = [clean_text_value(item) for item in value.values()]
        joined = " ".join(part for part in parts if part)
        return strip_markup(joined) or None
    return strip_markup(value) or None


def best_jurisprudence_principle(payload: dict[str, Any]) -> str | None:
    direct = clean_text_value(payload.get("resumePrincipal"))
    if direct:
        return short_excerpt(direct, 700)
    for field in ["Résumé principal", "Resume principal", "Sommaire", "Abstrat", "Résumé autre", "Resume autre"]:
        extracted = section_extract_text(payload, field)
        if extracted:
            return short_excerpt(extracted, 700)
    other = clean_text_value(payload.get("autreResume"))
    if other:
        return short_excerpt(other, 700)
    return None


def best_jurisprudence_excerpt(payload: dict[str, Any], principle: str | None = None) -> str:
    text = clean_text_value(payload.get("text"))
    if text:
        return short_excerpt(text, 900)
    if principle:
        return short_excerpt(principle, 900)
    values: list[str] = []
    for section in payload.get("sections") or []:
        if not isinstance(section, dict):
            continue
        for extract in section.get("extracts") or []:
            cleaned = clean_text_value((extract or {}).get("values"))
            if cleaned:
                values.append(cleaned)
    return short_excerpt(" ".join(values), 900)


def section_extract_text(payload: dict[str, Any], field_name: str) -> str | None:
    expected = normalize_text(field_name)
    for section in payload.get("sections") or []:
        if not isinstance(section, dict):
            continue
        for extract in section.get("extracts") or []:
            if not isinstance(extract, dict):
                continue
            name = normalize_text(extract.get("searchFieldName"))
            if name != expected:
                continue
            cleaned = clean_text_value(extract.get("values"))
            if cleaned:
                return cleaned
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
    value = first_value_for_keys(payload, keys)
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value) / 1000, tz=timezone.utc).date().isoformat()
        except (OSError, OverflowError, ValueError):
            return None
    if isinstance(value, str) and value.strip():
        stripped = value.strip()
        if stripped.isdigit():
            try:
                return datetime.fromtimestamp(float(stripped) / 1000, tz=timezone.utc).date().isoformat()
            except (OSError, OverflowError, ValueError):
                return None
        return stripped[:10]
    return None


def first_value_for_keys(value: Any, keys: list[str]) -> Any | None:
    if isinstance(value, dict):
        lower_keys = {key.lower() for key in keys}
        for key, candidate in value.items():
            if key.lower() in lower_keys and candidate not in (None, ""):
                return candidate
        for child in value.values():
            found = first_value_for_keys(child, keys)
            if found not in (None, ""):
                return found
    elif isinstance(value, list):
        for child in value:
            found = first_value_for_keys(child, keys)
            if found not in (None, ""):
                return found
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
    if etat and normalize_text(etat) != "vigueur":
        warning = f"Article en etat {etat}: verifier la version applicable sur Legifrance."
    if in_force is None:
        warning = "Etat de vigueur non determine automatiquement: verifier la fiche Legifrance."
    if not text:
        warning = "Texte de l'article non extrait: verifier la fiche Legifrance."
    ranking_reasons = [
        "Source officielle Legifrance via API PISTE",
        "Mini-index Code du travail V1",
    ]
    if (search_hit or {}).get("topic"):
        ranking_reasons.append("theme: " + str(search_hit["topic"]))
    if (search_hit or {}).get("reason"):
        ranking_reasons.append(str(search_hit["reason"]))
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
        "ranking_reasons": ranking_reasons,
        "source_quality_warning": warning,
    }


def code_source_quality_warning(source: dict[str, Any]) -> str | None:
    article = str(source.get("article") or source.get("article_or_section") or "").strip()
    official_id = str(source.get("official_id") or source.get("legifrance_id") or "").strip()
    etat = str(source.get("etat") or "").strip()
    excerpt = strip_markup(source.get("excerpt") or "")
    normalized_excerpt = normalize_text(excerpt)
    if not article:
        return "article absent"
    if not official_id:
        return "identifiant officiel Legifrance absent"
    if not etat:
        return "etat de vigueur absent"
    if len(normalized_excerpt) < 40 or normalized_excerpt in {"code du travail", normalize_text(article)}:
        return "extrait utile absent"
    return None


def is_usable_code_source(source: dict[str, Any]) -> bool:
    return code_source_quality_warning(source) is None


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
        key = str(
            hit.get("official_id")
            or hit.get("article")
            or hit.get("search_query")
            or hit.get("topic")
            or ""
        )
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(hit)
    return result


def dedupe_topic_hits(hits: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for hit in hits:
        topic = str(hit.get("topic") or "")
        if not topic or topic in seen:
            continue
        seen.add(topic)
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
