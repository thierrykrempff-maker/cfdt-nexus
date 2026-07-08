#!/usr/bin/env python
"""HTTP smoke tests for the Nexus local interface."""

from __future__ import annotations

import json
import threading
import unicodedata
import urllib.request

from server import NexusHandler, ThreadingHTTPServer


V2_QUESTIONS = [
    "classification",
    "Un salarie en 5x8 peut-il assister a une reunion du CSE pendant son repos, et comment ce temps doit-il etre traite ?",
    "Un salarie d'astreinte intervient la nuit, son repos est interrompu et il reprend ensuite son poste : quels sont ses droits en matiere de repos et comment l'intervention doit-elle apparaitre sur la paie ?",
]

V21_SCENARIOS = {
    "juriste_seul": "Un salarié peut-il contester sa classification si les fonctions réellement exercées dépassent sa fiche de poste ?",
    "paie_seul": "Je pense qu’il manque des heures de nuit et une majoration dimanche sur mon bulletin. Que faut-il contrôler ?",
    "juriste_paie": "Un salarié d’astreinte intervient la nuit puis reprend son poste : repos et paie ?",
    "question_incomplete": "Ma prime est fausse.",
}


def normalize(value: object) -> str:
    text = str(value or "").casefold()
    text = unicodedata.normalize("NFKD", text)
    return "".join(char for char in text if not unicodedata.combining(char))


def post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=240) as response:  # noqa: S310 - localhost test.
        return json.loads(response.read().decode("utf-8"))


def assert_base_payload(payload: dict[str, object]) -> None:
    assert payload.get("ok") is True
    assert payload.get("answer")
    assert payload.get("orchestration")
    assert payload.get("analysis_report")
    answer = payload["answer"]
    orchestration = payload["orchestration"]
    report = payload["analysis_report"]
    assert answer["short_answer"]
    assert answer["sources"]
    assert answer["source_layers"]
    assert answer["confidence"]
    assert orchestration["reponse_synthetique_nexus"]
    assert orchestration["domaines_detectes"]
    assert "niveau_de_confiance" in orchestration
    assert report["inputs"]["router_version"] == answer["route"]["router_version"]
    assert report["inputs"]["source_count"] == len(answer["sources"])
    assert "automation/scripts/assistant_ds_router.py: ask --format json" in report["generated_from"]
    assert "automation/experts/orchestrator.py: orchestrate" in report["generated_from"]
    assert "automation/experts/report_generator.py: build_report" in report["generated_from"]
    assert "TOPIC_RULES" not in report["markdown"]
    assert "CFDT_NEXUS_SALARY_ANALYSIS_V22" not in report["markdown"]
    assert report_section(report, "sources")["items"]
    assert report_section(report, "source_layers")["items"]
    assert report_section(report, "synthese")["items"][0] == orchestration["reponse_synthetique_nexus"]
    assert "source_layers" in orchestration
    for source in answer["sources"]:
        assert "source_layer" in source
        assert "source_layer_label" in source
        assert "excerpt" in source
        assert "article_or_section" in source
        assert "chunk_id" in source
        assert "ranking_reasons" in source
        assert "source_quality_warning" in source
    layers = source_layers(answer)
    if layers["code_travail"]["status"] == "present":
        assert layer_sources(answer, "code_travail")
        for source in layer_sources(answer, "code_travail"):
            assert source["source_layer"] == "code_travail"
            assert source["document"] == "Code du travail"
            assert source["official_id"]
            assert "retrieved_at" in source
    else:
        assert layers["code_travail"]["status"] == "absent"
        assert "Code du travail absent" in layers["code_travail"]["absent_message"]
    assert layers["jurisprudence"]["status"] == "absent"
    assert layers["prudhommes"]["status"] == "absent"


def report_section(report: dict[str, object], section_id: str) -> dict[str, object]:
    for section in report["sections"]:
        if section["id"] == section_id:
            return section
    raise AssertionError(f"Section rapport absente: {section_id}")


def source_layers(answer: dict[str, object]) -> dict[str, dict[str, object]]:
    return {layer["id"]: layer for layer in answer["source_layers"]}


def layer_sources(answer: dict[str, object], layer_id: str) -> list[dict[str, object]]:
    return source_layers(answer)[layer_id]["sources"]


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), NexusHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        for question in V2_QUESTIONS:
            payload = post_json(f"http://127.0.0.1:{port}/api/analyze", {"query": question, "source_limit": 6})
            assert_base_payload(payload)
            answer = payload["answer"]
            expert = payload["expert_juriste"]
            if "reunion du CSE" in question:
                assert answer["route"]["main_domain"] == "droit_syndical"
                assert "preparer_cse" not in answer["route"]["intents"]
                assert expert["active"] is True
                assert "mandat" in normalize(expert["response_courte"])
            if "astreinte" in question:
                assert [group["id"] for group in answer["issue_groups"]] == ["repos", "astreinte", "paie"]
                assert payload["expert_paie"]["active"] is True

        juriste_payload = post_json(
            f"http://127.0.0.1:{port}/api/analyze",
            {"query": V21_SCENARIOS["juriste_seul"], "source_limit": 6},
        )
        assert_base_payload(juriste_payload)
        assert juriste_payload["expert_juriste"]["active"] is True
        assert juriste_payload["expert_paie"]["active"] is False
        assert "automation/experts/juriste_travail.py: enrich" in juriste_payload["analysis_report"]["generated_from"]
        assert "automation/experts/paie.py: enrich" not in juriste_payload["analysis_report"]["generated_from"]
        assert juriste_payload["expert_juriste"]["prompt_version"] == "EXPERT_JURISTE_CFDT_NEXUS_V1"
        assert juriste_payload["expert_juriste"]["strategie_de_defense"]["argument_principal"]
        assert isinstance(juriste_payload["expert_juriste"]["analyse_contradictoire_contentieux"], list)
        assert juriste_payload["expert_juriste"]["niveau_de_certitude_detaille"]["information_manquante"]
        assert juriste_payload["expert_juriste"]["pieces_a_recuperer"]
        assert "classification" in normalize(juriste_payload["expert_juriste"]["qualification_juridique_situation"])
        assert "Regle certaine" in " ".join(juriste_payload["expert_juriste"]["analyse_et_raisonnement"])
        assert "classification_carriere" in report_section(juriste_payload["analysis_report"], "domaines")["items"]
        classification_answer = juriste_payload["answer"]
        assert layer_sources(classification_answer, "accord_entreprise")
        convention_sources = layer_sources(classification_answer, "convention_collective")
        assert convention_sources
        assert any("ccnic" in normalize(source["document"]) for source in convention_sources)
        for source in convention_sources:
            assert source["document_type"] == "convention_collective"
            assert source["idcc"] == "44"
            assert source["version"] == "septembre 2013"
            assert source["excerpt"]

        paie_payload = post_json(
            f"http://127.0.0.1:{port}/api/analyze",
            {"query": V21_SCENARIOS["paie_seul"], "source_limit": 6},
        )
        assert_base_payload(paie_payload)
        assert paie_payload["expert_juriste"]["active"] is False
        assert paie_payload["expert_paie"]["active"] is True
        assert "automation/experts/juriste_travail.py: enrich" not in paie_payload["analysis_report"]["generated_from"]
        assert "automation/experts/paie.py: enrich" in paie_payload["analysis_report"]["generated_from"]
        assert paie_payload["orchestration"]["experts_mobilises"] == ["Expert Paie V0"]
        paie_text = " ".join(paie_payload["expert_paie"]["elements_du_bulletin_concernes"])
        assert "nuit" in normalize(paie_text)
        assert "dimanche" in normalize(paie_text)
        assert "Non produit" in paie_payload["expert_paie"]["calcul_detaille"]
        assert "heures de nuit" in normalize(" ".join(report_section(paie_payload["analysis_report"], "hypotheses")["items"]))

        mixed_payload = post_json(
            f"http://127.0.0.1:{port}/api/analyze",
            {"query": V21_SCENARIOS["juriste_paie"], "source_limit": 6},
        )
        assert_base_payload(mixed_payload)
        assert mixed_payload["expert_juriste"]["active"] is True
        assert mixed_payload["expert_paie"]["active"] is True
        assert "automation/experts/juriste_travail.py: enrich" in mixed_payload["analysis_report"]["generated_from"]
        assert "automation/experts/paie.py: enrich" in mixed_payload["analysis_report"]["generated_from"]
        assert [group["id"] for group in mixed_payload["answer"]["issue_groups"]] == ["repos", "astreinte", "paie"]
        synthesis = normalize(mixed_payload["orchestration"]["reponse_synthetique_nexus"])
        assert "droit du travail" in synthesis
        assert "paie" in synthesis
        assert "Astreinte" in mixed_payload["analysis_report"]["title"] or "astreinte" in normalize(mixed_payload["analysis_report"]["title"])

        incomplete_payload = post_json(
            f"http://127.0.0.1:{port}/api/analyze",
            {"query": V21_SCENARIOS["question_incomplete"], "source_limit": 6},
        )
        assert_base_payload(incomplete_payload)
        assert incomplete_payload["expert_juriste"]["active"] is False
        assert incomplete_payload["expert_paie"]["active"] is True
        assert incomplete_payload["answer"]["confidence"] == "faible"
        assert "incomplete" in normalize(incomplete_payload["answer"]["short_answer"])
        assert incomplete_payload["expert_paie"]["niveau_de_confiance"] == "faible"
        incomplete_needed = normalize(" ".join(incomplete_payload["expert_paie"]["donnees_necessaires_au_calcul"]))
        assert "libelle exact" in incomplete_needed
        assert "periode" in incomplete_needed
        assert "montant" in incomplete_needed
        assert "Non produit" in incomplete_payload["expert_paie"]["calcul_detaille"]
        assert "faible" in report_section(incomplete_payload["analysis_report"], "confiance")["items"]
        assert "libelle exact" in normalize(" ".join(report_section(incomplete_payload["analysis_report"], "informations_manquantes")["items"]))

        mixed_answer = mixed_payload["answer"]
        mixed_accords = layer_sources(mixed_answer, "accord_entreprise")
        assert any("astreinte" in normalize(source["document"]) for source in mixed_accords)
        assert any("35 h" in normalize(source["document"]) or "5x8" in normalize(source["document"]) for source in mixed_accords)
        assert layer_sources(mixed_answer, "convention_collective")
        assert any(source.get("excerpt") for source in mixed_answer["sources"])

        print("Interface locale: socle juridique V1 + scenarios V2.1 OK")
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
