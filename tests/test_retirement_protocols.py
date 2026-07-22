from datetime import datetime, timezone

from RETIREMENT_PENIBILITY_ENGINE.retirement_models import RetirementReport
from NEXUS_ADAPTERS.retirement import RetirementAdapter, RetirementAdapterInput
from NEXUS_CORE import EvidenceProducer, FindingProducer, RecommendationProducer, EntityId, EntityReference
from NEXUS_CORE.orchestration import ExecutableEngine
from NEXUS_CORE.reasoning import FactProducer


def _adapter():
    report = RetirementReport("synthetic-report", "synthetic-request", "synthetic")
    source = RetirementAdapterInput(
        report, EntityReference(EntityId("synthetic-subject"), "person"),
        datetime(2026, 1, 2, tzinfo=timezone.utc),
    )
    return RetirementAdapter(source)


def test_adapter_implements_all_required_structural_protocols():
    adapter = _adapter()
    assert isinstance(adapter, ExecutableEngine)
    assert isinstance(adapter, EvidenceProducer)
    assert isinstance(adapter, FindingProducer)
    assert isinstance(adapter, RecommendationProducer)
    assert isinstance(adapter, FactProducer)


def test_public_import_does_not_load_network_transports():
    import NEXUS_ADAPTERS.retirement as public_api

    assert public_api.RetirementAdapter is RetirementAdapter
    forbidden = ("requests", "urllib.request", "http.client")
    module_globals = " ".join(public_api.__dict__).lower()
    assert all(name not in module_globals for name in forbidden)


def test_adapter_result_is_deterministic_and_immutable():
    adapter = _adapter()
    assert adapter.adapt() == adapter.adapt()
    result = adapter.adapt()
    try:
        result.source_schema_version = "changed"
    except AttributeError:
        pass
    else:
        raise AssertionError("adapter result must be immutable")
