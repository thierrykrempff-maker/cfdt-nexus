"""Knowledge source descriptions and explicit retrieval evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Mapping

from .enums import ConfidentialityLevel, ConnectionStatus, ConsultationStatus, SourceCategory
from .serialization import (
    contract_to_dict,
    freeze_metadata,
    parse_date,
    parse_datetime,
    reject_unknown_fields,
    require_text,
)


def _validate_timezone(value: datetime | None, field_name: str) -> None:
    if value is not None and value.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone")


@dataclass(frozen=True)
class KnowledgeSource:
    source_id: str
    name: str
    publisher: str
    category: SourceCategory
    source_type: str
    is_official: bool
    is_internal: bool
    confidentiality: ConfidentialityLevel
    connection_status: ConnectionStatus
    reference: str | None = None
    published_on: date | None = None
    effective_on: date | None = None
    consulted_at: datetime | None = None
    retrieval_evidence_id: str | None = None
    jurisdiction: str | None = None
    domains: tuple[str, ...] = ()
    version: str | None = None
    freshness: str | None = None
    schema_version: str = "1.0"
    metadata: Mapping[str, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        for name in ("source_id", "name", "publisher", "source_type"):
            object.__setattr__(self, name, require_text(getattr(self, name), name))
        object.__setattr__(self, "schema_version", require_text(self.schema_version, "schema_version"))
        if not isinstance(self.category, SourceCategory):
            raise TypeError("category must be a SourceCategory")
        if not isinstance(self.confidentiality, ConfidentialityLevel):
            raise TypeError("confidentiality must be a ConfidentialityLevel")
        if not isinstance(self.connection_status, ConnectionStatus):
            raise TypeError("connection_status must be a ConnectionStatus")
        if not isinstance(self.is_official, bool) or not isinstance(self.is_internal, bool):
            raise TypeError("is_official and is_internal must be booleans")
        _validate_timezone(self.consulted_at, "consulted_at")
        if self.consulted_at is not None and not self.retrieval_evidence_id:
            raise ValueError("consulted_at requires retrieval_evidence_id")
        if self.retrieval_evidence_id and self.consulted_at is None:
            raise ValueError("retrieval_evidence_id requires consulted_at")
        object.__setattr__(self, "domains", tuple(require_text(item, "domain") for item in self.domains))
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return contract_to_dict(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "KnowledgeSource":
        allowed = {
            "source_id", "name", "publisher", "category", "source_type", "is_official", "is_internal",
            "confidentiality", "connection_status", "reference", "published_on", "effective_on", "consulted_at",
            "retrieval_evidence_id", "jurisdiction", "domains", "version", "freshness", "schema_version", "metadata",
        }
        reject_unknown_fields(value, allowed, "KnowledgeSource")
        return cls(
            source_id=str(value.get("source_id", "")), name=str(value.get("name", "")),
            publisher=str(value.get("publisher", "")), category=SourceCategory(value.get("category")),
            source_type=str(value.get("source_type", "")), is_official=value.get("is_official"),
            is_internal=value.get("is_internal"), confidentiality=ConfidentialityLevel(value.get("confidentiality")),
            connection_status=ConnectionStatus(value.get("connection_status")), reference=value.get("reference"),
            published_on=parse_date(value.get("published_on"), "published_on"),
            effective_on=parse_date(value.get("effective_on"), "effective_on"),
            consulted_at=parse_datetime(value.get("consulted_at"), "consulted_at"),
            retrieval_evidence_id=value.get("retrieval_evidence_id"), jurisdiction=value.get("jurisdiction"),
            domains=tuple(value.get("domains") or ()), version=value.get("version"), freshness=value.get("freshness"),
            schema_version=str(value.get("schema_version", "1.0")),
            metadata=value.get("metadata") or {},
        )


@dataclass(frozen=True)
class SourceEvidence:
    evidence_id: str
    source_id: str
    access_mode: str
    consultation_status: ConsultationStatus
    occurred_at: datetime | None = None
    exact_reference: str | None = None
    excerpt_or_fingerprint: str | None = None
    access_result: str | None = None
    error: str | None = None
    schema_version: str = "1.0"
    metadata: Mapping[str, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        for name in ("evidence_id", "source_id", "access_mode"):
            object.__setattr__(self, name, require_text(getattr(self, name), name))
        object.__setattr__(self, "schema_version", require_text(self.schema_version, "schema_version"))
        if not isinstance(self.consultation_status, ConsultationStatus):
            raise TypeError("consultation_status must be a ConsultationStatus")
        _validate_timezone(self.occurred_at, "occurred_at")
        if self.consultation_status in {ConsultationStatus.SUCCEEDED, ConsultationStatus.CACHE_HIT}:
            if self.occurred_at is None:
                raise ValueError("successful or cached consultation evidence requires occurred_at")
            if not self.exact_reference or not self.exact_reference.strip():
                raise ValueError("successful or cached consultation evidence requires exact_reference")
            if not self.access_result or not self.access_result.strip():
                raise ValueError("successful or cached consultation evidence requires access_result")
        if self.consultation_status is ConsultationStatus.FAILED and not self.error:
            raise ValueError("failed consultation evidence requires an error")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))

    @property
    def consulted(self) -> bool:
        return self.consultation_status is ConsultationStatus.SUCCEEDED

    @property
    def cache_used(self) -> bool:
        return self.consultation_status is ConsultationStatus.CACHE_HIT

    def to_dict(self) -> dict[str, Any]:
        result = contract_to_dict(self)
        result["consulted"] = self.consulted
        result["cache_used"] = self.cache_used
        return result

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "SourceEvidence":
        allowed = {
            "evidence_id", "source_id", "access_mode", "consultation_status", "occurred_at", "exact_reference",
            "excerpt_or_fingerprint", "access_result", "error", "schema_version", "metadata", "consulted", "cache_used",
        }
        reject_unknown_fields(value, allowed, "SourceEvidence")
        status = ConsultationStatus(value.get("consultation_status"))
        if "consulted" in value and bool(value["consulted"]) != (status is ConsultationStatus.SUCCEEDED):
            raise ValueError("consulted is derived from consultation_status")
        if "cache_used" in value and bool(value["cache_used"]) != (status is ConsultationStatus.CACHE_HIT):
            raise ValueError("cache_used is derived from consultation_status")
        return cls(
            evidence_id=str(value.get("evidence_id", "")), source_id=str(value.get("source_id", "")),
            access_mode=str(value.get("access_mode", "")), consultation_status=status,
            occurred_at=parse_datetime(value.get("occurred_at"), "occurred_at"), exact_reference=value.get("exact_reference"),
            excerpt_or_fingerprint=value.get("excerpt_or_fingerprint"), access_result=value.get("access_result"),
            error=value.get("error"), schema_version=str(value.get("schema_version", "1.0")),
            metadata=value.get("metadata") or {},
        )
