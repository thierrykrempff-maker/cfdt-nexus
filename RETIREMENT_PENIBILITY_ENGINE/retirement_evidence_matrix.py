"""Declarative A-D evidence matrix for future retirement reasoning."""

from dataclasses import dataclass

from .retirement_models import EvidenceGrade


@dataclass(frozen=True)
class EvidenceRequirement:
    """Document type, documentary grade and non-computational weight metadata."""

    document_type: str
    grade: EvidenceGrade
    weight: float
    authoritative: bool
    individual_case_capable: bool
    notes: str


EVIDENCE_MATRIX = (
    EvidenceRequirement("official_career_statement", EvidenceGrade.A, 1.0, True, True, "Official career statement."),
    EvidenceRequirement("carsat_notification", EvidenceGrade.A, 1.0, True, True, "Official CARSAT notification within its competence."),
    EvidenceRequirement("assurance_retraite_notification", EvidenceGrade.A, 1.0, True, True, "Official Assurance Retraite notification."),
    EvidenceRequirement("payslip", EvidenceGrade.B, 0.65, False, True, "Supports employment and payroll periods but is not an entitlement decision."),
    EvidenceRequirement("employment_contract", EvidenceGrade.B, 0.65, False, True, "Supports employment conditions and dates."),
    EvidenceRequirement("employment_amendment", EvidenceGrade.B, 0.65, False, True, "Supports a documented contractual change."),
    EvidenceRequirement("employer_attestation", EvidenceGrade.C, 0.4, False, True, "Requires consistency checks against stronger evidence."),
    EvidenceRequirement("collective_agreement", EvidenceGrade.C, 0.4, False, False, "Establishes a collective rule, not an individual administrative situation."),
    EvidenceRequirement("employee_declaration", EvidenceGrade.D, 0.15, False, True, "Declared information only until corroborated."),
)


EVIDENCE_WEIGHTING_RULES = (
    "Weights express documentary strength only and must never be added to calculate entitlement.",
    "Several grade D declarations never become grade A evidence by accumulation.",
    "An applicable verified grade A item prevails over a contradictory lower-grade item.",
    "An expired, out-of-scope or unverified item cannot raise the output level.",
    "A collective agreement proves a rule but not an individual career fact.",
    "Employee-supplied information remains declared until supported by verifiable evidence.",
    "Missing indispensable official evidence blocks a confirmed conclusion.",
    "Every weighting decision must preserve source, version, scope and effective date.",
)
