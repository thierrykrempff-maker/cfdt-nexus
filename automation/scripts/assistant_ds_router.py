#!/usr/bin/env python
"""
Assistant DS CFDT Nexus V1.1.

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

ROUTER_VERSION = "1.1"
DEFAULT_SOURCE_LIMIT = 6
MAX_SOURCE_LIMIT = 12

BUSINESS_DOMAIN_EXCLUSIONS = {"bible_accords"}

PRUDENCE_POINTS = [
    "Verifier l'applicabilite, la date et le champ des textes cites.",
    "Verifier les avenants, usages ou textes plus recents eventuels.",
    "Articuler les accords locaux avec la convention collective, la loi et la jurisprudence utile.",
]

GENERIC_PRUDENCE_MARKERS = [
    "verifier si le document est toujours applicable",
    "verifier s il existe un avenant",
    "croiser avec la convention collective",
    "relire les sources citees",
    "valider la portee avant utilisation",
]

DOMAIN_LABELS = {
    "bible_accords": "Bible Accords",
    "classification_carriere": "classification/carriere",
    "inaptitude_reclassement": "inaptitude/reclassement",
    "disciplinaire": "disciplinaire",
    "cssct_securite": "CSSCT/securite",
    "temps_travail": "temps de travail",
    "astreinte": "astreinte",
    "paie_remuneration": "paie/remuneration",
    "conges_payes": "conges payes",
    "droit_syndical": "droit syndical",
    "analyse_documentaire": "analyse documentaire",
    "veille_juridique": "veille juridique",
    "cse": "CSE",
}

INTENT_LABELS = {
    "question_simple": "question simple",
    "rechercher_droit_local": "recherche de droit local",
    "preparer_cse": "preparation CSE",
    "preparer_cssct": "preparation CSSCT",
    "analyser_situation_individuelle": "situation individuelle",
    "analyser_paie": "controle paie",
    "analyser_document": "analyse documentaire",
    "preparer_negociation": "preparation de negociation",
    "preparer_entretien_direction": "entretien direction",
    "construire_argumentaire": "argumentaire",
    "demander_documents": "demande de documents",
    "verifier_conformite": "controle de conformite",
    "rechercher_veille": "veille juridique",
}

STOPWORDS = {
    "a",
    "afin",
    "ai",
    "ainsi",
    "alors",
    "au",
    "aux",
    "avec",
    "avant",
    "ce",
    "ces",
    "cet",
    "cette",
    "comme",
    "dans",
    "de",
    "des",
    "du",
    "elle",
    "en",
    "est",
    "et",
    "etre",
    "faire",
    "il",
    "ils",
    "la",
    "le",
    "les",
    "leur",
    "leurs",
    "mais",
    "ou",
    "par",
    "pas",
    "pour",
    "que",
    "qui",
    "sa",
    "sans",
    "se",
    "si",
    "son",
    "sur",
    "un",
    "une",
    "verifier",
    "verification",
    "verifications",
}

DOMAIN_SOURCE_BOOSTS: dict[str, list[tuple[str, int]]] = {
    "classification_carriere": [
        ("classification", 28),
        ("coefficient", 24),
        ("gepp", 26),
        ("gestion de carriere", 22),
        ("carriere", 16),
        ("emploi", 16),
        ("fiche de poste", 18),
        ("fonction", 16),
        ("responsabilite", 14),
        ("autonomie", 14),
        ("technicite", 14),
        ("pesee de poste", 20),
        ("ccnic", 12),
    ],
    "temps_travail": [
        ("5x8", 34),
        ("35 h", 22),
        ("35h", 22),
        ("temps de travail", 24),
        ("horaire poste", 26),
        ("horaires postes", 26),
        ("repos", 24),
        ("travail de nuit", 18),
        ("cycle", 14),
        ("poste", 10),
        ("duree du travail", 18),
        ("compteur", 10),
        ("pointage", 10),
    ],
    "astreinte": [
        ("accord astreinte", 42),
        ("astreinte", 36),
        ("intervention", 20),
        ("repos apres intervention", 28),
        ("repos compensateur", 24),
        ("declenchement", 14),
        ("trajet", 10),
    ],
    "paie_remuneration": [
        ("paie", 22),
        ("remuneration", 18),
        ("majoration", 26),
        ("bulletin", 18),
        ("heures payees", 18),
        ("heures d intervention", 18),
        ("prime", 14),
        ("salaire", 12),
        ("indemnisation", 18),
    ],
    "conges_payes": [
        ("conges payes", 34),
        ("dixieme", 30),
        ("indemnite de conges", 26),
        ("maintien de salaire", 18),
    ],
    "inaptitude_reclassement": [
        ("inaptitude", 30),
        ("inapte", 26),
        ("reclassement", 30),
        ("avis medical", 20),
        ("medecin du travail", 24),
        ("restriction", 18),
        ("etude de poste", 20),
        ("adaptation", 16),
    ],
    "disciplinaire": [
        ("disciplinaire", 30),
        ("sanction", 22),
        ("convocation", 20),
        ("reglement interieur", 24),
        ("entretien disciplinaire", 26),
    ],
    "droit_syndical": [
        ("droit syndical", 34),
        ("heures de delegation", 34),
        ("credit d heures", 28),
        ("elu cse", 22),
        ("mandat", 20),
        ("delegue syndical", 24),
        ("moyens syndicaux", 22),
    ],
    "cssct_securite": [
        ("cssct", 30),
        ("duerp", 28),
        ("duer", 24),
        ("securite process", 30),
        ("provox", 34),
        ("sncc", 30),
        ("panne", 18),
        ("pieces critiques", 24),
        ("maintenance", 18),
        ("risque", 14),
    ],
}

DOMAIN_SOURCE_PENALTIES: dict[str, list[tuple[str, int]]] = {
    "classification_carriere": [
        ("teletravail", -55),
        ("cet", -38),
        ("forfait jours", -50),
        ("securite process", -30),
    ],
    "temps_travail": [
        ("forfait jours", -55),
        ("cet", -38),
        ("remuneration generale", -25),
    ],
    "astreinte": [
        ("forfait jours", -65),
        ("cet", -50),
        ("teletravail", -35),
    ],
    "paie_remuneration": [
        ("cet", -28),
        ("forfait jours", -32),
    ],
    "cssct_securite": [
        ("cet", -40),
        ("forfait jours", -35),
        ("remuneration", -25),
        ("paie", -25),
    ],
    "droit_syndical": [
        ("cet", -35),
        ("forfait jours", -35),
        ("paie", -25),
        ("remuneration", -25),
    ],
}

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

ASK_REGRESSION_SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "ask-real-classification",
        "query": "Un salarie pense etre mal classe car il exerce plus de responsabilites que sa fiche de poste. Que dois-je verifier ?",
        "expected_domains": ["classification_carriere"],
        "expected_intents": ["analyser_situation_individuelle", "verifier_conformite"],
        "top_source_any": ["classification", "gepp", "gestion de carriere", "ccnic"],
        "forbidden_top_sources": ["teletravail"],
        "working_position_terms": ["classification", "fonctions", "coefficient"],
        "forbidden_text": ["provox", "cssct"],
        "dedupe_lists": True,
    },
    {
        "id": "ask-real-cse-repos-5x8",
        "query": "La direction veut reduire le repos entre deux postes en 5x8. Prepare-moi le point CSE.",
        "expected_domains": ["temps_travail"],
        "expected_intents": ["preparer_cse"],
        "top_source_any": ["5x8", "35 h", "horaires postes"],
        "forbidden_top_sources": ["forfait jours"],
        "working_position_terms": ["reduction", "repos", "projet", "garanties"],
        "max_sources": 6,
    },
    {
        "id": "ask-real-multi-astreinte-repos-paie",
        "query": "Un salarie d'astreinte intervient de nuit, termine son intervention a 4 h et reprend son poste a 8 h. Il pense egalement que ses heures d'intervention et ses majorations ont ete mal payees. Que dois-je verifier et quels documents dois-je demander ?",
        "expected_domains": ["temps_travail", "astreinte", "paie_remuneration"],
        "expected_intents": ["analyser_situation_individuelle", "analyser_paie"],
        "top_source_any": ["astreinte"],
        "source_any": ["repos", "5x8", "temps de travail", "majoration", "paie"],
        "forbidden_top_sources": ["cet", "forfait jours"],
        "issue_groups": ["repos", "astreinte", "paie"],
        "working_position_terms": ["repos", "intervention", "majorations", "bulletins"],
        "warning_terms": ["module paie"],
    },
    {
        "id": "ask-extra-repos-5x8-simple",
        "query": "Combien de repos entre deux postes en 5x8 ?",
        "expected_domains": ["temps_travail"],
        "expected_intents": ["question_simple"],
        "forbidden_engines": ["nexus_bible_bridge"],
        "max_sources": 4,
        "response_depth": "question_simple",
    },
    {
        "id": "ask-extra-inaptitude",
        "query": "Un salarie est declare inapte. Que dois-je verifier ?",
        "expected_domains": ["inaptitude_reclassement"],
        "expected_intents": ["analyser_situation_individuelle"],
        "required_text": ["avis medical", "restrictions", "etude de poste", "reclassement", "tracabilite"],
    },
    {
        "id": "ask-extra-provox-cssct",
        "query": "PROVOX tombe regulierement en panne et les pieces critiques sont difficiles a obtenir.",
        "expected_domains": ["cssct_securite"],
        "expected_intents": ["preparer_cssct"],
        "forbidden_domains": ["paie_remuneration"],
        "required_text": ["provox", "risque", "prevention"],
    },
    {
        "id": "ask-extra-droit-syndical",
        "query": "Combien d'heures de delegation pour les elus ?",
        "expected_domains": ["droit_syndical"],
        "expected_intents": ["question_simple"],
        "forbidden_domains": ["cssct_securite", "paie_remuneration"],
    },
    {
        "id": "ask-extra-conges-dixieme",
        "query": "Je veux verifier le calcul des conges payes au dixieme.",
        "expected_domains": ["conges_payes", "paie_remuneration"],
        "expected_intents": ["analyser_paie", "verifier_conformite"],
        "required_text": ["conges", "dixieme", "bulletins"],
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


def label_for(value: str, labels: dict[str, str]) -> str:
    return labels.get(value, value.replace("_", " "))


def business_domains(route: dict[str, Any]) -> list[str]:
    return [domain for domain in route.get("domains", []) if domain not in BUSINESS_DOMAIN_EXCLUSIONS]


def stem_token(token: str) -> str:
    for suffix in ["ements", "ement", "ations", "ation", "iques", "ique", "elles", "elle", "ites", "ite", "eurs", "euses", "euse", "es", "s"]:
        if len(token) > len(suffix) + 3 and token.endswith(suffix):
            return token[: -len(suffix)]
    return token


def significant_tokens(value: Any) -> set[str]:
    text = normalize(str(value or ""))
    tokens = re.findall(r"[a-z0-9]{3,}", text)
    return {stem_token(token) for token in tokens if token not in STOPWORDS}


def semantic_similarity(left: Any, right: Any) -> float:
    left_tokens = significant_tokens(left)
    right_tokens = significant_tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def semantic_dedupe(values: list[Any], threshold: float = 0.66) -> list[Any]:
    result: list[Any] = []
    token_sets: list[set[str]] = []
    for value in values:
        if value is None:
            continue
        text = compact_text(value).strip() if isinstance(value, dict) else str(value).strip()
        if not text:
            continue
        tokens = significant_tokens(text)
        if not tokens:
            key = normalize(text)
            if any(normalize(compact_text(item) if isinstance(item, dict) else str(item)) == key for item in result):
                continue
            result.append(value)
            token_sets.append(tokens)
            continue
        duplicate = False
        for existing_tokens in token_sets:
            if not existing_tokens:
                continue
            similarity = len(tokens & existing_tokens) / len(tokens | existing_tokens)
            if similarity >= threshold or (tokens <= existing_tokens and len(tokens) >= 2):
                duplicate = True
                break
        if duplicate:
            continue
        result.append(value)
        token_sets.append(tokens)
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
    context_parts = [
        source.get("document"),
        article,
        source.get("location"),
        source.get("excerpt"),
        source.get("ranking_profile"),
        " ".join(str(item) for item in source.get("ranking_reasons", []) if item),
        source.get("role_probable_du_document"),
        source.get("raison_de_pertinence"),
    ]
    return {
        "document": source.get("document"),
        "page": page,
        "article": article,
        "location": source.get("location") or " - ".join(part for part in [f"Page {page}" if page else "", article or ""] if part),
        "score": source.get("score") or source.get("match_score"),
        "status": source.get("source_status") or source.get("confidence_level") or source.get("source_quality_warning"),
        "origin": origin,
        "nature": "regle_locale_a_verifier",
        "_chunk_id": source.get("chunk_id"),
        "_context": " ".join(str(part) for part in context_parts if part),
    }


def source_context(source: dict[str, Any]) -> str:
    return normalize(
        " ".join(
            str(part)
            for part in [
                source.get("document"),
                source.get("article"),
                source.get("location"),
                source.get("status"),
                source.get("_context"),
            ]
            if part
        )
    )


def weighted_term_score(context: str, terms: list[tuple[str, int]]) -> int:
    score = 0
    for term, weight in terms:
        if normalize(term) in context:
            score += weight
    return score


def source_base_score(source: dict[str, Any]) -> float:
    try:
        return float(source.get("score") or 0)
    except (TypeError, ValueError):
        return 0.0


def source_direct_relevance(source: dict[str, Any], domains: list[str]) -> int:
    context = source_context(source)
    return sum(weighted_term_score(context, DOMAIN_SOURCE_BOOSTS.get(domain, [])) for domain in domains)


def contextual_source_score(source: dict[str, Any], route: dict[str, Any]) -> float:
    domains = business_domains(route)
    query = normalize(route.get("query", ""))
    context = source_context(source)
    base = source_base_score(source) * 0.08
    score = base

    query_hits = [token for token in significant_tokens(query) if token in significant_tokens(context)]
    score += min(18, len(query_hits) * 3)

    direct = 0
    for domain in domains:
        domain_direct = weighted_term_score(context, DOMAIN_SOURCE_BOOSTS.get(domain, []))
        direct += domain_direct
        score += domain_direct

        for term, penalty in DOMAIN_SOURCE_PENALTIES.get(domain, []):
            normalized_term = normalize(term)
            if normalized_term in query:
                continue
            if normalized_term in context and domain_direct < 18:
                score += penalty

    document = normalize(str(source.get("document") or ""))
    if "astreinte" in domains and "accord astreinte" in document:
        score += 45
    if "temps_travail" in domains and ("5x8" in document or "35 h" in document or "35h" in document):
        score += 38
    if "temps_travail" in domains and "horaires postes" in document:
        score += 30
    if "classification_carriere" in domains and ("gepp" in document or "gestion de carriere" in document):
        score += 36
    if "classification_carriere" in domains and "ccnic" in document:
        score += 18
    if "paie_remuneration" in domains and "repos compensateur" in document:
        score += 24
    if "conges_payes" in domains and ("conges" in document or "dixieme" in context):
        score += 28
    if "cssct_securite" in domains and any(term in document for term in ["provox", "sncc", "securite", "maintenance"]):
        score += 28
    if "droit_syndical" in domains and any(term in document for term in ["droit syndical", "cse", "rp", "dialogue social"]):
        score += 28

    if source.get("origin") == "nexus_bible_bridge" and any(intent in route.get("intents", []) for intent in ["preparer_cse", "analyser_situation_individuelle", "analyser_paie"]):
        score += 6
    if source.get("origin") == "bible_accords" and route.get("engines") == ["bible_accords"]:
        score += 4

    source["_router_score"] = round(score, 3)
    source["_direct_relevance"] = direct
    return score


def clean_source(source: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in source.items() if not key.startswith("_")}


def select_final_sources(sources: list[dict[str, Any]], route: dict[str, Any], source_limit: int) -> list[dict[str, Any]]:
    limit = max(1, min(source_limit, MAX_SOURCE_LIMIT))
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source in sources:
        key = source_key(source)
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        unique.append(source)

    ranked = sorted(unique, key=lambda item: contextual_source_score(item, route), reverse=True)
    if not ranked:
        return []

    selected: list[dict[str, Any]] = []
    skipped_noise: list[dict[str, Any]] = []
    by_document: dict[str, int] = {}
    top_score = float(ranked[0].get("_router_score") or 0)
    for source in ranked:
        if len(selected) >= 4 and is_contextual_noise_source(source, route):
            skipped_noise.append(source)
            continue
        document = normalize(str(source.get("document") or "document local"))
        current = by_document.get(document, 0)
        cap = 3 if float(source.get("_router_score") or 0) >= top_score - 16 else 2
        if current >= cap:
            continue
        selected.append(source)
        by_document[document] = current + 1
        if len(selected) >= limit:
            break

    minimum_sources = min(4, limit)
    if len(selected) < minimum_sources:
        selected_keys = {source_key(source) for source in selected}
        for source in ranked + skipped_noise:
            key = source_key(source)
            if key in selected_keys:
                continue
            selected.append(source)
            selected_keys.add(key)
            if len(selected) >= minimum_sources:
                break

    return [clean_source(source) for source in selected[:limit]]


def is_contextual_noise_source(source: dict[str, Any], route: dict[str, Any]) -> bool:
    query = normalize(route.get("query", ""))
    document = normalize(str(source.get("document") or ""))
    direct = int(source.get("_direct_relevance") or 0)
    for domain in business_domains(route):
        for term, _penalty in DOMAIN_SOURCE_PENALTIES.get(domain, []):
            normalized_term = normalize(term)
            if normalized_term in query:
                continue
            if normalized_term in document and direct < 130:
                return True
    return False


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
            "reason": "module paie dedie non connecte en V1.1",
        },
        "veille_juridique": {
            "available": False,
            "detected": False,
            "reason": "connecteur de veille non connecte en V1.1",
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
        warnings.append("Veille juridique non connectee en V1.1 : verifier les sources externes a jour manuellement.")

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
    secondary_domains = [domain for domain in business_domains({"domains": domains}) if domain != main_domain]
    route = {
        "query": query,
        "router_version": ROUTER_VERSION,
        "domains": domains,
        "main_domain": main_domain,
        "primary_domain": main_domain,
        "secondary_domains": secondary_domains,
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
    main = label_for(route["main_domain"], DOMAIN_LABELS)
    secondary = [label_for(domain, DOMAIN_LABELS) for domain in route.get("secondary_domains", []) if domain != "cse"]
    intents = [label_for(intent, INTENT_LABELS) for intent in route["intents"][:4]]
    sentence = f"Demande portant principalement sur {main}"
    if secondary:
        sentence += ", avec enjeux associes de " + ", ".join(secondary)
    if intents:
        sentence += ". L'analyse vise " + ", ".join(intents) + "."
    else:
        sentence += "."
    return sentence


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
    if "temps_travail" in domains and "preparer_cse" in route["intents"]:
        documents.extend(
            [
                "projet ecrit complet",
                "base juridique ou conventionnelle invoquee",
                "comparatif avant/apres des horaires et repos",
                "planning actuel et planning projete",
                "evaluation des impacts fatigue et sante",
                "garanties de prevention, compensation et suivi",
            ]
        )
    if "astreinte" in domains:
        documents.extend(
            [
                "accord astreinte applicable",
                "releve d'intervention avec heure de debut et de fin",
                "declenchement et motif de l'intervention",
                "temps de trajet si applicable",
                "regle de repos apres intervention",
            ]
        )
    if "paie_remuneration" in domains:
        documents.extend(
            [
                "bulletins de paie de la periode controlee",
                "detail des majorations appliquees",
                "historique des paiements et recuperations",
            ]
        )
    if "conges_payes" in domains:
        documents.extend(
            [
                "decompte conges payes",
                "base de calcul du dixieme",
                "comparaison maintien de salaire / dixieme",
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
    if "temps_travail" in domains and "preparer_cse" in route["intents"]:
        questions.extend(
            [
                "Quelle base juridique ou conventionnelle autoriserait la reduction du repos ?",
                "Quelle comparaison avant/apres des horaires et repos est communiquee au CSE ?",
                "Quels impacts fatigue, travail de nuit et securite ont ete evalues ?",
                "Quelles garanties de prevention, compensation et suivi sont proposees ?",
            ]
        )
    if "astreinte" in domains:
        questions.extend(
            [
                "Quelle regle d'astreinte s'applique a l'intervention concernee ?",
                "A quelle heure l'intervention a-t-elle reellement commence et pris fin ?",
                "Le repos apres intervention a-t-il ete reporte, compense ou derogatoire ?",
            ]
        )
    if "paie_remuneration" in domains:
        questions.extend(
            [
                "Quelles heures d'intervention ont ete payees, majorees ou recuperees ?",
                "Quelle regle de majoration nuit, dimanche ou jour ferie a ete appliquee ?",
                "Comment le bulletin se rapproche-t-il des compteurs et releves horaires ?",
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


def default_findings(route: dict[str, Any]) -> list[str]:
    domains = set(route["domains"])
    intents = set(route["intents"])
    findings: list[str] = []

    if {"temps_travail", "astreinte", "paie_remuneration"}.issubset(domains):
        findings.extend(
            [
                "Verifier le repos entre la fin reelle de l'intervention et la reprise du poste.",
                "Qualifier le temps d'intervention d'astreinte, y compris le trajet si applicable.",
                "Rapprocher heures d'intervention, compteurs, majorations et bulletins de paie.",
            ]
        )
    elif "classification_carriere" in domains:
        findings.extend(
            [
                "Comparer le coefficient et l'emploi retenus avec les fonctions reellement exercees.",
                "Objectiver le niveau d'autonomie, de responsabilite et de technicite.",
                "Verifier les criteres conventionnels et les comparaisons internes disponibles.",
            ]
        )
    elif "inaptitude_reclassement" in domains:
        findings.extend(
            [
                "Verifier l'avis medical, les restrictions et les preconisations du medecin du travail.",
                "Controler l'etude de poste, les adaptations envisagees et les postes compatibles.",
                "Reconstituer la tracabilite des recherches de reclassement et des echanges avec le salarie.",
            ]
        )
    elif "disciplinaire" in domains:
        findings.extend(
            [
                "Verifier les faits reproches, les preuves, les dates et les delais de procedure.",
                "Controler les droits de defense et les garanties prevues par le reglement interieur.",
            ]
        )
    elif "droit_syndical" in domains:
        findings.extend(
            [
                "Identifier le texte local applicable aux mandats, heures de delegation ou moyens syndicaux.",
                "Verifier le perimetre des beneficiaires et les conditions pratiques d'utilisation.",
            ]
        )
    elif "cssct_securite" in domains:
        findings.extend(
            [
                "Identifier le risque, les incidents ou pannes traces et les mesures de prevention existantes.",
                "Verifier DUERP, plan d'action, maintenance, pieces critiques et suivi CSSCT.",
            ]
        )
    elif "conges_payes" in domains:
        findings.extend(
            [
                "Comparer le calcul au dixieme avec le maintien de salaire sur la periode utile.",
                "Verifier les elements de remuneration inclus ou exclus de l'assiette.",
            ]
        )
    elif "temps_travail" in domains and "preparer_cse" in intents:
        findings.extend(
            [
                "Verifier la regle de repos applicable et les derogations eventuelles.",
                "Comparer la situation actuelle et le projet poste par poste ou cycle par cycle.",
                "Evaluer les impacts fatigue, travail de nuit, securite et compensations.",
            ]
        )
    elif "temps_travail" in domains:
        findings.extend(
            [
                "Identifier la regle locale de temps de travail applicable.",
                "Verifier les horaires reels, les repos et les compteurs sur la periode concernee.",
            ]
        )
    elif "paie_remuneration" in domains:
        findings.extend(
            [
                "Rapprocher la regle de paie applicable avec les bulletins et compteurs.",
                "Identifier les ecarts de taux, majorations, primes ou recuperations.",
            ]
        )

    return findings


def build_working_position(route: dict[str, Any], findings: list[str], engine_results: list[dict[str, Any]] | None = None) -> str:
    domains = set(route["domains"])
    intents = set(route["intents"])
    if {"temps_travail", "astreinte", "paie_remuneration"}.issubset(domains):
        return (
            "Verifier separement le respect du repos apres intervention, la comptabilisation du temps "
            "d'intervention et l'application des majorations, puis rapprocher l'accord d'astreinte, "
            "les horaires reels, les compteurs et les bulletins de paie."
        )
    if "classification_carriere" in domains:
        return (
            "Objectiver l'ecart entre la classification actuelle et les fonctions reellement exercees "
            "avant de demander un reexamen motive du coefficient."
        )
    if "temps_travail" in domains and "preparer_cse" in intents:
        return (
            "Ne pas accepter une reduction du repos sans projet ecrit, base juridique precise, "
            "comparaison avant/apres, evaluation des impacts sur la fatigue et garanties de prevention "
            "et de compensation."
        )
    if "inaptitude_reclassement" in domains:
        return (
            "Controler la realite et la tracabilite des recherches de reclassement, les adaptations "
            "etudiees et leur compatibilite avec l'avis medical avant toute conclusion."
        )
    if "disciplinaire" in domains:
        return (
            "Verifier les faits, les preuves, les delais et les droits de defense avant d'apprecier "
            "la proportionnalite d'une eventuelle sanction."
        )
    if "droit_syndical" in domains:
        return (
            "Identifier le texte local applicable aux mandats ou moyens syndicaux, puis verifier son "
            "champ, ses beneficiaires et ses modalites pratiques avant de contester ou revendiquer."
        )
    if "cssct_securite" in domains:
        return (
            "Obtenir une evaluation documentee du risque, les mesures de prevention et un plan "
            "d'action suivi avant de considerer le risque comme maitrise."
        )
    if "conges_payes" in domains:
        return (
            "Rapprocher l'assiette, la methode du dixieme, le maintien de salaire et les bulletins afin "
            "d'identifier et chiffrer l'eventuel ecart de conges payes."
        )
    if "paie_remuneration" in domains:
        return (
            "Rapprocher les horaires ou elements variables, les compteurs, les regles de paie et les "
            "bulletins afin d'identifier et chiffrer les ecarts."
        )
    if "question_simple" in intents:
        return "Identifier la regle locale applicable dans les sources citees avant de formuler une reponse prudente."
    if findings:
        return "Utiliser les sources locales comme base de travail, sans conclure avant verification humaine."
    return "Demande a approfondir avec les sources locales et les elements factuels."


def position_for(route: dict[str, Any], findings: list[str]) -> str:
    return build_working_position(route, findings, None)


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


def is_generic_prudence(value: str) -> bool:
    normalized = normalize(value)
    if any(marker in normalized for marker in GENERIC_PRUDENCE_MARKERS):
        return True
    if "avenant" in normalized and ("texte plus recent" in normalized or "existe" in normalized):
        return True
    if "document" in normalized and "applicable" in normalized:
        return True
    if "convention collective" in normalized and ("jurisprudence" in normalized or "loi" in normalized):
        return True
    if "relire" in normalized and "sources citees" in normalized:
        return True
    return False


def split_prudence_findings(findings: list[str]) -> tuple[list[str], list[str]]:
    business: list[str] = []
    prudence: list[str] = []
    for item in findings:
        if is_generic_prudence(item):
            prudence.append(item)
        else:
            business.append(item)
    return business, prudence


def response_depth(route: dict[str, Any]) -> str:
    domains = set(route.get("domains", []))
    intents = set(route.get("intents", []))
    business = [domain for domain in business_domains(route) if domain != "cse"]
    if {"temps_travail", "astreinte", "paie_remuneration"}.issubset(domains) or len(business) >= 3:
        return "multi_domain"
    if "preparer_cse" in intents:
        return "preparation_cse"
    if "question_simple" in intents and route.get("engines") == ["bible_accords"]:
        return "question_simple"
    if "analyser_situation_individuelle" in intents:
        return "situation_individuelle"
    if "preparer_cssct" in intents:
        return "preparation_cssct"
    return "standard"


def answer_limits(route: dict[str, Any], source_limit: int) -> dict[str, int]:
    depth = response_depth(route)
    sources = max(1, min(source_limit, MAX_SOURCE_LIMIT))
    if depth == "question_simple":
        sources = min(sources, 4)
        return {"sources": sources, "findings": 5, "documents": 5, "questions": 5}
    if depth == "preparation_cse":
        return {"sources": sources, "findings": 8, "documents": 10, "questions": 8}
    if depth == "multi_domain":
        return {"sources": sources, "findings": 12, "documents": 14, "questions": 12}
    if depth == "situation_individuelle":
        return {"sources": sources, "findings": 8, "documents": 10, "questions": 8}
    return {"sources": sources, "findings": 8, "documents": 10, "questions": 8}


ISSUE_GROUP_TEMPLATES: dict[str, dict[str, Any]] = {
    "repos": {
        "name": "Repos et reprise du poste",
        "keywords": ["repos", "reprise", "reprend", "horaire", "planning", "badgeage", "pointage", "fatigue"],
        "findings": [
            "Verifier l'heure reelle de fin d'intervention et l'heure de reprise du poste.",
            "Identifier la regle de repos applicable et toute derogation invoquee.",
            "Verifier la compensation ou le repos associe si le repos normal n'a pas ete respecte.",
        ],
        "documents": [
            "planning de travail",
            "releves de pointage ou badgeage",
            "historique des heures et repos",
        ],
        "questions": [
            "Quelle heure de fin d'intervention et quelle heure de reprise sont retenues ?",
            "Quelle regle autorise ou interdit cette reprise ?",
            "Quelle compensation ou quel repos a ete accorde ?",
        ],
    },
    "astreinte": {
        "name": "Astreinte et intervention",
        "keywords": ["astreinte", "intervention", "declenchement", "trajet", "duree", "accord astreinte"],
        "findings": [
            "Verifier le declenchement, la duree reelle et le regime d'astreinte applicable.",
            "Identifier si le trajet ou les temps annexes doivent etre comptabilises.",
        ],
        "documents": [
            "accord astreinte applicable",
            "releve d'intervention",
            "trace du declenchement et de la duree",
        ],
        "questions": [
            "Qui a declenche l'intervention et pour quel motif ?",
            "Quelle duree reelle, trajet compris si applicable, est retenue ?",
            "Quel regime l'accord d'astreinte prevoit-il ?",
        ],
    },
    "paie": {
        "name": "Paie et majorations",
        "keywords": ["paie", "paye", "payees", "majoration", "bulletin", "prime", "remuneration", "recuperation"],
        "findings": [
            "Verifier les heures payees, recuperees ou majorees sur la periode.",
            "Controler les majorations nuit, dimanche ou jour ferie si elles sont concernees.",
            "Rapprocher bulletin, compteur et regle locale applicable.",
        ],
        "documents": [
            "bulletins de paie",
            "detail des compteurs",
            "regles de majoration",
            "historique des paiements et recuperations",
        ],
        "questions": [
            "Quelles heures d'intervention ont ete payees ou recuperees ?",
            "Quelle majoration a ete appliquee et sur quelle base ?",
            "Le bulletin correspond-il au compteur et au releve d'intervention ?",
        ],
    },
    "classification": {
        "name": "Classification et fonctions exercees",
        "keywords": ["classification", "coefficient", "fiche de poste", "fonction", "responsabilite", "autonomie"],
        "findings": [
            "Comparer la classification actuelle aux fonctions reellement exercees.",
            "Objectiver responsabilites, autonomie, technicite et comparaisons internes.",
        ],
        "documents": ["fiche de poste", "descriptif des fonctions reelles", "criteres conventionnels"],
        "questions": ["Quels ecarts concrets existent entre fiche de poste et travail reel ?", "Quel coefficient est justifie par les criteres conventionnels ?"],
    },
    "cssct": {
        "name": "Risque et prevention",
        "keywords": ["cssct", "duerp", "risque", "securite", "panne", "maintenance", "provox"],
        "findings": ["Qualifier le risque et les mesures de prevention existantes.", "Verifier le suivi DUERP/CSSCT et le plan d'action."],
        "documents": ["DUERP/DUER", "registre securite", "plan d'action ou de maintenance"],
        "questions": ["Quels incidents sont traces ?", "Quelles mesures immediates protegent les salaries ?"],
    },
}


def select_items_for_group(values: list[str], keywords: list[str], defaults: list[str], limit: int) -> list[str]:
    normalized_keywords = [normalize(keyword) for keyword in keywords]
    selected = [
        value
        for value in values
        if any(keyword and keyword in normalize(value) for keyword in normalized_keywords)
    ]
    return semantic_dedupe(selected + defaults)[:limit]


def build_issue_groups(route: dict[str, Any], findings: list[str], documents: list[str], questions: list[str]) -> list[dict[str, Any]]:
    domains = set(route.get("domains", []))
    ordered_group_ids: list[str] = []
    if {"temps_travail", "astreinte", "paie_remuneration"}.issubset(domains):
        ordered_group_ids = ["repos", "astreinte", "paie"]
    elif response_depth(route) == "multi_domain":
        if "classification_carriere" in domains:
            ordered_group_ids.append("classification")
        if "temps_travail" in domains:
            ordered_group_ids.append("repos")
        if "astreinte" in domains:
            ordered_group_ids.append("astreinte")
        if "paie_remuneration" in domains or "conges_payes" in domains:
            ordered_group_ids.append("paie")
        if "cssct_securite" in domains:
            ordered_group_ids.append("cssct")

    groups: list[dict[str, Any]] = []
    for group_id in dedupe(ordered_group_ids):
        template = ISSUE_GROUP_TEMPLATES[group_id]
        groups.append(
            {
                "id": group_id,
                "name": template["name"],
                "findings": select_items_for_group(findings, template["keywords"], template["findings"], 5),
                "documents": select_items_for_group(documents, template["keywords"], template["documents"], 5),
                "questions": select_items_for_group(questions, template["keywords"], template["questions"], 4),
            }
        )
    return groups


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


def finalize_answer(answer: dict[str, Any], source_limit: int = DEFAULT_SOURCE_LIMIT) -> dict[str, Any]:
    route = answer["route"]
    limits = answer_limits(route, source_limit)

    answer["sources"] = select_final_sources(answer["sources"], route, limits["sources"])

    business_findings, prudence_findings = split_prudence_findings([item for item in answer["findings"] if item])
    answer["findings"] = semantic_dedupe(business_findings + default_findings(route))[: limits["findings"]]
    answer["documents_to_request"] = semantic_dedupe(answer["documents_to_request"] + default_documents(route))[: limits["documents"]]
    answer["questions_to_ask"] = semantic_dedupe(answer["questions_to_ask"] + default_questions(route))[: limits["questions"]]
    answer["issue_groups"] = build_issue_groups(route, answer["findings"], answer["documents_to_request"], answer["questions_to_ask"])
    module_warnings = [warning for warning in answer["warnings"] if not is_generic_prudence(warning)]
    answer["warnings"] = semantic_dedupe(module_warnings + PRUDENCE_POINTS)
    answer["working_position"] = build_working_position(route, answer["findings"], None)
    if not answer["next_action"]:
        answer["next_action"] = next_action_for(route)
    answer["response_depth"] = response_depth(route)
    return answer


def ask(query: str, limit: int, source_limit: int = DEFAULT_SOURCE_LIMIT) -> dict[str, Any]:
    route = route_query(query)
    answer: dict[str, Any] = {
        "query": query,
        "understanding": understanding_for(route),
        "route": route,
        "execution_plan": route["execution_plan"],
        "sources": [],
        "issue_groups": [],
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

    return finalize_answer(answer, source_limit)


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

    def grouped_lines(section: str, key: str, fallback: list[str]) -> list[str]:
        if not answer.get("issue_groups"):
            return ["", section, *list_or_dash(fallback)]
        lines = ["", section]
        for group in answer["issue_groups"]:
            values = group.get(key, [])
            if not values:
                continue
            lines.append(group["name"])
            lines.extend(f"- {value}" for value in values)
        if len(lines) == 2:
            lines.extend(list_or_dash(fallback))
        return lines

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
    lines.extend(grouped_lines("Ce qu'il faut verifier :", "findings", answer["findings"]))
    lines.extend(grouped_lines("Documents a recuperer :", "documents", answer["documents_to_request"]))
    lines.extend(grouped_lines("Questions a poser :", "questions", answer["questions_to_ask"]))
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
            "Points de prudence :",
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
        "router_version": ROUTER_VERSION,
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
        "local_index_protected": local_index_ignored,
        "connected_modules": [name for name, item in status.items() if item.get("available")],
        "detected_unavailable_modules": [name for name, item in status.items() if item.get("detected") and not item.get("available")],
        "errors": errors,
        "security_notice": "local-index/ et les fichiers *.private.* doivent rester hors Git.",
    }


def format_diagnose_text(report: dict[str, Any]) -> str:
    lines = [
        "DIAGNOSTIC ASSISTANT DS ROUTER",
        f"Version routeur : V{report['router_version']}",
        f"Bible Accords disponible : {'oui' if report['bible_accords_available'] else 'non'}",
        f"Chunks indexes : {report['chunks']}",
        f"Pont nexus_bible_bridge.py disponible : {'oui' if report['nexus_bible_bridge_available'] else 'non'}",
        f"Document Intelligence Center : {report['document_intelligence']['reason']}",
        f"Cycle CSE : {report['cycle_cse']['reason']}",
        f"Module paie : {report['paie_control']['reason']}",
        f"Veille juridique : {report['veille_juridique']['reason']}",
        f"Corpus local configure : {'oui' if report['corpus_local_configured'] else 'non'}",
        f"local-index/ ignore par Git : {'oui' if report['local_index_ignored'] else 'non'}",
        "Modules connectes : " + ", ".join(report["connected_modules"]),
        "Modules detectes non executables : " + (", ".join(report["detected_unavailable_modules"]) or "aucun"),
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


def answer_validation_text(answer: dict[str, Any]) -> str:
    return normalize(
        json.dumps(
            {
                "route": answer.get("route", {}),
                "sources": answer.get("sources", []),
                "issue_groups": answer.get("issue_groups", []),
                "findings": answer.get("findings", []),
                "documents_to_request": answer.get("documents_to_request", []),
                "questions_to_ask": answer.get("questions_to_ask", []),
                "working_position": answer.get("working_position", ""),
                "warnings": answer.get("warnings", []),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def source_text(answer: dict[str, Any], first_n: int | None = None) -> str:
    sources = answer.get("sources", [])
    if first_n is not None:
        sources = sources[:first_n]
    return normalize(json.dumps(sources, ensure_ascii=False, sort_keys=True))


def has_semantic_duplicates(values: list[str]) -> bool:
    token_sets: list[set[str]] = []
    for value in values:
        tokens = significant_tokens(value)
        if not tokens:
            continue
        for existing in token_sets:
            if existing and len(tokens & existing) / len(tokens | existing) >= 0.66:
                return True
        token_sets.append(tokens)
    return False


def validate_answer_scenario(scenario: dict[str, Any], answer: dict[str, Any]) -> list[dict[str, Any]]:
    route = answer["route"]
    domains = set(route["domains"])
    intents = set(route["intents"])
    engines = set(route["engines"])
    text = answer_validation_text(answer)
    top_sources = source_text(answer, 3)
    all_sources = source_text(answer)
    checks: list[dict[str, Any]] = []

    for domain in scenario.get("expected_domains", []):
        checks.append({"name": f"domaine_{domain}", "ok": domain in domains, "detail": domain})
    for domain in scenario.get("forbidden_domains", []):
        checks.append({"name": f"absence_domaine_{domain}", "ok": domain not in domains, "detail": domain})
    for intent in scenario.get("expected_intents", []):
        checks.append({"name": f"intention_{intent}", "ok": intent in intents, "detail": intent})
    for engine in scenario.get("forbidden_engines", []):
        checks.append({"name": f"absence_moteur_{engine}", "ok": engine not in engines, "detail": engine})

    if scenario.get("top_source_any"):
        terms = [normalize(term) for term in scenario["top_source_any"]]
        checks.append(
            {
                "name": "source_prioritaire",
                "ok": any(term in top_sources for term in terms),
                "detail": ", ".join(scenario["top_source_any"]),
            }
        )
    if scenario.get("source_any"):
        terms = [normalize(term) for term in scenario["source_any"]]
        checks.append(
            {
                "name": "source_pertinente",
                "ok": any(term in all_sources for term in terms),
                "detail": ", ".join(scenario["source_any"]),
            }
        )
    for forbidden in scenario.get("forbidden_top_sources", []):
        checks.append(
            {
                "name": f"source_bruitee_absente_{normalize(forbidden).replace(' ', '_')}",
                "ok": normalize(forbidden) not in top_sources,
                "detail": forbidden,
            }
        )
    for term in scenario.get("working_position_terms", []):
        checks.append(
            {
                "name": f"position_{normalize(term).replace(' ', '_')}",
                "ok": normalize(term) in normalize(answer.get("working_position", "")),
                "detail": answer.get("working_position", ""),
            }
        )
    for term in scenario.get("required_text", []):
        checks.append({"name": f"contenu_{normalize(term).replace(' ', '_')}", "ok": normalize(term) in text, "detail": term})
    for term in scenario.get("forbidden_text", []):
        checks.append({"name": f"absence_contenu_{normalize(term).replace(' ', '_')}", "ok": normalize(term) not in text, "detail": term})
    for term in scenario.get("warning_terms", []):
        warnings = normalize(" ".join(answer.get("warnings", [])))
        checks.append({"name": f"avertissement_{normalize(term).replace(' ', '_')}", "ok": normalize(term) in warnings, "detail": term})
    for group_id in scenario.get("issue_groups", []):
        group_ids = {group.get("id") for group in answer.get("issue_groups", [])}
        checks.append({"name": f"groupe_{group_id}", "ok": group_id in group_ids, "detail": group_id})
    if scenario.get("max_sources"):
        checks.append({"name": "source_limit", "ok": len(answer.get("sources", [])) <= scenario["max_sources"], "detail": len(answer.get("sources", []))})
    if scenario.get("response_depth"):
        checks.append({"name": "profondeur_reponse", "ok": answer.get("response_depth") == scenario["response_depth"], "detail": answer.get("response_depth")})
    if scenario.get("dedupe_lists"):
        checks.append({"name": "documents_dedoublonnes", "ok": not has_semantic_duplicates(answer.get("documents_to_request", [])), "detail": "documents"})
        checks.append({"name": "questions_dedoublonnees", "ok": not has_semantic_duplicates(answer.get("questions_to_ask", [])), "detail": "questions"})
    checks.append(
        {
            "name": "working_position_phrase_complete",
            "ok": len(significant_tokens(answer.get("working_position", ""))) >= 6,
            "detail": answer.get("working_position", ""),
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
    ask_rows = []
    for scenario in ASK_REGRESSION_SCENARIOS:
        answer = ask(scenario["query"], scenario.get("limit", 6), scenario.get("source_limit", DEFAULT_SOURCE_LIMIT))
        checks = validate_answer_scenario(scenario, answer)
        ok = all(check["ok"] for check in checks)
        ask_rows.append(
            {
                "id": scenario["id"],
                "query": scenario["query"],
                "main_domain": answer["route"]["main_domain"],
                "domains": answer["route"]["domains"],
                "intents": answer["route"]["intents"],
                "engines": answer["route"]["engines"],
                "response_depth": answer.get("response_depth"),
                "source_count": len(answer.get("sources", [])),
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
        "ask_regression_count": len(ask_rows),
        "ok": all(row["ok"] for row in rows) and all(row["ok"] for row in ask_rows) and simple_count >= 20 and multi_count >= 5,
        "rows": rows,
        "ask_rows": ask_rows,
    }


def format_scenarios_text(report: dict[str, Any]) -> str:
    lines = [
        "SCENARIOS ASSISTANT DS ROUTER",
        f"Scenarios : {report['scenario_count']} dont {report['simple_scenarios']} simples et {report['multi_domain_scenarios']} multi-domaines",
        f"Scenarios ask V1.1 : {report['ask_regression_count']}",
        f"Statut global : {'OK' if report['ok'] else 'ERREUR'}",
        "",
    ]
    for row in report["rows"]:
        status = "OK" if row["ok"] else "ERREUR"
        failed = [check["name"] for check in row["checks"] if not check["ok"]]
        suffix = "" if not failed else " | echecs: " + ", ".join(failed)
        lines.append(f"- {row['id']} | {status} | {row['main_domain']} | {', '.join(row['engines'])}{suffix}")
    if report.get("ask_rows"):
        lines.extend(["", "Scenarios ask V1.1 :"])
        for row in report["ask_rows"]:
            status = "OK" if row["ok"] else "ERREUR"
            failed = [check["name"] for check in row["checks"] if not check["ok"]]
            suffix = "" if not failed else " | echecs: " + ", ".join(failed)
            lines.append(f"- {row['id']} | {status} | {row['main_domain']} | sources {row['source_count']} | {row['response_depth']}{suffix}")
    return "\n".join(lines)


def emit(data: dict[str, Any], fmt: str, text_formatter) -> None:
    if fmt == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(text_formatter(data))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CFDT Nexus - Assistant DS router V1.1")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ask = sub.add_parser("ask")
    p_ask.add_argument("--query", required=True)
    p_ask.add_argument("--limit", type=int, default=6)
    p_ask.add_argument("--source-limit", type=int, default=DEFAULT_SOURCE_LIMIT)
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
        emit(ask(args.query, args.limit, args.source_limit), args.format, format_answer_text)
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
