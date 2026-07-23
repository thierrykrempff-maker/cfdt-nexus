"""Convert connector results already selected by the historical router into snapshots."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timezone
import hashlib
from typing import Any

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

from .config import RuntimeConnectorConfig


_CONNECTORS = {
    "legifrance_code_travail": (
        "legifrance", "LEGIFRANCE", ConnectorSourceCategory.LEGISLATION,
        "https://www.legifrance.gouv.fr",
    ),
    "judilibre_jurisprudence": (
        "judilibre", "JUDILIBRE", ConnectorSourceCategory.CASE_LAW,
        "https://www.courdecassation.fr",
    ),
    "cdtn_pratique_officielle": (
        "cdtn", "CODE_TRAVAIL_NUMERIQUE", ConnectorSourceCategory.ADMINISTRATIVE_DOCTRINE,
        "https://code.travail.gouv.fr",
    ),
}
_ENGINE_TO_ORIGIN = {
    "legifrance_code_travail": "legifrance_code_travail",
    "judilibre_jurisprudence": "judilibre_jurisprudence",
    "pratique_officielle": "cdtn_pratique_officielle",
}


def _stable(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:24]
    return f"runtime-connector-{prefix}-{digest}"


@dataclass(frozen=True, slots=True)
class RuntimeConnectorMappingResult:
    inputs: tuple[ConnectorAdapterInput, ...] = ()
    connector_ids: tuple[str, ...] = ()
    snapshot_count: int = 0
    fallback_code: str | None = None


class RuntimeConnectorPayloadMapper:
    """Map only Légifrance, JUDILIBRE and CDTN results already present in an answer."""

    def __init__(self, config: RuntimeConnectorConfig | None = None) -> None:
        self._config = config or RuntimeConnectorConfig()

    def map(self, answer: Mapping[str, Any]) -> RuntimeConnectorMappingResult:
        if not self._config.enabled:
            return RuntimeConnectorMappingResult()
        try:
            return self._map_enabled(answer)
        except Exception:
            return RuntimeConnectorMappingResult(fallback_code="CONNECTOR_SNAPSHOT_MAPPING_FAILED")

    def _map_enabled(self, answer: Mapping[str, Any]) -> RuntimeConnectorMappingResult:
        raw_sources = answer.get("sources", ())
        if not isinstance(raw_sources, Sequence) or isinstance(raw_sources, (str, bytes, bytearray)):
            raise TypeError("sources must be a sequence")
        grouped: dict[str, list[Mapping[str, Any]]] = {origin: [] for origin in _CONNECTORS}
        for source in raw_sources:
            if not isinstance(source, Mapping):
                continue
            origin = str(source.get("origin") or "")
            if origin in grouped:
                grouped[origin].append(source)

        attempted = self._attempted_origins(answer, grouped)
        acquired_at = self._acquired_at(answer)
        query = str(answer.get("query") or "")
        inputs = tuple(
            self._input(origin, grouped[origin], query, acquired_at, answer.get("confidence"))
            for origin in sorted(attempted)
        )
        return RuntimeConnectorMappingResult(
            inputs,
            tuple(item.descriptor.connector_id for item in inputs),
            len(inputs),
        )

    @staticmethod
    def _attempted_origins(answer, grouped) -> set[str]:
        attempted = {origin for origin, sources in grouped.items() if sources}
        route = answer.get("route") if isinstance(answer.get("route"), Mapping) else {}
        engines = route.get("engines") or ()
        if isinstance(engines, Sequence) and not isinstance(engines, (str, bytes, bytearray)):
            attempted.update(
                _ENGINE_TO_ORIGIN[str(engine)] for engine in engines if str(engine) in _ENGINE_TO_ORIGIN
            )
        if answer.get("legifrance_audit"):
            attempted.add("legifrance_code_travail")
        if answer.get("jurisprudence_audit"):
            attempted.add("judilibre_jurisprudence")
        return attempted

    def _input(self, origin, sources, query, acquired_at, confidence):
        connector_id, label, category, official_url = _CONNECTORS[origin]
        documents = tuple(self._document(origin, connector_id, source) for source in sources)
        return ConnectorAdapterInput(
            ConnectorDescriptor(connector_id, "runtime-1.0", (ConnectorCapability.DOCUMENTS,)),
            ConnectorSourceSnapshot(connector_id, label, category, True, official_url),
            ConnectorQuerySnapshot(
                _stable("query", connector_id, query),
                "RUNTIME_ROUTER_QUERY",
                (("query_fingerprint", _stable("question", query)),),
            ),
            ConnectorResponseSnapshot(
                _stable("response", connector_id, *(item.external_id or "missing" for item in documents)),
                ConnectorResponseStatus.SUCCEEDED if documents else ConnectorResponseStatus.EMPTY,
                documents,
                source_confidence=self._confidence(confidence),
            ),
            acquired_at,
        )

    def _document(self, origin, connector_id, source):
        external_id = str(
            source.get("official_id") or source.get("judilibre_id")
            or source.get("legifrance_id") or source.get("chunk_id")
            or _stable(
                "document-input", connector_id,
                str(source.get("url_or_id") or source.get("url") or ""),
                str(source.get("document") or source.get("title") or ""),
            )
        )
        document_type = {
            "legifrance_code_travail": "LEGAL_TEXT",
            "judilibre_jurisprudence": "CASE_LAW",
            "cdtn_pratique_officielle": "ADMINISTRATIVE_GUIDANCE",
        }[origin]
        return ConnectorDocumentSnapshot(
            external_id,
            connector_id,
            document_type,
            str(source.get("document") or source.get("title") or "").strip() or None,
            str(source.get("article") or source.get("case_number") or "").strip() or None,
            self._date(source.get("decision_date") or source.get("date_debut")),
            self._datetime(source.get("updated_at") or source.get("retrieved_at")),
            str(source.get("version") or "").strip() or None,
            str(source.get("juridiction") or source.get("official_origin") or "").strip() or None,
            str(source.get("url_or_id") or source.get("url") or "").strip() or None,
            "fr",
            excerpt=str(source.get("excerpt") or "").strip() or None,
            validity_status=str(source.get("etat") or source.get("status") or "").strip() or None,
            metadata=(("runtime_origin", origin), ("source_layer", str(source.get("source_layer") or ""))),
        )

    @staticmethod
    def _date(value: object) -> date | None:
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        try:
            return date.fromisoformat(str(value)[:10]) if value else None
        except ValueError:
            return None

    @staticmethod
    def _datetime(value: object) -> datetime | None:
        if isinstance(value, datetime):
            return value
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00")) if value else None
            if parsed is not None and parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            return None

    @staticmethod
    def _confidence(value: object) -> float | None:
        return {"fort": 0.8, "high": 0.8, "moyen": 0.5, "medium": 0.5, "faible": 0.2, "low": 0.2}.get(
            str(value or "").strip().lower()
        )

    @staticmethod
    def _acquired_at(answer: Mapping[str, Any]) -> datetime:
        value = answer.get("generated_at") or answer.get("retrieved_at")
        parsed = RuntimeConnectorPayloadMapper._datetime(value)
        return parsed or datetime.now(timezone.utc)
