from __future__ import annotations

from dataclasses import FrozenInstanceError
import json

import pytest

from NEXUS_RUNTIME_INTEGRATION import sanitize_public_payload
from SYNDICAL_REASONING_ENGINE import (
    ApplicabilityStatus,
    LegalNature,
    analyze_source_to_facts,
    build_case_factual_core,
    build_source_search_queries,
)
from tools.run_real_business_cases_baseline import (
    ROUTE_BY_CASE,
    build_case_prompt,
    load_fixtures,
)
from tools.run_real_business_cases_second_baseline import load_second_fixtures


def core(query: str):
    return build_case_factual_core(query, "QUESTION_SALARIE")


def source(
    *,
    origin: str = "legifrance_code_travail",
    layer: str = "code_travail",
    title: str = "Code du travail — Article L. 0000-1",
    excerpt: str = (
        "Lorsque la mesure est envisagée, l'employeur doit vérifier les faits "
        "et respecter la procédure applicable."
    ),
    article: str = "Article L. 0000-1",
    **extra,
):
    return {
        "origin": origin,
        "source_layer": layer,
        "document": title,
        "excerpt": excerpt,
        "article": article,
        "official_id": extra.pop("official_id", "OFFICIAL-1"),
        "is_in_force": extra.pop("is_in_force", True),
        **extra,
    }


def test_search_plan_contains_six_bounded_fact_driven_axes() -> None:
    factual = core(
        "La direction envisage une sanction après des pauses mesurées par le "
        "tourniquet de sécurité."
    )

    queries = build_source_search_queries(factual)

    assert [item.axis for item in queries] == [
        "A_MAIN_ACT",
        "B_PROCEDURE",
        "C_EVIDENCE_OR_CONTROL",
        "D_PROPORTIONALITY",
        "E_HEALTH_SAFETY_ORGANISATION",
        "F_CONTRACT_OR_DISCIPLINE",
    ]
    assert all(len(item.query) <= 320 for item in queries)
    assert all(item.query != factual.primary_event for item in queries[1:])


def test_models_are_immutable_and_serializable() -> None:
    report = analyze_source_to_facts(
        core("Une sanction est envisagée après des courriels insultants."),
        (source(excerpt="Les faits doivent être précis et la sanction proportionnée."),),
    )
    item = report.applicable_sources[0]

    with pytest.raises(FrozenInstanceError):
        item.source_title = "autre"  # type: ignore[misc]
    json.dumps(report.to_dict(), ensure_ascii=False)


def test_no_source_never_creates_a_rule_or_a_citation() -> None:
    report = analyze_source_to_facts(
        core("Une sanction est envisagée après des courriels insultants."),
        (),
    )

    assert report.applicable_sources == ()
    assert report.rule_to_facts_analysis == ()
    assert report.missing_source_requirements


def test_blocking_ambiguity_suspends_legal_comparison() -> None:
    factual = core("La règle des 10 % aurait disparu mais sa nature est inconnue.")
    report = analyze_source_to_facts(factual, (source(),))

    assert report.analysis_suspended is True
    assert report.applicable_sources == ()
    assert report.rule_to_facts_analysis == ()
    assert any("clarification" in item for item in report.missing_source_requirements)


def test_legifrance_is_qualified_by_document_not_as_a_provider_norm() -> None:
    report = analyze_source_to_facts(
        core("La sanction doit être comparée aux faits et à la procédure."),
        (source(),),
    )
    item = report.applicable_sources[0]

    assert item.source_provider == "Légifrance"
    assert item.legal_nature is LegalNature.STATUTE
    assert item.source_title.startswith("Code du travail")
    assert item.article_or_clause == "Article L. 0000-1"
    assert item.precise_excerpt


def test_keyword_only_case_law_is_rejected() -> None:
    factual = core("Un salarié conteste une sanction après des insultes.")
    decision = source(
        origin="judilibre_jurisprudence",
        layer="jurisprudence",
        title="Décision contenant le mot injure",
        excerpt="Le pourvoi concerne une injure dans un contexte non précisé.",
        article="",
        official_id="JUDI-1",
        juridiction="Cour de cassation",
        decision_date="2025-01-01",
        case_number="24-00.001",
    )

    report = analyze_source_to_facts(factual, (decision,))

    assert report.applicable_sources == ()
    assert "trois critères" in report.rejected_sources[0][1]


def test_factually_comparable_case_law_is_retained_with_prudent_scope() -> None:
    factual = core(
        "Le salarié reconnaît des courriels insultants mais conteste la faute grave "
        "et indique quinze ans d'ancienneté sans antécédent."
    )
    decision = source(
        origin="judilibre_jurisprudence",
        layer="jurisprudence",
        title="Cour de cassation, chambre sociale",
        excerpt=(
            "La décision examine des courriels insultants, l'ancienneté, les "
            "antécédents et la proportionnalité de la sanction."
        ),
        article="",
        official_id="JUDI-2",
        juridiction="Cour de cassation",
        decision_date="2025-02-01",
        case_number="24-00.002",
        ressemblance_avec_dossier=[
            "courriels",
            "ancienneté",
            "absence d'antécédent",
            "sanction",
        ],
        difference_avec_dossier=["diffusion plus large dans la décision"],
    )

    report = analyze_source_to_facts(factual, (decision,))

    item = report.applicable_sources[0]
    analysis = report.rule_to_facts_analysis[0]
    assert item.legal_nature is LegalNature.CASE_LAW
    assert item.factual_similarity_score >= 39
    assert "ne garantit pas la même issue" in analysis.next_action
    assert analysis.facts_not_matching


def test_source_hierarchy_places_internal_rule_before_collective_and_statute() -> None:
    factual = core("Le changement d'horaires doit être comparé au contrat et aux accords.")
    sources = (
        source(
            origin="legifrance_code_travail",
            layer="code_travail",
            title="Code du travail horaires",
            excerpt="Les horaires doivent être examinés selon les règles applicables.",
        ),
        source(
            origin="bible_accords",
            layer="convention_collective",
            title="CCNIC IDCC 44 — chapitre horaires",
            excerpt="Le chapitre traite des horaires de travail applicables.",
            article="Chapitre horaires",
            official_id="CCNIC-1",
        ),
        source(
            origin="bible_accords",
            layer="accord_entreprise",
            title="Accord INEOS sur les horaires postés",
            excerpt="La clause organise le passage vers des horaires postés.",
            article="Clause 4",
            official_id="INEOS-1",
        ),
    )

    report = analyze_source_to_facts(factual, sources)

    assert [item.hierarchy_level for item in report.applicable_sources] == sorted(
        item.hierarchy_level for item in report.applicable_sources
    )
    assert report.applicable_sources[0].legal_nature is LegalNature.COMPANY_AGREEMENT


@pytest.mark.parametrize(
    ("provider", "nature"),
    [
        ("CARSAT", LegalNature.PREVENTION_GUIDANCE),
        ("INRS", LegalNature.PREVENTION_GUIDANCE),
        ("ANACT", LegalNature.OFFICIAL_GUIDANCE),
    ],
)
def test_prevention_and_method_sources_are_never_legal_norms(
    provider: str,
    nature: LegalNature,
) -> None:
    report = analyze_source_to_facts(
        core("Les EPI sont inadaptés et la charge de travail augmente le risque."),
        (
            source(
                origin=provider.casefold(),
                layer="pratique_officielle",
                title=f"{provider} — prévention EPI et organisation",
                excerpt=(
                    "La prévention examine la disponibilité des EPI, leur adaptation "
                    "et l'organisation du travail."
                ),
                official_origin=provider,
            ),
        ),
    )

    item = report.applicable_sources[0]
    assert item.legal_nature is nature
    assert item.legal_nature not in {LegalNature.STATUTE, LegalNature.REGULATION}


def test_cnil_nature_depends_on_the_actual_document() -> None:
    factual = core("Le tourniquet de sécurité est utilisé pour contrôler les pauses.")
    guide = source(
        origin="cnil",
        layer="pratique_officielle",
        title="CNIL — guide sur le contrôle d'accès",
        excerpt="Le guide examine la finalité, l'information et la durée de conservation.",
        official_origin="CNIL",
        document_type="guide",
    )
    decision = source(
        origin="cnil",
        layer="pratique_officielle",
        title="CNIL — décision sur un dispositif de contrôle",
        excerpt="La décision examine la finalité et l'utilisation secondaire des données.",
        official_origin="CNIL",
        document_type="décision",
        official_id="CNIL-DEC-1",
    )

    report = analyze_source_to_facts(factual, (guide, decision))

    assert {item.legal_nature for item in report.applicable_sources} == {
        LegalNature.OFFICIAL_GUIDANCE,
        LegalNature.ADMINISTRATIVE_DECISION,
    }
    assert len(report.control_device_hypotheses) == 3


def test_cse_minutes_are_context_not_normative() -> None:
    report = analyze_source_to_facts(
        core("Le CSE avait déjà signalé une charge de travail excessive."),
        (
            source(
                origin="cse_memory",
                layer="historique_cse",
                title="PV CSE du 12 mars 2024",
                excerpt="Le CSE signale une charge de travail excessive.",
                article="Point 5",
                official_id="PV-2024-03-12",
            ),
        ),
    )

    assert report.applicable_sources[0].legal_nature is LegalNature.CSE_MINUTES
    assert report.applicable_sources[0].hierarchy_level == 6


def test_local_paths_and_sensitive_excerpts_are_not_citation_ready() -> None:
    report = analyze_source_to_facts(
        core("Un contrôle du temps est contesté."),
        (
            source(
                title="Note de contrôle",
                excerpt="Contact salarié@example.fr pour le contrôle du temps.",
                article="C:\\private\\note.pdf",
            ),
        ),
    )

    assert report.applicable_sources == ()
    assert "confidentialité" in report.rejected_sources[0][1]


def test_public_payload_exposes_visible_rule_to_facts_block() -> None:
    factual = core("La sanction doit être comparée aux faits et à la procédure.")
    report = analyze_source_to_facts(factual, (source(),)).to_dict()
    internal = {
        "ok": True,
        "answer": {
            "query": "Question synthétique",
            "confidence": "moyen",
            "route": {"domains": ["disciplinaire"]},
            "case_factual_core": factual.to_dict(),
            "actionable_preparation": {},
            "sources": [],
            "source_layers": [],
            "rule_to_facts_analysis": report["rule_to_facts_analysis"],
            "applicable_sources": report["applicable_sources"],
            "source_search_plan": report["search_queries"],
            "rejected_sources": report["rejected_sources"],
            "missing_source_requirements": report["missing_source_requirements"],
            "adversarial_source_analysis": report["adversarial_analysis"],
            "control_device_hypotheses": report["control_device_hypotheses"],
        },
    }

    public = sanitize_public_payload(internal)

    assert public["answer"]["rule_to_facts_analysis"]
    assert any(
        section["title"] == "Règles comparées aux faits"
        for section in public["analysis_report"]["sections"]
    )


def test_eleven_cases_build_queries_without_regressing_suspensions() -> None:
    fixtures = (*load_fixtures(), *load_second_fixtures())
    assert len(fixtures) == 11

    for fixture in fixtures:
        path = fixture["case_input"].get("requested_path") or ROUTE_BY_CASE[
            fixture["case_id"]
        ]
        factual = build_case_factual_core(build_case_prompt(fixture), path)
        report = analyze_source_to_facts(factual, ())
        assert len(report.search_queries) == 6
        if fixture["case_id"] in {
            "REAL-05-DELEGATION_HOURS_CSSCT_INCOMPLETE",
            "REAL-06-ANNUAL_LEAVE_TEN_PERCENT_UNRESOLVED",
        }:
            assert report.analysis_suspended is True
            assert report.rule_to_facts_analysis == ()
        else:
            assert report.analysis_suspended is False
