from datetime import datetime, timezone

from RETIREMENT_PENIBILITY_ENGINE.career_evidence_models import (
    CareerEvidenceItem, EvidenceAuthorityLevel, EvidenceBundle, EvidenceConfidenceLevel,
    EvidenceReference, EvidenceSourceType, EvidenceStatus,
)
from RETIREMENT_PENIBILITY_ENGINE.career_import_models import ImportConfidence, ImportDocumentType, ImportProvenance
from RETIREMENT_PENIBILITY_ENGINE.career_reconstruction_models import (
    DatePrecision, HumanValidationRequirement, ReconstructedCareerPeriod,
    ReconstructionConflict, ReconstructionConflictType, ReconstructionDate,
    ReconstructionProposal, ReconstructionStatus,
)
from NEXUS_ADAPTERS.retirement import RetirementCareerMapper, RetirementConflictMapper, RetirementEvidenceMapper
from NEXUS_CORE import DocumentType, EntityId, EntityReference
from NEXUS_CORE.conflict_resolution import ResolutionCategory


NOW = datetime(2026, 1, 2, tzinfo=timezone.utc)
SUBJECT = EntityReference(EntityId("synthetic-subject"), "person")


def _provenance(source="synthetic-contract"):
    return ImportProvenance(
        source, ImportDocumentType.EMPLOYMENT_CONTRACT, "synthetic-document",
        "2026-01-01", "1.0", "synthetic_fixture", ImportConfidence.HIGH,
    )


def _proposal(*, conflict=False):
    period = ReconstructedCareerPeriod(
        "period-one", "synthetic-employer",
        ReconstructionDate("2020-01-01", DatePrecision.EXACT),
        ReconstructionDate("2020-12-31", DatePrecision.EXACT),
        (_provenance(),),
    )
    conflicts = (ReconstructionConflict(
        "conflict-one", ReconstructionConflictType.DATE_CONFLICT,
        ("record-one", "record-two"), (), (_provenance(),), "synthetic conflict",
    ),) if conflict else ()
    return ReconstructionProposal(
        "proposal-one", ReconstructionStatus.PROPOSED, (), (), (), (), (period,),
        EvidenceBundle("bundle-empty"), conflicts, (), (),
        HumanValidationRequirement("validation-one", "synthetic review", ()),
    )


def _bundle():
    reference = EvidenceReference(
        "retirement-evidence-one", EvidenceSourceType.EMPLOYMENT_CONTRACT,
        "synthetic title", "synthetic-reference", "synthetic-provenance",
    )
    item = CareerEvidenceItem(
        reference, EvidenceAuthorityLevel.CONTRACTUAL,
        EvidenceConfidenceLevel.HIGH, EvidenceStatus.VERIFIED,
        valid_from="2020-01-01", valid_to="2020-12-31",
    )
    return EvidenceBundle("bundle-one", evidence=(item,))


def test_evidence_mapping_preserves_provenance_period_confidence_and_document_type():
    evidence = RetirementEvidenceMapper().map_bundle(_bundle(), SUBJECT, NOW)[0]
    assert evidence.period.start_date.isoformat() == "2020-01-01"
    assert evidence.confidence.value == 0.85
    assert evidence.document_reference.document_type is DocumentType.EMPLOYMENT_CONTRACT
    assert evidence.provenance.trace_reference is not None


def test_career_reconstruction_maps_to_core_employment_period_deterministically():
    mapper = RetirementCareerMapper()
    first = mapper.map(_proposal(), SUBJECT)
    second = mapper.map(_proposal(), SUBJECT)
    assert first == second
    assert first[0].period.start_date.isoformat() == "2020-01-01"
    assert "synthetic-employer" not in first[0].employment.employer.employer_id.value


def test_conflicts_preserve_meaning_without_arbitration():
    conflicts, candidates = RetirementConflictMapper().map(_proposal(conflict=True), None)
    assert conflicts[0].explanation.category == "DATE_CONFLICT"
    assert conflicts[0].arbitrated is False
    assert conflicts[0].selected_fact is None
    assert candidates[0].category is ResolutionCategory.TEMPORAL_CONFLICT


def test_mapping_does_not_copy_document_titles_or_references():
    result = RetirementEvidenceMapper().map_documents(_bundle())[0]
    rendered = repr(result)
    assert "synthetic title" not in rendered
    assert "synthetic-reference" not in rendered
