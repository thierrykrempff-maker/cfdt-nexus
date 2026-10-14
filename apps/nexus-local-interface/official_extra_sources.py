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
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

from cse_agenda_analysis import _public_text
from official_local_guides import search_guides

CALL_TIMEOUT_SECONDS = 25
ROWS_PER_CONNECTOR = 2
MAX_CATALOG_ROWS = 4
BROAD = frozenset({"cdtn", "service_public"})  # recherches larges : leurs résultats sont filtrés par pertinence

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


# Catalogues de fiches choisies (titre et adresse seulement) : organismes sans lecture en direct.
CATALOGS: tuple[tuple[str, str], ...] = (
    ("anact", "ANACT"),
    ("urssaf", "URSSAF"),
    ("assurance_maladie", "Assurance maladie"),
    ("ministere_travail", "Ministère du Travail"),
    ("france_chimie", "France Chimie"),
    ("defenseur_droits", "Défenseur des droits"),
    ("agirc_arrco", "Agirc-Arrco"),
    ("alsace_moselle_local_law", "Droit local Alsace-Moselle"),
    ("service_public", "Service-public"),
    ("inrs", "INRS"),
    ("cnil", "CNIL"),
    ("carsat", "CARSAT Alsace-Moselle"),
    ("dreets_grand_est", "DREETS Grand Est"),
)
_NOISE = frozenset({"comment", "quelles", "quelle", "quels", "salarie", "salaries", "travail", "entreprise", "employeur", "droit"})


def _plain(value: object) -> str:
    text = unicodedata.normalize("NFD", str(value or "").lower())
    return re.sub(r"[^a-z0-9 ]+", " ", "".join(char for char in text if not unicodedata.combining(char)))


def _stems(value: object) -> dict[str, int]:
    """Racines (6 lettres) des mots distinctifs d'un texte, avec la longueur du mot le plus long qui les porte."""

    found: dict[str, int] = {}
    for word in _plain(value).split():
        if len(word) >= 5 and word not in _NOISE:
            found[word[:6]] = max(found.get(word[:6], 0), len(word))
    return found


def _enough(wanted: Mapping[str, int], text: object) -> bool:
    """Au moins 2 mots de la question dans le texte, ou 1 seul s'il est long et distinctif (7 lettres et plus)."""

    if not wanted:
        return True
    matched = [stem for stem in _stems(text) if stem in wanted]
    return len(matched) >= 2 or any(wanted[stem] >= 7 for stem in matched) or (len(wanted) == 1 and bool(matched))


def _enough_text(wanted: Mapping[str, int], text: str) -> bool:
    return _enough(wanted, text)


def _relevant(row: Mapping[str, Any], wanted: Mapping[str, int]) -> bool:
    return _enough(wanted, f"{row.get('title', '')} {row.get('excerpt', '')}")


def search_catalogs(query: str) -> list[dict[str, Any]]:
    """Fiches des catalogues (titre et lien) qui recoupent la question : au moins 2 mots du titre (1 si la question n'en a qu'un)."""

    wanted = _stems(query)
    if not wanted:
        return []
    try:
        from automation.official_knowledge import additional_metadata_feed as feed  # noqa: PLC0415
    except Exception:  # noqa: BLE001
        return []
    scored: list[tuple[int, dict[str, Any]]] = []
    for name, label in CATALOGS:
        try:
            items = feed.load_additional_metadata_sources(name)
        except Exception:  # noqa: BLE001
            continue
        for item in items:
            url = str(item.get("canonical_url") or "")
            title = _public_text(item.get("title"), 160)
            if title and url.startswith("https://") and _enough(wanted, title):
                scored.append((len(set(wanted) & set(_stems(title))), {
                    "title": title, "date": None, "detail": label,
                    "excerpt": "Fiche à consulter sur le site de l’organisme (titre et lien seulement : le contenu n’est pas lu par Nexus).",
                    "url": url,
                }))
    scored.sort(key=lambda pair: -pair[0])
    return [row for _, row in scored[:MAX_CATALOG_ROWS]]


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
    wanted = _stems(query)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for part in parts:
        key_name = part["key"]  # CDTN et service-public renvoient parfois la même fiche : une seule ligne
        for row in part["rows"]:
            key = row["url"] or row["title"]
            if key not in seen and (key_name not in BROAD or _relevant(row, wanted)):
                seen.add(key)
                rows.append(row)
    guide_rows: list[dict[str, Any]] = []
    try:
        guide_rows = search_guides(wanted, _enough_text)
    except Exception:  # noqa: BLE001
        pass
    for row in [*guide_rows, *search_catalogs(query)]:
        if (row["url"] or row["title"]) not in seen:
            seen.add(row["url"] or row["title"])
            rows.append(row)
    down = [part["label"] for part in parts if part["status"] != "READY"]
    notice = "Explications et guides officiels : ils orientent mais ne remplacent ni la loi ni la jurisprudence."
    if down:
        notice += f" Non consultés : {', '.join(down)}."
    return {"status": "READY", "rows": rows, "notice": notice}
