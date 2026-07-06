#!/usr/bin/env python
"""
Bible Accords Sarralbe V1.

Local-only pipeline for private agreements:
- scan
- extract
- index
- search
- test
- missing

No document is copied into Git. Outputs are written under local-index/agreements/.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
LOCAL_ROOT = ROOT / "local-index" / "agreements"
STATE_DIR = LOCAL_ROOT / "state"
TEXT_DIR = LOCAL_ROOT / "text"
INDEX_DIR = LOCAL_ROOT / "index"
REPORT_DIR = LOCAL_ROOT / "reports"
SEARCH_DIR = LOCAL_ROOT / "search"
TEST_DIR = LOCAL_ROOT / "tests"
OCR_DIR = LOCAL_ROOT / "ocr"
SOURCE_CONFIG_PATH = STATE_DIR / "source-config.private.json"

MIN_TEXT_CHARS = 800
MIN_PAGE_TEXT_CHARS = 20
MAX_CHUNK_CHARS = 2400
CHUNK_OVERLAP_CHARS = 240
OCR_LOW_CONFIDENCE_THRESHOLD = 70.0
OCR_LANG_DEFAULT = "fra+eng"

DOCUMENT_TYPES = [
    ("avenant", [r"\bavenant\b", r"\bmodification\b"]),
    ("règlement intérieur", [r"reglement interieur", r"règlement intérieur"]),
    ("protocole", [r"\bprotocole\b", r"\bpap\b", r"vote electronique", r"vote électronique"]),
    ("décision unilatérale", [r"decision unilaterale", r"décision unilatérale", r"\bdue\b"]),
    ("accord entreprise", [r"\baccord\b"]),
    ("note collective", [r"\bnote\b", r"information collective"]),
]

TOPIC_RULES = [
    ("rémunération", [r"remuneration", r"rémunération", r"salaire", r"salaires"]),
    ("primes", [r"\bprime\b", r"\bprimes\b", r"\bppv\b", r"partage de la valeur"]),
    ("intéressement", [r"interessement", r"intéressement"]),
    ("participation", [r"participation"]),
    ("épargne salariale", [r"epargne", r"épargne", r"\bpereco\b", r"\bpee\b", r"\bcet\b"]),
    ("heures supplémentaires", [r"heures supplementaires", r"heures supplémentaires", r"compteur d heures", r"compteur d'heures", r"compteurs", r"pointage", r"badgeage", r"temps de travail effectif", r"heures effectuees", r"heures effectuées", r"heures payees", r"heures payées", r"heures recuperees", r"heures récupérées", r"repos compensateur", r"contingent", r"modulation", r"annualisation"]),
    ("temps de travail", [r"temps de travail", r"duree du travail", r"durée du travail", r"horaire", r"horaires"]),
    ("5x8", [r"\b5x8\b", r"equipes postees", r"équipes postées"]),
    ("travail posté", [r"travail poste", r"travail posté", r"\bposte\b", r"\bpostes\b"]),
    ("travail de nuit", [r"travail de nuit", r"\bnuit\b"]),
    ("repos", [r"\brepos\b", r"repos quotidien", r"repos hebdomadaire"]),
    ("congés payés", [r"conges payes", r"congés payés", r"conge paye", r"congé payé", r"indemnite de conges", r"indemnité de congés", r"regle du dixieme", r"règle du dixième", r"\bdixieme\b", r"\bdixième\b", r"maintien de salaire", r"periode de reference", r"période de référence", r"periode d'acquisition", r"période d'acquisition", r"indemnite compensatrice de conges", r"indemnité compensatrice de congés"]),
    ("congés", [r"conges", r"congés", r"conge", r"congé"]),
    ("astreinte", [r"astreinte"]),
    ("classification", [r"classification", r"coefficient", r"classement", r"\bniveau\b", r"echelon", r"échelon", r"fiche de poste", r"fonctions exercees", r"fonctions exercées", r"responsabilites", r"responsabilités", r"autonomie", r"technicite", r"technicité", r"evolution de poste", r"évolution de poste", r"pesee de poste", r"pesée de poste"]),
    ("emploi", [r"\bemploi\b", r"emplois", r"effectif", r"effectifs", r"\bposte\b", r"\bpostes\b", r"carriere", r"carrière", r"polyvalence"]),
    ("inaptitude reclassement", [r"inaptitude", r"reclassement", r"medecin du travail", r"médecin du travail", r"aptitude", r"restrictions medicales", r"restrictions médicales", r"amenagement de poste", r"aménagement de poste", r"adaptation de poste", r"poste compatible", r"recherche de reclassement", r"impossibilite de reclassement", r"impossibilité de reclassement", r"licenciement pour inaptitude", r"sante au travail", r"santé au travail"]),
    ("compétences", [r"competence", r"compétence", r"\bgepp\b", r"\bgpec\b"]),
    ("formation", [r"formation"]),
    ("égalité professionnelle", [r"egalite professionnelle", r"égalité professionnelle"]),
    ("télétravail", [r"teletravail", r"télétravail"]),
    ("santé", [r"sante", r"santé", r"maladie", r"medical", r"médical"]),
    ("sécurité", [r"securite", r"sécurité", r"prevention", r"prévention", r"risque"]),
    ("securite process", [r"securite process", r"risque industriel", r"risques industriels", r"incident", r"presque accident", r"analyseur", r"analyseurs", r"\bprovox\b", r"\bsncc\b"]),
    ("maintenance", [r"maintenance", r"piece de rechange", r"pieces de rechange", r"stock pieces", r"pieces critiques", r"climatisation"]),
    ("continuite exploitation", [r"continuite d exploitation", r"continuite exploitation", r"contingence", r"plan de contingence", r"\bpanne\b", r"scenario de panne", r"defaillance"]),
    ("RPS", [r"\brps\b", r"risques psychosociaux", r"charge mentale", r"\bstress\b"]),
    ("conditions de travail", [r"conditions de travail", r"rps", r"psychosocial"]),
    ("fin de carrière", [r"fin de carriere", r"fin de carrière", r"retraite"]),
    ("handicap", [r"handicap"]),
    ("droit syndical", [r"droit syndical", r"delegue syndical", r"délégué syndical", r"section syndicale"]),
    ("CSE", [r"\bcse\b", r"comite social", r"comité social"]),
    ("dialogue social", [r"dialogue social", r"negociation", r"négociation"]),
    ("disciplinaire", [r"disciplinaire", r"sanction", r"mise a pied", r"mise à pied"]),
]

BUSINESS_TESTS = [
    "repos entre deux postes",
    "astreinte",
    "prime de nuit",
    "majoration dimanche",
    "durée du travail",
    "heures supplémentaires",
    "heures supplémentaires compteurs récupération repos compensateur",
    "congé ancienneté",
    "congés payés règle du dixième maintien de salaire",
    "départ retraite",
    "classification",
    "classification coefficient évolution de poste",
    "inaptitude reclassement médecin du travail restrictions médicales",
    "procédure disciplinaire",
    "sanction",
    "sécurité",
    "DUERP RPS maintenance PROVOX",
    "droit syndical",
]

WEAK_QUERY_TOKENS = {"entre", "deux", "trois", "une", "un"}

SEARCH_PROFILES = [
    {
        "name": "temps de travail / repos",
        "triggers": [
            "repos",
            "poste",
            "postes",
            "5x8",
            "temps de travail",
            "temps de repos",
            "travail poste",
            "travail posté",
            "equipes postees",
            "équipes postées",
            "horaire",
            "horaires",
            "nuit",
            "astreinte",
        ],
        "synonym_phrases": [
            "repos entre deux postes",
            "repos entre deux journées",
            "repos entre deux journees",
            "repos quotidien",
            "temps de repos",
            "temps de travail",
            "organisation du travail",
            "durée du travail",
            "duree du travail",
            "5x8",
            "travail posté",
            "travail poste",
            "équipes postées",
            "equipes postees",
            "travail de nuit",
            "repos hebdomadaire",
        ],
        "topic_bonus": {
            "repos": 40,
            "temps de travail": 36,
            "5x8": 34,
            "travail posté": 34,
            "travail de nuit": 24,
            "astreinte": 20,
            "conditions de travail": 14,
            "sécurité": 8,
        },
        "theme_bonus_cap": 90,
        "doc_type_bonus": {
            "règlement intérieur": 12,
            "accord entreprise": 8,
            "convention collective": 14,
            "avenant": 10,
        },
        "title_terms": ["repos", "temps de travail", "5x8", "travail posté", "travail poste", "horaire", "horaires"],
        "penalty_topics": {
            "rémunération": 22,
            "primes": 20,
            "intéressement": 16,
            "participation": 16,
            "épargne salariale": 16,
        },
        "penalty_title_terms": ["nao", "salaire", "salaires", "rémunération", "remuneration", "prime", "primes", "intéressement", "interessement", "participation", "pereco", "pee", "télétravail", "teletravail"],
    },
    {
        "name": "paie / congés payés / indemnité de congés",
        "triggers": [
            "congés payés",
            "conges payes",
            "congé payé",
            "conge paye",
            "indemnité de congés",
            "indemnite de conges",
            "indemnité de congés payés",
            "indemnite de conges payes",
            "indemnité compensatrice",
            "indemnite compensatrice",
            "règle du dixième",
            "regle du dixieme",
            "dixième",
            "dixieme",
            "règle des 10",
            "regle des 10",
            "10 %",
            "maintien de salaire",
            "salaire de référence",
            "salaire de reference",
            "rémunération brute de référence",
            "remuneration brute de reference",
            "assiette",
            "période de référence",
            "periode de reference",
            "période d'acquisition",
            "periode d'acquisition",
            "prise des congés",
            "prise des conges",
            "régularisation",
            "regularisation",
            "rappel de salaire",
            "année civile",
            "annee civile",
        ],
        "synonym_phrases": [
            "congés payés",
            "conges payes",
            "congé payé",
            "conge paye",
            "indemnité de congés payés",
            "indemnite de conges payes",
            "indemnité de congés",
            "indemnite de conges",
            "indemnité compensatrice de congés payés",
            "indemnite compensatrice de conges payes",
            "règle du dixième",
            "regle du dixieme",
            "règle des 10 %",
            "regle des 10 %",
            "règle des 10 pour cent",
            "regle des 10 pour cent",
            "maintien de salaire",
            "comparaison dixième maintien",
            "comparaison dixieme maintien",
            "salaire de référence",
            "salaire de reference",
            "rémunération brute de référence",
            "remuneration brute de reference",
            "assiette de calcul",
            "période de référence",
            "periode de reference",
            "période d'acquisition",
            "periode d'acquisition",
            "prise des congés",
            "prise des conges",
            "régularisation",
            "regularisation",
            "rappel de salaire",
            "année civile",
            "annee civile",
        ],
        "topic_bonus": {
            "congés payés": 64,
            "congés": 54,
            "temps de travail": 28,
            "rémunération": 18,
            "primes": 10,
            "travail posté": 8,
            "travail de nuit": 8,
        },
        "theme_bonus_cap": 120,
        "doc_type_bonus": {
            "convention collective": 18,
            "accord entreprise": 14,
            "avenant": 12,
            "note collective": 8,
        },
        "title_terms": [
            "congés",
            "conges",
            "congés payés",
            "conges payes",
            "indemnité de congés",
            "indemnite de conges",
            "dixième",
            "dixieme",
            "maintien de salaire",
            "période de référence",
            "periode de reference",
            "temps de travail",
            "convention collective",
        ],
        "penalty_topics": {
            "droit syndical": 48,
            "CSE": 42,
            "dialogue social": 38,
            "intéressement": 36,
            "participation": 36,
            "épargne salariale": 34,
            "fin de carrière": 20,
        },
        "penalty_title_terms": [
            "nao",
            "prime",
            "primes",
            "intéressement",
            "interessement",
            "participation",
            "pereco",
            "pee",
            "cet",
            "forfait jours",
            "forfait jour",
        ],
    },
    {
        "name": "classification / emploi / carrière / coefficient",
        "triggers": [
            "classification",
            "coefficient",
            "niveau",
            "échelon",
            "echelon",
            "emploi",
            "poste",
            "fiche de poste",
            "fonctions exercées",
            "fonctions exercees",
            "responsabilités",
            "responsabilites",
            "autonomie",
            "technicité",
            "technicite",
            "évolution de poste",
            "evolution de poste",
            "carrière",
            "carriere",
            "polyvalence",
            "pesée de poste",
            "pesee de poste",
        ],
        "synonym_phrases": [
            "classification",
            "coefficient",
            "niveau",
            "échelon",
            "echelon",
            "fiche de poste",
            "fonctions exercées",
            "fonctions exercees",
            "responsabilités",
            "responsabilites",
            "autonomie",
            "technicité",
            "technicite",
            "évolution de poste",
            "evolution de poste",
            "carrière",
            "carriere",
            "polyvalence",
            "pesée de poste",
            "pesee de poste",
        ],
        "topic_bonus": {
            "classification": 64,
            "emploi": 44,
            "compétences": 22,
            "formation": 12,
            "rémunération": 8,
        },
        "theme_bonus_cap": 120,
        "doc_type_bonus": {
            "convention collective": 18,
            "accord entreprise": 12,
            "avenant": 10,
            "note collective": 8,
        },
        "title_terms": ["classification", "coefficient", "emploi", "poste", "carrière", "carriere", "fiche de poste"],
        "penalty_topics": {
            "droit syndical": 44,
            "CSE": 38,
            "dialogue social": 34,
            "securite process": 28,
            "maintenance": 24,
            "intéressement": 24,
            "participation": 24,
            "épargne salariale": 24,
        },
        "penalty_title_terms": ["droit syndical", "mandat", "cse", "nao", "interessement", "participation", "provox", "duerp", "maintenance"],
    },
    {
        "name": "inaptitude / reclassement / santé au travail",
        "triggers": [
            "inaptitude",
            "reclassement",
            "médecin du travail",
            "medecin du travail",
            "aptitude",
            "restrictions médicales",
            "restrictions medicales",
            "aménagement de poste",
            "amenagement de poste",
            "adaptation de poste",
            "poste compatible",
            "recherche de reclassement",
            "consultation cse",
            "impossibilité de reclassement",
            "impossibilite de reclassement",
            "licenciement pour inaptitude",
            "santé au travail",
            "sante au travail",
        ],
        "synonym_phrases": [
            "inaptitude",
            "reclassement",
            "médecin du travail",
            "medecin du travail",
            "aptitude",
            "restrictions médicales",
            "restrictions medicales",
            "aménagement de poste",
            "amenagement de poste",
            "adaptation de poste",
            "poste compatible",
            "recherche de reclassement",
            "consultation CSE",
            "consultation cse",
            "impossibilité de reclassement",
            "impossibilite de reclassement",
            "licenciement pour inaptitude",
            "santé au travail",
            "sante au travail",
        ],
        "topic_bonus": {
            "inaptitude reclassement": 70,
            "santé": 34,
            "emploi": 18,
            "formation": 16,
            "conditions de travail": 12,
        },
        "theme_bonus_cap": 130,
        "doc_type_bonus": {
            "convention collective": 18,
            "accord entreprise": 10,
            "règlement intérieur": 8,
            "note collective": 8,
        },
        "title_terms": ["inaptitude", "reclassement", "médecin du travail", "medecin du travail", "santé au travail", "sante au travail", "aptitude"],
        "penalty_topics": {
            "droit syndical": 46,
            "CSE": 32,
            "dialogue social": 30,
            "securite process": 36,
            "maintenance": 34,
            "continuite exploitation": 30,
            "rémunération": 18,
            "primes": 18,
        },
        "penalty_title_terms": ["droit syndical", "mandat", "heures de delegation", "provox", "sncc", "maintenance", "nao", "prime", "primes"],
    },
    {
        "name": "temps de travail / heures supplémentaires / compteurs",
        "triggers": [
            "heures supplémentaires",
            "heures supplementaires",
            "compteur",
            "compteurs",
            "compteur d'heures",
            "compteur d heures",
            "récupération",
            "recuperation",
            "repos compensateur",
            "majoration",
            "solde",
            "pointage",
            "badgeage",
            "temps de travail effectif",
            "heures effectuées",
            "heures effectuees",
            "heures payées",
            "heures payees",
            "heures récupérées",
            "heures recuperees",
            "contingent",
            "modulation",
            "annualisation",
        ],
        "synonym_phrases": [
            "heures supplémentaires",
            "heures supplementaires",
            "compteur d'heures",
            "compteur d heures",
            "compteurs d'heures",
            "compteurs d heures",
            "récupération",
            "recuperation",
            "repos compensateur",
            "majoration",
            "solde",
            "pointage",
            "badgeage",
            "temps de travail effectif",
            "heures effectuées",
            "heures effectuees",
            "heures payées",
            "heures payees",
            "heures récupérées",
            "heures recuperees",
            "contingent",
            "modulation",
            "annualisation",
        ],
        "topic_bonus": {
            "heures supplémentaires": 70,
            "temps de travail": 46,
            "repos": 24,
            "rémunération": 14,
            "primes": 10,
        },
        "theme_bonus_cap": 130,
        "doc_type_bonus": {
            "convention collective": 18,
            "accord entreprise": 14,
            "avenant": 10,
            "note collective": 8,
        },
        "title_terms": ["heures supplémentaires", "heures supplementaires", "compteur", "compteurs", "temps de travail", "repos compensateur", "pointage", "badgeage"],
        "penalty_topics": {
            "droit syndical": 44,
            "CSE": 36,
            "dialogue social": 32,
            "intéressement": 28,
            "participation": 28,
            "épargne salariale": 28,
            "securite process": 22,
            "maintenance": 22,
        },
        "penalty_title_terms": ["droit syndical", "mandat", "heures de delegation", "credit d heures", "nao", "interessement", "participation", "provox", "maintenance"],
    },
    {
        "name": "rémunération",
        "triggers": [
            "salaire",
            "salaires",
            "rémunération",
            "remuneration",
            "prime",
            "primes",
            "ppv",
            "intéressement",
            "interessement",
            "participation",
            "pereco",
            "pee",
        ],
        "synonym_phrases": [
            "rémunération",
            "remuneration",
            "salaires",
            "prime",
            "primes",
            "prime de nuit",
            "partage de la valeur",
            "intéressement",
            "interessement",
            "participation",
            "épargne salariale",
            "epargne salariale",
        ],
        "topic_bonus": {
            "rémunération": 34,
            "primes": 34,
            "intéressement": 28,
            "participation": 26,
            "épargne salariale": 24,
            "travail de nuit": 10,
        },
        "theme_bonus_cap": 86,
        "doc_type_bonus": {
            "accord entreprise": 8,
            "décision unilatérale": 8,
        },
        "title_terms": ["nao", "salaire", "salaires", "prime", "primes", "rémunération", "remuneration", "intéressement", "participation"],
        "penalty_topics": {},
        "penalty_title_terms": [],
    },
    {
        "name": "CSSCT / sécurité process / maintenance",
        "triggers": [
            "duerp",
            "duer",
            "rps",
            "risques psychosociaux",
            "securite",
            "securite process",
            "prevention",
            "conditions de travail",
            "maintenance",
            "piece de rechange",
            "pieces de rechange",
            "stock pieces",
            "pieces critiques",
            "climatisation",
            "analyseurs",
            "analyseurs en continu",
            "provox",
            "sncc",
            "panne",
            "scenario de panne",
            "continuite d exploitation",
            "contingence",
            "plan de contingence",
            "defaillance technique",
            "incident",
            "presque accident",
            "hn",
            "charge mentale",
            "stress",
            "astreinte technique",
            "risque chimique",
            "risques industriels",
        ],
        "synonym_phrases": [
            "DUERP",
            "DUER",
            "RPS",
            "risques psychosociaux",
            "securite process",
            "prevention",
            "conditions de travail",
            "maintenance",
            "pieces de rechange",
            "stock pieces",
            "pieces critiques",
            "climatisation",
            "analyseurs en continu",
            "PROVOX",
            "SNCC",
            "scenario de panne",
            "continuite d exploitation",
            "plan de contingence",
            "defaillance technique",
            "incident",
            "presque accident",
            "charge mentale",
            "astreinte technique",
            "risque chimique",
            "risques industriels",
        ],
        "topic_bonus": {
            "securite process": 54,
            "maintenance": 50,
            "continuite exploitation": 48,
            "RPS": 42,
            "securite": 40,
            "conditions de travail": 38,
            "sante": 24,
            "astreinte": 16,
            "temps de travail": 10,
        },
        "theme_bonus_cap": 130,
        "doc_type_bonus": {
            "reglement interieur": 16,
            "note collective": 12,
            "accord entreprise": 4,
            "avenant": 3,
        },
        "title_terms": [
            "cssct",
            "duerp",
            "duer",
            "rps",
            "securite",
            "securite process",
            "prevention",
            "conditions de travail",
            "maintenance",
            "pieces de rechange",
            "sncc",
            "provox",
            "analyseurs",
            "climatisation",
            "panne",
            "contingence",
            "reglement interieur",
        ],
        "penalty_topics": {
            "remuneration": 50,
            "primes": 48,
            "interessement": 42,
            "participation": 42,
            "epargne salariale": 42,
            "fin de carriere": 18,
            "droit syndical": 14,
            "dialogue social": 10,
        },
        "penalty_title_terms": [
            "nao",
            "paie",
            "salaire",
            "salaires",
            "remuneration",
            "prime",
            "primes",
            "cet",
            "pereco",
            "pee",
            "forfait jours",
            "forfait jour",
            "interessement",
            "participation",
        ],
    },
    {
        "name": "relations collectives / droit syndical",
        "triggers": [
            "droit syndical",
            "heures de delegation",
            "heures de délégation",
            "credit d heures",
            "crédit d heures",
            "moyens syndicaux",
            "local syndical",
            "affichage syndical",
            "reunions syndicales",
            "réunions syndicales",
            "mandat",
            "mandat syndical",
            "representant du personnel",
            "représentant du personnel",
            "representant syndical",
            "représentant syndical",
            "delegue syndical",
            "délégué syndical",
            "elu cse",
            "élu cse",
            "membre cse",
            "fonctionnement du cse",
        ],
        "synonym_phrases": [
            "heures de délégation",
            "heures de delegation",
            "crédit d'heures",
            "crédit d heures",
            "credit d'heures",
            "credit d heures",
            "temps de délégation",
            "temps de delegation",
            "mandat",
            "représentant du personnel",
            "representant du personnel",
            "élu CSE",
            "elu CSE",
            "membre CSE",
            "délégué syndical",
            "delegue syndical",
            "représentant syndical",
            "representant syndical",
            "droit syndical",
            "moyens syndicaux",
            "local syndical",
            "affichage syndical",
            "réunions syndicales",
            "reunions syndicales",
            "fonctionnement du CSE",
            "représentants du personnel",
            "representants du personnel",
        ],
        "topic_bonus": {
            "droit syndical": 44,
            "CSE": 38,
            "dialogue social": 34,
            "conditions de travail": 8,
            "formation": 6,
        },
        "theme_bonus_cap": 96,
        "doc_type_bonus": {
            "accord entreprise": 10,
            "protocole": 12,
            "règlement intérieur": 8,
            "convention collective": 12,
        },
        "title_terms": [
            "droit syndical",
            "représentant du personnel",
            "representant du personnel",
            "représentants du personnel",
            "representants du personnel",
            "délégué syndical",
            "delegue syndical",
            "moyens syndicaux",
            "local syndical",
            "fonctionnement du cse",
        ],
        "penalty_topics": {
            "rémunération": 22,
            "primes": 20,
            "intéressement": 16,
            "participation": 16,
            "épargne salariale": 16,
            "fin de carrière": 8,
        },
        "penalty_title_terms": [
            "paie",
            "salaire",
            "salaires",
            "rémunération",
            "remuneration",
            "prime",
            "primes",
            "cet",
            "pereco",
            "pee",
            "forfait jours",
            "forfait jour",
            "intéressement",
            "interessement",
            "participation",
        ],
    },
]

STOPWORDS = {
    "a",
    "au",
    "aux",
    "avec",
    "ce",
    "ces",
    "dans",
    "de",
    "des",
    "du",
    "en",
    "et",
    "la",
    "le",
    "les",
    "l",
    "un",
    "une",
    "pour",
    "par",
    "sur",
    "ou",
    "d",
}

CSSCT_PRIORITY_TERMS = [
    "duerp",
    "duer",
    "rps",
    "risques psychosociaux",
    "securite",
    "securite process",
    "prevention",
    "conditions de travail",
    "maintenance",
    "piece de rechange",
    "pieces de rechange",
    "stock pieces",
    "pieces critiques",
    "climatisation",
    "analyseurs",
    "analyseurs en continu",
    "provox",
    "sncc",
    "panne",
    "scenario de panne",
    "continuite d exploitation",
    "contingence",
    "plan de contingence",
    "defaillance technique",
    "incident",
    "presque accident",
    "charge mentale",
    "stress",
    "astreinte technique",
    "risque chimique",
    "risques industriels",
]

PAID_LEAVE_PRIORITY_TERMS = [
    "congés payés",
    "conges payes",
    "congé payé",
    "conge paye",
    "indemnité de congés",
    "indemnite de conges",
    "indemnité de congés payés",
    "indemnite de conges payes",
    "règle du dixième",
    "regle du dixieme",
    "dixième",
    "dixieme",
    "règle des 10",
    "regle des 10",
    "maintien de salaire",
    "période de référence",
    "periode de reference",
    "période d'acquisition",
    "periode d'acquisition",
    "indemnité compensatrice",
    "indemnite compensatrice",
    "passage à l'année civile",
    "passage a l'annee civile",
]

CLASSIFICATION_PRIORITY_TERMS = [
    "classification",
    "coefficient",
    "échelon",
    "echelon",
    "fiche de poste",
    "fonctions exercées",
    "fonctions exercees",
    "responsabilités",
    "responsabilites",
    "autonomie",
    "technicité",
    "technicite",
    "évolution de poste",
    "evolution de poste",
    "carrière",
    "carriere",
    "polyvalence",
    "pesée de poste",
    "pesee de poste",
]

INAPTITUDE_PRIORITY_TERMS = [
    "inaptitude",
    "reclassement",
    "médecin du travail",
    "medecin du travail",
    "restrictions médicales",
    "restrictions medicales",
    "aménagement de poste",
    "amenagement de poste",
    "adaptation de poste",
    "poste compatible",
    "recherche de reclassement",
    "impossibilité de reclassement",
    "impossibilite de reclassement",
    "licenciement pour inaptitude",
    "santé au travail",
    "sante au travail",
]

OVERTIME_COUNTER_PRIORITY_TERMS = [
    "heures supplémentaires",
    "heures supplementaires",
    "compteur d'heures",
    "compteur d heures",
    "compteurs",
    "récupération",
    "recuperation",
    "repos compensateur",
    "pointage",
    "badgeage",
    "temps de travail effectif",
    "heures effectuées",
    "heures effectuees",
    "heures payées",
    "heures payees",
    "heures récupérées",
    "heures recuperees",
    "contingent",
    "modulation",
    "annualisation",
]

REMUNERATION_QUERY_TERMS = [
    "salaire",
    "salaires",
    "remuneration",
    "paie",
    "prime",
    "primes",
    "majoration",
    "interessement",
    "participation",
    "pereco",
    "pee",
    "cet",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_dirs() -> None:
    for directory in [STATE_DIR, TEXT_DIR, INDEX_DIR, REPORT_DIR, SEARCH_DIR, TEST_DIR, OCR_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def try_write_json(path: Path, data: Any) -> bool:
    try:
        write_json(path, data)
        return True
    except OSError as error:
        print(f"AVERTISSEMENT: rapport privé non écrit ({error}).")
        return False


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value)
    without_marks = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    return without_marks.replace("æ", "ae").replace("œ", "oe").lower()


def tokenize(value: str) -> list[str]:
    tokens = re.findall(r"[a-zA-ZÀ-ÿ0-9]{2,}", normalize(value))
    return [token for token in tokens if token not in STOPWORDS]


def source_path_from_args(args: argparse.Namespace) -> Path:
    source = getattr(args, "source", None) or os.environ.get("CFDT_NEXUS_CORPUS_PATH") or load_remembered_source()
    if not source:
        raise SystemExit(
            "Source corpus manquante. Utiliser --source ou la variable CFDT_NEXUS_CORPUS_PATH."
        )
    path = Path(source).expanduser()
    if not path.exists() or not path.is_dir():
        raise SystemExit("Le chemin source n'est pas accessible ou n'est pas un dossier.")
    remember_source(path)
    return path


def remember_source(path: Path) -> None:
    write_json(
        SOURCE_CONFIG_PATH,
        {
            "source_path": str(path),
            "updated_at": now_iso(),
            "security_notice": "Private local source path. Do not commit.",
        },
    )


def load_remembered_source() -> str | None:
    config = load_json(SOURCE_CONFIG_PATH, None)
    if not config:
        return None
    return config.get("source_path")


def relative_to_source(path: Path, source: Path) -> str:
    return str(path.relative_to(source)).replace("\\", "/")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def doc_id_for_sha(sha256: str) -> str:
    return f"doc_{sha256[:16]}"


def match_rules(text: str, rules: list[tuple[str, list[str]]], sort_by_score: bool = True) -> list[str]:
    haystack = normalize(text)
    matches = []
    for order, (label, patterns) in enumerate(rules):
        count = 0
        first_index = None
        for pattern in patterns:
            for match in re.finditer(pattern, haystack, flags=re.IGNORECASE):
                count += 1
                first_index = match.start() if first_index is None else min(first_index, match.start())
        if count:
            matches.append({"label": label, "count": count, "first_index": first_index or 0, "order": order})
    if sort_by_score:
        matches.sort(key=lambda item: (-item["count"], item["first_index"], item["order"]))
    return [item["label"] for item in matches]


def classify_document(relative_path: str, text_sample: str = "") -> dict[str, Any]:
    combined = f"{relative_path}\n{text_sample[:6000]}"
    doc_types = match_rules(combined, DOCUMENT_TYPES, sort_by_score=False)
    topics = match_rules(combined, TOPIC_RULES)

    if len(doc_types) == 1:
        document_type = doc_types[0]
        classification_note = "Classement V1 déterministe à valider humainement."
    elif len(doc_types) > 1:
        document_type = doc_types[0]
        classification_note = "Plusieurs types possibles détectés. Type prioritaire retenu, validation humaine nécessaire."
    else:
        document_type = "autre document collectif"
        classification_note = "Aucun type spécifique détecté avec confiance."

    primary_topic = topics[0] if topics else "autres"
    secondary_topics = topics[1:] if len(topics) > 1 else []

    return {
        "document_type": document_type,
        "primary_topic": primary_topic,
        "secondary_topics": secondary_topics,
        "classification_note": classification_note,
    }


def inventory_paths() -> tuple[Path, Path]:
    return STATE_DIR / "inventory.private.json", STATE_DIR / "previous-inventory.private.json"


def scan_corpus(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    source = source_path_from_args(args)
    current_path, previous_path = inventory_paths()
    previous_inventory = load_json(current_path, {"documents": []})
    previous_by_rel = {item["relative_path"]: item for item in previous_inventory.get("documents", [])}
    current_docs = []
    seen_sha = defaultdict(list)
    checked_at = now_iso()

    extensions = {".pdf", ".docx", ".doc", ".txt", ".rtf", ".odt"}
    for file_path in sorted(source.rglob("*")):
        if not file_path.is_file():
            continue
        extension = file_path.suffix.lower() or "[sans extension]"
        if extension not in extensions:
            continue

        relative_path = relative_to_source(file_path, source)
        sha256 = file_sha256(file_path)
        document_id = doc_id_for_sha(sha256)
        previous = previous_by_rel.get(relative_path)
        if previous is None:
            change_status = "NEW"
        elif previous.get("sha256") != sha256:
            change_status = "MODIFIED"
        else:
            change_status = "UNCHANGED"

        classification = classify_document(relative_path)
        item = {
            "document_id": document_id,
            "filename": file_path.name,
            "extension": extension,
            "relative_path": relative_path,
            "file_size": file_path.stat().st_size,
            "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).isoformat(),
            "sha256": sha256,
            "change_status": change_status,
            "extraction_status": previous.get("extraction_status", "PENDING") if previous else "PENDING",
            "ocr_required": previous.get("ocr_required", False) if previous else False,
            "document_type": classification["document_type"],
            "primary_topic": classification["primary_topic"],
            "secondary_topics": classification["secondary_topics"],
            "classification_note": classification["classification_note"],
            "confidentiality_level": "private",
            "indexed_at": previous.get("indexed_at") if previous else None,
            "last_checked_at": checked_at,
        }
        current_docs.append(item)
        seen_sha[sha256].append(item)

    for items in seen_sha.values():
        if len(items) > 1:
            for item in items:
                item["change_status"] = "DUPLICATE_EXACT"

    current_rel = {item["relative_path"] for item in current_docs}
    for previous in previous_inventory.get("documents", []):
        if previous.get("relative_path") not in current_rel:
            missing = dict(previous)
            missing["change_status"] = "MISSING"
            missing["last_checked_at"] = checked_at
            current_docs.append(missing)

    if current_path.exists():
        previous_path.write_text(current_path.read_text(encoding="utf-8"), encoding="utf-8")

    summary = build_quality_summary(current_docs)
    inventory = {
        "generated_at": checked_at,
        "source_path_stored": False,
        "source_label": "private-local-corpus",
        "documents": current_docs,
        "summary": summary,
        "security_notice": "Private local inventory. Do not commit.",
    }
    write_json(current_path, inventory)
    write_json(REPORT_DIR / f"scan-summary-{safe_stamp()}.private.json", summary)
    print_scan_summary(summary)
    return inventory


def safe_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")


def build_quality_summary(documents: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "total_documents": len([d for d in documents if d.get("change_status") != "MISSING"]),
        "new": count_status(documents, "NEW"),
        "modified": count_status(documents, "MODIFIED"),
        "unchanged": count_status(documents, "UNCHANGED"),
        "missing": count_status(documents, "MISSING"),
        "duplicate_exact": count_status(documents, "DUPLICATE_EXACT"),
        "extraction_ok": count_extraction(documents, "EXTRACTION_OK"),
        "extraction_to_verify": count_extraction(documents, "EXTRACTION_A_VERIFIER"),
        "ocr_required": sum(1 for d in documents if d.get("ocr_required")),
        "ocr_low_confidence": count_extraction(documents, "OCR_LOW_CONFIDENCE"),
        "errors": count_extraction(documents, "ERROR"),
        "unsupported": count_extraction(documents, "UNSUPPORTED"),
        "classified": sum(1 for d in documents if d.get("document_type") not in {"à classer"}),
        "to_classify_manually": sum(1 for d in documents if d.get("document_type") == "à classer"),
        "by_extension": Counter(d.get("extension") for d in documents if d.get("change_status") != "MISSING"),
        "by_topic": Counter(d.get("primary_topic") for d in documents if d.get("change_status") != "MISSING"),
    }


def count_status(documents: list[dict[str, Any]], status: str) -> int:
    return sum(1 for item in documents if item.get("change_status") == status)


def count_extraction(documents: list[dict[str, Any]], status: str) -> int:
    return sum(1 for item in documents if item.get("extraction_status") == status)


def print_scan_summary(summary: dict[str, Any]) -> None:
    print(f"Documents détectés: {summary['total_documents']}")
    print(f"NEW: {summary['new']} | MODIFIED: {summary['modified']} | UNCHANGED: {summary['unchanged']} | MISSING: {summary['missing']}")
    print(f"DUPLICATE_EXACT: {summary['duplicate_exact']}")


def extract_pdf(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        import pdfplumber  # type: ignore

        with pdfplumber.open(str(path)) as pdf:
            for index, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                pages.append({"page": index, "text": text})
    except Exception as error:  # pragma: no cover - local fallback
        errors.append(f"pdfplumber: {error}")
        try:
            from pypdf import PdfReader  # type: ignore

            reader = PdfReader(str(path))
            pages = []
            for index, page in enumerate(reader.pages, start=1):
                pages.append({"page": index, "text": page.extract_text() or ""})
        except Exception as fallback_error:
            errors.append(f"pypdf: {fallback_error}")

    diagnostics = extraction_diagnostics(pages, errors, ocr_possible=True)
    return pages, diagnostics


def extract_docx(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    try:
        import docx  # type: ignore

        document = docx.Document(str(path))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text.strip())
        pages = [{"page": None, "text": text}]
        return pages, extraction_diagnostics(pages, [], ocr_possible=False)
    except Exception as error:
        return [], extraction_diagnostics([], [str(error)], ocr_possible=False)


def extract_txt(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    for encoding in ["utf-8", "cp1252", "latin-1"]:
        try:
            pages = [{"page": None, "text": path.read_text(encoding=encoding)}]
            return pages, extraction_diagnostics(pages, [], ocr_possible=False)
        except UnicodeDecodeError:
            continue
    return [], extraction_diagnostics([], ["encoding unsupported"], ocr_possible=False)


def ocr_doc_dir(document_id: str) -> Path:
    return OCR_DIR / document_id


def ocr_status_path(document_id: str) -> Path:
    return ocr_doc_dir(document_id) / "ocr-status.private.json"


def ocr_local_path(relative_path: str | None) -> Path | None:
    if not relative_path:
        return None
    return LOCAL_ROOT / relative_path


def ocr_relative_path(path: Path) -> str:
    return str(path.relative_to(LOCAL_ROOT)).replace("\\", "/")


def load_ocr_status(doc: dict[str, Any]) -> dict[str, Any] | None:
    status = load_json(ocr_status_path(doc["document_id"]), None)
    if not status or status.get("document_id") != doc.get("document_id"):
        return None
    return status


def is_ocr_success(status: dict[str, Any] | None) -> bool:
    if not status or status.get("status") not in {"OCR_SUCCESS", "OCR_LOW_CONFIDENCE"}:
        return False
    output_pdf = ocr_local_path(status.get("output_pdf_path"))
    pages_path = ocr_local_path(status.get("text_pages_path"))
    return bool((output_pdf and output_pdf.exists()) or (pages_path and pages_path.exists()))


def ocr_result_newer_than_text(doc: dict[str, Any], text_path: Path) -> bool:
    status_path = ocr_status_path(doc["document_id"])
    if not is_ocr_success(load_ocr_status(doc)) or not status_path.exists():
        return False
    return not text_path.exists() or status_path.stat().st_mtime >= text_path.stat().st_mtime


def run_local_command(cmd: list[str], cwd: Path | None = None, timeout: int | None = None) -> dict[str, Any]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
            "duration_seconds": round(time.monotonic() - started, 2),
        }
    except Exception as error:  # pragma: no cover - depends on local tools
        return {
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": str(error),
            "duration_seconds": round(time.monotonic() - started, 2),
        }


def command_version(command: str | None) -> str | None:
    if not command:
        return None
    result = run_local_command([command, "--version"], timeout=20)
    output = result.get("stdout") or result.get("stderr") or ""
    return output.splitlines()[0] if output else None


def tesseract_languages(tesseract_cmd: str | None) -> list[str]:
    if not tesseract_cmd:
        return []
    result = run_local_command([tesseract_cmd, "--list-langs"], timeout=20)
    if not result["ok"]:
        return []
    return [line.strip() for line in result["stdout"].splitlines() if line.strip() and "List of available languages" not in line]


def detect_ocr_environment() -> dict[str, Any]:
    ocrmypdf = shutil.which("ocrmypdf")
    tesseract = shutil.which("tesseract")
    ghostscript = shutil.which("gswin64c") or shutil.which("gs")
    pdftoppm = shutil.which("pdftoppm")
    languages = tesseract_languages(tesseract)
    has_french = "fra" in languages
    return {
        "generated_at": now_iso(),
        "commands": {
            "ocrmypdf": ocrmypdf,
            "tesseract": tesseract,
            "ghostscript": ghostscript,
            "pdftoppm": pdftoppm,
        },
        "versions": {
            "ocrmypdf": command_version(ocrmypdf),
            "tesseract": command_version(tesseract),
            "ghostscript": command_version(ghostscript),
            "pdftoppm": command_version(pdftoppm),
        },
        "python_modules": {
            "ocrmypdf": bool(importlib.util.find_spec("ocrmypdf")),
            "pdf2image": bool(importlib.util.find_spec("pdf2image")),
            "pytesseract": bool(importlib.util.find_spec("pytesseract")),
            "PIL": bool(importlib.util.find_spec("PIL")),
            "pdfplumber": bool(importlib.util.find_spec("pdfplumber")),
            "pypdf": bool(importlib.util.find_spec("pypdf")),
        },
        "tesseract_languages": languages,
        "has_french": has_french,
        "can_use_ocrmypdf": bool(ocrmypdf and tesseract and ghostscript and has_french),
        "can_use_tesseract_fallback": bool(tesseract and pdftoppm and has_french),
        "recommended_engine": "ocrmypdf"
        if ocrmypdf and tesseract and ghostscript and has_french
        else "tesseract-pdftoppm"
        if tesseract and pdftoppm and has_french
        else None,
        "security_notice": "Local OCR environment report. Do not commit generated reports.",
    }


def ocr_installation_instructions() -> list[str]:
    return [
        "Installer Tesseract OCR Windows 64-bit avec la langue française (fra.traineddata).",
        "Installer Ghostscript 64-bit si OCRmyPDF est utilisé.",
        "Installer OCRmyPDF dans un environnement Python local : python -m pip install ocrmypdf.",
        "Vérifier ensuite dans PowerShell : tesseract --list-langs ; ocrmypdf --version ; gswin64c --version.",
        "Relancer : python automation/scripts/agreements_bible.py ocr-diagnose.",
    ]


def choose_ocr_language(requested: str, languages: list[str]) -> str | None:
    requested_parts = [part.strip() for part in requested.split("+") if part.strip()]
    if "fra" not in languages:
        return None
    usable = [part for part in requested_parts if part in languages]
    if "fra" not in usable:
        usable.insert(0, "fra")
    return "+".join(dict.fromkeys(usable))


def ocr_required_documents(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        doc
        for doc in inventory.get("documents", [])
        if doc.get("change_status") != "MISSING"
        and doc.get("extension") == ".pdf"
        and (doc.get("ocr_required") or doc.get("extraction_status") == "OCR_REQUIRED")
    ]


def count_pdf_pages(path: Path) -> int | None:
    try:
        from pypdf import PdfReader  # type: ignore

        return len(PdfReader(str(path)).pages)
    except Exception:
        return None


def parse_tesseract_tsv(tsv: str) -> tuple[str, float | None]:
    lines: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    confidences: list[float] = []
    for raw_line in tsv.splitlines()[1:]:
        parts = raw_line.split("\t")
        if len(parts) < 12:
            continue
        text = parts[11].strip()
        if not text:
            continue
        key = (parts[2], parts[3], parts[4])
        lines[key].append(text)
        try:
            confidence = float(parts[10])
            if confidence >= 0:
                confidences.append(confidence)
        except ValueError:
            continue
    reconstructed = "\n".join(" ".join(words) for _, words in sorted(lines.items()))
    average = sum(confidences) / len(confidences) if confidences else None
    return reconstructed.strip(), average


def run_ocrmypdf_for_doc(doc: dict[str, Any], source_pdf: Path, env: dict[str, Any], lang: str) -> dict[str, Any]:
    doc_dir = ocr_doc_dir(doc["document_id"])
    work_dir = doc_dir / "work"
    work_dir.mkdir(parents=True, exist_ok=True)
    input_copy = work_dir / "source-copy.pdf"
    output_pdf = doc_dir / "document.ocr.pdf"
    shutil.copy2(source_pdf, input_copy)
    started = time.monotonic()
    command = [
        env["commands"]["ocrmypdf"],
        "--skip-text",
        "--language",
        lang,
        "--output-type",
        "pdf",
        "--optimize",
        "0",
        str(input_copy),
        str(output_pdf),
    ]
    result = run_local_command(command, timeout=None)
    pages, diagnostics = extract_pdf(output_pdf) if output_pdf.exists() else ([], extraction_diagnostics([], [result["stderr"]], ocr_possible=False))
    status = "OCR_SUCCESS" if result["ok"] and diagnostics["char_count"] > 0 else "OCR_FAILED"
    return {
        "document_id": doc["document_id"],
        "status": status,
        "engine": "ocrmypdf",
        "language": lang,
        "started_at": now_iso(),
        "duration_seconds": round(time.monotonic() - started, 2),
        "output_pdf_path": ocr_relative_path(output_pdf) if output_pdf.exists() else None,
        "text_pages_path": None,
        "page_count": diagnostics.get("page_count") or count_pdf_pages(source_pdf),
        "char_count": diagnostics.get("char_count", 0),
        "average_confidence": None,
        "confidence_status": "UNKNOWN",
        "error_message": None if status == "OCR_SUCCESS" else (result.get("stderr") or result.get("stdout")),
        "security_notice": "Private OCR status. Do not commit.",
    }


def run_tesseract_fallback_for_doc(doc: dict[str, Any], source_pdf: Path, env: dict[str, Any], lang: str) -> dict[str, Any]:
    doc_dir = ocr_doc_dir(doc["document_id"])
    work_dir = doc_dir / "work"
    work_dir.mkdir(parents=True, exist_ok=True)
    input_copy = work_dir / "source-copy.pdf"
    image_prefix = work_dir / "page"
    pages_path = doc_dir / "pages.private.json"
    shutil.copy2(source_pdf, input_copy)
    started = time.monotonic()
    convert = run_local_command([env["commands"]["pdftoppm"], "-r", "300", "-png", str(input_copy), str(image_prefix)], timeout=None)
    if not convert["ok"]:
        return {
            "document_id": doc["document_id"],
            "status": "OCR_FAILED",
            "engine": "tesseract-pdftoppm",
            "language": lang,
            "started_at": now_iso(),
            "duration_seconds": round(time.monotonic() - started, 2),
            "output_pdf_path": None,
            "text_pages_path": None,
            "page_count": count_pdf_pages(source_pdf),
            "char_count": 0,
            "average_confidence": None,
            "confidence_status": "UNKNOWN",
            "error_message": convert.get("stderr") or convert.get("stdout"),
            "security_notice": "Private OCR status. Do not commit.",
        }

    image_files = sorted(work_dir.glob("page-*.png"), key=lambda item: int(re.search(r"-(\d+)\.png$", item.name).group(1)) if re.search(r"-(\d+)\.png$", item.name) else 0)
    pages: list[dict[str, Any]] = []
    confidences: list[float] = []
    errors: list[str] = []
    for page_number, image in enumerate(image_files, start=1):
        ocr = run_local_command([env["commands"]["tesseract"], str(image), "stdout", "-l", lang, "--dpi", "300", "tsv"], timeout=None)
        if not ocr["ok"]:
            errors.append(f"page {page_number}: {ocr.get('stderr') or ocr.get('stdout')}")
            pages.append({"page": page_number, "text": "", "ocr_confidence": None})
            continue
        text, confidence = parse_tesseract_tsv(ocr["stdout"])
        if confidence is not None:
            confidences.append(confidence)
        pages.append({"page": page_number, "text": text, "ocr_confidence": confidence})
        try:
            image.unlink()
        except OSError:
            pass

    full_text = "\n".join(page.get("text", "") for page in pages).strip()
    average = sum(confidences) / len(confidences) if confidences else None
    confidence_status = "LOW" if average is not None and average < OCR_LOW_CONFIDENCE_THRESHOLD else "OK" if average is not None else "UNKNOWN"
    status = "OCR_LOW_CONFIDENCE" if full_text and confidence_status == "LOW" else "OCR_SUCCESS" if full_text else "OCR_FAILED"
    write_json(
        pages_path,
        {
            "document_id": doc["document_id"],
            "pages": pages,
            "average_confidence": average,
            "language": lang,
            "engine": "tesseract-pdftoppm",
            "security_notice": "Private OCR text pages. Do not commit.",
        },
    )
    return {
        "document_id": doc["document_id"],
        "status": status,
        "engine": "tesseract-pdftoppm",
        "language": lang,
        "started_at": now_iso(),
        "duration_seconds": round(time.monotonic() - started, 2),
        "output_pdf_path": None,
        "text_pages_path": ocr_relative_path(pages_path),
        "page_count": len(pages),
        "char_count": len(full_text),
        "average_confidence": average,
        "confidence_status": confidence_status,
        "error_message": " | ".join(errors) if errors else None,
        "security_notice": "Private OCR status. Do not commit.",
    }


def extract_from_ocr_result(doc: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]] | None:
    status = load_ocr_status(doc)
    if not is_ocr_success(status):
        return None
    pages_path = ocr_local_path(status.get("text_pages_path"))
    output_pdf = ocr_local_path(status.get("output_pdf_path"))
    if pages_path and pages_path.exists():
        payload = load_json(pages_path, {})
        pages = payload.get("pages", [])
        diagnostics = extraction_diagnostics(pages, [], ocr_possible=False)
    elif output_pdf and output_pdf.exists():
        pages, diagnostics = extract_pdf(output_pdf)
    else:
        return None

    confidence = status.get("average_confidence")
    confidence_status = status.get("confidence_status", "UNKNOWN")
    diagnostics["ocr_engine"] = status.get("engine")
    diagnostics["ocr_confidence"] = confidence
    diagnostics["ocr_confidence_status"] = confidence_status
    diagnostics["ocr_status"] = status.get("status")
    diagnostics["ocr_source"] = "local"
    if diagnostics["char_count"] == 0:
        diagnostics["status"] = "OCR_REQUIRED"
        diagnostics["ocr_required"] = True
        diagnostics["extraction_note"] = "OCR local réalisé mais aucun texte exploitable n'a été produit."
    elif status.get("status") == "OCR_LOW_CONFIDENCE" or confidence_status == "LOW":
        diagnostics["status"] = "OCR_LOW_CONFIDENCE"
        diagnostics["ocr_required"] = False
        diagnostics["extraction_note"] = "OCR local exploitable mais confiance faible. Vérification humaine obligatoire."
    elif diagnostics["status"] == "EXTRACTION_A_VERIFIER":
        diagnostics["status"] = "OCR_LOW_CONFIDENCE"
        diagnostics["ocr_required"] = False
        diagnostics["extraction_note"] = "OCR local extrait mais texte faible ou partiel. Vérification humaine obligatoire."
    else:
        diagnostics["status"] = "EXTRACTION_OK"
        diagnostics["ocr_required"] = False
        diagnostics["extraction_note"] = "Texte issu d'un OCR local."
    return pages, diagnostics


def extraction_diagnostics(pages: list[dict[str, Any]], errors: list[str], ocr_possible: bool) -> dict[str, Any]:
    text = "\n".join(page.get("text", "") for page in pages)
    chars = len(text.strip())
    page_count = len(pages)
    empty_pages = sum(1 for page in pages if len(page.get("text", "").strip()) < MIN_PAGE_TEXT_CHARS)
    weird = len(re.findall(r"[�□■]", text))
    weird_ratio = weird / max(chars, 1)
    error_message = " | ".join(errors) if errors else None

    if ocr_possible and page_count > 0 and chars == 0:
        status = "OCR_REQUIRED"
        ocr_required = True
        note = "PDF avec pages détectées mais aucun texte exploitable extrait. OCR local requis."
    elif errors and page_count == 0:
        status = "ERROR"
        ocr_required = False
        note = "Erreur technique : aucun parseur PDF n'a pu lire le document ou détecter ses pages."
    elif chars < MIN_TEXT_CHARS and ocr_possible:
        status = "OCR_REQUIRED"
        ocr_required = True
        note = "PDF avec texte extrait insuffisant. OCR ou contrôle manuel requis."
    elif chars < MIN_TEXT_CHARS:
        status = "EXTRACTION_A_VERIFIER"
        ocr_required = False
        note = "Texte extrait faible. Vérification humaine recommandée."
    elif weird_ratio > 0.02 or empty_pages > max(2, len(pages) // 2):
        status = "EXTRACTION_A_VERIFIER"
        ocr_required = False
        note = "Extraction partielle ou caractères inhabituels détectés. Vérification humaine recommandée."
    else:
        status = "EXTRACTION_OK"
        ocr_required = False
        note = "Extraction texte exploitable."

    return {
        "status": status,
        "ocr_required": ocr_required,
        "char_count": chars,
        "page_count": page_count,
        "empty_or_low_text_pages": empty_pages,
        "weird_char_ratio": weird_ratio,
        "errors": errors,
        "error_message": error_message,
        "extraction_note": note,
    }


def extract_documents(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    source = source_path_from_args(args)
    inventory_path, _ = inventory_paths()
    inventory = load_json(inventory_path, None)
    if inventory is None:
        inventory = scan_corpus(args)

    report_rows = []
    changed = 0
    for doc in inventory["documents"]:
        if doc.get("change_status") == "MISSING":
            continue
        if doc.get("extension") not in {".pdf", ".docx", ".txt"}:
            doc["extraction_status"] = "UNSUPPORTED"
            doc["ocr_required"] = False
            doc["error_message"] = None
            doc["extraction_note"] = "Format non supporté par la V1."
            doc["extraction_diagnostics"] = {
                "status": "UNSUPPORTED",
                "ocr_required": False,
                "char_count": 0,
                "page_count": 0,
                "empty_or_low_text_pages": 0,
                "weird_char_ratio": 0,
                "errors": [],
                "error_message": None,
                "extraction_note": "Format non supporté par la V1.",
            }
            report_rows.append(report_doc(doc, "UNSUPPORTED", 0, 0))
            continue

        output_path = text_output_path(doc["document_id"])
        must_extract = (
            getattr(args, "force", False)
            or doc.get("change_status") in {"NEW", "MODIFIED", "DUPLICATE_EXACT"}
            or not output_path.exists()
            or ocr_result_newer_than_text(doc, output_path)
        )
        if not must_extract:
            report_rows.append(report_doc(doc, doc.get("extraction_status", "PENDING"), None, None))
            continue

        file_path = source / doc["relative_path"]
        pages: list[dict[str, Any]]
        diagnostics: dict[str, Any]
        if doc["extension"] == ".pdf":
            ocr_extracted = extract_from_ocr_result(doc)
            if ocr_extracted:
                pages, diagnostics = ocr_extracted
            else:
                pages, diagnostics = extract_pdf(file_path)
        elif doc["extension"] == ".docx":
            pages, diagnostics = extract_docx(file_path)
        else:
            pages, diagnostics = extract_txt(file_path)

        full_text = "\n\n".join(page.get("text", "") for page in pages).strip()
        classification = classify_document(doc["relative_path"], full_text[:8000])
        doc.update(classification)
        doc["extraction_status"] = diagnostics["status"]
        doc["ocr_required"] = diagnostics["ocr_required"]
        doc["extraction_note"] = diagnostics.get("extraction_note")
        doc["error_message"] = diagnostics.get("error_message")
        doc["ocr_engine"] = diagnostics.get("ocr_engine")
        doc["ocr_confidence"] = diagnostics.get("ocr_confidence")
        doc["ocr_confidence_status"] = diagnostics.get("ocr_confidence_status")
        doc["last_extracted_at"] = now_iso()
        doc["extraction_diagnostics"] = diagnostics

        extracted = {
            "document_id": doc["document_id"],
            "filename": doc["filename"],
            "relative_path": doc["relative_path"],
            "sha256": doc["sha256"],
            "extracted_at": now_iso(),
            "pages": pages,
            "full_text": full_text,
            "diagnostics": diagnostics,
            "security_notice": "Private extracted text. Do not commit.",
        }
        write_json(output_path, extracted)
        report_rows.append(report_doc(doc, diagnostics["status"], diagnostics["char_count"], diagnostics["page_count"]))
        changed += 1

    inventory["summary"] = build_quality_summary(inventory["documents"])
    write_json(inventory_path, inventory)
    report = {
        "generated_at": now_iso(),
        "changed_or_extracted": changed,
        "rows": report_rows,
        "summary": inventory["summary"],
        "security_notice": "Private extraction report. Do not commit.",
    }
    write_json(REPORT_DIR / f"extraction-report-{safe_stamp()}.private.json", report)
    print(f"Documents extraits ou mis à jour: {changed}")
    print(f"EXTRACTION_OK: {inventory['summary']['extraction_ok']} | OCR_REQUIRED: {inventory['summary']['ocr_required']} | ERREUR: {inventory['summary']['errors']}")
    return report


def text_output_path(document_id: str) -> Path:
    return TEXT_DIR / f"{document_id}.private.json"


def report_doc(doc: dict[str, Any], status: str, chars: int | None, pages: int | None) -> dict[str, Any]:
    diagnostics = doc.get("extraction_diagnostics", {})
    return {
        "document_id": doc.get("document_id"),
        "extension": doc.get("extension"),
        "change_status": doc.get("change_status"),
        "extraction_status": status,
        "ocr_required": doc.get("ocr_required", False),
        "char_count": chars,
        "page_count": pages,
        "document_type": doc.get("document_type"),
        "primary_topic": doc.get("primary_topic"),
        "error_message": diagnostics.get("error_message"),
        "extraction_note": diagnostics.get("extraction_note"),
        "ocr_engine": diagnostics.get("ocr_engine") or doc.get("ocr_engine"),
        "ocr_confidence": diagnostics.get("ocr_confidence") or doc.get("ocr_confidence"),
        "ocr_confidence_status": diagnostics.get("ocr_confidence_status") or doc.get("ocr_confidence_status"),
    }


def find_section_or_article(line: str) -> tuple[str | None, str | None]:
    text = line.strip()
    article_match = re.match(r"^(article\s+[0-9ivxlcdm\-\.]+)", normalize(text), flags=re.IGNORECASE)
    if article_match:
        return None, text[:120]
    section_match = re.match(
        r"^((titre|chapitre|annexe|préambule|preambule|section)\s+[^:]{0,80})",
        text,
        flags=re.IGNORECASE,
    )
    if section_match:
        return text[:160], None
    return None, None


def chunk_text(extracted: dict[str, Any], metadata: dict[str, Any]) -> list[dict[str, Any]]:
    chunks = []
    chunk_number = 1
    current_section: str | None = None
    current_article: str | None = None

    for page in extracted.get("pages", []):
        page_number = page.get("page")
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n|\r\n\s*\r\n", page.get("text", "")) if p.strip()]
        buffer: list[str] = []

        def flush() -> None:
            nonlocal chunk_number, buffer
            if not buffer:
                return
            text = "\n\n".join(buffer).strip()
            if len(text) < 30:
                buffer = []
                return
            chunks.append(
                {
                    "chunk_id": f"{metadata['document_id']}_chunk_{chunk_number:05d}",
                    "document_id": metadata["document_id"],
                    "filename": metadata["filename"],
                    "relative_path": metadata["relative_path"],
                    "chunk_number": chunk_number,
                    "page": page_number,
                    "section": current_section,
                    "article": current_article,
                    "document_type": metadata.get("document_type"),
                    "primary_topic": metadata.get("primary_topic"),
                    "secondary_topics": metadata.get("secondary_topics", []),
                    "ocr_confidence_status": metadata.get("ocr_confidence_status"),
                    "source_quality_warning": "OCR local à confiance faible : relire le document source avant utilisation."
                    if metadata.get("extraction_status") == "OCR_LOW_CONFIDENCE"
                    else None,
                    "text": text,
                }
            )
            chunk_number += 1
            if len(text) > CHUNK_OVERLAP_CHARS:
                buffer = [text[-CHUNK_OVERLAP_CHARS:]]
            else:
                buffer = []

        for paragraph in paragraphs:
            section, article = find_section_or_article(paragraph.splitlines()[0])
            if section:
                flush()
                current_section = section
                current_article = None
            if article:
                flush()
                current_article = article

            candidate = "\n\n".join(buffer + [paragraph])
            if len(candidate) > MAX_CHUNK_CHARS:
                flush()
            buffer.append(paragraph)

        flush()
    return chunks


def build_index(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    inventory_path, _ = inventory_paths()
    inventory = load_json(inventory_path, None)
    if inventory is None:
        raise SystemExit("Aucun inventaire local. Lancer d'abord update ou scan.")

    docs_by_id = {doc["document_id"]: doc for doc in inventory.get("documents", [])}
    all_chunks: list[dict[str, Any]] = []
    relations = []

    for doc in inventory.get("documents", []):
        if doc.get("change_status") == "MISSING" or doc.get("extraction_status") not in {"EXTRACTION_OK", "EXTRACTION_A_VERIFIER", "OCR_LOW_CONFIDENCE"}:
            continue
        extracted_path = text_output_path(doc["document_id"])
        if not extracted_path.exists():
            continue
        extracted = load_json(extracted_path, {})
        chunks = chunk_text(extracted, doc)
        all_chunks.extend(chunks)
        doc["indexed_at"] = now_iso()

    token_index: dict[str, dict[str, int]] = defaultdict(dict)
    for chunk in all_chunks:
        counts = Counter(tokenize(chunk["text"]))
        for token, count in counts.items():
            token_index[token][chunk["chunk_id"]] = count

    relations = detect_potential_relations(inventory.get("documents", []))
    write_jsonl(INDEX_DIR / "chunks.private.jsonl", all_chunks)
    write_json(INDEX_DIR / "lexical-index.private.json", token_index)
    write_json(INDEX_DIR / "relations.private.json", relations)
    inventory["summary"] = build_quality_summary(inventory["documents"])
    inventory["summary"]["chunks"] = len(all_chunks)
    inventory["summary"]["potential_relations"] = len(relations)
    write_json(inventory_path, inventory)

    report = {
        "generated_at": now_iso(),
        "indexed_documents": len({chunk["document_id"] for chunk in all_chunks}),
        "chunks": len(all_chunks),
        "potential_relations": len(relations),
        "security_notice": "Private index report. Do not commit.",
    }
    write_json(REPORT_DIR / f"index-report-{safe_stamp()}.private.json", report)
    print(f"Documents indexés: {report['indexed_documents']} | Chunks: {report['chunks']} | Relations potentielles: {report['potential_relations']}")
    return report


def detect_potential_relations(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    active = [d for d in documents if d.get("change_status") != "MISSING"]
    by_topic: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for doc in active:
        by_topic[doc.get("primary_topic", "autres")].append(doc)

    relations = []
    for doc in active:
        text = normalize(f"{doc.get('filename', '')} {doc.get('document_type', '')}")
        if "avenant" not in text and "modification" not in text:
            continue
        for candidate in by_topic.get(doc.get("primary_topic", "autres"), []):
            if candidate["document_id"] == doc["document_id"]:
                continue
            relations.append(
                {
                    "source_document_id": doc["document_id"],
                    "target_document_id": candidate["document_id"],
                    "relation_type": "RELATION POTENTIELLE - A VERIFIER",
                    "reason": "Document de type avenant/modification et thème commun.",
                    "validated": False,
                }
            )
    return relations


def select_search_profile(query: str, query_tokens: list[str]) -> dict[str, Any] | None:
    normalized_query = normalize(query)
    cssct_priority = any(normalize(term) in normalized_query for term in CSSCT_PRIORITY_TERMS)
    paid_leave_priority = any(normalize(term) in normalized_query for term in PAID_LEAVE_PRIORITY_TERMS)
    classification_priority = any(normalize(term) in normalized_query for term in CLASSIFICATION_PRIORITY_TERMS)
    inaptitude_priority = any(normalize(term) in normalized_query for term in INAPTITUDE_PRIORITY_TERMS)
    overtime_counter_priority = any(normalize(term) in normalized_query for term in OVERTIME_COUNTER_PRIORITY_TERMS)
    remuneration_query = any(normalize(term) in normalized_query for term in REMUNERATION_QUERY_TERMS)
    if paid_leave_priority:
        for profile in SEARCH_PROFILES:
            if normalize(profile["name"]) == "paie / conges payes / indemnite de conges":
                return profile
    if classification_priority:
        for profile in SEARCH_PROFILES:
            if normalize(profile["name"]) == "classification / emploi / carriere / coefficient":
                return profile
    if inaptitude_priority:
        for profile in SEARCH_PROFILES:
            if normalize(profile["name"]) == "inaptitude / reclassement / sante au travail":
                return profile
    if overtime_counter_priority:
        for profile in SEARCH_PROFILES:
            if normalize(profile["name"]) == "temps de travail / heures supplementaires / compteurs":
                return profile
    if cssct_priority and not remuneration_query:
        for profile in SEARCH_PROFILES:
            if normalize(profile["name"]) == "cssct / securite process / maintenance":
                return profile

    best_profile = None
    best_score = 0
    for profile in SEARCH_PROFILES:
        score = 0
        for trigger in profile["triggers"]:
            normalized_trigger = normalize(trigger)
            if " " in normalized_trigger and normalized_trigger in normalized_query:
                score += 4
            elif normalized_trigger in query_tokens:
                score += 2
            elif normalized_trigger in normalized_query:
                score += 1
        if score > best_score:
            best_profile = profile
            best_score = score
    return best_profile if best_score > 0 else None


def chunk_title_haystack(chunk: dict[str, Any]) -> str:
    values = [
        chunk.get("filename", ""),
        chunk.get("relative_path", ""),
    ]
    return normalize(" ".join(values))


def token_positions(value: str) -> dict[str, list[int]]:
    positions: dict[str, list[int]] = defaultdict(list)
    for index, token in enumerate(tokenize(value)):
        positions[token].append(index)
    return positions


def proximity_score(text: str, query_tokens: list[str]) -> tuple[float, str | None]:
    significant_tokens = [token for token in query_tokens if token not in WEAK_QUERY_TOKENS]
    significant_tokens = list(dict.fromkeys(significant_tokens))
    if len(significant_tokens) < 2:
        return 0.0, None
    positions = token_positions(text)
    available = [token for token in significant_tokens if positions.get(token)]
    if len(available) < 2:
        return 0.0, None

    best_window = None
    first_token = available[0]
    for start_position in positions[first_token][:80]:
        window_positions = [start_position]
        for token in available[1:]:
            nearest = min(positions[token], key=lambda item: abs(item - start_position))
            window_positions.append(nearest)
        window = max(window_positions) - min(window_positions)
        best_window = window if best_window is None else min(best_window, window)

    if best_window is None:
        return 0.0, None
    if len(available) == len(significant_tokens) and best_window <= 8:
        return 42.0, f"mots principaux très proches (fenêtre {best_window})"
    if len(available) == len(significant_tokens) and best_window <= 18:
        return 30.0, f"mots principaux proches (fenêtre {best_window})"
    if best_window <= 35:
        return 16.0, f"mots principaux présents dans un même passage (fenêtre {best_window})"
    return 6.0, "mots principaux présents mais éloignés"


def phrase_hits(haystack: str, phrases: list[str]) -> list[str]:
    hits = []
    for phrase in phrases:
        normalized_phrase = normalize(phrase)
        if normalized_phrase and normalized_phrase in haystack:
            hits.append(phrase)
    return hits


def topic_score(chunk: dict[str, Any], profile: dict[str, Any] | None) -> tuple[float, list[str]]:
    if not profile:
        return 0.0, []
    topics = [chunk.get("primary_topic")] + chunk.get("secondary_topics", [])
    score = 0.0
    reasons = []
    seen_topics = set()
    for topic in topics:
        if not topic:
            continue
        normalized_topic = normalize(topic)
        if normalized_topic in seen_topics:
            continue
        seen_topics.add(normalized_topic)
        for expected, bonus in profile.get("topic_bonus", {}).items():
            if normalized_topic == normalize(expected):
                score += bonus
                reasons.append(f"thème {topic}: +{bonus}")
    cap = profile.get("theme_bonus_cap")
    if cap and score > cap:
        reasons.append(f"bonus thème plafonné à +{cap}")
        score = float(cap)
    return score, reasons


def type_score(chunk: dict[str, Any], profile: dict[str, Any] | None) -> tuple[float, list[str]]:
    if not profile:
        return 0.0, []
    document_type = chunk.get("document_type", "")
    for expected, bonus in profile.get("doc_type_bonus", {}).items():
        if normalize(document_type) == normalize(expected):
            return float(bonus), [f"type {document_type}: +{bonus}"]
    return 0.0, []


def title_score(title_haystack: str, profile: dict[str, Any] | None, exact_query: str) -> tuple[float, list[str]]:
    score = 0.0
    reasons = []
    normalized_query = normalize(exact_query)
    if normalized_query and normalized_query in title_haystack:
        score += 55
        reasons.append("expression exacte dans le titre/chemin: +55")
    if profile:
        hits = phrase_hits(title_haystack, profile.get("title_terms", []))
        if hits:
            bonus = min(70, 30 * len(hits))
            score += bonus
            reasons.append(f"titre/chemin cohérent ({', '.join(hits[:3])}): +{bonus}")
    return score, reasons


def non_relevant_penalty(chunk: dict[str, Any], title_haystack: str, profile: dict[str, Any] | None, clear_context: bool) -> tuple[float, list[str]]:
    if not profile:
        return 0.0, []
    penalty = 0.0
    reasons = []
    multiplier = 0.7 if clear_context else 1.0

    topics = [chunk.get("primary_topic")] if clear_context else [chunk.get("primary_topic")] + chunk.get("secondary_topics", [])
    for topic in topics:
        if not topic:
            continue
        for expected, value in profile.get("penalty_topics", {}).items():
            if normalize(topic) == normalize(expected):
                adjusted = round(value * multiplier, 2)
                penalty += adjusted
                reasons.append(f"thème peu pertinent {topic}: -{adjusted}")

    title_hits = phrase_hits(title_haystack, profile.get("penalty_title_terms", []))
    if title_hits:
        value = 70 if "nao" in {normalize(hit) for hit in title_hits} else min(55, 18 * len(title_hits))
        value = round(value * multiplier, 2)
        penalty += value
        reasons.append(f"titre potentiellement hors sujet sans passage métier clair ({', '.join(title_hits[:3])}): -{value}")
    if clear_context and reasons:
        reasons.append("pénalité réduite : le passage parle clairement du sujet recherché")
    return penalty, reasons


def score_chunk_details(chunk: dict[str, Any], query_tokens: list[str], exact_query: str) -> dict[str, Any]:
    text = chunk.get("text", "")
    normalized_text = normalize(text)
    title_haystack = chunk_title_haystack(chunk)
    profile = select_search_profile(exact_query, query_tokens)
    profile_name = profile["name"] if profile else "générique"
    counts = Counter(tokenize(text))

    lexical = 0.0
    lexical_reasons = []
    for token in query_tokens:
        if token in counts:
            weight = 2 if token in WEAK_QUERY_TOKENS else 7
            gain = weight + min(counts[token], 6)
            lexical += gain
            lexical_reasons.append(f"{token}: +{round(gain, 2)}")

    exact_expression_bonus = 0.0
    exact_reasons = []
    normalized_query = normalize(exact_query)
    if normalized_query and normalized_query in normalized_text:
        exact_expression_bonus += 80
        exact_reasons.append("expression exacte dans le passage: +80")

    proximity_bonus, proximity_reason = proximity_score(text, query_tokens)
    synonym_bonus = 0.0
    synonym_reasons = []
    if profile:
        text_hits = phrase_hits(normalized_text, profile.get("synonym_phrases", []))
        text_hits = [hit for hit in text_hits if normalize(hit) != normalized_query]
        if text_hits:
            synonym_bonus += min(95, 32 * len(text_hits))
            synonym_reasons.append(f"synonymes métier dans le passage ({', '.join(text_hits[:4])}): +{round(synonym_bonus, 2)}")
        title_hits = phrase_hits(title_haystack, profile.get("synonym_phrases", []))
        if title_hits:
            title_synonym_bonus = min(45, 20 * len(title_hits))
            synonym_bonus += title_synonym_bonus
            synonym_reasons.append(f"synonymes métier dans le titre ({', '.join(title_hits[:3])}): +{title_synonym_bonus}")

    theme_bonus, theme_reasons = topic_score(chunk, profile)
    doc_type_bonus, type_reasons = type_score(chunk, profile)
    title_bonus, title_reasons = title_score(title_haystack, profile, exact_query)
    article_bonus = 4.0 if (lexical + exact_expression_bonus + synonym_bonus > 0 and chunk.get("article")) else 0.0
    clear_context = bool(exact_expression_bonus or synonym_bonus or proximity_bonus >= 16)
    penalty, penalty_reasons = non_relevant_penalty(chunk, title_haystack, profile, clear_context)
    total = max(
        0.0,
        lexical
        + exact_expression_bonus
        + proximity_bonus
        + synonym_bonus
        + theme_bonus
        + doc_type_bonus
        + title_bonus
        + article_bonus
        - penalty,
    )

    reasons = []
    if profile:
        reasons.append(f"profil détecté: {profile_name}")
    reasons.extend(lexical_reasons[:5])
    reasons.extend(exact_reasons)
    if proximity_reason:
        reasons.append(f"proximité: {proximity_reason}")
    reasons.extend(synonym_reasons)
    reasons.extend(theme_reasons)
    reasons.extend(type_reasons)
    reasons.extend(title_reasons)
    if article_bonus:
        reasons.append("passage structuré en article: +4")
    reasons.extend(penalty_reasons)

    return {
        "total": round(total, 2),
        "lexical": round(lexical, 2),
        "exact_expression_bonus": round(exact_expression_bonus, 2),
        "proximity_bonus": round(proximity_bonus, 2),
        "synonym_bonus": round(synonym_bonus, 2),
        "theme_bonus": round(theme_bonus, 2),
        "document_type_bonus": round(doc_type_bonus, 2),
        "title_bonus": round(title_bonus, 2),
        "article_bonus": round(article_bonus, 2),
        "non_relevant_penalty": round(penalty, 2),
        "profile": profile_name,
        "reasons": reasons or ["correspondance lexicale simple"],
    }


def search_index(args: argparse.Namespace, save: bool = True, quiet: bool = False) -> dict[str, Any]:
    ensure_dirs()
    chunks = read_jsonl(INDEX_DIR / "chunks.private.jsonl")
    if not chunks:
        raise SystemExit("Aucun index local. Lancer update ou index.")

    query = args.query or ""
    query_tokens = tokenize(query)
    if not query_tokens:
        raise SystemExit("Requête vide.")

    results = []
    for chunk in chunks:
        if args.theme and args.theme != chunk.get("primary_topic") and args.theme not in chunk.get("secondary_topics", []):
            continue
        if args.doc_type and args.doc_type != chunk.get("document_type"):
            continue
        if args.document_id and args.document_id != chunk.get("document_id"):
            continue
        details = score_chunk_details(chunk, query_tokens, query)
        score = details["total"]
        if score <= 0:
            continue
        results.append((score, chunk, details))

    results.sort(key=lambda item: item[0], reverse=True)
    selected = results[: args.limit]
    sources = [format_source(score, chunk, query_tokens, details) for score, chunk, details in selected]
    confidence = "fort" if selected and selected[0][0] >= 35 else "moyen" if selected else "faible"
    response = {
        "question": query,
        "provisional_answer": "Recherche documentaire locale uniquement. Les passages ci-dessous doivent être analysés juridiquement avant conclusion.",
        "confidence_level": confidence,
        "sources_used": sources,
        "points_to_verify": [
            "Vérifier si le document est toujours applicable.",
            "Vérifier s'il existe un avenant ou un texte plus récent.",
            "Croiser avec la convention collective, la loi et la jurisprudence si nécessaire.",
        ],
        "possible_conflicts": [],
        "potentially_linked_newer_document": [],
        "recommended_human_action": "Relire les sources citées et valider la portée avant utilisation.",
        "security_notice": "Private search result. Do not commit.",
    }
    if save:
        try_write_json(SEARCH_DIR / f"search-{safe_stamp()}.private.json", response)
    if not quiet:
        print_search_response(response)
    return response


def format_source(score: float, chunk: dict[str, Any], query_tokens: list[str], score_details: dict[str, Any] | None = None) -> dict[str, Any]:
    text = chunk["text"]
    excerpt = best_excerpt(text, query_tokens)
    return {
        "document": chunk["filename"],
        "document_id": chunk["document_id"],
        "page": chunk.get("page"),
        "article_or_section": chunk.get("article") or chunk.get("section"),
        "location": citation_location(chunk),
        "excerpt": excerpt,
        "match_score": round(score, 2),
        "ranking_profile": score_details.get("profile") if score_details else None,
        "ranking_reasons": score_details.get("reasons", [])[:8] if score_details else [],
        "chunk_id": chunk["chunk_id"],
        "source_quality_warning": chunk.get("source_quality_warning"),
    }


def citation_location(chunk: dict[str, Any]) -> str:
    parts = []
    if chunk.get("page"):
        parts.append(f"Page {chunk['page']}")
    if chunk.get("article"):
        parts.append(chunk["article"])
    elif chunk.get("section"):
        parts.append(chunk["section"])
    return " - ".join(parts) if parts else "LOCALISATION NON DÉTERMINÉE"


def best_excerpt(text: str, query_tokens: list[str], length: int = 480) -> str:
    normalized = normalize(text)
    positions = [normalized.find(token) for token in query_tokens if normalized.find(token) >= 0]
    start = max(min(positions) - length // 3, 0) if positions else 0
    excerpt = text[start : start + length].strip()
    excerpt = re.sub(r"\s+", " ", excerpt)
    if start > 0:
        excerpt = "..." + excerpt
    if start + length < len(text):
        excerpt += "..."
    return excerpt


def print_search_response(response: dict[str, Any]) -> None:
    print(f"QUESTION: {response['question']}")
    print(f"NIVEAU DE CONFIANCE: {response['confidence_level']}")
    print(f"SOURCES TROUVÉES: {len(response['sources_used'])}")
    for source in response["sources_used"][:5]:
        print(f"- {source['document']} | {source['location']} | score {source['match_score']}")
        if source.get("source_quality_warning"):
            print(f"  avertissement: {source['source_quality_warning']}")


def search_debug(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    chunks = read_jsonl(INDEX_DIR / "chunks.private.jsonl")
    if not chunks:
        raise SystemExit("Aucun index local. Lancer update ou index.")

    query = args.query or ""
    query_tokens = tokenize(query)
    if not query_tokens:
        raise SystemExit("Requête vide.")

    rows = []
    for chunk in chunks:
        if args.theme and args.theme != chunk.get("primary_topic") and args.theme not in chunk.get("secondary_topics", []):
            continue
        if args.doc_type and args.doc_type != chunk.get("document_type"):
            continue
        if args.document_id and args.document_id != chunk.get("document_id"):
            continue
        details = score_chunk_details(chunk, query_tokens, query)
        if details["total"] <= 0:
            continue
        rows.append((details["total"], chunk, details))
    rows.sort(key=lambda item: item[0], reverse=True)
    selected = rows[: args.limit]

    print(f"SEARCH DEBUG: {query}")
    print(f"Résultats affichés: {len(selected)} / {len(rows)}")
    for index, (score, chunk, details) in enumerate(selected, start=1):
        print(f"\n#{index} {chunk.get('filename')} | {citation_location(chunk)}")
        print(f"score total: {score}")
        print(f"score lexical: {details['lexical']}")
        print(f"bonus expression exacte: {details['exact_expression_bonus']}")
        print(f"bonus proximité: {details['proximity_bonus']}")
        print(f"bonus synonymes métier: {details['synonym_bonus']}")
        print(f"bonus thème: {details['theme_bonus']}")
        print(f"bonus type document: {details['document_type_bonus']}")
        print(f"bonus titre: {details['title_bonus']}")
        print(f"pénalité thème non pertinent: -{details['non_relevant_penalty']}")
        print("raisons:")
        for reason in details["reasons"][:10]:
            print(f"- {reason}")
    return {
        "query": query,
        "results_count": len(rows),
        "displayed": len(selected),
        "security_notice": "Local debug only. Do not commit generated reports.",
    }


def run_update(args: argparse.Namespace) -> None:
    scan_corpus(args)
    extract_documents(args)
    build_index(args)


def run_tests(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    rows = []
    for query in BUSINESS_TESTS:
        test_args = argparse.Namespace(query=query, limit=5, theme=None, doc_type=None, document_id=None)
        try:
            response = search_index(test_args, save=False, quiet=True)
            rows.append(
                {
                    "query": query,
                    "result_count": len(response["sources_used"]),
                    "confidence_level": response["confidence_level"],
                    "has_citation": any(item.get("excerpt") for item in response["sources_used"]),
                    "has_page": any(item.get("page") for item in response["sources_used"]),
                    "has_article_or_section": any(item.get("article_or_section") for item in response["sources_used"]),
                }
            )
        except SystemExit:
            rows.append({"query": query, "result_count": 0, "confidence_level": "faible", "has_citation": False, "has_page": False, "has_article_or_section": False})
    report = {
        "generated_at": now_iso(),
        "tests": rows,
        "coverage": {
            "queries": len(rows),
            "queries_with_results": sum(1 for row in rows if row["result_count"] > 0),
            "queries_with_page": sum(1 for row in rows if row["has_page"]),
            "queries_with_article_or_section": sum(1 for row in rows if row["has_article_or_section"]),
        },
        "security_notice": "Private business test report. Do not commit.",
    }
    write_json(TEST_DIR / f"business-tests-{safe_stamp()}.private.json", report)
    print(f"Tests métier: {report['coverage']['queries']} | Avec résultats: {report['coverage']['queries_with_results']} | Avec page: {report['coverage']['queries_with_page']}")
    return report


def run_missing(args: argparse.Namespace) -> dict[str, Any]:
    query = args.query or "situation à préciser"
    response = {
        "question": query,
        "before_continuing_request": [
            "Décrire précisément les faits ou le sujet CSE.",
            "Indiquer les dates exactes utiles.",
            "Joindre le document de direction si un texte est cité.",
            "Vérifier si un accord ou avenant local plus récent existe.",
            "Préciser si le sujet relève aussi de la convention collective, du Code du travail ou d'une source institutionnelle.",
        ],
        "human_controls": ["correction humaine", "non applicable", "ajout d'une note terrain", "validation document suffisant"],
        "security_notice": "Private missing-information helper. Do not commit.",
    }
    write_json(SEARCH_DIR / f"missing-{safe_stamp()}.private.json", response)
    print("AVANT DE POURSUIVRE, DEMANDER EN PRIORITÉ :")
    for item in response["before_continuing_request"]:
        print(f"- {item}")
    return response


def ocr_status_summary(inventory: dict[str, Any]) -> dict[str, Any]:
    documents = [doc for doc in inventory.get("documents", []) if doc.get("change_status") != "MISSING"]
    required = ocr_required_documents(inventory)
    ocr_success = 0
    ocr_low_confidence = 0
    ocr_failed = 0
    ocr_pending = 0
    for doc in required:
        status = load_ocr_status(doc)
        if is_ocr_success(status):
            if status.get("status") == "OCR_LOW_CONFIDENCE":
                ocr_low_confidence += 1
            else:
                ocr_success += 1
        elif status and status.get("status") == "OCR_FAILED":
            ocr_failed += 1
        else:
            ocr_pending += 1
    indexed = sum(
        1
        for doc in documents
        if doc.get("extraction_status") in {"EXTRACTION_OK", "EXTRACTION_A_VERIFIER", "OCR_LOW_CONFIDENCE"}
    )
    coverage = round((indexed / len(documents)) * 100, 1) if documents else 0.0
    return {
        "documents_detected": len(documents),
        "documents_indexable": indexed,
        "ocr_required": len(required),
        "ocr_success": ocr_success,
        "ocr_low_confidence": ocr_low_confidence,
        "ocr_failed": ocr_failed,
        "ocr_pending": ocr_pending,
        "coverage_percent": coverage,
    }


def run_ocr_diagnose(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    inventory_path, _ = inventory_paths()
    inventory = load_json(inventory_path, {"documents": []})
    env = detect_ocr_environment()
    summary = ocr_status_summary(inventory)
    report = {
        "generated_at": now_iso(),
        "environment": env,
        "summary": summary,
        "installation_instructions": ocr_installation_instructions(),
        "security_notice": "Private OCR diagnostic. Do not commit.",
    }
    write_json(REPORT_DIR / f"ocr-diagnose-{safe_stamp()}.private.json", report)

    print("DIAGNOSTIC OCR LOCAL")
    print(f"OCRmyPDF: {'OK' if env['commands']['ocrmypdf'] else 'MANQUANT'}")
    print(f"Tesseract: {'OK' if env['commands']['tesseract'] else 'MANQUANT'}")
    print(f"Ghostscript: {'OK' if env['commands']['ghostscript'] else 'MANQUANT'}")
    print(f"pdftoppm: {'OK' if env['commands']['pdftoppm'] else 'MANQUANT'}")
    print(f"Langue fra: {'OK' if env['has_french'] else 'MANQUANTE'}")
    print(f"Moteur recommandé: {env['recommended_engine'] or 'aucun moteur OCR local prêt'}")
    print(
        f"Documents: {summary['documents_detected']} | indexables: {summary['documents_indexable']} | "
        f"OCR requis: {summary['ocr_required']} | couverture: {summary['coverage_percent']}%"
    )
    if not env["recommended_engine"]:
        print("OCR local non prêt. Procédure Windows :")
        for item in ocr_installation_instructions():
            print(f"- {item}")
    return report


def select_ocr_engine(args: argparse.Namespace, env: dict[str, Any]) -> str | None:
    requested = getattr(args, "engine", "auto")
    if requested == "auto":
        return env.get("recommended_engine")
    if requested == "ocrmypdf" and env.get("can_use_ocrmypdf"):
        return "ocrmypdf"
    if requested == "tesseract-pdftoppm" and env.get("can_use_tesseract_fallback"):
        return "tesseract-pdftoppm"
    return None


def run_ocr(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    inventory_path, _ = inventory_paths()
    inventory = load_json(inventory_path, None)
    env = detect_ocr_environment()
    engine = select_ocr_engine(args, env)
    lang = choose_ocr_language(getattr(args, "lang", OCR_LANG_DEFAULT), env.get("tesseract_languages", []))
    started = time.monotonic()
    report = {
        "generated_at": now_iso(),
        "engine": engine,
        "language": lang,
        "documents_to_process": 0,
        "ocr_success": 0,
        "ocr_low_confidence": 0,
        "ocr_failed": 0,
        "ocr_skipped": 0,
        "partial_or_low_confidence": 0,
        "pages_processed": 0,
        "duration_seconds": 0,
        "rows": [],
        "security_notice": "Private OCR run report. Do not commit.",
    }

    if not engine or not lang:
        report["error_message"] = "Dépendances OCR locales incomplètes ou langue française absente."
        report["installation_instructions"] = ocr_installation_instructions()
        write_json(REPORT_DIR / f"ocr-run-{safe_stamp()}.private.json", report)
        print("OCR local non disponible. Aucun document n'a été traité.")
        for item in ocr_installation_instructions():
            print(f"- {item}")
        return report

    source = source_path_from_args(args)
    if inventory is None:
        inventory = scan_corpus(args)

    candidates = ocr_required_documents(inventory)
    if args.document_id:
        candidates = [doc for doc in candidates if doc.get("document_id") == args.document_id]
    pending = []
    for doc in candidates:
        if is_ocr_success(load_ocr_status(doc)) and not args.force_ocr:
            report["ocr_skipped"] += 1
            continue
        pending.append(doc)
    if args.limit is not None:
        pending = pending[: args.limit]
    report["documents_to_process"] = len(pending)

    for doc in pending:
        source_pdf = source / doc["relative_path"]
        if engine == "ocrmypdf":
            result = run_ocrmypdf_for_doc(doc, source_pdf, env, lang)
        else:
            result = run_tesseract_fallback_for_doc(doc, source_pdf, env, lang)
        write_json(ocr_status_path(doc["document_id"]), result)

        doc["ocr_status"] = result["status"]
        doc["ocr_engine"] = result["engine"]
        doc["ocr_confidence"] = result.get("average_confidence")
        doc["ocr_confidence_status"] = result.get("confidence_status")
        doc["ocr_last_run_at"] = now_iso()
        doc["ocr_required"] = result["status"] == "OCR_FAILED"
        if result["status"] == "OCR_SUCCESS":
            report["ocr_success"] += 1
        elif result["status"] == "OCR_LOW_CONFIDENCE":
            report["ocr_low_confidence"] += 1
            report["partial_or_low_confidence"] += 1
        else:
            report["ocr_failed"] += 1
        report["pages_processed"] += result.get("page_count") or 0
        report["rows"].append(
            {
                "document_id": doc["document_id"],
                "status": result["status"],
                "engine": result["engine"],
                "page_count": result.get("page_count"),
                "char_count": result.get("char_count"),
                "average_confidence": result.get("average_confidence"),
                "confidence_status": result.get("confidence_status"),
                "error_message": result.get("error_message"),
            }
        )
        inventory["summary"] = build_quality_summary(inventory["documents"])
        write_json(inventory_path, inventory)

    report["duration_seconds"] = round(time.monotonic() - started, 2)
    write_json(REPORT_DIR / f"ocr-run-{safe_stamp()}.private.json", report)
    print(
        f"OCR local terminé | traités: {report['documents_to_process']} | succès: {report['ocr_success']} | "
        f"faible confiance: {report['ocr_low_confidence']} | échecs: {report['ocr_failed']} | pages: {report['pages_processed']}"
    )

    if report["ocr_success"] or report["ocr_low_confidence"]:
        extract_documents(args)
        build_index(args)
    return report


def diagnose_extractions(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    inventory_path, _ = inventory_paths()
    inventory = load_json(inventory_path, None)
    if inventory is None:
        raise SystemExit("Aucun inventaire local. Lancer update ou extract avant diagnose.")

    documents = [doc for doc in inventory.get("documents", []) if doc.get("change_status") != "MISSING"]
    categories = {
        "EXTRACTION_OK": [],
        "OCR_REQUIRED": [],
        "ERROR": [],
        "UNSUPPORTED": [],
        "EXTRACTION_A_VERIFIER": [],
        "PENDING": [],
    }
    for doc in documents:
        status = doc.get("extraction_status") or "PENDING"
        if doc.get("ocr_required"):
            status = "OCR_REQUIRED"
        categories.setdefault(status, []).append(doc)

    summary = {
        "generated_at": now_iso(),
        "total_documents": len(documents),
        "extraction_ok": len(categories.get("EXTRACTION_OK", [])),
        "ocr_required": len(categories.get("OCR_REQUIRED", [])),
        "technical_errors": len(categories.get("ERROR", [])),
        "unsupported_formats": len(categories.get("UNSUPPORTED", [])),
        "to_verify": len(categories.get("EXTRACTION_A_VERIFIER", [])),
        "pending": len(categories.get("PENDING", [])),
        "by_extension": dict(Counter(doc.get("extension") for doc in documents)),
        "security_notice": "Private extraction diagnostic. Do not commit.",
    }

    report = {"summary": summary, "categories": {}}
    for status, rows in categories.items():
        report["categories"][status] = [
            {
                "document_id": doc.get("document_id"),
                "filename": doc.get("filename"),
                "extension": doc.get("extension"),
                "page_count": doc.get("extraction_diagnostics", {}).get("page_count"),
                "char_count": doc.get("extraction_diagnostics", {}).get("char_count"),
                "error_message": doc.get("extraction_diagnostics", {}).get("error_message"),
                "extraction_note": doc.get("extraction_diagnostics", {}).get("extraction_note"),
            }
            for doc in rows
        ]
    write_json(REPORT_DIR / f"diagnostic-extraction-{safe_stamp()}.private.json", report)

    print("DIAGNOSTIC EXTRACTION BIBLE ACCORDS")
    print(f"Documents: {summary['total_documents']}")
    print(f"EXTRACTION_OK: {summary['extraction_ok']}")
    print(f"OCR_REQUIRED: {summary['ocr_required']}")
    print(f"ERREURS TECHNIQUES: {summary['technical_errors']}")
    print(f"FORMATS NON SUPPORTES: {summary['unsupported_formats']}")
    print(f"A VERIFIER: {summary['to_verify']}")
    if args.show_files:
        for status in ["EXTRACTION_OK", "OCR_REQUIRED", "ERROR", "UNSUPPORTED", "EXTRACTION_A_VERIFIER", "PENDING"]:
            rows = report["categories"].get(status, [])
            if not rows:
                continue
            print(f"\n{status}")
            for row in rows:
                print(
                    f"- {row['filename']} | pages={row['page_count']} | chars={row['char_count']} | "
                    f"note={row['extraction_note']}"
                )
                if row.get("error_message"):
                    print(f"  erreur={row['error_message']}")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bible Accords Sarralbe V1 - local secure pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    for command in ["scan", "extract", "index", "update"]:
        p = sub.add_parser(command)
        p.add_argument("--source", help="Chemin local privé du corpus. Sinon CFDT_NEXUS_CORPUS_PATH.")
        p.add_argument("--force", action="store_true", help="Retraiter même si inchangé.")

    p_search = sub.add_parser("search")
    p_search.add_argument("--query", required=True)
    p_search.add_argument("--limit", type=int, default=8)
    p_search.add_argument("--theme")
    p_search.add_argument("--doc-type")
    p_search.add_argument("--document-id")

    p_search_debug = sub.add_parser("search-debug")
    p_search_debug.add_argument("--query", required=True)
    p_search_debug.add_argument("--limit", type=int, default=8)
    p_search_debug.add_argument("--theme")
    p_search_debug.add_argument("--doc-type")
    p_search_debug.add_argument("--document-id")

    p_test = sub.add_parser("test")
    p_test.add_argument("--limit", type=int, default=5)

    p_missing = sub.add_parser("missing")
    p_missing.add_argument("--query", required=True)

    p_diagnose = sub.add_parser("diagnose")
    p_diagnose.add_argument("--show-files", action="store_true", help="Afficher les noms de fichiers localement. Ne pas copier vers GitHub.")

    sub.add_parser("ocr-diagnose")

    p_ocr = sub.add_parser("ocr-run")
    p_ocr.add_argument("--source", help="Chemin local privé du corpus. Sinon CFDT_NEXUS_CORPUS_PATH ou dernier chemin local mémorisé.")
    p_ocr.add_argument("--limit", type=int, default=None)
    p_ocr.add_argument("--document-id")
    p_ocr.add_argument("--engine", choices=["auto", "ocrmypdf", "tesseract-pdftoppm"], default="auto")
    p_ocr.add_argument("--lang", default=OCR_LANG_DEFAULT)
    p_ocr.add_argument("--force-ocr", action="store_true", help="Retraiter même les OCR déjà réussis.")

    return parser


def main() -> None:
    args = build_parser().parse_args()
    ensure_dirs()
    if args.command == "scan":
        scan_corpus(args)
    elif args.command == "extract":
        extract_documents(args)
    elif args.command == "index":
        build_index(args)
    elif args.command == "update":
        run_update(args)
    elif args.command == "search":
        search_index(args)
    elif args.command == "search-debug":
        search_debug(args)
    elif args.command == "test":
        run_tests(args)
    elif args.command == "missing":
        run_missing(args)
    elif args.command == "diagnose":
        diagnose_extractions(args)
    elif args.command == "ocr-diagnose":
        run_ocr_diagnose(args)
    elif args.command == "ocr-run":
        run_ocr(args)
    else:
        raise SystemExit(f"Commande inconnue: {args.command}")


if __name__ == "__main__":
    main()
