"""Mandatory safeguards for human-validated career reconstruction."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CareerReconstructionPolicyRule:
    rule_id: str
    description: str


CAREER_RECONSTRUCTION_POLICY = (
    CareerReconstructionPolicyRule("proposal_only", "Every reconstruction remains a proposal."),
    CareerReconstructionPolicyRule("human_validation", "Human validation is mandatory before integration."),
    CareerReconstructionPolicyRule("original_immutable", "Original imported records remain immutable."),
    CareerReconstructionPolicyRule("normalized_distinct", "Normalized values remain distinct from originals."),
    CareerReconstructionPolicyRule("contradictions_retained", "Contradictions and alternatives are retained."),
    CareerReconstructionPolicyRule("provenance_required", "Complete provenance is mandatory."),
    CareerReconstructionPolicyRule("official_not_exclusive", "Official sources may confirm administrative information but do not erase other sources."),
    CareerReconstructionPolicyRule("payslip_corroborates", "A payslip may corroborate activity but not the entire work organization."),
    CareerReconstructionPolicyRule("collective_not_individual", "A collective agreement does not prove an individual situation."),
    CareerReconstructionPolicyRule("declaration_remains_declarative", "An employee declaration remains declarative."),
    CareerReconstructionPolicyRule("approximate_remains_approximate", "An approximate date is never converted into an exact date."),
    CareerReconstructionPolicyRule("medical_details_hidden", "Detailed medical data is never reproduced."),
    CareerReconstructionPolicyRule("aggregate_not_individual", "Aggregated data is never individualized."),
    CareerReconstructionPolicyRule("security_data_prohibited", "Camera plans and site-security data are prohibited."),
    CareerReconstructionPolicyRule("missing_not_absence", "A missing document is not evidence of absent activity or entitlement."),
    CareerReconstructionPolicyRule("recency_not_truth", "Recency alone never establishes accuracy."),
)
