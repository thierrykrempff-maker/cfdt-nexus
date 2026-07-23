from __future__ import annotations

from datetime import datetime, timezone
import sys
from pathlib import Path

from NEXUS_RUNTIME_INTEGRATION import RuntimeOfficialConnectorsConfig
from NEXUS_RUNTIME_INTEGRATION.official_connectors_runtime import (
    RuntimeOfficialConnectorsIntegration,
)
from NEXUS_RUNTIME_INTEGRATION.retirement_runtime import needs_retirement


ROOT = Path(__file__).resolve().parents[1]
ROUTER_DIR = ROOT / "automation" / "scripts"
sys.path.insert(0, str(ROUTER_DIR))
import assistant_ds_router as router  # noqa: E402


NOW = datetime(2026, 7, 23, 12, 0, tzinfo=timezone.utc)


def route(query: str) -> dict[str, object]:
    return router.route_query(query)


def runtime_answer(query: str, domains: list[str]) -> dict[str, object]:
    return {
        "query": query,
        "generated_at": NOW.isoformat(),
        "route": {"domains": domains},
        "sources": [],
    }


def test_general_employment_question_selects_legal_runtime_sources() -> None:
    decision = route(
        "Ma période d'essai arrive à son terme et l'employeur veut la renouveler oralement."
    )
    assert "droit_travail_general" in decision["domains"]
    assert "legifrance_code_travail" in decision["engines"]
    assert "pratique_officielle" in decision["engines"]


def test_contentious_employment_question_selects_case_law_only_when_relevant() -> None:
    contentious = route(
        "Après trois CDD successifs, puis-je demander une requalification ?"
    )
    informational = route(
        "Ma période d'essai peut-elle être renouvelée par écrit ?"
    )
    assert "judilibre_jurisprudence" in contentious["engines"]
    assert "judilibre_jurisprudence" not in informational["engines"]


def test_case_law_and_practical_sources_are_not_selected_by_generic_intents() -> None:
    agreement_only = route(
        "Deux accords INEOS de dates diffÃ©rentes traitent de la mÃªme prime."
    )
    retirement = route(
        "J'ai travaillÃ© de nuit plusieurs annÃ©es : cela compte-t-il pour la retraite ?"
    )
    assert "judilibre_jurisprudence" not in agreement_only["engines"]
    assert "pratique_officielle" not in agreement_only["engines"]
    assert "pratique_officielle" not in retirement["engines"]


def test_work_schedule_pause_and_cse_protocol_select_expected_domains() -> None:
    schedule_domains = set(
        route("Mon service passe en equipes alternantes : quels elements verifier ?")[
            "domains"
        ]
    )
    pause_domains = set(route("Je travaille sept heures sans vraie pause.")["domains"])
    election_domains = set(
        route("Une categorie semble absente du protocole electoral.")["domains"]
    )
    history_domains = set(
        route(
            "Apres une expertise, peut-on retrouver les decisions et engagements anterieurs ?"
        )["domains"]
    )
    assert {"temps_travail", "paie_remuneration"} <= schedule_domains
    assert {"temps_travail", "paie_remuneration"} <= pause_domains
    assert "cse" in election_domains
    assert "cse" in history_domains


def test_rgpd_and_safety_domains_select_only_relevant_official_connectors() -> None:
    cnil = RuntimeOfficialConnectorsIntegration(
        RuntimeOfficialConnectorsConfig(True), clock=lambda: NOW
    ).integrate(
        runtime_answer(
            "Une caméra filme mon poste sans information préalable.",
            ["rgpd_cnil"],
        )
    )
    safety = RuntimeOfficialConnectorsIntegration(
        RuntimeOfficialConnectorsConfig(True), clock=lambda: NOW
    ).integrate(
        runtime_answer(
            "Une entreprise extérieure intervient avec des consignes contradictoires.",
            ["cssct_securite"],
        )
    )
    assert cnil.diagnostics.connectors_used == ("cnil",)
    assert safety.diagnostics.connectors_used == ("dreets_grand_est", "inrs")
    assert all(not item.response.documents for item in cnil.inputs + safety.inputs)


def test_official_connector_selection_is_not_forced_for_unrelated_question() -> None:
    result = RuntimeOfficialConnectorsIntegration(
        RuntimeOfficialConnectorsConfig(True), clock=lambda: NOW
    ).integrate(runtime_answer("Quel est le montant de cette prime ?", ["paie_remuneration"]))
    assert result.inputs == ()
    assert result.diagnostics.connector_runtime_called is False


def test_official_connector_selection_uses_clock_when_router_has_no_timestamp() -> None:
    answer = runtime_answer("Une caméra filme mon poste.", ["rgpd_cnil"])
    answer.pop("generated_at")
    result = RuntimeOfficialConnectorsIntegration(
        RuntimeOfficialConnectorsConfig(True), clock=lambda: NOW
    ).integrate(answer)
    assert result.diagnostics.connectors_used == ("cnil",)
    assert result.diagnostics.connector_runtime_fallback == "OFFICIAL_CONNECTORS_NO_RESULT"


def test_cse_documentary_need_is_explicitly_routed() -> None:
    decision = route(
        "Une question urgente n'apparaît pas à l'ordre du jour du prochain CSE."
    )
    assert "cse" in decision["domains"]
    assert "rechercher_cse_memory" in decision["intents"]


def test_retirement_domain_alias_activates_existing_runtime_bridge() -> None:
    answer = runtime_answer(
        "Comment documenter des années de nuit anciennes ?",
        ["retraite_penibilite"],
    )
    assert needs_retirement(answer) is True
