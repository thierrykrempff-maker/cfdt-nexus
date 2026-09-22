from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "apps" / "nexus-local-interface"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import rgpd_analysis as rgpd


def test_document_with_all_mentions_is_low_risk() -> None:
    document = {
        "name": "accord_videosurveillance_complet.txt",
        "passages": [
            {
                "reference": "Article 1",
                "text": (
                    "Des cameras de videosurveillance sont installees dans le but de "
                    "garantir la securite des biens et des personnes sur le site."
                ),
            },
            {
                "reference": "Article 2",
                "text": (
                    "Les images sont conservees pendant une duree de conservation de "
                    "quinze jours."
                ),
            },
            {
                "reference": "Article 3",
                "text": "Les salaries sont informes de ce dispositif par voie d'affichage.",
            },
            {
                "reference": "Article 4",
                "text": "Le CSE a ete consulte prealablement a la mise en place de ce dispositif.",
            },
        ],
    }

    report = rgpd.analyze_document_rgpd(document)

    assert report["no_sensitive_topic_detected"] is False
    assert report["topics_detected"] == 1
    topic = report["topics"][0]
    assert topic["topic_id"] == "videosurveillance_travail"
    assert topic["missing_count"] == 0
    assert topic["risk_level"] == "faible"
    assert all(item["present"] for item in topic["checklist"])
    for item in topic["checklist"]:
        assert item["evidence"] is not None
        assert item["evidence"]["text"]


def test_document_missing_everything_is_high_risk() -> None:
    document = {
        "name": "accord_videosurveillance_incomplet.txt",
        "text": "Des cameras de videosurveillance sont installees dans les ateliers.",
    }

    report = rgpd.analyze_document_rgpd(document)

    assert report["topics_detected"] == 1
    topic = report["topics"][0]
    assert topic["missing_count"] == topic["requirement_count"]
    assert topic["risk_level"] == "eleve"
    assert all(not item["present"] and item["evidence"] is None for item in topic["checklist"])


def test_document_without_sensitive_topic_is_flagged_as_such() -> None:
    document = {
        "name": "accord_restauration.txt",
        "text": "Le present accord fixe les modalites de la pause dejeuner et du forfait restauration.",
    }

    report = rgpd.analyze_document_rgpd(document)

    assert report["no_sensitive_topic_detected"] is True
    assert report["topics"] == []


def test_evidence_quotes_the_real_passage_not_invented_text() -> None:
    document = {
        "name": "accord_badgeage.txt",
        "passages": [
            {
                "reference": "Page 2",
                "text": (
                    "Le controle d'acces par badge a pour objet de securiser les "
                    "locaux sensibles de l'entreprise."
                ),
            },
        ],
    }

    report = rgpd.analyze_document_rgpd(document)
    topic = report["topics"][0]
    finalite = next(item for item in topic["checklist"] if item["requirement"] == "finalite")

    assert finalite["present"] is True
    assert finalite["evidence"]["reference"] == "Page 2"
    assert "controle d'acces par badge" in finalite["evidence"]["text"]


def test_build_rgpd_analysis_aggregates_multiple_documents_and_counts_gaps() -> None:
    documents = [
        {
            "name": "doc_avec_camera.txt",
            "text": "Des cameras de videosurveillance filment l'entree du batiment.",
        },
        {
            "name": "doc_sans_sujet.txt",
            "text": "Ce document traite uniquement des horaires d'ouverture du restaurant d'entreprise.",
        },
    ]

    result = rgpd.build_rgpd_analysis(documents)

    assert result["documents_analyzed"] == 2
    assert result["total_gaps_found"] > 0
    assert result["disclaimer"]
    names = {report["document_name"] for report in result["documents"]}
    assert names == {"doc_avec_camera.txt", "doc_sans_sujet.txt"}


def test_build_rgpd_analysis_ignores_non_mapping_entries() -> None:
    result = rgpd.build_rgpd_analysis([{"name": "ok.txt", "text": "sans sujet sensible"}, "not-a-document", None])
    assert result["documents_analyzed"] == 1


def test_build_rgpd_corpus_scan_runs_against_the_real_local_index() -> None:
    result = rgpd.build_rgpd_corpus_scan()

    assert "documents_scanned" in result
    assert "documents_with_findings" in result
    assert result["documents_with_findings"] == len(result["documents"])
    for report in result["documents"]:
        assert report["no_sensitive_topic_detected"] is False
        assert report["topics"]
