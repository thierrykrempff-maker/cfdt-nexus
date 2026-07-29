from __future__ import annotations

from NEXUS_RUNTIME_INTEGRATION.final_response import build_final_response
from NEXUS_RUNTIME_INTEGRATION.source_extraction import (
    DocumentAvailability,
    build_source_extraction_report,
    merge_metadata_source_qualifications,
)
from SYNDICAL_REASONING_ENGINE import build_case_factual_core


def _core(query: str):
    return build_case_factual_core(query, "QUESTION_SALARIE")


def _source(
    *,
    title: str,
    excerpt: str,
    article: str,
    layer: str = "accord_entreprise",
    origin: str = "bible_accords",
    **extra,
):
    return {
        "document": title,
        "excerpt": excerpt,
        "article": article,
        "location": article,
        "source_layer": layer,
        "origin": origin,
        "official_id": extra.pop("official_id", title),
        "is_in_force": extra.pop("is_in_force", True),
        **extra,
    }


def test_exact_company_clause_is_extracted_with_traceability() -> None:
    report = build_source_extraction_report(
        _core("La direction impose un passage du laboratoire de jour en 5x8."),
        (
            _source(
                title="Avenant 2 à l’accord 35 heures — 5x8",
                excerpt="Le passage en équipes 5x8 est organisé selon le cycle défini.",
                article="Article 4 — Cycle 5x8",
                publication_date="2014-06-12",
                date_debut="2014-07-01",
            ),
        ),
        ({"document": "Accord INEOS sur horaires postés"},),
    )

    assert report.retrieved_count == 1
    assert report.clause_count == 1
    assert report.sources[0].provider == "INEOS Sarralbe"
    assert report.sources[0].article_or_clause == "Article 4 — Cycle 5x8"
    assert report.sources[0].excerpt.startswith("Le passage")
    assert (
        report.document_resolutions[0].availability_status
        is DocumentAvailability.FOUND_VERSION_UNCERTAIN
    )


def test_version_uncertainty_is_stated_without_requesting_document_again() -> None:
    report = build_source_extraction_report(
        _core("La direction annonce un passage vers des horaires postés."),
        (
            _source(
                title="Accord INEOS sur les horaires postés",
                excerpt="La clause organise les horaires postés.",
                article="Clause 3",
            ),
        ),
        ({"document": "Accord INEOS sur horaires postés"},),
    )

    resolution = report.document_resolutions[0]
    assert (
        resolution.availability_status
        is DocumentAvailability.FOUND_VERSION_UNCERTAIN
    )
    assert "version applicable" in resolution.message


def test_legifrance_article_keeps_document_nature_and_exact_reference() -> None:
    report = build_source_extraction_report(
        _core("La procédure disciplinaire doit être vérifiée."),
        (
            _source(
                title="Code du travail — procédure disciplinaire",
                excerpt=(
                    "Dans une procédure disciplinaire, la sanction ne peut intervenir "
                    "plus d’un mois après l’entretien."
                ),
                article="Article L1332-2",
                layer="code_travail",
                origin="legifrance_code_travail",
                official_id="LEGIARTI-L1332-2",
                publication_date="2025-01-01",
                version="2025-01-01",
            ),
        ),
        ({"document": "Article du Code du travail sur la procédure disciplinaire"},),
    )

    extracted = report.sources[0]
    assert extracted.provider == "Légifrance"
    assert extracted.legal_nature == "STATUTE"
    assert extracted.article_or_clause == "Article L1332-2"
    assert report.legal_text_count == 1


def test_ccnic_disposition_is_cited_by_chapter_not_as_a_generic_page() -> None:
    report = build_source_extraction_report(
        _core("Le passage en horaires postés doit être comparé à la convention."),
        (
            _source(
                title="CCNIC IDCC 44 — Travail posté",
                excerpt="Le chapitre fixe les garanties applicables au travail posté.",
                article="Chapitre IV — Article 12",
                layer="convention_collective",
                official_id="IDCC44-CH4-A12",
                publication_date="2024-01-01",
                version="2024-01-01",
            ),
        ),
        ({"document": "Disposition CCNIC sur le travail posté"},),
    )

    assert report.sources[0].legal_nature == "COLLECTIVE_AGREEMENT"
    assert report.sources[0].article_or_clause == "Chapitre IV — Article 12"
    assert report.sources[0].excerpt


def test_cse_minutes_are_context_and_never_presented_as_a_norm() -> None:
    report = build_source_extraction_report(
        _core("Le CSE a déjà signalé une fatigue liée aux horaires."),
        (
            _source(
                title="PV CSE du 12 mars 2024",
                excerpt="Le CSE signale une fatigue récurrente liée aux horaires.",
                article="Point 5",
                layer="historique_cse",
                origin="cse_memory",
                publication_date="2024-03-12",
            ),
        ),
        ({"document": "PV CSE sur la fatigue et les horaires"},),
    )

    assert report.sources[0].normative_role == "CONTEXT_OR_EVIDENCE_ONLY"


def test_unrelated_document_does_not_satisfy_a_specific_request() -> None:
    report = build_source_extraction_report(
        _core("Un EPI adapté n’était pas disponible."),
        (
            _source(
                title="Règlement intérieur — accès au site",
                excerpt="Le badge est obligatoire pour accéder au site.",
                article="Article 2",
                publication_date="2023-01-01",
            ),
        ),
        ({"document": "Consigne EPI applicable"},),
    )

    assert (
        report.document_resolutions[0].availability_status
        is DocumentAvailability.ABSENT
    )


def test_source_from_another_establishment_is_never_used() -> None:
    source = _source(
        title="Accord horaires postés d’un autre site",
        excerpt="Le cycle 5x8 est défini pour cet autre établissement.",
        article="Article 3",
        publication_date="2024-01-01",
        establishment="Autre entreprise — autre site",
    )
    report = build_source_extraction_report(
        _core("La direction impose un passage vers les horaires postés."),
        (source,),
        ({"document": "Accord INEOS sur horaires postés"},),
    )

    assert report.sources == ()
    assert "autre établissement" in report.rejected_sources[0][1]


def test_suspended_analysis_can_report_a_document_without_drawing_a_rule() -> None:
    report = build_source_extraction_report(
        _core("La règle des 10 % aurait disparu mais son sens est inconnu."),
        (
            _source(
                title="Accord congés annuels — règle des 10 %",
                excerpt=(
                    "La période de référence des congés annuels et la règle dite "
                    "des 10 % sont mentionnées sans en définir ici le sens."
                ),
                article="Article 2",
                publication_date="2025-11-24",
            ),
        ),
        ({"document": "Texte exact définissant la règle des 10 %"},),
    )

    assert report.sources
    assert report.document_resolutions[0].availability_status in {
        DocumentAvailability.ABSENT,
        DocumentAvailability.NEEDS_CLARIFICATION,
    }


def test_metadata_only_official_result_is_title_only_not_a_fabricated_clause() -> None:
    merged = merge_metadata_source_qualifications(
        {"sources": [], "retrieved_count": 0},
        (
            {
                "organisme": "CNIL",
                "titre": "Contrôle d’accès sur le lieu de travail",
                "nature_document": "Guide",
                "portee_indicative": "Information officielle",
                "lien_avec_faits": "Utilisation du badgeage pour contrôler les pauses.",
            },
        ),
    )

    source = merged["sources"][0]
    assert source["availability_status"] == "TITLE_ONLY"
    assert source["excerpt"] == ""
    assert source["article_or_clause"] is None


def test_final_response_omits_found_document_and_keeps_traceable_source() -> None:
    core = _core("La direction impose un passage de jour vers le 5x8.")
    extraction = build_source_extraction_report(
        core,
        (
            _source(
                title="Accord INEOS sur les horaires postés 5x8",
                excerpt=(
                    "Le passage de jour vers les horaires postés et le cycle 5x8 "
                    "sont définis dans cette clause."
                ),
                article="Article 4",
                publication_date="2014-06-12",
                date_debut="2014-07-01",
            ),
        ),
        ({"document": "Accord INEOS sur horaires postés"},),
    )
    response = build_final_response(
        {
            "case_factual_core": core.to_dict(),
            "actionable_preparation": {
                "documents_to_request": [
                    {
                        "document": "Accord INEOS sur horaires postés",
                        "purpose": "Identifier les garanties.",
                        "priority": "HIGH",
                    },
                    {
                        "document": "Planning projeté",
                        "purpose": "Connaître le cycle.",
                        "priority": "HIGH",
                    },
                ]
            },
            "source_extraction": extraction.to_dict(),
        }
    )

    documents = response["public_summary"]["documents"]
    assert [item["document"] for item in documents] == ["Planning projeté"]
    visible = response["public_summary"]["source_extractions"][0]
    assert visible["reference"] == "Article 4"
    assert visible["excerpt"]
    assert response["detailed_analysis"]["source_extraction"]
