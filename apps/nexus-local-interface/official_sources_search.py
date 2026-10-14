"""Bloc « Sources officielles » sous chaque réponse : Légifrance, Judilibre et convention collective (IDCC 44).

Pour chaque question, Nexus propose à l'écran trois pistes à vérifier :
- Légifrance : articles du Code du travail (API PISTE) ;
- Judilibre : décisions de la Cour de cassation (API PISTE) ;
- convention collective des industries chimiques, cherchée dans l'archive locale (la recherche IDCC de Légifrance ne
  renvoie rien) ; l'édition archivée date de 2013 : la version en vigueur doit être vérifiée.

Garde-fous :
- activé seulement par ``NEXUS_OFFICIAL_SOURCES_BLOCK_ENABLED`` (désactivé par défaut) ;
- **seuls des mots-clés** quittent le poste vers Légifrance et Judilibre (3 à 6 mots), jamais la question brute ;
  les noms propres (mots capitalisés au milieu d'une phrase) et les nombres sont retirés ; les mots envoyés sont affichés ;
- ne lève jamais d'exception vers l'appelant : une section indisponible n'empêche pas les autres ;
- ne conserve rien sur disque ; le résultat reste à l'écran, hors rapport et exports (comme les archives locales).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

from agreement_compare import HEX_ID, _base_url, _service_call
from cse_agenda_analysis import _accord_row, _accords_enabled, _archive_endpoint, _public_text
from official_extra_sources import search_extra_sources
from official_topics import TOPICS
from pv_archive_search import _service_post, query_concepts, required_matches

ENABLED_VARIABLE = "NEXUS_OFFICIAL_SOURCES_BLOCK_ENABLED"
MAX_KEYWORDS = 6
ROWS_PER_SECTION = 3
MAX_REFERENCE_ARTICLES = 8
CALL_TIMEOUT_SECONDS = 25
CCN_FILE_MARKER = "ccnic"  # convention collective nationale des industries chimiques (fichier de l'archive des accords)
CCN_TITLE = "Convention collective nationale des industries chimiques (IDCC 44)"

_ALLOWED_URL_PREFIXES = (
    "https://www.legifrance.gouv.fr/",
    "https://www.courdecassation.fr/",
)
# Mots d'une question qui n'aident ni la recherche ni le tri (verbes et adverbes courants).
_SOURCES_STOP_WORDS = frozenset(
    {"vient", "deja", "fonctionne", "imposer", "possible", "conditions", "regles", "obligations", "peut", "peuvent",
     "faut", "cela", "quelles", "quelle", "autre", "autres", "cas", "titre", "pourrait", "pourraient", "permet"}
)
_WORD = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*|[.!?:;\n]")

NOTICE = (
    "Pistes à vérifier : résultats automatiques par mots-clés. Lisez le texte officiel avant de vous en servir ; "
    "ce n’est ni un avis juridique ni une garantie d’exhaustivité. Affiché ici uniquement : non repris dans le rapport ni les exports."
)
NOTICE_CCN = (
    "Édition de l’archive locale : septembre 2013. Vérifiez la version en vigueur (avenants et accords de branche "
    "postérieurs) sur Légifrance avant toute utilisation."
)


def official_sources_enabled() -> bool:
    return os.environ.get(ENABLED_VARIABLE, "").strip().lower() in {"1", "true", "yes", "on"}


def keywords_for_sources(question: object) -> list[str]:
    """3 à 6 mots-clés d'une question : sans noms propres, sans nombres, sans mots vides (jamais la question brute)."""

    text = question if isinstance(question, str) else ""
    tokens = _WORD.findall(text[:1500])

    def capitalized(token: str) -> bool:
        return token[0].isalpha() and token[0].isupper() and not token.isupper()

    kept: list[str] = []
    sentence_start = True
    for index, token in enumerate(tokens):
        if token in {".", "!", "?", ":", ";", "\n"}:
            sentence_start = True
            continue
        following = tokens[index + 1] if index + 1 < len(tokens) else ""
        # nom propre probable : mot capitalisé en milieu de phrase, ou en début de phrase suivi d'un autre mot capitalisé
        name = capitalized(token) and (not sentence_start or (following and capitalized(following)))
        if not name:
            kept.append(token)
        sentence_start = False
    concepts = [word for word in query_concepts(" ".join(kept)) if word not in _SOURCES_STOP_WORDS]
    if len(concepts) > MAX_KEYWORDS:
        keep = set(sorted(concepts, key=lambda item: (-len(item), item))[:MAX_KEYWORDS])
        concepts = [item for item in concepts if item in keep]
    return concepts


def _plain(value: object) -> str:
    text = unicodedata.normalize("NFD", str(value or "").lower())
    return "".join(char for char in text if not unicodedata.combining(char))


def matching_topics(question: object) -> list[dict[str, Any]]:
    """Sujets reconnus dans la question (chaque groupe de ``when`` doit être présent), du plus spécifique au plus général."""

    plain = _plain(question)[:1500]
    found = [
        topic
        for topic in TOPICS
        if all(any(re.search(r"\b" + re.escape(stem), plain) for stem in group) for group in topic["when"])
    ]
    precise = [topic for topic in found if not topic.get("generic")]
    return precise or found


def _article_key(value: object) -> str:
    return re.sub(r"[\s.]", "", str(value or ""))


FULL_TEXT_LIMIT = 6000


def _full_article_text(client: Any, official_id: str) -> str:
    """Texte intégral d'un article (le connecteur ne garde que 900 caractères)."""

    try:
        raw = client._post_json(client.config.article_endpoint, {"id": official_id})  # noqa: SLF001
        text = (raw.get("article") or {}).get("texte") or ""
    except Exception:  # noqa: BLE001
        return ""
    return _public_text(text, FULL_TEXT_LIMIT) if isinstance(text, str) else ""


def _fetch_article(client: Any, article: str, label: str, full_text: bool = False) -> dict[str, Any] | None:
    for query in (article, f"article {article}"):
        try:
            hits = client.search_article_hits(query, limit=5)
        except Exception:  # noqa: BLE001
            continue
        exact = [hit for hit in hits if _article_key(hit.get("article")) == article and hit.get("official_id")]
        if not exact:
            continue
        try:
            source = client.article_source(exact[0]["official_id"], exact[0])
        except Exception:  # noqa: BLE001
            return None
        row = {
            "title": f"Code du travail, article {article}",
            "date": _clip(source.get("version_start_date") or source.get("date_debut"), 10) or None,
            "detail": f"{'En vigueur' if source.get('is_in_force') else _clip(source.get('etat'), 30)} · {label}",
            "excerpt": _clip(source.get("excerpt"), 420),
            "url": _safe_url(source.get("url")),
            "article": article,
        }
        if full_text:
            row["full_text"] = _full_article_text(client, str(source.get("official_id") or exact[0]["official_id"]))
        return row
    return None


def _reference_section(topics: Sequence[dict[str, Any]], full_text: bool = False) -> dict[str, Any]:
    """Articles de référence des sujets reconnus, lus sur Légifrance (texte officiel en vigueur)."""

    if not topics:
        return {"status": "READY", "rows": [], "notice": ""}
    wanted: list[tuple[str, str]] = []
    for topic in topics[:2]:
        for article in topic["articles"]:
            if all(article != done for done, _ in wanted):
                wanted.append((article, topic["label"]))
    wanted = wanted[:MAX_REFERENCE_ARTICLES]
    try:
        legifrance, _ = _connector_modules()
        client = legifrance.LegifranceClient()
        if not client.config.configured:
            return {"status": "NOT_CONFIGURED", "rows": [], "notice": "Clés Légifrance non configurées sur ce poste."}
        with ThreadPoolExecutor(max_workers=3) as pool:
            fetched = list(pool.map(lambda item: _fetch_article(client, *item, full_text), wanted))
    except Exception:  # noqa: BLE001
        return {"status": "UNAVAILABLE", "rows": [], "notice": "Légifrance est injoignable pour le moment."}
    rows = [row for row in fetched if row]
    return {
        "status": "READY",
        "rows": rows,
        "notice": "Articles clés du sujet reconnu, lus sur Légifrance. Ils ne sont pas exhaustifs : vérifiez aussi les autres textes applicables.",
    }


def _safe_url(value: object) -> str:
    url = str(value or "").strip()
    return url if url.startswith(_ALLOWED_URL_PREFIXES) else ""


def _clip(value: object, limit: int) -> str:
    return _public_text(value, limit)


def _connector_modules() -> tuple[Any, Any]:
    scripts = str(Path(__file__).resolve().parents[2] / "automation" / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    import judilibre_connector  # noqa: PLC0415
    import legifrance_connector  # noqa: PLC0415

    return legifrance_connector, judilibre_connector


def _legifrance_section(query: str, keywords: Sequence[str] = (), skip: Sequence[str] = ()) -> dict[str, Any]:
    try:
        legifrance, _ = _connector_modules()
        client = legifrance.LegifranceClient()
        if not client.config.configured:
            return {"status": "NOT_CONFIGURED", "rows": [], "notice": "Clés Légifrance non configurées sur ce poste."}
        payload = client.search_code_sources(query, limit=ROWS_PER_SECTION)
    except Exception:  # noqa: BLE001 - jamais d'exception vers l'écran
        return {"status": "UNAVAILABLE", "rows": [], "notice": "Légifrance est injoignable pour le moment."}
    rows = []
    for source in payload.get("sources") or []:
        if not isinstance(source, Mapping):
            continue
        article = _clip(source.get("article"), 40)
        text = _plain(f"{source.get('excerpt', '')} {article}")
        distinctive = [word for word in keywords if len(word) >= 5]
        matched = sum(1 for word in distinctive if word[:7] in text)
        if _article_key(article) in skip or (distinctive and matched < min(2, len(distinctive))):
            continue  # déjà présent parmi les articles de référence, ou trop peu de mots de la question dans son texte
        rows.append(
            {
                "title": f"Code du travail, article {article}" if article else "Code du travail",
                "date": _clip(source.get("version_start_date") or source.get("date_debut"), 10) or None,
                "detail": "En vigueur" if source.get("is_in_force") else _clip(source.get("etat"), 30),
                "excerpt": _clip(source.get("excerpt"), 420),
                "url": _safe_url(source.get("url")),
            }
        )
    return {"status": "READY", "rows": rows, "notice": ""}


def _judilibre_section(query: str, must_mention: Sequence[str] = ()) -> dict[str, Any]:
    try:
        _, judilibre = _connector_modules()
        client = judilibre.JudilibreClient()
        if not client.config.configured:
            return {"status": "NOT_CONFIGURED", "rows": [], "notice": "Clés Judilibre non configurées sur ce poste."}
        payload = client.search_sources(query, limit=ROWS_PER_SECTION)
    except Exception:  # noqa: BLE001
        return {"status": "UNAVAILABLE", "rows": [], "notice": "Judilibre est injoignable pour le moment."}
    rows = []
    for source in payload.get("sources") or []:
        if not isinstance(source, Mapping):
            continue
        text = _plain(f"{source.get('summary', '')} {source.get('principle_summary', '')} {source.get('excerpt', '')} {source.get('themes', '')}")
        if must_mention and not any(word[:6] in text for word in must_mention if len(word) >= 5):
            continue  # décision sans aucun mot du sujet
        solution = _clip(source.get("solution"), 40)
        rows.append(
            {
                "title": _clip(source.get("document"), 160) or "Décision de la Cour de cassation",
                "date": _clip(source.get("decision_date"), 10) or None,
                "detail": f"Solution : {solution}" if solution else "",
                "excerpt": _clip(source.get("principle_summary") or source.get("summary") or source.get("excerpt"), 500),
                "url": _safe_url(source.get("url")),
            }
        )
    return {"status": "READY", "rows": rows, "notice": ""}


def _ccn_section(keywords: Sequence[str], strict: bool = False) -> dict[str, Any]:
    """Convention collective : cherchée uniquement dans le document ``ccnic`` de l'archive locale des accords."""

    if not _accords_enabled():
        return {"status": "DISABLED", "rows": [], "notice": "L’archive des accords n’est pas activée : convention collective non consultée."}
    base, endpoint = _base_url(), _archive_endpoint()
    listing = _service_call(f"{base}/api/documents?corpus=accords") if base else None
    items = listing.get("documents") if listing else None
    if not endpoint or not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
        return {"status": "UNAVAILABLE", "rows": [], "notice": "Le service d’archive est arrêté : convention collective non consultée."}
    ids = [
        str(item["id"])
        for item in items
        if isinstance(item, Mapping)
        and HEX_ID.fullmatch(str(item.get("id", "")))
        and CCN_FILE_MARKER in str(item.get("fichier") or "").lower()
    ]
    if not ids:
        return {"status": "NOT_INDEXED", "rows": [], "notice": "La convention collective n’est pas dans l’archive locale."}
    payload = _service_post(
        endpoint,
        {
            "corpus": "accords",
            "points": [{"id": "ccn", "concepts": list(keywords), "min_matches": len(keywords) if strict else required_matches(len(keywords))}],
            "limit": ROWS_PER_SECTION,
            "include": ids,
        },
    )
    by_point = payload.get("points") if payload else None
    if not isinstance(by_point, Mapping):
        return {"status": "UNAVAILABLE", "rows": [], "notice": "Le service d’archive est injoignable : convention collective non consultée."}
    rows = []
    for raw in by_point.get("ccn") or []:
        row = _accord_row(raw) if isinstance(raw, Mapping) else None
        if row:
            rows.append(
                {
                    "title": CCN_TITLE,
                    "date": None,
                    "detail": row.get("reference") or "",
                    "excerpt": row["excerpt"],
                    "url": "",
                }
            )
    return {"status": "READY", "rows": rows, "notice": NOTICE_CCN}


def official_sources_status() -> dict[str, Any]:
    return {"enabled": official_sources_enabled()}


def search_official_sources(question: object, *, full_text: bool = False) -> dict[str, Any]:
    """Trois sections (Légifrance, Judilibre, convention collective) pour une question. Ne lève jamais d'exception."""

    result: dict[str, Any] = {"status": "READY", "keywords": [], "topics": [], "notice": NOTICE, "sections": {}}
    if not official_sources_enabled():
        return {**result, "status": "DISABLED", "notice": "Le bloc « Sources officielles » n’est pas activé sur ce poste."}
    keywords = keywords_for_sources(question)
    if not keywords:
        return {**result, "status": "EMPTY_QUERY", "notice": "Pas assez de mots distinctifs dans la question."}
    topics = matching_topics(question)
    topic_terms = list(topics[0]["terms"]) if topics else []
    query = " ".join(dict.fromkeys([*topic_terms, *keywords]))  # mots du sujet reconnu d'abord, puis ceux de la question
    reference_articles = {article for topic in topics[:2] for article in topic["articles"]}
    jobs = {
        "reference": lambda: _reference_section(topics, full_text),
        "legifrance": lambda: _legifrance_section(" ".join(keywords), keywords, tuple(reference_articles)),
        "judilibre": lambda: _judilibre_section(query, tuple(topic_terms or keywords)),
        "convention": lambda: _ccn_section(topic_terms or keywords, strict=bool(topic_terms)),
        "autres": lambda: search_extra_sources(query),
    }
    pool = ThreadPoolExecutor(max_workers=len(jobs))
    futures = {name: pool.submit(job) for name, job in jobs.items()}
    sections: dict[str, Any] = {}
    for name, future in futures.items():
        try:
            sections[name] = future.result(timeout=CALL_TIMEOUT_SECONDS)
        except (FutureTimeout, Exception):  # noqa: BLE001
            sections[name] = {"status": "UNAVAILABLE", "rows": [], "notice": "Délai dépassé."}
    pool.shutdown(wait=False, cancel_futures=True)
    return {**result, "keywords": keywords, "topics": [topic["label"] for topic in topics[:2]], "sections": sections}
