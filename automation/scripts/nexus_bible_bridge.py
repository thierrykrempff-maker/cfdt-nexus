#!/usr/bin/env python
"""
CFDT Nexus local bridge:
Document / CSE topic -> Bible Accords Sarralbe.

This script is local-only. It never sends private documents to an external API and
never writes real document content into Git. Generated reports stay under
local-index/agreements/integration/.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import agreements_bible as bible


BRIDGE_DIR = bible.LOCAL_ROOT / "integration"
BRIDGE_REPORT_DIR = BRIDGE_DIR / "reports"
BRIDGE_TEST_DIR = BRIDGE_DIR / "tests"

PRUDENCE_WARNING = (
    "L'analyse automatique constitue une aide à la préparation. Vérifier les textes cités, "
    "leur date, leur champ d'application et leur articulation avec les normes supérieures "
    "avant toute position définitive en CSE, CSSCT ou négociation."
)

SOURCE_FOUND = "SOURCE LOCALE TROUVÉE"
SOURCE_TO_VERIFY = "SOURCE LOCALE À VÉRIFIER"
NO_RELEVANT_SOURCE = "AUCUNE SOURCE LOCALE PERTINENTE TROUVÉE"


THEME_RULES = [
    {
        "theme": "temps de travail / repos / 5x8",
        "patterns": [
            "repos entre postes",
            "repos entre deux postes",
            "repos quotidien",
            "changement de cycle",
            "cycle de travail",
            "modification des horaires",
            "horaires postés",
            "horaires postes",
            "5x8",
            "travail posté",
            "travail poste",
            "travail de nuit",
            "temps de repos",
        ],
        "queries": [
            "repos entre deux postes",
            "temps de travail 5x8 horaires postés",
            "repos quotidien travail posté",
            "travail de nuit organisation du travail",
        ],
        "comparison_points": [
            "disposition actuelle sur l'organisation du travail",
            "proposition nouvelle sur les horaires ou le repos",
            "compatibilité à vérifier avec les textes locaux 5x8 / temps de travail",
            "impact possible sur fatigue, vie familiale et sécurité",
        ],
        "questions": [
            "Quel est le changement concret demandé par rapport à l'organisation actuelle ?",
            "Quels salariés, équipes ou cycles sont concernés ?",
            "Quel délai de prévenance et quelle période de test sont prévus ?",
            "Quel impact sur le repos quotidien, le travail de nuit et la fatigue ?",
        ],
        "documents_to_request": [
            "planning actuel et projeté",
            "note de présentation détaillée",
            "analyse d'impact santé-sécurité",
            "liste des populations concernées",
        ],
    },
    {
        "theme": "astreinte",
        "patterns": [
            "astreinte",
            "intervention",
            "indemnisation des interventions",
            "régime d'astreinte",
            "regime d'astreinte",
        ],
        "queries": [
            "astreinte indemnisation interventions",
            "régime d'astreinte intervention",
            "temps d'intervention astreinte",
        ],
        "comparison_points": [
            "régime actuel d'astreinte",
            "indemnisation proposée ou modifiée",
            "articulation temps d'intervention / temps de repos",
        ],
        "questions": [
            "Quelles catégories de salariés seraient concernées ?",
            "L'indemnisation change-t-elle ?",
            "Comment le repos après intervention est-il garanti ?",
        ],
        "documents_to_request": [
            "projet d'organisation des astreintes",
            "barème d'indemnisation",
            "bilan des interventions passées",
        ],
    },
    {
        "theme": "disciplinaire / règlement intérieur",
        "patterns": [
            "sanction",
            "discipline",
            "disciplinaire",
            "avertissement",
            "mise à pied",
            "mise a pied",
            "entretien disciplinaire",
            "règlement intérieur",
            "reglement interieur",
        ],
        "queries": [
            "règlement intérieur procédure disciplinaire sanction avertissement",
            "entretien disciplinaire avertissement",
            "mise à pied disciplinaire procédure",
        ],
        "comparison_points": [
            "faits reprochés",
            "procédure prévue par le règlement intérieur",
            "sanction envisagée",
            "délais et garanties de défense",
        ],
        "questions": [
            "Quels faits précis sont reprochés et à quelle date ?",
            "Le salarié a-t-il été convoqué et informé de l'objet de l'entretien ?",
            "Quels éléments de preuve existent ?",
        ],
        "documents_to_request": [
            "convocation",
            "éléments reprochés",
            "règlement intérieur applicable",
            "témoignages ou éléments de contexte",
        ],
    },
    {
        "theme": "relations collectives / droit syndical",
        "patterns": [
            "cse",
            "heures de délégation",
            "heures de delegation",
            "crédit d'heures",
            "credit d'heures",
            "moyens syndicaux",
            "droit syndical",
            "mandat",
            "représentant du personnel",
            "representant du personnel",
            "rp",
            "délégué syndical",
            "delegue syndical",
            "représentant syndical",
            "representant syndical",
            "élu cse",
            "elu cse",
        ],
        "queries": [
            "heures de délégation droit syndical",
            "crédit d'heures mandat représentant du personnel",
            "accord CSE moyens syndicaux",
            "représentant syndical délégué syndical",
        ],
        "comparison_points": [
            "moyens actuels des représentants",
            "heures ou crédits d'heures concernés",
            "mandats et populations concernées",
            "articulation avec accord CSE / droit syndical",
        ],
        "questions": [
            "Quels mandats ou représentants sont concernés ?",
            "Le crédit d'heures est-il modifié, déplacé ou conditionné ?",
            "La consultation du CSE ou des organisations syndicales est-elle prévue ?",
        ],
        "documents_to_request": [
            "projet de modification des moyens",
            "accord CSE ou droit syndical applicable",
            "état actuel des crédits d'heures",
        ],
    },
    {
        "theme": "rémunération / primes",
        "patterns": [
            "rémunération",
            "remuneration",
            "salaire",
            "salaires",
            "prime",
            "primes",
            "majoration",
            "dimanche",
            "jour férié",
            "jour ferie",
            "nuit",
            "intéressement",
            "interessement",
            "participation",
        ],
        "queries": [
            "rémunération salaires primes",
            "prime de nuit majoration dimanche jour férié",
            "intéressement participation épargne salariale",
        ],
        "comparison_points": [
            "disposition actuelle sur rémunération ou prime",
            "montant ou condition proposé",
            "population bénéficiaire ou exclue",
        ],
        "questions": [
            "Quel montant ou quelle formule change ?",
            "Quels salariés sont concernés ?",
            "La mesure est-elle pérenne ou temporaire ?",
        ],
        "documents_to_request": [
            "note de calcul",
            "périmètre salariés concernés",
            "texte projeté",
        ],
    },
]


SCENARIOS = [
    {
        "id": "test-1-repos-5x8",
        "kind": "cse",
        "title": "Modification du repos entre deux postes",
        "text": "La direction souhaite modifier le repos entre deux postes pour les salariés en 5x8.",
        "expected": "les textes 5x8 et temps de travail doivent remonter prioritairement",
    },
    {
        "id": "test-2-astreinte",
        "kind": "cse",
        "title": "Modification astreinte",
        "text": "La direction envisage une modification du régime d'astreinte et de l'indemnisation des interventions.",
        "expected": "l'accord Astreinte doit être prioritaire",
    },
    {
        "id": "test-3-discipline",
        "kind": "document",
        "title": "Procédure disciplinaire",
        "text": "Un salarié fait l'objet d'une procédure disciplinaire pouvant conduire à un avertissement.",
        "expected": "le règlement intérieur doit être prioritaire",
    },
    {
        "id": "test-4-droit-syndical",
        "kind": "cse",
        "title": "Moyens de délégation",
        "text": "Modification des moyens et heures de délégation des représentants du personnel.",
        "expected": "accord CSE et textes RP/droit syndical prioritaires",
    },
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")


def ensure_dirs() -> None:
    bible.ensure_dirs()
    for directory in [BRIDGE_DIR, BRIDGE_REPORT_DIR, BRIDGE_TEST_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def write_private_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize(value: str) -> str:
    return bible.normalize(value)


def detect_themes(text: str) -> list[dict[str, Any]]:
    normalized = normalize(text)
    detected = []
    for rule in THEME_RULES:
        hits = []
        for pattern in rule["patterns"]:
            if normalize(pattern) in normalized:
                hits.append(pattern)
        if hits:
            detected.append(
                {
                    "theme": rule["theme"],
                    "matched_terms": hits,
                    "queries": rule["queries"],
                    "comparison_points": rule["comparison_points"],
                    "questions": rule["questions"],
                    "documents_to_request": rule["documents_to_request"],
                }
            )
    return detected


def generated_queries(text: str, themes: list[dict[str, Any]]) -> list[str]:
    queries = []
    for theme in themes:
        queries.extend(theme["queries"])
    if not queries:
        queries.append(text[:180])
    seen = set()
    deduped = []
    for query in queries:
        key = normalize(query)
        if key not in seen:
            seen.add(key)
            deduped.append(query)
    return deduped


def search_bible(query: str, limit: int) -> list[dict[str, Any]]:
    chunks = bible.read_jsonl(bible.INDEX_DIR / "chunks.private.jsonl")
    query_tokens = bible.tokenize(query)
    if not query_tokens:
        return []

    rows = []
    for chunk in chunks:
        details = bible.score_chunk_details(chunk, query_tokens, query)
        if details["total"] <= 0:
            continue
        rows.append((details["total"], chunk, details))
    rows.sort(key=lambda item: item[0], reverse=True)
    sources = []
    for score, chunk, details in rows[:limit]:
        source = bible.format_source(score, chunk, query_tokens, details)
        source["source_status"] = classify_source(score, source)
        source["confidence_level"] = confidence_level(score)
        sources.append(source)
    return sources


def classify_source(score: float, source: dict[str, Any]) -> str:
    if score >= 50 and source.get("page"):
        return SOURCE_FOUND
    if score > 0:
        return SOURCE_TO_VERIFY
    return NO_RELEVANT_SOURCE


def confidence_level(score: float) -> str:
    if score >= 150:
        return "fort"
    if score >= 70:
        return "moyen"
    return "faible"


def merge_sources(searches: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    by_chunk = {}
    for search in searches:
        for source in search["sources"]:
            chunk_id = source.get("chunk_id")
            if not chunk_id:
                continue
            existing = by_chunk.get(chunk_id)
            if existing is None or source["match_score"] > existing["match_score"]:
                merged = dict(source)
                merged["matched_query"] = search["query"]
                by_chunk[chunk_id] = merged
    return sorted(by_chunk.values(), key=lambda item: item["match_score"], reverse=True)[:limit]


def main_subject(text: str, themes: list[dict[str, Any]]) -> str:
    return themes[0]["theme"] if themes else "sujet à qualifier"


def inferred_intent(text: str, themes: list[dict[str, Any]]) -> str:
    if not themes:
        return "Le document ou point semble présenter un sujet nécessitant qualification humaine."
    theme_names = ", ".join(theme["theme"] for theme in themes[:3])
    return f"Le document ou point semble présenter ou modifier un sujet lié à : {theme_names}."


def comparison_points(themes: list[dict[str, Any]]) -> list[str]:
    points = []
    for theme in themes:
        points.extend(theme["comparison_points"])
    base = [
        "disposition actuelle",
        "proposition nouvelle",
        "différence détectée",
        "compatibilité à vérifier",
        "articulation à analyser",
        "conséquence possible",
        "bénéficiaire probable du changement",
        "risque salarié",
        "avantage éventuel",
        "point ambigu",
    ]
    return dedupe(points + base)


def questions_for(themes: list[dict[str, Any]]) -> list[str]:
    questions = []
    for theme in themes:
        questions.extend(theme["questions"])
    return dedupe(questions + ["Quelle est la base juridique ou conventionnelle invoquée par la direction ?"])


def documents_to_request(themes: list[dict[str, Any]]) -> list[str]:
    docs = []
    for theme in themes:
        docs.extend(theme["documents_to_request"])
    return dedupe(docs + ["texte projeté", "note d'impact", "calendrier de mise en œuvre"])


def dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        key = normalize(value)
        if key and key not in seen:
            seen.add(key)
            result.append(value)
    return result


def build_document_analysis(title: str, text: str, limit: int) -> dict[str, Any]:
    themes = detect_themes(text)
    queries = generated_queries(text, themes)
    searches = [{"query": query, "sources": search_bible(query, limit)} for query in queries]
    sources = merge_sources(searches, limit)
    source_status = sources[0]["source_status"] if sources else NO_RELEVANT_SOURCE
    return {
        "kind": "document-analysis",
        "generated_at": now_iso(),
        "title": title,
        "prudence_warning": PRUDENCE_WARNING,
        "source_status": source_status,
        "A_sujet_principal": main_subject(text, themes),
        "B_ce_que_le_document_semble_vouloir_modifier_ou_presenter": inferred_intent(text, themes),
        "C_textes_locaux_potentiellement_concernes": sources,
        "D_points_de_comparaison": comparison_points(themes),
        "detected_themes": themes,
        "generated_queries": queries,
        "points_to_verify": [
            "Vérifier la date et le champ d'application des textes cités.",
            "Vérifier s'il existe un accord, avenant ou usage plus récent.",
            "Ne pas conclure à une violation juridique sans analyse humaine.",
        ],
        "security_notice": "Private local analysis. Do not commit generated reports.",
    }


def build_cse_analysis(title: str, text: str, limit: int) -> dict[str, Any]:
    base = build_document_analysis(title, text, limit)
    sources = base["C_textes_locaux_potentiellement_concernes"]
    return {
        "kind": "cse-point-analysis",
        "generated_at": now_iso(),
        "point_cse": title,
        "prudence_warning": PRUDENCE_WARNING,
        "source_status": base["source_status"],
        "1_ce_que_la_direction_semble_vouloir_presenter": base["B_ce_que_le_document_semble_vouloir_modifier_ou_presenter"],
        "2_ce_que_nous_savons": {
            "sujet": base["A_sujet_principal"],
            "themes_detectes": [theme["theme"] for theme in base["detected_themes"]],
            "requêtes_bible": base["generated_queries"],
        },
        "3_ce_que_disent_les_textes_locaux": sources,
        "4_accords_lies": [
            {
                "document": source.get("document"),
                "page": source.get("page"),
                "article": source.get("article_or_section"),
                "pertinence": source.get("match_score"),
                "niveau_de_confiance": source.get("confidence_level"),
            }
            for source in sources
        ],
        "5_questions_a_poser_a_la_direction": questions_for(base["detected_themes"]),
        "6_questions_de_relance_selon_reponse": [
            "Pouvez-vous préciser la base du changement proposé ?",
            "Pouvez-vous confirmer que les textes locaux cités ont été pris en compte ?",
            "Quels éléments mesurables permettront d'évaluer l'impact pour les salariés ?",
        ],
        "7_documents_complementaires_a_demander": documents_to_request(base["detected_themes"]),
        "8_risques_pour_les_salaries": [
            "risque à qualifier après lecture des textes cités",
            "compatibilité à vérifier avec les accords locaux",
            "impact concret à objectiver avant position définitive",
        ],
        "9_opportunites_eventuelles": [
            "clarifier les règles applicables",
            "obtenir des garanties écrites",
            "préparer une position CFDT argumentée",
        ],
        "10_position_cfdt_a_construire": "Position à construire après vérification humaine des sources et échanges avec les salariés concernés.",
        "11_avis_motive_requis": "à vérifier",
        "12_informations_manquantes_avant_de_prendre_position": documents_to_request(base["detected_themes"]),
        "security_notice": "Private local CSE analysis. Do not commit generated reports.",
    }


def extract_document_text(path: Path) -> str:
    extension = path.suffix.lower()
    if extension == ".pdf":
        pages, _ = bible.extract_pdf(path)
    elif extension == ".docx":
        pages, _ = bible.extract_docx(path)
    elif extension == ".txt":
        pages, _ = bible.extract_txt(path)
    else:
        raise SystemExit("Format non supporté pour l'analyse documentaire V1.")
    return "\n\n".join(page.get("text", "") for page in pages).strip()


def print_sources(sources: list[dict[str, Any]]) -> None:
    if not sources:
        print(NO_RELEVANT_SOURCE)
        print("Ne jamais interpréter l'absence de résultat comme l'absence de droit.")
        return
    for source in sources[:8]:
        print(
            f"- {source.get('document')} | page {source.get('page')} | "
            f"{source.get('article_or_section') or 'article non détecté'} | "
            f"score {source.get('match_score')} | {source.get('source_status')}"
        )


def print_cse_summary(report: dict[str, Any]) -> None:
    print(f"POINT CSE: {report['point_cse']}")
    print(f"Statut source: {report['source_status']}")
    print(f"Sujet: {report['2_ce_que_nous_savons']['sujet']}")
    print("Textes locaux liés:")
    print_sources(report["3_ce_que_disent_les_textes_locaux"])
    print("Questions à poser:")
    for question in report["5_questions_a_poser_a_la_direction"][:6]:
        print(f"- {question}")
    print(PRUDENCE_WARNING)


def print_document_summary(report: dict[str, Any]) -> None:
    print(f"DOCUMENT: {report['title']}")
    print(f"Statut source: {report['source_status']}")
    print(f"Sujet principal: {report['A_sujet_principal']}")
    print("Textes locaux potentiellement concernés:")
    print_sources(report["C_textes_locaux_potentiellement_concernes"])
    print(PRUDENCE_WARNING)


def command_analyze_cse(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    report = build_cse_analysis(args.title or args.subject[:80], args.subject, args.limit)
    path = BRIDGE_REPORT_DIR / f"cse-analysis-{stamp()}.private.json"
    write_private_json(path, report)
    print_cse_summary(report)
    return report


def command_analyze_document(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    path = Path(args.path).expanduser()
    if not path.exists() or not path.is_file():
        raise SystemExit("Document local introuvable.")
    text = extract_document_text(path)
    if not text:
        raise SystemExit("Aucun texte exploitable extrait du document local.")
    report = build_document_analysis(args.title or path.name, text, args.limit)
    output = BRIDGE_REPORT_DIR / f"document-analysis-{stamp()}.private.json"
    write_private_json(output, report)
    print_document_summary(report)
    return report


def command_run_scenarios(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    rows = []
    for scenario in SCENARIOS:
        if scenario["kind"] == "cse":
            report = build_cse_analysis(scenario["title"], scenario["text"], args.limit)
            sources = report["3_ce_que_disent_les_textes_locaux"]
        else:
            report = build_document_analysis(scenario["title"], scenario["text"], args.limit)
            sources = report["C_textes_locaux_potentiellement_concernes"]
        rows.append(
            {
                "id": scenario["id"],
                "expected": scenario["expected"],
                "source_status": report["source_status"],
                "top_sources": [
                    {
                        "document": source.get("document"),
                        "page": source.get("page"),
                        "score": source.get("match_score"),
                        "confidence": source.get("confidence_level"),
                    }
                    for source in sources[:3]
                ],
            }
        )
    report = {
        "generated_at": now_iso(),
        "scenarios": rows,
        "prudence_warning": PRUDENCE_WARNING,
        "security_notice": "Private scenario report. Do not commit.",
    }
    write_private_json(BRIDGE_TEST_DIR / f"integration-scenarios-{stamp()}.private.json", report)
    print("SCÉNARIOS D'INTÉGRATION")
    for row in rows:
        print(f"- {row['id']} | {row['source_status']} | top sources: {len(row['top_sources'])}")
    return report


def command_diagnose(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    chunks = bible.read_jsonl(bible.INDEX_DIR / "chunks.private.jsonl")
    report = {
        "generated_at": now_iso(),
        "bible_index_available": bool(chunks),
        "chunks": len(chunks),
        "commands": [
            "python automation/scripts/nexus_bible_bridge.py analyze-cse --subject \"...\"",
            "python automation/scripts/nexus_bible_bridge.py analyze-document --path \"C:\\\\chemin\\\\document.pdf\"",
            "python automation/scripts/nexus_bible_bridge.py run-scenarios",
        ],
        "prudence_warning": PRUDENCE_WARNING,
        "security_notice": "Local integration diagnostic. Do not commit generated reports.",
    }
    write_private_json(BRIDGE_REPORT_DIR / f"integration-diagnose-{stamp()}.private.json", report)
    print(f"Bible Accords disponible: {'oui' if chunks else 'non'}")
    print(f"Chunks indexés: {len(chunks)}")
    print(PRUDENCE_WARNING)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CFDT Nexus - Bible Accords integration bridge")
    sub = parser.add_subparsers(dest="command", required=True)

    p_cse = sub.add_parser("analyze-cse")
    p_cse.add_argument("--subject", required=True)
    p_cse.add_argument("--title")
    p_cse.add_argument("--limit", type=int, default=6)

    p_doc = sub.add_parser("analyze-document")
    p_doc.add_argument("--path", required=True)
    p_doc.add_argument("--title")
    p_doc.add_argument("--limit", type=int, default=6)

    p_scenarios = sub.add_parser("run-scenarios")
    p_scenarios.add_argument("--limit", type=int, default=5)

    sub.add_parser("diagnose")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "analyze-cse":
        command_analyze_cse(args)
    elif args.command == "analyze-document":
        command_analyze_document(args)
    elif args.command == "run-scenarios":
        command_run_scenarios(args)
    elif args.command == "diagnose":
        command_diagnose(args)
    else:
        raise SystemExit(f"Commande inconnue: {args.command}")


if __name__ == "__main__":
    main()
