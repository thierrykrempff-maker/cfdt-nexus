"""Non-judicial policy governing document selection and temporal use."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentKnowledgePolicyRule:
    """One immutable documentary safeguard."""

    rule_id: str
    description: str


DOCUMENT_KNOWLEDGE_POLICY = (
    DocumentKnowledgePolicyRule("agreement_not_individual_evidence", "An agreement never proves an individual situation by itself."),
    DocumentKnowledgePolicyRule("collective_agreement_defines_rule", "A collective agreement defines a rule, not an individual fact."),
    DocumentKnowledgePolicyRule("individual_evidence_required", "Complementary individual evidence remains necessary."),
    DocumentKnowledgePolicyRule("temporal_version_required", "The document version applicable to the relevant date must be respected."),
    DocumentKnowledgePolicyRule("repealed_rule_forbidden", "A repealed rule must not be selected as applicable."),
    DocumentKnowledgePolicyRule("provenance_required", "Every selected document, passage and rule retains provenance."),
)


DOCUMENT_SOURCE_IDS = (
    "INEOS_AGREEMENTS_BIBLE",
    "CHEMICAL_INDUSTRY_COLLECTIVE_AGREEMENT",
    "CARSAT",
    "INRS",
    "ANACT",
    "CNIL",
    "CSE_MEMORY",
    "SOCIAL_PROTECTION",
)
"""Future providers may reuse these sources without duplicating their corpora."""
