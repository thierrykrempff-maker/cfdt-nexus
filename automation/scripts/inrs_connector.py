#!/usr/bin/env python
"""INRS connector - curated reference pages for CSSCT/risk-prevention topics.

Directly relevant to INEOS Sarralbe (chemical industry site). Mini connector
following the CNIL pattern (see official_reference_connector.py): a small,
individually verified list of public INRS pages on the DUERP, chemical risk
PPE, CSSCT missions and CSE attributions. Every URL below was checked to
resolve before being added here.
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

ENV_TIMEOUT = "CFDT_NEXUS_INRS_TIMEOUT"
ENV_CACHE_DIR = "CFDT_NEXUS_INRS_CACHE_DIR"
ENV_CACHE_TTL = "CFDT_NEXUS_INRS_CACHE_TTL_SECONDS"

CONNECTOR_ID = "inrs"
SOURCE_OFFICIELLE = "INRS"
OFFICIAL_ORIGIN = "inrs.fr"

INRS_PAGES: list[dict[str, Any]] = [
    {
        "id": "document_unique",
        "url": "https://www.inrs.fr/demarche/document-unique/ce-qu-il-faut-retenir.html",
        "keywords": [
            "document unique", "duerp", "evaluation des risques professionnels",
            "plan d action prevention",
        ],
    },
    {
        "id": "protection_individuelle_chimique",
        "url": "https://www.inrs.fr/risques/chimiques/protection-individuelle.html",
        "keywords": [
            "risque chimique", "epi", "equipement de protection individuelle",
            "protection respiratoire", "gants protection chimique",
        ],
    },
    {
        "id": "reglementation_risques_chimiques",
        "url": "https://www.inrs.fr/risques/chimiques/reglementation.html",
        "keywords": [
            "risque chimique", "reglementation risques chimiques", "agents chimiques dangereux",
            "cmr", "substances cancerogenes",
        ],
    },
    {
        "id": "missions_cssct",
        "url": "https://www.inrs.fr/demarche/cssct/missions-CSSCT.html",
        "keywords": [
            "cssct", "commission sante securite conditions de travail", "missions cssct",
            "attributions cssct",
        ],
    },
    {
        "id": "attributions_cse",
        "url": "https://www.inrs.fr/demarche/carrefour-CSE/CSE-missions-attributions/CSE-attributions.html",
        "keywords": [
            "cse", "attributions du cse", "missions du cse", "comite social et economique securite",
        ],
    },
]


def _config_from_env() -> OfficialReferenceConfig:
    timeout = _parse_int(os.environ.get(ENV_TIMEOUT), DEFAULT_TIMEOUT_SECONDS)
    cache_ttl = _parse_int(os.environ.get(ENV_CACHE_TTL), DEFAULT_CACHE_TTL_SECONDS)
    cache_dir = Path(os.environ.get(ENV_CACHE_DIR) or ROOT / "local-index" / "inrs")
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
        "curated_pages": len(INRS_PAGES),
        "cache_dir": str(config.cache_dir),
        "cache_ttl_seconds": config.cache_ttl_seconds,
        "uses_secret": False,
    }


class InrsClient(OfficialReferenceClient):
    def __init__(self, config: OfficialReferenceConfig | None = None) -> None:
        super().__init__(config or _config_from_env(), INRS_PAGES)


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="CFDT Nexus - connecteur INRS")
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    args = parser.parse_args()
    print(json.dumps(InrsClient().search_sources(args.query, limit=args.limit), ensure_ascii=False, indent=2))
