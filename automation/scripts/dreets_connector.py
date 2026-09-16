#!/usr/bin/env python
"""DREETS Grand Est connector - curated reference pages (guides, inaptitude, CSE).

INEOS Sarralbe is in the Grand Est region. Mini connector following the CNIL
pattern (see official_reference_connector.py): a small, individually verified
list of public DREETS Grand Est guides on the conseiller du salarie, salarie
inaptitude, CSE/CSSCT and collective negotiation. Most of the useful content
here is published as PDF guides, extracted live via pypdf - never invented.
Every URL below was checked to resolve before being added here.
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

ENV_TIMEOUT = "CFDT_NEXUS_DREETS_TIMEOUT"
ENV_CACHE_DIR = "CFDT_NEXUS_DREETS_CACHE_DIR"
ENV_CACHE_TTL = "CFDT_NEXUS_DREETS_CACHE_TTL_SECONDS"

CONNECTOR_ID = "dreets"
SOURCE_OFFICIELLE = "DREETS Grand Est"
OFFICIAL_ORIGIN = "grand-est.dreets.gouv.fr"

DREETS_PAGES: list[dict[str, Any]] = [
    {
        "id": "guide_conseiller_salarie",
        "url": "https://grand-est.dreets.gouv.fr/sites/grand-est.dreets.gouv.fr/IMG/pdf/guide_ge.pdf",
        "keywords": [
            "conseiller du salarie", "assistance entretien prealable", "entretien de licenciement",
            "conseil du salarie",
        ],
    },
    {
        "id": "fiche_inaptitude",
        "url": "https://grand-est.dreets.gouv.fr/sites/grand-est.dreets.gouv.fr/IMG/pdf/fiche_inaptitude_2020.pdf",
        "keywords": [
            "inaptitude", "reclassement", "medecin du travail", "licenciement pour inaptitude",
            "visite de reprise",
        ],
    },
    {
        "id": "qr_cse",
        "url": "https://grand-est.dreets.gouv.fr/sites/grand-est.dreets.gouv.fr/IMG/pdf/qr_cse.pdf",
        "keywords": [
            "cse", "comite social et economique", "elections professionnelles cse",
            "questions reponses cse",
        ],
    },
    {
        "id": "plaquette_cse_ssct",
        "url": "https://grand-est.dreets.gouv.fr/sites/grand-est.dreets.gouv.fr/IMG/pdf/plaquette_-_cse_-_ssct.pdf",
        "keywords": [
            "cssct", "formation cse", "sante securite conditions de travail", "formation ssct",
        ],
    },
    {
        "id": "guide_negociation_cse",
        "url": "https://grand-est.dreets.gouv.fr/sites/grand-est.dreets.gouv.fr/IMG/pdf/guide_negociation_cse_juillet_2020-2.pdf",
        "keywords": [
            "negociation cse", "moyens du cse", "accord de fonctionnement du cse",
            "negociation comite social et economique",
        ],
    },
    {
        "id": "dialogue_social_guides_negociation",
        "url": "https://grand-est.dreets.gouv.fr/Dialogue-social-guides-de-la-negociation-en-entreprise",
        "keywords": [
            "dialogue social", "negociation collective", "negociation d entreprise",
            "guide de la negociation",
        ],
    },
]


def _config_from_env() -> OfficialReferenceConfig:
    timeout = _parse_int(os.environ.get(ENV_TIMEOUT), DEFAULT_TIMEOUT_SECONDS)
    cache_ttl = _parse_int(os.environ.get(ENV_CACHE_TTL), DEFAULT_CACHE_TTL_SECONDS)
    cache_dir = Path(os.environ.get(ENV_CACHE_DIR) or ROOT / "local-index" / "dreets")
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
        "curated_pages": len(DREETS_PAGES),
        "cache_dir": str(config.cache_dir),
        "cache_ttl_seconds": config.cache_ttl_seconds,
        "uses_secret": False,
    }


class DreetsClient(OfficialReferenceClient):
    def __init__(self, config: OfficialReferenceConfig | None = None) -> None:
        super().__init__(config or _config_from_env(), DREETS_PAGES)


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="CFDT Nexus - connecteur DREETS Grand Est")
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    args = parser.parse_args()
    print(json.dumps(DreetsClient().search_sources(args.query, limit=args.limit), ensure_ascii=False, indent=2))
