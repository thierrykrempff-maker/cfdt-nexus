"""Structured report generator for real Nexus V2.1 analysis payloads."""

from __future__ import annotations

import re
from typing import Any, Iterable

from .utils import normalize, source_label, unique


REPORT_VERSION = "2.2"


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def text_items(values: Iterable[Any], limit: int | None = None) -> list[str]:
    return unique((str(value).strip() for value in values if str(value or "").strip()), limit=limit)


def strip_known_prefix(value: Any) -> str:
    text = str(value or "").strip()
    return re.sub(r"^(Regle certaine|Interpretation|Hypothese|Information manquante|Risque)\s*:\s*", "", text)


def prefixed(values: Iterable[Any], prefix: str) -> list[str]:
    prefix_key = normalize(prefix)
    return text_items(
        strip_known_prefix(value)
        for value in values
        if normalize(str(value)).startswith(prefix_key)
    )


def unprefixed(values: Iterable[Any]) -> list[str]:
    return text_items(strip_known_prefix(value) for value in values)


def active(expert: dict[str, Any] | None) -> bool:
    return bool(expert and expert.get("active"))


def title_from_payload(answer: dict[str, Any], orchestration: dict[str, Any]) -> str:
    domains = orchestration.get("domaines_detectes") or answer.get("route", {}).get("domains", [])
    business_domains = [str(domain) for domain in domains if domain and domain != "bible_accords"]
    if business_domains:
        return "Dossier salarie - " + ", ".join(business_domains[:3])
    return "Dossier salarie - analyse Nexus"


def source_items(answer: dict[str, Any], orchestration: dict[str, Any]) -> list[str]:
    raw_sources = answer.get("sources", [])
    values: list[str] = []
    for source in raw_sources:
        if isinstance(source, dict):
            parts = [source_label(source)]
            if source.get("origin"):
                parts.append(f"origine {source['origin']}")
            if source.get("match_score") is not None:
                parts.append(f"score {source['match_score']}")
            if source.get("excerpt"):
                parts.append(str(source["excerpt"]))
            values.append(" | ".join(parts))
        else:
            values.append(str(source))
    if not values:
        values.extend(str(item) for item in orchestration.get("sources", []))
    return text_items(values, limit=12)


def juriste_section(juriste: dict[str, Any]) -> list[dict[str, Any]]:
    if not active(juriste):
        return []
    return [
        {"title": "Reponse courte Juriste", "items": as_list(juriste.get("response_courte"))},
        {"title": "Qualification juridique", "items": as_list(juriste.get("qualification_juridique_situation"))},
        {"title": "Analyse et raisonnement", "items": juriste.get("analyse_et_raisonnement", [])},
        {"title": "Risques et vigilance", "items": juriste.get("risques_points_vigilance", [])},
    ]


def paie_section(paie_expert: dict[str, Any]) -> list[dict[str, Any]]:
    if not active(paie_expert):
        return []
    return [
        {"title": "Objet du controle paie", "items": as_list(paie_expert.get("objet_du_controle"))},
        {"title": "Elements du bulletin concernes", "items": paie_expert.get("elements_du_bulletin_concernes", [])},
        {"title": "Methode de controle", "items": paie_expert.get("methode_de_controle", [])},
        {"title": "Calcul detaille", "items": as_list(paie_expert.get("calcul_detaille"))},
    ]


def collect_report_values(payload: dict[str, Any]) -> dict[str, list[str]]:
    answer = payload.get("answer", {})
    orchestration = payload.get("orchestration", {})
    juriste = payload.get("expert_juriste", {})
    paie_expert = payload.get("expert_paie", {})
    reasoning = as_list(juriste.get("analyse_et_raisonnement")) if active(juriste) else []

    established = []
    if active(juriste):
        established.extend(as_list(juriste.get("ce_qui_est_etabli_par_sources")))
        established.extend(prefixed(reasoning, "Regle certaine"))
    if answer.get("sources"):
        established.append("Des sources locales ont ete remontees par le routeur Nexus.")

    interpretations = prefixed(reasoning, "Interpretation") if active(juriste) else []
    hypotheses = prefixed(reasoning, "Hypothese") if active(juriste) else []
    if active(paie_expert):
        hypotheses.extend(str(item) for item in paie_expert.get("anomalies_potentielles", []))

    missing = []
    if active(juriste):
        missing.extend(as_list(juriste.get("ce_qui_depend_accord_statut_element_manquant")))
        missing.extend(prefixed(reasoning, "Information manquante"))
    if active(paie_expert):
        missing.extend(str(item) for item in paie_expert.get("donnees_necessaires_au_calcul", []))

    return {
        "points_etablis": unprefixed(established),
        "interpretations": text_items(interpretations),
        "hypotheses": text_items(hypotheses),
        "informations_manquantes": unprefixed(missing),
        "pieces_a_recuperer": text_items(orchestration.get("documents_necessaires", []), limit=16),
        "questions_direction": text_items(orchestration.get("questions_utiles", []), limit=16),
        "limites": text_items(orchestration.get("limites", []), limit=16),
    }


def section(section_id: str, title: str, items: Iterable[Any] | Any) -> dict[str, Any]:
    values = text_items(as_list(items))
    return {
        "id": section_id,
        "title": title,
        "items": values or ["Aucun element distinct remonte par l'analyse Nexus a ce stade."],
    }


def build_report(payload: dict[str, Any]) -> dict[str, Any]:
    answer = payload.get("answer", {})
    orchestration = payload.get("orchestration", {})
    juriste = payload.get("expert_juriste", {})
    paie_expert = payload.get("expert_paie", {})
    collected = collect_report_values(payload)
    domains = orchestration.get("domaines_detectes") or answer.get("route", {}).get("domains", [])
    experts = orchestration.get("experts_mobilises", [])
    title = title_from_payload(answer, orchestration)

    sections = [
        section("titre", "Titre du dossier", title),
        section("question", "Question", orchestration.get("question_posee") or answer.get("query")),
        section("resume", "Resume du probleme", answer.get("understanding") or orchestration.get("reponse_synthetique_nexus")),
        section("domaines", "Domaines detectes", domains),
        section("experts", "Experts reellement mobilises", experts),
        section("synthese", "Synthese Nexus", orchestration.get("reponse_synthetique_nexus")),
        section("points_etablis", "Points etablis", collected["points_etablis"]),
        section("interpretations", "Interpretations", collected["interpretations"]),
        section("hypotheses", "Hypotheses", collected["hypotheses"]),
        section("informations_manquantes", "Informations manquantes", collected["informations_manquantes"]),
        section("pieces", "Pieces a recuperer", collected["pieces_a_recuperer"]),
        section("questions_direction", "Questions a poser a la direction", collected["questions_direction"]),
        section("position", "Position de travail", orchestration.get("position_de_travail") or answer.get("working_position")),
        section("conclusion", "Conclusion provisoire", provisional_conclusion(orchestration)),
        section("sources", "Sources reellement remontees par Nexus", source_items(answer, orchestration)),
        section("confiance", "Niveau de confiance", orchestration.get("niveau_de_confiance") or answer.get("confidence")),
        section("limites", "Limites", collected["limites"]),
    ]

    expert_sections = {
        "juriste": juriste_section(juriste),
        "paie": paie_section(paie_expert),
    }
    report = {
        "version": REPORT_VERSION,
        "title": title,
        "inputs": {
            "router_version": answer.get("route", {}).get("router_version"),
            "router_query": answer.get("query"),
            "source_count": len(answer.get("sources", [])),
            "juriste_active": active(juriste),
            "paie_active": active(paie_expert),
        },
        "generated_from": generated_from(juriste, paie_expert),
        "sections": sections,
        "expert_sections": expert_sections,
    }
    report["markdown"] = render_markdown(report)
    return report


def generated_from(juriste: dict[str, Any], paie_expert: dict[str, Any]) -> list[str]:
    steps = [
        "apps/nexus-local-interface/server.py: analyze_question",
        "automation/scripts/assistant_ds_router.py: ask --format json",
        "automation/experts/orchestrator.py: orchestrate",
    ]
    if active(juriste):
        steps.append("automation/experts/juriste_travail.py: enrich")
    if active(paie_expert):
        steps.append("automation/experts/paie.py: enrich")
    steps.append("automation/experts/report_generator.py: build_report")
    return steps


def provisional_conclusion(orchestration: dict[str, Any]) -> str:
    confidence = str(orchestration.get("niveau_de_confiance") or "a verifier")
    synthesis = str(orchestration.get("reponse_synthetique_nexus") or "").strip()
    if confidence == "faible":
        return "Conclusion provisoire limitee : informations insuffisantes pour conclure. " + synthesis
    return "Conclusion provisoire Nexus : " + synthesis


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# {report['title']}",
        "",
        f"- Version rapport : {report['version']}",
        "- Flux reel : " + " -> ".join(report.get("generated_from", [])),
        "",
    ]
    for item in report.get("sections", []):
        lines.extend(render_section(item["title"], item.get("items", [])))
    expert_sections = report.get("expert_sections", {})
    if expert_sections.get("juriste"):
        lines.extend(["## Analyse Juriste reelle", ""])
        for item in expert_sections["juriste"]:
            lines.extend(render_section(item["title"], item.get("items", []), level=3))
    if expert_sections.get("paie"):
        lines.extend(["## Analyse Paie reelle", ""])
        for item in expert_sections["paie"]:
            lines.extend(render_section(item["title"], item.get("items", []), level=3))
    return "\n".join(lines).strip() + "\n"


def render_section(title: str, items: Iterable[Any], level: int = 2) -> list[str]:
    marker = "#" * level
    lines = [f"{marker} {title}", ""]
    values = text_items(items)
    if not values:
        lines.append("- Aucun element distinct remonte par l'analyse Nexus a ce stade.")
    elif len(values) == 1:
        lines.append(str(values[0]))
    else:
        lines.extend(f"- {value}" for value in values)
    lines.append("")
    return lines
