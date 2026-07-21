"""Provenance construction and verification for injected import metadata."""

from .career_import_models import ImportProvenance, ImportSource


class ImportProvenanceManager:
    """Create complete provenance and reject missing mandatory metadata."""

    @staticmethod
    def from_source(source: ImportSource) -> ImportProvenance:
        values = (
            source.source_id,
            source.internal_document_id,
            source.imported_at,
            source.version,
            source.origin,
        )
        if any(not value for value in values):
            raise ValueError("Complete import provenance is required.")
        return ImportProvenance(
            source.source_id,
            source.document_type,
            source.internal_document_id,
            source.imported_at,
            source.version,
            source.origin,
            source.confidence,
        )
