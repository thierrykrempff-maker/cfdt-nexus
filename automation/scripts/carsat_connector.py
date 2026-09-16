#!/usr/bin/env python
"""CARSAT Nord-Est connector - curated reference pages for prevention/AT-MP topics.

Regional caisse for INEOS Sarralbe (Moselle, Grand Est): Carsat Nord-Est. Mini
connector following the CNIL pattern (see official_reference_connector.py):
a small, individually verified list of public pages on penibilite, the C2P,
AT/MP contributions and occupational risk prevention. Every URL below was
checked to resolve before being added here.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from official_reference_connector import (
    DEFAULT_CACHE_TTL_SECONDS,
    DEFAULT_LIMIT,
    DEFAULT_TIMEOUT_SECONDS,
    OfficialReferenceClient,
    OfficialReferenceConfig,
)

ROOT = Path(__file__).resolve().parents[2]

ENV_TIMEOUT = "CFDT_NEXUS_CARSAT_TIMEOUT"
ENV_CACHE_DIR = "CFDT_NEXUS_CARSAT_CACHE_DIR"
ENV_CACHE_TTL = "CFDT_NEXUS_CARSAT_CACHE_TTL_SECONDS"

CONNECTOR_ID = "carsat"
SOURCE_OFFICIELLE = "CARSAT Nord-Est"
OFFICIAL_ORIGIN = "carsat-nordest.fr"

CARSAT_PAGES: list[dict[str, Any]] = [
    {
        "id": "c2p_entreprise",
        "url": "https://www.carsat-nordest.fr/home/entreprise/prevenir-vos-risques-professionn/compte-professionnel-de-preventi.html",
        "keywords": [
            "penibilite", "compte professionnel de prevention", "c2p", "points prevention",
            "facteurs de risques professionnels",
        ],
    },
    {
        "id": "c2p_salarie",
        "url": "https://www.carsat-nordest.fr/home/actif/preserver-sa-sante/c2p.html",
        "keywords": [
            "penibilite", "c2p", "compte penibilite", "compte professionnel de prevention",
            "retraite anticipee penibilite", "reconversion penibilite",
        ],
    },
    {
        "id": "cotisations_atmp",
        "url": "https://www.carsat-nordest.fr/home/entreprise/vos-cotisations-accidents-du-tra.html",
        "keywords": [
            "cotisation at mp", "taux atmp", "accident du travail cotisation",
            "maladie professionnelle cotisation", "tarification risques professionnels",
        ],
    },
    {
        "id": "prevenir_risques_professionnels",
        "url": "https://www.carsat-nordest.fr/home/entreprise/prevenir-vos-risques-professionn.html",
        "keywords": [
            "prevention des risques professionnels", "accident du travail prevention",
            "maladie professionnelle prevention", "securite au travail carsat",
        ],
    },
]


def _config_from_env() -> OfficialReferenceConfig:
    timeout = _parse_int(os.environ.get(ENV_TIMEOUT), DEFAULT_TIMEOUT_SECONDS)
    cache_ttl = _parse_int(os.environ.get(ENV_CACHE_TTL), DEFAULT_CACHE_TTL_SECONDS)
    cache_dir = Path(os.environ.get(ENV_CACHE_DIR) or ROOT / "local-index" / "carsat")
    return OfficialReferenceConfig(
        connector_id=CONNECTOR_ID,
        source_officielle=SOURCE_OFFICIELLE,
        official_origin=OFFICIAL_ORIGIN,
        cache_dir=cache_dir,
        timeout_seconds=timeout,
        cache_ttl_seconds=cache_ttl,
    )


def _parse_int(value: str | None, default: int) -> int:
    try:
        parsed = int(str(value or "").strip())
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def status_from_env() -> dict[str, Any]:
    config = _config_from_env()
    return {
        "detected": True,
        "available": True,
        "curated_pages": len(CARSAT_PAGES),
        "cache_dir": str(config.cache_dir),
        "cache_ttl_seconds": config.cache_ttl_seconds,
        "uses_secret": False,
    }


class CarsatClient(OfficialReferenceClient):
    def __init__(self, config: OfficialReferenceConfig | None = None) -> None:
        super().__init__(config or _config_from_env(), CARSAT_PAGES)


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="CFDT Nexus - connecteur CARSAT Nord-Est")
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    args = parser.parse_args()
    print(json.dumps(CarsatClient().search_sources(args.query, limit=args.limit), ensure_ascii=False, indent=2))
