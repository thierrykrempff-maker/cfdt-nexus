#!/usr/bin/env python
"""Prototype connector for official practical explanations.

This connector is intentionally not integrated into the Nexus router. It only
tests the public Code du travail numerique presearch endpoint and normalizes
official practical results as source_layer=pratique_officielle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import socket
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

ENV_API_BASE_URL = "CFDT_NEXUS_PRATIQUE_OFFICIELLE_API_BASE_URL"
ENV_TIMEOUT = "CFDT_NEXUS_PRATIQUE_OFFICIELLE_TIMEOUT"
ENV_CACHE_DIR = "CFDT_NEXUS_PRATIQUE_OFFICIELLE_CACHE_DIR"
ENV_CACHE_TTL = "CFDT_NEXUS_PRATIQUE_OFFICIELLE_CACHE_TTL_SECONDS"
ENV_MAX_RESPONSE_BYTES = "CFDT_NEXUS_PRATIQUE_OFFICIELLE_MAX_RESPONSE_BYTES"
ENV_ALLOW_LOCAL_TEST_BASE_URL = "CFDT_NEXUS_PRATIQUE_OFFICIELLE_ALLOW_LOCAL_TEST_BASE_URL"

DEFAULT_API_BASE_URL = "https://code.travail.gouv.fr"
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_CACHE_TTL_SECONDS = 24 * 60 * 60
# 1 MB is intentionally generous for /api/presearch metadata while preventing
# accidental parsing of an abnormal or unrelated payload.
DEFAULT_MAX_RESPONSE_BYTES = 1_000_000
PRESEARCH_ENDPOINT = "/api/presearch"
SOURCE_LAYER = "pratique_officielle"
OFFICIAL_API_HOST = "code.travail.gouv.fr"
LOCAL_TEST_HOSTS = {"localhost", "127.0.0.1", "::1"}
OFFICIAL_CONTENT_LICENSE = "Licence Ouverte Etalab 2.0"
OFFICIAL_CONTENT_ATTRIBUTION = "Code du travail numérique – ministère du Travail"
OFFICIAL_DISCLAIMER = "Nexus n'est pas cautionné par l'administration."

OFFICIAL_SOURCES: dict[str, dict[str, str]] = {
    "fiches_service_public": {
        "label": "Service-Public.fr",
        "quality": "fiche pratique officielle",
    },
    "fiches_ministere_travail": {
        "label": "Ministere du Travail / Code du travail numerique",
        "quality": "fiche pratique officielle",
    },
    "contributions": {
        "label": "Code du travail numerique",
        "quality": "reponse pratique officielle",
    },
    "themes": {
        "label": "Code du travail numerique",
        "quality": "theme de navigation officiel",
    },
}

SCENARIOS: list[dict[str, str]] = [
    {"id": "astreinte_repos", "query": "astreinte repos", "theme": "Astreinte et repos"},
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
        "id": "classification_professionnelle",
        "query": "classification coefficient convention collective salaire minimum",
        "theme": "Classification professionnelle",
    },
]


class PratiqueOfficielleError(RuntimeError):
    """Base class for expected connector failures."""


class PratiqueOfficielleAPIError(PratiqueOfficielleError):
    """Raised when the public endpoint returns an unusable response."""


class PratiqueOfficielleSecurityError(PratiqueOfficielleError):
    """Raised when configuration would make an unofficial source look official."""


@dataclass(frozen=True)
class PratiqueOfficielleConfig:
    api_base_url: str = DEFAULT_API_BASE_URL
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    cache_dir: Path = ROOT / "local-index" / "pratique-officielle"
    cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS
    max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES
    allow_local_test_base_url: bool = False

    @classmethod
    def from_env(cls) -> "PratiqueOfficielleConfig":
        timeout = parse_int(os.environ.get(ENV_TIMEOUT), DEFAULT_TIMEOUT_SECONDS)
        cache_ttl = parse_int(os.environ.get(ENV_CACHE_TTL), DEFAULT_CACHE_TTL_SECONDS)
        max_response_bytes = parse_int(os.environ.get(ENV_MAX_RESPONSE_BYTES), DEFAULT_MAX_RESPONSE_BYTES)
        cache_dir = Path(os.environ.get(ENV_CACHE_DIR) or ROOT / "local-index" / "pratique-officielle")
        return cls(
            api_base_url=(os.environ.get(ENV_API_BASE_URL) or DEFAULT_API_BASE_URL).strip().rstrip("/"),
            timeout_seconds=timeout,
            cache_dir=cache_dir,
            cache_ttl_seconds=cache_ttl,
            max_response_bytes=max_response_bytes,
            allow_local_test_base_url=parse_bool(os.environ.get(ENV_ALLOW_LOCAL_TEST_BASE_URL)),
        )

    def endpoint_url(self, endpoint: str, params: dict[str, str] | None = None) -> str:
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        url = self.api_base_url.rstrip("/") + endpoint
        if params:
            url += "?" + urllib.parse.urlencode(params)
        return url


class PratiqueOfficielleClient:
    def __init__(self, config: PratiqueOfficielleConfig | None = None) -> None:
        self.config = config or PratiqueOfficielleConfig.from_env()
        self.cache_warnings: list[str] = []

    def search_sources(self, query: str, limit: int = 5, theme: str | None = None) -> dict[str, Any]:
        self.cache_warnings = []
        cleaned_query = compact_text(query)
        if not cleaned_query:
            return unavailable_result("Question vide: aucune recherche pratique officielle.")

        try:
            payload = self.presearch(cleaned_query)
        except PratiqueOfficielleError as exc:
            return unavailable_result(str(exc))

        hits = payload.get("results")
        if not isinstance(hits, list):
            return unavailable_result("Reponse Code du travail numerique sans liste results exploitable.")

        normalized = []
        for hit in hits:
            if not isinstance(hit, dict):
                continue
            source = hit.get("source")
            if source not in OFFICIAL_SOURCES:
                continue
            normalized.append(normalize_hit(hit, cleaned_query, theme))
            if len(normalized) >= limit:
                break

        warnings = list(self.cache_warnings)
        if not normalized:
            warnings.append("Aucun contenu pratique officiel pertinent remonte par /api/presearch.")
        if normalized:
            warnings.append(
                "Prototype V1: /api/presearch fournit surtout titre, resume et URL; "
                "le corps complet des fiches n'est pas recupere sans autre API stable."
            )

        return {
            "available": True,
            "endpoint": self.config.endpoint_url(PRESEARCH_ENDPOINT),
            "query": cleaned_query,
            "theme": theme,
            "sources": normalized,
            "warnings": warnings,
            "retrieved_at": utc_now(),
        }

    def presearch(self, query: str) -> dict[str, Any]:
        validate_api_base_url(self.config.api_base_url, self.config.allow_local_test_base_url)
        cache_key = stable_hash(
            {"endpoint": PRESEARCH_ENDPOINT, "query": query, "api_base_url": self.config.api_base_url}
        )
        cached = self.read_response_cache(cache_key)
        if cached is not None:
            return cached

        url = self.config.endpoint_url(PRESEARCH_ENDPOINT, {"q": query})
        request = urllib.request.Request(url, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                status = getattr(response, "status", 200)
                body_bytes = read_limited_response(response, self.config.max_response_bytes)
        except urllib.error.HTTPError as exc:
            raise PratiqueOfficielleAPIError(f"HTTP {exc.code} sur {PRESEARCH_ENDPOINT}") from exc
        except urllib.error.URLError as exc:
            raise PratiqueOfficielleAPIError(f"Connexion impossible a {PRESEARCH_ENDPOINT}: {exc.reason}") from exc
        except (TimeoutError, socket.timeout) as exc:
            raise PratiqueOfficielleAPIError(f"Timeout sur {PRESEARCH_ENDPOINT}") from exc

        if status >= 400:
            raise PratiqueOfficielleAPIError(f"HTTP {status} sur {PRESEARCH_ENDPOINT}")
        if len(body_bytes) > self.config.max_response_bytes:
            raise PratiqueOfficielleAPIError(
                f"Reponse trop volumineuse sur {PRESEARCH_ENDPOINT}: limite {self.config.max_response_bytes} octets"
            )
        body = body_bytes.decode("utf-8", errors="replace")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise PratiqueOfficielleAPIError("Reponse non JSON sur /api/presearch") from exc
        if not isinstance(payload, dict):
            raise PratiqueOfficielleAPIError("Reponse JSON sans objet racine exploitable sur /api/presearch")

        self.write_response_cache(cache_key, payload)
        return payload

    def response_cache_path(self, cache_key: str) -> Path:
        return self.config.cache_dir / "responses" / f"{cache_key}.json"

    def read_response_cache(self, cache_key: str) -> dict[str, Any] | None:
        path = self.response_cache_path(cache_key)
        try:
            if not path.exists():
                return None
            if self.config.cache_ttl_seconds > 0 and time.time() - path.stat().st_mtime > self.config.cache_ttl_seconds:
                return None
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.cache_warnings.append("Cache pratique officielle ignore: lecture impossible ou JSON invalide.")
            return None
        if not isinstance(payload, dict):
            self.cache_warnings.append("Cache pratique officielle ignore: structure JSON inattendue.")
            return None
        if "results" not in payload:
            self.cache_warnings.append("Cache pratique officielle ignore: structure incomplete.")
            return None
        return payload

    def write_response_cache(self, cache_key: str, payload: dict[str, Any]) -> None:
        path = self.response_cache_path(cache_key)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = path.with_suffix(path.suffix + ".tmp")
            tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp_path.replace(path)
        except OSError:
            self.cache_warnings.append("Cache pratique officielle non ecrit: dossier inaccessible ou erreur disque.")


def normalize_hit(hit: dict[str, Any], query: str, theme: str | None) -> dict[str, Any]:
    source_key = str(hit.get("source") or "")
    source_meta = OFFICIAL_SOURCES.get(source_key, {"label": source_key, "quality": "source officielle"})
    description = compact_text(hit.get("description") or "")
    title = compact_text(hit.get("title") or "")
    slug = compact_text(hit.get("slug") or "")
    cdtn_id = compact_text(hit.get("cdtnId") or "")
    url = compact_text(hit.get("url") or "") or build_content_url(source_key, slug, hit)
    breadcrumbs = normalize_breadcrumbs(hit.get("breadcrumbs"))
    updated_at = compact_text(hit.get("date") or hit.get("date_publi") or "")
    reference = cdtn_id or (f"{source_key}:{slug}" if slug else source_key)
    quality_warning = None
    if not description:
        quality_warning = "Resultat sans resume exploitable dans /api/presearch."
    elif source_key == "themes":
        quality_warning = "Theme de navigation: utile pour orienter, mais pas une fiche de fond."

    return {
        "document": title or source_meta["label"],
        "title": title,
        "theme": theme or theme_from_breadcrumbs(breadcrumbs),
        "summary": description,
        "contenu_utile": description,
        "excerpt": description,
        "source_officielle": source_meta["label"],
        "source_key": source_key,
        "document_type": "explication_pratique_officielle",
        "source_layer": SOURCE_LAYER,
        "source_layer_label": "Explication pratique officielle",
        "source_quality": source_meta["quality"],
        "source_quality_warning": quality_warning,
        "license": OFFICIAL_CONTENT_LICENSE,
        "attribution": OFFICIAL_CONTENT_ATTRIBUTION,
        "official_disclaimer": OFFICIAL_DISCLAIMER,
        "updated_at": updated_at or None,
        "retrieved_at": utc_now(),
        "official_id": reference,
        "reference": reference,
        "cdtn_id": cdtn_id or None,
        "slug": slug or None,
        "url": url or None,
        "breadcrumbs": breadcrumbs,
        "query": query,
        "ranking_reasons": [
            "Resultat issu du endpoint public Code du travail numerique /api/presearch",
            f"Source officielle: {source_meta['label']}",
            "Normalise pour Nexus sans remplacer les sources juridiques opposables",
        ],
    }


def build_content_url(source_key: str, slug: str, hit: dict[str, Any]) -> str | None:
    if not slug:
        return None
    base = DEFAULT_API_BASE_URL
    if source_key == "fiches_ministere_travail":
        return f"{base}/fiche-ministere-travail/{slug.split('#', 1)[0]}"
    if source_key == "contributions":
        return f"{base}/contribution/{slug}"
    if source_key == "themes":
        parent_slug = compact_text(hit.get("parentSlug") or "")
        if parent_slug:
            return f"{base}/themes/{parent_slug}#{slug}"
        return f"{base}/themes/{slug}"
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
                "label": compact_text(item.get("label") or ""),
                "position": item.get("position"),
                "slug": compact_text(item.get("slug") or ""),
            }
        )
    return breadcrumbs


def theme_from_breadcrumbs(breadcrumbs: list[dict[str, Any]]) -> str | None:
    labels = [item.get("label") for item in breadcrumbs if item.get("label")]
    return " > ".join(str(label) for label in labels) if labels else None


def unavailable_result(warning: str) -> dict[str, Any]:
    return {
        "available": False,
        "endpoint": DEFAULT_API_BASE_URL + PRESEARCH_ENDPOINT,
        "sources": [],
        "warnings": [warning],
        "retrieved_at": utc_now(),
    }


def compact_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return text.lower()


def parse_int(value: str | None, default: int) -> int:
    try:
        parsed = int(str(value or "").strip())
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def parse_bool(value: str | None) -> bool:
    return normalize_text(value) in {"1", "true", "yes", "oui", "on"}


def validate_api_base_url(api_base_url: str, allow_local_test_base_url: bool = False) -> None:
    parsed = urllib.parse.urlparse(api_base_url)
    host = (parsed.hostname or "").lower()
    try:
        port = parsed.port
    except ValueError as exc:
        raise PratiqueOfficielleSecurityError("URL pratique officielle invalide: port incorrect.") from exc
    has_clean_base = (
        not parsed.username
        and not parsed.password
        and parsed.path in {"", "/"}
        and not parsed.params
        and not parsed.query
        and not parsed.fragment
    )
    if parsed.scheme not in {"http", "https"} or not host or not has_clean_base:
        raise PratiqueOfficielleSecurityError("URL pratique officielle invalide: scheme HTTP(S) et domaine requis.")
    if parsed.scheme == "https" and host == OFFICIAL_API_HOST and port is None:
        return
    if allow_local_test_base_url and host in LOCAL_TEST_HOSTS:
        return
    raise PratiqueOfficielleSecurityError(
        "Domaine pratique officielle non autorise: seul code.travail.gouv.fr est accepte "
        "(localhost uniquement avec le mode test explicite)."
    )


def read_limited_response(response: Any, max_bytes: int) -> bytes:
    header_value = response_header(response, "Content-Length")
    if header_value:
        try:
            declared_size = int(header_value)
        except ValueError:
            declared_size = None
        if declared_size is not None and declared_size > max_bytes:
            raise PratiqueOfficielleAPIError(
                f"Reponse trop volumineuse sur {PRESEARCH_ENDPOINT}: limite {max_bytes} octets"
            )

    chunks: list[bytes] = []
    total = 0
    while True:
        remaining = max_bytes - total
        read_size = 1 if remaining <= 0 else min(64 * 1024, remaining)
        chunk = response.read(read_size)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise PratiqueOfficielleAPIError(
                f"Reponse trop volumineuse sur {PRESEARCH_ENDPOINT}: limite {max_bytes} octets"
            )
        chunks.append(chunk)
    return b"".join(chunks)


def response_header(response: Any, name: str) -> str | None:
    if hasattr(response, "headers"):
        value = response.headers.get(name)
        if value is not None:
            return str(value)
    getheader = getattr(response, "getheader", None)
    if callable(getheader):
        value = getheader(name)
        if value is not None:
            return str(value)
    return None


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_prototype(limit: int = 4) -> dict[str, Any]:
    client = PratiqueOfficielleClient()
    rows = []
    for scenario in SCENARIOS:
        result = client.search_sources(scenario["query"], limit=limit, theme=scenario["theme"])
        rows.append(
            {
                "id": scenario["id"],
                "query": scenario["query"],
                "theme": scenario["theme"],
                "available": result.get("available"),
                "source_count": len(result.get("sources", [])),
                "sources": result.get("sources", []),
                "warnings": result.get("warnings", []),
            }
        )
    return {
        "source_layer": SOURCE_LAYER,
        "endpoint": PratiqueOfficielleConfig.from_env().endpoint_url(PRESEARCH_ENDPOINT),
        "scenario_count": len(rows),
        "rows": rows,
        "retrieved_at": utc_now(),
    }


def format_result_text(result: dict[str, Any]) -> str:
    lines = [
        "COUCHE PRATIQUE OFFICIELLE - PROTOTYPE",
        f"Endpoint : {result.get('endpoint')}",
        f"source_layer : {result.get('source_layer', SOURCE_LAYER)}",
        "",
    ]
    rows = result.get("rows") or [{"id": "search", **result}]
    for row in rows:
        lines.append(f"{row.get('id')} - {row.get('theme') or row.get('query')}")
        lines.append(f"- sources : {row.get('source_count', len(row.get('sources', [])))}")
        for source in row.get("sources", [])[:4]:
            url = f" | {source.get('url')}" if source.get("url") else ""
            warning = f" | limite: {source.get('source_quality_warning')}" if source.get("source_quality_warning") else ""
            lines.append(
                f"- {source.get('source_officielle')} | {source.get('title')} | "
                f"{source.get('source_key')} | {source.get('summary')}{url}{warning}"
            )
        for warning in row.get("warnings", [])[:3]:
            lines.append(f"- avertissement : {warning}")
        lines.append("")
    return "\n".join(lines).strip()


def emit(data: dict[str, Any], fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(format_result_text(data))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Nexus - prototype pratique officielle V1")
    sub = parser.add_subparsers(dest="command", required=True)

    p_search = sub.add_parser("search")
    p_search.add_argument("--query", required=True)
    p_search.add_argument("--theme")
    p_search.add_argument("--limit", type=int, default=4)
    p_search.add_argument("--format", choices=["text", "json"], default="text")

    p_proto = sub.add_parser("prototype")
    p_proto.add_argument("--limit", type=int, default=4)
    p_proto.add_argument("--format", choices=["text", "json"], default="text")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    client = PratiqueOfficielleClient()
    if args.command == "search":
        result = client.search_sources(args.query, limit=args.limit, theme=args.theme)
        result["source_layer"] = SOURCE_LAYER
        emit(result, args.format)
        return 0 if result.get("available") else 1
    if args.command == "prototype":
        emit(run_prototype(limit=args.limit), args.format)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
