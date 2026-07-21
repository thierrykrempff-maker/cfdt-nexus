"""Engine-independent adaptation contracts for gradual Nexus V3 migration."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .analysis import AnalysisRequest, DomainAnalysisResult
from .evidence import Evidence
from .findings import Finding
from .recommendations import Recommendation


@runtime_checkable
class EvidenceProducer(Protocol):
    def produce_evidence(self, request: AnalysisRequest) -> tuple[Evidence, ...]: ...


@runtime_checkable
class FindingProducer(Protocol):
    def produce_findings(self, request: AnalysisRequest) -> tuple[Finding, ...]: ...


@runtime_checkable
class RecommendationProducer(Protocol):
    def produce_recommendations(
        self, request: AnalysisRequest
    ) -> tuple[Recommendation, ...]: ...


@runtime_checkable
class DomainAnalyzer(Protocol):
    def analyze(self, request: AnalysisRequest) -> DomainAnalysisResult: ...


@runtime_checkable
class DomainResultAdapter(Protocol):
    def adapt(self, result: object) -> DomainAnalysisResult: ...
