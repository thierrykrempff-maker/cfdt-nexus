"""Missing-information and risk assessment contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .enums import CriticalityLevel
from .serialization import contract_to_dict, freeze_metadata, reject_unknown_fields, require_text


@dataclass(frozen=True)
class MissingInformation:
    missing_id: str
    description: str
    reason: str
    criticality: CriticalityLevel
    addressee: str
    suggested_question: str
    blocking: bool
    domain: str
    schema_version: str = "1.0"
    metadata: Mapping[str, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        for name in ("missing_id", "description", "reason", "addressee", "suggested_question", "domain"):
            object.__setattr__(self, name, require_text(getattr(self, name), name))
        object.__setattr__(self, "schema_version", require_text(self.schema_version, "schema_version"))
        if not isinstance(self.criticality, CriticalityLevel):
            raise TypeError("criticality must be a CriticalityLevel")
        if not isinstance(self.blocking, bool):
            raise TypeError("blocking must be a boolean")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return contract_to_dict(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "MissingInformation":
        allowed = {"missing_id", "description", "reason", "criticality", "addressee", "suggested_question", "blocking", "domain", "schema_version", "metadata"}
        reject_unknown_fields(value, allowed, "MissingInformation")
        return cls(
            missing_id=str(value.get("missing_id", "")), description=str(value.get("description", "")),
            reason=str(value.get("reason", "")), criticality=CriticalityLevel(value.get("criticality")),
            addressee=str(value.get("addressee", "")), suggested_question=str(value.get("suggested_question", "")),
            blocking=value.get("blocking"), domain=str(value.get("domain", "")),
            schema_version=str(value.get("schema_version", "1.0")), metadata=value.get("metadata") or {},
        )


@dataclass(frozen=True)
class RiskAssessment:
    risk_id: str
    risk_type: str
    description: str
    level: CriticalityLevel
    probability: float | None
    impact: str
    horizon: str
    supporting_evidence: tuple[str, ...] = ()
    mitigation_actions: tuple[str, ...] = ()
    domain: str = "general"
    schema_version: str = "1.0"
    metadata: Mapping[str, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        for name in ("risk_id", "risk_type", "description", "impact", "horizon", "domain"):
            object.__setattr__(self, name, require_text(getattr(self, name), name))
        object.__setattr__(self, "schema_version", require_text(self.schema_version, "schema_version"))
        if not isinstance(self.level, CriticalityLevel):
            raise TypeError("level must be a CriticalityLevel")
        if self.probability is not None and not 0.0 <= self.probability <= 1.0:
            raise ValueError("probability must be between 0 and 1")
        if self.level is CriticalityLevel.CRITICAL and (not self.description.strip() or not self.impact.strip()):
            raise ValueError("CRITICAL risk requires a description and an impact")
        object.__setattr__(self, "supporting_evidence", tuple(require_text(item, "supporting_evidence") for item in self.supporting_evidence))
        object.__setattr__(self, "mitigation_actions", tuple(require_text(item, "mitigation_action") for item in self.mitigation_actions))
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return contract_to_dict(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RiskAssessment":
        allowed = {"risk_id", "risk_type", "description", "level", "probability", "impact", "horizon", "supporting_evidence", "mitigation_actions", "domain", "schema_version", "metadata"}
        reject_unknown_fields(value, allowed, "RiskAssessment")
        return cls(
            risk_id=str(value.get("risk_id", "")), risk_type=str(value.get("risk_type", "")),
            description=str(value.get("description", "")), level=CriticalityLevel(value.get("level")),
            probability=value.get("probability"), impact=str(value.get("impact", "")),
            horizon=str(value.get("horizon", "")), supporting_evidence=tuple(value.get("supporting_evidence") or ()),
            mitigation_actions=tuple(value.get("mitigation_actions") or ()), domain=str(value.get("domain", "general")),
            schema_version=str(value.get("schema_version", "1.0")),
            metadata=value.get("metadata") or {},
        )
