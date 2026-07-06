#!/usr/bin/env python
"""
Assistant DS CFDT Nexus V1.

Central local router for natural-language DS questions. The router classifies the
request, selects callable local engines, executes them when available, and fuses a
short operational answer. It does not copy private documents into Git and does
not simulate unavailable connectors.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import agreements_bible as bible

try:
    import nexus_bible_bridge as bridge
except ImportError:  # pragma: no cover - diagnosed at runtime.
    bridge = None


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
DIC_DIR = ROOT / "apps" / "document-intelligence-center"
CYCLE_CSE_DIR = ROOT / "apps" / "cycle-cse-intelligent"

PRUDENCE_WARNING = (
    "L'analyse constitue une aide a la preparation syndicale. Verifier les textes cites, "
    "leur date, leur champ d'application et leur articulation avec les normes superieures "
    "avant toute position definitive."
)

DOMAIN_ORDER = [
    "classification_carriere",
    "inaptitude_reclassement",
    "disciplinaire",
    "cssct_securite",
    "temps_travail",
    "astreinte",
    "paie_remuneration",
    "conges_payes",
    "droit_syndical",
    "analyse_documentaire",
    "veille_juridique",
    "cse",
]

REQUIRED_DOMAINS = [
    "bible_accords",
    "cse",
    "cssct_securite",
    "paie_remuneration",
    "temps_travail",
    "classification_carriere",
    "inaptitude_reclassement",
    "disciplinaire",
    "droit_syndical",
    "analyse_documentaire",
    "veille_juridique",
]

INTENTS = [
    "question_simple",
    "rechercher_droit_local",
    "preparer_cse",
    "preparer_cssct",
    "analyser_situation_individuelle",
    "analyser_paie",
    "analyser_document",
    "preparer_negociation",
    "preparer_entretien_direction",
    "construire_argumentaire",
    "demander_documents",
    "verifier_conformite",
    "rechercher_veille",
]

DOMAIN_RULES: list[dict[str, Any]] = [
    {
        "domain": "classification_carriere",
        "reason": "La demande porte sur classification, emploi, carriere ou coefficient.",
        "patterns": [
            r"\bclassification\b",
            r"\bcoefficient\b",
            r"\bniveau\b",
            r"\bechelon\b",
            r"\bemploi\b",
            r"fiche de poste",
            r"fonctions? exerce",
            r"responsabilites?",
            r"\bautonomie\b",
            r"\btechnicite\b",
            r"evolution de poste",
            r"\bcarriere\b",
            r"\bpolyvalence\b",
            r"pesee de poste",
            r"mal classe",
        ],
    },
    {
        "domain": "inaptitude_reclassement",
        "reason": "La demande porte sur inaptitude, reclassement ou sante au travail.",
        "patterns": [
            r"\binaptitude\b",
            r"\binapte\b",
            r"\breclassement\b",
            r"medecin du travail",
            r"\baptitude\b",
            r"restrictions? medicales?",
            r"amenagement de poste",
            r"adaptation de poste",
            r"poste compatible",
            r"recherche de reclassement",
            r"consultation cse",
            r"impossibilite de reclassement",
            r"licenciement pour inaptitude",
            r"sante au travail",
        ],
    },
    {
        "domain": "temps_travail",
        "reason": "La demande concerne le temps de travail, les repos, horaires ou compteurs.",
        "patterns": [
            r"temps de travail",
            r"temps de travail effectif",
            r"\brepos\b",
            r"\b5x8\b",
            r"cycle 5x8",
            r"\bcycle\b",
            r"\bpostes?\s+en\s+5x8\b",
            r"travail poste",
            r"salaries? postes?",
            r"fatigue des postes?",
            r"reprend son poste",
            r"\bhoraires?\b",
            r"heures supplementaires",
            r"compteurs? d'?heures?",
            r"\bcompteurs?\b",
            r"\bpointage\b",
            r"\bbadgeage\b",
            r"heures effectuees",
            r"heures recuperees",
            r"\brecuperation\b",
            r"repos compensateur",
            r"\bcontingent\b",
            r"\bmodulation\b",
            r"\bannualisation\b",
            r"travail de nuit",
            r"\bdimanches?\b",
            r"jours? feries?",
        ],
    },
    {
        "domain": "astreinte",
        "reason": "La demande mentionne l'astreinte ou une intervention hors poste.",
        "patterns": [
            r"\bastreinte\b",
            r"\bd'?astreinte\b",
            r"intervention pendant une astreinte",
            r"intervient de nuit",
            r"intervention de nuit",
        ],
    },
    {
        "domain": "paie_remuneration",
        "reason": "La demande implique paie, remuneration, prime, majoration ou indemnisation.",
        "patterns": [
            r"\bpaie\b",
            r"\bpaye(?:e|es|s)?\b",
            r"\bpayer\b",
            r"\bremuneration\b",
            r"\bsalaire\b",
            r"\bprime\b",
            r"\bindemnise",
            r"\bindemnisation\b",
            r"\bmajoration\b",
            r"\bbulletin\b",
            r"fiche de paie",
            r"heures supplementaires",
            r"\bcompteurs?\b",
            r"heures payees",
            r"mal paye",
            r"dimanches?",
            r"jours? feries?",
            r"calcul des conges",
            r"\bdixieme\b",
        ],
    },
    {
        "domain": "conges_payes",
        "reason": "La demande vise les conges payes ou la regle du dixieme.",
        "patterns": [
            r"conges payes",
            r"indemnite de conges",
            r"indemnite compensatrice",
            r"regle du dixieme",
            r"\bdixieme\b",
            r"maintien de salaire",
        ],
    },
    {
        "domain": "cssct_securite",
        "reason": "La demande releve de la sante, securite, CSSCT, DUERP ou securite process.",
        "patterns": [
            r"\bcssct\b",
            r"\bduerp\b",
            r"\bduer\b",
            r"sante securite",
            r"securite process",
            r"risques? industriels?",
            r"\brps\b",
            r"\bprovox\b",
            r"\bsncc\b",
            r"analyseurs?",
            r"\bclimatisation\b",
            r"forte chaleur",
            r"\bchaleur\b",
            r"\bpannes?\b",
            r"pieces? de rechange",
            r"pieces? critiques?",
            r"plan de contingence",
            r"maintenance preventive",
            r"\bfatigue\b",
        ],
    },
    {
        "domain": "disciplinaire",
        "reason": "La demande porte sur une procedure ou sanction disciplinaire.",
        "patterns": [
            r"\bdisciplinaire\b",
            r"\bsanction\b",
            r"entretien disciplinaire",
            r"\bavertissement\b",
            r"mise a pied",
            r"licenciement disciplinaire",
            r"\bconvoque\b",
            r"\bconvocation\b",
        ],
    },
    {
        "domain": "droit_syndical",
        "reason": "La demande vise explicitement mandat, elu CSE ou moyens syndicaux.",
        "patterns": [
            r"\bdroit syndical\b",
            r"\bmandat\b",
            r"\belu(?:s)? cse\b",
            r"\belus?\b",
            r"delegue syndical",
            r"representant syndical",
            r"heures? de delegation",
            r"credit d'?heures",
            r"moyens? syndicaux?",
            r"local syndical",
            r"affichage syndical",
            r"reunions? syndicales?",
            r"fonctionnement du cse",
        ],
    },
    {
        "domain": "analyse_documentaire",
        "reason": "La demande demande l'analyse d'un document ou projet d'accord.",
        "patterns": [
            r"analyse(?:r)? ce document",
            r"analyse(?:r)? le document",
            r"analyse(?:r)? ce projet",
            r"projet d'?accord",
            r"\bpdf\b",
            r"\bdocx\b",
            r"\bfichier\b",
            r"piece jointe",
        ],
    },
    {
        "domain": "veille_juridique",
        "reason": "La demande appelle une veille juridique ou jurisprudence.",
        "patterns": [
            r"\bveille\b",
            r"\bjurisprudence\b",
            r"actualite juridique",
            r"derniers? textes?",
            r"cour de cassation",
            r"nouveau decret",
            r"reforme",
        ],
    },
    {
        "domain": "cse",
        "reason": "La demande appelle une preparation ou discussion CSE.",
        "patterns": [
            r"\bcse\b",
            r"prepare(?:r)? le cse",
            r"prepare(?:r)? .*questions? cse",
            r"point cse",
            r"questions? cse",
            r"consultation cse",
            r"information consultation",
            r"ordre du jour",
            r"la direction veut",
            r"modification .*cycle",
            r"modification .*horaires?",
        ],
    },
]

INTENT_RULES: list[dict[str, Any]] = [
    {
        "intent": "question_simple",
        "reason": "La formulation appelle une reponse courte ou une recherche ciblee.",
        "patterns": [
            r"^combien\b",
            r"^comment\b",
            r"^quels?\b",
            r"^quelle\b",
            r"^que dois-je\b",
            r"^que faut-il\b",
        ],
    },
    {
        "intent": "rechercher_droit_local",
        "reason": "Une recherche dans les accords locaux est necessaire.",
        "patterns": [
            r"accords? locaux?",
            r"parlent? du",
            r"regle",
            r"droit local",
            r"combien",
            r"comment .*paye",
            r"comment .*indemnise",
            r"repos",
            r"astreinte",
            r"droit syndical",
        ],
    },
    {
        "intent": "preparer_cse",
        "reason": "La demande vise une preparation CSE.",
        "patterns": [
            r"prepare(?:r)? .*cse",
            r"point cse",
            r"questions? cse",
            r"\bcse\b",
            r"la direction veut",
            r"modification .*cycle",
            r"modification .*horaires?",
        ],
    },
    {
        "intent": "preparer_cssct",
        "reason": "La demande appelle une preparation CSSCT ou sante-securite.",
        "patterns": [
            r"\bcssct\b",
            r"\bduerp\b",
            r"\bduer\b",
            r"securite process",
            r"\bprovox\b",
            r"\bsncc\b",
            r"\bclimatisation\b",
            r"forte chaleur",
            r"\bpannes?\b",
            r"pieces? de rechange",
            r"\bfatigue\b",
        ],
    },
    {
        "intent": "analyser_situation_individuelle",
        "reason": "La demande concerne un dossier ou une situation de salarie.",
        "patterns": [
            r"\bsalarie\b",
            r"\bsalaries\b",
            r"\binapte\b",
            r"\binaptitude\b",
            r"\breclassement\b",
            r"\bcoefficient\b",
            r"mal classe",
            r"entretien disciplinaire",
            r"\bconvoque\b",
            r"proposition de reclassement",
            r"\brefuse\b",
        ],
    },
    {
        "intent": "analyser_paie",
        "reason": "La demande appelle une methode de controle paie.",
        "patterns": [
            r"\bpaie\b",
            r"\bpaye(?:e|es|s)?\b",
            r"\bremuneration\b",
            r"\bprime\b",
            r"\bbulletin\b",
            r"heures supplementaires",
            r"\bcompteurs?\b",
            r"majoration",
            r"conges payes",
            r"\bdixieme\b",
            r"dimanches?",
            r"jours? feries?",
        ],
    },
    {
        "intent": "analyser_document",
        "reason": "La demande cible l'analyse d'un document.",
        "patterns": [
            r"analyse(?:r)? ce document",
            r"analyse(?:r)? le document",
            r"analyse(?:r)? ce projet",
            r"projet d'?accord",
            r"\bpdf\b",
            r"\bdocx\b",
            r"\bfichier\b",
            r"piece jointe",
        ],
    },
    {
        "intent": "preparer_negociation",
        "reason": "La demande vise une negotiation.",
        "patterns": [
            r"\bnegociation\b",
            r"\bnegocier\b",
            r"preparer .*negociation",
        ],
    },
    {
        "intent": "preparer_entretien_direction",
        "reason": "La demande vise un echange avec la direction.",
        "patterns": [
            r"entretien direction",
            r"rencontrer la direction",
            r"rdv direction",
            r"preparer .*direction",
        ],
    },
    {
        "intent": "construire_argumentaire",
        "reason": "La demande appelle un argumentaire.",
        "patterns": [
            r"\bargumentaire\b",
            r"\barguments?\b",
            r"construire .*position",
            r"defendre",
        ],
    },
    {
        "intent": "demander_documents",
        "reason": "La demande porte sur les documents a demander ou recuperer.",
        "patterns": [
            r"documents? .*demander",
            r"quels? documents?",
            r"documents? .*recuperer",
            r"pieces? .*demander",
        ],
    },
    {
        "intent": "verifier_conformite",
        "reason": "La demande vise une verification ou un controle.",
        "patterns": [
            r"\bverifier\b",
            r"\bverifications?\b",
            r"\bcontrole(?:r)?\b",
            r"\bconforme\b",
            r"\bcalcul\b",
            r"\bregularisation\b",
            r"\becarts?\b",
            r"\brisques?\b",
        ],
    },
    {
        "intent": "rechercher_veille",
        "reason": "La demande appelle une recherche de veille.",
        "patterns": [
            r"\bveille\b",
            r"\bjurisprudence\b",
            r"actualite juridique",
            r"derniers? textes?",
            r"cour de cassation",
            r"nouveau decret",
        ],
    },
]

ROUTING_SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "test-repos-5x8-simple",
        "query": "Combien de repos entre deux postes en 5x8 ?",
        "expected_domains": ["temps_travail"],
        "expected_intents": ["question_simple", "rechercher_droit_local"],
        "expected_engines": ["bible_accords"],
        "forbidden_engines": ["nexus_bible_bridge"],
    },
    {
        "id": "test-cse-reduction-repos",
        "query": "La direction veut reduire le repos entre deux postes. Prepare le CSE.",
        "expected_domains": ["temps_travail", "cse"],
        "expected_intents": ["preparer_cse"],
        "expected_engines": ["bible_accords", "nexus_bible_bridge"],
    },
    {
        "id": "test-classification-coefficient",
        "query": "Un salarie pense etre mal classe car il exerce plus de responsabilites que sa fiche de poste.",
        "expected_domains": ["classification_carriere"],
        "expected_intents": ["analyser_situation_individuelle"],
        "expected_engines": ["bible_accords", "nexus_bible_bridge"],
        "forbidden_domains": ["cssct_securite", "droit_syndical"],
    },
    {
        "id": "test-inaptitude-reclassement",
        "query": "Un salarie est declare inapte. Que dois-je verifier sur le reclassement ?",
        "expected_domains": ["inaptitude_reclassement"],
        "expected_intents": ["analyser_situation_individuelle", "verifier_conformite"],
        "expected_engines": ["bible_accords", "nexus_bible_bridge"],
        "forbidden_domains": ["droit_syndical"],
    },
    {
        "id": "test-heures-supplementaires-compteurs",
        "query": "Des salaries pensent que leurs heures supplementaires disparaissent des compteurs.",
        "expected_domains": ["temps_travail", "paie_remuneration"],
        "expected_intents": ["analyser_paie"],
        "expected_engines": ["bible_accords", "nexus_bible_bridge"],
        "forbidden_domains": ["droit_syndical"],
    },
    {
        "id": "test-astreinte-indemnisation",
        "query": "Comment est indemnisee une intervention pendant une astreinte ?",
        "expected_domains": ["astreinte", "paie_remuneration"],
        "expected_intents": ["question_simple", "rechercher_droit_local"],
        "expected_engines": ["bible_accords"],
    },
    {
        "id": "test-disciplinaire-entretien",
        "query": "Un salarie est convoque a un entretien disciplinaire.",
        "expected_domains": ["disciplinaire"],
        "expected_intents": ["analyser_situation_individuelle"],
        "expected_engines": ["bible_accords", "nexus_bible_bridge"],
    },
    {
        "id": "test-droit-syndical-delegation",
        "query": "Combien d'heures de delegation pour les elus ?",
        "expected_domains": ["droit_syndical"],
        "expected_intents": ["question_simple", "rechercher_droit_local"],
        "expected_engines": ["bible_accords"],
    },
    {
        "id": "test-provox-cssct",
        "query": "PROVOX tombe regulierement en panne et les pieces de rechange sont difficiles a obtenir.",
        "expected_domains": ["cssct_securite"],
        "expected_intents": ["preparer_cssct"],
        "expected_engines": ["bible_accords", "nexus_bible_bridge"],
        "forbidden_domains": ["paie_remuneration", "droit_syndical"],
    },
    {
        "id": "test-sncc-chaleur-cssct",
        "query": "La climatisation du SNCC est defaillante et les salaries signalent une forte chaleur.",
        "expected_domains": ["cssct_securite"],
        "expected_intents": ["preparer_cssct"],
        "expected_engines": ["bible_accords", "nexus_bible_bridge"],
        "forbidden_domains": ["paie_remuneration"],
    },
    {
        "id": "test-dimanches-feries-paie",
        "query": "Comment sont payes les dimanches et jours feries ?",
        "expected_domains": ["temps_travail", "paie_remuneration"],
        "expected_intents": ["question_simple", "rechercher_droit_local", "analyser_paie"],
        "expected_engines": ["bible_accords"],
    },
    {
        "id": "test-fatigue-postes-cse",
        "query": "Prepare-moi des questions CSE sur la fatigue des postes.",
        "expected_domains": ["temps_travail", "cssct_securite", "cse"],
        "expected_intents": ["preparer_cse", "preparer_cssct"],
        "expected_engines": ["bible_accords", "nexus_bible_bridge"],
    },
    {
        "id": "test-conges-payes-dixieme",
        "query": "Je veux verifier le calcul des conges payes au dixieme.",
        "expected_domains": ["paie_remuneration", "conges_payes"],
        "expected_intents": ["analyser_paie", "verifier_conformite"],
        "expected_engines": ["bible_accords", "nexus_bible_bridge"],
    },
    {
        "id": "test-cycle-5x8-risques",
        "query": "Analyse les risques d'une modification du cycle 5x8.",
        "expected_domains": ["temps_travail", "cse"],
        "expected_intents": ["preparer_cse", "verifier_conformite"],
        "expected_engines": ["bible_accords", "nexus_bible_bridge"],
    },
    {
        "id": "test-refus-revoir-coefficient",
        "query": "La direction refuse de revoir le coefficient d'un salarie.",
        "expected_domains": ["classification_carriere"],
        "expected_intents": ["analyser_situation_individuelle"],
        "expected_engines": ["bible_accords", "nexus_bible_bridge"],
        "forbidden_domains": ["cssct_securite", "droit_syndical"],
    },
    {
        "id": "test-documents-compteurs-heures",
        "query": "Quels documents demander pour controler les compteurs d'heures ?",
        "expected_domains": ["temps_travail", "paie_remuneration"],
        "expected_intents": ["question_simple", "demander_documents", "verifier_conformite"],
        "expected_engines": ["bible_accords", "nexus_bible_bridge"],
        "forbidden_domains": ["droit_syndical"],
    },
    {
        "id": "test-argumentaire-horaires",
        "query": "Prepare un argumentaire sur une modification des horaires.",
        "expected_domains": ["temps_travail", "cse"],
        "expected_intents": ["preparer_cse", "construire_argumentaire"],
        "expected_engines": ["bible_accords", "nexus_bible_bridge"],
    },
    {
        "id": "test-accords-droit-syndical",
        "query": "Quels accords locaux parlent du droit syndical ?",
        "expected_domains": ["droit_syndical"],
        "expected_intents": ["question_simple", "rechercher_droit_local"],
        "expected_engines": ["bible_accords"],
    },
    {
        "id": "test-negociation-prime",
        "query": "Je veux preparer une negociation sur une prime.",
        "expected_domains": ["paie_remuneration"],
        "expected_intents": ["preparer_negociation"],
        "expected_engines": ["bible_accords", "nexus_bible_bridge"],
    },
    {
        "id": "test-refus-proposition-reclassement",
        "query": "Le salarie refuse une proposition de reclassement, quelles verifications faire ?",
        "expected_domains": ["inaptitude_reclassement"],
        "expected_intents": ["analyser_situation_individuelle", "verifier_conformite"],
        "expected_engines": ["bible_accords", "nexus_bible_bridge"],
    },
    {
        "id": "test-multi-astreinte-nuit-repos-paie",
        "query": "Un salarie d'astreinte intervient de nuit, termine a 4 h et reprend son poste a 8 h. Il pense aussi que ses heures ont ete mal payees.",
        "expected_domains": ["temps_travail", "astreinte", "paie_remuneration"],
        "expected_intents": ["analyser_situation_individuelle", "analyser_paie", "verifier_conformite"],
        "expected_engines": ["bible_accords", "nexus_bible_bridge"],
    },
    {
        "id": "test-multi-cycle-5x8-fatigue-prime",
        "query": "La direction veut modifier le cycle 5x8, les salaries craignent plus de fatigue et une perte de prime.",
        "expected_domains": ["temps_travail", "cssct_securite", "paie_remuneration", "cse"],
        "expected_intents": ["preparer_cse", "preparer_cssct", "analyser_paie"],
        "expected_engines": ["bible_accords", "nexus_bible_bridge"],
    },
    {
        "id": "test-multi-inaptitude-horaires-reclassement",
        "query": "Un salarie inapte propose un poste compatible mais la direction change aussi ses horaires.",
        "expected_domains": ["inaptitude_reclassement", "temps_travail"],
        "expected_intents": ["analyser_situation_individuelle", "verifier_conformite"],
        "expected_engines": ["bible_accords", "nexus_bible_bridge"],
    },
    {
        "id": "test-multi-document-accord-prime",
        "query": "Analyse ce projet d'accord sur une prime et dis-moi ce qu'on perd en paie.",
        "expected_domains": ["analyse_documentaire", "paie_remuneration"],
        "expected_intents": ["analyser_document", "preparer_negociation", "analyser_paie"],
        "expected_engines": ["bible_accords"],
    },
    {
        "id": "test-multi-discipline-representant",
        "query": "Un elu CSE est convoque a un entretien disciplinaire apres une intervention syndicale.",
        "expected_domains": ["disciplinaire", "droit_syndical"],
        "expected_intents": ["analyser_situation_individuelle"],
        "expected_engines": ["bible_accords", "nexus_bible_bridge"],
    },
]


def normalize(value: str) -> str:
    return bible.normalize(value or "")


def match_patterns(text: str, patterns: list[str]) -> list[str]:
    return [pattern for pattern in patterns if re.search(pattern, text)]


def dedupe(values: list[Any]) -> list[Any]:
    seen: set[str] = set()
    result: list[Any] = []
    for value in values:
        key = normalize(json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, dict) else str(value))
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def compact_text(value: Any) -> str:
    if isinstance(value, dict):
        label = value.get("categorie") or value.get("element") or value.get("document") or value.get("si_reponse_direction")
        detail = (
            value.get("analyse")
            or value.get("risque_ou_effet_possible")
            or value.get("role_probable_du_document")
            or value.get("relances")
            or value.get("situation_actuelle")
            or value.get("condition")
        )
        if isinstance(detail, list):
            detail = "; ".join(str(item) for item in detail)
        if label and detail:
            return f"{label}: {detail}"
        if label:
            return str(label)
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def source_key(source: dict[str, Any]) -> str:
    return "|".join(
        normalize(str(source.get(key) or ""))
        for key in ["document", "page", "article", "article_or_section", "location"]
    )


def normalize_source(source: dict[str, Any], origin: str) -> dict[str, Any]:
    article = source.get("article") or source.get("article_or_section")
    page = source.get("page")
    return {
        "document": source.get("document"),
        "page": page,
        "article": article,
        "location": source.get("location") or " - ".join(part for part in [f"Page {page}" if page else "", article or ""] if part),
        "score": source.get("score") or source.get("match_score"),
        "status": source.get("source_status") or source.get("confidence_level") or source.get("source_quality_warning"),
        "origin": origin,
        "nature": "regle_locale_a_verifier",
    }


def primary_domain(domains: list[str]) -> str:
    for domain in DOMAIN_ORDER:
        if domain in domains:
            return domain
    return "bible_accords"


def detect_domains(query: str) -> tuple[list[str], list[str], dict[str, int]]:
    text = normalize(query)
    scores: dict[str, int] = {}
    reasons: list[str] = []
    for rule in DOMAIN_RULES:
        matches = match_patterns(text, rule["patterns"])
        if not matches:
            continue
        scores[rule["domain"]] = scores.get(rule["domain"], 0) + len(matches)
        reasons.append(rule["reason"])

    domains = [domain for domain in DOMAIN_ORDER if scores.get(domain)]
    if "droit_syndical" in domains and not re.search(
        r"droit syndical|mandat|elu(?:s)? cse|elus?|delegue syndical|representant syndical|heures? de delegation|credit d'?heures|moyens? syndicaux?|local syndical|affichage syndical|reunions? syndicales?|fonctionnement du cse",
        text,
    ):
        domains.remove("droit_syndical")
        scores.pop("droit_syndical", None)

    if not domains and re.search(r"\baccords?\b|\blocal\b|\bconvention\b|\breglement interieur\b", text):
        reasons.append("La demande appelle au moins une recherche documentaire locale.")

    return ["bible_accords", *domains], dedupe(reasons), scores


def detect_intents(query: str, domains: list[str]) -> tuple[list[str], list[str], dict[str, int]]:
    text = normalize(query)
    scores: dict[str, int] = {}
    reasons: list[str] = []
    for rule in INTENT_RULES:
        matches = match_patterns(text, rule["patterns"])
        if not matches:
            continue
        scores[rule["intent"]] = scores.get(rule["intent"], 0) + len(matches)
        reasons.append(rule["reason"])

    if "cssct_securite" in domains and "preparer_cssct" not in scores:
        scores["preparer_cssct"] = 1
        reasons.append("Le domaine sante-securite appelle une preparation CSSCT/CSE.")
    if any(domain in domains for domain in ["classification_carriere", "inaptitude_reclassement", "disciplinaire"]):
        scores.setdefault("analyser_situation_individuelle", 1)
        reasons.append("Le domaine RH detecte appelle une fiche de situation individuelle.")
    if any(domain in domains for domain in ["temps_travail", "paie_remuneration", "conges_payes"]) and re.search(
        r"verifier|controler|calcul|compteurs?|heures supplementaires|mal paye|dixieme", text
    ):
        scores.setdefault("verifier_conformite", 1)
        reasons.append("La demande appelle une verification de conformite ou de calcul.")
    if "inaptitude_reclassement" in domains and re.search(r"refuse|propose|proposition|change|horaires?", text):
        scores.setdefault("verifier_conformite", 1)
        reasons.append("Le reclassement detecte appelle une verification de conformite et de tracabilite.")
    if "analyse_documentaire" in domains and "preparer_negociation" not in scores and re.search(r"accord|ce qu'on perd|perd", text):
        scores["preparer_negociation"] = 1
        reasons.append("L'analyse documentaire mentionne un projet d'accord ou une perte a negocier.")
    if not scores:
        scores["question_simple"] = 1
        scores["rechercher_droit_local"] = 1
        reasons.append("Aucune intention complexe n'est detectee : recherche locale simple.")

    intents = [intent for intent in INTENTS if scores.get(intent)]
    return intents, dedupe(reasons), scores


def simple_bible_only(intents: list[str], domains: list[str], query: str) -> bool:
    text = normalize(query)
    complex_intents = {
        "preparer_cse",
        "preparer_cssct",
        "analyser_situation_individuelle",
        "analyser_document",
        "preparer_negociation",
        "preparer_entretien_direction",
        "construire_argumentaire",
        "demander_documents",
        "verifier_conformite",
    }
    if any(intent in intents for intent in complex_intents):
        return False
    if "question_simple" in intents and "rechercher_droit_local" in intents:
        return True
    return bool(re.search(r"^combien|^comment|^quels?", text))


def engine_status() -> dict[str, dict[str, Any]]:
    chunks_path = bible.INDEX_DIR / "chunks.private.jsonl"
    chunks = bible.read_jsonl(chunks_path) if chunks_path.exists() else []
    return {
        "bible_accords": {
            "available": bool(chunks),
            "chunks": len(chunks),
            "path": str(chunks_path),
        },
        "nexus_bible_bridge": {
            "available": bridge is not None and (SCRIPT_DIR / "nexus_bible_bridge.py").exists(),
            "path": str(SCRIPT_DIR / "nexus_bible_bridge.py"),
        },
        "document_intelligence": {
            "available": False,
            "detected": DIC_DIR.exists(),
            "path": str(DIC_DIR),
            "reason": "module detecte mais connecteur d'execution non disponible",
        },
        "cycle_cse": {
            "available": False,
            "detected": CYCLE_CSE_DIR.exists(),
            "path": str(CYCLE_CSE_DIR),
            "reason": "interface detectee ; execution locale couverte par nexus_bible_bridge",
        },
        "paie_control": {
            "available": False,
            "detected": False,
            "reason": "module paie dedie non connecte en V1",
        },
        "veille_juridique": {
            "available": False,
            "detected": False,
            "reason": "connecteur de veille non connecte en V1",
        },
    }


def choose_engines(query: str, domains: list[str], intents: list[str]) -> tuple[list[str], list[dict[str, Any]], list[str]]:
    status = engine_status()
    engines = ["bible_accords"]
    warnings: list[str] = []
    text = normalize(query)

    needs_bridge = False
    if any(intent in intents for intent in ["preparer_cse", "preparer_cssct", "analyser_situation_individuelle", "construire_argumentaire", "demander_documents", "verifier_conformite", "preparer_negociation"]):
        needs_bridge = True
    if any(domain in domains for domain in ["classification_carriere", "inaptitude_reclassement", "disciplinaire"]):
        needs_bridge = True
    if "analyser_paie" in intents and not simple_bible_only(intents, domains, query):
        needs_bridge = True
    if simple_bible_only(intents, domains, query) and not re.search(r"documents? .*demander|controler|verifier|salaries? pensent|mal paye", text):
        needs_bridge = False

    if needs_bridge:
        if status["nexus_bible_bridge"]["available"]:
            engines.append("nexus_bible_bridge")
        else:
            warnings.append("nexus_bible_bridge detecte comme necessaire mais non disponible.")

    if "analyse_documentaire" in domains:
        warnings.append("Document Intelligence Center : module detecte mais connecteur d'execution non disponible.")
    if "analyser_paie" in intents:
        warnings.append("Module paie dedie non connecte : controle realise via sources locales et methode metier.")
    if "rechercher_veille" in intents or "veille_juridique" in domains:
        warnings.append("Veille juridique non connectee en V1 : verifier les sources externes a jour manuellement.")

    engines = dedupe(engines)
    plan = []
    for engine in engines:
        if engine == "bible_accords":
            plan.append(
                {
                    "engine": engine,
                    "action": "rechercher les textes locaux pertinents dans l'index Bible Accords",
                    "status": "connected" if status[engine]["available"] else "unavailable",
                }
            )
        elif engine == "nexus_bible_bridge":
            plan.append(
                {
                    "engine": engine,
                    "action": "construire une fiche metier CSE/RH/Paie a partir des sources locales",
                    "status": "connected",
                }
            )

    if "analyse_documentaire" in domains:
        plan.append(
            {
                "engine": "document_intelligence",
                "action": "analyse documentaire",
                "status": "unavailable",
                "detail": status["document_intelligence"]["reason"],
            }
        )
    if "rechercher_veille" in intents or "veille_juridique" in domains:
        plan.append(
            {
                "engine": "veille_juridique",
                "action": "recherche de veille juridique",
                "status": "unavailable",
                "detail": status["veille_juridique"]["reason"],
            }
        )

    return engines, plan, dedupe(warnings)


def route_query(query: str) -> dict[str, Any]:
    domains, domain_reasons, domain_scores = detect_domains(query)
    intents, intent_reasons, intent_scores = detect_intents(query, domains)
    engines, execution_plan, warnings = choose_engines(query, domains, intents)
    score_total = sum(domain_scores.values()) + sum(intent_scores.values())
    confidence = "fort" if score_total >= 5 else "moyen" if score_total >= 2 else "faible"
    main_domain = primary_domain(domains)
    route = {
        "query": query,
        "domains": domains,
        "main_domain": main_domain,
        "intents": intents,
        "engines": engines,
        "confidence": confidence,
        "reasoning_summary": dedupe(domain_reasons + intent_reasons)[:8],
        "execution_plan": execution_plan,
        "warnings": warnings,
    }
    return route


def search_bible(query: str, limit: int) -> dict[str, Any]:
    args = argparse.Namespace(query=query, limit=limit, theme=None, doc_type=None, document_id=None)
    return bible.search_index(args, save=False, quiet=True)


def understanding_for(route: dict[str, Any]) -> str:
    main = route["main_domain"].replace("_", " ")
    intents = ", ".join(intent.replace("_", " ") for intent in route["intents"][:3])
    return f"Demande classee principalement en {main}, avec intention(s) {intents}."


def default_documents(route: dict[str, Any]) -> list[str]:
    domains = set(route["domains"])
    documents: list[str] = []
    if "classification_carriere" in domains:
        documents.extend(
            [
                "fiche de poste actuelle",
                "fonctions reellement exercees",
                "niveau d'autonomie et responsabilites",
                "historique des changements de poste",
                "comparaison avec salaries similaires",
                "criteres conventionnels et demande de reexamen du coefficient",
            ]
        )
    if "inaptitude_reclassement" in domains:
        documents.extend(
            [
                "avis du medecin du travail et restrictions",
                "etude de poste",
                "postes disponibles et adaptations possibles",
                "formations envisageables",
                "perimetre de reclassement",
                "tracabilite des recherches et echanges avec le salarie",
            ]
        )
    if "temps_travail" in domains and ("paie_remuneration" in domains or "analyser_paie" in route["intents"]):
        documents.extend(
            [
                "releves de pointage",
                "compteurs d'heures",
                "heures validees et refusees",
                "regles de majoration et de recuperation",
                "contingent et repos compensateur",
                "parametrage logiciel et periode a controler",
            ]
        )
    if "disciplinaire" in domains:
        documents.extend(["convocation", "reglement interieur", "faits reproches", "dossier disciplinaire communique"])
    if "cssct_securite" in domains:
        documents.extend(["DUERP/DUER", "registre securite", "signalements salaries", "plan de maintenance ou de contingence"])
    if "droit_syndical" in domains:
        documents.extend(["accords ou usages sur heures de delegation", "regles de fonctionnement CSE", "moyens syndicaux applicables"])
    return dedupe(documents)


def default_questions(route: dict[str, Any]) -> list[str]:
    domains = set(route["domains"])
    questions: list[str] = []
    if "classification_carriere" in domains:
        questions.extend(
            [
                "Quelles fonctions sont reellement exercees au-dela de la fiche de poste ?",
                "Quels criteres conventionnels justifient ou contestent le coefficient actuel ?",
                "Quels salaries comparables occupent des fonctions similaires ?",
            ]
        )
    if "inaptitude_reclassement" in domains:
        questions.extend(
            [
                "Quelles restrictions le medecin du travail a-t-il formulees ?",
                "Quels postes disponibles ont ete examines et pourquoi ont-ils ete ecartes ?",
                "Quelle tracabilite existe sur les echanges avec le salarie ?",
            ]
        )
    if "temps_travail" in domains and ("paie_remuneration" in domains or "analyser_paie" in route["intents"]):
        questions.extend(
            [
                "Comment les heures effectuees sont-elles rapprochees du pointage, des compteurs et de la paie ?",
                "Quelles heures ont ete validees, refusees, payees ou recuperees ?",
                "Quel parametre logiciel applique les majorations, contingents et repos compensateurs ?",
            ]
        )
    if "cssct_securite" in domains:
        questions.extend(
            [
                "Quels risques sont identifies dans le DUERP et quelles actions sont planifiees ?",
                "Quels incidents, pannes ou signalements ont ete traces ?",
                "Quelles mesures immediates protegent les salaries ?",
            ]
        )
    if "disciplinaire" in domains:
        questions.extend(["Quels faits precis sont reproches ?", "Quels delais et droits de defense ont ete respectes ?"])
    return dedupe(questions)


def position_for(route: dict[str, Any], findings: list[str]) -> str:
    domains = set(route["domains"])
    if "classification_carriere" in domains:
        return "Construire un dossier factuel sur les fonctions exercees avant de demander le reexamen du coefficient."
    if "inaptitude_reclassement" in domains:
        return "Verifier la realite, la loyauté et la tracabilite de la recherche de reclassement avant toute conclusion."
    if "temps_travail" in domains and ("paie_remuneration" in domains or "analyser_paie" in route["intents"]):
        return "Rapprocher heures effectuees, compteurs, recuperation et bulletins avant de demander correction ou regularisation."
    if "cssct_securite" in domains:
        return "Objectiver les risques, demander les documents techniques et exiger des mesures de prevention tracees."
    if "droit_syndical" in domains:
        return "Identifier le texte local applicable puis verifier qu'il vise bien les mandats et moyens syndicaux."
    if findings:
        return "Utiliser les sources locales comme base de travail, sans conclure avant verification humaine."
    return "Demande a approfondir avec les sources locales et les elements factuels."


def next_action_for(route: dict[str, Any]) -> str:
    domains = set(route["domains"])
    if "question_simple" in route["intents"] and route["engines"] == ["bible_accords"]:
        return "Relire les sources citees et verifier si un avenant ou une regle plus recente existe."
    if "classification_carriere" in domains:
        return "Rassembler fiche de poste, fonctions reelles et comparaisons internes avant demande de reexamen."
    if "inaptitude_reclassement" in domains:
        return "Reconstituer la chronologie medecin du travail, etude de poste, recherches et echanges salarie."
    if "temps_travail" in domains and ("paie_remuneration" in domains or "analyser_paie" in route["intents"]):
        return "Fixer une periode de controle puis rapprocher pointage, compteurs, recuperation et bulletins."
    if "preparer_cse" in route["intents"] or "preparer_cssct" in route["intents"]:
        return "Mettre le sujet a l'ordre du jour avec les documents demandes et les questions prioritaires."
    return "Completer les faits, relire les sources citees puis choisir la suite syndicale adaptee."


def merge_bible_result(answer: dict[str, Any], result: dict[str, Any]) -> None:
    for source in result.get("sources_used", [])[:8]:
        answer["sources"].append(normalize_source(source, "bible_accords"))
    answer["findings"].extend(result.get("points_to_verify", []))
    if result.get("recommended_human_action"):
        answer["findings"].append(result["recommended_human_action"])


def merge_bridge_result(answer: dict[str, Any], report: dict[str, Any]) -> None:
    for source in report.get("2_textes_locaux_potentiellement_concernes", [])[:8]:
        answer["sources"].append(normalize_source(source, "nexus_bible_bridge"))
    answer["findings"].extend(compact_text(item) for item in report.get("3_situation_actuelle_a_verifier", [])[:8])
    answer["findings"].extend(compact_text(item) for item in report.get("7_risques_et_points_de_vigilance", [])[:8])
    answer["documents_to_request"].extend(compact_text(item) for item in report.get("9_documents_a_demander", [])[:12])
    answer["questions_to_ask"].extend(compact_text(item) for item in report.get("10_questions_principales_a_poser_en_cse", [])[:12])
    position = report.get("13_position_cfdt_a_construire")
    if isinstance(position, dict):
        points = position.get("conditions_minimales") or position.get("points_non_acceptables_sans_garantie") or []
        if points:
            answer["working_position"] = compact_text(points[0])
    elif position:
        answer["working_position"] = compact_text(position)
    if report.get("niveau_de_confiance"):
        answer["confidence"] = report["niveau_de_confiance"]


def finalize_answer(answer: dict[str, Any]) -> dict[str, Any]:
    answer["sources"] = dedupe(answer["sources"])
    source_seen: set[str] = set()
    source_rows = []
    for source in answer["sources"]:
        key = source_key(source)
        if key and key not in source_seen:
            source_seen.add(key)
            source_rows.append(source)
    answer["sources"] = source_rows[:10]
    answer["findings"] = dedupe([item for item in answer["findings"] if item])[:12]
    answer["documents_to_request"] = dedupe(answer["documents_to_request"] + default_documents(answer["route"]))[:14]
    answer["questions_to_ask"] = dedupe(answer["questions_to_ask"] + default_questions(answer["route"]))[:14]
    answer["warnings"] = dedupe(answer["warnings"] + [PRUDENCE_WARNING])
    if not answer["working_position"]:
        answer["working_position"] = position_for(answer["route"], answer["findings"])
    if not answer["next_action"]:
        answer["next_action"] = next_action_for(answer["route"])
    return answer


def ask(query: str, limit: int) -> dict[str, Any]:
    route = route_query(query)
    answer: dict[str, Any] = {
        "query": query,
        "understanding": understanding_for(route),
        "route": route,
        "execution_plan": route["execution_plan"],
        "sources": [],
        "findings": [],
        "documents_to_request": [],
        "questions_to_ask": [],
        "working_position": "",
        "next_action": "",
        "confidence": route["confidence"],
        "warnings": list(route["warnings"]),
    }

    if "bible_accords" in route["engines"]:
        try:
            merge_bible_result(answer, search_bible(query, limit))
        except SystemExit as exc:
            answer["warnings"].append(f"Bible Accords indisponible ou index vide: {exc}")

    if "nexus_bible_bridge" in route["engines"] and bridge is not None:
        try:
            report = bridge.build_cse_analysis(query[:80], query, limit)
            merge_bridge_result(answer, report)
        except SystemExit as exc:
            answer["warnings"].append(f"Pont Nexus/Bible indisponible: {exc}")

    return finalize_answer(answer)


def format_route_text(route: dict[str, Any]) -> str:
    lines = [
        "ROUTAGE ASSISTANT DS",
        "",
        f"Question : {route['query']}",
        f"Domaine principal : {route['main_domain']}",
        "Domaines : " + ", ".join(route["domains"]),
        "Intentions : " + ", ".join(route["intents"]),
        "Moteurs : " + ", ".join(route["engines"]),
        f"Niveau de confiance : {route['confidence']}",
        "",
        "Resume du routage :",
    ]
    lines.extend(f"- {reason}" for reason in route["reasoning_summary"])
    if route["execution_plan"]:
        lines.extend(["", "Plan d'execution :"])
        for step in route["execution_plan"]:
            detail = f" ({step['detail']})" if step.get("detail") else ""
            lines.append(f"- {step['engine']} [{step['status']}] : {step['action']}{detail}")
    if route["warnings"]:
        lines.extend(["", "Avertissements :"])
        lines.extend(f"- {warning}" for warning in route["warnings"])
    return "\n".join(lines)


def format_answer_text(answer: dict[str, Any]) -> str:
    def list_or_dash(values: list[Any], formatter=str) -> list[str]:
        if not values:
            return ["- A completer apres lecture des sources locales."]
        return [f"- {formatter(value)}" for value in values]

    def source_line(source: dict[str, Any]) -> str:
        parts = [str(source.get("document") or "Document local")]
        if source.get("page"):
            parts.append(f"page {source['page']}")
        if source.get("article"):
            parts.append(str(source["article"]))
        if source.get("status"):
            parts.append(str(source["status"]))
        return " | ".join(parts)

    lines = [
        "ASSISTANT DS — ANALYSE",
        "",
        "Question :",
        answer["query"],
        "",
        "Compréhension :",
        answer["understanding"],
        "",
        "Sources locales principales :",
    ]
    lines.extend(list_or_dash(answer["sources"], source_line))
    lines.extend(["", "Ce qu'il faut verifier :"])
    lines.extend(list_or_dash(answer["findings"]))
    lines.extend(["", "Documents à récupérer :"])
    lines.extend(list_or_dash(answer["documents_to_request"]))
    lines.extend(["", "Questions a poser :"])
    lines.extend(list_or_dash(answer["questions_to_ask"]))
    lines.extend(
        [
            "",
            "Position de travail :",
            answer["working_position"],
            "",
            "Prochaine action recommandée :",
            answer["next_action"],
            "",
            "Niveau de confiance :",
            answer["confidence"],
            "",
            "Avertissement :",
        ]
    )
    lines.extend(f"- {warning}" for warning in answer["warnings"])
    return "\n".join(lines)


def diagnose() -> dict[str, Any]:
    status = engine_status()
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8") if (ROOT / ".gitignore").exists() else ""
    local_index_ignored = any(line.strip() == "local-index/" for line in gitignore.splitlines())
    source_config = bible.SOURCE_CONFIG_PATH
    errors: list[str] = []
    if not local_index_ignored:
        errors.append("local-index/ n'est pas ignore par Git.")
    if not status["bible_accords"]["available"]:
        errors.append("Index Bible Accords absent ou vide.")
    if not status["nexus_bible_bridge"]["available"]:
        errors.append("nexus_bible_bridge.py indisponible.")
    return {
        "bible_accords_available": status["bible_accords"]["available"],
        "chunks": status["bible_accords"]["chunks"],
        "nexus_bible_bridge_available": status["nexus_bible_bridge"]["available"],
        "document_intelligence": status["document_intelligence"],
        "cycle_cse": status["cycle_cse"],
        "paie_control": status["paie_control"],
        "veille_juridique": status["veille_juridique"],
        "corpus_local_configured": source_config.exists(),
        "source_config_path": str(source_config),
        "local_index_ignored": local_index_ignored,
        "errors": errors,
        "security_notice": "local-index/ et les fichiers *.private.* doivent rester hors Git.",
    }


def format_diagnose_text(report: dict[str, Any]) -> str:
    lines = [
        "DIAGNOSTIC ASSISTANT DS ROUTER",
        f"Bible Accords disponible : {'oui' if report['bible_accords_available'] else 'non'}",
        f"Chunks indexes : {report['chunks']}",
        f"Pont nexus_bible_bridge.py disponible : {'oui' if report['nexus_bible_bridge_available'] else 'non'}",
        f"Document Intelligence Center : {report['document_intelligence']['reason']}",
        f"Cycle CSE : {report['cycle_cse']['reason']}",
        f"Module paie : {report['paie_control']['reason']}",
        f"Veille juridique : {report['veille_juridique']['reason']}",
        f"Corpus local configure : {'oui' if report['corpus_local_configured'] else 'non'}",
        f"local-index/ ignore par Git : {'oui' if report['local_index_ignored'] else 'non'}",
    ]
    if report["errors"]:
        lines.append("Erreurs :")
        lines.extend(f"- {error}" for error in report["errors"])
    else:
        lines.append("Erreurs : aucune")
    lines.append(report["security_notice"])
    return "\n".join(lines)


def validate_scenario(scenario: dict[str, Any], route: dict[str, Any]) -> list[dict[str, Any]]:
    domains = set(route["domains"])
    intents = set(route["intents"])
    engines = set(route["engines"])
    checks: list[dict[str, Any]] = []
    for domain in scenario.get("expected_domains", []):
        checks.append({"name": f"domaine_{domain}", "ok": domain in domains, "detail": domain})
    for intent in scenario.get("expected_intents", []):
        checks.append({"name": f"intention_{intent}", "ok": intent in intents, "detail": intent})
    for engine in scenario.get("expected_engines", []):
        checks.append({"name": f"moteur_{engine}", "ok": engine in engines, "detail": engine})
    for domain in scenario.get("forbidden_domains", []):
        checks.append({"name": f"absence_domaine_{domain}", "ok": domain not in domains, "detail": domain})
    for engine in scenario.get("forbidden_engines", []):
        checks.append({"name": f"absence_moteur_{engine}", "ok": engine not in engines, "detail": engine})
    if scenario["id"] == "test-repos-5x8-simple":
        checks.append(
            {
                "name": "question_simple_sans_fiche_cse_complete",
                "ok": "nexus_bible_bridge" not in engines,
                "detail": "la question simple reste limitee a la Bible Accords",
            }
        )
    return checks


def run_scenarios() -> dict[str, Any]:
    rows = []
    for scenario in ROUTING_SCENARIOS:
        route = route_query(scenario["query"])
        checks = validate_scenario(scenario, route)
        ok = all(check["ok"] for check in checks)
        rows.append(
            {
                "id": scenario["id"],
                "query": scenario["query"],
                "main_domain": route["main_domain"],
                "domains": route["domains"],
                "intents": route["intents"],
                "engines": route["engines"],
                "ok": ok,
                "checks": checks,
            }
        )
    simple_count = len([row for row in rows if not row["id"].startswith("test-multi-")])
    multi_count = len([row for row in rows if row["id"].startswith("test-multi-")])
    return {
        "scenario_count": len(rows),
        "simple_scenarios": simple_count,
        "multi_domain_scenarios": multi_count,
        "ok": all(row["ok"] for row in rows) and simple_count >= 20 and multi_count >= 5,
        "rows": rows,
    }


def format_scenarios_text(report: dict[str, Any]) -> str:
    lines = [
        "SCENARIOS ASSISTANT DS ROUTER",
        f"Scenarios : {report['scenario_count']} dont {report['simple_scenarios']} simples et {report['multi_domain_scenarios']} multi-domaines",
        f"Statut global : {'OK' if report['ok'] else 'ERREUR'}",
        "",
    ]
    for row in report["rows"]:
        status = "OK" if row["ok"] else "ERREUR"
        failed = [check["name"] for check in row["checks"] if not check["ok"]]
        suffix = "" if not failed else " | echecs: " + ", ".join(failed)
        lines.append(f"- {row['id']} | {status} | {row['main_domain']} | {', '.join(row['engines'])}{suffix}")
    return "\n".join(lines)


def emit(data: dict[str, Any], fmt: str, text_formatter) -> None:
    if fmt == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(text_formatter(data))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CFDT Nexus - Assistant DS router V1")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ask = sub.add_parser("ask")
    p_ask.add_argument("--query", required=True)
    p_ask.add_argument("--limit", type=int, default=6)
    p_ask.add_argument("--format", choices=["text", "json"], default="text")

    p_route = sub.add_parser("route")
    p_route.add_argument("--query", required=True)
    p_route.add_argument("--format", choices=["text", "json"], default="text")

    p_diagnose = sub.add_parser("diagnose")
    p_diagnose.add_argument("--format", choices=["text", "json"], default="text")

    p_scenarios = sub.add_parser("run-scenarios")
    p_scenarios.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "route":
        emit(route_query(args.query), args.format, format_route_text)
    elif args.command == "ask":
        emit(ask(args.query, args.limit), args.format, format_answer_text)
    elif args.command == "diagnose":
        emit(diagnose(), args.format, format_diagnose_text)
    elif args.command == "run-scenarios":
        report = run_scenarios()
        emit(report, args.format, format_scenarios_text)
        if not report["ok"]:
            raise SystemExit(1)
    else:
        raise SystemExit(f"Commande inconnue: {args.command}")


if __name__ == "__main__":
    main()
