"""Connector Platform compatible facade for Légifrance and JUDILIBRE."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Callable

import judilibre_connector
import legifrance_connector
from piste_oauth import PisteOAuthError


HEALTH_STATUSES = frozenset({
    "configured", "not_configured", "authentication_failed", "forbidden",
    "quota_exceeded", "timeout", "network_error", "invalid_response", "available",
})


@dataclass(frozen=True)
class LegalConnectorIdentity:
    connector_id: str
    label: str
    official_publisher: str
    mode: str = "real"


@dataclass
class LegalConnectorResult:
    identity: LegalConnectorIdentity
    configured: bool
    health_status: str
    capabilities: tuple[str, ...]
    query: dict[str, Any] = field(default_factory=dict)
    results: list[dict[str, Any]] = field(default_factory=list)
    diagnostic: list[str] = field(default_factory=list)
    duration_ms: float = 0
    error: str | None = None
    retrieved_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        if self.health_status not in HEALTH_STATUSES:
            raise ValueError("unknown legal connector health status")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


LEGIFRANCE_IDENTITY = LegalConnectorIdentity("legifrance", "Légifrance", "DILA")
JUDILIBRE_IDENTITY = LegalConnectorIdentity("judilibre", "JUDILIBRE", "Cour de cassation")


def _safe_status(exc: Exception) -> str:
    cause = exc.__cause__
    if isinstance(cause, PisteOAuthError):
        return cause.status
    text = str(exc).casefold()
    for status in ("not_configured", "authentication_failed", "forbidden", "quota_exceeded", "timeout", "network_error", "invalid_response"):
        if status in text:
            return status
    if "non configure" in text:
        return "not_configured"
    if "http 403" in text:
        return "forbidden"
    if "http 429" in text:
        return "quota_exceeded"
    if "http 401" in text or "http 400" in text:
        return "authentication_failed"
    if any(f"http {code}" in text for code in (500, 502, 503, 504)):
        return "network_error"
    return "invalid_response"


def _health(
    identity: LegalConnectorIdentity,
    configured: bool,
    capabilities: tuple[str, ...],
    probe: Callable[[], Any],
) -> LegalConnectorResult:
    started = perf_counter()
    if not configured:
        return LegalConnectorResult(identity, False, "not_configured", capabilities)
    try:
        probe()
        return LegalConnectorResult(
            identity, True, "available", capabilities,
            duration_ms=round((perf_counter() - started) * 1000, 2),
        )
    except Exception as exc:
        return LegalConnectorResult(
            identity, True, _safe_status(exc), capabilities,
            duration_ms=round((perf_counter() - started) * 1000, 2),
            error=str(exc),
        )


def healthcheck_piste_oauth(connector: str = "legifrance") -> dict[str, Any]:
    client = (
        judilibre_connector.JudilibreClient()
        if connector.casefold() == "judilibre"
        else legifrance_connector.LegifranceClient()
    )
    started = perf_counter()
    try:
        diagnostic = client.auth_diagnostic()
        return {
            "connector": connector,
            "configured": client.config.configured,
            "status": "available",
            "duration_ms": round((perf_counter() - started) * 1000, 2),
            "diagnostic": diagnostic,
        }
    except Exception as exc:
        return {
            "connector": connector,
            "configured": client.config.configured,
            "status": _safe_status(exc),
            "duration_ms": round((perf_counter() - started) * 1000, 2),
            "error": str(exc),
        }


def healthcheck_legifrance() -> dict[str, Any]:
    client = legifrance_connector.LegifranceClient()
    return _health(
        LEGIFRANCE_IDENTITY,
        client.config.configured,
        ("article_search", "article_detail", "consolidated_text", "idcc_search", "pagination"),
        client.healthcheck,
    ).as_dict()


def healthcheck_judilibre() -> dict[str, Any]:
    client = judilibre_connector.JudilibreClient()
    return _health(
        JUDILIBRE_IDENTITY,
        client.config.configured,
        ("full_text_search", "decision_number", "decision_detail", "filters", "pagination", "factual_comparison"),
        client.healthcheck,
    ).as_dict()
