from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "automation" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import assistant_ds_router as router  # noqa: E402
from NEXUS_RUNTIME_INTEGRATION.config import RuntimeOfficialConnectorsConfig  # noqa: E402
from NEXUS_RUNTIME_INTEGRATION import (  # noqa: E402
    RuntimeConnectorConfig,
    RuntimeConnectorPayloadMapper,
)
from NEXUS_RUNTIME_INTEGRATION.official_connectors_runtime import (  # noqa: E402
    RuntimeOfficialConnectorsIntegration,
)
from tools.run_real_business_cases_baseline import (  # noqa: E402
    build_case_prompt,
    load_fixtures,
)
from tools.run_real_business_cases_second_baseline import (  # noqa: E402
    load_second_fixtures,
)


NOW = datetime(2026, 7, 29, tzinfo=timezone.utc)


def answer(query: str, domains: tuple[str, ...] = ()) -> dict[str, object]:
    return {
        "query": query,
        "generated_at": NOW.isoformat(),
        "route": {"domains": list(domains), "engines": []},
        "sources": [],
    }


def selected(query: str, domains: tuple[str, ...] = ()) -> set[str]:
    return RuntimeOfficialConnectorsIntegration._selected_connectors(
        answer(query, domains)
    )


def test_seveso_turnstile_case_selects_cnil_without_simulating_a_result() -> None:
    result = RuntimeOfficialConnectorsIntegration(
        RuntimeOfficialConnectorsConfig(enabled=True),
        clock=lambda: NOW,
    ).integrate(
        answer(
            "La direction veut utiliser le badgeage du tourniquet Seveso "
            "pour mesurer les pauses cigarettes.",
            ("rgpd_cnil", "disciplinaire"),
        )
    )

    assert result.diagnostics.connectors_used == ("cnil",)
    assert result.unavailable_connectors == ("cnil",)
    assert result.questions == ()
    assert result.diagnostics.connector_runtime_fallback == "OFFICIAL_CONNECTORS_NO_RESULT"


def test_carsat_is_selected_for_ppe_rps_and_night_shift_fatigue() -> None:
    assert "carsat" in selected(
        "Les sur-lunettes sont inadaptées et les EPI requis étaient indisponibles."
    )
    assert "carsat" in selected(
        "Un tag est relié à une souffrance au travail et à une surcharge."
    )
    assert "carsat" in selected(
        "Après cinq postes de nuit, le salarié invoque fatigue et charge de travail."
    )


def test_carsat_results_generate_prevention_questions_and_are_not_legal_rules() -> None:
    result = RuntimeOfficialConnectorsIntegration(
        RuntimeOfficialConnectorsConfig(enabled=True),
        clock=lambda: NOW,
    ).integrate(
        answer(
            "Les EPI et les sur-lunettes étaient-ils adaptés, et quelles mesures "
            "de prévention auraient dû être prises ?"
        )
    )

    assert result.diagnostics.connectors_used == ("carsat", "inrs")
    assert any("disponibles et adaptés" in item for item in result.questions)
    carsat = next(
        item for item in result.source_qualifications if item.connector_id == "carsat"
    )
    assert carsat.nature_document == "page_institutionnelle"
    assert "ne constitue pas automatiquement" in carsat.portee_indicative
    assert carsat.statut_disponibilite == "DISPONIBLE"
    assert "ne constitue pas automatiquement" in (
        RuntimeOfficialConnectorsIntegration._source_scope("inrs")
    )
    assert "sans portée normative automatique" in (
        RuntimeOfficialConnectorsIntegration._source_scope("anact")
    )
    assert all("article " not in item.casefold() for item in result.questions)


def test_available_cnil_metadata_generates_only_non_normative_control_questions() -> None:
    payload = answer(
        "La direction utilise les données du badgeage du tourniquet comme preuve disciplinaire.",
        ("rgpd_cnil", "disciplinaire"),
    )
    payload["sources"] = [
        {
            "origin": "cnil",
            "url": "https://www.cnil.fr/fr/guide-synthetique",
            "title": "Guide synthétique",
            "publication_date": "2026-01-10",
            "category": "guide",
            "family": "guide",
            "document_type": "guide",
            "mime_type": "text/html",
            "discovered_at": "2026-07-22",
        }
    ]
    result = RuntimeOfficialConnectorsIntegration(
        RuntimeOfficialConnectorsConfig(enabled=True),
        clock=lambda: NOW,
    ).integrate(payload)

    assert result.unavailable_connectors == ()
    assert len(result.questions) == 7
    assert any("finalité" in item for item in result.questions)
    assert any("CSE" in item for item in result.questions)
    assert any("droit d'accès" in item for item in result.questions)
    cnil = result.source_qualifications[0]
    assert cnil.organisme == "CNIL"
    assert cnil.titre == "Guide synthétique"
    assert cnil.nature_document == "guide"
    assert "dépend de la nature réelle" in cnil.portee_indicative
    assert cnil.lien_avec_faits
    assert cnil.question_dossier
    assert all("article " not in item.casefold() for item in result.questions)


def test_cdtn_is_pedagogical_and_follows_precise_legal_sources() -> None:
    domains = ["bible_accords", "droit_travail_general", "disciplinaire"]
    intents = ["analyser_situation_individuelle"]
    assert router.needs_pratique_officielle(
        "Quelle procédure suivre pour une sanction après des insultes ?",
        domains,
        intents,
    )
    assert router.SOURCE_LAYER_ORDER.index("code_travail") < (
        router.SOURCE_LAYER_ORDER.index("pratique_officielle")
    )
    assert router.SOURCE_LAYER_ORDER.index("jurisprudence") < (
        router.SOURCE_LAYER_ORDER.index("pratique_officielle")
    )
    mapped = RuntimeConnectorPayloadMapper(RuntimeConnectorConfig(True)).map(
        {
            "query": "Quelle procédure suivre ?",
            "route": {"engines": ["pratique_officielle"]},
            "sources": [
                {
                    "origin": "cdtn_pratique_officielle",
                    "document": "Fiche pratique officielle",
                    "source_layer": "pratique_officielle",
                }
            ],
        }
    )
    assert (
        "source_nature",
        "service_public_information_pedagogique_non_substitutif",
    ) in mapped.inputs[0].response.documents[0].metadata
    assert RuntimeConnectorPayloadMapper._source_nature(
        "legifrance_code_travail"
    ) == "source_officielle_publication_acces_textes_portee_selon_document"
    assert "valeur juridique dépend du document retrouvé" in (
        RuntimeConnectorPayloadMapper._source_scope("legifrance_code_travail")
    )
    assert "comparabilité factuelle" in (
        RuntimeConnectorPayloadMapper._source_scope("judilibre_jurisprudence")
    )


def test_judilibre_requires_a_factual_comparator() -> None:
    domains = ["bible_accords", "disciplinaire"]
    intents = ["analyser_situation_individuelle"]
    assert router.needs_jurisprudence(
        "Un salarié a insulté son supérieur après cinq nuits et l'employeur "
        "envisage une faute grave.",
        domains,
        intents,
    )
    assert router.needs_jurisprudence(
        "Le badgeage du tourniquet serait utilisé comme preuve disciplinaire.",
        domains,
        intents,
    )
    assert not router.needs_jurisprudence(
        "Explique la procédure disciplinaire générale.",
        domains,
        intents,
    )


def test_unrelated_terms_do_not_select_official_connectors_by_substring() -> None:
    assert selected(
        "Le caractère isolé du fait doit être analysé avec prudence."
    ) == set()
    assert "defenseur_droits" not in selected(
        "Il faut seulement vérifier une égalité de traitement dans les pauses."
    )
    assert "cnil" not in selected(
        "La confidentialité de l'entretien doit être respectée."
    )


def test_source_guidance_is_only_emitted_for_real_connector_documents() -> None:
    unavailable = RuntimeOfficialConnectorsIntegration(
        RuntimeOfficialConnectorsConfig(enabled=True),
        clock=lambda: NOW,
    ).integrate(answer("Le tourniquet sert au badgeage.", ("rgpd_cnil",)))
    available = RuntimeOfficialConnectorsIntegration(
        RuntimeOfficialConnectorsConfig(enabled=True),
        clock=lambda: NOW,
    ).integrate(answer("Fatigue, surcharge et cinq postes de nuit."))

    assert unavailable.questions == ()
    assert unavailable.unavailable_connectors == ("cnil",)
    assert available.questions
    assert available.unavailable_connectors == ("inrs",)
    assert all(
        connector_id in available.diagnostics.connectors_used
        for connector_id in (
            qualification.connector_id
            for qualification in available.source_qualifications
        )
    )


def test_eleven_real_cases_use_the_validated_connector_selection_matrix() -> None:
    expected = {
        "REAL-01-INSULTING_EMAILS_ALCOHOL": {"carsat"},
        "REAL-02-SMOKING_BREAKS_SEVESO_BADGE": {"cnil"},
        "REAL-03-TAG_INSTALLATION": {"anact", "carsat"},
        "REAL-04-FORCED_DAY_TO_SHIFT_LABORATORY": {"carsat", "inrs"},
        "REAL-05-DELEGATION_HOURS_CSSCT_INCOMPLETE": set(),
        "REAL-06-ANNUAL_LEAVE_TEN_PERCENT_UNRESOLVED": set(),
        "REAL-07-SAFETY_PPE_UNAVAILABLE_OR_UNSUITABLE": {"carsat", "inrs"},
        "REAL-08-TEMPORARY_DAY_TO_THREE_SHIFT_REFUSAL": {"inrs"},
        "REAL-09-CHEMICAL_RECIPE_OUTDATED_PROCEDURE": {"carsat", "inrs"},
        "REAL-10-POSITIVE_ALCOHOL_TEST_HIGH_RISK_POSITION": {"carsat", "inrs"},
        "REAL-11-INSULTS_SUPERVISOR_FATIGUE_CONTEXT": {"anact", "carsat", "inrs"},
    }

    fixtures = load_fixtures() + load_second_fixtures()
    assert len(fixtures) == 11
    for fixture in fixtures:
        query = build_case_prompt(fixture)
        route = router.route_query(
            query, fixture["case_input"].get("requested_path")
        )
        actual = selected(query, tuple(route["domains"]))
        assert actual == expected[fixture["case_id"]]


def test_eleven_real_cases_keep_legal_sources_precise_and_fact_bound() -> None:
    fixtures = load_fixtures() + load_second_fixtures()
    expected_case_law = {
        "REAL-01-INSULTING_EMAILS_ALCOHOL",
        "REAL-02-SMOKING_BREAKS_SEVESO_BADGE",
        "REAL-04-FORCED_DAY_TO_SHIFT_LABORATORY",
        "REAL-07-SAFETY_PPE_UNAVAILABLE_OR_UNSUITABLE",
        "REAL-08-TEMPORARY_DAY_TO_THREE_SHIFT_REFUSAL",
        "REAL-09-CHEMICAL_RECIPE_OUTDATED_PROCEDURE",
        "REAL-10-POSITIVE_ALCOHOL_TEST_HIGH_RISK_POSITION",
        "REAL-11-INSULTS_SUPERVISOR_FATIGUE_CONTEXT",
    }
    expected_pedagogical_guidance = {
        "REAL-02-SMOKING_BREAKS_SEVESO_BADGE",
        "REAL-04-FORCED_DAY_TO_SHIFT_LABORATORY",
        "REAL-07-SAFETY_PPE_UNAVAILABLE_OR_UNSUITABLE",
        "REAL-08-TEMPORARY_DAY_TO_THREE_SHIFT_REFUSAL",
    }
    for fixture in fixtures:
        route = router.route_query(
            build_case_prompt(fixture),
            fixture["case_input"].get("requested_path"),
        )
        engines = set(route["engines"])
        if route["analysis_suspended"]:
            assert "legifrance_code_travail" not in engines
        else:
            assert "legifrance_code_travail" in engines
        assert ("pratique_officielle" in engines) is (
            fixture["case_id"] in expected_pedagogical_guidance
        )
        assert ("judilibre_jurisprudence" in engines) is (
            fixture["case_id"] in expected_case_law
        )


def test_server_passes_real_connector_questions_to_expert_orchestration(
    monkeypatch,
) -> None:
    server_path = ROOT / "apps" / "nexus-local-interface" / "server.py"
    sys.path.insert(0, str(server_path.parent))
    spec = importlib.util.spec_from_file_location(
        "nexus_official_guidance_server", server_path
    )
    assert spec and spec.loader
    server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server)

    routed = answer(
        "La direction utilise les données du badgeage du tourniquet comme preuve disciplinaire.",
        ("rgpd_cnil", "disciplinaire"),
    )
    routed["sources"] = [
        {
            "origin": "cnil",
            "url": "https://www.cnil.fr/fr/guide-synthetique",
            "title": "Guide synthétique",
            "publication_date": "2026-01-10",
            "category": "guide",
            "family": "guide",
            "document_type": "guide",
            "mime_type": "text/html",
            "discovered_at": "2026-07-22",
        }
    ]
    seen: dict[str, object] = {}
    monkeypatch.setattr(server, "run_router", lambda *_args, **_kwargs: routed)

    def orchestrate(enriched):
        seen.update(enriched)
        legal = {"active": True, "ce_qui_est_certain": [], "limites": []}
        payroll = {"active": False}
        return {
            "expert_juriste": legal,
            "expert_paie": payroll,
            "experts": {"juriste": legal, "paie": payroll},
            "orchestration": {},
        }

    monkeypatch.setattr(server.orchestrator, "orchestrate", orchestrate)
    monkeypatch.setattr(
        server.report_generator,
        "build_report",
        lambda _payload: {"sections": [], "markdown": ""},
    )
    monkeypatch.setenv("NEXUS_OFFICIAL_CONNECTORS_RUNTIME_ENABLED", "true")
    monkeypatch.delenv("NEXUS_CORE_RUNTIME_ENABLED", raising=False)

    payload = server.analyze_question(str(routed["query"]))

    assert any("finalité" in item for item in seen["questions_to_ask"])
    assert seen["official_source_qualifications"] == [
        {
            "connector_id": "cnil",
            "organisme": "CNIL",
            "titre": "Guide synthétique",
            "nature_document": "guide",
            "statut_disponibilite": "DISPONIBLE",
            "portee_indicative": (
                "La portée dépend de la nature réelle du document : recommandation, "
                "référentiel, ligne directrice, décision ou sanction."
            ),
            "lien_avec_faits": (
                "Utilisation d'un dispositif de badgeage ou de contrôle d'accès."
            ),
            "question_dossier": (
                "Quelle finalité précise a été déclarée pour le dispositif de badgeage "
                "ou de contrôle d'accès ?"
            ),
        }
    ]
    assert payload["answer"]["questions_to_ask"] == seen["questions_to_ask"]
