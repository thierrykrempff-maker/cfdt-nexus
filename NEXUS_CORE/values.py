"""Explicit, extensible value types accepted by generic Evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Protocol, runtime_checkable

from .entities import EntityReference
from .privacy import MetadataEntry


@runtime_checkable
class EvidenceValue(Protocol):
    @property
    def value_type(self) -> str:
        """Return a stable, non-sensitive value type code."""


@dataclass(frozen=True, slots=True)
class TextEvidenceValue:
    value: str = field(repr=False)

    @property
    def value_type(self) -> str:
        return "text"


@dataclass(frozen=True, slots=True)
class NumericEvidenceValue:
    value: Decimal = field(repr=False)
    unit: str | None = None

    @property
    def value_type(self) -> str:
        return "numeric"


@dataclass(frozen=True, slots=True)
class BooleanEvidenceValue:
    value: bool = field(repr=False)

    @property
    def value_type(self) -> str:
        return "boolean"


@dataclass(frozen=True, slots=True)
class TemporalEvidenceValue:
    value: date | datetime = field(repr=False)

    @property
    def value_type(self) -> str:
        return "temporal"


@dataclass(frozen=True, slots=True)
class EntityEvidenceValue:
    value: EntityReference = field(repr=False)

    @property
    def value_type(self) -> str:
        return "entity_reference"


@dataclass(frozen=True, slots=True)
class CustomEvidenceValue:
    """Engine extension represented by a named tuple of typed metadata."""

    type_name: str
    fields: tuple[MetadataEntry, ...] = field(default=(), repr=False)

    @property
    def value_type(self) -> str:
        return self.type_name


EvidenceValueType = (
    TextEvidenceValue
    | NumericEvidenceValue
    | BooleanEvidenceValue
    | TemporalEvidenceValue
    | EntityEvidenceValue
    | CustomEvidenceValue
)
