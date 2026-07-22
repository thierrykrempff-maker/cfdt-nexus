"""Offline Runtime bridge for existing, activable official connectors.

Only metadata already present in the router answer is supplied to connector
public APIs.  This module performs no discovery transport and retains no data.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timezone
import hashlib
import time
from typing import Any, Callable

from automation.official_knowledge.connectors.cnil import CnilConnector, CnilDiscoveryEntry
from automation.official_knowledge.connectors.dreets_grand_est.dreets_connector import (
    DreetsGrandEstConnector,
)
from automation.official_knowledge.connectors.dreets_grand_est import DreetsDiscoveryItem
from automation.official_knowledge.connectors.inrs import InrsConnector
from automation.official_knowledge.document_registry import stable_document_id
from NEXUS_ADAPTERS.connectors import (
    ConnectorAdapterInput,
    ConnectorCapability,
    ConnectorDescriptor,
    ConnectorDocumentSnapshot,
    ConnectorQuerySnapshot,
    ConnectorResponseSnapshot,
    ConnectorResponseStatus,
    ConnectorSourceCategory,
    ConnectorSourceSnapshot,
)

from .config import RuntimeOfficialConnectorsConfig


_SUPPORTED = frozenset({"cnil", "dreets_grand_est", "inrs"})
_SOURCE_DETAILS = {
    "cnil": ("CNIL", ConnectorSourceCategory.INDEPENDENT_AUTHORITY, "https://cnil.fr"),
    "dreets_grand_est": (
        "DREETS_GRAND_EST",
        ConnectorSourceCategory.ADMINISTRATIVE_DOCTRINE,
        "https://grand-est.dreets.gouv.fr",
    ),
    "inrs": ("INRS", ConnectorSourceCategory.OTHER_OFFICIAL, "https://www.inrs.fr"),
}


def _stable(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:24]
    return f"runtime-official-{prefix}-{digest}"


@dataclass(frozen=True, slots=True)
class RuntimeOfficialConnectorsDiagnostics:
    connector_runtime_called: bool = False
    connector_runtime_ms: int = 0
    connectors_used: tuple[str, ...] = ()
    connector_runtime_fallback: str | None = None

    def __post_init__(self) -> None:
        if self.connector_runtime_ms < 0:
            raise ValueError("connector_runtime_ms must be non-negative")
        if tuple(sorted(set(self.connectors_used))) != self.connectors_used:
            raise ValueError("connectors_used must be unique and sorted")
        code = self.connector_runtime_fallback
        if code is not None and (not code or not code.replace("_", "").isalnum()):
            raise ValueError("connector_runtime_fallback must be a stable technical code")

    def to_dict(self) -> dict[str, object]:
        return {
            "connector_runtime_called": self.connector_runtime_called,
            "connector_runtime_ms": self.connector_runtime_ms,
            "connectors_used": list(self.connectors_used),
            "connector_runtime_fallback": self.connector_runtime_fallback,
        }


@dataclass(frozen=True, slots=True)
class RuntimeOfficialConnectorsResult:
    inputs: tuple[ConnectorAdapterInput, ...] = ()
    diagnostics: RuntimeOfficialConnectorsDiagnostics = RuntimeOfficialConnectorsDiagnostics()

    def to_dict(self) -> dict[str, object]:
        return {
            "diagnostics": self.diagnostics.to_dict(),
            "snapshot_count": sum(len(item.response.documents) for item in self.inputs),
        }


class RuntimeOfficialConnectorsIntegration:
    """Invoke only connector metadata APIs that are complete and locally injectable."""

    def __init__(
        self,
        config: RuntimeOfficialConnectorsConfig | None = None,
        *,
        clock: Callable[[], datetime] | None = None,
        timer: Callable[[], float] | None = None,
    ) -> None:
        self._config = config or RuntimeOfficialConnectorsConfig()
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._timer = timer or time.perf_counter

    def integrate(self, answer: Mapping[str, Any]) -> RuntimeOfficialConnectorsResult:
        if not self._config.enabled:
            return RuntimeOfficialConnectorsResult()
        grouped = self._group_sources(answer)
        if not grouped:
            return RuntimeOfficialConnectorsResult()
        started = self._timer()
        try:
            inputs = tuple(
                self._connector_input(connector_id, grouped[connector_id], answer)
                for connector_id in sorted(grouped)
            )
            if not any(item.response.documents for item in inputs):
                return self._fallback("OFFICIAL_CONNECTORS_NO_RESULT", started)
            return RuntimeOfficialConnectorsResult(
                inputs,
                RuntimeOfficialConnectorsDiagnostics(
                    True,
                    self._duration(started),
                    tuple(item.descriptor.connector_id for item in inputs),
                ),
            )
        except Exception:
            return self._fallback("OFFICIAL_CONNECTOR_RUNTIME_FAILED", started)

    @staticmethod
    def _group_sources(answer: Mapping[str, Any]) -> dict[str, tuple[Mapping[str, Any], ...]]:
        if not isinstance(answer, Mapping):
            return {}
        sources = answer.get("sources", ())
        if not isinstance(sources, Sequence) or isinstance(sources, (str, bytes, bytearray)):
            return {}
        grouped: dict[str, list[Mapping[str, Any]]] = {}
        for source in sources:
            if not isinstance(source, Mapping):
                continue
            connector_id = str(
                source.get("origin") or source.get("connector_id") or source.get("source_id") or ""
            ).strip().lower()
            if connector_id in _SUPPORTED:
                grouped.setdefault(connector_id, []).append(source)
        return {key: tuple(value) for key, value in grouped.items()}

    def _connector_input(
        self,
        connector_id: str,
        sources: tuple[Mapping[str, Any], ...],
        answer: Mapping[str, Any],
    ) -> ConnectorAdapterInput:
        if len(sources) > self._config.max_documents_per_connector:
            raise ValueError("official connector quota exceeded")
        discovered_at = self._date_text(answer.get("generated_at"))
        if connector_id == "cnil":
            metadata = CnilConnector(
                enabled=True, limit=self._config.max_documents_per_connector
            ).discover_metadata(tuple(self._cnil_entry(item, discovered_at) for item in sources))
        elif connector_id == "dreets_grand_est":
            metadata = DreetsGrandEstConnector(
                metadata_discovery_enabled=True,
                discovery_quota=self._config.max_documents_per_connector,
            ).discover_metadata(
                tuple(self._dreets_entry(item) for item in sources), discovered_on=discovered_at
            )
        elif connector_id == "inrs":
            metadata = InrsConnector(
                enabled=True, limit=self._config.max_documents_per_connector
            ).discover_metadata(tuple(self._inrs_entry(item, discovered_at) for item in sources))
        else:  # pragma: no cover - guarded by _SUPPORTED
            raise ValueError("unsupported connector")
        documents = tuple(self._snapshot(connector_id, item) for item in metadata)
        label, category, official_url = _SOURCE_DETAILS[connector_id]
        acquired_at = self._datetime(answer.get("generated_at")) or self._clock()
        query = str(answer.get("query") or "")
        return ConnectorAdapterInput(
            ConnectorDescriptor(connector_id, "runtime-1.0", (ConnectorCapability.DOCUMENTS,)),
            ConnectorSourceSnapshot(connector_id, label, category, True, official_url),
            ConnectorQuerySnapshot(
                _stable("query", connector_id, query), "OFFICIAL_METADATA_ALREADY_DISCOVERED"
            ),
            ConnectorResponseSnapshot(
                _stable("response", connector_id, *(item.external_id or "" for item in documents)),
                ConnectorResponseStatus.SUCCEEDED if documents else ConnectorResponseStatus.EMPTY,
                documents,
                source_confidence=0.5,
            ),
            acquired_at,
        )

    @staticmethod
    def _cnil_entry(source: Mapping[str, Any], discovered_at: str) -> CnilDiscoveryEntry:
        return CnilDiscoveryEntry(
            url=str(source.get("canonical_url") or source.get("url") or source.get("url_or_id") or ""),
            title=str(source.get("title") or source.get("document") or ""),
            publication_date=source.get("publication_date") or source.get("date"),
            category=str(source.get("category") or "autre_publication_publique"),
            family=str(source.get("family") or "autre_publication_publique"),
            document_type=str(source.get("document_type") or "autre_publication_publique"),
            mime_type=str(source.get("mime_type") or ""),
            discovered_at=RuntimeOfficialConnectorsIntegration._date_text(
                source.get("discovered_at") or discovered_at
            ),
        )

    @staticmethod
    def _dreets_entry(source: Mapping[str, Any]) -> DreetsDiscoveryItem:
        return DreetsDiscoveryItem(
            url=str(source.get("canonical_url") or source.get("url") or source.get("url_or_id") or ""),
            title=str(source.get("title") or source.get("document") or ""),
            date=source.get("publication_date") or source.get("date"),
            category=str(source.get("category") or ""),
            family=str(source.get("family") or ""),
            document_type=str(source.get("document_type") or ""),
            mime_type=str(source.get("mime_type") or ""),
        )

    @staticmethod
    def _inrs_entry(source: Mapping[str, Any], discovered_at: str) -> Mapping[str, Any]:
        allowed = {
            "title", "document_type", "category", "family", "publication_date",
            "last_modified_date", "language", "reference", "edition", "author", "status",
            "keywords", "summary", "redirect_url",
        }
        result = {key: source[key] for key in allowed if key in source}
        result["url"] = source.get("canonical_url") or source.get("url") or source.get("url_or_id")
        result["discovered_at"] = RuntimeOfficialConnectorsIntegration._date_text(
            source.get("discovered_at") or discovered_at
        )
        return result

    @staticmethod
    def _snapshot(connector_id: str, item: object) -> ConnectorDocumentSnapshot:
        canonical_url = str(getattr(item, "canonical_url"))
        publication_date = getattr(item, "publication_date", None)
        if connector_id == "dreets_grand_est":
            publication_date = getattr(item, "date", None)
        document_type = getattr(item, "document_type")
        family = getattr(item, "family")
        category = getattr(item, "category")
        return ConnectorDocumentSnapshot(
            external_id=str(
                getattr(item, "document_id", None)
                or stable_document_id(connector_id, canonical_url)
            ),
            source_id=connector_id,
            document_type=str(getattr(document_type, "value", document_type)),
            title=str(getattr(item, "title")),
            publication_date=date.fromisoformat(publication_date) if publication_date else None,
            source_url=canonical_url,
            language=str(getattr(item, "language")),
            metadata=(
                ("category", str(getattr(category, "value", category))),
                ("family", str(getattr(family, "value", family))),
                ("metadata_only", True),
            ),
        )

    def _fallback(self, code: str, started: float) -> RuntimeOfficialConnectorsResult:
        return RuntimeOfficialConnectorsResult(
            (), RuntimeOfficialConnectorsDiagnostics(True, self._duration(started), (), code)
        )

    def _duration(self, started: float) -> int:
        return max(0, round((self._timer() - started) * 1000))

    @staticmethod
    def _date_text(value: object) -> str:
        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, date):
            return value.isoformat()
        text = str(value or "")
        return date.fromisoformat(text[:10]).isoformat()

    @staticmethod
    def _datetime(value: object) -> datetime | None:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00")) if value else None
            if parsed is not None and parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            return None
