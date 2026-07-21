"""Resolution categories classify structures without selecting evidence."""

from dataclasses import replace
from datetime import datetime, timezone

from NEXUS_CORE import EntityId
from NEXUS_CORE.conflict_resolution import ResolutionCategory, ResolutionClassifier
from NEXUS_CORE.reasoning import (
    ConfidenceAssessment,
    ConflictExplanation,
    Corroboration,
    CorroborationStrength,
    FactCollection,
    MissingEvidence,
    MissingEvidenceReason,
    ReasoningConfidence,
    ReasoningConflict,
    ReasoningReport,
)
from NEXUS_CORE import ConfidenceLevel, ConfidenceScore, EntityReference
from NEXUS_CORE.reasoning import FactType


NOW = datetime(2026, 7, 21, 15, 0, tzinfo=timezone.utc)
SUBJECT = EntityReference(EntityId("subject-resolution"), "person")


def report():
    return ReasoningReport(
        EntityId("reasoning-resolution"),
        FactCollection(),
        (),
        (),
        (),
        (),
        ConfidenceAssessment(
            ReasoningConfidence.INSUFFICIENT,
            ConfidenceScore(0.0, ConfidenceLevel.UNKNOWN),
            0,
            0,
            0,
            0,
            (),
        ),
        (),
        (),
        NOW,
    )


def conflict(code, count=2):
    references = tuple(EntityId(f"fact-category-{index}") for index in range(count))
    return ReasoningConflict(
        EntityId(f"conflict-{code.lower()}-{count}"),
        references,
        ConflictExplanation(code, "structural_conflict", references),
        None,
    )


def categories(value):
    _, classifications = ResolutionClassifier().classify(value)
    return {item.category for item in classifications}


def test_every_resolution_category_has_a_structured_explanation():
    for category in ResolutionCategory:
        explanation = ResolutionClassifier.explanation_for(category)
        assert explanation
        assert explanation.replace("_", "").isalnum()


def test_document_temporal_source_and_unresolved_classification():
    base = report()
    assert ResolutionCategory.DOCUMENT_CONFLICT in categories(
        replace(base, conflicts=(conflict("FACT_VALUE_MISMATCH"),))
    )
    assert ResolutionCategory.TEMPORAL_CONFLICT in categories(
        replace(base, conflicts=(conflict("TEMPORAL_PERIOD_MISMATCH"),))
    )
    source_categories = categories(
        replace(base, conflicts=(conflict("SOURCE_PROVENANCE_MISMATCH"),))
    )
    assert ResolutionCategory.SOURCE_CONFLICT in source_categories
    assert ResolutionCategory.UNRESOLVED in source_categories


def test_missing_evidence_and_multiple_hypotheses_are_preserved():
    missing = MissingEvidence(
        EntityId("missing-resolution"),
        SUBJECT,
        FactType("employment_period"),
        MissingEvidenceReason.REQUIRED_FACT_ABSENT,
    )
    value = replace(
        report(),
        conflicts=(conflict("FACT_VALUE_MISMATCH", 3),),
        missing_evidence=(missing,),
    )
    actual = categories(value)
    assert ResolutionCategory.MISSING_EVIDENCE in actual
    assert ResolutionCategory.MULTIPLE_HYPOTHESES in actual


def test_partial_and_strong_corroboration_are_distinct():
    references = (EntityId("fact-a"), EntityId("fact-b"))
    partial = Corroboration(
        EntityId("corroboration-partial"),
        references,
        (EntityId("source-a"), EntityId("source-b")),
        CorroborationStrength.TWO_DISTINCT_SOURCES,
        None,
    )
    strong = replace(
        partial,
        corroboration_id=EntityId("corroboration-strong"),
        strength=CorroborationStrength.THREE_DISTINCT_SOURCES,
    )
    assert ResolutionCategory.PARTIAL_CORROBORATION in categories(
        replace(report(), corroborations=(partial,))
    )
    assert ResolutionCategory.STRONG_CORROBORATION in categories(
        replace(report(), corroborations=(strong,))
    )


def test_empty_report_is_insufficient_and_never_invents_a_hypothesis():
    actual = categories(report())
    assert actual == {
        ResolutionCategory.NO_CONFLICT,
        ResolutionCategory.INSUFFICIENT_EVIDENCE,
    }
