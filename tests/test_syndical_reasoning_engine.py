from __future__ import annotations

from dataclasses import replace

from SYNDICAL_REASONING_ENGINE import (
    CaseFact,
    ConfidenceLevel,
    FactStatus,
    SourceReference,
    SourceVerification,
    SyndicalCaseInput,
    SyndicalReasoningEngine,
)
from SYNDICAL_REASONING_ENGINE.protocol import PROTOCOL_STEPS
from SYNDICAL_REASONING_ENGINE.source_policy import rank_sources


def verified(source_id: str, source_type: str, rank_title: str) -> SourceReference:
    return SourceReference(
        source_id,
        rank_title,
        source_type,
        "Autorité synthétique",
        f"https://example.invalid/{source_id}",
        SourceVerification.VERIFIED,
    )


def test_protocol_exposes_all_eighteen_steps_in_order():
    report = SyndicalReasoningEngine().analyze(SyndicalCaseInput("Comment réagir ?"))
    assert len(PROTOCOL_STEPS) == 18
    assert report.completed_steps == tuple(item.value for item in PROTOCOL_STEPS)


def test_missing_information_is_detected_without_inventing_facts():
    report = SyndicalReasoningEngine().analyze(SyndicalCaseInput("Que faire ?"))
    assert "date ou période des faits" in report.missing_information
    assert "sources applicables vérifiées" in report.missing_information
    assert report.retained_facts == ()


def test_multi_domain_provisional_qualification_is_cautious():
    case = SyndicalCaseInput(
        "Le CSE doit-il être consulté pour un changement d'horaires et de prime ?"
    )
    report = SyndicalReasoningEngine().analyze(case)
    assert {"cse_consultation", "working_time", "payroll"} <= set(report.domains)
    assert all("provisoire" in item.lower() for item in report.provisional_qualification)
    assert "décision juridique" in report.analysis_limits[-1]


def test_source_hierarchy_is_contextual_and_traceable():
    sources = (
        verified("jurisprudence", "case_law", "Décision synthétique"),
        verified("code", "labour_code", "Code du travail"),
        verified("accord", "ineos_agreement", "Accord synthétique"),
    )
    ranked = rank_sources(sources, ("employment_contract",))
    assert [item.source.source_id for item in ranked] == ["accord", "code", "jurisprudence"]
    assert all(item.rationale for item in ranked)


def test_explicit_source_contradiction_is_reported():
    first = replace(
        verified("a", "labour_code", "Source A"),
        contradicts_source_ids=("b",),
    )
    second = verified("b", "case_law", "Source B")
    report = SyndicalReasoningEngine().analyze(
        SyndicalCaseInput("Question", available_sources=(first, second))
    )
    assert report.contradictions[0].source_ids == ("a", "b")
    assert report.confidence is ConfidenceLevel.LOW


def test_confidence_uses_observable_evidence():
    case = SyndicalCaseInput(
        "Question sur le contrat",
        established_facts=(
            CaseFact("Fait 1", FactStatus.ESTABLISHED),
            CaseFact("Fait 2", FactStatus.ESTABLISHED),
            CaseFact("Fait 3", FactStatus.ESTABLISHED),
        ),
        person_capacity="salarié",
        workplace_context="site synthétique",
        fact_period="2026",
        desired_outcome="clarifier",
        available_sources=(
            verified("code", "labour_code", "Code"),
            verified("accord", "ineos_agreement", "Accord"),
            verified("convention", "collective_agreement_chemistry", "Convention"),
        ),
    )
    report = SyndicalReasoningEngine().analyze(case)
    assert report.confidence is ConfidenceLevel.HIGH


def test_actions_are_progressive_and_not_automatically_confrontational():
    report = SyndicalReasoningEngine().analyze(
        SyndicalCaseInput("Comment réagir à un changement de contrat ?")
    )
    assert report.action_options[0].name == "Clarifier les faits par écrit"
    assert [item.recommended_order for item in report.action_options] == sorted(
        item.recommended_order for item in report.action_options
    )
    assert all(item.reversible for item in report.action_options[:3])


def test_verified_sources_create_traceable_metadata_only_citations():
    source = verified("code", "labour_code", "Code du travail")
    report = SyndicalReasoningEngine().analyze(
        SyndicalCaseInput("Question", available_sources=(source,))
    )
    assert report.citations[0].source_id == "code"
    assert report.citations[0].canonical_url == "https://example.invalid/code"
    assert not hasattr(report.citations[0], "content")
