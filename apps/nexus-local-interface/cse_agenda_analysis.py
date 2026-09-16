"""Local, deterministic analysis of an uploaded CSE meeting agenda."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
from pathlib import Path
import re
import unicodedata
from typing import Any

from NEXUS_RUNTIME_INTEGRATION.config import RuntimeCSEMemoryConfig
from SYNDICAL_REASONING_ENGINE.cse_models import MeetingBody, PVSearchQuery
from SYNDICAL_REASONING_ENGINE.cse_search import CSECSSCTSearchEngine


MAX_AGENDA_POINTS = 40
MAX_PREVIOUS_PASSAGES = 3
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


def _merge_previous_minutes(
    uploaded: Sequence[Mapping[str, Any]],
    corpus: Sequence[Mapping[str, Any]],
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
    for point in points:
        corpus_previous, corpus_status = _search_previous_minutes(
            engine,
            point["title"],
            point["position"],
        )
        uploaded_previous = _search_uploaded_minutes(
            additional_minutes_documents,
            point["title"],
        )
        previous = _merge_previous_minutes(uploaded_previous, corpus_previous)
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
    return {
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
