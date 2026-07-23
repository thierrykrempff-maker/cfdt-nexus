"""Structural tests for neutral engine adaptation Protocols."""

from datetime import datetime, timezone

from NEXUS_CORE import (
    AnalysisId,
    AnalysisQuestion,
    AnalysisRequest,
    AnalysisScope,
    AnalysisStatus,
    CorrelationId,
    DomainAnalysisResult,
    DomainAnalyzer,
    DomainResultAdapter,
    DomainSelection,
    EntityId,
    EntityReference,
    EvidenceProducer,
    FindingProducer,
    RecommendationProducer,
)


def request() -> AnalysisRequest:
    return AnalysisRequest(
        AnalysisId("analysis-contract-1"),
        CorrelationId("correlation-contract-1"),
        AnalysisQuestion("CONTRACT_TEST"),
        AnalysisScope((EntityReference(EntityId("subject-contract-1"), "person"),)),
        (DomainSelection.CSE,),
    )


class SyntheticAdapter:
    def produce_evidence(self, request):
        return ()

    def produce_findings(self, request):
        return ()

    def produce_recommendations(self, request):
        return ()

    def analyze(self, request):
        return DomainAnalysisResult(DomainSelection.CSE, AnalysisStatus.COMPLETED)

    def adapt(self, result):
        return DomainAnalysisResult(DomainSelection.CSE, AnalysisStatus.COMPLETED)


def test_protocols_accept_structural_engine_adapter():
    adapter = SyntheticAdapter()
    assert isinstance(adapter, EvidenceProducer)
    assert isinstance(adapter, FindingProducer)
    assert isinstance(adapter, RecommendationProducer)
    assert isinstance(adapter, DomainAnalyzer)
    assert isinstance(adapter, DomainResultAdapter)
    assert adapter.analyze(request()).domain is DomainSelection.CSE


def test_domain_result_is_neutral_and_has_expected_collections():
    result = SyntheticAdapter().analyze(request())
    assert result.evidence == ()
    assert result.findings == ()
    assert result.conflicts == ()
    assert result.recommendations == ()
    assert result.diagnostics == ()


def test_contracts_do_not_require_engine_base_classes():
    assert SyntheticAdapter.__bases__ == (object,)
