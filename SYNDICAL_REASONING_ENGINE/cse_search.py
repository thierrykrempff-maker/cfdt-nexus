"""Deterministic hybrid search over prepared CSE/CSSCT JSONL chunks."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from time import monotonic
from typing import Any, Iterable, Mapping
import unicodedata

from .cse_models import (
    MeetingBody,
    MeetingType,
    NOT_A_LEGAL_NORM,
    PVDocument,
    PVPassage,
    PVSearchExecution,
    PVSearchQuery,
    PassageNature,
    SearchMode,
    SpeakerRole,
)


_DATE = re.compile(r"\b(20\d{2}|19\d{2})[-/.](0?[1-9]|1[0-2])[-/.]([0-2]?\d|3[01])\b")
_DATE_FR = re.compile(
    r"\b([0-2]?\d|3[01])\s+"
    r"(janvier|fevrier|mars|avril|mai|juin|juillet|aout|septembre|octobre|novembre|decembre)"
    r"\s+(20\d{2}|19\d{2})\b"
)
_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
_PHONE = re.compile(r"(?<!\d)(?:\+33|0)[1-9](?:[ .-]?\d{2}){4}(?!\d)")
_LOCAL_PATH = re.compile(r"(?i)(?:\b[A-Z]:\\|/(?:home|users|tmp)/)\S+")
_NAME_AFTER_ROLE = re.compile(
    r"(?i)\b(?:m\.?|mr\.?|mme|monsieur|madame)\s+"
    r"[A-ZÀ-ÖØ-Ý][A-Za-zÀ-ÖØ-öø-ÿ'-]+"
)
_FULL_NAME = re.compile(
    r"\b[A-ZÀ-ÖØ-Ý][a-zà-öø-ÿ'-]{2,}\s+[A-ZÀ-ÖØ-Ý][a-zà-öø-ÿ'-]{2,}\b"
)
_SENSITIVE = re.compile(
    r"(?i)\b(?:diagnostic|pathologie|traitement médical|arrêt maladie de|sanction de "
    r"|appartenance syndicale|secret industriel)\b"
)
_TABLE_LIKE = re.compile(r"(?:\S+\s+){1,4}\d+(?:\s+\d+){5,}")
_MONTHS = {
    "janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
    "juillet": 7, "aout": 8, "septembre": 9, "octobre": 10,
    "novembre": 11, "decembre": 12,
}
_SYNONYMS = {
    "pause": {"pause", "pauses", "cigarette", "tabac", "fumer", "vapoter"},
    "badgeage": {"badgeage", "pointage", "tourniquet", "badge", "décompte"},
    "epi": {"epi", "gants", "visière", "lunettes", "équipement", "protection"},
    "horaire": {"horaire", "horaires", "poste", "posté", "équipe", "3x8"},
    "rps": {"rps", "psychosocial", "souffrance", "fatigue", "tension", "conflit"},
    "procedure": {"procédure", "instruction", "recette", "version", "diffusion"},
    "alcool": {"alcool", "alcoolémie", "éthylotest", "contre-expertise", "calibration"},
}
_GENERIC_QUERY_TERMS = frozenset(
    {
        "quel", "quelle", "quels", "quelles", "concret", "existe", "entre",
        "entreprise", "peut", "etre", "role", "projet", "implique", "information",
        "consultation", "precedent", "informe", "consulte", "saisi", "comparable",
    }
)
_BROAD_DOCUMENTARY_CONCEPTS = frozenset(
    {
        "procedure", "diffusion", "information", "consultation", "conflit",
        "incident", "alerte", "risque", "fatigue", "organisation", "horaire",
        "horaires", "projet", "personnel", "role", "precedent",
    }
)


def _norm(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def _stable(prefix: str, *parts: object) -> str:
    digest = hashlib.sha256("\x1f".join(str(part) for part in parts).encode()).hexdigest()[:24]
    return f"pv-{prefix}-{digest}"


def _metadata(item: Mapping[str, Any], key: str) -> Any:
    metadata = item.get("metadata_snapshot")
    value = metadata.get(key) if isinstance(metadata, Mapping) else None
    return value.get("value") if isinstance(value, Mapping) else None


def _body(item: Mapping[str, Any]) -> MeetingBody:
    declared = _norm(_metadata(item, "instance"))
    if declared in {"cse", "cssct", "ce", "chsct", "commission"}:
        return {
            "cse": MeetingBody.CSE,
            "cssct": MeetingBody.CSSCT,
            "ce": MeetingBody.CE,
            "chsct": MeetingBody.CHSCT,
            "commission": MeetingBody.COMMISSION,
        }[declared]
    value = _norm(item.get("source_relative_path", ""))
    if "cssct" in value:
        return MeetingBody.CSSCT
    if "chsct" in value:
        return MeetingBody.CHSCT
    if "commission" in value:
        return MeetingBody.COMMISSION
    if "cse" in value:
        return MeetingBody.CSE
    if re.search(r"\bce\b", value):
        return MeetingBody.CE
    return MeetingBody.UNKNOWN


def _meeting_type(item: Mapping[str, Any]) -> MeetingType:
    value = _norm(f"{_metadata(item, 'meeting_type')} {item.get('source_relative_path', '')}")
    for marker, result in (
        ("extraordinaire", MeetingType.EXTRAORDINARY),
        ("preparatoire", MeetingType.PREPARATORY),
        ("suivi", MeetingType.FOLLOW_UP),
        ("special", MeetingType.SPECIAL),
        ("ordinaire", MeetingType.ORDINARY),
    ):
        if marker in value:
            return result
    return MeetingType.UNKNOWN


def _date(item: Mapping[str, Any]) -> tuple[str | None, str]:
    direct = str(_metadata(item, "meeting_date") or "")
    values = (direct, str(item.get("source_relative_path") or ""), str(item.get("text") or "")[:500])
    for value in values:
        normalized = _norm(value)
        if match := _DATE.search(normalized):
            year, month, day = map(int, match.groups())
            try:
                return datetime(year, month, day).date().isoformat(), "high"
            except ValueError:
                pass
        if match := _DATE_FR.search(normalized):
            day, month, year = match.groups()
            try:
                return datetime(int(year), _MONTHS[month], int(day)).date().isoformat(), "medium"
            except ValueError:
                pass
    years = re.findall(r"\b(?:19|20)\d{2}\b", " ".join(values))
    return (f"{years[0]}-01-01", "low") if years else (None, "very_low")


def _speaker_and_nature(text: str) -> tuple[str | None, SpeakerRole, PassageNature, str, str]:
    normalized = _norm(text[:500])
    patterns = (
        (("la direction repond", "reponse de la direction"), SpeakerRole.MANAGEMENT,
         PassageNature.MANAGEMENT_RESPONSE, "Le passage attribue explicitement une réponse à la direction."),
        (("la direction informe", "la direction indique", "la direction precise"),
         SpeakerRole.MANAGEMENT, PassageNature.MANAGEMENT_INFORMATION,
         "Le passage attribue explicitement une information à la direction."),
        (("les elus demandent", "question des elus", "les representants demandent"),
         SpeakerRole.ELECTED_REPRESENTATIVE, PassageNature.EMPLOYEE_REPRESENTATIVE_QUESTION,
         "Le passage formule explicitement une question ou demande des élus."),
        (("s engage", "engagement de la direction"), SpeakerRole.MANAGEMENT,
         PassageNature.COMMITMENT, "Le texte emploie une formulation explicite d’engagement."),
        (("il est decide", "decision adoptee", "le cse decide"), SpeakerRole.UNKNOWN,
         PassageNature.DECISION, "Le texte emploie une formulation explicite de décision."),
        (("desaccord", "conteste"), SpeakerRole.UNKNOWN,
         PassageNature.DISAGREEMENT, "Le passage exprime explicitement un désaccord."),
        (("alerte", "danger grave"), SpeakerRole.UNKNOWN,
         PassageNature.WARNING, "Le passage comporte un signalement ou une alerte explicite."),
        (("suivi", "point precedent"), SpeakerRole.UNKNOWN,
         PassageNature.FOLLOW_UP, "Le passage est identifié comme un suivi."),
    )
    for markers, role, nature, reason in patterns:
        if any(marker in normalized for marker in markers):
            public = _NAME_AFTER_ROLE.sub("<personne>", text[:120])
            return public if public != text[:120] else None, role, nature, reason, "high"
    if "?" in text:
        return None, SpeakerRole.UNKNOWN, PassageNature.DISCUSSION, (
            "Une interrogation est visible mais son auteur n’est pas établi."
        ), "medium"
    return None, SpeakerRole.UNKNOWN, PassageNature.DISCUSSION, (
        "La structure ne permet pas une qualification plus précise."
    ), "low"


def _redact(text: str) -> tuple[str, bool]:
    redacted = _EMAIL.sub("<email expurgé>", text)
    redacted = _PHONE.sub("<téléphone expurgé>", redacted)
    redacted = _LOCAL_PATH.sub("<chemin local expurgé>", redacted)
    redacted = _NAME_AFTER_ROLE.sub("<personne>", redacted)
    redacted = _FULL_NAME.sub("<personne>", redacted)
    return redacted, redacted != text


def _readable(text: str) -> bool:
    if len(_norm(text)) < 30 or _TABLE_LIKE.search(text):
        return False
    replacement_ratio = text.count("�") / max(1, len(text))
    alpha_ratio = sum(char.isalpha() for char in text) / max(1, len(text))
    return replacement_ratio < 0.02 and alpha_ratio > 0.35


def _exact_excerpt(text: str, max_length: int = 700) -> str:
    """Select complete source sentences without paraphrasing or cutting words."""

    candidate = text.strip()
    if candidate and candidate[0].islower():
        boundaries = [
            position + 1
            for separator in ("\n", ". ", "? ", "! ")
            if 0 <= (position := candidate.find(separator, 0, 180))
        ]
        if boundaries:
            candidate = candidate[min(boundaries):].lstrip()
    if len(candidate) <= max_length:
        return candidate
    window = candidate[:max_length]
    sentence_ends = [
        match.end() for match in re.finditer(r"[.!?](?:\s|$)", window)
        if match.end() >= max_length // 3
    ]
    if sentence_ends:
        return window[: sentence_ends[-1]].strip()
    return window.rsplit(" ", 1)[0].strip() + "…"


@dataclass(frozen=True, slots=True)
class PVCorpusInventory:
    root_status: str
    file_count: int
    document_count: int
    indexable_document_count: int
    chunk_count: int
    indexable_chunk_count: int
    page_count: int
    formats: tuple[tuple[str, int], ...]
    bodies: tuple[tuple[str, int], ...]
    meeting_types: tuple[tuple[str, int], ...]
    date_range: str | None
    documents_without_date: int
    empty_documents: int
    duplicate_documents: int
    documents_with_warnings: int
    cssct_distinguished: bool
    quality: tuple[tuple[str, int], ...]

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "corpus_status": self.root_status,
            "documents": self.indexable_document_count,
            "chunks": self.indexable_chunk_count,
            "period": self.date_range,
            "bodies": dict(self.bodies),
            "quality": dict(self.quality),
        }


class CSECSSCTSearchEngine:
    """Read-only search over importer outputs, with no network or implicit corpus."""

    def __init__(self, processed_root: Path | str | None) -> None:
        self._root = Path(processed_root).resolve() if processed_root else None

    def _chunk_files(self) -> tuple[Path, ...]:
        root = self._root / "chunks" if self._root else None
        if root is None or not root.is_dir() or root.is_symlink():
            return ()
        return tuple(
            path for path in sorted(root.glob("*.jsonl"), key=lambda item: item.name)
            if path.is_file() and not path.is_symlink()
        )

    def _rows(self) -> tuple[Mapping[str, Any], ...]:
        rows: list[Mapping[str, Any]] = []
        for path in self._chunk_files():
            try:
                with path.open("r", encoding="utf-8") as stream:
                    for line in stream:
                        if not line.strip():
                            continue
                        value = json.loads(line)
                        if isinstance(value, Mapping):
                            rows.append(value)
            except (OSError, ValueError, UnicodeError):
                continue
        return tuple(rows)

    def inventory(self) -> PVCorpusInventory:
        rows = self._rows()
        if not self._chunk_files():
            return PVCorpusInventory(
                "UNAVAILABLE", 0, 0, 0, 0, 0, 0, (), (), (), None, 0, 0, 0, 0, False, ()
            )
        by_doc: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
        for row in rows:
            by_doc[str(row.get("document_id") or "")].append(row)
        documents = [items[0] for key, items in by_doc.items() if key]
        dates = [_date(item)[0] for item in documents]
        valid_dates = sorted(item for item in dates if item)
        hashes = [str(item.get("source_sha256") or "") for item in documents]
        formats = Counter(Path(str(item.get("source_relative_path") or "")).suffix.lower() for item in documents)
        bodies = Counter(_body(item).value for item in documents)
        types = Counter(_meeting_type(item).value for item in documents)
        quality = Counter(str(item.get("document_quality_level") or "unknown") for item in documents)
        return PVCorpusInventory(
            "AVAILABLE",
            len(self._chunk_files()),
            len(documents),
            sum(any(bool(row.get("indexable")) for row in items) for items in by_doc.values()),
            len(rows),
            sum(bool(row.get("indexable")) for row in rows),
            len({page for row in rows for page in (row.get("page_numbers") or ())}),
            tuple(sorted(formats.items())),
            tuple(sorted(bodies.items())),
            tuple(sorted(types.items())),
            f"{valid_dates[0][:4]}–{valid_dates[-1][:4]}" if valid_dates else None,
            sum(date is None for date in dates),
            sum(not any(str(row.get("text") or "").strip() for row in items) for items in by_doc.values()),
            sum(count - 1 for count in Counter(item for item in hashes if item).values() if count > 1),
            sum(any(row.get("warnings") for row in items) for items in by_doc.values()),
            any(_body(item) is MeetingBody.CSSCT for item in documents),
            tuple(sorted(quality.items())),
        )

    @staticmethod
    def from_research_query(
        query: Any,
        *,
        case_session_id: str,
        body_scope: tuple[MeetingBody, ...],
        blocked: bool = False,
        max_results: int = 8,
    ) -> PVSearchQuery:
        original_concepts = tuple(
            dict.fromkeys(str(item) for item in query.concepts if str(item).strip())
        )
        concepts = tuple(
            item for item in original_concepts if _norm(item) not in _GENERIC_QUERY_TERMS
        )
        if not concepts:
            concepts = ("question juridique sans concept documentaire spécifique",)
        variants: list[str] = []
        for concept in concepts:
            normalized = _norm(concept)
            for family in _SYNONYMS.values():
                if normalized in {_norm(item) for item in family}:
                    variants.extend(sorted(family))
        return PVSearchQuery(
            query.query_id,
            query.issue_id,
            query.target_id,
            case_session_id,
            concepts,
            tuple(dict.fromkeys(variants)),
            (),
            tuple(query.negative_terms),
            query.temporal_scope,
            body_scope,
            query.establishment_scope,
            tuple(query.document_types),
            0.22,
            max_results,
            query.reason,
            blocked,
            query.reason,
        )

    def search(self, query: PVSearchQuery) -> PVSearchExecution:
        started_dt = datetime.now(timezone.utc)
        timer = monotonic()
        inventory = self.inventory()
        if query.blocked:
            return self._execution(query, inventory, started_dt, timer, (), 0, 0, (
                "Recherche suspendue : informations manquantes.",
            ), (), ())
        rows = self._rows()
        if inventory.root_status != "AVAILABLE":
            return self._execution(query, inventory, started_dt, timer, (), 0, 0, (
                "Corpus CSE/CSSCT non configuré.",
            ), ("CORPUS_UNAVAILABLE",), ())
        concepts = tuple(dict.fromkeys(
            _norm(item) for item in (*query.concepts, *query.variants, *query.exact_phrases)
            if _norm(item)
        ))
        negative = tuple(_norm(item) for item in query.negative_terms if _norm(item))
        temporal_years = tuple(
            int(item) for item in re.findall(r"\b(?:19|20)\d{2}\b", query.temporal_scope)
        )
        temporal_min = min(temporal_years) if temporal_years else None
        temporal_max = max(temporal_years) if temporal_years else None
        candidates: list[tuple[float, Mapping[str, Any], tuple[str, ...], float, float]] = []
        rejected = Counter()
        scanned_docs: set[str] = set()
        for row in rows:
            if not row.get("indexable"):
                rejected["NOT_INDEXABLE"] += 1
                continue
            document_id = str(row.get("document_id") or "")
            scanned_docs.add(document_id)
            body = _body(row)
            if query.body_scope and body not in query.body_scope:
                rejected["BODY_SCOPE"] += 1
                continue
            meeting_date, _ = _date(row)
            if meeting_date and temporal_min is not None:
                year = int(meeting_date[:4])
                if year < temporal_min or year > temporal_max:
                    rejected["TEMPORAL_SCOPE"] += 1
                    continue
            relative = _norm(row.get("source_relative_path"))
            establishment = _norm(query.establishment_scope)
            if establishment not in {"", "all", "unknown", "tous"}:
                declared_establishment = _norm(_metadata(row, "establishment"))
                inferred_establishment = next(
                    (
                        marker for marker in ("sarralbe", "tavaux")
                        if marker in relative
                    ),
                    "",
                )
                actual_establishment = declared_establishment or inferred_establishment
                if actual_establishment and establishment not in actual_establishment:
                    rejected["ESTABLISHMENT_SCOPE"] += 1
                    continue
            requested_types = {_norm(item) for item in query.document_types}
            actual_kind = _norm(_metadata(row, "document_kind") or "")
            if requested_types and actual_kind:
                asks_annex = any("annexe" in item or "support" in item for item in requested_types)
                asks_minutes = any(
                    marker in item
                    for item in requested_types
                    for marker in ("minute", "pv", "proces verbal", "cse", "cssct")
                )
                is_annex = "annexe" in actual_kind or "presentation" in actual_kind
                if asks_annex and not asks_minutes and not is_annex:
                    rejected["DOCUMENT_TYPE"] += 1
                    continue
                if asks_minutes and not asks_annex and is_annex:
                    rejected["DOCUMENT_TYPE"] += 1
                    continue
            text = str(row.get("text") or "").strip()
            if not _readable(text):
                rejected["UNREADABLE"] += 1
                continue
            normalized = _norm(text)
            if any(term and term in normalized for term in negative):
                rejected["NEGATIVE_TERM"] += 1
                continue
            matched = tuple(item for item in concepts if item in normalized)
            if not matched:
                rejected["NO_CONCEPT"] += 1
                continue
            exact_hits = sum(_norm(item) in normalized for item in query.exact_phrases)
            distinctive = tuple(
                item for item in concepts
                if item not in _BROAD_DOCUMENTARY_CONCEPTS and len(item) >= 4
            )
            if distinctive and not set(matched).intersection(distinctive):
                rejected["MISSING_DISTINCTIVE_CONCEPT"] += 1
                continue
            minimum_concepts = 1 if len(concepts) == 1 else 2
            if len(matched) < minimum_concepts and not exact_hits:
                rejected["INSUFFICIENT_CONCEPT_PROXIMITY"] += 1
                continue
            lexical = min(1.0, (len(matched) + exact_hits * 2) / max(2, len(concepts)))
            tokens = set(normalized.split())
            semantic_families = sum(
                bool(tokens.intersection({_norm(item) for item in family}))
                for family in _SYNONYMS.values()
                if any(_norm(item) in {_norm(v) for v in family} for item in concepts)
            )
            semantic = min(1.0, (len(matched) + semantic_families) / max(2, len(concepts)))
            positions = sorted(normalized.find(item) for item in matched if normalized.find(item) >= 0)
            proximity = (
                1.0
                if len(positions) <= 1
                else max(0.0, 1.0 - (positions[-1] - positions[0]) / max(1, len(normalized)))
            )
            final = round(0.57 * lexical + 0.33 * semantic + 0.10 * proximity, 6)
            if final < query.min_score:
                rejected["BELOW_THRESHOLD"] += 1
                continue
            candidates.append((final, row, matched, lexical, semantic))
        candidates.sort(
            key=lambda item: (
                -item[0],
                str(item[1].get("document_id") or ""),
                int(item[1].get("chunk_index") or 0),
            )
        )
        by_doc_rows = defaultdict(dict)
        for row in rows:
            by_doc_rows[str(row.get("document_id") or "")][int(row.get("chunk_index") or 0)] = row
        retained: list[PVPassage] = []
        documents: dict[str, PVDocument] = {}
        for final, row, matched, lexical, semantic in candidates[: query.max_results]:
            passage = self._passage(query, row, matched, lexical, semantic, final, by_doc_rows)
            if passage.sensitive:
                rejected["SENSITIVE"] += 1
                continue
            retained.append(passage)
            documents[passage.document_id] = self._document(row, by_doc_rows[passage.document_id])
        return self._execution(
            query,
            inventory,
            started_dt,
            timer,
            tuple(retained),
            len(candidates),
            len(scanned_docs),
            (() if retained else ("Aucun résultat suffisamment pertinent.",)),
            (),
            tuple(sorted(rejected.items())),
            tuple(documents.values()),
        )

    def _document(
        self, row: Mapping[str, Any], chunks: Mapping[int, Mapping[str, Any]]
    ) -> PVDocument:
        relative = str(row.get("source_relative_path") or "document")
        date, confidence = _date(row)
        body = _body(row)
        title = str(_metadata(row, "title") or Path(relative).stem or "PV")
        public_title = f"{body.value} {date or 'date non établie'}"
        pages = {page for item in chunks.values() for page in (item.get("page_numbers") or ())}
        return PVDocument(
            str(row.get("document_id") or _stable("document", relative)),
            title,
            public_title,
            body,
            _meeting_type(row),
            date,
            confidence,
            "Sarralbe" if "sarralbe" in _norm(relative) else None,
            hashlib.sha256(relative.encode()).hexdigest(),
            Path(relative).suffix.lower() or "unknown",
            max(pages) if pages else None,
            len(chunks),
            str(row.get("created_at") or ""),
            str(row.get("chunking_version") or "1.0"),
            False,
            tuple(str(item) for item in row.get("warnings") or ()),
            str(_metadata(row, "document_kind") or "minutes"),
        )

    def _passage(
        self,
        query: PVSearchQuery,
        row: Mapping[str, Any],
        matched: tuple[str, ...],
        lexical: float,
        semantic: float,
        final: float,
        by_doc_rows: Mapping[str, Mapping[int, Mapping[str, Any]]],
    ) -> PVPassage:
        text = str(row.get("text") or "").strip()
        redacted_text, was_redacted = _redact(text)
        excerpt = _exact_excerpt(redacted_text)
        idx = int(row.get("chunk_index") or 0)
        document_id = str(row.get("document_id") or "")
        siblings = by_doc_rows[document_id]
        before = str(siblings.get(idx - 1, {}).get("text") or "")[-240:] or None
        after = str(siblings.get(idx + 1, {}).get("text") or "")[:240] or None
        before = _redact(before)[0] if before else None
        after = _redact(after)[0] if after else None
        speaker, role, nature, reason, confidence = _speaker_and_nature(text)
        document_kind = _norm(_metadata(row, "document_kind") or "")
        if "annexe" in document_kind or "presentation" in document_kind:
            speaker = None
            role = SpeakerRole.UNKNOWN
            nature = PassageNature.DOCUMENT_REFERENCE
            reason = "Le document est qualifié comme annexe ou support préparatoire."
            confidence = "high"
        date, _ = _date(row)
        pages = row.get("page_numbers") or ()
        page = ", ".join(str(item) for item in pages) or f"chunk {idx + 1}"
        limitations = [
            NOT_A_LEGAL_NORM,
            "La qualification dépend de la structure explicite du texte indexé.",
        ]
        if not date:
            limitations.append("Date de réunion non établie dans les métadonnées.")
        if was_redacted:
            limitations.append("Extrait expurgé pour protéger des identifiants.")
        return PVPassage(
            _stable("passage", query.query_id, document_id, idx),
            document_id,
            query.query_id,
            query.issue_id,
            matched[0],
            page,
            str(row.get("chunk_id") or _stable("chunk", document_id, idx)),
            str(_metadata(row, "title") or "") or None,
            text,
            _norm(text),
            excerpt,
            _body(row),
            _meeting_type(row),
            date,
            speaker,
            role,
            nature,
            tuple(sorted(set(matched))),
            matched,
            semantic,
            lexical,
            final,
            confidence,
            bool(_SENSITIVE.search(text)),
            before,
            after,
            reason,
            tuple(limitations),
            f"Le document contient un passage relatif à : {', '.join(matched)}.",
            (
                "Ce passage ne prouve ni l’existence d’une règle collective ni son "
                f"opposabilité. {NOT_A_LEGAL_NORM}"
            ),
            {
                PassageNature.MANAGEMENT_RESPONSE: "position de la direction",
                PassageNature.COMMITMENT: "engagement",
                PassageNature.DECISION: "décision interne",
                PassageNature.EMPLOYEE_REPRESENTATIVE_QUESTION: "demande des élus",
            }.get(nature, "contexte et chronologie"),
            was_redacted,
        )

    @staticmethod
    def _execution(
        query: PVSearchQuery,
        inventory: PVCorpusInventory,
        started: datetime,
        timer: float,
        results: tuple[PVPassage, ...],
        matched: int,
        scanned: int,
        warnings: tuple[str, ...],
        errors: tuple[str, ...],
        rejected: tuple[tuple[str, int], ...],
        documents: tuple[PVDocument, ...] = (),
    ) -> PVSearchExecution:
        completed = datetime.now(timezone.utc)
        return PVSearchExecution(
            _stable("execution", query.query_id, query.case_session_id),
            query.query_id,
            inventory.root_status,
            inventory.indexable_document_count,
            scanned,
            inventory.indexable_chunk_count if inventory.root_status == "AVAILABLE" else 0,
            matched,
            len(results),
            started.isoformat(),
            completed.isoformat(),
            max(0, int((monotonic() - timer) * 1000)),
            SearchMode.HYBRID_LOCAL if inventory.root_status == "AVAILABLE" else SearchMode.DEGRADED_MODE,
            query.concepts,
            warnings,
            errors,
            results,
            documents,
            rejected,
            inventory.date_range,
        )


__all__ = ("CSECSSCTSearchEngine", "PVCorpusInventory")
