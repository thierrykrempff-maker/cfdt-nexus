"""Architecture-only public entry point for Retirement & Penibility."""

from __future__ import annotations

from .retirement_contract import RETIREMENT_FOUNDATION_CONTRACT, RetirementRequest, RetirementResponse
from .retirement_evidence_matrix import EVIDENCE_MATRIX, EVIDENCE_WEIGHTING_RULES
from .retirement_reasoning_protocol import REASONING_PROTOCOL
from .retirement_source_policy import RETIREMENT_SOURCE_POLICY


class RetirementArchitectureOnlyError(RuntimeError):
    """Raised whenever business execution is requested before a future lot."""


class RetirementPlatform:
    """Public facade exposing declarations while refusing all business execution."""

    domain_id = RETIREMENT_FOUNDATION_CONTRACT.domain_id
    status = RETIREMENT_FOUNDATION_CONTRACT.status
    enabled = RETIREMENT_FOUNDATION_CONTRACT.enabled

    def describe(self):
        """Return the immutable foundation safety contract."""

        return RETIREMENT_FOUNDATION_CONTRACT

    def source_policy(self):
        """Return the ordered declarative source policy."""

        return RETIREMENT_SOURCE_POLICY

    def reasoning_protocol(self):
        """Return the fifteen architecture-only reasoning instructions."""

        return REASONING_PROTOCOL

    def evidence_matrix(self):
        """Return the evidence declarations and their prudential rules."""

        return EVIDENCE_MATRIX, EVIDENCE_WEIGHTING_RULES

    def assess(self, _request: RetirementRequest) -> RetirementResponse:
        """Refuse execution because no retirement engine exists in LOT 1."""

        raise RetirementArchitectureOnlyError("RETIREMENT_PENIBILITY_ENGINE_ARCHITECTURE_ONLY")
