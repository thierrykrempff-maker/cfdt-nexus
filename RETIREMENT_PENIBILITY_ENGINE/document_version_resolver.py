"""Temporal resolution over explicitly supplied document-version metadata."""

from __future__ import annotations

from datetime import date

from .document_knowledge_models import DocumentTimeline, DocumentValidity, DocumentVersion


class DocumentVersionResolver:
    """Resolve a declared version for a date without accessing its document."""

    def resolve(self, timeline: DocumentTimeline, applicable_on: str) -> DocumentVersion | None:
        target = date.fromisoformat(applicable_on)
        candidates = tuple(
            version
            for version in timeline.versions
            if version.validity is not DocumentValidity.REPEALED
            and self._contains(version, target)
        )
        if not candidates:
            return None
        return max(candidates, key=self._sort_key)

    @staticmethod
    def _contains(version: DocumentVersion, target: date) -> bool:
        start = date.fromisoformat(version.period.valid_from) if version.period.valid_from else date.min
        end = date.fromisoformat(version.period.valid_to) if version.period.valid_to else date.max
        if end < start:
            raise ValueError(f"Invalid period for version: {version.version_id}")
        return start <= target <= end

    @staticmethod
    def _sort_key(version: DocumentVersion) -> tuple[str, str]:
        return (version.period.valid_from or "", version.version_id)
