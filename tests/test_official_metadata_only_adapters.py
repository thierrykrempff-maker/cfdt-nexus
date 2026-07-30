from SYNDICAL_REASONING_ENGINE import (
    RetrievalStatus, SourceExecutionCoordinator, SourceFamily, default_metadata_executors,
)
from tests.connector_execution_cases import plan_for


def test_official_catalog_is_metadata_only_and_empty_catalog_fabricates_nothing() -> None:
    catalogs = {"cnil": ({"id": "cnil-1", "title": "Badgeage des salariés"},)}
    executors = default_metadata_executors(catalogs)
    summary = SourceExecutionCoordinator(executors).execute(
        plan_for(SourceFamily.OFFICIAL_GUIDANCE, query_text="badge données salariés")
    )
    assert summary.events[0].status is RetrievalStatus.METADATA_ONLY
    assert summary.documents[0].raw_excerpt is None
    assert not summary.events[0].network_call_executed


def test_prevention_query_can_select_carsat_and_inrs_without_double_call() -> None:
    catalogs = {
        "carsat": ({"id": "carsat-1", "title": "Prévention des risques"},),
        "inrs": ({"id": "inrs-1", "title": "Équipements de protection"},),
    }
    summary = SourceExecutionCoordinator(default_metadata_executors(catalogs)).execute(
        plan_for(SourceFamily.OFFICIAL_GUIDANCE, query_text="prévention risque EPI sécurité")
    )
    selected = {event.connector_id for event in summary.events}
    assert selected == {"carsat", "inrs"}
    assert all(event.status is RetrievalStatus.METADATA_ONLY for event in summary.events)


def test_registered_catalog_wrappers_have_truthful_static_capabilities() -> None:
    executors = default_metadata_executors()
    assert {item.connector_id for item in executors} == {
        "cnil", "carsat", "inrs", "anact", "dreets_grand_est", "france_chimie",
        "assurance_maladie", "service_public", "ministere_travail",
        "defenseur_droits", "urssaf", "agirc_arrco", "droit_local",
    }
    assert all(item.connector_kind.value == "STATIC_CATALOG" for item in executors)
