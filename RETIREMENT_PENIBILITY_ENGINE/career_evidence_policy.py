"""Declarative and non-judicial evidence rules for career reconstruction."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CareerEvidencePolicyRule:
    """One immutable prudential rule."""

    rule_id: str
    description: str


CAREER_EVIDENCE_POLICY = (
    CareerEvidencePolicyRule("employee_declaration_not_conclusive", "An employee declaration alone never definitively confirms an entitlement."),
    CareerEvidencePolicyRule("collective_rule_not_individual_fact", "An INEOS agreement states a collective rule but alone does not prove an individual situation."),
    CareerEvidencePolicyRule("payslip_corroborates", "A payslip may corroborate a work period, premium or schedule."),
    CareerEvidencePolicyRule("schedule_corroborates", "A schedule may corroborate a work organization."),
    CareerEvidencePolicyRule("official_notification_prevails", "An official notification is authoritative for an administrative right already recognized."),
    CareerEvidencePolicyRule("absence_is_not_disproof", "A missing document does not prove the absence of an entitlement."),
    CareerEvidencePolicyRule("history_is_traceable", "Expired and superseded references remain traceable."),
    CareerEvidencePolicyRule("contradictions_are_retained", "Contradictory evidence is never silently removed."),
    CareerEvidencePolicyRule("provenance_is_mandatory", "Every conclusion retains its complete provenance."),
    CareerEvidencePolicyRule("sensitive_output_is_minimal", "Sensitive data may be used but is never reproduced in full."),
    CareerEvidencePolicyRule("social_report_is_aggregate", "Aggregated social-report data cannot confirm an individual situation."),
    CareerEvidencePolicyRule("camera_plan_prohibited", "Camera plans and camera positions cannot be attached to an individual career."),
    CareerEvidencePolicyRule("corroboration_required", "A collective rule cannot become an individual fact without complementary evidence."),
)
