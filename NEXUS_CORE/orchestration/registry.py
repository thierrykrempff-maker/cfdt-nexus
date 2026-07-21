"""In-process registry limited to public orchestration Protocols."""

from __future__ import annotations

from ..identifiers import EntityId
from .contracts import ExecutableEngine
from .models import EngineCapability, EngineDescriptor


class EngineRegistry:
    def __init__(self) -> None:
        self._descriptors: dict[EntityId, EngineDescriptor] = {}
        self._engines: dict[EntityId, ExecutableEngine] = {}

    def register(self, descriptor: EngineDescriptor, engine: ExecutableEngine) -> None:
        if not isinstance(engine, ExecutableEngine):
            raise TypeError("engine must implement ExecutableEngine")
        if descriptor.engine_id in self._descriptors:
            raise ValueError("engine identifier is already registered")
        self._descriptors[descriptor.engine_id] = descriptor
        self._engines[descriptor.engine_id] = engine

    def unregister(self, engine_id: EntityId) -> bool:
        if engine_id not in self._descriptors:
            return False
        del self._descriptors[engine_id]
        del self._engines[engine_id]
        return True

    def get(self, engine_id: EntityId) -> ExecutableEngine | None:
        return self._engines.get(engine_id)

    def descriptor(self, engine_id: EntityId) -> EngineDescriptor | None:
        return self._descriptors.get(engine_id)

    def list(self) -> tuple[EngineDescriptor, ...]:
        return tuple(
            sorted(self._descriptors.values(), key=lambda item: item.engine_id.value)
        )

    def supports(self, engine_id: EntityId, capability: EngineCapability) -> bool:
        descriptor = self.descriptor(engine_id)
        return descriptor is not None and capability in descriptor.capabilities
