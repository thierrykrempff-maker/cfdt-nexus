"""Engine registry behavior and Protocol-only engine acceptance."""

from datetime import datetime, timezone

import pytest

from NEXUS_CORE import EntityId
from NEXUS_CORE.orchestration import (
    EngineCapability,
    EngineDescriptor,
    EngineRegistry,
    ExecutableEngine,
    ExecutionContext,
    ExecutionResult,
    ExecutionStatus,
)


CAPABILITY = EngineCapability("STRUCTURAL_ANALYSIS")


class StubEngine:
    def __init__(self, engine_id):
        self.engine_id = engine_id

    def execute(self, context: ExecutionContext) -> ExecutionResult:
        return ExecutionResult(
            EntityId("result-registry"),
            self.engine_id,
            ExecutionStatus.SUCCEEDED,
            (CAPABILITY,),
        )


def descriptor(identifier="engine-registry", enabled=True):
    return EngineDescriptor(
        EntityId(identifier),
        "GENERIC_ENGINE",
        (CAPABILITY,),
        enabled,
    )


def test_register_get_list_supports_and_unregister():
    registry = EngineRegistry()
    item = descriptor()
    engine = StubEngine(item.engine_id)
    registry.register(item, engine)
    assert registry.get(item.engine_id) is engine
    assert registry.list() == (item,)
    assert registry.supports(item.engine_id, CAPABILITY)
    assert registry.unregister(item.engine_id) is True
    assert registry.get(item.engine_id) is None
    assert registry.unregister(item.engine_id) is False


def test_registry_accepts_structural_protocol_and_rejects_invalid_engine():
    registry = EngineRegistry()
    engine = StubEngine(EntityId("engine-protocol"))
    assert isinstance(engine, ExecutableEngine)
    registry.register(descriptor("engine-protocol"), engine)
    with pytest.raises(TypeError, match="ExecutableEngine"):
        registry.register(descriptor("engine-invalid"), object())


def test_duplicate_registration_fails_closed():
    registry = EngineRegistry()
    item = descriptor()
    registry.register(item, StubEngine(item.engine_id))
    with pytest.raises(ValueError, match="already registered"):
        registry.register(item, StubEngine(item.engine_id))


def test_registry_order_is_technical_and_deterministic():
    registry = EngineRegistry()
    for identifier in ("engine-zeta", "engine-alpha"):
        item = descriptor(identifier)
        registry.register(item, StubEngine(item.engine_id))
    assert tuple(item.engine_id.value for item in registry.list()) == (
        "engine-alpha",
        "engine-zeta",
    )
