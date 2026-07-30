"""Immutable contracts for truthful connector execution traceability."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
import re
from typing import Any, Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACE_VERSION = "3.0"


class RetrievalStatus(str, Enum):
    LOCAL_DOCUMENT = "LOCAL_DOCUMENT"
    LIVE_SEARCH_EXECUTED = "LIVE_SEARCH_EXECUTED"
    LIVE_RESULT_OBTAINED = "LIVE_RESULT_OBTAINED"
    LIVE_NO_RELEVANT_RESULT = "LIVE_NO_RELEVANT_RESULT"
    CONNECTOR_NOT_CONFIGURED = "CONNECTOR_NOT_CONFIGURED"
    CONNECTOR_UNAVAILABLE = "CONNECTOR_UNAVAILABLE"
    CONNECTOR_ERROR = "CONNECTOR_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    CACHE_RESULT = "CACHE_RESULT"
    STALE_CACHE_RESULT = "STALE_CACHE_RESULT"
    FIXTURE_RESULT = "FIXTURE_RESULT"
    METADATA_ONLY = "METADATA_ONLY"
    TITLE_ONLY = "TITLE_ONLY"
    SKIPPED_NOT_RELEVANT = "SKIPPED_NOT_RELEVANT"
    BLOCKED_BY_MISSING_FACTS = "BLOCKED_BY_MISSING_FACTS"
    UNSUPPORTED_SOURCE = "UNSUPPORTED_SOURCE"
    REJECTED_RESULT = "REJECTED_RESULT"


class ConnectorKind(str, Enum):
    LOCAL_INDEX = "LOCAL_INDEX"
    LIVE_API = "LIVE_API"
    LIVE_PUBLIC_WEB = "LIVE_PUBLIC_WEB"
    CACHE_BACKED_API = "CACHE_BACKED_API"
    STATIC_CATALOG = "STATIC_CATALOG"
    METADATA_BRIDGE = "METADATA_BRIDGE"
    FIXTURE_PROVIDER = "FIXTURE_PROVIDER"
    UNSUPPORTED = "UNSUPPORTED"


LIVE_STATUSES = frozenset(
    {
        RetrievalStatus.LIVE_SEARCH_EXECUTED,
        RetrievalStatus.LIVE_RESULT_OBTAINED,
        RetrievalStatus.LIVE_NO_RELEVANT_RESULT,
    }
)
RESULT_STATUSES = frozenset(
    {
        RetrievalStatus.LOCAL_DOCUMENT,
        RetrievalStatus.LIVE_RESULT_OBTAINED,
        RetrievalStatus.CACHE_RESULT,
        RetrievalStatus.STALE_CACHE_RESULT,
        RetrievalStatus.FIXTURE_RESULT,
        RetrievalStatus.METADATA_ONLY,
        RetrievalStatus.TITLE_ONLY,
    }
)


_SECRET_KEY = re.compile(
    r"(authorization|access[_-]?token|refresh[_-]?token|client[_-]?secret|"
    r"password|cookie|api[_-]?key)",
    re.IGNORECASE,
)
_SECRET_VALUE = re.compile(
    r"(?i)\b(?:bearer\s+)?(?:eyJ[a-zA-Z0-9._~-]{12,}|"
    r"(?:token|secret|password|authorization)\s*[:=]\s*\S+)"
)
_WINDOWS_PATH = re.compile(r"(?i)\b[A-Z]:\\(?:[^\\\r\n]+\\)*[^\\\r\n]*")
_POSIX_PRIVATE_PATH = re.compile(r"(?i)(?:/home/|/users/|/tmp/)[^\s\"']+")
_URL_SECRET_KEYS = frozenset(
    {"token", "access_token", "refresh_token", "client_secret", "api_key", "key"}
)


def redact_public_value(value: object, *, max_length: int = 500) -> str | None:
    """Remove credentials and local paths from a public trace value."""

    if value is None:
        return None
    text = str(value)
    text = _SECRET_VALUE.sub("<redacted>", text)
    text = _WINDOWS_PATH.sub("<local-path-redacted>", text)
    text = _POSIX_PRIVATE_PATH.sub("<local-path-redacted>", text)
    return text[:max_length]


def redact_endpoint(value: object) -> str | None:
    """Keep an endpoint useful for audit while removing sensitive query values."""

    text = redact_public_value(value, max_length=2048)
    if not text:
        return None
    try:
        parsed = urlsplit(text)
    except ValueError:
        return redact_public_value(text)
    if not parsed.scheme or not parsed.netloc:
        return redact_public_value(text)
    safe_query = urlencode(
        [
            (key, "<redacted>" if key.lower() in _URL_SECRET_KEYS else val)
            for key, val in parse_qsl(parsed.query, keep_blank_values=True)
        ]
    )
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, safe_query, ""))


def redact_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively redact a technical mapping without changing its shape."""

    result: dict[str, Any] = {}
    for key, item in value.items():
        if _SECRET_KEY.search(str(key)):
            result[str(key)] = "<redacted>"
        elif isinstance(item, Mapping):
            result[str(key)] = redact_mapping(item)
        elif isinstance(item, (list, tuple)):
            result[str(key)] = [
                redact_mapping(child) if isinstance(child, Mapping) else redact_public_value(child)
                for child in item
            ]
        else:
            result[str(key)] = redact_public_value(item)
    return result


@dataclass(frozen=True, slots=True)
class RetrievalEvent:
    event_id: str
    case_session_id: str
    plan_id: str
    issue_id: str
    target_id: str
    query_id: str
    connector_id: str
    connector_name: str
    connector_kind: ConnectorKind
    source_family: str
    status: RetrievalStatus
    started_at: str
    completed_at: str
    duration_ms: int
    live_call_attempted: bool
    network_call_executed: bool
    cache_checked: bool
    cache_hit: bool
    fixture_used: bool
    metadata_only: bool
    query_text: str
    normalized_query: str
    endpoint_domain: str | None
    http_status: int | None
    result_count: int
    accepted_count: int
    rejected_count: int
    warning_codes: tuple[str, ...] = ()
    error_code: str | None = None
    error_message_public: str | None = None
    provenance: tuple[tuple[str, str], ...] = ()
    trace_version: str = TRACE_VERSION

    def __post_init__(self) -> None:
        required = (
            self.event_id,
            self.case_session_id,
            self.plan_id,
            self.issue_id,
            self.target_id,
            self.query_id,
            self.connector_id,
            self.connector_name,
            self.source_family,
            self.started_at,
            self.completed_at,
            self.query_text,
            self.normalized_query,
            self.trace_version,
        )
        if not all(str(item).strip() for item in required):
            raise ValueError("retrieval event identity and query fields are required")
        if min(self.duration_ms, self.result_count, self.accepted_count, self.rejected_count) < 0:
            raise ValueError("retrieval counters cannot be negative")
        if self.accepted_count + self.rejected_count > self.result_count:
            raise ValueError("accepted and rejected counts exceed result count")
        if self.status in LIVE_STATUSES and not (
            self.live_call_attempted and self.network_call_executed
        ):
            raise ValueError("a live status requires an executed network call")
        if self.status is RetrievalStatus.LIVE_RESULT_OBTAINED and not self.accepted_count:
            raise ValueError("LIVE_RESULT_OBTAINED requires an accepted result")
        if self.status is RetrievalStatus.LIVE_NO_RELEVANT_RESULT and self.accepted_count:
            raise ValueError("LIVE_NO_RELEVANT_RESULT cannot contain accepted results")
        if self.cache_hit and self.status not in {
            RetrievalStatus.CACHE_RESULT,
            RetrievalStatus.STALE_CACHE_RESULT,
        }:
            raise ValueError("cache hits must use an explicit cache status")
        if self.fixture_used and self.status is not RetrievalStatus.FIXTURE_RESULT:
            raise ValueError("fixtures must use FIXTURE_RESULT")
        if self.metadata_only and self.status not in {
            RetrievalStatus.METADATA_ONLY,
            RetrievalStatus.TITLE_ONLY,
        }:
            raise ValueError("metadata-only events must use a metadata status")

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["connector_kind"] = self.connector_kind.value
        payload["status"] = self.status.value
        return payload

    def to_public_dict(self) -> dict[str, object]:
        return {
            "source": self.connector_name,
            "source_family": self.source_family,
            "search_live": self.status in LIVE_STATUSES,
            "query": redact_public_value(self.query_text, max_length=240),
            "status": self.status.value,
            "results_examined": self.result_count,
            "results_retained": self.accepted_count,
            "reason": redact_public_value(self.error_message_public, max_length=240),
        }

    def redacted(self) -> "RetrievalEvent":
        return replace(
            self,
            query_text=redact_public_value(self.query_text) or "<redacted>",
            normalized_query=redact_public_value(self.normalized_query) or "<redacted>",
            endpoint_domain=redact_endpoint(self.endpoint_domain),
            error_message_public=redact_public_value(self.error_message_public),
            provenance=tuple(
                (
                    redact_public_value(key, max_length=80) or "<redacted>",
                    redact_public_value(value, max_length=240) or "<redacted>",
                )
                for key, value in self.provenance
                if not _SECRET_KEY.search(str(key))
            ),
        )


@dataclass(frozen=True, slots=True)
class RetrievedDocument:
    document_id: str
    event_id: str
    source_family: str
    provider: str
    title: str
    public_reference: str | None = None
    url_or_external_id: str | None = None
    document_type: str | None = None
    date: str | None = None
    version: str | None = None
    jurisdiction: str | None = None
    court: str | None = None
    chamber: str | None = None
    case_number: str | None = None
    article_number: str | None = None
    clause_number: str | None = None
    page: str | None = None
    raw_excerpt: str | None = None
    normalized_excerpt: str | None = None
    provenance: tuple[tuple[str, str], ...] = ()
    status: RetrievalStatus = RetrievalStatus.METADATA_ONLY
    cache_age: int | None = None
    metadata_complete: bool = False
    sensitive: bool = False
    establishment_scope: str | None = None
    temporal_scope: str | None = None
    rejected: bool = False
    rejection_reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not all((self.document_id.strip(), self.event_id.strip(), self.source_family.strip())):
            raise ValueError("retrieved document identity is required")
        if not self.provider.strip() or not self.title.strip():
            raise ValueError("retrieved document provider and title are required")
        if self.status in LIVE_STATUSES and self.status is not RetrievalStatus.LIVE_RESULT_OBTAINED:
            raise ValueError("documents cannot use a live-attempt-only status")
        if self.rejected and not self.rejection_reasons:
            raise ValueError("rejected documents require a reason")
        if self.cache_age is not None and self.cache_age < 0:
            raise ValueError("cache age cannot be negative")

    def to_dict(self, *, public: bool = False) -> dict[str, object]:
        payload = asdict(self)
        payload["status"] = self.status.value
        payload["url_or_external_id"] = redact_endpoint(self.url_or_external_id)
        payload["raw_excerpt"] = (
            "<redacted>"
            if self.sensitive and self.raw_excerpt
            else redact_public_value(self.raw_excerpt, max_length=1200)
        )
        payload["normalized_excerpt"] = (
            "<redacted>"
            if self.sensitive and self.normalized_excerpt
            else redact_public_value(self.normalized_excerpt, max_length=1200)
        )
        payload["provenance"] = [
            (key, redact_public_value(value, max_length=240))
            for key, value in self.provenance
            if not _SECRET_KEY.search(key)
        ]
        if public:
            payload.pop("raw_excerpt", None)
            payload["normalized_excerpt"] = redact_public_value(
                self.normalized_excerpt, max_length=700
            )
        return payload


@dataclass(frozen=True, slots=True)
class ConnectorExecutionResult:
    event: RetrievalEvent
    documents: tuple[RetrievedDocument, ...] = ()
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    partial: bool = False
    retryable: bool = False
    fallback_used: bool = False

    def __post_init__(self) -> None:
        accepted = sum(not document.rejected for document in self.documents)
        rejected = sum(document.rejected for document in self.documents)
        if self.event.accepted_count != accepted or self.event.rejected_count != rejected:
            raise ValueError("event and document acceptance counters differ")
        if self.event.result_count != len(self.documents):
            raise ValueError("event result_count must match normalized documents")
        if any(document.event_id != self.event.event_id for document in self.documents):
            raise ValueError("every document must reference the result event")
        if self.event.status is RetrievalStatus.LIVE_RESULT_OBTAINED and any(
            document.status is not RetrievalStatus.LIVE_RESULT_OBTAINED
            for document in self.documents
            if not document.rejected
        ):
            raise ValueError("live results cannot contain a disguised cache or fixture")

    def to_dict(self, *, public: bool = False) -> dict[str, object]:
        return {
            "event": (
                self.event.redacted().to_public_dict()
                if public
                else self.event.redacted().to_dict()
            ),
            "documents": [item.to_dict(public=public) for item in self.documents],
            "warnings": [
                redact_public_value(item, max_length=240) for item in self.warnings
            ],
            "errors": [redact_public_value(item, max_length=240) for item in self.errors],
            "partial": self.partial,
            "retryable": self.retryable,
            "fallback_used": self.fallback_used,
        }


@dataclass(frozen=True, slots=True)
class ConnectorExecutionSummary:
    case_session_id: str
    plan_id: str
    total_queries: int
    executed_queries: int
    blocked_queries: int
    skipped_queries: int
    live_calls_attempted: int
    live_calls_succeeded: int
    live_calls_failed: int
    cache_results: int
    local_results: int
    fixture_results: int
    metadata_only_results: int
    unavailable_connectors: tuple[str, ...]
    unconfigured_connectors: tuple[str, ...]
    unsupported_sources: tuple[str, ...]
    events: tuple[RetrievalEvent, ...]
    documents: tuple[RetrievedDocument, ...] = ()
    duplicate_calls_avoided: int = 0

    def __post_init__(self) -> None:
        counters = (
            self.total_queries,
            self.executed_queries,
            self.blocked_queries,
            self.skipped_queries,
            self.live_calls_attempted,
            self.live_calls_succeeded,
            self.live_calls_failed,
            self.cache_results,
            self.local_results,
            self.fixture_results,
            self.metadata_only_results,
            self.duplicate_calls_avoided,
        )
        if min(counters, default=0) < 0:
            raise ValueError("summary counters cannot be negative")

    def to_dict(self, *, public: bool = False) -> dict[str, object]:
        if public:
            return {
                "title": "Recherches effectuées",
                "total_queries": self.total_queries,
                "executed_queries": self.executed_queries,
                "blocked_queries": self.blocked_queries,
                "skipped_queries": self.skipped_queries,
                "sources": [event.redacted().to_public_dict() for event in self.events],
            }
        payload = asdict(self)
        payload["events"] = [event.redacted().to_dict() for event in self.events]
        payload["documents"] = [document.to_dict() for document in self.documents]
        return payload


__all__ = (
    "ConnectorExecutionResult",
    "ConnectorExecutionSummary",
    "ConnectorKind",
    "LIVE_STATUSES",
    "RESULT_STATUSES",
    "RetrievalEvent",
    "RetrievalStatus",
    "RetrievedDocument",
    "TRACE_VERSION",
    "redact_endpoint",
    "redact_mapping",
    "redact_public_value",
)
