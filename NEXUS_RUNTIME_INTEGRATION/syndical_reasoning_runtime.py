"""Fail-safe Runtime bridge for the Syndical Reasoning Engine R0."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
import hashlib
import time
from typing import Any, Callable
import unicodedata

from SYNDICAL_REASONING_ENGINE import (
    CaseFact,
    ConfidentialityLevel,
    ContractChangeReasoningEngine,
    DisciplinaryReasoningEngine,
    SourceReference,
    SourceVerification,
    SyndicalCaseInput,
    SyndicalReasoningEngine,
    SyndicalReasoningReport,
    UrgencyLevel,
    needs_contract_change_reasoning,
    needs_disciplinary_reasoning,
)

from .config import RuntimeSyndicalReasoningConfig


class RuntimeSyndicalReasoningMode(str, Enum):
    DISABLED = "DISABLED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    SUCCEEDED = "SUCCEEDED"
    FALLBACK = "FALLBACK"


@dataclass(frozen=True, slots=True)
class RuntimeSyndicalReasoningDiagnostics:
    enabled: bool
    called: bool = False
    runtime_ms: int = 0
    fallback_code: str | None = None

    def __post_init__(self) -> None:
        if self.runtime_ms < 0:
            raise ValueError("runtime_ms must be non-negative")
        if self.fallback_code is not None and not self.fallback_code.replace("_", "").isalnum():
            raise ValueError("fallback_code must be a stable technical code")

    def to_dict(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "called": self.called,
            "runtime_ms": self.runtime_ms,
            "fallback_code": self.fallback_code,
        }


@dataclass(frozen=True, slots=True)
class RuntimeSyndicalReasoningResult:
    mode: RuntimeSyndicalReasoningMode
    diagnostics: RuntimeSyndicalReasoningDiagnostics
    report: SyndicalReasoningReport | None = None
    domain_analysis: Mapping[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode.value,
            "diagnostics": self.diagnostics.to_dict(),
            "short_view": self.report.short_view() if self.report else None,
            "expert_view": self.report.expert_view() if self.report else None,
            "domain_analysis": dict(self.domain_analysis) if self.domain_analysis else None,
        }


def needs_syndical_reasoning(answer: Mapping[str, Any]) -> bool:
    route = answer.get("route") if isinstance(answer.get("route"), Mapping) else {}
    domains = {
        str(item).strip().lower()
        for item in route.get("domains", ())
        if isinstance(item, str)
    }
    intents = {
        str(item).strip().lower()
        for item in route.get("intents", ())
        if isinstance(item, str)
    }
    explicit_domains = {
        "droit_syndical",
        "cse",
        "temps_travail",
        "paie_remuneration",
        "sante_securite",
        "discrimination",
        "contrat_travail",
        "classification_carriere",
        "disciplinary_procedure",
        "disciplinaire",
        "employee_protection",
        "licenciement",
    }
    if domains.intersection(explicit_domains):
        return True
    if intents.intersection({"preparer_cse", "conseiller_salarie", "analyser_paie"}):
        return True
    normalized = _normalize(str(answer.get("query") or ""))
    return any(
        marker in normalized
        for marker in (
            "delegue syndical",
            "comment reagir",
            "quelle strategie",
            "cse",
            "employeur peut il",
            "defendre le salarie",
            "sanction",
            "disciplinaire",
            "avertissement",
            "mise a pied",
            "licenciement pour faute",
            "entretien prealable",
        )
    )


class RuntimeSyndicalReasoningIntegration:
    def __init__(
        self,
        config: RuntimeSyndicalReasoningConfig | None = None,
        *,
        engine: SyndicalReasoningEngine | None = None,
        contract_change_engine: ContractChangeReasoningEngine | None = None,
        disciplinary_engine: DisciplinaryReasoningEngine | None = None,
        timer: Callable[[], float] | None = None,
    ) -> None:
        self._config = config or RuntimeSyndicalReasoningConfig()
        self._engine = engine or SyndicalReasoningEngine()
        self._contract_change_engine = (
            contract_change_engine or ContractChangeReasoningEngine(self._engine)
        )
        self._disciplinary_engine = (
            disciplinary_engine or DisciplinaryReasoningEngine(self._engine)
        )
        self._timer = timer or time.perf_counter

    def integrate(self, answer: Mapping[str, Any]) -> RuntimeSyndicalReasoningResult:
        if not self._config.enabled:
            return RuntimeSyndicalReasoningResult(
                RuntimeSyndicalReasoningMode.DISABLED,
                RuntimeSyndicalReasoningDiagnostics(False),
            )
        if not needs_syndical_reasoning(answer):
            return RuntimeSyndicalReasoningResult(
                RuntimeSyndicalReasoningMode.NOT_APPLICABLE,
                RuntimeSyndicalReasoningDiagnostics(True),
            )
        started = self._timer()
        try:
            case = self._case_from_answer(answer)
            domain_analysis = None
            if needs_disciplinary_reasoning(case):
                specialized = self._disciplinary_engine.analyze(case)
                report = specialized.base_report
                domain_analysis = specialized.to_dict()
            elif needs_contract_change_reasoning(case):
                specialized = self._contract_change_engine.analyze(case)
                report = specialized.base_report
                domain_analysis = specialized.to_dict()
            else:
                report = self._engine.analyze(case)
            return RuntimeSyndicalReasoningResult(
                RuntimeSyndicalReasoningMode.SUCCEEDED,
                RuntimeSyndicalReasoningDiagnostics(
                    True, True, self._duration(started)
                ),
                report,
                domain_analysis,
            )
        except Exception:
            return RuntimeSyndicalReasoningResult(
                RuntimeSyndicalReasoningMode.FALLBACK,
                RuntimeSyndicalReasoningDiagnostics(
                    True,
                    True,
                    self._duration(started),
                    "SYNDICAL_REASONING_RUNTIME_FAILED",
                ),
            )

    @staticmethod
    def _case_from_answer(answer: Mapping[str, Any]) -> SyndicalCaseInput:
        route = answer.get("route") if isinstance(answer.get("route"), Mapping) else {}
        query = str(answer.get("query") or "").strip()
        sources = RuntimeSyndicalReasoningIntegration._sources(answer)
        missing = tuple(
            str(item).strip()
            for item in answer.get("missing_information", ())
            if isinstance(item, str) and item.strip()
        )
        return SyndicalCaseInput(
            question=query,
            declared_facts=(
                CaseFact(
                    "La question constitue une déclaration à vérifier ; aucun fait "
                    "n'est automatiquement tenu pour établi."
                ),
            ),
            suspected_domains=tuple(
                sorted(
                    str(item).strip().lower()
                    for item in route.get("domains", ())
                    if isinstance(item, str) and item.strip()
                )
            ),
            available_sources=sources,
            urgency=RuntimeSyndicalReasoningIntegration._urgency(answer),
            confidentiality=ConfidentialityLevel.INTERNAL,
            desired_outcome="structurer l'analyse et les prochaines actions",
            missing_information=missing,
        )

    @staticmethod
    def _sources(answer: Mapping[str, Any]) -> tuple[SourceReference, ...]:
        raw_sources = answer.get("sources", ())
        if not isinstance(raw_sources, Sequence) or isinstance(
            raw_sources, (str, bytes, bytearray)
        ):
            return ()
        result = {}
        for raw in raw_sources:
            if not isinstance(raw, Mapping):
                continue
            url = str(raw.get("canonical_url") or raw.get("url") or "").strip()
            title = str(raw.get("title") or raw.get("document") or "").strip()
            if not url.startswith("https://") or not title:
                continue
            origin = str(
                raw.get("origin") or raw.get("connector_id") or raw.get("source_id") or "official"
            ).strip().lower()
            source_id = hashlib.sha256(f"{origin}\x1f{url}".encode("utf-8")).hexdigest()[:20]
            result[source_id] = SourceReference(
                source_id,
                title,
                _source_type(origin),
                str(raw.get("publisher") or origin or "source officielle"),
                url,
                SourceVerification.VERIFIED,
                False,
                str(raw.get("effective_on") or raw.get("publication_date") or "") or None,
            )
        return tuple(result[key] for key in sorted(result))

    @staticmethod
    def _urgency(answer: Mapping[str, Any]) -> UrgencyLevel:
        value = _normalize(str(answer.get("urgency") or ""))
        if value in {"immediate", "immediat", "critique"}:
            return UrgencyLevel.IMMEDIATE
        if value in {"urgent", "eleve"}:
            return UrgencyLevel.URGENT
        return UrgencyLevel.ROUTINE

    def _duration(self, started: float) -> int:
        return max(0, int((self._timer() - started) * 1000))


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return " ".join(
        "".join(char for char in normalized if not unicodedata.combining(char))
        .lower()
        .split()
    )


def _source_type(origin: str) -> str:
    mapping = {
        "legifrance": "labour_code",
        "judilibre": "case_law",
        "cdtn": "official_administration",
        "code_travail_numerique": "official_administration",
        "cnil": "cnil",
        "defenseur_droits": "defenseur_droits",
        "ministere_travail": "ministere_travail",
        "service_public": "service_public",
        "inrs": "inrs",
        "anact": "anact",
        "carsat": "carsat",
        "assurance_maladie": "cpam",
        "urssaf": "urssaf",
        "agirc_arrco": "agirc_arrco",
        "dreets_grand_est": "dreets",
        "alsace_moselle_local_law": "local_law",
    }
    return mapping.get(origin, "other")
