"""Required wording and safety policy for potential-rights reporting."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PotentialRightsPolicyRule:
    """One immutable non-decisional reporting rule."""

    rule_id: str
    description: str


POTENTIAL_RIGHTS_POLICY = (
    PotentialRightsPolicyRule("never_attribute_right", "Never state that the employee has an entitlement."),
    PotentialRightsPolicyRule("use_examination_wording", "Use: This scheme appears to warrant examination."),
    PotentialRightsPolicyRule("use_suggestive_wording", "Use: The available information suggests further review."),
    PotentialRightsPolicyRule("official_validation_visible", "State clearly when official validation remains necessary."),
    PotentialRightsPolicyRule("maturity_is_case_only", "Maturity qualifies only the documentary case, never the employee."),
    PotentialRightsPolicyRule("missing_is_not_disproof", "Missing evidence is not evidence that a right is absent."),
    PotentialRightsPolicyRule("conflicts_visible", "Contradictions remain visible and unresolved."),
    PotentialRightsPolicyRule("no_sensitive_output", "Reports exclude medical detail, secrets and local paths."),
)


FORBIDDEN_ASSERTIVE_PHRASES = ("you are entitled", "vous avez droit")
ALLOWED_PRUDENT_PHRASES = (
    "Ce dispositif semble devoir être examiné.",
    "Les informations disponibles suggèrent un examen complémentaire.",
    "Une validation officielle reste nécessaire.",
)
