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
    "juriste_paie": "Un salarié d’astreinte intervient la nuit, son repos est interrompu et il reprend ensuite son poste. Quels sont ses droits et comment contrôler sa paie ?",
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
    answer = payload["answer"]
    orchestration = payload["orchestration"]
    assert answer["short_answer"]
    assert answer["sources"]
    assert answer["confidence"]
    assert orchestration["reponse_synthetique_nexus"]
    assert orchestration["domaines_detectes"]
    assert "niveau_de_confiance" in orchestration


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
        assert "classification" in normalize(juriste_payload["expert_juriste"]["qualification_juridique_situation"])
        assert "Regle certaine" in " ".join(juriste_payload["expert_juriste"]["analyse_et_raisonnement"])

        paie_payload = post_json(
            f"http://127.0.0.1:{port}/api/analyze",
            {"query": V21_SCENARIOS["paie_seul"], "source_limit": 6},
        )
        assert_base_payload(paie_payload)
        assert paie_payload["expert_juriste"]["active"] is False
        assert paie_payload["expert_paie"]["active"] is True
        assert paie_payload["orchestration"]["experts_mobilises"] == ["Expert Paie V0"]
        paie_text = " ".join(paie_payload["expert_paie"]["elements_du_bulletin_concernes"])
        assert "nuit" in normalize(paie_text)
        assert "dimanche" in normalize(paie_text)
        assert "Non produit" in paie_payload["expert_paie"]["calcul_detaille"]

        mixed_payload = post_json(
            f"http://127.0.0.1:{port}/api/analyze",
            {"query": V21_SCENARIOS["juriste_paie"], "source_limit": 6},
        )
        assert_base_payload(mixed_payload)
        assert mixed_payload["expert_juriste"]["active"] is True
        assert mixed_payload["expert_paie"]["active"] is True
        assert [group["id"] for group in mixed_payload["answer"]["issue_groups"]] == ["repos", "astreinte", "paie"]
        synthesis = normalize(mixed_payload["orchestration"]["reponse_synthetique_nexus"])
        assert "droit du travail" in synthesis
        assert "paie" in synthesis

        incomplete_payload = post_json(
            f"http://127.0.0.1:{port}/api/analyze",
            {"query": V21_SCENARIOS["question_incomplete"], "source_limit": 6},
        )
        assert_base_payload(incomplete_payload)
        assert incomplete_payload["expert_juriste"]["active"] is False
        assert incomplete_payload["expert_paie"]["active"] is True
        assert incomplete_payload["expert_paie"]["niveau_de_confiance"] == "faible"
        assert "libelle exact" in normalize(" ".join(incomplete_payload["expert_paie"]["donnees_necessaires_au_calcul"]))
        assert "Non produit" in incomplete_payload["expert_paie"]["calcul_detaille"]

        print("Interface locale: 3 questions V2 + 4 scenarios V2.1 OK")
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
