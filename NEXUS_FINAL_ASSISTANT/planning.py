"""Bounded and deterministic analysis planning."""

from __future__ import annotations

from .models import AnalysisPlan, AssistantRequest, Domain, DomainMatch, ResponseMode


_SOURCES = {
    Domain.CONTRACT: ("Accords INEOS", "Convention collective Chimie", "Code du travail", "Contrat"),
    Domain.DISCIPLINE: ("Code du travail", "Convention collective Chimie", "Jurisprudence"),
    Domain.WORKING_TIME: ("Accords INEOS", "Convention collective Chimie", "Code du travail", "Kelio"),
    Domain.DISCRIMINATION: ("Code du travail", "Jurisprudence", "Défenseur des droits"),
    Domain.HEALTH: ("Code de la sécurité sociale", "Accords INEOS", "Sources officielles"),
    Domain.CSE_CONSULTATION: ("Code du travail", "Documents CSE", "Accords INEOS"),
    Domain.CSE_OPERATION: ("Code du travail", "Documents CSE", "Historique CSE"),
    Domain.CSE_ALERTS: ("Code du travail", "Documents CSE", "INRS"),
    Domain.PAYROLL: ("Accords INEOS", "Convention collective Chimie", "Bulletin", "Kelio", "Nibelis"),
    Domain.DOCUMENTARY: ("Sources officielles", "Documents CSE"),
    Domain.TRANSVERSAL: ("Sources officielles",),
}


class AnalysisPlanner:
    def __init__(self, max_engines: int = 4) -> None:
        if max_engines < 1:
            raise ValueError("max_engines must be positive")
        self.max_engines = max_engines

    def plan(self, request: AssistantRequest, matches: tuple[DomainMatch, ...]) -> AnalysisPlan:
        primary = matches[0].domain
        complementary = tuple(item.domain for item in matches[1:4] if item.score >= 25)
        engines: list[str] = []
        for item in matches:
            for engine in self._engines_for(item.domain, item.proposed_engine):
                if engine not in engines:
                    engines.append(engine)
        allowed = set(request.allowed_engines)
        excluded: list[str] = []
        if allowed:
            excluded = [engine for engine in engines if engine not in allowed]
            engines = [engine for engine in engines if engine in allowed]
        engines = engines[: self.max_engines]
        missing = []
        if not request.period:
            missing.append("Période concernée")
        if not request.available_documents:
            missing.append("Documents disponibles")
        mode = self._mode(request, matches)
        sources: list[str] = []
        for domain in (primary, *complementary):
            sources.extend(_SOURCES[domain])
        return AnalysisPlan(
            primary,
            complementary,
            tuple(engines),
            tuple(dict.fromkeys(sources)),
            tuple(missing[:3]),
            tuple(missing),
            False,
            tuple(excluded),
            ("Donnée critique absente", "Confidentialité bloquante"),
            "historical_runtime",
            mode,
        )

    @staticmethod
    def _engines_for(domain: Domain, proposed: str) -> tuple[str, ...]:
        if domain in {Domain.CSE_CONSULTATION, Domain.CSE_OPERATION, Domain.CSE_ALERTS}:
            return ("syndical_reasoning", "cse_memory")
        return (proposed,)

    @staticmethod
    def _mode(request: AssistantRequest, matches: tuple[DomainMatch, ...]) -> ResponseMode:
        forced = request.requested_detail.strip().upper()
        if forced in ResponseMode.__members__:
            return ResponseMode[forced]
        if request.union_role or request.expected_output.lower() == "expert":
            return ResponseMode.EXPERT
        return ResponseMode.QUICK if len(matches) == 1 and matches[0].score >= 60 else ResponseMode.CASE
