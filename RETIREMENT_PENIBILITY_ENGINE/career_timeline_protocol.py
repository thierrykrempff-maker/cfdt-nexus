"""Declarative protocol for assembling a career timeline without calculation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CareerTimelineProtocolStep:
    """One ordered, non-executable timeline preparation instruction."""

    ordinal: int
    step_id: str
    description: str


CAREER_TIMELINE_PROTOCOL = (
    CareerTimelineProtocolStep(1, "collect", "Collect explicitly supplied career metadata and evidence references."),
    CareerTimelineProtocolStep(2, "normalize", "Normalize structural fields without inferring missing facts."),
    CareerTimelineProtocolStep(3, "order", "Order dated events deterministically while preserving their sources."),
    CareerTimelineProtocolStep(4, "merge", "Merge source inventories without silently removing contradictions."),
    CareerTimelineProtocolStep(5, "detect_conflicts", "Identify incompatible declarations and retain every version."),
    CareerTimelineProtocolStep(6, "detect_gaps", "Identify unexplained zones without reconstructing them."),
    CareerTimelineProtocolStep(7, "evaluate_evidence", "Associate declared evidence levels without legal conclusion."),
    CareerTimelineProtocolStep(8, "qualify_confidence", "Qualify confidence prudentially without a numeric calculation."),
    CareerTimelineProtocolStep(9, "generate_report", "Generate a structural report containing no retirement estimate."),
)
