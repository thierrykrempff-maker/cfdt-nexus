"""RGPD/CNIL compliance checklist analysis for accords and uploaded documents.

Deterministic and keyword-based, like the rest of Nexus: no LLM, nothing
invented. For each personal-data topic actually found in a document's own
text (video surveillance, geolocalisation, controle d'acces, biometrie,
cybersurveillance, donnees de sante, communication syndicale, elections
professionnelles, registre des traitements, gestion du personnel), this
checks whether the mentions CNIL/Code du travail guidance expects nearby
(finalite, duree de conservation, information des salaries, consultation du
CSE, droits d'acces...) are literally present in the text, quoting the real
passage as evidence. A missing mention is reported as "absent du texte
fourni", never as a legal conclusion: the analysis only ever describes what
the document does or does not say.
"""

from __future__ import annotations

import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "automation" / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import cnil_connector as cnil  # noqa: E402  (reuse the curated topic taxonomy + CNIL urls)


def _normalize(value: object) -> str:
    decomposed = unicodedata.normalize("NFKD", str(value or ""))
    return " ".join(
        "".join(char for char in decomposed if not unicodedata.combining(char))
        .lower()
        .replace("’", " ")
        .replace("'", " ")
        .split()
    )


REQUIREMENT_LABELS: dict[str, str] = {
    "finalite": "Finalite du dispositif precisee",
    "duree_conservation": "Duree de conservation des donnees precisee",
    "information_salaries": "Information prealable des salaries",
    "consultation_cse": "Consultation ou avis du CSE",
    "droits_acces": "Droits d'acces et de rectification rappeles",
    "confidentialite_medicale": "Confidentialite / secret medical rappele",
}

REQUIREMENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "finalite": (
        "finalite", "a pour objet de", "a pour but de", "objectif du dispositif",
        "a pour finalite", "vise a", "dans le but de", "afin d assurer", "afin de garantir",
    ),
    "duree_conservation": (
        "duree de conservation", "delai de conservation", "conservees pendant",
        "conserve pendant", "conservation des donnees", "duree maximale de conservation",
    ),
    "information_salaries": (
        "information des salaries", "informe les salaries", "information prealable",
        "note d information", "prealablement informes", "porte a la connaissance",
        "salaries sont informes", "salaries informes", "personnel est informe",
        "informes prealablement",
    ),
    "consultation_cse": (
        "consultation du cse", "avis du cse", "consulte le cse", "apres avis du cse",
        "information consultation", "comite social et economique a ete consulte",
        "cse a ete consulte", "cse a ete informe et consulte", "avis prealable du cse",
    ),
    "droits_acces": (
        "droit d acces", "droit de rectification", "droit d opposition",
        "droits des salaries", "droit a la portabilite",
    ),
    "confidentialite_medicale": (
        "secret medical", "confidentialite medicale", "secret professionnel",
        "medecin du travail uniquement", "seul le medecin du travail",
    ),
}

# Which of the requirements above actually apply to each CNIL_PAGES topic.
# Topics not listed here (or mapped to an empty tuple) are not checked
# against a checklist - e.g. the CNIL sanction example page is illustrative
# case law, not a document topic with mandatory mentions of its own.
TOPIC_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "videosurveillance_travail": (
        "finalite", "duree_conservation", "information_salaries", "consultation_cse",
    ),
    "geolocalisation_vehicules": (
        "finalite", "duree_conservation", "information_salaries", "consultation_cse",
    ),
    "controle_horaires_acces": (
        "finalite", "duree_conservation", "information_salaries", "consultation_cse",
    ),
    "controle_acces_biometrique": (
        "finalite", "duree_conservation", "information_salaries", "consultation_cse",
    ),
    "gestion_activite_equipements": (
        "finalite", "duree_conservation", "information_salaries", "consultation_cse",
    ),
    "intranet_messagerie_syndicats": ("finalite", "information_salaries"),
    "elections_pro_donnees": ("finalite", "duree_conservation"),
    "registre_traitements": ("finalite", "duree_conservation", "droits_acces"),
    "gestion_personnel": ("finalite", "duree_conservation", "droits_acces"),
    "donnees_sante_pratique": ("finalite", "confidentialite_medicale", "droits_acces"),
    "sanction_surveillance_excessive": (),
}


def _passages_of(document: Mapping[str, Any]) -> list[dict[str, str]]:
    raw_passages = document.get("passages")
    if isinstance(raw_passages, list) and raw_passages:
        return [
            {
                "reference": str(item.get("reference") or ""),
                "text": str(item.get("text") or ""),
            }
            for item in raw_passages
            if isinstance(item, Mapping) and item.get("text")
        ]
    text = document.get("text")
    return [{"reference": "", "text": str(text)}] if text else []


def _topic_hits(passages: Sequence[Mapping[str, str]]) -> dict[str, list[dict[str, str]]]:
    hits: dict[str, list[dict[str, str]]] = {}
    for passage in passages:
        normalized = _normalize(passage.get("text"))
        if not normalized:
            continue
        for page in cnil.CNIL_PAGES:
            topic_id = page["id"]
            if not TOPIC_REQUIREMENTS.get(topic_id):
                continue
            if any(_normalize(keyword) in normalized for keyword in page["keywords"]):
                hits.setdefault(topic_id, []).append(
                    {"reference": passage.get("reference") or "", "text": passage.get("text") or ""}
                )
    return hits


def _requirement_evidence(
    full_text_normalized: str,
    passages: Sequence[Mapping[str, str]],
    requirement: str,
) -> dict[str, str] | None:
    keywords = REQUIREMENT_KEYWORDS.get(requirement, ())
    if not any(_normalize(keyword) in full_text_normalized for keyword in keywords):
        return None
    for passage in passages:
        normalized = _normalize(passage.get("text"))
        if any(_normalize(keyword) in normalized for keyword in keywords):
            return {"reference": passage.get("reference") or "", "text": passage.get("text") or ""}
    return None


def analyze_document_rgpd(document: Mapping[str, Any]) -> dict[str, Any]:
    passages = _passages_of(document)
    full_text_normalized = _normalize(document.get("text") or " ".join(p["text"] for p in passages))
    topic_hits = _topic_hits(passages)

    topics_report: list[dict[str, Any]] = []
    for page in cnil.CNIL_PAGES:
        topic_id = page["id"]
        requirements = TOPIC_REQUIREMENTS.get(topic_id, ())
        hits = topic_hits.get(topic_id)
        if not hits or not requirements:
            continue
        checklist = []
        missing_count = 0
        for requirement in requirements:
            evidence = _requirement_evidence(full_text_normalized, passages, requirement)
            present = evidence is not None
            if not present:
                missing_count += 1
            checklist.append(
                {
                    "requirement": requirement,
                    "label": REQUIREMENT_LABELS[requirement],
                    "present": present,
                    "evidence": evidence,
                }
            )
        topics_report.append(
            {
                "topic_id": topic_id,
                "cnil_reference_url": page["url"],
                "excerpts": hits[:3],
                "checklist": checklist,
                "missing_count": missing_count,
                "requirement_count": len(requirements),
                "risk_level": (
                    "eleve" if missing_count >= 3
                    else "moyen" if missing_count >= 1
                    else "faible"
                ),
            }
        )

    topics_report.sort(key=lambda item: item["missing_count"], reverse=True)
    return {
        "document_name": document.get("name") or document.get("document_name"),
        "topics_detected": len(topics_report),
        "topics": topics_report,
        "no_sensitive_topic_detected": not topics_report,
    }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


DISCLAIMER = (
    "Analyse automatique fondee uniquement sur le texte fourni : elle verifie la "
    "presence litterale des mentions attendues (finalite, duree de conservation, "
    "information des salaries, consultation du CSE...), sans jugement juridique. "
    "L'absence d'une mention dans ce texte ne prouve pas une non-conformite : elle "
    "peut figurer dans un autre document (registre des traitements, note RH, "
    "reglement interieur). A verifier avant toute conclusion."
)


def build_rgpd_analysis(documents: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    reports = [
        analyze_document_rgpd(document)
        for document in documents
        if isinstance(document, Mapping)
    ]
    total_gaps = sum(
        sum(1 for topic in report["topics"] for item in topic["checklist"] if not item["present"])
        for report in reports
    )
    return {
        "generated_at": _utc_now(),
        "documents": reports,
        "documents_analyzed": len(reports),
        "total_gaps_found": total_gaps,
        "disclaimer": DISCLAIMER,
    }


def build_rgpd_corpus_scan(limit_documents: int | None = None) -> dict[str, Any]:
    """Run the same checklist over every document already indexed locally."""

    import agreements_bible as bible  # noqa: E402  (path already extended above)

    chunks_path = bible.INDEX_DIR / "chunks.private.jsonl"
    chunks = bible.read_jsonl(chunks_path) if chunks_path.exists() else []

    by_document: dict[str, list[dict[str, str]]] = {}
    order: list[str] = []
    for chunk in chunks:
        name = str(chunk.get("filename") or chunk.get("relative_path") or chunk.get("document_id") or "")
        if not name:
            continue
        if name not in by_document:
            by_document[name] = []
            order.append(name)
        page = chunk.get("page")
        reference = f"Page {page}" if page else ""
        text = str(chunk.get("text") or "")
        if text:
            by_document[name].append({"reference": reference, "text": text})

    names = order[:limit_documents] if limit_documents else order
    documents = [
        {
            "name": name,
            "text": "\n\n".join(passage["text"] for passage in by_document[name]),
            "passages": by_document[name],
        }
        for name in names
    ]

    result = build_rgpd_analysis(documents)
    all_reports = result["documents"]
    result["documents_scanned"] = len(by_document)
    result["documents"] = [report for report in all_reports if not report["no_sensitive_topic_detected"]]
    result["documents_with_findings"] = len(result["documents"])
    result["index_available"] = bool(chunks)
    return result
