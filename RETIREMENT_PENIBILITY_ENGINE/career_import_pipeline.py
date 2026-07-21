"""Mandatory Career Import gateway for every reconstruction request.

The gateway performs structural validation and provenance checks before it
hands an immutable ``ImportBatch`` to the Career Reconstruction Engine.  It
does not read documents and it does not perform any network or business work.
"""

from __future__ import annotations

from dataclasses import replace

from .career_import_engine import CareerImportEngine
from .career_import_models import ImportBatch, ImportStatus
from .career_reconstruction_engine import CareerReconstructionEngine
from .career_reconstruction_models import (
    ReconstructionContext,
    ReconstructionProposal,
    ReconstructionRequest,
)
from .privacy_gate import RetirementPrivacyGate, require_privacy_gate


CAREER_IMPORT_PIPELINE_STAGES = (
    "CONNECTOR",
    "CAREER_IMPORT",
    "CAREER_RECONSTRUCTION",
    "TIMELINE",
    "EVIDENCE",
    "POTENTIAL_RIGHTS",
)


class CareerImportPipeline:
    """Validate connector metadata before delegating reconstruction."""

    def __init__(
        self,
        import_engine=None,
        reconstruction_engine=None,
        privacy_gate=RetirementPrivacyGate(),
    ) -> None:
        self._import = import_engine or CareerImportEngine()
        self._reconstruction = reconstruction_engine or CareerReconstructionEngine()
        self._privacy_gate = privacy_gate

    def create_reconstruction_context(
        self,
        context_id: str,
        request: ReconstructionRequest,
        existing_timeline=None,
        existing_evidence=None,
    ) -> ReconstructionContext:
        return self._reconstruction.create_reconstruction_context(
            context_id,
            request,
            existing_timeline,
            existing_evidence,
        )

    def add_import_batch(
        self, context: ReconstructionContext, batch: ImportBatch
    ) -> ReconstructionContext:
        validated = self.validate_for_reconstruction(batch)
        return self._reconstruction.add_import_batch(context, validated)

    def build_reconstruction_proposal(
        self, context: ReconstructionContext
    ) -> ReconstructionProposal:
        return self._reconstruction.build_reconstruction_proposal(context)

    def validate_for_reconstruction(self, batch: ImportBatch) -> ImportBatch:
        """Return a validated immutable batch or fail closed."""

        if type(batch) is not ImportBatch:
            raise TypeError("Career reconstruction accepts ImportBatch only.")
        require_privacy_gate(self._privacy_gate).assert_safe(batch)
        if not batch.synthetic_only:
            raise ValueError("Career reconstruction accepts synthetic metadata only.")
        self._require_provenance(batch)
        validation = self._import.validate_batch(batch)
        if not validation.valid:
            raise ValueError("ImportBatch must pass Career Import validation.")
        return replace(batch, status=ImportStatus.VALIDATED)

    @staticmethod
    def _require_provenance(batch: ImportBatch) -> None:
        for document in batch.documents:
            source = document.source
            if not all(
                (
                    source.source_id,
                    source.internal_document_id,
                    source.imported_at,
                    source.version,
                    source.origin,
                )
            ):
                raise ValueError("Every imported document requires provenance.")
        for record in batch.records:
            provenance = getattr(record, "provenance", None)
            if provenance is None or not all(
                (
                    provenance.source_id,
                    provenance.internal_document_id,
                    provenance.imported_at,
                    provenance.version,
                    provenance.origin,
                )
            ):
                raise ValueError("Every imported record requires provenance.")


__all__ = ("CAREER_IMPORT_PIPELINE_STAGES", "CareerImportPipeline")
