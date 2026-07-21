"""Immutable safeguards for future career imports."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CareerImportPolicyRule:
    """One architecture-level import safeguard."""

    rule_id: str
    description: str


CAREER_IMPORT_POLICY = (
    CareerImportPolicyRule("original_unchanged", "Original declared values remain unchanged."),
    CareerImportPolicyRule("normalization_separate", "Normalized projections remain separate from original data."),
    CareerImportPolicyRule("conflicts_retained", "Every conflict remains retained and visible."),
    CareerImportPolicyRule("provenance_required", "Every imported record retains complete provenance."),
    CareerImportPolicyRule("no_invention", "Missing values are never invented."),
    CareerImportPolicyRule("recency_not_reliability", "A more recent document is not assumed more reliable solely because of its date."),
    CareerImportPolicyRule("no_content", "Document content, PDF bytes and extracted full text are prohibited."),
)
