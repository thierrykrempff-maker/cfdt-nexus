from __future__ import annotations

from NEXUS_ADAPTERS.connectors import ConnectorResponseStatus
from NEXUS_RUNTIME_INTEGRATION import RuntimeConnectorConfig, RuntimeConnectorPayloadMapper


def answer():
    return {
        "query": "Question juridique synthétique",
        "confidence": "fort",
        "generated_at": "2026-07-22T12:00:00+00:00",
        "route": {
            "engines": ["legifrance_code_travail", "judilibre_jurisprudence", "pratique_officielle"]
        },
        "sources": [
            {
                "origin": "legifrance_code_travail",
                "official_id": "LEGI-SYNTHETIC",
                "document": "Article synthétique",
                "article": "L. 0000-1",
                "source_layer": "code_travail",
                "url": "https://www.legifrance.gouv.fr/synthetic",
                "excerpt": "Extrait public synthétique.",
            },
            {
                "origin": "judilibre_jurisprudence",
                "judilibre_id": "JUDI-SYNTHETIC",
                "document": "Décision synthétique",
                "source_layer": "jurisprudence",
                "decision_date": "2026-01-02",
            },
            {
                "origin": "cdtn_pratique_officielle",
                "official_id": "CDTN-SYNTHETIC",
                "document": "Fiche pratique synthétique",
                "source_layer": "pratique_officielle",
            },
            {"origin": "nexus_bible_bridge", "document": "Corpus local non connecteur"},
        ],
    }


def test_disabled_connector_runtime_produces_no_snapshot():
    result = RuntimeConnectorPayloadMapper(RuntimeConnectorConfig(False)).map(answer())
    assert result.inputs == ()
    assert result.connector_ids == ()


def test_maps_real_router_sources_to_three_public_connector_snapshots():
    result = RuntimeConnectorPayloadMapper(RuntimeConnectorConfig(True)).map(answer())
    assert result.connector_ids == ("cdtn", "judilibre", "legifrance")
    assert result.snapshot_count == 3
    assert all(item.response.status is ConnectorResponseStatus.SUCCEEDED for item in result.inputs)
    assert [len(item.response.documents) for item in result.inputs] == [1, 1, 1]
    assert result.inputs[2].response.documents[0].external_id == "LEGI-SYNTHETIC"


def test_attempted_connector_without_result_produces_empty_snapshot():
    value = answer()
    value["sources"] = []
    value["route"]["engines"] = ["legifrance_code_travail"]
    result = RuntimeConnectorPayloadMapper(RuntimeConnectorConfig(True)).map(value)
    assert result.connector_ids == ("legifrance",)
    assert result.inputs[0].response.status is ConnectorResponseStatus.EMPTY


def test_modern_offline_connectors_are_not_invented_from_unrelated_sources():
    result = RuntimeConnectorPayloadMapper(RuntimeConnectorConfig(True)).map(answer())
    assert not ({"carsat", "cnil", "inrs", "dreets_grand_est", "anact", "france_chimie"} & set(result.connector_ids))


def test_malformed_source_collection_fails_closed_with_stable_code():
    value = answer()
    value["sources"] = "SECRET-SYNTHETIQUE"
    result = RuntimeConnectorPayloadMapper(RuntimeConnectorConfig(True)).map(value)
    assert result.inputs == ()
    assert result.fallback_code == "CONNECTOR_SNAPSHOT_MAPPING_FAILED"
    assert "SECRET" not in result.fallback_code
