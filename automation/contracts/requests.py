"""Normalized request contract for future Nexus experts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .assessments import MissingInformation
from .enums import ConfidentialityLevel, StatementKind
from .serialization import contract_to_dict, freeze_json, freeze_metadata, reject_unknown_fields, require_text
from .statements import Statement


@dataclass(frozen=True)
class ExpertRequest:
    request_id: str
    question_text: str
    requested_domain: str
    context: Mapping[str, Any] = field(default_factory=dict, repr=False)
    facts: tuple[Statement, ...] = ()
    declared_information: tuple[Statement, ...] = ()
    available_evidence_refs: tuple[str, ...] = ()
    missing_information: tuple[MissingInformation, ...] = ()
    detail_level: str = "STANDARD"
    confidentiality: ConfidentialityLevel = ConfidentialityLevel.RESTRICTED
    schema_version: str = "1.0"
    metadata: Mapping[str, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        for name in ("request_id", "question_text", "requested_domain", "detail_level"):
            object.__setattr__(self, name, require_text(getattr(self, name), name))
        object.__setattr__(self, "schema_version", require_text(self.schema_version, "schema_version"))
        if not isinstance(self.confidentiality, ConfidentialityLevel):
            raise TypeError("confidentiality must be a ConfidentialityLevel")
        facts = tuple(self.facts)
        declarations = tuple(self.declared_information)
        if any(not isinstance(item, Statement) for item in facts + declarations):
            raise TypeError("facts and declared_information must contain Statement objects")
        if any(item.kind is not StatementKind.ESTABLISHED_FACT for item in facts):
            raise ValueError("facts may contain only ESTABLISHED_FACT statements; assumptions and intentions are forbidden")
        if any(item.kind is not StatementKind.DECLARED_INFORMATION for item in declarations):
            raise ValueError("declared_information may contain only DECLARED_INFORMATION statements")
        object.__setattr__(self, "facts", facts)
        object.__setattr__(self, "declared_information", declarations)
        object.__setattr__(self, "available_evidence_refs", tuple(require_text(item, "available_evidence_ref") for item in self.available_evidence_refs))
        object.__setattr__(self, "missing_information", tuple(self.missing_information))
        if any(not isinstance(item, MissingInformation) for item in self.missing_information):
            raise TypeError("missing_information must contain MissingInformation objects")
        object.__setattr__(self, "context", freeze_json(self.context, "context"))
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return contract_to_dict(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ExpertRequest":
        allowed = {
            "request_id", "question_text", "requested_domain", "context", "facts", "declared_information",
            "available_evidence_refs", "missing_information", "detail_level", "confidentiality", "schema_version", "metadata",
        }
        reject_unknown_fields(value, allowed, "ExpertRequest")
        return cls(
            request_id=str(value.get("request_id", "")), question_text=str(value.get("question_text", "")),
            requested_domain=str(value.get("requested_domain", "")), context=value.get("context") or {},
            facts=tuple(Statement.from_dict(item) for item in value.get("facts") or ()),
            declared_information=tuple(Statement.from_dict(item) for item in value.get("declared_information") or ()),
            available_evidence_refs=tuple(value.get("available_evidence_refs") or ()),
            missing_information=tuple(MissingInformation.from_dict(item) for item in value.get("missing_information") or ()),
            detail_level=str(value.get("detail_level", "STANDARD")),
            confidentiality=ConfidentialityLevel(value.get("confidentiality", "RESTRICTED")),
            schema_version=str(value.get("schema_version", "1.0")),
            metadata=value.get("metadata") or {},
        )
