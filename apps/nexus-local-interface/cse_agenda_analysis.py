"""Local, deterministic analysis of an uploaded CSE meeting agenda."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
import os
from pathlib import Path
import re
import unicodedata
from typing import Any
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

from NEXUS_RUNTIME_INTEGRATION.config import RuntimeCSEMemoryConfig
from SYNDICAL_REASONING_ENGINE.cse_models import MeetingBody, PVSearchQuery
from SYNDICAL_REASONING_ENGINE.cse_search import CSECSSCTSearchEngine


MAX_AGENDA_POINTS = 40
MAX_PREVIOUS_PASSAGES = 3
MAX_ARCHIVE_PASSAGES = 3
# Source optionnelle « archive PV » : service local du module Précédents (loopback uniquement).
# Désactivée par défaut, comme les autres activations locales (voir start-nexus-local.bat).
_ARCHIVE_FLAG = "NEXUS_PV_ARCHIVE_ENABLED"
# Seconde archive : accords d'entreprise (même service local, corpus « accords »). Désactivée par défaut.
_ACCORDS_FLAG = "NEXUS_ACCORDS_ARCHIVE_ENABLED"
MAX_ACCORDS_PASSAGES = 3
_ARCHIVE_URL_VARIABLE = "NEXUS_PV_ARCHIVE_URL"
_ARCHIVE_DEFAULT_URL = "http://127.0.0.1:8791"
_ARCHIVE_TIMEOUT_SECONDS = 10
_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
_AGENDA_NAME_MARKERS = ("ordre", "jour", "odj", "agenda", "convocation")
_HEADER = re.compile(
    r"(?i)^(?:ordre\s+du\s+jour|odj|agenda|convocation|réunion\s+(?:ordinaire|extraordinaire)|date|lieu|participants?)\s*:?$"
)


class _AgendaSearchEngine(CSECSSCTSearchEngine):
    """Reuse one immutable corpus snapshot during a single agenda analysis."""

    def __init__(self, processed_root: Path | str | None) -> None:
        super().__init__(processed_root)
        self._agenda_rows_cache: tuple[tuple[Mapping[str, Any], ...], int] | None = None

    def _load_rows(self) -> tuple[tuple[Mapping[str, Any], ...], int]:
        if self._agenda_rows_cache is None:
            self._agenda_rows_cache = super()._load_rows()
        return self._agenda_rows_cache
_BULLET = re.compile(r"^\s*(?:\d{1,2}(?:[.)-]|\s+-)|[A-Z](?:[.)-])|[-–—•*])\s*(.+?)\s*$")
_NUMBERED_POINT = re.compile(r"^\s*(\d{1,2})(?:[.)-]|\s+-)\s*(.+?)\s*$")
_UNPUNCTUATED_MEMBER_POINT = re.compile(
    r"^\s*(\d{1,2})\s+(questions?\s+(?:des|de\s+la|du)\s+(?:membres?|élus?|délégation)\b.*?)\s*$",
    re.IGNORECASE,
)
_SIMPLE_BULLET = re.compile(r"^\s*[-–—•*]\s*(.+?)\s*$")
_MEMBER_QUESTIONS = re.compile(
    r"(?i)\bquestions?\s+(?:des|de\s+la|du)\s+(?:membres?|élus?|délégation)\b"
)
_NUMBERED_INLINE = re.compile(r"(?=(?:^|\s)(?:\d{1,2}[.)])\s+)")
_STOP_WORDS = frozenset(
    {
        "afin", "ainsi", "avec", "cette", "dans", "des", "donc", "elle", "elles",
        "entre", "être", "leur", "leurs", "mais", "nous", "notre", "pour", "quel",
        "quelle", "quelles", "quels", "sans", "sera", "seront", "sont", "sous", "sur",
        "une", "vous", "votre", "point", "points", "question", "questions", "information",
        "informations", "présentation", "divers", "cse", "ordre", "jour", "direction",
    }
)


def _normalize(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def _public_text(value: object, limit: int = 500) -> str:
    return " ".join(str(value or "").split())[:limit].strip()


def _agenda_document(documents: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    if not documents:
        return None
    ranked = sorted(
        documents,
        key=lambda item: (
            -sum(marker in _normalize(item.get("name")) for marker in _AGENDA_NAME_MARKERS),
            str(item.get("name") or "").casefold(),
        ),
    )
    return ranked[0]


def _document_lines(document: Mapping[str, Any]) -> list[tuple[str, str]]:
    output: list[tuple[str, str]] = []
    passages = document.get("passages")
    if not isinstance(passages, Sequence) or isinstance(passages, (str, bytes, bytearray)):
        passages = ({"reference": "Document", "text": document.get("text")},)
    for passage in passages:
        if not isinstance(passage, Mapping):
            continue
        reference = _public_text(passage.get("reference"), 100) or "Document"
        text = str(passage.get("text") or "").replace("\r", "\n")
        lines = [line.strip() for line in re.split(r"\n+", text) if line.strip()]
        if len(lines) == 1 and len(lines[0]) > 240:
            lines = [part.strip() for part in _NUMBERED_INLINE.split(lines[0]) if part.strip()]
        output.extend((reference, line) for line in lines)
    return output


def _agenda_section(line: str) -> str | None:
    normalized = _normalize(line)
    if "mis a l ordre du jour" in normalized and "direction" in normalized:
        return "DIRECTION"
    if (
        "mis a l ordre du jour" in normalized
        and any(marker in normalized for marker in ("organisation syndicale", "organisations syndicales", "delegation"))
    ) or (
        "questions" in normalized
        and any(marker in normalized for marker in ("membre", "elu", "delegation"))
    ):
        return "MEMBERS"
    return None


def _direction_section_lines(lines: Sequence[tuple[str, str]]) -> list[tuple[str, str, str]]:
    """Keep unnumbered direction items from their explicit agenda section."""

    output: list[tuple[str, str, str]] = []
    in_direction_section = False
    for reference, line in lines:
        section = _agenda_section(line)
        if section == "DIRECTION":
            in_direction_section = True
            continue
        if section == "MEMBERS" and in_direction_section:
            break
        if not in_direction_section:
            continue
        numbered = _NUMBERED_POINT.match(line)
        bullet = _SIMPLE_BULLET.match(line)
        candidate = numbered.group(2) if numbered else bullet.group(1) if bullet else line
        candidate = candidate.strip(" -–—•\t")
        if not candidate or _HEADER.match(candidate) or len(candidate) < 8:
            continue
        direction_index = len(output) + 1
        output.append((f"D{direction_index}", reference, _public_text(candidate, 700)))
    return output


def _candidate_lines(document: Mapping[str, Any]) -> list[tuple[str, str, str]]:
    """Return real agenda points, excluding preamble and administrative lines."""

    lines = _document_lines(document)
    def numbered_point(line: str) -> re.Match[str] | None:
        return _NUMBERED_POINT.match(line) or _UNPUNCTUATED_MEMBER_POINT.match(line)

    numbered = [item for item in lines if numbered_point(item[1])]
    output: list[tuple[str, str, str]] = _direction_section_lines(lines)
    if numbered:
        active_member_position: str | None = None
        member_subquestion_index = 0
        for reference, line in lines:
            numbered_match = numbered_point(line)
            if numbered_match:
                position = numbered_match.group(1)
                candidate = numbered_match.group(2).strip(" -–—•\t")
                active_member_position = position if _MEMBER_QUESTIONS.search(candidate) else None
                member_subquestion_index = 0
                if candidate and not _HEADER.match(candidate) and 4 <= len(candidate) <= 700:
                    output.append((position, reference, _public_text(candidate, 700)))
                continue
            if active_member_position:
                bullet = _SIMPLE_BULLET.match(line)
                candidate = bullet.group(1) if bullet else line if "?" in line else ""
                candidate = candidate.strip(" -–—•\t")
                if candidate and 6 <= len(candidate) <= 700:
                    member_subquestion_index += 1
                    output.append(
                        (
                            f"{active_member_position}.{member_subquestion_index}",
                            reference,
                            _public_text(f"Question des membres — {candidate}", 700),
                        )
                    )
        return output

    # OCR or plain-text agendas sometimes lose numbering. In that degraded case,
    # keep bounded bullet lines and explicit member-question headings only.
    for reference, line in lines:
        match = _BULLET.match(line)
        candidate = match.group(1) if match else line
        candidate = candidate.strip(" -–—•\t")
        if not candidate or _HEADER.match(candidate):
            continue
        if not match and not _MEMBER_QUESTIONS.search(candidate):
            continue
        if 12 <= len(candidate) <= 700:
            output.append((str(len(output) + 1), reference, _public_text(candidate, 700)))
    return output


def extract_agenda_points(document: Mapping[str, Any]) -> list[dict[str, str]]:
    """Extract bounded agenda points while preserving their source reference."""

    unique: list[dict[str, str]] = []
    seen: set[str] = set()
    for position, reference, candidate in _candidate_lines(document):
        normalized = _normalize(candidate)
        if normalized in seen or len(normalized) < 10:
            continue
        seen.add(normalized)
        unique.append(
            {
                "position": position,
                "display_label": (
                    f"Direction — point {position[1:]}"
                    if position.startswith("D") and position[1:].isdigit()
                    else f"Point {position}"
                ),
                "title": candidate,
                "source_reference": reference,
            }
        )
        if len(unique) >= MAX_AGENDA_POINTS:
            break
    return unique


def _concepts(title: str) -> tuple[str, ...]:
    tokens = [
        token
        for token in _normalize(title).split()
        if len(token) >= 4 and token not in _STOP_WORDS and not token.isdigit()
    ]
    return tuple(dict.fromkeys(tokens))[:8]


def _stable_id(prefix: str, *values: str) -> str:
    digest = hashlib.sha256("\x1f".join(values).encode("utf-8")).hexdigest()[:20]
    return f"agenda-{prefix}-{digest}"


def _search_previous_minutes(
    engine: CSECSSCTSearchEngine,
    title: str,
    position: str,
) -> tuple[list[dict[str, Any]], str]:
    concepts = _concepts(title)
    if not concepts:
        return [], engine.inventory().root_status
    identity = _stable_id("point", position, title)
    query = PVSearchQuery(
        query_id=_stable_id("query", identity),
        issue_id=_stable_id("issue", identity),
        target_id=_stable_id("target", identity),
        case_session_id=_stable_id("session", title),
        concepts=concepts,
        variants=(),
        exact_phrases=(),
        negative_terms=(),
        temporal_scope="",
        body_scope=(
            MeetingBody.CSE,
            MeetingBody.CE,
            MeetingBody.CSSCT,
            MeetingBody.CHSCT,
            MeetingBody.COMMISSION,
        ),
        establishment_scope="Sarralbe",
        document_types=("meeting_minutes", "pv", "proces verbal"),
        min_score=0.22,
        max_results=MAX_PREVIOUS_PASSAGES,
        purpose="Vérifier si le point de l’ordre du jour a déjà été traité.",
        blocked=False,
        reason="Comparaison locale et factuelle avec les anciens PV.",
    )
    execution = engine.search(query)
    rows: list[dict[str, Any]] = []
    for passage in execution.results:
        public = passage.to_dict(public=True)
        rows.append(
            {
                "title": _public_text(public.get("section_title"), 180)
                or f"{public.get('meeting_body') or 'PV'} {public.get('meeting_date') or 'date non établie'}",
                "date": public.get("meeting_date"),
                "instance": public.get("meeting_body") or "CSE",
                "reference": _public_text(public.get("page"), 100),
                "excerpt": _public_text(public.get("excerpt"), 700),
                "nature": public.get("passage_nature") or "DISCUSSION",
                "relation": _public_text(public.get("proves"), 300),
                "limits": [
                    "Ce passage constitue un contexte historique et non une norme juridique.",
                    "L’absence de résultat ne prouve pas que le sujet n’a jamais été traité.",
                ],
            }
        )
    return rows, execution.corpus_root_status


def _search_uploaded_minutes(
    documents: Sequence[Mapping[str, Any]],
    title: str,
) -> list[dict[str, Any]]:
    """Match user-provided minutes in memory without persisting their contents."""

    concepts = _concepts(title)
    if not concepts:
        return []
    minimum_matches = 2 if len(concepts) >= 3 else 1
    candidates: list[tuple[int, str, str, str]] = []
    for document in documents:
        name = _public_text(document.get("name"), 160) or "Ancien PV importé"
        passages = document.get("passages")
        if not isinstance(passages, Sequence) or isinstance(passages, (str, bytes, bytearray)):
            passages = ({"reference": "Document", "text": document.get("text")},)
        for passage in passages:
            if not isinstance(passage, Mapping):
                continue
            text = _public_text(passage.get("text"), 2000)
            normalized = _normalize(text)
            matched = tuple(concept for concept in concepts if concept in normalized)
            if len(matched) < minimum_matches:
                continue
            candidates.append(
                (
                    len(matched),
                    name,
                    _public_text(passage.get("reference"), 100) or "Document",
                    text,
                )
            )
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for match_count, name, reference, text in sorted(
        candidates, key=lambda item: (-item[0], item[1].casefold(), item[2])
    ):
        excerpt = _public_text(text, 700)
        key = _normalize(excerpt)
        if not key or key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "title": name,
                "date": None,
                "instance": "PV importé",
                "reference": reference,
                "excerpt": excerpt,
                "nature": "CONTEXTE_HISTORIQUE",
                "origin": "UPLOADED_MINUTES",
                "relation": f"{match_count} notion(s) du point apparaissent dans ce passage du PV importé.",
                "limits": [
                    "Ce passage provient d’un PV ajouté pour cette analyse uniquement.",
                    "Il constitue un contexte historique et non une norme juridique.",
                ],
            }
        )
        if len(rows) >= MAX_PREVIOUS_PASSAGES:
            break
    return rows


def _archive_enabled() -> bool:
    return os.environ.get(_ARCHIVE_FLAG, "").strip().lower() in {"1", "true", "yes", "on"}


def _archive_endpoint() -> str | None:
    """URL du service d'archive, uniquement si elle désigne la machine locale."""

    base = os.environ.get(_ARCHIVE_URL_VARIABLE, "").strip() or _ARCHIVE_DEFAULT_URL
    parsed = urllib_parse.urlparse(base)
    if parsed.scheme != "http" or (parsed.hostname or "") not in _LOOPBACK_HOSTS:
        return None
    return f"{parsed.scheme}://{parsed.netloc}/api/passages"


def _archive_date(date: object, precision: object) -> str | None:
    text = str(date or "")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text) or text.startswith("0000"):
        return None
    if precision == "jour":
        return text
    if precision == "mois":
        return text[:7]
    return text[:4]


def _archive_row(raw: Mapping[str, Any]) -> dict[str, Any] | None:
    excerpt = _public_text(raw.get("extrait"), 700)
    if not excerpt:
        return None
    path = str(raw.get("fichier") or "")
    name = re.split(r"[\\/]", path)[-1]
    title = _public_text(re.sub(r"\.[A-Za-z0-9]{2,5}$", "", name), 180) or "PV de l’archive"
    instance = "CSE" if re.search(r"(?i)\bPV du CSE\b", path) else "CE"
    notions = [
        _public_text(item, 60)
        for item in (raw.get("notions") if isinstance(raw.get("notions"), Sequence) else ())
        if item
    ]
    page = raw.get("page")
    return {
        "title": title,
        "date": _archive_date(raw.get("date"), raw.get("precision_date")),
        "instance": f"{instance} · archive PV",  # visible dans le titre : distingue ces passages des autres sources
        "reference": f"p. {page}" if isinstance(page, int) and page > 0 else "",
        "excerpt": excerpt,
        "nature": "CONTEXTE_HISTORIQUE",
        "origin": "PV_ARCHIVE",
        "relation": (
            f"Notion(s) du point retrouvée(s) dans ce PV de l’archive : {', '.join(notions)}."
            if notions
            else "Passage rapproché du point par les termes factuels du sujet."
        ),
        "limits": [
            "Ce passage provient de l’archive locale des PV du CE/CSE (OCR possible sur les anciens scans).",
            "Il constitue un contexte historique et non une norme juridique.",
            "L’absence de résultat ne prouve pas que le sujet n’a jamais été traité.",
        ],
    }


def _search_pv_archive(
    points: Sequence[Mapping[str, Any]],
) -> tuple[dict[int, list[dict[str, Any]]], str]:
    """Interroge l'archive locale des PV en une seule requête ; ne lève jamais d'exception.

    Renvoie ({indice du point: passages}, statut) avec statut DISABLED, READY ou UNAVAILABLE.
    """

    if not _archive_enabled():
        return {}, "DISABLED"
    endpoint = _archive_endpoint()
    if endpoint is None:
        return {}, "UNAVAILABLE"
    request_points = []
    for index, point in enumerate(points):
        concepts = _concepts(str(point.get("title") or ""))
        if concepts:
            request_points.append(
                {
                    "id": str(index),
                    "concepts": list(concepts),
                    "min_matches": 2 if len(concepts) >= 3 else 1,
                }
            )
    if not request_points:
        return {}, "READY"
    request = urllib_request.Request(
        endpoint,
        data=json.dumps({"points": request_points}).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-Nexus": "1",
            "X-Nexus-Server": "1",
        },
        method="POST",
    )
    try:
        with urllib_request.urlopen(request, timeout=_ARCHIVE_TIMEOUT_SECONDS) as response:  # noqa: S310 - loopback verifie
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib_error.URLError, OSError, ValueError):
        return {}, "UNAVAILABLE"
    by_point = payload.get("points") if isinstance(payload, Mapping) else None
    if not isinstance(by_point, Mapping):
        return {}, "UNAVAILABLE"
    rows: dict[int, list[dict[str, Any]]] = {}
    for key, items in by_point.items():
        if not str(key).isdigit() or not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
            continue
        converted = [row for row in (_archive_row(item) for item in items if isinstance(item, Mapping)) if row]
        if converted:
            rows[int(key)] = converted[:MAX_ARCHIVE_PASSAGES]
    return rows, "READY"


def _accords_enabled() -> bool:
    return os.environ.get(_ACCORDS_FLAG, "").strip().lower() in {"1", "true", "yes", "on"}


_ACCORD_KINDS = (
    ("desaccord", "PV de désaccord"),  # avant « accord », que ce mot contient
    ("avenant", "Avenant"),
    ("protocole", "Protocole d’accord"),
    ("reglement", "Règlement"),
    ("charte", "Charte"),
    ("code de conduite", "Code de conduite"),
    ("accord", "Accord"),
)


def _accord_kind(name: str) -> str:
    folded = _normalize(name)
    for marker, label in _ACCORD_KINDS:
        if marker in folded:
            return label
    return "Document"


def _accord_row(raw: Mapping[str, Any]) -> dict[str, Any] | None:
    """Passage d'un accord de l'archive locale, au format des autres extraits (titre, date, extrait...)."""

    excerpt = _public_text(raw.get("extrait"), 700)
    if not excerpt:
        return None
    path = str(raw.get("fichier") or "")
    name = re.split(r"[\\/]", path)[-1]
    base = re.sub(r"\.[A-Za-z0-9]{2,5}$", "", name)
    title = _public_text(re.sub(r"^\d{4}[.\-_ ]\d{2}[.\-_ ]\d{2}\s*[-_ ]*", "", base), 180) or "Accord de l’archive"
    notions = [
        _public_text(item, 60)
        for item in (raw.get("notions") if isinstance(raw.get("notions"), Sequence) else ())
        if item
    ]
    page = raw.get("page")
    return {
        "title": title,
        "date": _archive_date(raw.get("date"), raw.get("precision_date")),
        "instance": f"{_accord_kind(name)} · archive accords",
        "reference": f"p. {page}" if isinstance(page, int) and page > 0 else "",
        "excerpt": excerpt,
        "nature": "TEXTE_ACCORD",
        "origin": "ACCORDS_ARCHIVE",
        "relation": (
            f"Notion(s) du point retrouvée(s) dans ce texte : {', '.join(notions)}."
            if notions
            else "Passage rapproché du point par les termes factuels du sujet."
        ),
        "limits": [
            "Texte tiré de l’archive locale des accords (OCR possible sur les anciens scans).",
            "Vérifiez la version en vigueur, les avenants et une éventuelle dénonciation avant de vous en servir.",
            "Ce n’est pas une analyse juridique ; l’absence de résultat ne prouve pas qu’aucun accord n’existe.",
        ],
    }


def _search_accords_archive(
    points: Sequence[Mapping[str, Any]],
) -> tuple[dict[int, list[dict[str, Any]]], str]:
    """Cherche chaque point dans l'archive des accords (une seule requête) ; ne lève jamais d'exception."""

    if not _accords_enabled():
        return {}, "DISABLED"
    endpoint = _archive_endpoint()
    if endpoint is None:
        return {}, "UNAVAILABLE"
    request_points = []
    for index, point in enumerate(points):
        concepts = _concepts(str(point.get("title") or ""))
        if concepts:
            request_points.append(
                {"id": str(index), "concepts": list(concepts), "min_matches": 2 if len(concepts) >= 3 else 1}
            )
    if not request_points:
        return {}, "READY"
    request = urllib_request.Request(
        endpoint,
        data=json.dumps({"corpus": "accords", "points": request_points}).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Nexus": "1", "X-Nexus-Server": "1"},
        method="POST",
    )
    try:
        with urllib_request.urlopen(request, timeout=_ARCHIVE_TIMEOUT_SECONDS) as response:  # noqa: S310 - loopback verifie
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib_error.URLError, OSError, ValueError):
        return {}, "UNAVAILABLE"
    by_point = payload.get("points") if isinstance(payload, Mapping) else None
    if not isinstance(by_point, Mapping):
        return {}, "UNAVAILABLE"
    rows: dict[int, list[dict[str, Any]]] = {}
    for key, items in by_point.items():
        if not str(key).isdigit() or not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
            continue
        converted = [row for row in (_accord_row(item) for item in items if isinstance(item, Mapping)) if row]
        if converted:
            rows[int(key)] = converted[:MAX_ACCORDS_PASSAGES]
    return rows, "READY"


def _merge_previous_minutes(
    uploaded: Sequence[Mapping[str, Any]],
    corpus: Sequence[Mapping[str, Any]],
    archive: Sequence[Mapping[str, Any]] = (),
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in (*uploaded, *corpus):
        key = _normalize(row.get("excerpt"))
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(dict(row))
        if len(merged) >= MAX_PREVIOUS_PASSAGES:
            break
    # L'archive complète les deux sources existantes sans jamais les remplacer ni changer leur ordre.
    added = 0
    for row in archive:
        key = _normalize(row.get("excerpt"))
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(dict(row))
        added += 1
        if added >= MAX_ARCHIVE_PASSAGES:
            break
    return merged


def _clarity(title: str) -> tuple[str, str]:
    normalized = _normalize(title)
    vague = any(marker in normalized.split() for marker in ("information", "presentation", "divers"))
    asks = "?" in title or any(
        normalized.startswith(marker)
        for marker in ("comment ", "pourquoi ", "quand ", "quel ", "quelle ", "quels ", "quelles ")
    )
    if asks:
        return "QUESTION_EXPLICITE", "Le point contient une question explicite qui peut recevoir une réponse vérifiable."
    if vague or len(normalized.split()) < 5:
        return "A_PRECISER", "Le libellé est trop général : il faut préciser l’objet, les faits attendus et la décision demandée."
    return "SUJET_IDENTIFIE", "Le sujet est identifiable, mais la décision attendue du CSE doit être formulée explicitement."


def _management_questions(title: str, previous: Sequence[Mapping[str, Any]]) -> list[str]:
    subject = _public_text(title, 240)
    questions = [
        f"Quel est l’objectif exact du point « {subject} » et quelle décision ou quel avis attendez-vous du CSE ?",
        f"Quels faits, données chiffrées et documents vérifiables la direction transmet-elle sur « {subject} » ?",
        f"Quelles conséquences concrètes sont prévues pour les salariés, les équipes, les horaires, la charge et la sécurité ?",
        f"Quelles solutions alternatives ont été étudiées, selon quels critères, et pourquoi ont-elles été écartées ou retenues ?",
    ]
    if previous:
        reference = [previous[0].get("title"), previous[0].get("date")]
        label = " — ".join(str(item) for item in reference if item) or "l’ancien PV retrouvé"
        questions.insert(
            1,
            f"Quelles suites précises ont été données au sujet comparable retrouvé dans {label}, et quels engagements restent ouverts ?",
        )
    return questions[:5]


def build_cse_agenda_analysis(
    uploaded_documents: Sequence[Mapping[str, Any]],
    *,
    processed_root: Path | str | None = None,
    selected_positions: Sequence[str] | None = None,
    additional_minutes_documents: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Build a public-safe point-by-point agenda analysis and PV comparison."""

    document = _agenda_document(uploaded_documents)
    if document is None:
        return {
            "status": "AGENDA_REQUIRED",
            "message": "Ajoutez l’ordre du jour pour lancer l’analyse point par point.",
            "points": [],
        }
    points = extract_agenda_points(document)
    if selected_positions is not None:
        selected = {str(position) for position in selected_positions}
        points = [point for point in points if point["position"] in selected]
    if not points:
        return {
            "status": "AGENDA_SELECTION_REQUIRED" if selected_positions is not None else "AGENDA_UNREADABLE",
            "agenda_document": _public_text(document.get("name"), 160),
            "message": (
                "Sélectionnez au moins un point de l’ordre du jour à approfondir."
                if selected_positions is not None
                else "Aucun point d’ordre du jour suffisamment lisible n’a été détecté."
            ),
            "points": [],
        }

    config = RuntimeCSEMemoryConfig.from_env()
    root = Path(processed_root) if processed_root is not None else config.processed_root
    engine = _AgendaSearchEngine(root)
    analyzed = []
    corpus_status = engine.inventory().root_status
    archive_rows, archive_status = _search_pv_archive(points)
    accords_rows, accords_status = _search_accords_archive(points)
    for index, point in enumerate(points):
        corpus_previous, corpus_status = _search_previous_minutes(
            engine,
            point["title"],
            point["position"],
        )
        uploaded_previous = _search_uploaded_minutes(
            additional_minutes_documents,
            point["title"],
        )
        previous = _merge_previous_minutes(uploaded_previous, corpus_previous, archive_rows.get(index, ()))
        clarity, analysis = _clarity(point["title"])
        analyzed.append(
            {
                **point,
                "clarity": clarity,
                "analysis": analysis,
                "previously_discussed": bool(previous),
                "previous_minutes": previous,
                "questions_for_management": _management_questions(point["title"], previous),
                "checks_before_meeting": [
                    "Vérifier que les documents nécessaires ont été transmis assez tôt pour permettre un examen utile.",
                    "Formuler séparément les faits à obtenir, la réponse demandée et la décision ou l’avis attendu du CSE.",
                ],
            }
        )
        if accords_status != "DISABLED":
            analyzed[-1]["agreements"] = accords_rows.get(index, [])
    result: dict[str, Any] = {
        "status": "READY",
        "agenda_document": _public_text(document.get("name"), 160),
        "agenda_point_count": len(analyzed),
        "points_with_previous_minutes": sum(item["previously_discussed"] for item in analyzed),
        "uploaded_previous_minutes_count": len(additional_minutes_documents),
        "corpus_status": corpus_status,
        "corpus_notice": (
            "Le corpus d’anciens PV est partiellement indexé ; les résultats retrouvés sont exploitables, mais l’absence de résultat n’établit jamais l’absence de traitement antérieur."
            if corpus_status == "PARTIAL"
            else "La comparaison utilise les anciens PV disponibles dans le corpus local."
        ),
        "points": analyzed,
    }
    if archive_status != "DISABLED":
        result["archive_status"] = archive_status
        result["points_with_archive_minutes"] = sum(
            any(row.get("origin") == "PV_ARCHIVE" for row in item["previous_minutes"]) for item in analyzed
        )
        result["corpus_notice"] = (
            f"{result['corpus_notice']} "
            + (
                "L’archive complète des PV du CE/CSE a aussi été interrogée (extraits locaux, jamais publiés)."
                if archive_status == "READY"
                else "L’archive des PV est activée mais indisponible : lancez le service local « Précédents »."
            )
        )
    if accords_status != "DISABLED":
        result["accords_status"] = accords_status
        result["points_with_agreements"] = sum(bool(item.get("agreements")) for item in analyzed)
        result["corpus_notice"] = (
            f"{result['corpus_notice']} "
            + (
                "Les accords de l’archive locale ont aussi été consultés (extraits locaux, jamais publiés)."
                if accords_status == "READY"
                else "L’archive des accords est activée mais indisponible : lancez le service local « Précédents »."
            )
        )
    return result
