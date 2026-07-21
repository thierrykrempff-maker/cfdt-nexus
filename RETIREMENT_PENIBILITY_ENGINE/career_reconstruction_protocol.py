"""Declarative protocol for cautious career reconstruction."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CareerReconstructionProtocolStep:
    ordinal: int
    step_id: str
    description: str


CAREER_RECONSTRUCTION_PROTOCOL = (
    CareerReconstructionProtocolStep(1, "receive_batches", "Receive validated synthetic import batches."),
    CareerReconstructionProtocolStep(2, "verify_validation", "Verify import validation references."),
    CareerReconstructionProtocolStep(3, "preserve_originals", "Preserve every original record unchanged."),
    CareerReconstructionProtocolStep(4, "group_records", "Group comparable structured record types."),
    CareerReconstructionProtocolStep(5, "normalize_references", "Reuse separate normalized references."),
    CareerReconstructionProtocolStep(6, "build_candidates", "Generate deterministic record pairs."),
    CareerReconstructionProtocolStep(7, "compare_periods", "Compare declared periods and precision."),
    CareerReconstructionProtocolStep(8, "compare_employers", "Compare declared employers."),
    CareerReconstructionProtocolStep(9, "compare_positions", "Compare positions, classifications and coefficients."),
    CareerReconstructionProtocolStep(10, "compare_schedules", "Compare declared schedules."),
    CareerReconstructionProtocolStep(11, "find_corroboration", "Identify distinct corroborating sources."),
    CareerReconstructionProtocolStep(12, "detect_duplicates", "Detect possible duplicates without deleting them."),
    CareerReconstructionProtocolStep(13, "detect_contradictions", "Retain all contradictions and alternatives."),
    CareerReconstructionProtocolStep(14, "detect_gaps", "Report gaps without inferring absent activity."),
    CareerReconstructionProtocolStep(15, "merge_compatible", "Merge only compatible structured metadata."),
    CareerReconstructionProtocolStep(16, "prepare_timeline", "Prepare a distinct timeline proposal."),
    CareerReconstructionProtocolStep(17, "prepare_evidence", "Prepare unverified evidence proposals."),
    CareerReconstructionProtocolStep(18, "request_human_validation", "Request every necessary human decision."),
    CareerReconstructionProtocolStep(19, "employee_view", "Produce a non-technical employee view."),
    CareerReconstructionProtocolStep(20, "expert_view", "Produce a sourced expert view without secrets."),
)
