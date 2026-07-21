"""Small composition component for identical connector orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from .career_import_models import ImportBatch
from .career_reconstruction_models import ReconstructionProposal, ReconstructionRequest
from .connector_contract import (
    ConnectorConversionResult,
    ConnectorConverter,
    ConnectorValidationResult,
    ConnectorValidator,
    ReconstructionCoordinator,
)


SourceT = TypeVar("SourceT")
ValidationT = TypeVar("ValidationT", bound=ConnectorValidationResult)
ConversionT = TypeVar("ConversionT", bound=ConnectorConversionResult)


@dataclass(frozen=True)
class ConnectorReconstructionSpec:
    """Technical identifiers and wording for a reconstruction request."""

    context_prefix: str
    request_prefix: str
    description: str


class ConnectorFoundation(Generic[SourceT, ValidationT, ConversionT]):
    """Compose validator, converter and reconstruction coordinator only."""

    def __init__(
        self,
        validator: ConnectorValidator[SourceT, ValidationT],
        converter: ConnectorConverter[SourceT, ConversionT],
        reconstruction: ReconstructionCoordinator,
    ) -> None:
        self._validator = validator
        self._converter = converter
        self._reconstruction = reconstruction

    def validate(self, source: SourceT) -> ValidationT:
        return self._validator.validate(source)

    def convert(self, source: SourceT) -> ConversionT:
        return self._converter.convert(source)

    def convert_validated(self, source: SourceT, error_message: str) -> ConversionT:
        if not self.validate(source).valid:
            raise ValueError(error_message)
        return self.convert(source)

    def prepare_reconstruction(
        self,
        source_id: str,
        batch: ImportBatch,
        spec: ConnectorReconstructionSpec,
    ) -> ReconstructionProposal:
        context = self._reconstruction.create_reconstruction_context(
            f"{spec.context_prefix}:{source_id}",
            ReconstructionRequest(
                f"{spec.request_prefix}:{source_id}",
                spec.description,
            ),
        )
        context = self._reconstruction.add_import_batch(context, batch)
        return self._reconstruction.build_reconstruction_proposal(context)


__all__ = ("ConnectorFoundation", "ConnectorReconstructionSpec")
