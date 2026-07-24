"""Feature-flagged and fail-safe bridge to Expert Paie V2."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
import time
from typing import Any, Callable
import unicodedata

from EXPERT_PAIE_V2 import (
    ExpertPaieV2Engine,
    PayrollEvent,
    PayrollEventType,
    PayrollV2Analysis,
    PayrollV2Input,
    SyntheticEmployee,
    Unit,
)

from .config import RuntimeExpertPaieV2Config


class RuntimeExpertPaieV2Mode(str, Enum):
    DISABLED = "DISABLED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    SUCCEEDED = "SUCCEEDED"
    FALLBACK = "FALLBACK"


@dataclass(frozen=True, slots=True)
class RuntimeExpertPaieV2Diagnostics:
    enabled: bool
    called: bool = False
    runtime_ms: int = 0
    fallback_code: str | None = None


@dataclass(frozen=True, slots=True)
class RuntimeExpertPaieV2Result:
    mode: RuntimeExpertPaieV2Mode
    diagnostics: RuntimeExpertPaieV2Diagnostics
    analysis: PayrollV2Analysis | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode.value,
            "diagnostics": {
                "enabled": self.diagnostics.enabled,
                "called": self.diagnostics.called,
                "runtime_ms": self.diagnostics.runtime_ms,
                "fallback_code": self.diagnostics.fallback_code,
            },
            "analysis": self.analysis.to_dict() if self.analysis else None,
        }


def needs_expert_paie_v2(answer: Mapping[str, Any]) -> bool:
    route = answer.get("route") if isinstance(answer.get("route"), Mapping) else {}
    domains = {str(item).lower() for item in route.get("domains", ()) if isinstance(item, str)}
    if "paie_remuneration" in domains:
        return True
    text = _normalize(str(answer.get("query") or ""))
    return any(marker in text for marker in ("bulletin", "paie", "kelio", "nibelis", "rubrique", "compteur", "heures supplementaires", "astreinte", "ijss", "subrogation"))


class RuntimeExpertPaieV2Integration:
    def __init__(
        self,
        config: RuntimeExpertPaieV2Config | None = None,
        *,
        engine: ExpertPaieV2Engine | None = None,
        timer: Callable[[], float] | None = None,
    ) -> None:
        self._config = config or RuntimeExpertPaieV2Config()
        self._engine = engine or ExpertPaieV2Engine()
        self._timer = timer or time.perf_counter

    def integrate(self, answer: Mapping[str, Any]) -> RuntimeExpertPaieV2Result:
        if not self._config.enabled:
            return RuntimeExpertPaieV2Result(
                RuntimeExpertPaieV2Mode.DISABLED,
                RuntimeExpertPaieV2Diagnostics(False),
            )
        if not needs_expert_paie_v2(answer):
            return RuntimeExpertPaieV2Result(
                RuntimeExpertPaieV2Mode.NOT_APPLICABLE,
                RuntimeExpertPaieV2Diagnostics(True),
            )
        started = self._timer()
        try:
            supplied = answer.get("expert_paie_v2_input")
            payload = supplied if isinstance(supplied, PayrollV2Input) else _minimal_input(answer)
            analysis = self._engine.analyze(payload)
            return RuntimeExpertPaieV2Result(
                RuntimeExpertPaieV2Mode.SUCCEEDED,
                RuntimeExpertPaieV2Diagnostics(True, True, self._duration(started)),
                analysis,
            )
        except Exception:
            return RuntimeExpertPaieV2Result(
                RuntimeExpertPaieV2Mode.FALLBACK,
                RuntimeExpertPaieV2Diagnostics(
                    True, True, self._duration(started), "EXPERT_PAIE_V2_FAILED"
                ),
            )

    def _duration(self, started: float) -> int:
        return max(0, int((self._timer() - started) * 1000))


def _minimal_input(answer: Mapping[str, Any]) -> PayrollV2Input:
    text = _normalize(str(answer.get("query") or ""))
    event_type = (
        PayrollEventType.OVERTIME if "heure" in text
        else PayrollEventType.ON_CALL if "astreinte" in text
        else PayrollEventType.IJSS if "ijss" in text
        else PayrollEventType.NOT_MODELLED
    )
    return PayrollV2Input(
        str(answer.get("query") or ""),
        None,
        SyntheticEmployee("RUNTIME-SYNTHETIC", "unknown"),
        (PayrollEvent(event_type, "période à préciser", None, Unit.HOUR, "user_statement"),),
        source_domain="R1E" if event_type is PayrollEventType.IJSS else "R1C",
    )


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return " ".join(
        "".join(char for char in normalized if not unicodedata.combining(char))
        .lower()
        .split()
    )
