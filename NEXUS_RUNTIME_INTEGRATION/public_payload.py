"""Public Runtime response boundary.

Internal engines may use storage identifiers, source fingerprints and local
paths while building a response.  This module removes those implementation
details only when the completed payload crosses the user-facing HTTP boundary.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import re
from typing import Any


_DROP_KEYS = frozenset(
    {
        "_context",
        "cache_path",
        "cache_stale",
        "cache_stored_at",
        "candidate_rank",
        "chunk_id",
        "diagnostic",
        "diagnostics",
        "document_id",
        "employee_id",
        "engine_id",
        "engines",
        "evidence_id",
        "execution_id",
        "file_path",
        "finding_id",
        "fingerprint",
        "hash",
        "internal_id",
        "local_path",
        "metadata_record_id",
        "next_chunk_id",
        "normalized_id",
        "path",
        "plan_id",
        "previous_chunk_id",
        "ranking_reasons",
        "recommendation_id",
        "report_id",
        "request_id",
        "root_path",
        "selection_limits",
        "selection_reasons",
        "source_document_id",
        "source_path",
        "source_relative_path",
        "source_sha256",
        "storage_id",
        "technical_id",
        "technical_reference",
    }
)
_DROP_TOP_LEVEL = frozenset(
    {
        "cse_memory_runtime",
        "official_connectors_runtime",
        "protection_sociale_runtime",
        "retirement_runtime",
        "runtime_integration",
    }
)
_FLOW_LABELS = (
    ("apps/nexus-local-interface/server.py: analyze_question", "Interface Nexus"),
    ("automation/scripts/assistant_ds_router.py: ask --format json", "Routeur Nexus"),
    ("automation/experts/juriste_travail.py: enrich", "Juriste Travail"),
    ("automation/experts/paie.py: enrich", "Expert Paie"),
    (
        "automation/scripts/cdtn_connector.py: search_sources",
        "Code du travail numérique",
    ),
    ("automation/experts/orchestrator.py: orchestrate", "Orchestration experte"),
    ("automation/experts/report_generator.py: build_report", "Rapport Nexus"),
    ("NEXUS_CORE/orchestration: PipelineExecutor", "Nexus Core"),
    (
        "automation/orchestrator_common/orchestrator.py: CommonExpertOrchestrator",
        "Orchestrateur commun",
    ),
    ("NEXUS_RUNTIME_INTEGRATION/cse_memory_runtime.py", "Mémoire CSE"),
    ("NEXUS_RUNTIME_INTEGRATION/retirement_runtime.py", "Retraite et pénibilité"),
    (
        "NEXUS_RUNTIME_INTEGRATION/protection_sociale_runtime.py",
        "Protection sociale",
    ),
)
_ORIGIN_LABELS = {
    "bible_accords": "Accords INEOS",
    "cdtn_pratique_officielle": "Code du travail numérique",
    "judilibre_jurisprudence": "JUDILIBRE",
    "legifrance_code_travail": "Légifrance",
    "nexus_bible_bridge": "Accords INEOS",
    "pratique_officielle": "Code du travail numérique",
}
_SECTION_LABELS = {
    "core_v3_runtime": "analyse_transversale",
    "cse_memory_runtime": "memoire_cse",
    "protection_sociale_runtime": "protection_sociale",
    "retirement_runtime": "retraite_penibilite",
}
_WINDOWS_PATH = re.compile(
    r"(?i)(?<![a-z0-9])(?:file:/+)?[a-z]:[\\/][^|;\r\n)\]]+"
    r"(?=\s+\||[;\r\n)\]]|$)"
)
_POSIX_LOCAL_PATH = re.compile(
    r"(?i)/(?:tmp|home|users)(?:/[^|;\s\r\n)\]]+)+"
)
_UUID = re.compile(
    r"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}\b"
)
_LONG_HASH = re.compile(r"(?i)\b[0-9a-f]{32,128}\b")
_RUNTIME_IDENTIFIER = re.compile(r"(?i)\bruntime-[a-z0-9_-]{8,}\b")
_TECHNICAL_REFERENCE = re.compile(
    r"(?i)\b(?:chunk(?:_id)?|storage_id|internal_id|uuid|hash)"
    r"\s*(?:[:=]\s*|\s+)[a-z0-9_.:-]+"
)
_INTERNAL_CORPUS = re.compile(
    r"(?i)\b(?:CCSEMEMORYENGINE|PROTECTION_SOCIALE_ENGINE|LOT_1D)\b"
)
_REDACTED_REFERENCE = "référence interne non publiée"


def sanitize_public_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return a user-safe copy without mutating the internal Runtime payload."""

    if not isinstance(payload, Mapping):
        raise TypeError("public Runtime payload must be a mapping")
    return _sanitize_mapping(payload, top_level=True)


def _sanitize_mapping(value: Mapping[str, Any], *, top_level: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for raw_key, item in value.items():
        key = str(raw_key)
        normalized = key.lower()
        if normalized in _DROP_KEYS or (top_level and normalized in _DROP_TOP_LEVEL):
            continue
        if normalized.endswith(("_sha256", "_storage_id", "_internal_id")):
            continue
        if normalized == "generated_from":
            result[key] = _public_flow(item)
            continue
        if normalized == "origin" and isinstance(item, str):
            result[key] = _ORIGIN_LABELS.get(item, _sanitize_text(item))
            continue
        if normalized == "id" and isinstance(item, str):
            result[key] = _SECTION_LABELS.get(item, _sanitize_text(item))
            continue
        result[key] = _sanitize_value(item)
    return result


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _sanitize_mapping(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, str):
        return _sanitize_text(value)
    return value


def _public_flow(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    labels: list[str] = []
    for item in value:
        text = str(item)
        label = next((public for internal, public in _FLOW_LABELS if internal in text), None)
        if label and label not in labels:
            labels.append(label)
    return labels


def _sanitize_text(value: str) -> str:
    text = value
    for internal, public in _FLOW_LABELS:
        text = text.replace(internal, public)
    for internal, public in _ORIGIN_LABELS.items():
        text = text.replace(internal, public)
    text = _INTERNAL_CORPUS.sub("corpus local", text)
    text = _WINDOWS_PATH.sub(_REDACTED_REFERENCE, text)
    text = _POSIX_LOCAL_PATH.sub(_REDACTED_REFERENCE, text)
    text = _UUID.sub(_REDACTED_REFERENCE, text)
    text = _LONG_HASH.sub(_REDACTED_REFERENCE, text)
    text = _RUNTIME_IDENTIFIER.sub(_REDACTED_REFERENCE, text)
    text = _TECHNICAL_REFERENCE.sub(_REDACTED_REFERENCE, text)
    text = re.sub(r"\s+\|\s+\|", " | ", text)
    return text.strip()
