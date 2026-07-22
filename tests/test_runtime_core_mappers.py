from __future__ import annotations

from datetime import datetime, timezone

from NEXUS_CORE import EntityId, EntityReference
from NEXUS_RUNTIME_INTEGRATION.mappers import RuntimeExpertPayloadMapper


NOW = datetime(2026, 7, 22, 12, 0, tzinfo=timezone.utc)


def test_legal_mapping_preserves_existing_content_and_source_provenance():
    mapper = RuntimeExpertPayloadMapper()
    answer = {
        "query": "Question juridique synthétique",
        "confidence": "fort",
        "route": {"main_domain": "droit_syndical", "domains": ["droit_syndical"]},
        "sources": [{
            "origin": "legifrance_code_travail",
            "source_layer": "code_travail",
            "document": "Article synthétique",
        }],
    }
    request = mapper.build_request(answer)
    mapped = mapper.map_legal(
        {
            "active": True,
            "ce_qui_est_certain": ["Constat synthétique."],
            "conclusion_provisoire_juridique": {"position": "Conclusion synthétique."},
            "strategie_action_ordonnee": ["Relecture humaine."],
            "limites": [],
        },
        answer,
        request.request_id,
        EntityReference(EntityId("subject-synthetic"), "runtime_request"),
        NOW,
    )
    assert mapped is not None
    assert mapped.report.findings == ("Constat synthétique.",)
    assert mapped.report.conclusions == ("Conclusion synthétique.",)
    assert len(mapped.artifacts.evidence) == 1
    assert len(mapped.artifacts.documents) == 1
    assert mapped.artifacts.documents[0].source.reference.label_code == "RUNTIME_LEGAL_SOURCE"


def test_payroll_mapping_normalizes_producer_for_payroll_adapter():
    mapper = RuntimeExpertPayloadMapper()
    report = mapper.map_payroll({
        "active": True,
        "name": "Expert Paie V0",
        "objet_du_controle": "Contrôle synthétique.",
        "elements_du_bulletin_concernes": [],
        "donnees_necessaires_au_calcul": [],
        "limites": [],
    }, "request-synthetic")
    assert report is not None
    assert report.producer == "paie"
    assert report.to_dict()["metadata"]["runtime_original_producer"] == "Expert Paie V0"


def test_same_question_produces_stable_request_identifier():
    mapper = RuntimeExpertPayloadMapper()
    value = {"query": "Question stable", "route": {"main_domain": "paie", "domains": ["paie"]}}
    assert mapper.build_request(value).request_id == mapper.build_request(value).request_id
