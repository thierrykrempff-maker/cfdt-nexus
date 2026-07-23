from datetime import datetime, timezone

from NEXUS_ADAPTERS.cse import CSEAdapter, CSEAdapterInput
from NEXUS_CORE import (
    EntityId, EntityReference, EvidenceProducer, FindingProducer, RecommendationProducer,
)
from NEXUS_CORE.orchestration import ExecutableEngine
from NEXUS_CORE.reasoning import FactProducer


def adapter():
    return CSEAdapter(CSEAdapterInput(
        EntityReference(EntityId("synthetic-cse-subject"), "cse_body"),
        datetime(2026, 2, 3, tzinfo=timezone.utc),
    ))


def test_adapter_implements_required_protocols():
    value = adapter()
    assert isinstance(value, ExecutableEngine)
    assert isinstance(value, EvidenceProducer)
    assert isinstance(value, FindingProducer)
    assert isinstance(value, RecommendationProducer)
    assert isinstance(value, FactProducer)


def test_public_api_does_not_import_cse_transports_or_document_importer():
    import importlib
    import sys

    sys.modules.pop("automation.cse_memory.document_importer", None)
    for name in tuple(sys.modules):
        if name.startswith("NEXUS_ADAPTERS.cse"):
            sys.modules.pop(name)
    public_api = importlib.import_module("NEXUS_ADAPTERS.cse")

    assert public_api.CSEAdapter.__name__ == CSEAdapter.__name__
    assert "automation.cse_memory.document_importer" not in sys.modules
    assert "requests" not in public_api.__dict__


def test_diagnostics_do_not_reproduce_personal_values():
    value = adapter().adapt()
    rendered = repr(value.diagnostics)
    for sensitive in ("Alice Example", "alice@example.test", "+33102030405"):
        assert sensitive not in rendered


def test_result_is_deterministic_and_immutable():
    value = adapter()
    assert value.adapt() == value.adapt()
    result = value.adapt()
    try:
        result.source_schema_version = "changed"
    except AttributeError:
        pass
    else:
        raise AssertionError("CSE adapter result must be immutable")
