"""Bounded metadata-only lookup over existing Protection Sociale LOT 1D chunks."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json
from pathlib import Path
import re
import time
import unicodedata
from typing import Any

from automation.protection_sociale.chunk_models import Chunk

from .config import RuntimeProtectionSocialeConfig


_STOP_WORDS = frozenset({
    "avec", "avoir", "comment", "dans", "des", "est", "les", "mes", "mon",
    "pour", "quelle", "quelles", "quel", "quels", "une", "sur", "dois",
    "notice", "tableau", "garantie", "garanties",
})
_GENERIC_TERMS = frozenset({
    "protection", "sociale", "mutuelle", "prevoyance", "sante", "regime",
})


def normalize(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return " ".join(re.findall(r"[a-z0-9]+", text.encode("ascii", "ignore").decode().lower()))


@dataclass(frozen=True, slots=True)
class ProtectionSocialeMetadataDocument:
    """Confidential-source identity plus a bounded, non-content metadata projection."""

    document_id: str
    document_type: str
    domain: str
    topic: str
    source_sha256: str


@dataclass(frozen=True, slots=True)
class ProtectionSocialeSearchResult:
    documents: tuple[ProtectionSocialeMetadataDocument, ...] = ()
    document_count: int = 0
    chunk_count: int = 0
    duration_ms: int = 0
    fallback_code: str | None = None


class RuntimeProtectionSocialeGateway:
    """Read existing chunks without writing, indexing or returning their text."""

    def __init__(self, config: RuntimeProtectionSocialeConfig) -> None:
        self._config = config

    def search(self, answer: Mapping[str, Any]) -> ProtectionSocialeSearchResult:
        started = time.perf_counter()
        root = self._config.processed_root
        chunk_root = root / "chunks" if root is not None else None
        if chunk_root is None or not chunk_root.is_dir():
            return self._empty(started, "PROTECTION_SOCIALE_UNAVAILABLE")
        tokens = self._tokens(answer.get("query"))
        if not tokens:
            return self._empty(started, "PROTECTION_SOCIALE_NO_RESULT")
        candidates = []
        for path in sorted(chunk_root.glob("*.jsonl"), key=lambda item: item.name):
            if not path.is_file() or path.is_symlink():
                continue
            with path.open("r", encoding="utf-8") as stream:
                for line in stream:
                    if not line.strip():
                        continue
                    raw = json.loads(line)
                    if not isinstance(raw, Mapping) or not raw.get("is_indexable"):
                        continue
                    chunk = Chunk(**dict(raw))
                    score = self._score(tokens, chunk.metadata_snapshot)
                    if score:
                        candidates.append((score, chunk.document_id, chunk.chunk_index, chunk))
        candidates.sort(key=lambda row: (-row[0], row[1], row[2]))
        selected = candidates[: self._config.max_chunks]
        if not selected:
            return self._empty(started, "PROTECTION_SOCIALE_NO_RESULT")
        by_document: dict[str, list[Chunk]] = {}
        for _, document_id, _, chunk in selected:
            if document_id and (
                document_id in by_document or len(by_document) < self._config.max_documents
            ):
                by_document.setdefault(document_id, []).append(chunk)
        documents = tuple(
            self._document(document_id, chunks)
            for document_id, chunks in sorted(by_document.items())
        )
        return ProtectionSocialeSearchResult(
            documents,
            len(documents),
            sum(len(chunks) for chunks in by_document.values()),
            self._duration(started),
        )

    @staticmethod
    def _tokens(query: object) -> tuple[str, ...]:
        tokens = tuple(
            token for token in dict.fromkeys(normalize(query).split())
            if len(token) >= 3 and token not in _STOP_WORDS
        )
        specific = tuple(token for token in tokens if token not in _GENERIC_TERMS)
        return specific or tokens

    @staticmethod
    def _score(tokens: Sequence[str], metadata: Mapping[str, Any]) -> int:
        values = " ".join(
            str(value.get("value") or "")
            for value in metadata.values()
            if isinstance(value, Mapping)
        )
        words = set(normalize(values).split())
        return sum(1 for token in tokens if token in words)

    @classmethod
    def _document(cls, document_id: str, chunks: list[Chunk]):
        first = chunks[0]
        metadata = first.metadata_snapshot
        document_type = cls._value(metadata, "type_document") or "other"
        domain = cls._value(metadata, "domaine_principal") or "protection_sociale"
        topic = cls._value(metadata, "sous_domaine") or cls._value(
            metadata, "thème_principal"
        ) or "information"
        return ProtectionSocialeMetadataDocument(
            document_id,
            normalize(document_type).replace(" ", "_") or "other",
            normalize(domain).replace(" ", "_") or "protection_sociale",
            normalize(topic).replace(" ", "_") or "information",
            first.source_sha256,
        )

    @staticmethod
    def _value(metadata: Mapping[str, Any], key: str):
        item = metadata.get(key)
        return item.get("value") if isinstance(item, Mapping) else None

    @staticmethod
    def _duration(started: float) -> int:
        return max(0, round((time.perf_counter() - started) * 1000))

    @classmethod
    def _empty(cls, started: float, code: str) -> ProtectionSocialeSearchResult:
        return ProtectionSocialeSearchResult(
            duration_ms=cls._duration(started), fallback_code=code
        )
