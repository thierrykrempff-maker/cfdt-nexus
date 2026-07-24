from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from SYNDICAL_REASONING_ENGINE import (
    CSEConsultationReasoningEngine,
    CSEMemoryMetadata,
    CollectiveDimension,
    ConsultationAssessment,
    ObstructionRisk,
    ParticipationMechanism,
    ProjectType,
    cse_consultation_scenarios,
    needs_cse_consultation_reasoning,
)


class SyntheticMemory:
    def search_metadata(self, query):
        return (
            CSEMemoryMetadata(
                "synthetic-pv-2024",
                "PV CSE synthétique – projet de service",
                "pv_cse",
                2024,
                "CSE",
                "organisation",
                True,
                True,
                2,
            ),
        )


def test_collective_reorganization_is_prudently_qualified():
    case = cse_consultation_scenarios()["job_suppression"]
    result = CSEConsultationReasoningEngine().analyze(case)
    assert result.project.project_type is ProjectType.REORGANIZATION
    assert result.collective_dimension is CollectiveDimension.IDENTIFIED_COLLECTIVE_PROJECT
    assert result.mechanism.mechanism is ParticipationMechanism.CONSULTATION
    assert any("potentiellement" in item.label for item in result.qualifications)


def test_isolated_case_keeps_r1a_primary():
    result = CSEConsultationReasoningEngine().analyze(
        cse_consultation_scenarios()["isolated_individual"]
    )
    assert result.collective_dimension is CollectiveDimension.ISOLATED_INDIVIDUAL
    assert result.articulation.primary_domain == "R1A_CONTRACT_CHANGE"
    assert "R2A_CSE_CONSULTATION" in result.articulation.complementary_domains


def test_information_consultation_and_negotiation_are_distinct():
    result = CSEConsultationReasoningEngine().analyze(
        cse_consultation_scenarios()["regular_consultation"]
    )
    assert result.consultation_assessment is ConsultationAssessment.APPARENTLY_REGULAR
    assert result.mechanism.competent_actor == "CSE"
    assert "organisations syndicales" not in result.mechanism.competent_actor


def test_early_implementation_does_not_assert_illegality_or_crime():
    result = CSEConsultationReasoningEngine().analyze(
        cse_consultation_scenarios()["obstruction_risk"]
    )
    rendered = str(result.to_dict()).lower()
    assert result.obstruction.risk is ObstructionRisk.POSSIBLE_INDICATORS
    assert "qualification non établie" in rendered
    assert "délit constitué" not in rendered
    assert "consultation obligatoirement requise" not in rendered


def test_questions_skip_documented_answers():
    result = CSEConsultationReasoningEngine().analyze(
        cse_consultation_scenarios()["regular_consultation"]
    )
    questions = {item.question for item in result.automatic_questions}
    assert "Le CSE a-t-il été informé ou consulté, à quelle date et sur quel ordre du jour ?" not in questions


def test_document_requests_are_prioritized_and_metadata_only():
    result = CSEConsultationReasoningEngine().analyze(
        cse_consultation_scenarios()["insufficient_documents"]
    )
    assert result.document_requests
    rendered = str(result.to_dict()).lower()
    assert "fulltext" not in rendered
    assert "chunk_id" not in rendered
    assert "local_path" not in rendered


def test_memory_boundary_is_injected_and_returns_metadata_only():
    result = CSEConsultationReasoningEngine(memory_lookup=SyntheticMemory()).analyze(
        cse_consultation_scenarios()["historical_commitment"]
    )
    assert result.cse_memory_results[0].document_id == "synthetic-pv-2024"
    assert "engagement antérieur à confirmer" not in str(result.to_dict()).lower()
    assert "content" not in result.cse_memory_results[0].__dataclass_fields__
    assert "synthetic-pv-2024" not in str(result.to_dict())


def test_models_are_immutable():
    metadata = CSEMemoryMetadata("id", "titre fictif", "pv")
    with pytest.raises(FrozenInstanceError):
        metadata.title = "autre"


@pytest.mark.parametrize(
    "question",
    (
        "Le CSE doit-il examiner cette réorganisation de plusieurs services ?",
        "Un nouvel outil de contrôle est introduit avant avis.",
        "Plusieurs équipes changent de cycle.",
    ),
)
def test_r2a_detection(question):
    assert needs_cse_consultation_reasoning(question)
