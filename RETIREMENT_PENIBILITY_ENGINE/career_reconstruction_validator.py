"""Validation of reconstruction proposals before mandatory human review."""

from .career_evidence_models import EvidenceStatus
from .career_reconstruction_models import ReconstructionProposal, ReconstructionStatus


class CareerReconstructionValidator:
    """Reject automatic validation, lost provenance and verified proposals."""

    def validate(self, proposal: ReconstructionProposal) -> tuple[str, ...]:
        issues: list[str] = []
        if proposal.status is ReconstructionStatus.VALIDATED:
            issues.append("VALIDATED is reserved for a future explicit human action.")
        if not proposal.validation_requirement or proposal.validation_requirement.completed:
            issues.append("Pending human validation is mandatory.")
        if any(not record.provenance for record in proposal.records):
            issues.append("Every reconstruction record requires provenance.")
        if any(item.status is EvidenceStatus.VERIFIED for item in proposal.proposed_evidence.evidence):
            issues.append("Proposed evidence must never be automatically VERIFIED.")
        return tuple(issues)
