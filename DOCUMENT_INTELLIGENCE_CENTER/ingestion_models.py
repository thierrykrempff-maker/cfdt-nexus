"""Validated and serializable contracts for metadata-only ingestion."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import json
import re
from typing import Any

from .models import DocumentKind, RelationKind


class MetadataStatus(str, Enum):
    ACTIVE = "ACTIVE"
    REPLACED = "REPLACED"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"


class IssueSeverity(str, Enum):
    WARNING = "WARNING"
    ERROR = "ERROR"


class IngestionDecision(str, Enum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    DUPLICATE = "DUPLICATE"
    REJECTED = "REJECTED"


class AgreementNature(str, Enum):
    AGREEMENT = "AGREEMENT"
    AMENDMENT = "AMENDMENT"
    PROTOCOL = "PROTOCOL"
    UNILATERAL_DECISION = "UNILATERAL_DECISION"
    INTERNAL_REGULATION = "INTERNAL_REGULATION"
    OTHER = "OTHER"


_PSEUDONYMOUS_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:-]{7,127}$")
_WINDOWS_PATH = re.compile(r"(?i)(?:^|[\s\"'])[a-z]:\\")
_LINUX_PATH = re.compile(r"(?:^|[\s\"'])(?:/home/|/users/|/tmp/|/var/)")
_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
_IBAN = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b", re.I)
_NIR = re.compile(
    r"\b[12]\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{3}\s?\d{3}\s?\d{2}\b"
)
_SECRET = re.compile(
    r"(?i)\b(?:bearer\s+[a-z0-9._-]+|api[_-]?key\s*[:=]|token\s*[:=]|secret\s*[:=])"
)
_HTML = re.compile(r"<\s*(?:html|body|script|div|p|table|article)\b", re.I)


def validate_safe_metadata(value: str, field_name: str) -> str:
    """Reject content-like or sensitive values before graph ingestion."""

    normalized = value.strip()
    if len(normalized) > 500:
        raise ValueError(f"{field_name}: metadata value is too long")
    checks = (
        (_WINDOWS_PATH, "local path"),
        (_LINUX_PATH, "local path"),
        (_EMAIL, "personal email"),
        (_IBAN, "IBAN"),
        (_NIR, "NIR"),
        (_SECRET, "secret"),
        (_HTML, "HTML content"),
    )
    for pattern, label in checks:
        if pattern.search(normalized):
            raise ValueError(f"{field_name}: forbidden {label}")
    lowered = normalized.lower()
    if "chunk_" in lowered or "storage_id" in lowered:
        raise ValueError(f"{field_name}: forbidden internal identifier")
    return normalized


@dataclass(frozen=True, slots=True)
class ExplicitDocumentLink:
    target_document_id: str
    relation_kind: RelationKind

    def __post_init__(self) -> None:
        if not _PSEUDONYMOUS_ID.fullmatch(self.target_document_id):
            raise ValueError("target_document_id must be pseudonymized")
        if not isinstance(self.relation_kind, RelationKind):
            raise TypeError("relation_kind must be a RelationKind")


@dataclass(frozen=True, slots=True)
class DocumentMetadataInput:
    """Generic, content-free input accepted by the ingestion service."""

    pseudonymous_id: str
    document_kind: DocumentKind
    normalized_title: str
    logical_provenance: str
    document_date: str | None = None
    instance: str | None = None
    nature: str | None = None
    agreement_reference: str | None = None
    family: str | None = None
    version: str | None = None
    effective_from: str | None = None
    effective_to: str | None = None
    status: MetadataStatus = MetadataStatus.UNKNOWN
    confidence: float = 1.0
    topics: tuple[str, ...] = field(default_factory=tuple)
    explicit_links: tuple[ExplicitDocumentLink, ...] = field(default_factory=tuple)
    quality_warnings: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not _PSEUDONYMOUS_ID.fullmatch(self.pseudonymous_id):
            raise ValueError("pseudonymous_id is invalid")
        if not isinstance(self.document_kind, DocumentKind):
            raise TypeError("document_kind must be a DocumentKind")
        if not isinstance(self.status, MetadataStatus):
            raise TypeError("status must be a MetadataStatus")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        required = ("normalized_title", "logical_provenance")
        for field_name in required:
            value = validate_safe_metadata(getattr(self, field_name), field_name)
            if not value:
                raise ValueError(f"{field_name} is required")
            object.__setattr__(self, field_name, value)
        optional = (
            "document_date",
            "instance",
            "nature",
            "agreement_reference",
            "family",
            "version",
            "effective_from",
            "effective_to",
        )
        for field_name in optional:
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    validate_safe_metadata(value, field_name),
                )
        safe_topics = tuple(
            sorted(
                {
                    validate_safe_metadata(topic, "topic")
                    for topic in self.topics
                    if topic.strip()
                }
            )
        )
        object.__setattr__(self, "topics", safe_topics)
        object.__setattr__(
            self,
            "explicit_links",
            tuple(
                sorted(
                    set(self.explicit_links),
                    key=lambda item: (
                        item.target_document_id,
                        item.relation_kind.value,
                    ),
                )
            ),
        )
        object.__setattr__(
            self,
            "quality_warnings",
            tuple(
                sorted(
                    {
                        validate_safe_metadata(warning, "quality_warning")
                        for warning in self.quality_warnings
                        if warning.strip()
                    }
                )
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["document_kind"] = self.document_kind.value
        value["status"] = self.status.value
        value["explicit_links"] = [
            {
                "target_document_id": link.target_document_id,
                "relation_kind": link.relation_kind.value,
            }
            for link in self.explicit_links
        ]
        return value

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )


@dataclass(frozen=True, slots=True)
class AgreementMetadataInput:
    """Declarative agreement metadata before generic ingestion."""

    pseudonymous_id: str
    normalized_title: str
    logical_provenance: str
    nature: AgreementNature
    family: str
    agreement_reference: str
    version: str | None = None
    signature_date: str | None = None
    effective_from: str | None = None
    effective_to: str | None = None
    status: MetadataStatus = MetadataStatus.UNKNOWN
    parent_link: ExplicitDocumentLink | None = None
    confidence: float = 1.0
    topics: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.nature, AgreementNature):
            raise TypeError("nature must be an AgreementNature")
        if self.parent_link is not None and not isinstance(
            self.parent_link,
            ExplicitDocumentLink,
        ):
            raise TypeError("parent_link must be an ExplicitDocumentLink")

    def to_document_input(self) -> DocumentMetadataInput:
        return DocumentMetadataInput(
            pseudonymous_id=self.pseudonymous_id,
            document_kind=DocumentKind.AGREEMENT,
            normalized_title=self.normalized_title,
            logical_provenance=self.logical_provenance,
            document_date=self.signature_date,
            nature=self.nature.value,
            agreement_reference=self.agreement_reference,
            family=self.family,
            version=self.version,
            effective_from=self.effective_from,
            effective_to=self.effective_to,
            status=self.status,
            confidence=self.confidence,
            topics=self.topics,
            explicit_links=(self.parent_link,) if self.parent_link else (),
        )


@dataclass(frozen=True, slots=True)
class MeetingMinutesMetadataInput:
    """CSE or CSSCT minutes metadata before generic ingestion."""

    pseudonymous_id: str
    normalized_title: str
    logical_provenance: str
    document_date: str | None
    instance: str
    document_kind: DocumentKind = DocumentKind.CSE_MINUTES
    agreement_links: tuple[ExplicitDocumentLink, ...] = ()
    confidence: float = 1.0
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        safe_warnings = tuple(
            sorted(
                {
                    validate_safe_metadata(warning, "warning")
                    for warning in self.warnings
                    if warning.strip()
                }
            )
        )
        object.__setattr__(self, "warnings", safe_warnings)

    def to_document_input(self) -> DocumentMetadataInput:
        if self.document_kind not in (
            DocumentKind.CSE_MINUTES,
            DocumentKind.CSSCT_MINUTES,
        ):
            raise ValueError("meeting minutes kind is invalid")
        return DocumentMetadataInput(
            pseudonymous_id=self.pseudonymous_id,
            document_kind=self.document_kind,
            normalized_title=self.normalized_title,
            logical_provenance=self.logical_provenance,
            document_date=self.document_date,
            instance=self.instance,
            nature="MEETING_MINUTES",
            status=MetadataStatus.ACTIVE,
            confidence=self.confidence,
            explicit_links=self.agreement_links,
            quality_warnings=self.warnings,
        )


@dataclass(frozen=True, slots=True)
class IngestionIssue:
    code: str
    description: str
    severity: IssueSeverity
    document_id: str | None
    decision: IngestionDecision
    graph_state: str


@dataclass(frozen=True, slots=True)
class IngestionResult:
    document_id: str | None
    decision: IngestionDecision
    created_relations: int = 0
    issues: tuple[IngestionIssue, ...] = ()


@dataclass(frozen=True, slots=True)
class IngestionBatchResult:
    results: tuple[IngestionResult, ...]

    @property
    def created(self) -> int:
        return sum(item.decision is IngestionDecision.CREATED for item in self.results)

    @property
    def updated(self) -> int:
        return sum(item.decision is IngestionDecision.UPDATED for item in self.results)

    @property
    def duplicates(self) -> int:
        return sum(item.decision is IngestionDecision.DUPLICATE for item in self.results)

    @property
    def rejected(self) -> int:
        return sum(item.decision is IngestionDecision.REJECTED for item in self.results)

    @property
    def relation_count(self) -> int:
        return sum(item.created_relations for item in self.results)

    @property
    def issues(self) -> tuple[IngestionIssue, ...]:
        return tuple(issue for item in self.results for issue in item.issues)

    def to_dict(self) -> dict[str, Any]:
        return {
            "created": self.created,
            "duplicates": self.duplicates,
            "issues": [
                {
                    "code": issue.code,
                    "decision": issue.decision.value,
                    "description": issue.description,
                    "document_id": issue.document_id,
                    "graph_state": issue.graph_state,
                    "severity": issue.severity.value,
                }
                for issue in self.issues
            ],
            "rejected": self.rejected,
            "relation_count": self.relation_count,
            "results": [
                {
                    "created_relations": result.created_relations,
                    "decision": result.decision.value,
                    "document_id": result.document_id,
                }
                for result in self.results
            ],
            "updated": self.updated,
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
