"""Truthful, deterministic coordination of planned source retrievals."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
from importlib import import_module
import os
from pathlib import Path
import sys
from time import monotonic
from typing import Any, Protocol
import unicodedata
from urllib.parse import urlsplit

from .legal_issue_models import (
    PlanningStatus,
    ResearchPlan,
    ResearchQuery,
    ResearchTarget,
    SourceFamily,
)
from .retrieval_models import (
    ConnectorExecutionResult,
    ConnectorExecutionSummary,
    ConnectorKind,
    RetrievalEvent,
    RetrievalStatus,
    RetrievedDocument,
    TRACE_VERSION,
    redact_public_value,
)
from .cse_models import MeetingBody
from .cse_search import CSECSSCTSearchEngine


ERROR_MESSAGES = {
    "CONNECTOR_NOT_CONFIGURED": "Connecteur non configuré.",
    "CONNECTOR_TIMEOUT": "Le connecteur n’a pas répondu dans le délai prévu.",
    "NETWORK_UNAVAILABLE": "Le réseau est indisponible pour cette source.",
    "AUTHENTICATION_FAILED": "L’authentification de la source a échoué.",
    "RATE_LIMITED": "La source limite temporairement les requêtes.",
    "INVALID_RESPONSE": "La réponse de la source est inexploitable.",
    "CACHE_CORRUPTED": "Le cache de cette source est inexploitable.",
    "UNSUPPORTED_QUERY": "Cette recherche n’est pas prise en charge.",
    "NO_RELEVANT_RESULT": "Aucun résultat pertinent n’a été retenu.",
}


class ConnectorAuthenticationError(RuntimeError):
    """A connector rejected or cannot perform authentication."""


class ConnectorRateLimitError(RuntimeError):
    """A connector explicitly reported a rate limit."""


class ConnectorCacheCorruptedError(RuntimeError):
    """A connector found a cache entry that cannot be decoded or trusted."""

LOCAL_FAMILIES = frozenset(
    {
        SourceFamily.INEOS_AGREEMENT,
        SourceFamily.INEOS_INTERNAL_RULE,
        SourceFamily.INEOS_PROCEDURE,
        SourceFamily.INTERNAL_PRACTICE,
        SourceFamily.EMPLOYMENT_CONTRACT,
    }
)
UNSUPPORTED_IN_THIS_LOT: frozenset[SourceFamily] = frozenset()


def _stable(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(str(part) for part in parts).encode()).hexdigest()[:24]
    return f"retrieval-{prefix}-{digest}"


def _normalize(text: object) -> str:
    value = unicodedata.normalize("NFKD", str(text or ""))
    return " ".join(
        "".join(char for char in value if not unicodedata.combining(char))
        .lower()
        .replace("’", " ")
        .replace("'", " ")
        .split()
    )


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _script_module(name: str):
    scripts = str(Path(__file__).resolve().parents[1] / "automation" / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    return import_module(f"automation.scripts.{name}")


def _any_complete_credentials(pairs: Sequence[tuple[str, str]]) -> bool:
    return any(
        bool(os.environ.get(client_id, "").strip())
        and bool(os.environ.get(client_secret, "").strip())
        for client_id, client_secret in pairs
    )


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    case_session_id: str
    plan_id: str
    plan_version: str
    allow_network: bool = False
    allow_stale_cache: bool = True
    fixture_mode: bool = False
    max_results: int = 8


@dataclass(frozen=True, slots=True)
class ConnectorConfiguration:
    configured: bool
    available: bool = True
    reason_code: str | None = None


class ConnectorExecutor(Protocol):
    connector_id: str
    connector_name: str
    connector_kind: ConnectorKind

    def can_handle(self, research_query: ResearchQuery, target: ResearchTarget) -> bool: ...

    def configuration_status(self) -> ConnectorConfiguration: ...

    def execute(
        self, research_query: ResearchQuery, target: ResearchTarget, context: ExecutionContext
    ) -> ConnectorExecutionResult: ...

    def healthcheck(self) -> Mapping[str, object]: ...

    def public_capabilities(self) -> Mapping[str, object]: ...

    def technical_capabilities(self) -> Mapping[str, object]: ...


class BaseConnectorExecutor:
    """Small base class shared by wrappers; it never performs implicit I/O."""

    connector_id = "unsupported"
    connector_name = "Source non supportée"
    connector_kind = ConnectorKind.UNSUPPORTED
    source_families: frozenset[SourceFamily] = frozenset()

    def can_handle(self, research_query: ResearchQuery, target: ResearchTarget) -> bool:
        del research_query
        return target.source_family in self.source_families

    def configuration_status(self) -> ConnectorConfiguration:
        return ConnectorConfiguration(True)

    def healthcheck(self) -> Mapping[str, object]:
        status = self.configuration_status()
        return {
            "connector_id": self.connector_id,
            "configured": status.configured,
            "available": status.available,
            "reason_code": status.reason_code,
        }

    def public_capabilities(self) -> Mapping[str, object]:
        return {
            "connector": self.connector_name,
            "kind": self.connector_kind.value,
            "source_families": tuple(sorted(item.value for item in self.source_families)),
        }

    def technical_capabilities(self) -> Mapping[str, object]:
        return {
            **self.public_capabilities(),
            "network_capable": self.connector_kind
            in {
                ConnectorKind.LIVE_API,
                ConnectorKind.LIVE_PUBLIC_WEB,
                ConnectorKind.CACHE_BACKED_API,
            },
        }


class CallableExecutionAdapter(BaseConnectorExecutor):
    """Adapter for a controlled transport returning normalized source mappings."""

    def __init__(
        self,
        *,
        connector_id: str,
        connector_name: str,
        connector_kind: ConnectorKind,
        source_families: Sequence[SourceFamily],
        transport: Callable[[ResearchQuery, ExecutionContext], Mapping[str, Any]],
        configured: Callable[[], bool] | bool = True,
    ) -> None:
        self.connector_id = connector_id
        self.connector_name = connector_name
        self.connector_kind = connector_kind
        self.source_families = frozenset(source_families)
        self._transport = transport
        self._configured = configured

    def configuration_status(self) -> ConnectorConfiguration:
        configured = self._configured() if callable(self._configured) else self._configured
        return ConnectorConfiguration(
            bool(configured),
            bool(configured),
            None if configured else "CONNECTOR_NOT_CONFIGURED",
        )

    def execute(self, query, target, context) -> ConnectorExecutionResult:
        started = _utc_now()
        timer = monotonic()
        config = self.configuration_status()
        if not config.configured:
            return self._empty(
                query,
                target,
                context,
                started,
                timer,
                RetrievalStatus.CONNECTOR_NOT_CONFIGURED,
                "CONNECTOR_NOT_CONFIGURED",
            )
        if not config.available:
            return self._empty(
                query,
                target,
                context,
                started,
                timer,
                RetrievalStatus.CONNECTOR_UNAVAILABLE,
                config.reason_code or "CONNECTOR_UNAVAILABLE",
            )
        if (
            self.connector_kind
            in {
                ConnectorKind.LIVE_API,
                ConnectorKind.LIVE_PUBLIC_WEB,
                ConnectorKind.CACHE_BACKED_API,
            }
            and not context.allow_network
        ):
            return self._empty(
                query,
                target,
                context,
                started,
                timer,
                RetrievalStatus.CONNECTOR_UNAVAILABLE,
                "NETWORK_UNAVAILABLE",
            )
        network_capable = self.connector_kind in {
            ConnectorKind.LIVE_API,
            ConnectorKind.LIVE_PUBLIC_WEB,
            ConnectorKind.CACHE_BACKED_API,
        }
        try:
            payload = self._transport(query, context)
        except ConnectorCacheCorruptedError:
            return self._empty(
                query,
                target,
                context,
                started,
                timer,
                RetrievalStatus.CONNECTOR_ERROR,
                "CACHE_CORRUPTED",
            )
        except ConnectorAuthenticationError:
            return self._empty(
                query,
                target,
                context,
                started,
                timer,
                RetrievalStatus.CONNECTOR_ERROR,
                "AUTHENTICATION_FAILED",
                live=network_capable,
            )
        except ConnectorRateLimitError:
            return self._empty(
                query,
                target,
                context,
                started,
                timer,
                RetrievalStatus.CONNECTOR_ERROR,
                "RATE_LIMITED",
                live=network_capable,
            )
        except TimeoutError:
            return self._empty(
                query,
                target,
                context,
                started,
                timer,
                RetrievalStatus.NETWORK_ERROR,
                "CONNECTOR_TIMEOUT",
                live=network_capable,
            )
        except (ConnectionError, OSError):
            return self._empty(
                query,
                target,
                context,
                started,
                timer,
                RetrievalStatus.NETWORK_ERROR,
                "NETWORK_UNAVAILABLE",
                live=network_capable,
            )
        except Exception:
            return self._empty(
                query,
                target,
                context,
                started,
                timer,
                RetrievalStatus.CONNECTOR_ERROR,
                "INVALID_RESPONSE",
                live=network_capable,
            )
        if not isinstance(payload, Mapping):
            return self._empty(
                query,
                target,
                context,
                started,
                timer,
                RetrievalStatus.CONNECTOR_ERROR,
                "INVALID_RESPONSE",
                live=network_capable,
            )
        return self._from_payload(query, target, context, payload, started, timer)

    def _from_payload(self, query, target, context, payload, started, timer):
        raw_items = payload.get("documents", payload.get("sources", ()))
        if not isinstance(raw_items, Sequence) or isinstance(raw_items, (str, bytes)):
            raw_items = ()
        origin = str(payload.get("origin") or "").upper()
        cache_hit = bool(payload.get("cache_hit")) or origin in {"CACHE", "STALE_CACHE"}
        stale = bool(payload.get("stale")) or origin == "STALE_CACHE"
        fixture = bool(payload.get("fixture")) or self.connector_kind is ConnectorKind.FIXTURE_PROVIDER
        metadata = bool(payload.get("metadata_only")) or self.connector_kind in {
            ConnectorKind.STATIC_CATALOG,
            ConnectorKind.METADATA_BRIDGE,
        }
        network_executed = bool(payload.get("network_call_executed"))

        if fixture and raw_items:
            status = RetrievalStatus.FIXTURE_RESULT
        elif cache_hit:
            status = (
                RetrievalStatus.STALE_CACHE_RESULT if stale else RetrievalStatus.CACHE_RESULT
            )
        elif metadata:
            status = RetrievalStatus.METADATA_ONLY
        elif self.connector_kind is ConnectorKind.LOCAL_INDEX and raw_items:
            status = RetrievalStatus.LOCAL_DOCUMENT
        elif self.connector_kind in {
            ConnectorKind.LOCAL_INDEX,
            ConnectorKind.FIXTURE_PROVIDER,
        }:
            status = RetrievalStatus.REJECTED_RESULT
        elif network_executed and raw_items:
            status = RetrievalStatus.LIVE_RESULT_OBTAINED
        elif network_executed:
            status = RetrievalStatus.LIVE_NO_RELEVANT_RESULT
        else:
            status = RetrievalStatus.CONNECTOR_ERROR

        event_id = _stable(
            "event",
            context.case_session_id,
            context.plan_version,
            query.query_id,
            self.connector_id,
        )
        documents = tuple(
            self._document(item, event_id, target, status, index)
            for index, item in enumerate(raw_items[: context.max_results])
            if isinstance(item, Mapping)
        )
        accepted = sum(not item.rejected for item in documents)
        if network_executed and not accepted:
            status = RetrievalStatus.LIVE_NO_RELEVANT_RESULT
            documents = tuple(replace(item, status=RetrievalStatus.REJECTED_RESULT) for item in documents)
        event = self._event(
            query,
            target,
            context,
            started,
            timer,
            status,
            result_count=len(documents),
            accepted=accepted,
            rejected=len(documents) - accepted,
            network=network_executed,
            cache_checked=bool(payload.get("cache_checked")) or self.connector_kind is ConnectorKind.CACHE_BACKED_API,
            cache_hit=cache_hit,
            fixture=fixture,
            metadata=metadata,
            endpoint=payload.get("endpoint_domain"),
            http_status=payload.get("http_status"),
            warnings=tuple(str(item) for item in payload.get("warnings", ())),
            error_code=(
                "NO_RELEVANT_RESULT"
                if status is RetrievalStatus.REJECTED_RESULT and not documents
                else None
            ),
            error_message=(
                ERROR_MESSAGES["NO_RELEVANT_RESULT"]
                if status is RetrievalStatus.REJECTED_RESULT and not documents
                else None
            ),
        )
        documents = tuple(replace(document, event_id=event.event_id) for document in documents)
        return ConnectorExecutionResult(
            event,
            documents,
            warnings=tuple(str(item) for item in payload.get("warnings", ())),
            partial=bool(payload.get("partial")),
            fallback_used=cache_hit and network_executed,
        )

    def _document(self, item, event_id, target, status, index):
        rejected = bool(item.get("rejected"))
        public_id = (
            item.get("official_id")
            or item.get("id")
            or item.get("external_id")
            or item.get("url")
            or item.get("url_or_id")
            or f"result-{index}"
        )
        document_status = RetrievalStatus.REJECTED_RESULT if rejected else status
        return RetrievedDocument(
            document_id=_stable("document", self.connector_id, str(public_id)),
            event_id=event_id,
            source_family=target.source_family.value,
            provider=self.connector_name,
            title=str(item.get("title") or item.get("document") or "Document sans titre"),
            public_reference=str(item.get("reference") or public_id),
            url_or_external_id=str(item.get("url") or item.get("url_or_id") or public_id),
            document_type=str(item.get("document_type") or item.get("type") or ""),
            date=str(item.get("date") or item.get("decision_date") or "") or None,
            version=str(item.get("version") or "") or None,
            jurisdiction=str(item.get("jurisdiction") or item.get("juridiction") or "") or None,
            court=str(item.get("court") or "") or None,
            chamber=str(item.get("chamber") or item.get("formation") or "") or None,
            case_number=str(item.get("case_number") or item.get("numero") or "") or None,
            article_number=str(item.get("article_number") or item.get("article") or "") or None,
            clause_number=str(item.get("clause_number") or item.get("clause") or "") or None,
            page=str(item.get("page") or "") or None,
            raw_excerpt=str(item.get("raw_excerpt") or item.get("excerpt") or "") or None,
            normalized_excerpt=str(
                item.get("normalized_excerpt") or item.get("excerpt") or ""
            ) or None,
            provenance=(("origin", status.value),),
            status=document_status,
            cache_age=int(item["cache_age"]) if item.get("cache_age") is not None else None,
            metadata_complete=bool(item.get("metadata_complete")),
            sensitive=bool(item.get("sensitive")),
            establishment_scope=query_scope(item.get("establishment_scope")),
            temporal_scope=query_scope(item.get("temporal_scope")),
            rejected=rejected,
            rejection_reasons=tuple(str(reason) for reason in item.get("rejection_reasons", ())),
        )

    def _empty(
        self,
        query,
        target,
        context,
        started,
        timer,
        status,
        error_code,
        *,
        live=False,
    ):
        event = self._event(
            query,
            target,
            context,
            started,
            timer,
            status,
            network=live,
            error_code=error_code,
            error_message=ERROR_MESSAGES.get(error_code, "Source indisponible."),
        )
        return ConnectorExecutionResult(
            event,
            errors=(error_code,),
            retryable=error_code
            in {"CONNECTOR_TIMEOUT", "NETWORK_UNAVAILABLE", "RATE_LIMITED"},
        )

    def _event(
        self,
        query,
        target,
        context,
        started,
        timer,
        status,
        *,
        result_count=0,
        accepted=0,
        rejected=0,
        network=False,
        cache_checked=False,
        cache_hit=False,
        fixture=False,
        metadata=False,
        endpoint=None,
        http_status=None,
        warnings=(),
        error_code=None,
        error_message=None,
    ):
        completed = _utc_now()
        return RetrievalEvent(
            event_id=_stable(
                "event",
                context.case_session_id,
                context.plan_version,
                query.query_id,
                self.connector_id,
            ),
            case_session_id=context.case_session_id,
            plan_id=context.plan_id,
            issue_id=query.issue_id,
            target_id=query.target_id,
            query_id=query.query_id,
            connector_id=self.connector_id,
            connector_name=self.connector_name,
            connector_kind=self.connector_kind,
            source_family=target.source_family.value,
            status=status,
            started_at=started.isoformat(),
            completed_at=completed.isoformat(),
            duration_ms=max(0, round((monotonic() - timer) * 1000)),
            live_call_attempted=network,
            network_call_executed=network,
            cache_checked=cache_checked,
            cache_hit=cache_hit,
            fixture_used=fixture,
            metadata_only=metadata,
            query_text=query.query_text,
            normalized_query=_normalize(query.query_text),
            endpoint_domain=_endpoint_domain(endpoint),
            http_status=int(http_status) if http_status is not None else None,
            result_count=result_count,
            accepted_count=accepted,
            rejected_count=rejected,
            warning_codes=tuple(warnings),
            error_code=error_code,
            error_message_public=redact_public_value(error_message),
            provenance=(("adapter", self.connector_id),),
            trace_version=TRACE_VERSION,
        )


def query_scope(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _endpoint_domain(value: object) -> str | None:
    if not value:
        return None
    parsed = urlsplit(str(value))
    return parsed.netloc or str(value).split("/")[0]


class LegifranceExecutionAdapter(CallableExecutionAdapter):
    def __init__(self, transport=None, configured=None):
        if transport is None:
            transport = self._live_transport
        if configured is None:
            configured = self._configured
        super().__init__(
            connector_id="legifrance",
            connector_name="Légifrance",
            connector_kind=ConnectorKind.CACHE_BACKED_API,
            source_families=(
                SourceFamily.LABOUR_CODE,
                SourceFamily.REGULATION,
                SourceFamily.CCNIC_IDCC_44,
            ),
            transport=transport,
            configured=configured,
        )

    @staticmethod
    def _configured():
        return _any_complete_credentials(
            (
                ("CFDT_NEXUS_LEGIFRANCE_CLIENT_ID", "CFDT_NEXUS_LEGIFRANCE_CLIENT_SECRET"),
                ("LEGIFRANCE_CLIENT_ID", "LEGIFRANCE_CLIENT_SECRET"),
                ("PISTE_CLIENT_ID", "PISTE_CLIENT_SECRET"),
            )
        )

    @staticmethod
    def _live_transport(query, context):
        client = _script_module("legifrance_connector").LegifranceClient()
        counters = _instrument_client(client, "_post_json", "_read_response_cache")
        payload = (
            client.search_idcc_sources("44", query.query_text, context.max_results)
            if "COLLECTIVE_AGREEMENT" in query.document_types
            else client.search_code_sources(query.query_text, context.max_results)
        )
        return _legacy_payload(payload, "api.piste.gouv.fr", counters)


class JudilibreExecutionAdapter(CallableExecutionAdapter):
    def __init__(self, transport=None, configured=None):
        if transport is None:
            transport = self._live_transport
        if configured is None:
            configured = self._configured
        super().__init__(
            connector_id="judilibre",
            connector_name="JUDILIBRE",
            connector_kind=ConnectorKind.CACHE_BACKED_API,
            source_families=(SourceFamily.CASE_LAW,),
            transport=transport,
            configured=configured,
        )

    @staticmethod
    def _configured():
        return _any_complete_credentials(
            (
                ("CFDT_NEXUS_JUDILIBRE_CLIENT_ID", "CFDT_NEXUS_JUDILIBRE_CLIENT_SECRET"),
                ("JUDILIBRE_CLIENT_ID", "JUDILIBRE_CLIENT_SECRET"),
                ("CFDT_NEXUS_LEGIFRANCE_CLIENT_ID", "CFDT_NEXUS_LEGIFRANCE_CLIENT_SECRET"),
                ("PISTE_CLIENT_ID", "PISTE_CLIENT_SECRET"),
            )
        )

    @staticmethod
    def _live_transport(query, context):
        client = _script_module("judilibre_connector").JudilibreClient()
        counters = _instrument_client(client, "_get_json", "_read_response_cache")
        payload = client.search_sources(query.query_text, context.max_results)
        return _legacy_payload(payload, "api.piste.gouv.fr", counters)


class CdtnExecutionAdapter(CallableExecutionAdapter):
    def __init__(self, transport=None):
        super().__init__(
            connector_id="cdtn",
            connector_name="Code du travail numérique",
            connector_kind=ConnectorKind.LIVE_PUBLIC_WEB,
            source_families=(SourceFamily.OFFICIAL_GUIDANCE,),
            transport=transport or self._live_transport,
            configured=True,
        )

    def can_handle(self, query, target):
        if target.source_family is not SourceFamily.OFFICIAL_GUIDANCE:
            return False
        text = _normalize(" ".join((query.query_text, *query.concepts)))
        specialized = (
            "cnil",
            "donnee personnelle",
            "badge",
            "epi",
            "prevention",
            "risque",
            "securite",
            "carsat",
            "inrs",
            "anact",
        )
        return not any(marker in text for marker in specialized)

    @staticmethod
    def _live_transport(query, context):
        client = _script_module("cdtn_connector").CdtnClient()
        counters = _instrument_client(client, "_get_json", "read_response_cache")
        payload = client.search_sources(query.query_text, limit=context.max_results)
        return _legacy_payload(payload, "code.travail.gouv.fr", counters)


class LocalCorpusExecutionAdapter(CallableExecutionAdapter):
    def __init__(self, transport, *, connector_id="local-corpus", connector_name="Corpus local"):
        super().__init__(
            connector_id=connector_id,
            connector_name=connector_name,
            connector_kind=ConnectorKind.LOCAL_INDEX,
            source_families=tuple(LOCAL_FAMILIES),
            transport=transport,
            configured=True,
        )


class CSECSSCTExecutionAdapter(BaseConnectorExecutor):
    """LOT 3-compatible, network-free adapter for indexed meeting minutes."""

    connector_id = "cse-cssct-local-index"
    connector_name = "PV CSE/CSSCT"
    connector_kind = ConnectorKind.LOCAL_INDEX
    source_families = frozenset(
        {
            SourceFamily.CSE_MINUTES,
            SourceFamily.CSSCT_MINUTES,
            SourceFamily.INTERNAL_PRACTICE,
        }
    )

    def __init__(self, processed_root: Path | str | None) -> None:
        self._engine = CSECSSCTSearchEngine(processed_root)

    def configuration_status(self) -> ConnectorConfiguration:
        available = self._engine.inventory().root_status in {"AVAILABLE", "PARTIAL"}
        return ConnectorConfiguration(
            configured=available,
            available=available,
            reason_code=None if available else "CORPUS_NOT_CONFIGURED",
        )

    def can_handle(self, query: ResearchQuery, target: ResearchTarget) -> bool:
        del query
        return target.source_family in self.source_families

    def execute(self, query, target, context) -> ConnectorExecutionResult:
        body_scope = {
            SourceFamily.CSE_MINUTES: (MeetingBody.CSE, MeetingBody.CE),
            SourceFamily.CSSCT_MINUTES: (MeetingBody.CSSCT, MeetingBody.CHSCT),
            SourceFamily.INTERNAL_PRACTICE: (
                MeetingBody.CSE,
                MeetingBody.CSSCT,
                MeetingBody.CE,
                MeetingBody.CHSCT,
                MeetingBody.COMMISSION,
                MeetingBody.JOINT_MEETING,
                MeetingBody.UNKNOWN,
            ),
        }[target.source_family]
        pv_query = self._engine.from_research_query(
            query,
            case_session_id=context.case_session_id,
            body_scope=body_scope,
            max_results=context.max_results,
        )
        execution = self._engine.search(pv_query)
        event_id = _stable(
            "event", context.case_session_id, context.plan_version,
            query.query_id, self.connector_id,
        )
        documents = tuple(
            RetrievedDocument(
                document_id=_stable("document", passage.passage_id),
                event_id=event_id,
                source_family=target.source_family.value,
                provider=self.connector_name,
                title=next(
                    (
                        document.public_title
                        for document in execution.documents
                        if document.document_id == passage.document_id
                    ),
                    f"{passage.meeting_body.value} {passage.meeting_date or 'date non établie'}",
                ),
                public_reference=(
                    f"{passage.meeting_body.value} — "
                    f"{passage.meeting_date or 'date non établie'} — {passage.page}"
                ),
                document_type="meeting_minutes",
                date=passage.meeting_date,
                page=passage.page,
                raw_excerpt=passage.raw_text,
                normalized_excerpt=passage.excerpt,
                provenance=(
                    ("passage_nature", passage.passage_nature.value),
                    ("speaker_role", passage.speaker_role.value),
                    ("qualification_reason", passage.qualification_reason),
                    ("legal_value", passage.legal_value),
                    ("proves", passage.proves),
                    ("does_not_prove", passage.does_not_prove),
                    ("final_score", str(passage.final_score)),
                ),
                status=RetrievalStatus.LOCAL_DOCUMENT,
                metadata_complete=bool(passage.meeting_date),
                sensitive=False,
                establishment_scope=query.establishment_scope,
                temporal_scope=query.temporal_scope,
            )
            for passage in execution.results
        )
        stamp_started = execution.started_at
        stamp_completed = execution.completed_at
        if execution.corpus_root_status not in {"AVAILABLE", "PARTIAL"}:
            status = RetrievalStatus.CONNECTOR_NOT_CONFIGURED
            error_code = "CORPUS_NOT_CONFIGURED"
            error_message = "Corpus CSE/CSSCT non configuré."
        elif documents:
            status = RetrievalStatus.LOCAL_DOCUMENT
            error_code = None
            error_message = None
        else:
            status = RetrievalStatus.REJECTED_RESULT
            error_code = "NO_RELEVANT_RESULT"
            error_message = (
                "Aucun passage suffisamment pertinent retrouvé. Cette absence ne "
                "prouve pas une absence d’information ou de consultation."
            )
        event = RetrievalEvent(
            event_id=event_id,
            case_session_id=context.case_session_id,
            plan_id=context.plan_id,
            issue_id=query.issue_id,
            target_id=query.target_id,
            query_id=query.query_id,
            connector_id=self.connector_id,
            connector_name=self.connector_name,
            connector_kind=self.connector_kind,
            source_family=target.source_family.value,
            status=status,
            started_at=stamp_started,
            completed_at=stamp_completed,
            duration_ms=execution.duration_ms,
            live_call_attempted=False,
            network_call_executed=False,
            cache_checked=False,
            cache_hit=False,
            fixture_used=False,
            metadata_only=False,
            query_text=query.query_text,
            normalized_query=_normalize(query.query_text),
            endpoint_domain=None,
            http_status=None,
            result_count=len(documents),
            accepted_count=len(documents),
            rejected_count=0,
            warning_codes=tuple(execution.warnings),
            error_code=error_code,
            error_message_public=error_message,
            provenance=(
                ("documents_available", str(execution.documents_available)),
                ("documents_scanned", str(execution.documents_scanned)),
                ("chunks_scanned", str(execution.chunks_scanned)),
                ("passages_matched", str(execution.passages_matched)),
                ("passages_retained", str(execution.passages_retained)),
                ("search_mode", execution.search_mode.value),
                ("rejected_reasons", repr(execution.rejected_reasons)),
            ),
        )
        return ConnectorExecutionResult(
            event,
            documents,
            warnings=execution.warnings,
            errors=execution.errors,
            fallback_used=status in {
                RetrievalStatus.CONNECTOR_NOT_CONFIGURED,
                RetrievalStatus.REJECTED_RESULT,
            },
        )

    def public_capabilities(self) -> Mapping[str, object]:
        inventory = self._engine.inventory()
        return {
            **super().public_capabilities(),
            "network_required": False,
            "search_mode": "HYBRID_LOCAL",
            "corpus": inventory.to_public_dict(),
            "legal_scope": "Les PV apportent du contexte et ne sont pas des normes juridiques.",
        }


class MetadataOnlyExecutionAdapter(CallableExecutionAdapter):
    def __init__(
        self,
        connector_id: str,
        connector_name: str,
        catalog: Sequence[Mapping[str, object]],
        *,
        matcher: Callable[[ResearchQuery], bool],
        source_families: Sequence[SourceFamily] = (SourceFamily.OFFICIAL_GUIDANCE,),
    ):
        self._catalog = tuple(catalog)
        self._matcher = matcher
        super().__init__(
            connector_id=connector_id,
            connector_name=connector_name,
            connector_kind=ConnectorKind.STATIC_CATALOG,
            source_families=source_families,
            transport=self._catalog_transport,
            configured=True,
        )

    def can_handle(self, query, target):
        return target.source_family in self.source_families and self._matcher(query)

    def _catalog_transport(self, query, context):
        del query
        return {
            "documents": self._catalog[: context.max_results],
            "metadata_only": True,
            "network_call_executed": False,
        }


class SourceExecutionCoordinator:
    """Execute a plan once per query/connector and preserve source-local failures."""

    def __init__(self, executors: Sequence[ConnectorExecutor]) -> None:
        ids = [executor.connector_id for executor in executors]
        if len(ids) != len(set(ids)):
            raise ValueError("connector identifiers must be unique")
        self._executors = tuple(executors)
        self._results: dict[tuple[str, str, str, str], ConnectorExecutionResult] = {}

    def execute(
        self,
        plan: ResearchPlan,
        *,
        allow_network: bool = False,
        allow_stale_cache: bool = True,
        fixture_mode: bool = False,
    ) -> ConnectorExecutionSummary:
        context = ExecutionContext(
            plan.case_session_id,
            plan.plan_id,
            plan.version,
            allow_network,
            allow_stale_cache,
            fixture_mode,
        )
        target_by_id = {target.target_id: target for target in plan.targets}
        excluded = {
            (item.issue_id, item.source_family)
            for item in plan.exclusions
            if item.issue_id is not None
        }
        events: list[RetrievalEvent] = []
        documents: list[RetrievedDocument] = []
        duplicates = 0
        for query in sorted(plan.queries, key=lambda item: (item.priority, item.query_id)):
            target = target_by_id[query.target_id]
            if (query.issue_id, target.source_family) in excluded:
                events.append(self._status_event(plan, query, target, RetrievalStatus.SKIPPED_NOT_RELEVANT))
                continue
            if target.source_family in UNSUPPORTED_IN_THIS_LOT:
                events.append(self._status_event(plan, query, target, RetrievalStatus.UNSUPPORTED_SOURCE))
                continue
            executors = tuple(
                candidate
                for candidate in self._executors
                if candidate.can_handle(query, target)
            )
            if not executors:
                events.append(self._status_event(plan, query, target, RetrievalStatus.UNSUPPORTED_SOURCE))
                continue
            for executor in executors:
                key = (plan.case_session_id, query.query_id, executor.connector_id, plan.version)
                if key in self._results:
                    result = self._results[key]
                    duplicates += 1
                else:
                    result = executor.execute(query, target, context)
                    self._results[key] = result
                events.append(result.event)
                documents.extend(result.documents)
        blocked_events = tuple(
            self._status_event(
                plan,
                query,
                target_by_id[query.target_id],
                RetrievalStatus.BLOCKED_BY_MISSING_FACTS,
            )
            for query in plan.blocked_queries
        )
        events.extend(blocked_events)
        return self._summary(plan, events, documents, duplicates)

    @staticmethod
    def _status_event(plan, query, target, status):
        stamp = _utc_now().isoformat()
        connector_id = {
            RetrievalStatus.BLOCKED_BY_MISSING_FACTS: "not-executed",
            RetrievalStatus.SKIPPED_NOT_RELEVANT: "excluded",
        }.get(status, "unsupported")
        return RetrievalEvent(
            event_id=_stable("event", plan.case_session_id, plan.version, query.query_id, connector_id),
            case_session_id=plan.case_session_id,
            plan_id=plan.plan_id,
            issue_id=query.issue_id,
            target_id=query.target_id,
            query_id=query.query_id,
            connector_id=connector_id,
            connector_name="Aucun connecteur exécuté",
            connector_kind=ConnectorKind.UNSUPPORTED,
            source_family=target.source_family.value,
            status=status,
            started_at=stamp,
            completed_at=stamp,
            duration_ms=0,
            live_call_attempted=False,
            network_call_executed=False,
            cache_checked=False,
            cache_hit=False,
            fixture_used=False,
            metadata_only=False,
            query_text=query.query_text,
            normalized_query=_normalize(query.query_text),
            endpoint_domain=None,
            http_status=None,
            result_count=0,
            accepted_count=0,
            rejected_count=0,
            warning_codes=(),
            error_code=status.value,
            error_message_public=(
                "Recherche suspendue : informations manquantes."
                if status is RetrievalStatus.BLOCKED_BY_MISSING_FACTS
                else "Source non exécutée dans ce lot."
            ),
        )

    @staticmethod
    def _summary(plan, events, documents, duplicates):
        live_attempts = sum(event.network_call_executed for event in events)
        live_success = sum(
            event.status is RetrievalStatus.LIVE_RESULT_OBTAINED for event in events
        )
        unavailable = tuple(
            sorted(
                {
                    event.connector_id
                    for event in events
                    if event.status
                    in {RetrievalStatus.CONNECTOR_UNAVAILABLE, RetrievalStatus.NETWORK_ERROR}
                }
            )
        )
        unconfigured = tuple(
            sorted(
                {
                    event.connector_id
                    for event in events
                    if event.status is RetrievalStatus.CONNECTOR_NOT_CONFIGURED
                }
            )
        )
        unsupported = tuple(
            sorted(
                {
                    event.source_family
                    for event in events
                    if event.status is RetrievalStatus.UNSUPPORTED_SOURCE
                }
            )
        )
        return ConnectorExecutionSummary(
            case_session_id=plan.case_session_id,
            plan_id=plan.plan_id,
            total_queries=len(plan.queries) + len(plan.blocked_queries),
            executed_queries=len(
                {
                    event.query_id
                    for event in events
                    if event.status
                    not in {
                        RetrievalStatus.BLOCKED_BY_MISSING_FACTS,
                        RetrievalStatus.SKIPPED_NOT_RELEVANT,
                        RetrievalStatus.UNSUPPORTED_SOURCE,
                    }
                }
            ),
            blocked_queries=len(plan.blocked_queries),
            skipped_queries=len(
                {
                    event.query_id
                    for event in events
                    if event.status
                    in {
                        RetrievalStatus.SKIPPED_NOT_RELEVANT,
                        RetrievalStatus.UNSUPPORTED_SOURCE,
                    }
                }
            ),
            live_calls_attempted=live_attempts,
            live_calls_succeeded=live_success,
            live_calls_failed=live_attempts - live_success,
            cache_results=sum(
                event.status
                in {RetrievalStatus.CACHE_RESULT, RetrievalStatus.STALE_CACHE_RESULT}
                for event in events
            ),
            local_results=sum(
                event.status is RetrievalStatus.LOCAL_DOCUMENT for event in events
            ),
            fixture_results=sum(
                event.status is RetrievalStatus.FIXTURE_RESULT for event in events
            ),
            metadata_only_results=sum(
                event.status in {RetrievalStatus.METADATA_ONLY, RetrievalStatus.TITLE_ONLY}
                for event in events
            ),
            unavailable_connectors=unavailable,
            unconfigured_connectors=unconfigured,
            unsupported_sources=unsupported,
            events=tuple(events),
            documents=tuple(documents),
            duplicate_calls_avoided=duplicates,
        )


def _instrument_client(client: object, network_method: str, cache_method: str) -> dict[str, int]:
    """Observe a legacy client instance without changing its implementation."""

    counters = {"network_calls": 0, "cache_checks": 0, "cache_hits": 0}
    original_network = getattr(client, network_method)
    original_cache = getattr(client, cache_method)

    def observed_network(*args, **kwargs):
        counters["network_calls"] += 1
        return original_network(*args, **kwargs)

    def observed_cache(*args, **kwargs):
        counters["cache_checks"] += 1
        value = original_cache(*args, **kwargs)
        if value is not None:
            counters["cache_hits"] += 1
        return value

    setattr(client, network_method, observed_network)
    setattr(client, cache_method, observed_cache)
    return counters


def _legacy_payload(
    payload: Mapping[str, Any],
    endpoint: str,
    counters: Mapping[str, int] | None = None,
) -> Mapping[str, Any]:
    sources = payload.get("sources", ())
    audit = payload.get("audit", {}) if isinstance(payload.get("audit"), Mapping) else {}
    counters = counters or {}
    cache = bool(
        payload.get("cache_used")
        or audit.get("cache_used")
        or counters.get("cache_hits")
    )
    stale = bool(payload.get("stale_cache") or audit.get("stale_cache"))
    network = bool(
        payload.get("network_call_executed")
        or audit.get("network_call_executed")
        or counters.get("network_calls")
    )
    return {
        "documents": sources if isinstance(sources, Sequence) else (),
        "cache_checked": bool(counters.get("cache_checks")) or cache,
        "cache_hit": cache,
        "stale": stale,
        "network_call_executed": network,
        "endpoint_domain": endpoint,
        "http_status": (
            payload.get("http_status")
            or audit.get("http_status")
            or (200 if network else None)
        ),
        "warnings": payload.get("warnings", ()),
    }


def default_metadata_executors(
    catalogs: Mapping[str, Sequence[Mapping[str, object]]] | None = None,
) -> tuple[MetadataOnlyExecutionAdapter, ...]:
    """Build honest catalog wrappers; an absent catalog yields no fabricated source."""

    catalogs = catalogs or {}
    def contains(*markers: str):
        return lambda query: any(
            item in _normalize(" ".join((query.query_text, *query.concepts)))
            for item in markers
        )

    definitions = {
        "cnil": ("CNIL", (SourceFamily.OFFICIAL_GUIDANCE,), contains(
            "badge", "donnee", "surveillance", "preuve numerique"
        )),
        "carsat": ("CARSAT", (SourceFamily.OFFICIAL_GUIDANCE,), contains(
            "prevention", "risque", "epi", "securite"
        )),
        "inrs": ("INRS", (SourceFamily.OFFICIAL_GUIDANCE,), contains(
            "prevention", "risque", "epi", "securite"
        )),
        "anact": ("ANACT", (SourceFamily.OFFICIAL_GUIDANCE,), contains(
            "organisation", "charge", "fatigue", "psychosoc"
        )),
        "dreets_grand_est": ("DREETS Grand Est", (SourceFamily.OFFICIAL_GUIDANCE,), contains(
            "inspection du travail", "grand est", "dreets"
        )),
        "france_chimie": ("France Chimie", (SourceFamily.CCNIC_IDCC_44,), contains(
            "chimie", "idcc 44", "convention collective"
        )),
        "assurance_maladie": ("Assurance Maladie", (SourceFamily.OFFICIAL_GUIDANCE,), contains(
            "arret maladie", "ijss", "at/mp", "invalidite", "maternite", "cpam"
        )),
        "service_public": ("Service-Public", (SourceFamily.OFFICIAL_GUIDANCE,), contains(
            "demarche", "formalite", "service public"
        )),
        "ministere_travail": ("Ministère du Travail", (SourceFamily.OFFICIAL_GUIDANCE,), contains(
            "procedure officielle", "ministere du travail", "fiche pratique"
        )),
        "defenseur_droits": ("Défenseur des droits", (SourceFamily.OFFICIAL_GUIDANCE,), contains(
            "discrimination", "harcelement", "handicap", "lanceur d alerte"
        )),
        "urssaf": ("URSSAF", (SourceFamily.OFFICIAL_GUIDANCE,), contains(
            "cotisation", "exoneration", "assiette", "avantage en nature"
        )),
        "agirc_arrco": ("Agirc-Arrco", (SourceFamily.OFFICIAL_GUIDANCE,), contains(
            "retraite complementaire", "points agirc", "agirc arrco"
        )),
        "droit_local": ("Droit local Alsace-Moselle", (SourceFamily.REGULATION,), contains(
            "alsace moselle", "droit local", "moselle"
        )),
    }
    return tuple(
        MetadataOnlyExecutionAdapter(
            key,
            name,
            catalogs.get(key, ()),
            matcher=matcher,
            source_families=families,
        )
        for key, (name, families, matcher) in definitions.items()
    )


def build_default_executors(
    *,
    catalogs: Mapping[str, Sequence[Mapping[str, object]]] | None = None,
    local_transport: Callable[[ResearchQuery, ExecutionContext], Mapping[str, Any]] | None = None,
    cse_processed_root: Path | str | None = None,
) -> tuple[ConnectorExecutor, ...]:
    """Return wrappers for existing sources without enabling any network call."""

    executors: list[ConnectorExecutor] = [
        LegifranceExecutionAdapter(),
        JudilibreExecutionAdapter(),
        CdtnExecutionAdapter(),
        *default_metadata_executors(catalogs),
    ]
    if cse_processed_root is not None:
        executors.insert(0, CSECSSCTExecutionAdapter(cse_processed_root))
    if local_transport is not None:
        executors.insert(0, LocalCorpusExecutionAdapter(local_transport))
    return tuple(executors)


__all__ = (
    "BaseConnectorExecutor",
    "CallableExecutionAdapter",
    "CdtnExecutionAdapter",
    "CSECSSCTExecutionAdapter",
    "ConnectorConfiguration",
    "ConnectorAuthenticationError",
    "ConnectorCacheCorruptedError",
    "ConnectorExecutor",
    "ConnectorRateLimitError",
    "ExecutionContext",
    "JudilibreExecutionAdapter",
    "LegifranceExecutionAdapter",
    "LocalCorpusExecutionAdapter",
    "MetadataOnlyExecutionAdapter",
    "SourceExecutionCoordinator",
    "build_default_executors",
    "default_metadata_executors",
)
