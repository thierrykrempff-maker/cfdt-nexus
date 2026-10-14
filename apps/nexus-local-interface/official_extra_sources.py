"""Autres sources officielles du bloc « Sources officielles » : CDTN, service-public, CNIL, DREETS Grand Est, CARSAT, INRS.

Ces connecteurs (``automation/scripts``) lisent des pages publiques en direct, sans clé :
- CDTN (code.travail.gouv.fr) et service-public.gouv.fr (« pratique officielle ») : explications en langage clair ;
- CNIL, DREETS Grand Est, CARSAT Nord-Est, INRS : listes de pages choisies (RGPD, guides CSE/CSSCT/inaptitude, retraite et pénibilité,
  prévention des risques). Un connecteur sans page pour la question ne renvoie rien : c'est normal.

Comme pour Légifrance et Judilibre, seuls des mots-clés partent vers ces sites (jamais la question brute). Ces sources
expliquent ou orientent : elles ne remplacent ni la loi ni la jurisprudence. Aucune exception ne remonte à l'appelant.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
import sys
from pathlib import Path
from typing import Any

from cse_agenda_analysis import _public_text

CALL_TIMEOUT_SECONDS = 25
ROWS_PER_CONNECTOR = 2

# (clé, module, classe, libellé affiché, hôtes de liens autorisés)
CONNECTORS: tuple[tuple[str, str, str, str, tuple[str, ...]], ...] = (
    ("cdtn", "cdtn_connector", "CdtnClient", "Code du travail numérique", ("https://code.travail.gouv.fr/",)),
    ("service_public", "pratique_officielle_connector", "PratiqueOfficielleClient", "Service-public / Code du travail numérique",
     ("https://www.service-public.gouv.fr/", "https://code.travail.gouv.fr/")),
    ("cnil", "cnil_connector", "CnilClient", "CNIL", ("https://www.cnil.fr/",)),
    ("dreets", "dreets_connector", "DreetsClient", "DREETS Grand Est", ("https://grand-est.dreets.gouv.fr/",)),
    ("carsat", "carsat_connector", "CarsatClient", "CARSAT Nord-Est", ("https://www.carsat-nordest.fr/",)),
    ("inrs", "inrs_connector", "InrsClient", "INRS", ("https://www.inrs.fr/",)),
)


def _load(module: str, cls: str) -> Any:
    scripts = str(Path(__file__).resolve().parents[2] / "automation" / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    return getattr(__import__(module), cls)()


def _one(key: str, module: str, cls: str, label: str, hosts: tuple[str, ...], query: str) -> dict[str, Any]:
    try:
        payload = _load(module, cls).search_sources(query, limit=ROWS_PER_CONNECTOR)
    except Exception:  # noqa: BLE001 - un site en panne ne bloque pas les autres
        return {"key": key, "label": label, "status": "UNAVAILABLE", "rows": []}
    rows = []
    for source in (payload.get("sources") or [])[:ROWS_PER_CONNECTOR]:
        if not isinstance(source, Mapping):
            continue
        url = str(source.get("url") or "").strip()
        excerpt = _public_text(source.get("excerpt") or source.get("summary") or source.get("resume_court"), 500)
        title = _public_text(source.get("document") or source.get("title"), 160)
        if not (title or excerpt):
            continue
        rows.append(
            {
                "title": title or label,
                "date": None,
                "detail": label,
                "excerpt": excerpt,
                "url": url if url.startswith(hosts) else "",
            }
        )
    return {"key": key, "label": label, "status": "READY", "rows": rows}


def search_extra_sources(query: str) -> dict[str, Any]:
    """Interroge les six connecteurs en parallèle. Renvoie une section ``{status, rows, notice}`` (lignes de tous les sites)."""

    pool = ThreadPoolExecutor(max_workers=len(CONNECTORS))
    futures = [pool.submit(_one, *connector, query) for connector in CONNECTORS]
    parts: list[dict[str, Any]] = []
    for connector, future in zip(CONNECTORS, futures):
        try:
            parts.append(future.result(timeout=CALL_TIMEOUT_SECONDS))
        except (FutureTimeout, Exception):  # noqa: BLE001
            parts.append({"key": connector[0], "label": connector[3], "status": "UNAVAILABLE", "rows": []})
    pool.shutdown(wait=False, cancel_futures=True)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for part in parts:  # CDTN et service-public renvoient parfois la même fiche : une seule ligne
        for row in part["rows"]:
            key = row["url"] or row["title"]
            if key not in seen:
                seen.add(key)
                rows.append(row)
    down = [part["label"] for part in parts if part["status"] != "READY"]
    notice = "Explications et guides officiels : ils orientent mais ne remplacent ni la loi ni la jurisprudence."
    if down:
        notice += f" Non consultés : {', '.join(down)}."
    return {"status": "READY", "rows": rows, "notice": notice}
