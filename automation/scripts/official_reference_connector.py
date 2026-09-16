#!/usr/bin/env python
"""Shared engine for small curated-reference connectors (CNIL-style pattern).

Several official bodies (CNIL, CARSAT, DREETS, INRS...) do not expose a public
search API the way Legifrance/Judilibre/CDTN do. For these, Nexus uses a
mini-connector: a small, hand-picked and individually verified list of public
pages relevant to union/CSE/CSSCT work. At query time it fetches the live
content (HTML or PDF) of the pages that match the question and extracts the
real title and a short excerpt.

It never invents content: every title/excerpt/url returned comes straight
from the fetched page, or the source is marked unavailable. This module holds
the reusable fetch/cache/scoring machinery; each connector (cnil_connector.py,
carsat_connector.py, dreets_connector.py, inrs_connector.py...) supplies its
own curated CNIL_PAGES-equivalent list and a thin config.
"""

from __future__ import annotations

import hashlib
import html
import io
import json
import re
import time
import unicodedata
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_CACHE_TTL_SECONDS = 7 * 24 * 60 * 60  # official reference pages change rarely.
DEFAULT_LIMIT = 3
SOURCE_LAYER = "pratique_officielle"
USER_AGENT = "CFDT-Nexus/1.0 (usage syndical interne, non commercial)"


class OfficialReferenceError(RuntimeError):
    """Base class for expected official-reference connector failures."""


class OfficialReferenceFetchError(OfficialReferenceError):
    """Raised when a reference page cannot be fetched or parsed."""


@dataclass(frozen=True)
class OfficialReferenceConfig:
    connector_id: str
    source_officielle: str
    official_origin: str
    cache_dir: Path
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS


class OfficialReferenceClient:
    """Generic client for a curated list of official reference pages."""

    def __init__(self, config: OfficialReferenceConfig, pages: list[dict[str, Any]]) -> None:
        self.config = config
        self.pages = pages

    def search_sources(self, query: str, limit: int = DEFAULT_LIMIT) -> dict[str, Any]:
        cleaned_query = compact_text(query)
        if not cleaned_query:
            return unavailable_result(self.config, "Question vide : aucune recherche.")

        query_norm = normalize_text(cleaned_query)
        scored = []
        for page in self.pages:
            score, hits = page_relevance_score(page, query_norm)
            if score > 0:
                scored.append((score, page, hits))
        if not scored:
            return unavailable_result(
                self.config,
                f"Aucune page {self.config.source_officielle} du corpus cible ne correspond a cette question.",
                query=cleaned_query,
            )
        scored.sort(key=lambda item: item[0], reverse=True)

        sources: list[dict[str, Any]] = []
        warnings: list[str] = []
        for score, page, hits in scored[: max(1, limit)]:
            try:
                fetched = self.fetch_page(page["url"])
            except OfficialReferenceError as exc:
                warnings.append(f"{page['id']} indisponible : {exc}")
                continue
            sources.append(normalize_reference_source(self.config, page, fetched, hits, score))

        if not sources:
            return unavailable_result(
                self.config,
                f"Pages {self.config.source_officielle} ciblees identifiees mais indisponibles (reseau).",
                query=cleaned_query,
            )
        return {
            "available": True,
            "source_layer": SOURCE_LAYER,
            "query": cleaned_query,
            "source_count": len(sources),
            "sources": sources,
            "warnings": warnings,
            "retrieved_at": utc_now(),
        }

    def fetch_page(self, url: str) -> dict[str, Any]:
        cache_key = stable_hash({"url": url})
        cached = self.read_response_cache(cache_key)
        if cached is not None:
            return cached

        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:  # noqa: S310
                status = getattr(response, "status", 200)
                body = response.read()
                content_type = response.headers.get("Content-Type", "")
        except urllib.error.HTTPError as exc:
            raise OfficialReferenceFetchError(f"HTTP {exc.code} sur {url}") from exc
        except urllib.error.URLError as exc:
            raise OfficialReferenceFetchError(f"Connexion impossible a {url}: {safe_reason(exc)}") from exc
        except TimeoutError as exc:
            raise OfficialReferenceFetchError(f"Timeout sur {url}") from exc
        if status >= 400:
            raise OfficialReferenceFetchError(f"HTTP {status} sur {url}")

        if url.lower().endswith(".pdf") or "application/pdf" in content_type.lower():
            payload = extract_pdf_payload(body, url)
        else:
            text_body = body.decode("utf-8", errors="replace")
            payload = {
                "title": extract_title(text_body),
                "description": extract_meta_description(text_body),
                "updated_at": extract_updated_at(text_body),
            }
        payload["fetched_at"] = utc_now()
        self.write_response_cache(cache_key, payload)
        return payload

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


def page_relevance_score(page: dict[str, Any], query_norm: str) -> tuple[float, list[str]]:
    score = 0.0
    hits: list[str] = []
    for keyword in page["keywords"]:
        if normalize_text(keyword) in query_norm:
            score += 10.0
            hits.append(keyword)
    return score, hits


def normalize_reference_source(
    config: OfficialReferenceConfig,
    page: dict[str, Any],
    fetched: dict[str, Any],
    hits: list[str],
    score: float,
) -> dict[str, Any]:
    title = fetched.get("title") or page["id"]
    description = fetched.get("description")
    return {
        "document": title,
        "document_type": f"reference_{config.connector_id}",
        "source_layer": SOURCE_LAYER,
        "source_layer_label": "Explication pratique officielle",
        "title": title,
        "summary": description,
        "excerpt": description,
        "content_type": f"page de reference {config.source_officielle}",
        "source_officielle": config.source_officielle,
        "official_origin": config.official_origin,
        "url": page["url"],
        "url_or_id": page["url"],
        "official_id": page["id"],
        "reference": page["id"],
        "updated_at": fetched.get("updated_at"),
        "retrieved_at": fetched.get("fetched_at"),
        "score": score,
        "ranking_reasons": (
            [f"page {config.source_officielle} ciblee correspondant a : {', '.join(hits[:4])}"] if hits else []
        ),
        "full_content_available": False,
        "content_access": "titre_et_extrait_uniquement",
        "complementarity_with_legifrance": (
            f"Reference {config.source_officielle} utile pour la pratique/prevention ; a completer par le Code du "
            "travail, les accords applicables et la jurisprudence pour les aspects juridiques opposables."
        ),
        "contradiction_risk": (
            f"Faible si presentee comme reference {config.source_officielle} distincte des sources juridiques opposables."
        ),
        "source_quality_warning": (
            None
            if description
            else f"Page {config.source_officielle} sans extrait exploitable extrait automatiquement ; ouvrir l'URL pour le contenu complet."
        ),
    }


def unavailable_result(config: OfficialReferenceConfig, warning: str, query: str | None = None) -> dict[str, Any]:
    return {
        "available": False,
        "source_layer": SOURCE_LAYER,
        "query": query,
        "source_count": 0,
        "sources": [],
        "warnings": [warning],
        "retrieved_at": utc_now(),
    }


def extract_pdf_payload(body: bytes, url: str) -> dict[str, Any]:
    try:
        import pypdf
    except ImportError as exc:
        raise OfficialReferenceFetchError(f"pypdf indisponible pour extraire {url}") from exc
    try:
        reader = pypdf.PdfReader(io.BytesIO(body))
        first_page_text = compact_text(reader.pages[0].extract_text()) if reader.pages else ""
        metadata_title = compact_text(getattr(reader.metadata, "title", None) or "")
    except Exception as exc:  # noqa: BLE001 - any pypdf parsing failure is a fetch failure here.
        raise OfficialReferenceFetchError(f"PDF illisible sur {url}: {exc}") from exc
    title = metadata_title or first_page_text[:120] or None
    description = first_page_text[:400] or None
    return {"title": title, "description": description, "updated_at": None}


def extract_title(body: str) -> str | None:
    match = re.search(r"<title[^>]*>(.*?)</title>", body, re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    title = clean_text_value(match.group(1))
    if title:
        title = re.sub(r"\s*\|.*$", "", title).strip()
    return title or None


def extract_meta_description(body: str) -> str | None:
    match = re.search(
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
        body,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        match = re.search(
            r'<meta[^>]+content=["\'](.*?)["\'][^>]+name=["\']description["\']',
            body,
            re.IGNORECASE | re.DOTALL,
        )
    if not match:
        return None
    return clean_text_value(match.group(1))


def extract_updated_at(body: str) -> str | None:
    match = re.search(
        r'<meta[^>]+property=["\']article:modified_time["\'][^>]+content=["\'](.*?)["\']',
        body,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return None
    return clean_text_value(match.group(1))


def clean_text_value(value: Any) -> str | None:
    if value is None:
        return None
    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def compact_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_text(value: Any) -> str:
    text = compact_text(clean_text_value(value)).casefold()
    text = unicodedata.normalize("NFKD", text)
    return "".join(char for char in text if not unicodedata.combining(char))


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_reason(exc: urllib.error.URLError) -> str:
    reason = getattr(exc, "reason", exc)
    return str(reason).replace("\n", " ")[:240]
