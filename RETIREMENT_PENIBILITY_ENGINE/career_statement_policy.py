"""Privacy and prudence rules for the Career Statement Connector."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CareerStatementPolicyRule:
    rule_id: str
    description: str


CAREER_STATEMENT_POLICY = (
    CareerStatementPolicyRule("immutable_originals", "Original declared values remain immutable."),
    CareerStatementPolicyRule("provenance_required", "Every converted record requires explicit provenance."),
    CareerStatementPolicyRule("confidence_required", "A declared confidence level is mandatory."),
    CareerStatementPolicyRule("no_invention", "No missing value may be invented."),
    CareerStatementPolicyRule("no_auto_correction", "No value is corrected automatically."),
    CareerStatementPolicyRule("no_merge", "Periods and employers are never merged automatically."),
    CareerStatementPolicyRule("no_delete", "Duplicates and conflicts are retained for review."),
    CareerStatementPolicyRule("no_retirement_calculation", "No retirement date, entitlement or amount is calculated."),
    CareerStatementPolicyRule("no_decision", "The connector never makes an administrative or legal decision."),
    CareerStatementPolicyRule("no_personal_identity", "Names, addresses and social-security numbers are prohibited."),
    CareerStatementPolicyRule("no_medical_data", "Medical data is prohibited."),
    CareerStatementPolicyRule("no_real_document", "Real statements and document content are prohibited."),
    CareerStatementPolicyRule("human_review", "All prepared data remains subject to human review."),
)
