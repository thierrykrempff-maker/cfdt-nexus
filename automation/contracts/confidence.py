"""Multidimensional confidence contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .enums import ConfidenceDimension, ConfidenceLevel
from .serialization import contract_to_dict, freeze_metadata, reject_unknown_fields, require_text


@dataclass(frozen=True)
class ConfidenceAssessment:
    assessment_id: str
    dimension: ConfidenceDimension
    level: ConfidenceLevel | None = None
    score: float | None = None
    rationale: str | None = None
    factors: tuple[str, ...] = ()
    raw_value: str | None = None
    producer: str | None = None
    schema_version: str = "1.0"
    metadata: Mapping[str, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "assessment_id", require_text(self.assessment_id, "assessment_id"))
        object.__setattr__(self, "schema_version", require_text(self.schema_version, "schema_version"))
        if not isinstance(self.dimension, ConfidenceDimension):
            raise TypeError("dimension must be a ConfidenceDimension")
        if self.level is not None and not isinstance(self.level, ConfidenceLevel):
            raise TypeError("level must be a ConfidenceLevel or None")
        if self.score is not None and not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be between 0 and 1")
        if self.level is None and self.score is not None:
            raise ValueError("score cannot be set when confidence level is unknown")
        object.__setattr__(self, "factors", tuple(require_text(item, "factor") for item in self.factors))
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))

    @property
    def known(self) -> bool:
        return self.level is not None

    def to_dict(self) -> dict[str, Any]:
        result = contract_to_dict(self)
        result["known"] = self.known
        return result

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ConfidenceAssessment":
        allowed = {
            "assessment_id", "dimension", "level", "score", "rationale", "factors",
            "raw_value", "producer", "schema_version", "metadata", "known",
        }
        reject_unknown_fields(value, allowed, "ConfidenceAssessment")
        level = value.get("level")
        if "known" in value and bool(value["known"]) != (level is not None):
            raise ValueError("known must match the presence of a confidence level")
        return cls(
            assessment_id=str(value.get("assessment_id", "")),
            dimension=ConfidenceDimension(value.get("dimension")),
            level=ConfidenceLevel(level) if level is not None else None,
            score=value.get("score"),
            rationale=value.get("rationale"),
            factors=tuple(value.get("factors") or ()),
            raw_value=value.get("raw_value"),
            producer=value.get("producer"),
            schema_version=str(value.get("schema_version", "1.0")),
            metadata=value.get("metadata") or {},
        )
