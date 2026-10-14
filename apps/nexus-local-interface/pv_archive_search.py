"""Recherche libre dans les archives locales : PV du CE/CSE et accords d'entreprise.

Disponible partout dans l'interface Nexus : sous une réponse à une question, et par le bouton « Recherche dans les PV ».
(L'analyse d'ordre du jour CSE utilise la même archive dans ``cse_agenda_analysis``.)

L'archive est un service local du module « Précédents » (``127.0.0.1``). Ce module :
- ne s'active qu'avec ``NEXUS_PV_ARCHIVE_ENABLED`` (désactivé par défaut) ;
- n'appelle que la machine locale (URL vérifiée) ;
- ne lève jamais d'exception vers l'appelant : service absent => statut ``UNAVAILABLE`` ;
- ne conserve rien : aucun PV, aucune requête n'est écrit sur disque.

Les extraits ne font partie d'aucun rapport ni export : ils sont renvoyés à l'écran uniquement.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
import re
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

from cse_agenda_analysis import (
    _ARCHIVE_TIMEOUT_SECONDS,
    _STOP_WORDS,
    _archive_enabled,
    _archive_endpoint,
    _accord_row,
    _accords_enabled,
    _archive_row,
    _normalize,
    _public_text,
)


MAX_QUERY_CHARS = 1500
MAX_CONCEPTS = 12
DEFAULT_LIMIT = 6
MAX_LIMIT = 15

# Mots d'une question en langage naturel qui n'aident pas à retrouver un passage de PV.
_QUERY_STOP_WORDS = frozenset(
    {
        "comment", "combien", "quand", "pourquoi", "peut", "peuvent", "doit", "doivent", "dois", "avoir",
        "avez", "avons", "faire", "fait", "font", "etre", "suis", "sommes", "etes", "aussi", "encore",
        "depuis", "pendant", "apres", "avant", "vers", "chez", "tout", "tous", "toute", "toutes", "plus",
        "moins", "tres", "trop", "bien", "alors", "cela", "celui", "celle", "ceux", "dont", "comme",
        "parce", "quoi", "dire", "veux", "veut", "voudrais", "souhaite", "souhaitons", "savoir", "situation",
        "salarie", "salaries", "entreprise", "societe", "etre", "sujet", "demande", "existe", "il", "elle",
        "quelle", "quelles", "quels", "dans", "avec", "pour", "sans", "sous", "cette", "leurs", "notre",
        "votre", "nous", "vous", "mais", "donc", "sont", "sera",
    }
)

NOTICE = (
    "Ces passages viennent de l’archive locale des PV du CE/CSE (OCR possible sur les anciens scans). "
    "Ils apportent un contexte historique et ne constituent pas une norme juridique. "
    "L’absence de résultat ne prouve pas que le sujet n’a jamais été traité."
)


NOTICE_ACCORDS = (
    "Ces passages viennent de l’archive locale des accords (OCR possible sur les anciens scans). "
    "Vérifiez la version en vigueur, les avenants et une éventuelle dénonciation avant de vous en servir. "
    "Ce n’est pas une analyse juridique ; l’absence de résultat ne prouve pas qu’aucun accord n’existe."
)

# Deux archives, un seul service local : le corpus est choisi par le champ « corpus » de la requête.
CORPORA: dict[str, dict[str, Any]] = {
    "pv": {
        "enabled": _archive_enabled,
        "row": _archive_row,
        "notice": NOTICE,
        "disabled": "La recherche dans les PV n’est pas activée sur ce poste.",
    },
    "accords": {
        "enabled": _accords_enabled,
        "row": _accord_row,
        "notice": NOTICE_ACCORDS,
        "disabled": "La recherche dans les accords n’est pas activée sur ce poste.",
    },
}


def query_concepts(text: str) -> list[str]:
    """Mots distinctifs d'une question ou de mots-clés (max 12, les plus longs si trop nombreux)."""

    tokens: list[str] = []
    for token in _normalize(text[:MAX_QUERY_CHARS]).split():
        if (
            len(token) >= 4
            and not token.isdigit()
            and token not in _STOP_WORDS
            and token not in _QUERY_STOP_WORDS
            and token not in tokens
        ):
            tokens.append(token)
    if len(tokens) > MAX_CONCEPTS:
        keep = set(sorted(tokens, key=lambda item: (-len(item), item))[:MAX_CONCEPTS])
        tokens = [token for token in tokens if token in keep]
    return tokens


def required_matches(count: int) -> int:
    """Nombre de mots à retrouver ensemble : tous pour 1-2 mots, environ la moitié au-delà (4 au plus)."""

    if count <= 2:
        return max(1, count)
    return min(4, max(2, (count + 1) // 2))


def _year(value: object) -> int | None:
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return number if 1990 <= number <= 2100 else None


def _service_post(endpoint: str, body: Mapping[str, Any]) -> Mapping[str, Any] | None:
    request = urllib_request.Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Nexus": "1", "X-Nexus-Server": "1"},
        method="POST",
    )
    try:
        with urllib_request.urlopen(request, timeout=_ARCHIVE_TIMEOUT_SECONDS) as response:  # noqa: S310 - loopback verifie
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib_error.URLError, OSError, ValueError):
        return None
    return payload if isinstance(payload, Mapping) else None


def archive_status(corpus: str = "pv") -> dict[str, Any]:
    """Option activée ? service joignable ? corpus chargé ? (sans lever d'exception)."""

    config = CORPORA.get(corpus)
    status: dict[str, Any] = {"enabled": bool(config and config["enabled"]()), "available": False}
    if not status["enabled"]:
        return status
    endpoint = _archive_endpoint()
    if endpoint is None:
        return status
    health = endpoint.removesuffix("/api/passages") + "/api/health"
    request = urllib_request.Request(health, headers={"X-Nexus": "1"}, method="GET")
    try:
        with urllib_request.urlopen(request, timeout=3) as response:  # noqa: S310 - loopback verifie
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib_error.URLError, OSError, ValueError):
        return status
    if isinstance(payload, Mapping) and payload.get("ok"):
        corpora = payload.get("corpora") if isinstance(payload.get("corpora"), Mapping) else {}
        size = int(corpora.get(corpus, payload.get("pv_indexes") if corpus == "pv" else 0) or 0)
        status["available"] = size > 0
        status["indexed_documents"] = size
    return status


def search_pv_archive(query: object, **options: Any) -> dict[str, Any]:
    """Cherche dans l'archive des PV (voir ``search_archive``)."""

    return search_archive("pv", query, **options)


def search_archive(
    corpus: str,
    query: object,
    *,
    since: object = None,
    until: object = None,
    limit: object = DEFAULT_LIMIT,
    strict: bool = False,
) -> dict[str, Any]:
    """Cherche une question ou des mots-clés dans une archive (« pv » ou « accords »). Ne lève jamais d'exception."""

    config = CORPORA.get(corpus)
    if config is None:
        return {"status": "UNAVAILABLE", "query": "", "concepts": [], "required_matches": 0, "results": [],
                "notice": "Archive inconnue."}
    text = _public_text(query, MAX_QUERY_CHARS) if isinstance(query, str) else ""
    result: dict[str, Any] = {
        "status": "READY",
        "query": _public_text(text, 300),
        "concepts": [],
        "required_matches": 0,
        "results": [],
        "notice": config["notice"],
    }
    if not config["enabled"]():
        return {**result, "status": "DISABLED", "notice": config["disabled"]}
    concepts = query_concepts(text)
    if not concepts:
        return {**result, "status": "EMPTY_QUERY", "notice": "Saisissez au moins un mot-clé de 4 lettres ou plus."}
    endpoint = _archive_endpoint()
    if endpoint is None:
        return {**result, "status": "UNAVAILABLE", "concepts": concepts}
    need = len(concepts) if strict and len(concepts) <= 4 else required_matches(len(concepts))
    body: dict[str, Any] = {
        "corpus": corpus,
        "points": [{"id": "q", "concepts": concepts, "min_matches": need}],
        "limit": max(1, min(int(limit) if str(limit).isdigit() else DEFAULT_LIMIT, MAX_LIMIT)),
    }
    for key, value in (("since", _year(since)), ("until", _year(until))):
        if value is not None:
            body[key] = value
    payload = _service_post(endpoint, body)
    by_point = payload.get("points") if payload else None
    if not isinstance(by_point, Mapping):
        return {**result, "status": "UNAVAILABLE", "concepts": concepts, "required_matches": need}
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    items = by_point.get("q")
    for item in items if isinstance(items, Sequence) and not isinstance(items, (str, bytes)) else ():
        row = config["row"](item) if isinstance(item, Mapping) else None
        key = _normalize(row.get("excerpt")) if row else ""
        if row and key and key not in seen:
            seen.add(key)
            rows.append(row)
    return {**result, "concepts": concepts, "required_matches": need, "results": rows}
