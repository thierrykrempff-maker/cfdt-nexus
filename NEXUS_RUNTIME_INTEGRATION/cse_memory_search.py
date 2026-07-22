"""Read-only lexical access to the existing CSE Memory LOT 1D chunk outputs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json
from pathlib import Path
import re
import time
import unicodedata
from typing import Any

from automation.cse_memory.document_models import DocumentRecord

from .config import RuntimeCSEMemoryConfig


_CSE_MARKERS = (
    "pv cse", "ancien pv", "decision cse", "consultation", "avis", "reunion",
    "ordre du jour", "commission", "historique", "vote", "resolution",
)
_STRONG_CSE_MARKERS = ("pv cse", "ancien pv", "decision cse", "ordre du jour")
_STOP_WORDS = frozenset({
    "dans", "pour", "avec", "sans", "quel", "quelle", "quels", "quelles", "ancien",
    "ancienne", "document", "documents", "concernant", "retrouver", "trouve", "trouver",
    "notre", "disait", "parle", "parlait", "sujet", "que", "sur",
})
_GENERIC_CSE_TERMS = frozenset({"cse", "pv", "avis", "reunion", "ordre", "jour", "historique"})


def _normalize(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return " ".join(re.findall(r"[a-z0-9]+", text.encode("ascii", "ignore").decode().lower()))


def needs_cse_memory(answer: Mapping[str, Any]) -> bool:
    """Use existing router domains first, then a closed documentary marker list."""
    route = answer.get("route") if isinstance(answer.get("route"), Mapping) else {}
    domains = {str(item) for item in route.get("domains") or ()}
    intents = {str(item) for item in route.get("intents") or ()}
    query = _normalize(answer.get("query"))
    if "cse" in domains and any(marker in query for marker in _CSE_MARKERS):
        return True
    if "rechercher_cse_memory" in intents:
        return True
    return any(marker in query for marker in _STRONG_CSE_MARKERS)


@dataclass(frozen=True, slots=True)
class CSEMemorySearchResult:
    documents: tuple[DocumentRecord, ...] = ()
    document_count: int = 0
    chunk_count: int = 0
    duration_ms: int = 0
    fallback_code: str | None = None


class RuntimeCSEMemoryGateway:
    """Scan prepared JSONL chunks without changing corpus, index or source documents."""

    def __init__(self, config: RuntimeCSEMemoryConfig) -> None:
        self._config = config

    def search(self, answer: Mapping[str, Any]) -> CSEMemorySearchResult:
        started = time.perf_counter()
        root = self._config.processed_root
        chunk_root = root / "chunks" if root is not None else None
        if chunk_root is None or not chunk_root.is_dir():
            return self._empty(started, "CSE_MEMORY_UNAVAILABLE")
        tokens = self._tokens(answer.get("query"))
        if not tokens:
            return self._empty(started, "CSE_MEMORY_NO_MATCH")
        candidates = []
        for path in sorted(chunk_root.glob("*.jsonl"), key=lambda item: item.name):
            if not path.is_file() or path.is_symlink():
                continue
            with path.open("r", encoding="utf-8") as stream:
                for line in stream:
                    if not line.strip():
                        continue
                    item = json.loads(line)
                    if not isinstance(item, Mapping) or not item.get("indexable"):
                        continue
                    score = self._score(tokens, item)
                    if score:
                        candidates.append((score, str(item.get("document_id") or ""), item))
        candidates.sort(key=lambda row: (-row[0], row[1], int(row[2].get("chunk_index") or 0)))
        selected = candidates[: self._config.max_chunks]
        if not selected:
            return self._empty(started, "CSE_MEMORY_NO_MATCH")
        by_document: dict[str, list[Mapping[str, Any]]] = {}
        for _, document_id, chunk in selected:
            if document_id and (document_id in by_document or len(by_document) < self._config.max_documents):
                by_document.setdefault(document_id, []).append(chunk)
        documents = tuple(
            self._document(document_id, chunks)
            for document_id, chunks in sorted(by_document.items())
        )
        return CSEMemorySearchResult(
            documents,
            len(documents),
            sum(len(items) for items in by_document.values()),
            self._duration(started),
        )

    @staticmethod
    def _tokens(query: object) -> tuple[str, ...]:
        tokens = tuple(
            token for token in dict.fromkeys(_normalize(query).split())
            if len(token) >= 3 and token not in _STOP_WORDS
        )
        specific = tuple(token for token in tokens if token not in _GENERIC_CSE_TERMS)
        return specific or tokens

    @staticmethod
    def _score(tokens: Sequence[str], item: Mapping[str, Any]) -> int:
        metadata = item.get("metadata_snapshot") if isinstance(item.get("metadata_snapshot"), Mapping) else {}
        metadata_values = " ".join(
            str(value.get("value") or "")
            for value in metadata.values()
            if isinstance(value, Mapping)
        )
        searchable = set(_normalize(f"{item.get('text') or ''} {metadata_values}").split())
        metadata_words = set(_normalize(metadata_values).split())
        return sum(2 if token in metadata_words else 1 for token in tokens if token in searchable)

    @staticmethod
    def _document(document_id: str, chunks: list[Mapping[str, Any]]) -> DocumentRecord:
        first = chunks[0]
        relative_path = str(first.get("source_relative_path") or "cse/document")
        metadata = first.get("metadata_snapshot") if isinstance(first.get("metadata_snapshot"), Mapping) else {}
        year = RuntimeCSEMemoryGateway._metadata_value(metadata, "year")
        family = RuntimeCSEMemoryGateway._metadata_value(metadata, "document_kind") or "cse_document"
        created_at = str(first.get("created_at") or "")
        text_length = sum(int(item.get("unique_text_length_chars") or 0) for item in chunks)
        return DocumentRecord(
            document_id=document_id,
            source_relative_path=relative_path,
            source_filename=Path(relative_path).name,
            source_extension=Path(relative_path).suffix.lower(),
            source_size_bytes=text_length,
            source_sha256=str(first.get("source_sha256") or ""),
            source_modified_at=created_at,
            detected_year=str(year) if year is not None else None,
            detected_family=str(family),
            extractor_name="cse_memory_lot_1d",
            extractor_method="prepared_chunk_lookup",
            extraction_status="extracted",
            extraction_error_code=None,
            extraction_error_message=None,
            text_content="",
            text_length=text_length,
            page_count=None,
            sheet_count=None,
            slide_count=None,
            paragraph_count=None,
            technical_metadata={},
            warnings=[],
            imported_at=created_at,
        )

    @staticmethod
    def _metadata_value(metadata, key):
        item = metadata.get(key)
        return item.get("value") if isinstance(item, Mapping) else None

    @staticmethod
    def _duration(started: float) -> int:
        return max(0, int((time.perf_counter() - started) * 1000))

    @classmethod
    def _empty(cls, started, code):
        return CSEMemorySearchResult(duration_ms=cls._duration(started), fallback_code=code)
