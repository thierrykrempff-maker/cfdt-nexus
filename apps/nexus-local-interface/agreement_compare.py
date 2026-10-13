"""Comparaison d'un ancien accord avec un nouvel accord, un avenant ou un projet, et contrôle des interférences.

Aide à la vérification, déterministe et locale : aucune interprétation juridique, aucun service externe.

- Les textes viennent de l'archive locale des accords (service du module « Précédents », ``127.0.0.1``) ou d'un fichier
  importé pour l'occasion (jamais conservé).
- Découpage en articles, appariement ancien/nouveau, différences phrase par phrase, valeurs chiffrées et termes
  d'obligation modifiés.
- Interférences : les autres accords de l'archive qui traitent des mêmes sujets (avec écarts de valeurs), et les textes
  que le nouvel accord cite, remplace ou abroge (retrouvés par leur date).
- Contexte : ce qui a été dit sur ces sujets dans les PV du CE/CSE, si l'archive des PV est activée.

Ne lève jamais d'exception vers l'appelant. Les extraits ne font partie d'aucun rapport ni export.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
import datetime
import difflib
import json
import re
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

from cse_agenda_analysis import (
    _ARCHIVE_TIMEOUT_SECONDS,
    _accord_kind,
    _accord_row,
    _accords_enabled,
    _archive_enabled,
    _archive_endpoint,
    _archive_row,
    _normalize,
    _public_text,
)
from pv_archive_search import query_concepts, required_matches


MAX_CHANGES = 40
MAX_TOPICS = 8
MAX_OLD_SENTENCES = 30000  # phrases de l'ancien texte indexées pour un avenant (plafond de temps de calcul)
_SHINGLE = 10  # longueur des fragments pour retrouver une phrase malgré l'OCR
MAX_SENTENCES = 80  # phrases comparées par article (plafond de temps de calcul)
EXCERPT_CHARS = 460
HEX_ID = re.compile(r"[0-9a-f]{16}")  # référence courte : le filtre de sortie de Nexus masque les hash complets
_SERVER_HEADERS = {"X-Nexus": "1", "X-Nexus-Server": "1"}

LIMITS = (
    "Comparaison automatique : le découpage en articles et l'appariement sont des heuristiques (OCR possible sur les anciens scans).",
    "Les « autres accords » sont les textes de l'archive qui traitent des mêmes sujets : à lire, pas à présumer en conflit.",
    "Ce n'est pas une analyse juridique : vérifiez la version en vigueur, les avenants, la dénonciation et la hiérarchie des normes.",
)


# --------------------------------------------------------------------------- service local
def _base_url() -> str | None:
    endpoint = _archive_endpoint()
    return endpoint.removesuffix("/api/passages") if endpoint else None


def _service_call(url: str, body: Mapping[str, Any] | None = None) -> Mapping[str, Any] | None:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = dict(_SERVER_HEADERS)
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib_request.Request(url, data=data, headers=headers, method="POST" if data is not None else "GET")
    try:
        with urllib_request.urlopen(request, timeout=_ARCHIVE_TIMEOUT_SECONDS) as response:  # noqa: S310 - loopback verifie
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib_error.URLError, OSError, ValueError):
        return None
    return payload if isinstance(payload, Mapping) else None


def _title_from_name(name: str) -> str:
    base = re.split(r"[\\/]", str(name))[-1]
    base = re.sub(r"\.[A-Za-z0-9]{2,5}$", "", base)
    return _public_text(re.sub(r"^\d{4}[.\-_ ]\d{2}[.\-_ ]\d{2}\s*[-_ ]*", "", base), 160) or "Accord"


def list_archive_agreements() -> dict[str, Any]:
    """Accords de l'archive, du plus récent au plus ancien (pour choisir l'ancien et le nouveau texte)."""

    if not _accords_enabled():
        return {"status": "DISABLED", "documents": [],
                "notice": "La comparaison d'accords n'est pas activée sur ce poste (option NEXUS_ACCORDS_ARCHIVE_ENABLED)."}
    base = _base_url()
    payload = _service_call(f"{base}/api/documents?corpus=accords") if base else None
    items = payload.get("documents") if payload else None
    if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
        return {"status": "UNAVAILABLE", "documents": [], "notice": "Le service d'archive est arrêté ou l'index des accords est absent."}
    documents = []
    for item in items:
        if not isinstance(item, Mapping) or not HEX_ID.fullmatch(str(item.get("id", ""))):
            continue
        name = str(item.get("fichier") or "")
        date = str(item.get("date") or "")
        documents.append({
            "id": str(item["id"]),
            "titre": _title_from_name(name),
            "type": _accord_kind(name),
            "date": date if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date) and not date.startswith("0000") else None,
            "precision_date": str(item.get("precision_date") or "?"),
        })
    documents.sort(key=lambda d: (d["date"] or "", d["titre"]), reverse=True)
    return {"status": "READY", "documents": documents}


def _fetch_text(doc_id: str) -> tuple[str, Mapping[str, Any]] | None:
    base = _base_url()
    if not base or not HEX_ID.fullmatch(doc_id):
        return None
    payload = _service_call(f"{base}/api/document", {"corpus": "accords", "id": doc_id})
    if not payload or not payload.get("ok") or not isinstance(payload.get("texte"), str):
        return None
    return payload["texte"], payload


# --------------------------------------------------------------------------- découpage en articles
_HEADING = re.compile(
    r"^\s*(?:art(?:icle)?s?\.?)\s*(?P<num>\d{1,3}(?:[.\-]\d{1,2})?)\s*(?:er|°|º)?\s*(?:[:.\-–—)]\s*|\s+)(?P<title>.{0,160})$",
    re.IGNORECASE,
)
_NUMBERED = re.compile(r"^\s*(?P<num>\d{1,2})\s*[.)\-]\s+(?P<title>[A-ZÉÈÀÂÊÎÔÛÇ][^\n]{3,110})$")


def clean_text(text: str) -> list[str]:
    """Lignes utiles : sans marqueurs de page, numéros de page seuls ni espaces parasites."""

    text = text.replace("\f", "\n").replace(" ", " ")
    lines = []
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        if re.fullmatch(r"-+ ?page \d+ ?-+", line, flags=re.IGNORECASE):
            continue
        if re.fullmatch(r"(?:page\s*)?\d{1,3}(?:\s*/\s*\d{1,3})?", line, flags=re.IGNORECASE):
            continue
        lines.append(line)
    return lines


def _tokens(text: str) -> set[str]:
    return {token for token in _normalize(text).split() if len(token) >= 3}


def _article(label: str, num: str | None, title: str, body_lines: Sequence[str]) -> dict[str, Any]:
    body = " ".join(line for line in body_lines if line).strip()
    return {
        "num": num,
        "label": label,
        "title": _public_text(title, 160),
        "body": body,
        "tokens": _tokens(title + " " + body),
        "title_tokens": _tokens(title),
    }


def parse_articles(text: str) -> list[dict[str, Any]]:
    """Découpe un accord en articles (« Article 4 - Titre »), sinon en rubriques numérotées, sinon en passages."""

    lines = clean_text(text)
    for pattern, prefix in ((_HEADING, "Article"), (_NUMBERED, "Rubrique")):
        found = [(index, match) for index, line in enumerate(lines) if (match := pattern.match(line))]
        if len(found) >= (1 if pattern is _HEADING else 2):  # un avenant peut ne reprendre qu'un seul article
            articles = []
            preamble = [line for line in lines[: found[0][0]] if line]
            if len(" ".join(preamble)) >= 120:
                articles.append(_article("Préambule", None, "Préambule", preamble))
            for position, (index, match) in enumerate(found):
                end = found[position + 1][0] if position + 1 < len(found) else len(lines)
                num = match.group("num").strip()
                articles.append(_article(f"{prefix} {num}", num, match.group("title").strip(" .:-–—"), lines[index + 1:end]))
            return articles
    paragraphs, current = [], []
    for line in lines + [""]:
        if line:
            current.append(line)
        elif current:
            paragraphs.append(" ".join(current))
            current = []
    chunks, buffer = [], ""
    for paragraph in paragraphs:
        buffer = f"{buffer} {paragraph}".strip()
        if len(buffer) >= 700:
            chunks.append(buffer)
            buffer = ""
    if buffer:
        chunks.append(buffer)
    return [_article(f"Passage {i}", None, chunk[:80], [chunk]) for i, chunk in enumerate(chunks, 1)]


def align(old: Sequence[Mapping[str, Any]], new: Sequence[Mapping[str, Any]]) -> list[tuple[int, int]]:
    """Apparie les articles : même numéro et contenu proche d'abord, puis meilleure ressemblance."""

    def jaccard(a: set[str], b: set[str]) -> float:
        return len(a & b) / len(a | b) if a and b else 0.0

    pairs: list[tuple[int, int]] = []
    used_old: set[int] = set()
    used_new: set[int] = set()
    for j, article in enumerate(new):
        if article["num"] is None:
            continue
        for i, previous in enumerate(old):
            if i in used_old or previous["num"] != article["num"]:
                continue
            similarity = max(jaccard(previous["title_tokens"], article["title_tokens"]), jaccard(previous["tokens"], article["tokens"]))
            if similarity >= 0.25:
                pairs.append((i, j))
                used_old.add(i)
                used_new.add(j)
            break
    candidates = sorted(
        (
            (jaccard(previous["tokens"], article["tokens"]), i, j)
            for i, previous in enumerate(old) if i not in used_old
            for j, article in enumerate(new) if j not in used_new
        ),
        reverse=True,
    )
    for similarity, i, j in candidates:
        if similarity < 0.45:
            break
        if i in used_old or j in used_new:
            continue
        pairs.append((i, j))
        used_old.add(i)
        used_new.add(j)
    return sorted(pairs, key=lambda pair: pair[1])


# --------------------------------------------------------------------------- différences
_LETTERHEAD = re.compile(
    r"(?i)\b(?:tel\.|fax\b|www\b|cedex\b|bp \d{3,})|\bsarralbe\b.{0,40}\bfrance\b"
    r"|\bfait [àa] \w+|\bpour (?:ineos|les organisations)|\brepr[ée]sent[ée]e? par\b|\b(?:d'une|d'autre) part\b"
    r"|\ben sa qualit[ée]\b"
)  # papier à en-tête, adresses, signatures et présentation des parties : bruit
_UNITS = {
    "%": "%", "€": "€", "euro": "€", "euros": "€", "eur": "€", "jour": "jour", "jours": "jour", "j": "jour",
    "heure": "heure", "heures": "heure", "h": "heure", "mois": "mois", "an": "an", "ans": "an",
    "semaine": "semaine", "semaines": "semaine", "point": "point", "points": "point", "fois": "fois",
    "minute": "minute", "minutes": "minute", "min": "minute",
}
_FIGURE = re.compile(
    r"(?<![\w.,])(\d{1,3}(?:[  ]\d{3})+|\d+)(?:[.,](\d+))?\s*(%|€|euros?|eur\b|jours?|j\b|heures?|h\b|mois|ans?|semaines?|points?|fois|minutes?|min\b)",
    re.IGNORECASE,
)
_CLOCK = re.compile(r"(?<![\w.,])(\d{1,2})\s?[hH]\s?(\d{2})?(?!\w)")  # 8H30, 16h : horaires
_MODALS = ("doit", "doivent", "devra", "devront", "peut", "peuvent", "pourra", "pourront", "obligatoire", "facultatif", "interdit", "autorise")


def _number_key(value: str) -> tuple[float, str]:
    try:
        return float(value), value
    except ValueError:  # horaires « 8h30 »
        digits = re.sub(r"\D", "", value)
        return (float(digits) if digits else 0.0), value


def figures(text: str) -> Counter[tuple[str, str]]:
    found: Counter[tuple[str, str]] = Counter()
    for match in _CLOCK.finditer(text):
        found[(f"{int(match.group(1))}h{match.group(2) or ''}", "heure")] += 1
    for match in _FIGURE.finditer(_CLOCK.sub(" ", text)):
        whole = re.sub(r"[  ]", "", match.group(1))
        value = f"{whole}.{match.group(2)}".rstrip("0").rstrip(".") if match.group(2) else whole
        found[(value, _UNITS.get(match.group(3).lower(), match.group(3).lower()))] += 1
    return found


def _figure_changes(before: Counter, after: Counter) -> list[str]:
    removed, added = before - after, after - before
    changes = []
    for unit in sorted({unit for _, unit in list(removed) + list(added)}):
        old_values = sorted((value for value, u in removed if u == unit), key=_number_key)
        new_values = sorted((value for value, u in added if u == unit), key=_number_key)
        changes.append(f"{unit} : {', '.join(old_values) or '—'} → {', '.join(new_values) or '—'}")
    return changes


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.;:!?])\s+(?=[A-ZÉÈÀÂÊÎÔÛÇ0-9«\"'(\-–•])", text)
    return [part.strip() for part in parts if len(part.strip()) >= 12]


def _modal_words(text: str) -> set[str]:
    return {word for word in _normalize(text).split() if word in _MODALS}


def diff_article(old: Mapping[str, Any], new: Mapping[str, Any]) -> dict[str, Any] | None:
    """Différences entre deux articles appariés ; ``None`` si le texte est identique au détail près."""

    old_norm, new_norm = _normalize(old["body"]), _normalize(new["body"])
    if old_norm == new_norm:
        return None
    ratio = difflib.SequenceMatcher(None, old_norm[:6000], new_norm[:6000], autojunk=False).ratio()
    old_sentences, new_sentences = _sentences(old["body"])[:MAX_SENTENCES], _sentences(new["body"])[:MAX_SENTENCES]
    old_keys, new_keys = [_normalize(s) for s in old_sentences], [_normalize(s) for s in new_sentences]

    def unmatched(sentences: list[str], keys: list[str], other_sentences: list[str], other_keys: list[str]) -> list[str]:
        result = []
        for sentence, key in zip(sentences, keys):
            if key in other_keys:
                continue
            close = difflib.get_close_matches(key, other_keys, n=1, cutoff=0.9)
            if close and figures(sentence) == figures(other_sentences[other_keys.index(close[0])]):
                continue  # même phrase à la ponctuation ou à une faute d'OCR près, valeurs chiffrées identiques
            result.append(sentence)
        return result

    removed = unmatched(old_sentences, old_keys, new_sentences, new_keys)
    added = unmatched(new_sentences, new_keys, old_sentences, old_keys)
    if ratio >= 0.985 and not removed and not added:
        return None
    figure_changes = _figure_changes(figures(" ".join(removed)), figures(" ".join(added)))
    modal_before, modal_after = _modal_words(" ".join(removed)), _modal_words(" ".join(added))
    modals = []
    if modal_before != modal_after:
        modals.append(f"{', '.join(sorted(modal_before)) or '—'} → {', '.join(sorted(modal_after)) or '—'}")
    return {
        "avant": [_public_text(s, EXCERPT_CHARS) for s in removed[:3]],
        "apres": [_public_text(s, EXCERPT_CHARS) for s in added[:3]],
        "autres_phrases_modifiees": max(0, len(removed) - 3) + max(0, len(added) - 3),
        "valeurs": figure_changes,
        "termes_d_obligation": modals,
        "ressemblance": round(ratio, 2),
    }


def _is_avenant(label: str, text: str, new_count: int, old_count: int) -> bool:
    if "avenant" in _normalize(label):
        return True
    return bool(re.search(r"\bavenant\b", _normalize(text[:900]))) and new_count < 0.6 * max(old_count, 1)


def compare_articles(old_articles: Sequence[Mapping[str, Any]], new_articles: Sequence[Mapping[str, Any]], avenant: bool) -> dict[str, Any]:
    pairs = align(old_articles, new_articles)
    paired_old = {i for i, _ in pairs}
    paired_new = {j for _, j in pairs}
    changes: list[dict[str, Any]] = []
    unchanged = 0
    for i, j in pairs:
        diff = diff_article(old_articles[i], new_articles[j])
        if diff is None:
            unchanged += 1
            continue
        changes.append({"type": "modifie", "article": new_articles[j]["label"], "ancien_article": old_articles[i]["label"],
                        "titre": new_articles[j]["title"] or old_articles[i]["title"], "_new_index": j, **diff})
    for j, article in enumerate(new_articles):
        if j not in paired_new:
            changes.append({"type": "ajoute", "article": article["label"], "titre": article["title"], "_new_index": j,
                            "apres": [_public_text(s, EXCERPT_CHARS) for s in _sentences(article["body"])[:3]] or [_public_text(article["body"], EXCERPT_CHARS)],
                            "avant": [], "valeurs": _figure_changes(Counter(), figures(article["body"])), "termes_d_obligation": []})
    not_targeted = 0
    for i, article in enumerate(old_articles):
        if i in paired_old:
            continue
        if avenant:
            not_targeted += 1  # un avenant ne reprend que les articles qu'il modifie : les autres restent applicables
            continue
        changes.append({"type": "supprime", "article": article["label"], "titre": article["title"], "_new_index": None,
                        "avant": [_public_text(s, EXCERPT_CHARS) for s in _sentences(article["body"])[:3]] or [_public_text(article["body"], EXCERPT_CHARS)],
                        "apres": [], "valeurs": _figure_changes(figures(article["body"]), Counter()), "termes_d_obligation": []})
    order = {"modifie": 0, "supprime": 1, "ajoute": 2}
    changes.sort(key=lambda c: (order[c["type"]], 0 if c["valeurs"] else 1, c["article"]))
    return {"changes": changes, "unchanged": unchanged, "not_targeted": not_targeted}


def compare_by_sentences(old_articles: Sequence[Mapping[str, Any]], new_articles: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Avenant : chaque phrase du nouveau texte est cherchée dans TOUT l'ancien accord.

    Un avenant ne reprend pas la numérotation de l'accord (il remplace des annexes, reformule des clauses...) : on ne peut
    pas l'apparier article par article. Une phrase est « reprise » (identique), « modifiée » (proche d'une phrase de
    l'ancien texte, avec l'ancienne phrase en regard) ou « nouvelle ». Chaque modification indique l'article de l'ancien
    accord auquel elle se rattache.
    """

    old_items: list[tuple[str, str, int]] = []  # (phrase, clé normalisée, indice de l'article ancien)
    for index, article in enumerate(old_articles):
        for sentence in _sentences(article["body"]):
            old_items.append((sentence, _normalize(sentence), index))
            if len(old_items) >= MAX_OLD_SENTENCES:
                break
    old_keys = [key for _, key, _ in old_items]
    exact = {key: position for position, key in enumerate(old_keys)}
    squashed = [key.replace(" ", "") for key in old_keys]  # l'OCR colle des mots : on compare sans espaces
    shingles: dict[str, list[int]] = defaultdict(list)
    for position, text in enumerate(squashed):
        for start in range(0, max(1, len(text) - _SHINGLE + 1), 3):
            bucket = shingles[text[start:start + _SHINGLE]]
            if len(bucket) < 60:
                bucket.append(position)

    def best_match(key: str) -> tuple[float, int]:
        if key in exact:
            return 1.0, exact[key]
        text = key.replace(" ", "")
        votes: Counter[int] = Counter()
        for start in range(max(1, len(text) - _SHINGLE + 1)):
            votes.update(shingles.get(text[start:start + _SHINGLE], ()))
        best = (0.0, -1)
        for position, _ in votes.most_common(12):
            ratio = difflib.SequenceMatcher(None, text, squashed[position], autojunk=False).ratio()
            if ratio > best[0]:
                best = (ratio, position)
        return best

    touched_old: set[int] = set()
    changes: list[dict[str, Any]] = []
    unchanged_articles = 0
    for j, article in enumerate(new_articles):
        reused = 0
        modified: list[tuple[str, str]] = []
        added: list[str] = []
        anchors: Counter[int] = Counter()
        for sentence in _sentences(article["body"])[:MAX_SENTENCES * 4]:
            if sum(ch.isalpha() for ch in sentence) < 20 or _LETTERHEAD.search(sentence):
                continue
            key = _normalize(sentence)
            ratio, position = best_match(key)
            if position >= 0 and ratio >= 0.6:
                touched_old.add(old_items[position][2])
                if ratio >= 0.97 and figures(sentence) == figures(old_items[position][0]):
                    reused += 1
                    continue
                anchors[old_items[position][2]] += 1
                modified.append((old_items[position][0], sentence))
            else:
                added.append(sentence)
        if not modified and not added:
            unchanged_articles += 1
            continue
        before = [old for old, _ in modified]
        after = [new for _, new in modified] + added
        anchor = old_articles[anchors.most_common(1)[0][0]]["label"] if anchors else None
        change = {
            "type": "modifie" if modified else "ajoute",
            "article": article["label"],
            "titre": article["title"],
            "ancien_article": anchor,
            "_new_index": j,
            "avant": [_public_text(x, EXCERPT_CHARS) for x in before[:3]],
            "apres": [_public_text(x, EXCERPT_CHARS) for x in after[:3]],
            "autres_phrases_modifiees": max(0, len(before) - 3) + max(0, len(after) - 3),
            "valeurs": _figure_changes(figures(" ".join(before)), figures(" ".join(x for x in after))),
            "termes_d_obligation": [],
            "phrases": {"reprises": reused, "modifiees": len(modified), "nouvelles": len(added)},
        }
        modal_before, modal_after = _modal_words(" ".join(before)), _modal_words(" ".join(after))
        if modal_before != modal_after:
            change["termes_d_obligation"] = [f"{', '.join(sorted(modal_before)) or '—'} → {', '.join(sorted(modal_after)) or '—'}"]
        changes.append(change)
    changes.sort(key=lambda c: (0 if c["type"] == "modifie" else 1, 0 if c["valeurs"] else 1, c["article"]))
    return {"changes": changes, "unchanged": unchanged_articles, "not_targeted": len(old_articles) - len(touched_old)}


# --------------------------------------------------------------------------- textes cités par le nouvel accord
_MONTHS = {"janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7, "aout": 8,
           "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12}
_CITATION = re.compile(
    r"(?P<kind>accords?|avenants?|protocoles?|conventions?|notes?|d[ée]cisions?|r[èe]glements?)[^.\n;]{0,110}?"
    r"(?:du|en date du|datant du|sign[ée]e? le|conclu le)\s+"
    r"(?:(?P<d>\d{1,2})[./\- ](?P<m>\d{1,2})[./\- ](?P<y>\d{4}|\d{2})\b"
    r"|(?P<d2>\d{1,2})(?:er)?\s+(?P<mon>janvier|f[ée]vrier|mars|avril|mai|juin|juillet|ao[ûu]t|septembre|octobre|novembre|d[ée]cembre)\s+(?P<y2>\d{4}))",
    re.IGNORECASE,
)
_EFFECTS = (
    ("remplace", r"annul\w*\s+et\s+remplac|se\s+substitu|remplac"),
    ("abroge", r"abrog"),
    ("denonce", r"d[ée]nonc"),
    ("revise", r"r[ée]vis"),
    ("modifie", r"modifi"),
    ("complete", r"compl[èe]t"),
    ("maintient", r"demeur\w*\s+(?:en\s+vigueur|applicable)|reste\w*\s+(?:en\s+vigueur|applicable|inchang)|inchang"),
)
_EFFECT_LABELS = {"remplace": "remplace", "abroge": "abroge", "denonce": "dénonce", "revise": "révise", "modifie": "modifie",
                  "complete": "complète", "maintient": "maintient en vigueur", "mentionne": "mentionne"}


def find_citations(text: str, documents: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    flat = " ".join(clean_text(text))
    by_date: dict[str, list[Mapping[str, Any]]] = {}
    for document in documents:
        if document.get("date"):
            by_date.setdefault(str(document["date"]), []).append(document)
    results: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for match in _CITATION.finditer(flat):
        try:
            if match.group("d"):
                year = int(match.group("y"))
                year += 2000 if year < 100 else 0
                date = datetime.date(year, int(match.group("m")), int(match.group("d")))
            else:
                date = datetime.date(int(match.group("y2")), _MONTHS[_normalize(match.group("mon"))], int(match.group("d2")))
        except (ValueError, KeyError):
            continue
        boundary = flat.rfind(". ", 0, match.start())
        start = boundary + 2 if boundary != -1 else 0
        end = flat.find(". ", match.end())
        sentence = flat[start:end + 1 if end != -1 else len(flat)]
        folded = _normalize(sentence)
        effect = next((name for name, pattern in _EFFECTS if re.search(pattern, folded)), "mentionne")
        key = (date.isoformat(), effect)
        if key in seen:
            continue
        seen.add(key)
        found = by_date.get(date.isoformat(), [])
        results.append({
            "date": date.isoformat(),
            "nature": match.group("kind").lower(),
            "effet": _EFFECT_LABELS[effect],
            "phrase": _public_text(sentence, EXCERPT_CHARS),
            "dans_l_archive": bool(found),
            "documents": [f"{d['titre']} ({d['type']})" for d in found[:3]],
        })
    return results[:12]


# --------------------------------------------------------------------------- interférences et contexte
def _topics(changes: Sequence[Mapping[str, Any]], new_articles: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    topics, seen = [], set()
    ranked = sorted((c for c in changes if c["type"] in {"modifie", "ajoute"}), key=lambda c: (0 if c["valeurs"] else 1, 0 if c["type"] == "ajoute" else 1))
    for change in ranked:
        article = new_articles[change["_new_index"]] if change.get("_new_index") is not None else None
        seed = f"{change['titre']} {' '.join(change['apres'][:1])}"
        concepts = query_concepts(seed)
        concepts = sorted(concepts, key=lambda c: (-len(c), c))[:6]
        if len(concepts) < 2 or tuple(sorted(concepts)) in seen:
            continue
        seen.add(tuple(sorted(concepts)))
        topics.append({"sujet": change["titre"] or change["article"], "article": change["article"], "mots": concepts,
                       "valeurs": figures(article["body"]) if article else Counter()})
        if len(topics) >= MAX_TOPICS:
            break
    return topics


def _conflicting_values(mine: Counter, other_text: str) -> list[str]:
    """Même unité, valeurs différentes entre le nouvel article et un autre texte : à vérifier."""

    theirs = figures(other_text)
    notes = []
    for unit in sorted({unit for _, unit in mine} & {unit for _, unit in theirs}):
        mine_values = {value for value, u in mine if u == unit}
        their_values = {value for value, u in theirs if u == unit}
        if mine_values and their_values and not (mine_values & their_values):
            notes.append(f"{unit} : {', '.join(sorted(mine_values, key=_number_key))} (nouveau texte) / {', '.join(sorted(their_values, key=_number_key))} (autre texte)")
    return notes[:3]


def _topic_search(base: str, corpus: str, topics: Sequence[Mapping[str, Any]], exclude: Sequence[str], limit: int) -> dict[str, list[Mapping[str, Any]]] | None:
    points = [{"id": f"t{i}", "concepts": t["mots"], "min_matches": required_matches(len(t["mots"]))} for i, t in enumerate(topics)]
    if not points:
        return {}
    payload = _service_call(f"{base}/api/passages", {"corpus": corpus, "points": points, "limit": limit, "exclude": list(exclude)})
    by_point = payload.get("points") if payload else None
    if not isinstance(by_point, Mapping):
        return None
    return {key: [row for row in rows if isinstance(row, Mapping)] for key, rows in by_point.items() if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes))}


# --------------------------------------------------------------------------- orchestration
def compare_texts(
    old_text: str,
    new_text: str,
    *,
    old_label: str,
    new_label: str,
    old_id: str | None = None,
    new_id: str | None = None,
    documents: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    old_articles, new_articles = parse_articles(old_text), parse_articles(new_text)
    if not old_articles or not new_articles:
        return {"status": "INVALID", "message": "Un des deux textes est vide ou illisible."}
    avenant = _is_avenant(new_label, new_text, len(new_articles), len(old_articles))
    compared = compare_by_sentences(old_articles, new_articles) if avenant else compare_articles(old_articles, new_articles, avenant)
    changes = compared["changes"]
    summary = {
        "inchanges": compared["unchanged"],
        "modifies": sum(c["type"] == "modifie" for c in changes),
        "ajoutes": sum(c["type"] == "ajoute" for c in changes),
        "supprimes": sum(c["type"] == "supprime" for c in changes),
        "non_vises_par_l_avenant": compared["not_targeted"],
        "valeurs_modifiees": sum(len(c["valeurs"]) for c in changes if c["type"] == "modifie"),
        "articles_anciens": len(old_articles),
        "articles_nouveaux": len(new_articles),
    }
    topics = _topics(changes, new_articles)
    citations = find_citations(new_text, documents)

    interferences: list[dict[str, Any]] = []
    meetings: list[dict[str, Any]] = []
    interference_status = "DISABLED"
    base = _base_url() if _accords_enabled() else None
    if base:
        exclude = [x for x in (old_id, new_id) if x]
        found = _topic_search(base, "accords", topics, exclude, 3)
        if found is None:
            interference_status = "UNAVAILABLE"
        else:
            interference_status = "READY"
            for i, topic in enumerate(topics):
                rows = []
                for raw in found.get(f"t{i}", []):
                    row = _accord_row(raw)
                    if row:
                        row["valeurs_differentes"] = _conflicting_values(topic["valeurs"], str(raw.get("extrait") or ""))
                        rows.append(row)
                if rows:
                    interferences.append({"sujet": topic["sujet"], "article": topic["article"], "mots": topic["mots"], "textes": rows})
        if _archive_enabled():
            title_topic = {"sujet": _title_from_name(new_label), "mots": sorted(query_concepts(_title_from_name(new_label)), key=lambda c: (-len(c), c))[:6]}
            context_topics = ([title_topic] if len(title_topic["mots"]) >= 1 else []) + topics[:3]
            found_pv = _topic_search(base, "pv", context_topics, [], 2) or {}
            seen_excerpts: set[str] = set()
            for i in range(len(context_topics)):
                for raw in found_pv.get(f"t{i}", []):
                    row = _archive_row(raw)
                    key = _normalize(row.get("excerpt")) if row else ""
                    if row and key and key not in seen_excerpts:
                        seen_excerpts.add(key)
                        row["sujet"] = context_topics[i]["sujet"]
                        meetings.append(row)
            meetings = meetings[:8]

    attention = _attention_points(summary, changes, avenant, citations, interferences, interference_status)
    public_changes = [{k: v for k, v in change.items() if not k.startswith("_")} for change in changes[:MAX_CHANGES]]
    return {
        "status": "READY",
        "mode": "avenant" if avenant else "remplacement",
        "ancien": {"titre": _title_from_name(old_label), "articles": len(old_articles)},
        "nouveau": {"titre": _title_from_name(new_label), "articles": len(new_articles)},
        "resume": summary,
        "points_attention": attention,
        "modifications": public_changes,
        "modifications_non_affichees": max(0, len(changes) - MAX_CHANGES),
        "interferences": interferences,
        "interferences_status": interference_status,
        "citations": citations,
        "reunions": meetings,
        "limites": list(LIMITS),
    }


def _attention_points(summary, changes, avenant, citations, interferences, interference_status) -> list[str]:
    points = []
    if not changes:
        points.append("Aucune différence détectée entre les deux textes (à confirmer à la lecture : OCR et découpage imparfaits).")
    if summary["valeurs_modifiees"]:
        points.append(f"{summary['valeurs_modifiees']} valeur(s) chiffrée(s) modifiée(s) (taux, montants, durées) : à vérifier une à une.")
    if summary["supprimes"]:
        titles = ", ".join(c["article"] for c in changes if c["type"] == "supprime")[:200]
        points.append(f"{summary['supprimes']} article(s) de l'ancien texte ne figurent plus dans le nouveau : {titles}.")
    if summary["ajoutes"]:
        points.append(f"{summary['ajoutes']} article(s) nouveau(x) sans équivalent dans l'ancien texte.")
    if any(c["termes_d_obligation"] for c in changes):
        points.append("Des termes d'obligation changent (peut / doit, facultatif / obligatoire…) : la portée de la clause peut changer.")
    if avenant:
        points.append(
            f"Texte traité comme un avenant : {summary['non_vises_par_l_avenant']} article(s) de l'accord initial ne sont pas visés et restent applicables sauf mention contraire."
        )
    replacing = [c for c in citations if c["effet"] in {"remplace", "abroge", "dénonce"}]
    for citation in replacing:
        where = "retrouvé dans l'archive" if citation["dans_l_archive"] else "NON retrouvé dans l'archive"
        points.append(f"Le nouveau texte {citation['effet']} un texte du {citation['date']} ({where}) : vérifier qu'il vise bien l'accord comparé.")
    if interferences:
        total = sum(len(item["textes"]) for item in interferences)
        points.append(f"{total} passage(s) d'autres accords traitent des mêmes sujets ({len(interferences)} sujet(s)) : voir « Autres accords concernés ».")
        if any(row["valeurs_differentes"] for item in interferences for row in item["textes"]):
            points.append("Des valeurs diffèrent entre le nouveau texte et d'autres accords sur le même sujet : possible incohérence à lever.")
    elif interference_status == "READY":
        points.append("Aucun autre accord de l'archive ne traite des mêmes sujets (selon les mots-clés retenus).")
    elif interference_status == "UNAVAILABLE":
        points.append("Contrôle des interférences impossible : le service d'archive est arrêté.")
    return points


# --------------------------------------------------------------------------- demande de l'interface
def _resolve_side(spec: object, read_attachment: Callable[[Mapping[str, Any]], tuple[str, str]], documents: Sequence[Mapping[str, Any]]):
    """Texte d'un côté de la comparaison : accord de l'archive (``id``) ou fichier importé (``attachment``)."""

    if not isinstance(spec, Mapping):
        return None
    if isinstance(spec.get("attachment"), Mapping):
        name, text = read_attachment(spec["attachment"])
        return {"label": name, "text": text, "id": None}
    doc_id = str(spec.get("id") or "")
    fetched = _fetch_text(doc_id)
    if fetched is None:
        return None
    text, meta = fetched
    known = next((d for d in documents if d["id"] == doc_id), None)
    return {"label": (known and known["titre"]) or _title_from_name(str(meta.get("fichier") or "")), "text": text, "id": doc_id,
            "filename": str(meta.get("fichier") or "")}


def compare_request(payload: object, read_attachment: Callable[[Mapping[str, Any]], tuple[str, str]]) -> dict[str, Any]:
    """Point d'entrée de la route HTTP. Ne lève jamais d'exception."""

    if not isinstance(payload, Mapping):
        return {"status": "INVALID", "message": "Requête invalide."}
    if not _accords_enabled():
        return {"status": "DISABLED", "message": "La comparaison d'accords n'est pas activée sur ce poste."}
    listing = list_archive_agreements()
    documents = listing.get("documents", [])
    try:
        old = _resolve_side(payload.get("old"), read_attachment, documents)
        new = _resolve_side(payload.get("new"), read_attachment, documents)
    except ValueError as error:
        return {"status": "INVALID", "message": str(error)}
    if old is None or new is None:
        status = "UNAVAILABLE" if listing["status"] == "UNAVAILABLE" else "INVALID"
        return {"status": status, "message": "Choisissez l'ancien et le nouveau texte (accord de l'archive ou fichier importé)."}
    if old.get("id") and old["id"] == new.get("id"):
        return {"status": "INVALID", "message": "Choisissez deux textes différents."}
    result = compare_texts(
        old["text"], new["text"],
        old_label=old.get("filename") or old["label"], new_label=new.get("filename") or new["label"],
        old_id=old["id"], new_id=new["id"], documents=documents,
    )
    return result
