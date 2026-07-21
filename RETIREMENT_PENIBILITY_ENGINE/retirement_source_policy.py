"""Declarative hierarchy and authority limits for retirement sources."""

from dataclasses import dataclass
from enum import Enum


class SourceAuthority(str, Enum):
    """Primary characterization used by the future source resolver."""

    AUTHORITATIVE = "authoritative"
    SECONDARY = "secondary"
    CONTEXTUAL = "contextual"
    NEVER_SUFFICIENT_ALONE = "never_sufficient_alone"


@dataclass(frozen=True)
class RetirementSourcePolicy:
    """One ranked source and its non-exclusive authority characteristics."""

    priority: int
    source_id: str
    label: str
    authoritative: bool
    secondary: bool
    contextual: bool
    never_sufficient_alone: bool
    planned: bool = False
    aggregate_only: bool = False
    notes: str = ""


RETIREMENT_SOURCE_POLICY = (
    RetirementSourcePolicy(
        1,
        "carsat",
        "CARSAT",
        authoritative=True,
        secondary=False,
        contextual=True,
        never_sufficient_alone=True,
        notes="Central for work-health-retirement, AT/MP, incapacity and prevention; not a complete personal retirement record.",
    ),
    RetirementSourcePolicy(
        2,
        "assurance_retraite_cnav",
        "Assurance Retraite / CNAV",
        authoritative=True,
        secondary=False,
        contextual=False,
        never_sufficient_alone=False,
        planned=True,
        notes="Future source for official career and retirement administration; no connection exists in LOT 1.",
    ),
    RetirementSourcePolicy(
        3,
        "code_securite_sociale",
        "Code de la sécurité sociale",
        authoritative=True,
        secondary=False,
        contextual=False,
        never_sufficient_alone=True,
        notes="Authoritative rules do not prove an individual's administrative situation.",
    ),
    RetirementSourcePolicy(
        4,
        "code_travail",
        "Code du travail",
        authoritative=True,
        secondary=False,
        contextual=True,
        never_sufficient_alone=True,
        notes="Authoritative for work, exposure and employer obligations, not pension confirmation.",
    ),
    RetirementSourcePolicy(
        5,
        "c2p",
        "Compte professionnel de prévention C2P",
        authoritative=True,
        secondary=False,
        contextual=False,
        never_sufficient_alone=True,
        planned=True,
        notes="Declared points and administrative evidence must be confirmed by the competent service.",
    ),
    RetirementSourcePolicy(
        6,
        "ineos_agreements",
        "Accords INEOS",
        authoritative=False,
        secondary=True,
        contextual=True,
        never_sufficient_alone=True,
        notes="Applicable contractual end-of-career measures require scope and effective-date checks.",
    ),
    RetirementSourcePolicy(
        7,
        "inrs",
        "INRS",
        authoritative=False,
        secondary=True,
        contextual=True,
        never_sufficient_alone=True,
        notes="Prevention and occupational exposure guidance only.",
    ),
    RetirementSourcePolicy(
        8,
        "anact",
        "ANACT",
        authoritative=False,
        secondary=False,
        contextual=True,
        never_sufficient_alone=True,
        notes="Work organization, QVCT, transformations and social dialogue context.",
    ),
    RetirementSourcePolicy(
        9,
        "social_report",
        "Bilan social",
        authoritative=False,
        secondary=False,
        contextual=True,
        never_sufficient_alone=True,
        aggregate_only=True,
        notes="Collective aggregates only; never individual evidence.",
    ),
    RetirementSourcePolicy(
        10,
        "employee_supplied_data",
        "Données fournies par le salarié",
        authoritative=False,
        secondary=False,
        contextual=True,
        never_sufficient_alone=True,
        notes="Declared information until supported by verifiable evidence.",
    ),
)
