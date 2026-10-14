"""Guides PDF de la DREETS Grand Est lus en texte intégral (droit local Alsace-Moselle, CSE, négociation, inaptitude…).

Le connecteur DREETS ne garde que le titre et 400 caractères de chaque page. Ce module télécharge **une seule fois** les guides
publics ci-dessous (adresses fixes : aucune donnée de l'utilisateur n'est envoyée), en extrait le texte avec ``pypdf`` et le garde
dans ``local-index/dreets/guides`` (dossier ignoré par git). Une recherche par mots-clés renvoie ensuite les passages et les pages.

- Un guide absent du cache est ignoré et téléchargé en arrière-plan (la recherche ne bloque jamais sur un téléchargement) ;
  ``python -I official_local_guides.py --prefetch`` les télécharge tous d'avance.
- Aucune exception ne remonte à l'appelant.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
import datetime
import io
import json
import math
import re
import sys
import threading
import unicodedata
import urllib.request
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / "local-index" / "dreets" / "guides"
DOWNLOAD_TIMEOUT_SECONDS = 90
MAX_PDF_BYTES = 40_000_000
WINDOW = 900
STEP = 600
MAX_ROWS = 3
HOST = "https://grand-est.dreets.gouv.fr/"
_PDF = HOST + "sites/dreets-als-champ/files/"
_LEGACY = HOST + "sites/grand-est.dreets.gouv.fr/IMG/pdf/"

GUIDES: tuple[dict[str, str], ...] = (
    {
        "id": "droit_local_alsace_moselle",
        "title": "Guide du droit local du travail en Alsace-Moselle (décembre 2022)",
        "pdf": _PDF + "2026-08/Guide%20droit%20local%20du%20travail%20alsace%20moselle%20-%20d%C3%A9cembre%202022.pdf",
        "page": HOST + "guide-local-du-droit-du-travail-en-alsace-moselle",
    },
    {
        "id": "qr_cse",
        "title": "100 questions-réponses sur le comité social et économique",
        "pdf": _LEGACY + "qr_cse.pdf",
        "page": HOST + "un-representant-syndical-un-elu-cse",
    },
    {
        "id": "guide_negociation_cse",
        "title": "Guide de la négociation CSE (juillet 2020)",
        "pdf": _LEGACY + "guide_negociation_cse_juillet_2020-2.pdf",
        "page": HOST + "dialogue-social-guides-de-la-negociation-en-entreprise",
    },
    {
        "id": "fiche_inaptitude",
        "title": "L'inaptitude du salarié (fiche DREETS 2020)",
        "pdf": _LEGACY + "fiche_inaptitude_2020.pdf",
        "page": HOST + "un-salarie-un-apprenti-un-jeune-actif/droit-du-travail",
    },
    {
        "id": "plaquette_cse_ssct",
        "title": "CSE et santé, sécurité, conditions de travail (plaquette DREETS)",
        "pdf": _LEGACY + "plaquette_-_cse_-_ssct.pdf",
        "page": HOST + "un-representant-syndical-un-elu-cse",
    },
    {
        "id": "guide_conseiller_salarie",
        "title": "Guide du conseiller du salarié Grand Est",
        "pdf": _LEGACY + "guide_ge.pdf",
        "page": HOST + "le-conseiller-du-salarie-un-appui-en-cas-de-licenciement",
    },
    {
        "id": "guide_accidents_du_travail",
        "title": "Guide pour les victimes d'accident du travail (octobre 2023)",
        "pdf": _PDF + "files-spip/pdf/dreets_-_guide_accidents_de_travail_-_version_nume_rique_-_maj.pdf",
        "page": HOST + "un-guide-pour-les-victimes-daccidents-du-travail",
    },
)

_FETCHING: set[str] = set()
_LOCK = threading.Lock()
_MEMORY: dict[str, dict[str, Any]] = {}


def _cache_file(guide_id: str) -> Path:
    return CACHE_DIR / f"{guide_id}.json"


def _plain(value: object) -> str:
    text = unicodedata.normalize("NFD", str(value or "").lower())
    return "".join(char for char in text if not unicodedata.combining(char))


def _download(guide: Mapping[str, str]) -> dict[str, Any] | None:
    if not str(guide["pdf"]).startswith(HOST):
        return None
    request = urllib.request.Request(guide["pdf"], headers={"User-Agent": "Mozilla/5.0 (CFDT Nexus local)"})
    with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:  # noqa: S310 - hôte DREETS fixe
        body = response.read(MAX_PDF_BYTES + 1)
    if len(body) > MAX_PDF_BYTES:
        return None
    import pypdf  # noqa: PLC0415

    reader = pypdf.PdfReader(io.BytesIO(body))
    pages = [re.sub(r"\s+", " ", page.extract_text() or "").strip() for page in reader.pages]
    return {"id": guide["id"], "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "pages": pages}


def fetch_guide(guide: Mapping[str, str]) -> bool:
    """Télécharge un guide et l'écrit dans le cache. Renvoie True si le cache est prêt."""

    try:
        data = _download(guide)
        if not data or not any(data["pages"]):
            return False
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _cache_file(guide["id"]).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        _MEMORY[guide["id"]] = data
        return True
    except Exception:  # noqa: BLE001
        return False


def _background_fetch(guide: Mapping[str, str]) -> None:
    with _LOCK:
        if guide["id"] in _FETCHING:
            return
        _FETCHING.add(guide["id"])

    def run() -> None:
        try:
            fetch_guide(guide)
        finally:
            with _LOCK:
                _FETCHING.discard(guide["id"])

    threading.Thread(target=run, daemon=True).start()


def _load(guide: Mapping[str, str]) -> dict[str, Any] | None:
    cached = _MEMORY.get(guide["id"])
    if cached:
        return cached
    try:
        data = json.loads(_cache_file(guide["id"]).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        _background_fetch(guide)
        return None
    if isinstance(data, dict) and isinstance(data.get("pages"), list):
        _MEMORY[guide["id"]] = data
        return data
    return None


def search_guides(stems: Mapping[str, int], enough: Callable[[Mapping[str, int], str], bool]) -> list[dict[str, Any]]:
    """Meilleurs passages des guides en cache pour les racines ``stems`` (racine -> longueur du mot).

    Les mots rares pèsent plus que les mots banals (« jours », « salarié ») ; un guide n'est retenu que si son meilleur passage
    réunit au moins 55 % du poids des mots de la question présents dans les guides. ``enough`` : règle de pertinence minimale."""

    if not stems:
        return []
    loaded = [(guide, data) for guide in GUIDES for data in [_load(guide)] if data]
    windows: list[tuple[dict[str, str], int, str, str]] = []
    for guide, data in loaded:
        for number, text in enumerate(data["pages"], start=1):
            for start in range(0, max(1, len(text)), STEP):
                window = text[start:start + WINDOW]
                if window.count("....") >= 3:
                    continue  # table des matières : tous les mots y figurent sans rien dire
                windows.append((guide, number, window, _plain(window)))
    if not windows:
        return []
    count = len(windows)
    document_frequency = {stem: sum(1 for *_, plain in windows if stem in plain) for stem in stems}
    weight = {stem: math.log(1 + count / (1 + frequency)) for stem, frequency in document_frequency.items() if frequency}
    total = sum(weight.values())
    if not total:
        return []
    best: dict[str, tuple[float, int, str]] = {}
    for guide, number, window, plain in windows:
        matched = [stem for stem in weight if stem in plain]
        if len(matched) < min(2, len(weight)) or not enough(stems, window):
            continue
        score = sum(weight[stem] for stem in matched)
        if score >= 0.55 * total and (guide["id"] not in best or score > best[guide["id"]][0]):
            first = min(plain.find(stem) for stem in matched)
            best[guide["id"]] = (score, number, window[max(0, first - 120):first + 520])
    rows: list[tuple[float, dict[str, Any]]] = []
    for guide, _ in loaded:
        if guide["id"] in best:
            score, number, excerpt = best[guide["id"]]
            rows.append((score, {
                "title": f"{guide['title']} (p. {number})",
                "date": None,
                "detail": "DREETS Grand Est — guide",
                "excerpt": ("…" + excerpt.strip() + "…")[:650],
                "url": guide["page"],
            }))
    rows.sort(key=lambda pair: -pair[0])
    return [row for _, row in rows[:MAX_ROWS]]


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args != ["--prefetch"]:
        print("usage : python -I official_local_guides.py --prefetch", file=sys.stderr)
        return 2
    failed = 0
    for guide in GUIDES:
        ok = fetch_guide(guide)
        failed += 0 if ok else 1
        print(("OK     " if ok else "ECHEC  ") + guide["id"])
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
