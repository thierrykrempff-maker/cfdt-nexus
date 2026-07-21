"""Neutral protocols for the shared retirement connector foundation."""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from .career_import_models import ImportBatch
from .career_reconstruction_models import (
    ReconstructionContext,
    ReconstructionProposal,
    ReconstructionRequest,
)


SourceT = TypeVar("SourceT")
ValidationT = TypeVar("ValidationT", bound="ConnectorValidationResult")
ConversionT = TypeVar("ConversionT", bound="ConnectorConversionResult")
PreparedT = TypeVar("PreparedT", covariant=True)
ViewT = TypeVar("ViewT", contravariant=True)
ReportT = TypeVar("ReportT", covariant=True)


class ConnectorValidationResult(Protocol):
    """Minimum structural result required by technical orchestration."""

    @property
    def valid(self) -> bool: ...


class ConnectorConversionResult(Protocol):
    """Minimum structural conversion result used by the foundation."""

    @property
    def import_batch(self) -> ImportBatch: ...


class ConnectorValidator(Protocol[SourceT, ValidationT]):
    """Validate one injected source without acquiring data."""

    def validate(self, source: SourceT) -> ValidationT: ...


class ConnectorConverter(Protocol[SourceT, ConversionT]):
    """Convert one validated source to a typed result containing ImportBatch."""

    def convert(self, source: SourceT) -> ConversionT: ...


class ReconstructionCoordinator(Protocol):
    """Subset of reconstruction operations used by all five connectors."""

    def create_reconstruction_context(
        self,
        context_id: str,
        request: ReconstructionRequest,
        existing_timeline=None,
        existing_evidence=None,
    ) -> ReconstructionContext: ...

    def add_import_batch(
        self, context: ReconstructionContext, batch: ImportBatch
    ) -> ReconstructionContext: ...

    def build_reconstruction_proposal(
        self, context: ReconstructionContext
    ) -> ReconstructionProposal: ...


@runtime_checkable
class RetirementSourceConnector(Protocol[SourceT, PreparedT, ViewT, ReportT]):
    """Small common public core; source-specific methods remain untouched."""

    def convert_to_import_batch(self, source: SourceT) -> ImportBatch: ...

    def prepare_reconstruction(self, source: SourceT) -> PreparedT: ...

    def generate_import_report(self, source: SourceT, view: ViewT) -> ReportT: ...


__all__ = (
    "ConnectorConversionResult",
    "ConnectorConverter",
    "ConnectorValidationResult",
    "ConnectorValidator",
    "ReconstructionCoordinator",
    "RetirementSourceConnector",
)
