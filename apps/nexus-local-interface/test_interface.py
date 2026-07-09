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

BUSINESS_MODE_SCENARIOS = {
    "defense_sanction": {
        "query": "Un salarié risque une sanction après une erreur de manipulation. Comment préparer sa défense ?",
        "expected_mode": "DEFENSE_SALARIE",
    },
    "negociation_repos": {
        "query": "La direction propose un accord réduisant le repos entre deux périodes de travail. Que faut-il analyser avant de signer ?",
        "expected_mode": "NEGOCIATION_ACCORD",
    },
    "cse_reorganisation": {
        "query": "La direction présente au CSE une réorganisation d’atelier avec suppression de postes et changement d’horaires. Quels documents demander et quelles questions poser ?",
        "expected_mode": "CSE_CSSCT",
    },
    "defense_paie_collective": {
        "query": "Plusieurs salariés pensent que les majorations d’astreinte sont mal calculées. Comment construire le dossier ?",
        "expected_mode": "DEFENSE_SALARIE",
    },
}

CSE_V12_SCENARIOS = {
    "reorganisation_atelier": {
        "query": "La direction annonce une reorganisation d'un atelier avec deux suppressions de postes, modification des taches et changement d'horaires. Quels sont les droits du CSE et comment preparer la reunion ?",
        "expected_position": "information-consultation",
        "required_terms": ["suppressions", "horaires", "taches", "PV"],
        "requires_primary_sources": True,
        "forbidden_terms": [
            "statut du participant",
            "qualite du participant",
            "base de convocation",
            "base de participation",
            "traitement du temps de reunion pendant un repos",
            "repos 5x8",
        ],
    },
    "changement_mineur": {
        "query": "La direction annonce au CSE un simple changement mineur sans impact collectif. Quels sont les droits du CSE ?",
        "expected_position": "consultation non automatique",
        "required_terms": ["absence d'impact", "information"],
    },
    "horaires_collectif": {
        "query": "La direction veut un changement d'horaires collectif dans un atelier. Quels sont les droits du CSE ?",
        "expected_position": "information-consultation",
        "required_terms": ["horaires", "planning"],
    },
    "impact_sante_securite": {
        "query": "La direction presente un projet avec impact sante-securite important et fatigue accrue. Comment preparer le CSE ?",
        "expected_position": "information-consultation",
        "required_terms": ["sante", "securite", "expertise"],
    },
    "fermeture_activite": {
        "query": "La direction annonce la fermeture d'une activite avec transfert de charge. Quels sont les droits du CSE ?",
        "expected_position": "information-consultation",
        "required_terms": ["fermeture", "charge"],
    },
    "transfert_taches": {
        "query": "La direction transfere des taches entre equipes sans suppression de postes. Quels documents demander au CSE ?",
        "expected_position": "a qualifier",
        "required_terms": ["taches", "charge"],
    },
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
    assert report_section(report, "modes_metier")["items"]
    assert report_section(report, "analyse_metier")["items"]
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
    if layers["jurisprudence"]["status"] == "present":
        assert layer_sources(answer, "jurisprudence")
        for source in layer_sources(answer, "jurisprudence"):
            assert source["source_layer"] == "jurisprudence"
            assert source.get("excerpt")
    else:
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


def assert_business_mode_payload(payload: dict[str, object], expected_mode: str) -> dict[str, object]:
    assert_base_payload(payload)
    juriste = payload["expert_juriste"]
    orchestration = payload["orchestration"]
    report = payload["analysis_report"]
    assert juriste["active"] is True
    assert juriste["mode_metier_principal"] == expected_mode
    assert orchestration["mode_metier_principal"] == expected_mode
    assert expected_mode in juriste["modes_metier"]
    assert expected_mode in orchestration["modes_metier"]
    assert juriste["reponse_juridique_argumentee"]["regle_applicable"]
    assert juriste["reponse_juridique_argumentee"]["application_aux_faits"]
    assert juriste["conclusion_provisoire_juridique"]["position"]
    assert juriste["argumentation_de_defense"]["argument_principal_salarie"]
    assert juriste["strategie_action_ordonnee"]
    assert "source_principale" in juriste["selection_juridique_sources"]
    assert "source_ecartee" in juriste["selection_juridique_sources"]
    assert orchestration["analyse_metier"]
    matching = [item for item in orchestration["analyse_metier"] if item.get("mode") == expected_mode]
    assert matching
    analysis = matching[0]
    assert analysis["analyse_contradictoire"]
    assert analysis["action_immediate_recommandee"]
    assert analysis["strategie_progressive"]
    assert "Mode principal" in " ".join(report_section(report, "modes_metier")["items"])
    assert "Contradictoire" in " ".join(report_section(report, "analyse_metier")["items"])
    return analysis


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

        for scenario_id, scenario in BUSINESS_MODE_SCENARIOS.items():
            payload = post_json(
                f"http://127.0.0.1:{port}/api/analyze",
                {"query": scenario["query"], "source_limit": 8},
            )
            analysis = assert_business_mode_payload(payload, scenario["expected_mode"])
            if scenario_id == "defense_sanction":
                assert "disciplinaire" in normalize(analysis["qualification_juridique"])
                assert "procedure" in normalize(" ".join(analysis["preuves_indispensables"]))
            elif scenario_id == "negociation_repos":
                assert analysis["recommandation"]
                assert "repos" in normalize(" ".join(analysis["modifications_proposees"]))
                assert "signature" in normalize(" ".join(analysis["questions_avant_signature"]))
            elif scenario_id == "cse_reorganisation":
                assert analysis["documents_manquants"]
                assert analysis["questions_prioritaires"]
                assert analysis["points_pv"]
                assert "preparer_cse" in payload["answer"]["route"]["intents"]
                assert "question_simple" not in payload["answer"]["route"]["intents"]
                cse_sources = " ".join(source["document"] for source in payload["answer"]["sources"])
                assert "teletravail" not in normalize(cse_sources)
            elif scenario_id == "defense_paie_collective":
                assert payload["expert_paie"]["active"] is True
                assert "majoration" in normalize(" ".join(payload["expert_paie"]["elements_du_bulletin_concernes"]))

        for scenario_id, scenario in CSE_V12_SCENARIOS.items():
            payload = post_json(
                f"http://127.0.0.1:{port}/api/analyze",
                {"query": scenario["query"], "source_limit": 10},
            )
            analysis = assert_business_mode_payload(payload, "CSE_CSSCT")
            juriste = payload["expert_juriste"]
            source_selection = juriste["selection_juridique_sources"]
            conclusion_text = normalize(
                " ".join(
                    [
                        juriste["conclusion_provisoire_juridique"]["position"],
                        juriste["conclusion_provisoire_juridique"]["pourquoi"],
                        juriste["response_courte"],
                        analysis["information_ou_consultation_eventuelle"],
                    ]
                )
            )
            assert normalize(scenario["expected_position"]) in conclusion_text
            full_cse_text = normalize(json.dumps(analysis, ensure_ascii=False))
            for term in scenario["required_terms"]:
                assert normalize(term) in full_cse_text, (scenario_id, term)
            payload_text = normalize(json.dumps(payload, ensure_ascii=False))
            for term in scenario.get("forbidden_terms", []):
                assert normalize(term) not in payload_text, (scenario_id, term)
            if scenario.get("requires_primary_sources"):
                assert source_selection["source_principale"], scenario_id
            source_text = normalize(" ".join(source["document"] for source in payload["answer"]["sources"]))
            for forbidden_source_term in [
                "teletravail",
                "pee",
                "plan epargne",
                "interessement",
                "participation",
                "restauration",
                "pre retraite",
                "preretraite",
            ]:
                assert forbidden_source_term not in source_text, (scenario_id, forbidden_source_term)
            if scenario_id == "changement_mineur":
                assert "consultation obligatoire non deduite automatiquement" in conclusion_text

        print("Interface locale: socle juridique V1 + scenarios V2.1 OK")
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
