from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from SYNDICAL_REASONING_ENGINE import (
    AlertHistoryMetadata,
    AlertDocumentPriority,
    AlertMechanism,
    CSEAlertsExpertiseReasoningEngine,
    ClaimScope,
    ExpertiseKind,
    InvestigationKind,
    needs_cse_alerts_reasoning,
)
from SYNDICAL_REASONING_ENGINE.cse_alerts_scenarios import cse_alerts_scenarios


def analyze(code: str):
    return CSEAlertsExpertiseReasoningEngine().analyze(
        cse_alerts_scenarios()[code], scenario_code=code
    )


def test_collective_claim_is_distinguished_from_individual_case():
    assert analyze("similar_counter_claims").claim.scope is ClaimScope.COLLECTIVE_CLAIM
    isolated = analyze("isolated_individual")
    assert isolated.claim.scope is ClaimScope.INDIVIDUAL_CLAIM
    assert isolated.articulation.primary_domain.startswith("R1")


@pytest.mark.parametrize(
    ("code", "mechanism"),
    [
        ("collective_union_discrimination", AlertMechanism.RIGHTS_OF_PERSONS),
        ("potential_economic_alert", AlertMechanism.ECONOMIC),
        ("temporary_work_increase", AlertMechanism.SOCIAL),
        ("recurring_understaffing", AlertMechanism.SOCIAL),
        ("documents_refused", AlertMechanism.DEGRADED_CSE_FUNCTIONING),
    ],
)
def test_potential_alert_typology_is_cautious(code, mechanism):
    analysis = analyze(code)
    hypothesis = next(item for item in analysis.alert_hypotheses if item.mechanism is mechanism)
    assert not hypothesis.automatically_established
    assert hypothesis.legal_review_required
    assert "confirmer" in hypothesis.cautious_qualification or "investigation" in hypothesis.cautious_qualification


@pytest.mark.parametrize(
    ("code", "kind"),
    [
        ("potential_economic_expertise", ExpertiseKind.ECONOMIC_ACCOUNTING),
        ("important_project", ExpertiseKind.RESTRUCTURING),
        ("disputed_expertise", ExpertiseKind.EXTERNAL_LEGAL_TECHNICAL_SUPPORT),
    ],
)
def test_expertise_hypotheses_are_never_acquired(code, kind):
    hypothesis = next(item for item in analyze(code).expertise_hypotheses if item.kind is kind)
    assert not hypothesis.automatically_acquired
    assert "vérifier" in hypothesis.funding_to_verify
    assert hypothesis.legal_review_required


def test_investigation_has_legality_neutrality_and_confidentiality_guards():
    proposal = analyze("investigation_request").investigations[0]
    assert proposal.kind is InvestigationKind.CSE
    assert "illégalement" in " ".join(proposal.precautions)
    assert proposal.confidentiality
    assert proposal.neutrality


def test_history_lookup_is_metadata_only_and_sorted():
    class Lookup:
        def search_metadata(self, query):
            return (
                AlertHistoryMetadata("Suivi B", "2025-02", "effectifs", has_commitment=True),
                AlertHistoryMetadata("Suivi A", "2025-01", "effectifs", has_resolution=True),
            )

    result = CSEAlertsExpertiseReasoningEngine(history_lookup=Lookup()).analyze(
        cse_alerts_scenarios()["unmet_commitment"]
    )
    assert [item.title for item in result.history] == ["Suivi A", "Suivi B"]
    assert any(item.kind.value == "employer_commitment" for item in result.timeline)
    assert "fulltext" not in str(result.to_dict()).lower()


def test_documents_cover_all_three_priorities():
    priorities = {item.priority for item in analyze("documents_refused").document_requests}
    assert priorities == {
        AlertDocumentPriority.ESSENTIAL,
        AlertDocumentPriority.USEFUL,
        AlertDocumentPriority.COMPLEMENTARY,
    }


def test_questions_are_hierarchical_and_do_not_duplicate_documented_wording():
    result = analyze("potential_economic_alert")
    assert {item.priority.value for item in result.questions} >= {"critical", "priority", "useful"}
    assert len({item.wording for item in result.questions}) == len(result.questions)


def test_resolution_is_a_draft_requiring_legal_review():
    resolution = analyze("expertise_resolution").resolutions[0]
    assert resolution.draft_only
    assert resolution.legal_review_required
    assert "relire" in resolution.proposed_decision


def test_actors_and_escalation_routes_are_distinguished():
    result = analyze("labour_inspectorate")
    names = {item.name for item in result.competent_actors}
    assert {"CSE", "délégué syndical", "inspection du travail", "Défenseur des droits"} <= names
    assert {item.kind.value for item in result.escalation_options} >= {
        "internal_reminder",
        "labour_inspectorate",
        "defender_of_rights",
        "court",
    }


def test_contradictory_argumentation_and_five_strategies():
    result = analyze("possible_obstruction")
    assert result.cse_position.arguments
    assert result.employer_position.arguments
    assert [item.level for item in result.strategies] == [1, 2, 3, 4, 5]
    assert result.legal_review_required


def test_corrected_situation_keeps_proportionate_strategy():
    result = analyze("corrected_situation")
    assert result.timeline[-1].kind.value == "corrective_measure"
    assert not any("obligatoire" in item.objective for item in result.strategies)


def test_insufficient_alert_remains_unestablished():
    result = analyze("insufficient_alert")
    rendered = str(result.to_dict()).lower()
    assert "alerte non établie" in rendered or "investigation" in rendered
    assert "droit d'alerte est ouvert" not in rendered


def test_models_are_frozen_and_serializable():
    result = analyze("similar_counter_claims")
    with pytest.raises(FrozenInstanceError):
        result.claim.origin = "changed"
    assert result.to_dict()["analysis_type"] == "cse_claims_alerts_expertise"


def test_detector_requires_context_and_rejects_plain_alert_or_isolated_case():
    assert not needs_cse_alerts_reasoning("Alerte")
    assert not needs_cse_alerts_reasoning("Réunion commerciale sur une alerte de stock")
    assert not needs_cse_alerts_reasoning("Un salarié présente un cas individuel isolé au CSE")
    assert needs_cse_alerts_reasoning("Plusieurs salariés signalent au CSE une réclamation collective et demandent une enquête")


def test_output_has_no_automatic_legal_conclusion_or_confidential_identifier():
    rendered = str(analyze("possible_obstruction").to_dict()).lower()
    for forbidden in (
        "droit d'alerte est ouvert",
        "expertise acquise",
        "financement certain",
        "danger grave et imminent établi",
        "entrave constituée",
        "chunk_id",
        "storage_id",
        "local_path",
        "c:\\",
        "/home/",
    ):
        assert forbidden not in rendered
