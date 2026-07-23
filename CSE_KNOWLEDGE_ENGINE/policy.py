"""Deterministic metadata policy for the CSE Knowledge Engine."""

from __future__ import annotations

import re
import unicodedata

from DOCUMENT_INTELLIGENCE_CENTER import NavigationDocument
from DOCUMENT_INTELLIGENCE_CENTER.ingestion_models import validate_safe_metadata


DECISION_NATURE = "DECISION"
MANAGEMENT_COMMITMENT_NATURE = "MANAGEMENT_COMMITMENT"
CONSULTATION_NATURE = "CONSULTATION"
OPEN_STATUSES = frozenset({"ACTIVE", "OPEN", "PENDING", "UNKNOWN"})

_TOKEN_SEPARATOR = re.compile(r"[^a-z0-9]+")


def normalize_label(value: str) -> str:
    """Normalize safe metadata for exact lexical matching."""

    validate_safe_metadata(value, "label")
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    ascii_value = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )
    return " ".join(_TOKEN_SEPARATOR.sub(" ", ascii_value).split())


def matches_subject(document: NavigationDocument, subject: str) -> bool:
    """Match a subject only against the safe public metadata projection."""

    normalized_subject = normalize_label(subject)
    if not normalized_subject:
        return False
    candidates = (
        document.title,
        document.family or "",
        document.nature or "",
    )
    return any(
        normalized_subject in normalize_label(candidate)
        for candidate in candidates
        if candidate
    )


def subject_labels(document: NavigationDocument) -> tuple[str, ...]:
    """Return controlled labels usable for recurrence analysis."""

    labels = {
        value.strip()
        for value in (document.family,)
        if value is not None and value.strip()
    }
    return tuple(sorted(labels, key=lambda value: (normalize_label(value), value)))
