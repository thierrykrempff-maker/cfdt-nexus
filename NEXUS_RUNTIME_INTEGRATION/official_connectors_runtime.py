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
import unicodedata

from automation.official_knowledge.connectors.cnil import CnilConnector, CnilDiscoveryEntry
from automation.official_knowledge.connectors.dreets_grand_est.dreets_connector import (
    DreetsGrandEstConnector,
)
from automation.official_knowledge.connectors.dreets_grand_est import DreetsDiscoveryItem
from automation.official_knowledge.connectors.inrs import InrsConnector
from automation.official_knowledge.additional_metadata_feed import (
    load_additional_metadata_sources,
    validate_additional_runtime_sources,
)
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


_ADDITIONAL = frozenset({
    "agirc_arrco", "anact", "alsace_moselle_local_law", "assurance_maladie",
    "carsat", "defenseur_droits", "france_chimie", "ministere_travail",
    "service_public", "urssaf",
})
_SUPPORTED = frozenset({"cnil", "dreets_grand_est", "inrs"}) | _ADDITIONAL
_SOURCE_DETAILS = {
    "cnil": ("CNIL", ConnectorSourceCategory.INDEPENDENT_AUTHORITY, "https://cnil.fr"),
    "dreets_grand_est": (
        "DREETS_GRAND_EST",
        ConnectorSourceCategory.ADMINISTRATIVE_DOCTRINE,
        "https://grand-est.dreets.gouv.fr",
    ),
    "inrs": ("INRS", ConnectorSourceCategory.OTHER_OFFICIAL, "https://www.inrs.fr"),
    "anact": ("ANACT", ConnectorSourceCategory.OTHER_OFFICIAL, "https://www.anact.fr"),
    "alsace_moselle_local_law": (
        "DROIT_LOCAL_ALSACE_MOSELLE",
        ConnectorSourceCategory.LEGISLATION,
        "https://www.legifrance.gouv.fr",
    ),
    "carsat": (
        "CARSAT",
        ConnectorSourceCategory.SOCIAL_SECURITY_BODY,
        "https://www.carsat-alsacemoselle.fr",
    ),
    "france_chimie": (
        "FRANCE_CHIMIE",
        ConnectorSourceCategory.COLLECTIVE_AGREEMENT,
        "https://www.francechimie.fr",
    ),
    "defenseur_droits": (
        "DEFENSEUR_DES_DROITS",
        ConnectorSourceCategory.INDEPENDENT_AUTHORITY,
        "https://www.defenseurdesdroits.fr",
    ),
    "ministere_travail": (
        "MINISTERE_DU_TRAVAIL",
        ConnectorSourceCategory.ADMINISTRATIVE_DOCTRINE,
        "https://travail-emploi.gouv.fr",
    ),
    "service_public": (
        "SERVICE_PUBLIC",
        ConnectorSourceCategory.OTHER_OFFICIAL,
        "https://www.service-public.fr",
    ),
    "assurance_maladie": (
        "ASSURANCE_MALADIE_CPAM",
        ConnectorSourceCategory.SOCIAL_SECURITY_BODY,
        "https://www.ameli.fr",
    ),
    "urssaf": (
        "URSSAF",
        ConnectorSourceCategory.SOCIAL_SECURITY_BODY,
        "https://www.urssaf.fr",
    ),
    "agirc_arrco": (
        "AGIRC_ARRCO",
        ConnectorSourceCategory.SOCIAL_SECURITY_BODY,
        "https://www.agirc-arrco.fr",
    ),
}
_CONNECTOR_MARKERS = {
    "cnil": (
        "rgpd", "donnees personnelles", "details personnels", "confidentialite",
        "camera", "videosurveillance", "geolocalisation", "messagerie",
        "boite professionnelle", "appartenance syndicale", "biometrie",
        "classe automatiquement",
    ),
    "inrs": (
        "incident dangereux", "risque grave", "presque-accident",
        "accident du travail", "risque chimique", "produit chimique",
        "substance", "epi", "gant", "prevention", "tms", "douleur",
        "surcharge", "entreprise exterieure", "coactivite", "exposition",
        "expose", "symptome", "mesures d ambiance", "travail de nuit",
        "travail poste", "5x8", "penibilite", "inaptitude",
    ),
    "dreets_grand_est": (
        "incident dangereux", "protocole electoral", "substance",
        "entreprise exterieure", "coactivite", "mesures d ambiance",
        "projet industriel", "risque grave",
    ),
    "carsat": (
        "carsat", "assurance retraite", "carriere longue", "depart anticipe",
        "c2p", "compte professionnel de prevention", "risque professionnel",
        "accident du travail", "maladie professionnelle", "releve de carriere",
    ),
    "france_chimie": (
        "france chimie", "branche chimie", "convention chimie",
        "convention collective chimie", "classification chimie",
        "coefficient chimie", "accord de branche chimie",
    ),
    "anact": (
        "anact", "aract", "qvct", "qualite de vie et conditions de travail",
        "transformation du travail", "risques psychosociaux", "charge de travail",
    ),
    "alsace_moselle_local_law": (
        "droit local", "alsace moselle", "alsace-moselle",
        "repos dominical alsace", "repos dominical moselle",
        "jour ferie alsace", "jour ferie moselle",
    ),
    "defenseur_droits": (
        "defenseur des droits", "discrimination au travail",
        "harcelement discriminatoire", "harcelement au travail",
        "egalite de traitement", "egalite professionnelle",
        "liberte syndicale", "discrimination syndicale",
        "handicap au travail", "amenagement raisonnable", "lanceur d alerte",
    ),
    "ministere_travail": (
        "ministere du travail", "inspection du travail",
        "procedure de licenciement", "licenciement salarie protege",
        "rupture conventionnelle collective", "actualite reglementaire",
        "interpretation administrative",
    ),
    "service_public": (
        "service public", "service-public", "demarche salarie",
        "formalite administrative", "formulaire cerfa",
        "modele de lettre", "quelle demarche", "comment faire une demande",
    ),
    "assurance_maladie": (
        "assurance maladie", "cpam", "ijss", "indemnite journaliere",
        "arret maladie", "accident du travail", "maladie professionnelle",
        "invalidite", "conge maternite", "temps partiel therapeutique",
        "mi temps therapeutique",
    ),
    "urssaf": (
        "urssaf", "cotisation sociale", "cotisations sociales",
        "exoneration de cotisations", "reduction de cotisations",
        "assiette de cotisations", "avantage en nature",
        "avantages en nature", "cotisations heures supplementaires",
    ),
    "agirc_arrco": (
        "agirc arrco", "agirc-arrco", "retraite complementaire",
        "points retraite", "points de retraite", "retraite progressive",
        "droits retraite complementaire",
    ),
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
        selected = self._selected_connectors(answer) | set(grouped)
        if not selected:
            return RuntimeOfficialConnectorsResult()
        grouped = {
            connector_id: grouped.get(connector_id)
            or (
                load_additional_metadata_sources(connector_id)
                if connector_id in _ADDITIONAL else ()
            )
            for connector_id in selected
        }
        started = self._timer()
        try:
            inputs = tuple(
                self._connector_input(connector_id, grouped.get(connector_id, ()), answer)
                for connector_id in sorted(selected)
            )
            connectors_used = tuple(item.descriptor.connector_id for item in inputs)
            if not any(item.response.documents for item in inputs):
                return RuntimeOfficialConnectorsResult(
                    inputs,
                    RuntimeOfficialConnectorsDiagnostics(
                        True,
                        self._duration(started),
                        connectors_used,
                        "OFFICIAL_CONNECTORS_NO_RESULT",
                    ),
                )
            return RuntimeOfficialConnectorsResult(
                inputs,
                RuntimeOfficialConnectorsDiagnostics(
                    True,
                    self._duration(started),
                    connectors_used,
                ),
            )
        except Exception:
            return self._fallback("OFFICIAL_CONNECTOR_RUNTIME_FAILED", started)

    @classmethod
    def _selected_connectors(cls, answer: Mapping[str, Any]) -> set[str]:
        if not isinstance(answer, Mapping):
            return set()
        query = cls._normalize(answer.get("query"))
        route = answer.get("route") if isinstance(answer.get("route"), Mapping) else {}
        domains = {
            cls._normalize(item).replace(" ", "_")
            for item in route.get("domains", ())
        }
        selected = {
            connector_id
            for connector_id, markers in _CONNECTOR_MARKERS.items()
            if any(marker in query for marker in markers)
        }
        if "rgpd_cnil" in domains:
            selected.add("cnil")
        if "cssct_securite" in domains:
            selected.add("inrs")
        if "retraite_penibilite" in domains:
            selected.update({"agirc_arrco", "carsat"})
        if "protection_sociale" in domains or "social_protection" in domains:
            selected.add("assurance_maladie")
        if "droit_local" in domains or "alsace_moselle_local_law" in domains:
            selected.add("alsace_moselle_local_law")
        return selected

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
        discovered_at = self._date_text(
            answer.get("generated_at"), default=self._clock().date()
        )
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
        elif connector_id in _ADDITIONAL:
            metadata = validate_additional_runtime_sources(
                connector_id, sources, discovered_at
            )
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
    def _normalize(value: object) -> str:
        text = unicodedata.normalize("NFKD", str(value or ""))
        return " ".join(
            "".join(char for char in text if not unicodedata.combining(char))
            .lower()
            .replace("'", " ")
            .split()
        )

    @staticmethod
    def _date_text(value: object, *, default: date | None = None) -> str:
        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, date):
            return value.isoformat()
        text = str(value or "")
        if not text and default is not None:
            return default.isoformat()
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
