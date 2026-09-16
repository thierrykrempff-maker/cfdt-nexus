#!/usr/bin/env python
"""CNIL connector - curated reference pages for workplace personal-data topics.

This is a mini connector, not a crawler: it holds a small, hand-picked and
individually verified list of public CNIL guidance pages relevant to union/CSE
work (videosurveillance, geolocalisation, controle d'acces, cybersurveillance,
communication syndicale, elections professionnelles, registre des traitements,
gestion du personnel, donnees de sante). At query time it fetches the live
HTML of the pages that match the question and extracts the real page title
and meta description as an excerpt.

It never invents CNIL content: every title/excerpt/url returned comes
straight from the fetched page, or the source is marked unavailable. Adding a
new page to CNIL_PAGES requires verifying the URL actually resolves first.
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
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

ENV_TIMEOUT = "CFDT_NEXUS_CNIL_TIMEOUT"
ENV_CACHE_DIR = "CFDT_NEXUS_CNIL_CACHE_DIR"
ENV_CACHE_TTL = "CFDT_NEXUS_CNIL_CACHE_TTL_SECONDS"

DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_CACHE_TTL_SECONDS = 7 * 24 * 60 * 60  # CNIL guidance pages change rarely.
DEFAULT_LIMIT = 3
SOURCE_LAYER = "pratique_officielle"
USER_AGENT = "CFDT-Nexus/1.0 (usage syndical interne, non commercial)"

# Hand-picked CNIL guidance pages relevant to union/CSE work at a manufacturing
# site. Every URL below was checked to resolve (HTTP 200, real CNIL content)
# before being added here. This is not a crawl of cnil.fr: add new pages the
# same way, one verified URL at a time.
CNIL_PAGES: list[dict[str, Any]] = [
    {
        "id": "videosurveillance_travail",
        "url": "https://www.cnil.fr/fr/la-videosurveillance-au-travail",
        "keywords": [
            "videosurveillance", "video surveillance", "camera", "cameras",
            "surveillance video", "video protection",
        ],
    },
    {
        "id": "geolocalisation_vehicules",
        "url": "https://www.cnil.fr/fr/la-geolocalisation-des-vehicules-des-salaries",
        "keywords": [
            "geolocalisation", "geolocalisation vehicule", "vehicule de service",
            "traceur gps", "gps", "suivi vehicule",
        ],
    },
    {
        "id": "controle_horaires_acces",
        "url": "https://www.cnil.fr/fr/lacces-aux-locaux-et-le-controle-des-horaires-sur-le-lieu-de-travail",
        "keywords": [
            "badgeage", "badge", "controle d acces", "controle acces",
            "controle des horaires", "badgeuse", "pointeuse",
        ],
    },
    {
        "id": "controle_acces_biometrique",
        "url": "https://www.cnil.fr/fr/le-controle-dacces-biometrique-sur-les-lieux-de-travail",
        "keywords": [
            "biometrie", "biometrique", "empreinte", "reconnaissance faciale",
            "controle d acces biometrique",
        ],
    },
    {
        "id": "gestion_activite_equipements",
        "url": "https://www.cnil.fr/fr/gestion-de-lactivite-et-des-equipements",
        "keywords": [
            "cybersurveillance", "surveillance informatique", "logiciel de surveillance",
            "capture d ecran", "keylogger", "controle activite", "surveillance des salaries",
        ],
    },
    {
        "id": "intranet_messagerie_syndicats",
        "url": "https://www.cnil.fr/fr/lutilisation-de-lintranet-et-de-la-messagerie-electronique-de-lentreprise-par-les-organisations",
        "keywords": [
            "intranet syndical", "messagerie syndicale", "communication syndicale",
            "tract electronique", "diffusion syndicale", "messagerie electronique entreprise",
        ],
    },
    {
        "id": "elections_pro_donnees",
        "url": "https://www.cnil.fr/fr/elections-professionnelles-et-donnees-personnelles-questions-reponses",
        "keywords": [
            "elections professionnelles", "vote electronique", "election cse",
            "liste electorale", "election des representants",
        ],
    },
    {
        "id": "registre_traitements",
        "url": "https://www.cnil.fr/fr/RGPD-le-registre-des-activites-de-traitement",
        "keywords": [
            "registre des traitements", "registre de traitement", "registre rgpd",
            "traitement de donnees",
        ],
    },
    {
        "id": "gestion_personnel",
        "url": "https://www.cnil.fr/fr/les-regles-pour-la-gestion-du-personnel",
        "keywords": [
            "donnees personnelles rh", "gestion du personnel", "dossier salarie",
            "fichier du personnel", "donnees rh",
        ],
    },
    {
        "id": "donnees_sante_pratique",
        "url": "https://www.cnil.fr/fr/les-donnees-de-sante-en-pratique",
        "keywords": [
            "donnees de sante", "medecine du travail", "dossier medical",
            "sante au travail", "donnees medicales",
        ],
    },
    {
        "id": "sanction_surveillance_excessive",
        "url": "https://www.cnil.fr/fr/surveillance-excessive-des-salaries-sanction-de-40-000-euros-entreprise-secteur-immobilier",
        "keywords": [
            "surveillance excessive", "sanction cnil", "capture d ecran",
            "logiciel de surveillance salaries", "amende cnil",
        ],
    },
]


class CnilConnectorError(RuntimeError):
    """Base class for expected CNIL connector failures."""


class CnilFetchError(CnilConnectorError):
    """Raised when a CNIL page cannot be fetched or parsed."""


@dataclass(frozen=True)
class CnilConfig:
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    cache_dir: Path = ROOT / "local-index" / "cnil"
    cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS

    @classmethod
    def from_env(cls) -> "CnilConfig":
        timeout = parse_int(os.environ.get(ENV_TIMEOUT), DEFAULT_TIMEOUT_SECONDS)
        cache_ttl = parse_int(os.environ.get(ENV_CACHE_TTL), DEFAULT_CACHE_TTL_SECONDS)
        cache_dir = Path(os.environ.get(ENV_CACHE_DIR) or ROOT / "local-index" / "cnil")
        return cls(timeout_seconds=timeout, cache_dir=cache_dir, cache_ttl_seconds=cache_ttl)


def status_from_env() -> dict[str, Any]:
    config = CnilConfig.from_env()
    return {
        "detected": True,
        "available": True,
        "curated_pages": len(CNIL_PAGES),
        "cache_dir": str(config.cache_dir),
        "cache_ttl_seconds": config.cache_ttl_seconds,
        "uses_secret": False,
    }


class CnilClient:
    def __init__(self, config: CnilConfig | None = None) -> None:
        self.config = config or CnilConfig.from_env()

    def search_sources(self, query: str, limit: int = DEFAULT_LIMIT) -> dict[str, Any]:
        cleaned_query = compact_text(query)
        if not cleaned_query:
            return unavailable_result("Question vide : aucune recherche CNIL.")

        query_norm = normalize_text(cleaned_query)
        scored = []
        for page in CNIL_PAGES:
            score, hits = page_relevance_score(page, query_norm)
            if score > 0:
                scored.append((score, page, hits))
        if not scored:
            return unavailable_result(
                "Aucune page CNIL du corpus cible ne correspond a cette question.",
                query=cleaned_query,
            )
        scored.sort(key=lambda item: item[0], reverse=True)

        sources: list[dict[str, Any]] = []
        warnings: list[str] = []
        for score, page, hits in scored[: max(1, limit)]:
            try:
                fetched = self.fetch_page(page["url"])
            except CnilConnectorError as exc:
                warnings.append(f"{page['id']} indisponible : {exc}")
                continue
            sources.append(normalize_cnil_source(page, fetched, hits, score))

        if not sources:
            return unavailable_result(
                "Pages CNIL ciblees identifiees mais indisponibles (reseau).",
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
                body = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            raise CnilFetchError(f"HTTP {exc.code} sur {url}") from exc
        except urllib.error.URLError as exc:
            raise CnilFetchError(f"Connexion impossible a {url}: {safe_reason(exc)}") from exc
        except TimeoutError as exc:
            raise CnilFetchError(f"Timeout sur {url}") from exc
        if status >= 400:
            raise CnilFetchError(f"HTTP {status} sur {url}")

        payload = {
            "title": extract_title(body),
            "description": extract_meta_description(body),
            "updated_at": extract_updated_at(body),
            "fetched_at": utc_now(),
        }
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


def normalize_cnil_source(
    page: dict[str, Any], fetched: dict[str, Any], hits: list[str], score: float
) -> dict[str, Any]:
    title = fetched.get("title") or page["id"]
    description = fetched.get("description")
    return {
        "document": title,
        "document_type": "reference_cnil",
        "source_layer": SOURCE_LAYER,
        "source_layer_label": "Explication pratique officielle",
        "title": title,
        "summary": description,
        "excerpt": description,
        "content_type": "page de reference CNIL",
        "source_officielle": "CNIL",
        "official_origin": "cnil.fr",
        "url": page["url"],
        "url_or_id": page["url"],
        "official_id": page["id"],
        "reference": page["id"],
        "updated_at": fetched.get("updated_at"),
        "retrieved_at": fetched.get("fetched_at"),
        "score": score,
        "ranking_reasons": (
            [f"page CNIL ciblee correspondant a : {', '.join(hits[:4])}"] if hits else []
        ),
        "full_content_available": False,
        "content_access": "titre_et_description_uniquement",
        "complementarity_with_legifrance": (
            "Reference CNIL utile pour la protection des donnees personnelles ; a completer "
            "par le Code du travail et les accords applicables pour les aspects contractuels."
        ),
        "contradiction_risk": (
            "Faible si presentee comme reference CNIL distincte des sources juridiques opposables."
        ),
        "source_quality_warning": (
            None
            if description
            else "Page CNIL sans description exploitable extraite automatiquement ; ouvrir l'URL pour le contenu complet."
        ),
    }


def unavailable_result(warning: str, query: str | None = None) -> dict[str, Any]:
    return {
        "available": False,
        "source_layer": SOURCE_LAYER,
        "query": query,
        "source_count": 0,
        "sources": [],
        "warnings": [warning],
        "retrieved_at": utc_now(),
    }


def extract_title(body: str) -> str | None:
    match = re.search(r"<title[^>]*>(.*?)</title>", body, re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    title = clean_text_value(match.group(1))
    if title:
        title = re.sub(r"\s*\|\s*CNIL\s*$", "", title).strip()
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


def safe_configuration(config: CnilConfig) -> dict[str, Any]:
    return {
        "curated_pages": len(CNIL_PAGES),
        "cache_dir": str(config.cache_dir),
        "cache_ttl_seconds": config.cache_ttl_seconds,
        "cache_ignored_by_git": "local-index" in config.cache_dir.parts,
        "uses_secret": False,
    }


def command_search(args: argparse.Namespace) -> dict[str, Any]:
    client = CnilClient()
    return client.search_sources(args.query, limit=args.limit)


def command_list_pages(_args: argparse.Namespace) -> dict[str, Any]:
    return {
        "curated_pages": [
            {"id": page["id"], "url": page["url"], "keywords": page["keywords"]}
            for page in CNIL_PAGES
        ]
    }


def format_text(payload: dict[str, Any]) -> str:
    if "curated_pages" in payload:
        lines = ["CNIL - PAGES CIBLEES"]
        for page in payload["curated_pages"]:
            lines.append(f"- {page['id']} : {page['url']}")
        return "\n".join(lines)

    lines = ["CNIL - RECHERCHE"]
    lines.append(f"Question : {payload.get('query')}")
    lines.append(f"Sources : {payload.get('source_count', len(payload.get('sources', [])))}")
    for source in payload.get("sources", []):
        lines.append(
            "- "
            + " | ".join(
                compact_text(part)
                for part in [source.get("title"), source.get("summary"), source.get("url")]
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CFDT Nexus - connecteur CNIL (pages de reference ciblees)")
    sub = parser.add_subparsers(dest="command", required=True)

    search = sub.add_parser("search")
    search.add_argument("--query", required=True)
    search.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    search.add_argument("--format", choices=["text", "json"], default="text")

    list_pages = sub.add_parser("list-pages")
    list_pages.add_argument("--format", choices=["text", "json"], default="text")

    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "search":
        emit(command_search(args), args.format)
    elif args.command == "list-pages":
        emit(command_list_pages(args), args.format)
    else:
        raise SystemExit(f"Commande inconnue: {args.command}")


if __name__ == "__main__":
    main()
