#!/usr/bin/env python
"""
CFDT Nexus local bridge:
Document / CSE topic -> Bible Accords Sarralbe.

This script is local-only. It never sends private documents to an external API and
never writes real document content into Git. Generated reports stay under
local-index/agreements/integration/.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import agreements_bible as bible


BRIDGE_DIR = bible.LOCAL_ROOT / "integration"
BRIDGE_REPORT_DIR = BRIDGE_DIR / "reports"
BRIDGE_TEST_DIR = BRIDGE_DIR / "tests"

PRUDENCE_WARNING = (
    "L'analyse automatique constitue une aide à la préparation. Vérifier les textes cités, "
    "leur date, leur champ d'application et leur articulation avec les normes supérieures "
    "avant toute position définitive en CSE, CSSCT ou négociation."
)

SOURCE_FOUND = "SOURCE LOCALE TROUVÉE"
SOURCE_TO_VERIFY = "SOURCE LOCALE À VÉRIFIER"
NO_RELEVANT_SOURCE = "AUCUNE SOURCE LOCALE PERTINENTE TROUVÉE"
NO_DIRECT_CSSCT_SOURCE = "Aucune source locale directement pertinente trouvée — analyse CSSCT à construire avec DUERP, documents techniques et informations direction."
NO_PRECISE_PAID_LEAVE_RULE = "Aucune règle locale précise identifiée dans les sources remontées. Vérification juridique externe nécessaire."
PAID_LEAVE_THEME = "paie / congés payés / indemnité de congés"
CLASSIFICATION_THEME = "classification / emploi / carrière / coefficient"
INAPTITUDE_THEME = "inaptitude / reclassement / santé au travail"
OVERTIME_COUNTER_THEME = "temps de travail / heures supplémentaires / compteurs"

PAID_LEAVE_SOURCE_MARKERS = [
    "congés payés",
    "conges payes",
    "congé payé",
    "conge paye",
    "indemnité de congés",
    "indemnite de conges",
    "indemnité compensatrice de congés",
    "indemnite compensatrice de conges",
    "règle du dixième",
    "regle du dixieme",
    "dixième",
    "dixieme",
    "règle des 10",
    "regle des 10",
    "10 %",
    "maintien de salaire",
]

PAID_LEAVE_CONTEXT_MARKERS = [
    "congés",
    "conges",
    "congé",
    "conge",
    "assiette",
    "salaire de référence",
    "salaire de reference",
    "rémunération brute de référence",
    "remuneration brute de reference",
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
]


THEME_RULES = [
    {
        "theme": "temps de travail / repos / 5x8",
        "patterns": [
            "repos entre postes",
            "repos entre deux postes",
            "repos quotidien",
            "changement de cycle",
            "cycle de travail",
            "modification des horaires",
            "horaires postés",
            "horaires postes",
            "5x8",
            "travail posté",
            "travail poste",
            "travail de nuit",
            "temps de repos",
        ],
        "queries": [
            "repos entre deux postes",
            "temps de travail 5x8 horaires postés",
            "repos quotidien travail posté",
            "travail de nuit organisation du travail",
        ],
        "comparison_points": [
            "disposition actuelle sur l'organisation du travail",
            "proposition nouvelle sur les horaires ou le repos",
            "compatibilité à vérifier avec les textes locaux 5x8 / temps de travail",
            "impact possible sur fatigue, vie familiale et sécurité",
        ],
        "questions": [
            "Quel est le changement concret demandé par rapport à l'organisation actuelle ?",
            "Quels salariés, équipes ou cycles sont concernés ?",
            "Quel délai de prévenance et quelle période de test sont prévus ?",
            "Quel impact sur le repos quotidien, le travail de nuit et la fatigue ?",
        ],
        "documents_to_request": [
            "planning actuel et projeté",
            "note de présentation détaillée",
            "analyse d'impact santé-sécurité",
            "liste des populations concernées",
        ],
    },
    {
        "theme": "astreinte",
        "patterns": [
            "astreinte",
            "intervention",
            "indemnisation des interventions",
            "régime d'astreinte",
            "regime d'astreinte",
        ],
        "queries": [
            "astreinte indemnisation interventions",
            "régime d'astreinte intervention",
            "temps d'intervention astreinte",
        ],
        "comparison_points": [
            "régime actuel d'astreinte",
            "indemnisation proposée ou modifiée",
            "articulation temps d'intervention / temps de repos",
        ],
        "questions": [
            "Quelles catégories de salariés seraient concernées ?",
            "L'indemnisation change-t-elle ?",
            "Comment le repos après intervention est-il garanti ?",
        ],
        "documents_to_request": [
            "projet d'organisation des astreintes",
            "barème d'indemnisation",
            "bilan des interventions passées",
        ],
    },
    {
        "theme": CLASSIFICATION_THEME,
        "patterns": [
            "classification",
            "coefficient",
            "niveau",
            "échelon",
            "echelon",
            "emploi",
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
        "queries": [
            "classification coefficient emploi carrière fiche de poste",
            "coefficient niveau échelon fonctions exercées responsabilités autonomie technicité",
            "évolution de poste polyvalence pesée de poste critères conventionnels",
            "classification emploi poste convention collective coefficient",
        ],
        "comparison_points": [
            "fiche de poste actuelle",
            "fonctions réellement exercées",
            "niveau d'autonomie",
            "responsabilités",
            "technicité",
            "comparaison avec salariés similaires",
            "historique des changements de poste",
            "critères conventionnels à vérifier",
            "demande de réexamen du coefficient",
        ],
        "questions": [
            "Quelle est la fiche de poste actuelle et correspond-elle aux fonctions réellement exercées ?",
            "Quel niveau d'autonomie, de responsabilité et de technicité est attendu et constaté ?",
            "Quels salariés comparables ont un coefficient ou une classification différente ?",
            "Quels critères conventionnels justifient le coefficient retenu ?",
            "Un réexamen du coefficient est-il prévu après l'évolution de poste ?",
        ],
        "documents_to_request": [
            "fiche de poste actuelle",
            "descriptif des fonctions réellement exercées",
            "historique des changements de poste",
            "grille de classification et critères conventionnels applicables",
            "comparaison anonymisée avec salariés similaires",
            "éléments justifiant le coefficient actuel",
            "demande ou réponse de réexamen du coefficient",
        ],
    },
    {
        "theme": INAPTITUDE_THEME,
        "patterns": [
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
        "queries": [
            "inaptitude reclassement médecin du travail restrictions médicales",
            "recherche de reclassement poste compatible adaptation de poste",
            "licenciement pour inaptitude impossibilité de reclassement consultation CSE",
            "santé au travail aptitude aménagement de poste reclassement",
        ],
        "comparison_points": [
            "avis du médecin du travail",
            "restrictions médicales",
            "étude de poste",
            "postes disponibles",
            "adaptations possibles",
            "formations envisageables",
            "périmètre de reclassement",
            "consultation éventuelle du CSE",
            "échanges avec le salarié",
            "traçabilité des recherches",
        ],
        "questions": [
            "Quel avis le médecin du travail a-t-il rendu et quelles restrictions sont mentionnées ?",
            "Quelle étude de poste a été réalisée ?",
            "Quels postes disponibles ou compatibles ont été recherchés ?",
            "Quelles adaptations de poste ou formations ont été étudiées ?",
            "Quelle traçabilité existe sur les échanges avec le salarié et les recherches de reclassement ?",
        ],
        "documents_to_request": [
            "avis du médecin du travail",
            "restrictions médicales",
            "étude de poste",
            "liste des postes disponibles",
            "analyse des adaptations possibles",
            "formations envisageables",
            "périmètre de reclassement",
            "éléments de consultation éventuelle du CSE",
            "échanges avec le salarié",
            "traçabilité des recherches de reclassement",
        ],
    },
    {
        "theme": OVERTIME_COUNTER_THEME,
        "patterns": [
            "heures supplémentaires",
            "heures supplementaires",
            "compteur",
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
        "queries": [
            "heures supplémentaires compteur heures récupération repos compensateur",
            "pointage badgeage temps de travail effectif heures effectuées heures payées",
            "majoration contingent modulation annualisation compteur d'heures",
            "temps de travail heures supplémentaires repos compensateur convention collective",
        ],
        "comparison_points": [
            "relevés de pointage",
            "compteurs d'heures",
            "heures validées ou refusées",
            "règles de majoration",
            "récupération",
            "contingent",
            "repos compensateur",
            "paramétrage logiciel",
            "exemples anonymisés",
            "période à contrôler",
        ],
        "questions": [
            "Quels relevés de pointage ou badgeage justifient les heures effectuées ?",
            "Quelles heures ont été validées, refusées, payées ou récupérées ?",
            "Quelles règles de majoration et de repos compensateur sont appliquées ?",
            "Quel contingent, modulation ou annualisation s'applique au périmètre concerné ?",
            "Quel paramétrage logiciel produit les compteurs transmis aux salariés ?",
        ],
        "documents_to_request": [
            "relevés de pointage",
            "compteurs d'heures",
            "liste des heures validées et refusées",
            "règles de majoration",
            "règles de récupération",
            "contingent applicable",
            "règles de repos compensateur",
            "paramétrage logiciel",
            "exemples anonymisés",
            "période à contrôler",
        ],
    },
    {
        "theme": "CSSCT / sécurité process / maintenance",
        "patterns": [
            "duerp",
            "duer",
            "rps",
            "risques psychosociaux",
            "sécurité",
            "securite",
            "sécurité process",
            "securite process",
            "prévention",
            "prevention",
            "conditions de travail",
            "maintenance",
            "pièces de rechange",
            "pieces de rechange",
            "stock pièces",
            "stock pieces",
            "pièces critiques",
            "pieces critiques",
            "climatisation",
            "analyseurs",
            "analyseurs en continu",
            "provox",
            "sncc",
            "panne",
            "scénario de panne",
            "scenario de panne",
            "continuité d'exploitation",
            "continuite d exploitation",
            "contingence",
            "plan de contingence",
            "défaillance technique",
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
        "queries": [
            "DUERP RPS sécurité process maintenance",
            "PROVOX SNCC analyseurs climatisation panne",
            "pièces de rechange pièces critiques plan de contingence",
            "conditions de travail charge mentale risques psychosociaux",
            "sécurité process risques industriels prévention maintenance",
        ],
        "comparison_points": [
            "état actuel des équipements critiques",
            "scénarios de panne et plan de contingence",
            "maintenance préventive et pièces critiques",
            "mise à jour DUERP et évaluation RPS",
            "impact sur sécurité process et conditions de travail",
        ],
        "questions": [
            "Quel est l'état réel des équipements et locaux concernés ?",
            "Quels incidents, dysfonctionnements ou alertes ont été recensés ?",
            "Quels scénarios de panne ont été évalués ?",
            "Le DUERP a-t-il été mis à jour ?",
            "Quelles mesures de prévention immédiates sont prévues ?",
        ],
        "documents_to_request": [
            "état des lieux technique",
            "liste des pièces critiques et stocks disponibles",
            "plan de contingence",
            "historique incidents et dysfonctionnements",
            "mise à jour DUERP",
            "analyse RPS et charge mentale",
            "plan de maintenance préventive",
        ],
    },
    {
        "theme": "disciplinaire / règlement intérieur",
        "patterns": [
            "sanction",
            "discipline",
            "disciplinaire",
            "avertissement",
            "mise à pied",
            "mise a pied",
            "entretien disciplinaire",
            "règlement intérieur",
            "reglement interieur",
        ],
        "queries": [
            "règlement intérieur procédure disciplinaire sanction avertissement",
            "entretien disciplinaire avertissement",
            "mise à pied disciplinaire procédure",
        ],
        "comparison_points": [
            "faits reprochés",
            "procédure prévue par le règlement intérieur",
            "sanction envisagée",
            "délais et garanties de défense",
        ],
        "questions": [
            "Quels faits précis sont reprochés et à quelle date ?",
            "Le salarié a-t-il été convoqué et informé de l'objet de l'entretien ?",
            "Quels éléments de preuve existent ?",
        ],
        "documents_to_request": [
            "convocation",
            "éléments reprochés",
            "règlement intérieur applicable",
            "témoignages ou éléments de contexte",
        ],
    },
    {
        "theme": PAID_LEAVE_THEME,
        "patterns": [
            "congés payés",
            "conges payes",
            "congé payé",
            "conge paye",
            "indemnité de congés payés",
            "indemnite de conges payes",
            "indemnité de congés",
            "indemnite de conges",
            "règle du dixième",
            "regle du dixieme",
            "dixième",
            "dixieme",
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
            "indemnité compensatrice de congés payés",
            "indemnite compensatrice de conges payes",
            "régularisation",
            "regularisation",
            "rappel de salaire",
            "année civile",
            "annee civile",
        ],
        "queries": [
            "congés payés indemnité dixième maintien de salaire",
            "indemnité de congés payés règle du dixième maintien de salaire",
            "congés payés salaire de référence assiette période de référence",
            "indemnité compensatrice congés payés régularisation rappel de salaire",
            "passage année civile congés payés période de référence acquisition",
            "temps de travail congés payés prise des congés",
            "convention collective congés payés indemnité maintien dixième",
        ],
        "comparison_points": [
            "méthode actuellement appliquée par l'entreprise",
            "date d'un éventuel changement de méthode",
            "règle du maintien de salaire",
            "règle du dixième",
            "comparaison individuelle dixième / maintien",
            "méthode la plus favorable à retenir selon le cadre applicable",
            "éléments inclus ou exclus de l'assiette",
            "période de référence et période d'acquisition",
            "impact du passage éventuel à l'année civile",
            "régularisations ou rappels de salaire éventuels",
        ],
        "questions": [
            "Quelle méthode de calcul de l'indemnité de congés payés est actuellement appliquée ?",
            "Les deux méthodes, maintien de salaire et dixième, sont-elles comparées pour chaque salarié lorsque le droit applicable l'exige ?",
            "Quels éléments de rémunération entrent dans l'assiette du dixième ?",
            "Quelle conséquence a eu le passage éventuel à l'année civile ?",
            "À quelle date le paramétrage ou la méthode de paie a-t-il changé ?",
            "Combien de salariés ont été contrôlés ?",
            "Existe-t-il des écarts défavorables et une régularisation rétroactive est-elle prévue ?",
        ],
        "documents_to_request": [
            "note détaillée de méthode de calcul",
            "règle utilisée avant et après le changement évoqué",
            "date exacte du changement",
            "exemples anonymisés de calcul",
            "comparaison dixième / maintien pour plusieurs profils",
            "éléments de rémunération intégrés et exclus de l'assiette",
            "nombre de salariés concernés",
            "montant global des écarts éventuels",
            "historique des régularisations",
            "paramétrage fonctionnel du logiciel de paie pertinent",
        ],
    },
    {
        "theme": "relations collectives / droit syndical",
        "patterns": [
            "heures de délégation",
            "heures de delegation",
            "crédit d'heures",
            "credit d'heures",
            "moyens syndicaux",
            "droit syndical",
            "mandat",
            "mandat syndical",
            "représentant du personnel",
            "representant du personnel",
            "délégué syndical",
            "delegue syndical",
            "représentant syndical",
            "representant syndical",
            "élu cse",
            "elu cse",
            "membre cse",
            "fonctionnement du cse",
            "local syndical",
            "affichage syndical",
            "réunion syndicale",
            "reunion syndicale",
            "réunions syndicales",
            "reunions syndicales",
        ],
        "queries": [
            "heures de délégation droit syndical",
            "crédit d'heures mandat représentant du personnel",
            "accord CSE moyens syndicaux",
            "représentant syndical délégué syndical",
        ],
        "comparison_points": [
            "moyens actuels des représentants",
            "heures ou crédits d'heures concernés",
            "mandats et populations concernées",
            "articulation avec accord CSE / droit syndical",
        ],
        "questions": [
            "Quels mandats ou représentants sont concernés ?",
            "Le crédit d'heures est-il modifié, déplacé ou conditionné ?",
            "La consultation du CSE ou des organisations syndicales est-elle prévue ?",
        ],
        "documents_to_request": [
            "projet de modification des moyens",
            "accord CSE ou droit syndical applicable",
            "état actuel des crédits d'heures",
        ],
    },
    {
        "theme": "rémunération / primes",
        "patterns": [
            "rémunération",
            "remuneration",
            "salaire",
            "salaires",
            "prime",
            "primes",
            "majoration",
            "dimanche",
            "jour férié",
            "jour ferie",
            "nuit",
            "intéressement",
            "interessement",
            "participation",
        ],
        "queries": [
            "rémunération salaires primes",
            "prime de nuit majoration dimanche jour férié",
            "intéressement participation épargne salariale",
        ],
        "comparison_points": [
            "disposition actuelle sur rémunération ou prime",
            "montant ou condition proposé",
            "population bénéficiaire ou exclue",
        ],
        "questions": [
            "Quel montant ou quelle formule change ?",
            "Quels salariés sont concernés ?",
            "La mesure est-elle pérenne ou temporaire ?",
        ],
        "documents_to_request": [
            "note de calcul",
            "périmètre salariés concernés",
            "texte projeté",
        ],
    },
]


SCENARIOS = [
    {
        "id": "test-1-repos-5x8",
        "kind": "cse",
        "title": "Modification du repos entre deux postes",
        "text": "La direction souhaite modifier le repos entre deux postes pour les salariés en 5x8.",
        "expected": "les textes 5x8 et temps de travail doivent remonter prioritairement",
    },
    {
        "id": "test-2-astreinte",
        "kind": "cse",
        "title": "Modification astreinte",
        "text": "La direction envisage une modification du régime d'astreinte et de l'indemnisation des interventions.",
        "expected": "l'accord Astreinte doit être prioritaire",
    },
    {
        "id": "test-3-discipline",
        "kind": "cse",
        "title": "Procédure disciplinaire",
        "text": "Un salarié fait l'objet d'une procédure disciplinaire pouvant conduire à un avertissement.",
        "expected": "le règlement intérieur doit être prioritaire",
    },
    {
        "id": "test-4-droit-syndical",
        "kind": "cse",
        "title": "Moyens de délégation",
        "text": "Modification des moyens et heures de délégation des représentants du personnel.",
        "expected": "accord CSE et textes RP/droit syndical prioritaires",
    },
    {
        "id": "test-5-prime-nuit-dimanche-ferie",
        "kind": "cse",
        "title": "Prime de nuit, dimanche et jour ferie",
        "text": "La direction souhaite revoir les primes de nuit, dimanche et jour ferie.",
        "expected": "les textes remuneration, primes et majorations doivent remonter prioritairement",
    },
    {
        "id": "test-6-cssct-provox-duerp",
        "kind": "cse",
        "title": "Fiabilité PROVOX, climatisation, pièces de rechange et mise à jour du DUERP",
        "text": "La CFDT demande un point sur l'état de la climatisation des locaux SNCC PROVOX et des analyseurs en continu, le plan de contingence et la gestion des stocks de pièces de rechange PROVOX, ainsi que les modalités de mise à jour du DUERP pour intégrer les scénarios de panne et l'évaluation des RPS associés.",
        "expected": "le profil CSSCT / sécurité process / maintenance doit être prioritaire et les documents rémunération ne doivent pas dominer",
    },
    {
        "id": "test-7-conges-payes-dixieme",
        "kind": "cse",
        "title": "Valorisation des congés payés et règle du dixième",
        "text": "La CFDT constate que la règle du dixième pour l'indemnité de congés payés semble ne plus être appliquée depuis le passage à l'année civile et que certains salariés constatent une baisse de rémunération nette. Préparer une analyse CSE complète : méthode actuelle de calcul, comparaison avec le maintien de salaire et la règle du dixième, accords locaux éventuellement concernés, populations touchées, données de paie à demander, exemples de calcul à exiger de la direction, questions CSE, relances et position CFDT à construire.",
        "expected": "le profil paie / congés payés / indemnité de congés doit être prioritaire et aucun bloc droit syndical ne doit remonter",
        "expected_theme": PAID_LEAVE_THEME,
        "forbidden_themes": ["relations collectives / droit syndical"],
        "must_contain": [
            "règle du dixième",
            "maintien de salaire",
            "comparaison",
            "données de paie",
            "assiette",
            "régularisation",
        ],
        "must_not_contain": [
            "crédit d'heures",
            "credits d'heures",
            "heures de délégation",
            "mandat syndical",
            "moyens syndicaux",
        ],
    },
    {
        "id": "test-classification-coefficient",
        "kind": "cse",
        "title": "Classification, coefficient et évolution de poste",
        "text": "La CFDT demande une analyse CSE sur un salarié dont les fonctions réellement exercées, responsabilités, autonomie et technicité semblent avoir évolué sans réexamen du coefficient. Préparer les questions à poser sur la fiche de poste actuelle, les critères conventionnels de classification, la comparaison avec salariés similaires, l'historique des changements de poste et la demande de réexamen du coefficient.",
        "expected": "le profil classification / emploi / carrière / coefficient doit être prioritaire sans classement droit syndical",
        "expected_theme": CLASSIFICATION_THEME,
        "forbidden_themes": ["relations collectives / droit syndical"],
        "allow_no_sources": True,
        "must_contain": [
            "fiche de poste actuelle",
            "fonctions réellement exercées",
            "niveau d'autonomie",
            "responsabilités",
            "technicité",
            "comparaison avec salariés similaires",
            "critères conventionnels",
            "réexamen du coefficient",
        ],
        "must_not_contain": [
            "crédit d'heures",
            "heures de délégation",
            "mandat syndical",
            "moyens syndicaux",
        ],
    },
    {
        "id": "test-inaptitude-reclassement",
        "kind": "cse",
        "title": "Inaptitude, restrictions médicales et reclassement",
        "text": "La CFDT prépare un point CSE sur une situation d'inaptitude avec avis du médecin du travail, restrictions médicales, recherche de reclassement, adaptation de poste, postes compatibles, formations envisageables, consultation éventuelle du CSE, échanges avec le salarié et traçabilité des recherches.",
        "expected": "le profil inaptitude / reclassement / santé au travail doit être prioritaire sans classement CSSCT process ni droit syndical",
        "expected_theme": INAPTITUDE_THEME,
        "forbidden_themes": ["relations collectives / droit syndical", "CSSCT / sécurité process / maintenance"],
        "allow_no_sources": True,
        "must_contain": [
            "avis du médecin du travail",
            "restrictions médicales",
            "étude de poste",
            "postes disponibles",
            "adaptations possibles",
            "formations envisageables",
            "périmètre de reclassement",
            "traçabilité des recherches",
        ],
        "must_not_contain": [
            "crédit d'heures",
            "heures de délégation",
            "mandat syndical",
            "moyens syndicaux",
        ],
    },
    {
        "id": "test-heures-supplementaires-compteurs",
        "kind": "cse",
        "title": "Heures supplémentaires, compteurs et récupération",
        "text": "La CFDT demande une analyse CSE sur des heures supplémentaires et compteurs d'heures : relevés de pointage, badgeage, temps de travail effectif, heures effectuées, heures validées ou refusées, heures payées, heures récupérées, majoration, récupération, contingent, repos compensateur, modulation, annualisation et paramétrage logiciel.",
        "expected": "le profil temps de travail / heures supplémentaires / compteurs doit être prioritaire sans classement rémunération générale ni droit syndical",
        "expected_theme": OVERTIME_COUNTER_THEME,
        "forbidden_themes": ["relations collectives / droit syndical"],
        "allow_no_sources": True,
        "must_contain": [
            "relevés de pointage",
            "compteurs",
            "heures validées",
            "heures refusées",
            "règles de majoration",
            "récupération",
            "contingent",
            "repos compensateur",
            "paramétrage logiciel",
            "période à contrôler",
        ],
        "must_not_contain": [
            "crédit d'heures",
            "heures de délégation",
            "mandat syndical",
            "moyens syndicaux",
        ],
    },
]


REQUIRED_CSE_SECTIONS = [
    "2_textes_locaux_potentiellement_concernes",
    "3_situation_actuelle_a_verifier",
    "4_points_a_comparer_avant_apres",
    "5_consequences_concretes_pour_les_salaries",
    "8_informations_manquantes",
    "10_questions_principales_a_poser_en_cse",
    "11_relances_conditionnelles",
    "14_synthese_pour_l_elu",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")


def ensure_dirs() -> None:
    bible.ensure_dirs()
    for directory in [BRIDGE_DIR, BRIDGE_REPORT_DIR, BRIDGE_TEST_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def write_private_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize(value: str) -> str:
    return bible.normalize(value)


def detect_themes(text: str) -> list[dict[str, Any]]:
    normalized = normalize(text)
    detected = []
    for rule in THEME_RULES:
        hits = []
        for pattern in rule["patterns"]:
            if normalize(pattern) in normalized:
                hits.append(pattern)
        if hits:
            detected.append(
                {
                    "theme": rule["theme"],
                    "matched_terms": hits,
                    "queries": rule["queries"],
                    "comparison_points": rule["comparison_points"],
                    "questions": rule["questions"],
                    "documents_to_request": rule["documents_to_request"],
                }
            )
    if any(normalize(item["theme"]) == "cssct / securite process / maintenance" for item in detected):
        detected = [
            item
            for item in detected
            if normalize(item["theme"]) != "relations collectives / droit syndical"
        ]
    if any(normalize(item["theme"]) == normalize(PAID_LEAVE_THEME) for item in detected):
        detected = [
            item
            for item in detected
            if normalize(item["theme"]) != "relations collectives / droit syndical"
        ]
    precise_hr_payroll_themes = {
        normalize(CLASSIFICATION_THEME),
        normalize(INAPTITUDE_THEME),
        normalize(OVERTIME_COUNTER_THEME),
    }
    if any(normalize(item["theme"]) in precise_hr_payroll_themes for item in detected):
        detected = [
            item
            for item in detected
            if normalize(item["theme"]) != "relations collectives / droit syndical"
        ]
    if any(normalize(item["theme"]) == normalize(INAPTITUDE_THEME) for item in detected):
        detected = [
            item
            for item in detected
            if normalize(item["theme"])
            not in {
                normalize(CLASSIFICATION_THEME),
                "cssct / securite process / maintenance",
            }
        ]
    return detected


def generated_queries(text: str, themes: list[dict[str, Any]]) -> list[str]:
    queries = []
    for theme in themes:
        queries.extend(theme["queries"])
    if not queries:
        queries.append(text[:180])
    seen = set()
    deduped = []
    for query in queries:
        key = normalize(query)
        if key not in seen:
            seen.add(key)
            deduped.append(query)
    return deduped


def search_bible(query: str, limit: int) -> list[dict[str, Any]]:
    chunks = bible.read_jsonl(bible.INDEX_DIR / "chunks.private.jsonl")
    query_tokens = bible.tokenize(query)
    if not query_tokens:
        return []

    rows = []
    for chunk in chunks:
        details = bible.score_chunk_details(chunk, query_tokens, query)
        if details["total"] <= 0:
            continue
        rows.append((details["total"], chunk, details))
    rows.sort(key=lambda item: item[0], reverse=True)
    sources = []
    for score, chunk, details in rows[:limit]:
        source = bible.format_source(score, chunk, query_tokens, details)
        source["source_status"] = classify_source(score, source)
        source["confidence_level"] = confidence_level(score)
        sources.append(source)
    return sources


def classify_source(score: float, source: dict[str, Any]) -> str:
    if score >= 50 and source.get("page"):
        return SOURCE_FOUND
    if score > 0:
        return SOURCE_TO_VERIFY
    return NO_RELEVANT_SOURCE


def confidence_level(score: float) -> str:
    if score >= 150:
        return "fort"
    if score >= 70:
        return "moyen"
    return "faible"


def merge_sources(searches: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    by_chunk = {}
    for search in searches:
        for source in search["sources"]:
            chunk_id = source.get("chunk_id")
            if not chunk_id:
                continue
            existing = by_chunk.get(chunk_id)
            if existing is None or source["match_score"] > existing["match_score"]:
                merged = dict(source)
                merged["matched_query"] = search["query"]
                by_chunk[chunk_id] = merged
    return sorted(by_chunk.values(), key=lambda item: item["match_score"], reverse=True)[:limit]


def main_subject(text: str, themes: list[dict[str, Any]]) -> str:
    return themes[0]["theme"] if themes else "sujet à qualifier"


def inferred_intent(text: str, themes: list[dict[str, Any]]) -> str:
    if not themes:
        return "Le document ou point semble présenter un sujet nécessitant qualification humaine."
    theme_names = ", ".join(theme["theme"] for theme in themes[:3])
    return f"Le document ou point semble présenter ou modifier un sujet lié à : {theme_names}."


def comparison_points(themes: list[dict[str, Any]]) -> list[str]:
    points = []
    for theme in themes:
        points.extend(theme["comparison_points"])
    base = [
        "disposition actuelle",
        "proposition nouvelle",
        "différence détectée",
        "compatibilité à vérifier",
        "articulation à analyser",
        "conséquence possible",
        "bénéficiaire probable du changement",
        "risque salarié",
        "avantage éventuel",
        "point ambigu",
    ]
    return dedupe(points + base)


def questions_for(themes: list[dict[str, Any]]) -> list[str]:
    questions = []
    for theme in themes:
        questions.extend(theme["questions"])
    return dedupe(questions + ["Quelle est la base juridique ou conventionnelle invoquée par la direction ?"])


def documents_to_request(themes: list[dict[str, Any]]) -> list[str]:
    docs = []
    for theme in themes:
        docs.extend(theme["documents_to_request"])
    return dedupe(docs + ["texte projeté", "note d'impact", "calendrier de mise en œuvre"])


def dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        key = normalize(value)
        if key and key not in seen:
            seen.add(key)
            result.append(value)
    return result


def build_document_analysis(title: str, text: str, limit: int) -> dict[str, Any]:
    analysis_text = f"{title}\n{text}".strip()
    themes = detect_themes(analysis_text)
    queries = generated_queries(analysis_text, themes)
    searches = [{"query": query, "sources": search_bible(query, limit)} for query in queries]
    sources = merge_sources(searches, limit)
    source_status = sources[0]["source_status"] if sources else NO_RELEVANT_SOURCE
    return {
        "kind": "document-analysis",
        "generated_at": now_iso(),
        "title": title,
        "prudence_warning": PRUDENCE_WARNING,
        "source_status": source_status,
        "A_sujet_principal": main_subject(text, themes),
        "B_ce_que_le_document_semble_vouloir_modifier_ou_presenter": inferred_intent(text, themes),
        "C_textes_locaux_potentiellement_concernes": sources,
        "D_points_de_comparaison": comparison_points(themes),
        "detected_themes": themes,
        "generated_queries": queries,
        "points_to_verify": [
            "Vérifier la date et le champ d'application des textes cités.",
            "Vérifier s'il existe un accord, avenant ou usage plus récent.",
            "Ne pas conclure à une violation juridique sans analyse humaine.",
        ],
        "security_notice": "Private local analysis. Do not commit generated reports.",
    }


def theme_names(themes: list[dict[str, Any]]) -> list[str]:
    return [theme["theme"] for theme in themes]


def has_theme(themes: list[dict[str, Any]], *needles: str) -> bool:
    haystack = normalize(" ".join(theme_names(themes)))
    return any(normalize(needle) in haystack for needle in needles)


def has_exact_theme(themes: list[dict[str, Any]], theme_name: str) -> bool:
    return any(normalize(theme["theme"]) == normalize(theme_name) for theme in themes)


def is_worktime_rest_theme(themes: list[dict[str, Any]]) -> bool:
    return has_exact_theme(themes, "temps de travail / repos / 5x8")


def is_cssct_theme(themes: list[dict[str, Any]]) -> bool:
    return has_theme(themes, "CSSCT / sécurité process / maintenance")


def is_paid_leave_theme(themes: list[dict[str, Any]]) -> bool:
    return has_theme(themes, PAID_LEAVE_THEME, "congés payés", "indemnité de congés")


def is_classification_theme(themes: list[dict[str, Any]]) -> bool:
    return has_theme(themes, CLASSIFICATION_THEME)


def is_inaptitude_theme(themes: list[dict[str, Any]]) -> bool:
    return has_theme(themes, INAPTITUDE_THEME)


def is_overtime_counter_theme(themes: list[dict[str, Any]]) -> bool:
    return has_theme(themes, OVERTIME_COUNTER_THEME)


def paid_leave_specific_source(source: dict[str, Any]) -> bool:
    haystack = normalize(
        " ".join(
            [
                str(source.get("document") or ""),
                str(source.get("article_or_section") or ""),
                str(source.get("location") or ""),
                str(source.get("excerpt") or ""),
                " ".join(str(reason) for reason in source.get("ranking_reasons", [])),
            ]
        )
    )
    if any(normalize(marker) in haystack for marker in PAID_LEAVE_SOURCE_MARKERS):
        return True
    has_leave = any(normalize(marker) in haystack for marker in ["congés", "conges", "congé", "conge"])
    has_pay_context = any(
        normalize(marker) in haystack
        for marker in PAID_LEAVE_CONTEXT_MARKERS
        if normalize(marker) not in {"conges", "conge"}
    )
    return has_leave and has_pay_context


def is_remuneration_source(source: dict[str, Any]) -> bool:
    haystack = normalize(
        " ".join(
            [
                str(source.get("document") or ""),
                str(source.get("matched_query") or ""),
                str(source.get("ranking_profile") or ""),
                " ".join(str(reason) for reason in source.get("ranking_reasons", [])),
            ]
        )
    )
    remuneration_terms = [
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
    ]
    return any(term in haystack for term in remuneration_terms)


def cse_sources_for_theme(sources: list[dict[str, Any]], themes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if is_paid_leave_theme(themes):
        return [source for source in sources if paid_leave_specific_source(source)]
    if not is_cssct_theme(themes):
        return sources
    return [source for source in sources if not is_remuneration_source(source)]


def cse_source_status(sources: list[dict[str, Any]], themes: list[dict[str, Any]], fallback: str) -> str:
    if is_paid_leave_theme(themes) and not sources:
        return NO_PRECISE_PAID_LEAVE_RULE
    if is_cssct_theme(themes) and not sources:
        return NO_DIRECT_CSSCT_SOURCE
    if sources:
        return sources[0].get("source_status") or fallback
    return fallback


def source_reference(source: dict[str, Any]) -> str:
    parts = [source.get("document") or "document local"]
    if source.get("page"):
        parts.append(f"page {source.get('page')}")
    if source.get("article_or_section"):
        parts.append(str(source.get("article_or_section")))
    return " / ".join(parts)


def role_probable(source: dict[str, Any], themes: list[dict[str, Any]], index: int) -> str:
    haystack = normalize(
        " ".join(
            str(source.get(key) or "")
            for key in ["document", "matched_query", "ranking_profile", "article_or_section"]
        )
    )
    main_theme = normalize(theme_names(themes)[0]) if themes else ""
    if is_paid_leave_theme(themes):
        if "convention" in haystack or "ccnic" in haystack:
            return "convention collective à vérifier pour congés payés"
        if "temps de travail" in haystack or "conges" in haystack or "conge" in haystack:
            return "texte congés payés ou temps de travail à vérifier"
        if "remuneration" in haystack or "paie" in haystack or "salaire" in haystack:
            return "document paie à vérifier uniquement s'il traite explicitement les congés payés"
        return "source congés payés à vérifier"
    if "reglement" in haystack or "interieur" in haystack:
        return "règlement intérieur"
    if "convention" in haystack or "ccnic" in haystack:
        return "convention collective"
    if "historique" in haystack or "ancien" in haystack:
        return "document historique"
    if "remuneration" not in main_theme and any(
        term in haystack
        for term in ["nao", "paie", "salaire", "prime", "primes", "cet", "pereco", "pee", "forfait jours", "interessement", "participation"]
    ):
        return "document potentiellement non prioritaire"
    if index == 0 and source.get("source_status") == SOURCE_FOUND:
        return "texte principal"
    if index <= 2 and source.get("source_status") == SOURCE_FOUND:
        return "texte complémentaire"
    return "texte à vérifier"


def enrich_sources_for_cse(sources: list[dict[str, Any]], themes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = []
    for index, source in enumerate(sources):
        reasons = source.get("ranking_reasons") or []
        enriched.append(
            {
                "document": source.get("document"),
                "page": source.get("page"),
                "article": source.get("article_or_section"),
                "score": source.get("match_score"),
                "raison_de_pertinence": "; ".join(reasons[:3]) if reasons else "Correspondance locale à vérifier.",
                "role_probable_du_document": role_probable(source, themes, index),
                "statut_source": source.get("source_status"),
                "niveau_de_confiance": source.get("confidence_level"),
                "requete_associee": source.get("matched_query"),
            }
        )
    return enriched


def cse_confidence(sources: list[dict[str, Any]]) -> str:
    if not sources:
        return "faible"
    best_score = max(float(source.get("match_score") or 0) for source in sources)
    if best_score >= 150:
        return "fort"
    if best_score >= 70:
        return "moyen"
    return "faible"


def direction_intent(text: str, themes: list[dict[str, Any]]) -> str:
    if not themes:
        return "Le changement exact doit être précisé par la direction."
    if is_classification_theme(themes):
        return (
            "Le point semble porter sur la classification, le coefficient, l'emploi tenu ou l'évolution de poste. "
            "Il faut objectiver les fonctions réellement exercées, l'autonomie, les responsabilités, la technicité "
            "et les critères conventionnels avant toute demande de réexamen."
        )
    if is_inaptitude_theme(themes):
        return (
            "Le point semble porter sur une situation d'inaptitude, de restrictions médicales ou de reclassement. "
            "La priorité est de vérifier l'avis du médecin du travail, l'étude de poste, les adaptations possibles "
            "et la traçabilité des recherches de reclassement."
        )
    if is_overtime_counter_theme(themes):
        return (
            "Le point semble porter sur les heures supplémentaires, compteurs d'heures, récupérations ou majorations. "
            "Il faut rapprocher pointage, heures effectuées, heures validées, heures payées ou récupérées, contingent "
            "et paramétrage logiciel."
        )
    if is_cssct_theme(themes):
        return (
            "Le point semble porter sur la fiabilité d'équipements critiques, la maintenance, "
            "la continuité d'exploitation, la mise à jour du DUERP et l'évaluation des RPS. "
            "L'état réel des installations, les scénarios de panne et les mesures immédiates doivent être précisés."
        )
    if is_paid_leave_theme(themes):
        return (
            "Le point semble porter sur le calcul de l'indemnité de congés payés : méthode actuellement appliquée, "
            "comparaison entre maintien de salaire et règle du dixième, assiette de calcul, période de référence "
            "et éventuel impact d'un passage à l'année civile. La règle locale précise et le paramétrage paie doivent être vérifiés."
        )
    if is_worktime_rest_theme(themes):
        return (
            "La direction semble vouloir modifier l'organisation du repos, des horaires ou du cycle 5x8. "
            "Le changement exact doit être précisé par la direction."
        )
    if has_theme(themes, "astreinte"):
        return (
            "La direction semble vouloir modifier le régime d'astreinte, l'organisation des interventions "
            "ou leur indemnisation. Les modalités exactes doivent être précisées."
        )
    if has_theme(themes, "disciplinaire"):
        return (
            "Le sujet semble porter sur une procédure disciplinaire ou sur l'application du règlement intérieur. "
            "Les faits, délais et garanties de défense doivent être précisés."
        )
    if has_theme(themes, "droit syndical", "relations collectives"):
        return (
            "La direction semble vouloir modifier ou encadrer les moyens des représentants du personnel. "
            "Le périmètre exact des mandats et droits concernés doit être précisé."
        )
    if has_theme(themes, "rémunération", "primes"):
        return (
            "La direction semble vouloir modifier une prime, une majoration ou une modalité de rémunération collective. "
            "Le montant, les bénéficiaires et la durée doivent être précisés."
        )
    return "Le changement exact doit être précisé par la direction."


def current_situation_checks(themes: list[dict[str, Any]], sources: list[dict[str, Any]]) -> list[str]:
    ref = source_reference(sources[0]) if sources else "une source locale à identifier"
    checks = []
    if is_classification_theme(themes):
        checks.extend(
            [
                f"À vérifier dans {ref} : fiche de poste actuelle et classification/coefficient retenus.",
                f"À vérifier dans {ref} : fonctions réellement exercées, responsabilités, autonomie et technicité.",
                f"À vérifier dans {ref} : comparaison avec des salariés occupant des postes similaires.",
                f"À vérifier dans {ref} : historique des évolutions de poste, polyvalence et changements de périmètre.",
                f"À vérifier dans {ref} : critères conventionnels applicables et possibilité de réexamen du coefficient.",
            ]
        )
    if is_inaptitude_theme(themes):
        checks.extend(
            [
                f"À vérifier dans {ref} : avis du médecin du travail et restrictions médicales mentionnées.",
                f"À vérifier dans {ref} : étude de poste et analyse des adaptations possibles.",
                f"À vérifier dans {ref} : postes disponibles, postes compatibles et formations envisageables.",
                f"À vérifier dans {ref} : périmètre de reclassement et traçabilité des recherches.",
                f"À vérifier dans {ref} : échanges avec le salarié et consultation éventuelle du CSE si requise.",
            ]
        )
    if is_overtime_counter_theme(themes):
        checks.extend(
            [
                f"À vérifier dans {ref} : relevés de pointage, badgeage et compteurs d'heures.",
                f"À vérifier dans {ref} : heures effectuées, validées, refusées, payées ou récupérées.",
                f"À vérifier dans {ref} : règles de majoration, contingent et repos compensateur.",
                f"À vérifier dans {ref} : modulation, annualisation ou temps de travail effectif applicables.",
                f"À vérifier dans {ref} : paramétrage logiciel et période à contrôler.",
            ]
        )
    if is_cssct_theme(themes):
        checks.extend(
            [
                f"À vérifier dans {ref} ou dans les documents techniques : état réel des locaux SNCC/PROVOX et analyseurs.",
                f"À vérifier dans {ref} ou dans les documents techniques : incidents, dysfonctionnements et alertes recensés.",
                f"À vérifier dans {ref} ou dans les documents techniques : stock de pièces critiques, délais de réapprovisionnement et plan de contingence.",
                f"À vérifier dans {ref} ou dans le DUERP : scénarios de panne, risques sécurité process et RPS associés.",
            ]
        )
    if is_paid_leave_theme(themes):
        if not sources:
            checks.append(NO_PRECISE_PAID_LEAVE_RULE)
        checks.extend(
            [
                f"À vérifier dans {ref} : méthode actuellement appliquée pour l'indemnité de congés payés.",
                f"À vérifier dans {ref} : date exacte d'un éventuel changement de méthode ou de paramétrage paie.",
                f"À vérifier dans {ref} : règle du maintien de salaire et règle du dixième applicables au périmètre concerné.",
                f"À vérifier dans {ref} : comparaison individuelle des deux méthodes et méthode la plus favorable à retenir selon le cadre applicable.",
                f"À vérifier dans {ref} : éléments inclus ou exclus de l'assiette de calcul, notamment primes variables et éléments propres aux postés.",
                f"À vérifier dans {ref} : période de référence, période d'acquisition, prise des congés et impact éventuel du passage à l'année civile.",
                f"À vérifier dans {ref} : régularisations ou rappels de salaire déjà réalisés ou à prévoir.",
            ]
        )
    if is_worktime_rest_theme(themes):
        checks.extend(
            [
                f"À vérifier dans {ref} : règle actuelle de repos et éventuelles dérogations.",
                f"À vérifier dans {ref} : cycle actuel, salariés concernés et délai de prévenance.",
                f"À vérifier dans {ref} : garanties, contreparties et articulation avec le travail de nuit.",
            ]
        )
    if has_theme(themes, "astreinte"):
        checks.extend(
            [
                f"À vérifier dans {ref} : régime actuel d'astreinte et conditions d'intervention.",
                f"À vérifier dans {ref} : indemnisation, repos après intervention et population concernée.",
            ]
        )
    if has_theme(themes, "disciplinaire"):
        checks.extend(
            [
                f"À vérifier dans {ref} : procédure disciplinaire applicable et garanties de défense.",
                f"À vérifier dans {ref} : sanctions prévues, délais et modalités de convocation.",
            ]
        )
    if has_theme(themes, "droit syndical", "relations collectives"):
        checks.extend(
            [
                f"À vérifier dans {ref} : crédits d'heures, mandats concernés et moyens syndicaux existants.",
                f"À vérifier dans {ref} : modalités d'utilisation, suivi et garanties des représentants.",
            ]
        )
    if has_theme(themes, "rémunération", "primes"):
        checks.extend(
            [
                f"À vérifier dans {ref} : prime ou majoration actuelle, bénéficiaires et conditions d'ouverture.",
                f"À vérifier dans {ref} : règles existantes de calcul, périodicité et exclusions éventuelles.",
            ]
        )
    return dedupe(checks or [f"À vérifier dans {ref} : disposition actuelle, champ d'application et texte le plus récent."])


def comparison_elements(themes: list[dict[str, Any]]) -> list[str]:
    if is_classification_theme(themes):
        return [
            "fiche de poste actuelle",
            "fonctions réellement exercées",
            "niveau d'autonomie",
            "responsabilités",
            "technicité",
            "polyvalence",
            "comparaison avec salariés similaires",
            "historique des changements de poste",
            "critères conventionnels",
            "coefficient actuel",
            "coefficient revendiqué ou à réexaminer",
        ]
    if is_inaptitude_theme(themes):
        return [
            "avis du médecin du travail",
            "restrictions médicales",
            "étude de poste",
            "postes disponibles",
            "adaptations possibles",
            "formations envisageables",
            "périmètre de reclassement",
            "consultation éventuelle du CSE",
            "échanges avec le salarié",
            "traçabilité des recherches",
        ]
    if is_overtime_counter_theme(themes):
        return [
            "relevés de pointage",
            "compteurs d'heures",
            "heures effectuées",
            "heures validées",
            "heures refusées",
            "heures payées",
            "heures récupérées",
            "règles de majoration",
            "contingent",
            "repos compensateur",
            "paramétrage logiciel",
            "période à contrôler",
        ]
    if is_cssct_theme(themes):
        return [
            "état climatisation locaux SNCC/PROVOX",
            "fiabilité des analyseurs en continu",
            "stock de pièces critiques",
            "délai de réapprovisionnement",
            "plan de contingence",
            "scénarios de panne",
            "sécurité process",
            "maintenance préventive",
            "charge mentale",
            "RPS",
            "mise à jour DUERP",
            "escalade en cas de panne",
        ]
    if is_paid_leave_theme(themes):
        return [
            "méthode actuellement appliquée par l'entreprise",
            "date d'un éventuel changement de méthode ou de paramétrage",
            "maintien de salaire",
            "règle du dixième",
            "comparaison individuelle des deux méthodes",
            "méthode la plus favorable à retenir selon le cadre applicable",
            "salaire de référence et rémunération brute de référence",
            "éléments inclus dans l'assiette",
            "éléments exclus de l'assiette",
            "période de référence",
            "période d'acquisition",
            "prise des congés",
            "indemnité compensatrice de congés payés",
            "salariés postés, primes variables et éléments particuliers",
            "impact du passage éventuel à l'année civile",
            "régularisations et rappels de salaire",
            "période à contrôler",
            "données de paie nécessaires",
        ]
    if is_worktime_rest_theme(themes):
        return [
            "durée de repos",
            "délai de prévenance",
            "cycle de travail",
            "salariés concernés",
            "volontariat",
            "contreparties",
            "fatigue",
            "sécurité",
            "articulation avec l'accord 5x8",
            "articulation avec la convention collective",
        ]
    if has_theme(themes, "astreinte"):
        return [
            "périmètre de l'astreinte",
            "fréquence d'appel",
            "temps d'intervention",
            "repos après intervention",
            "indemnisation",
            "volontariat ou rotation",
            "sécurité",
        ]
    if has_theme(themes, "disciplinaire"):
        return [
            "faits reprochés",
            "délai de procédure",
            "convocation",
            "preuve",
            "proportionnalité de la sanction",
            "droits de défense",
        ]
    if has_theme(themes, "droit syndical", "relations collectives"):
        return [
            "mandats concernés",
            "crédit d'heures",
            "modalités d'utilisation",
            "moyens syndicaux",
            "information du CSE",
            "égalité entre représentants",
        ]
    if has_theme(themes, "rémunération", "primes"):
        return [
            "montant actuel",
            "montant projeté",
            "bénéficiaires",
            "conditions d'attribution",
            "période d'application",
            "effet paie",
            "égalité de traitement",
        ]
    return ["salariés concernés", "fréquence d'utilisation", "contreparties", "égalité de traitement"]


def comparison_table(themes: list[dict[str, Any]], sources: list[dict[str, Any]]) -> list[dict[str, str]]:
    refs = [source_reference(source) for source in sources] or ["source locale à identifier"]
    if is_paid_leave_theme(themes):
        return [
            {
                "element": element,
                "situation_actuelle": f"À vérifier dans {refs[index % len(refs)]} et avec le paramétrage paie réel.",
                "projet_direction": "Demander le calcul appliqué, la date d'effet et les exemples anonymisés avant/après.",
                "ecart_ou_changement": "Écart à mesurer par comparaison maintien de salaire / dixième pour chaque profil concerné.",
                "risque_ou_effet_possible": "Risque de perte individuelle, d'assiette incomplète ou de régularisation non réalisée.",
                "source_a_verifier": refs[index % len(refs)],
            }
            for index, element in enumerate(comparison_elements(themes))
        ]
    return [
        {
            "element": element,
            "situation_actuelle": f"À vérifier dans {refs[index % len(refs)]}.",
            "projet_direction": "À préciser par la direction dans un tableau avant/après.",
            "ecart_ou_changement": "Écart à objectiver après réception du projet écrit.",
            "risque_ou_effet_possible": "Risque ou effet à qualifier avec les salariés concernés.",
            "source_a_verifier": refs[index % len(refs)],
        }
        for index, element in enumerate(comparison_elements(themes))
    ]


def employee_consequences(themes: list[dict[str, Any]]) -> list[dict[str, str]]:
    cssct_sensitive = is_cssct_theme(themes) or is_inaptitude_theme(themes) or is_worktime_rest_theme(themes) or is_overtime_counter_theme(themes) or has_theme(themes, "astreinte")
    remuneration_sensitive = has_theme(themes, "rémunération", "primes") or is_paid_leave_theme(themes) or is_overtime_counter_theme(themes) or is_classification_theme(themes)
    consequences = [
        {"categorie": "charge de travail", "analyse": "Impact potentiel à mesurer selon la fréquence et les postes concernés."},
        {"categorie": "fatigue", "analyse": "Risque potentiel renforcé si le sujet touche repos, 5x8, astreinte ou travail de nuit." if cssct_sensitive else "À vérifier selon l'organisation concrète."},
        {"categorie": "sommeil", "analyse": "À analyser en CSSCT si travail de nuit, repos réduit ou astreinte sont concernés." if cssct_sensitive else "Impact non établi à ce stade."},
        {"categorie": "vie personnelle", "analyse": "Effet possible sur organisation familiale, prévisibilité et récupération."},
        {"categorie": "santé", "analyse": "À croiser avec prévention, médecine du travail et DUERP si le sujet a un impact organisationnel."},
        {"categorie": "sécurité", "analyse": "Point de vigilance si fatigue, récupération ou erreurs opérationnelles peuvent augmenter."},
        {"categorie": "organisation familiale", "analyse": "À mesurer selon délais de prévenance, fréquence et caractère temporaire ou permanent."},
        {"categorie": "récupération", "analyse": "À vérifier dans les textes locaux et avec les plannings simulés."},
        {"categorie": "égalité de traitement", "analyse": "Comparer populations incluses, exclues et critères d'application."},
        {"categorie": "rémunération éventuelle", "analyse": "Impact direct à chiffrer." if remuneration_sensitive else "À vérifier si une contrepartie financière est proposée."},
        {"categorie": "impact sur postés", "analyse": "Point prioritaire si les salariés en 5x8, équipes postées ou travail de nuit sont concernés."},
        {"categorie": "impact sur astreinte", "analyse": "À vérifier si intervention, rappel ou continuité de production sont dans le projet."},
    ]
    if is_cssct_theme(themes):
        consequences.extend(
            [
                {"categorie": "sécurité process", "analyse": "Risque potentiel en cas de défaillance d'équipements critiques ou d'analyseurs indisponibles."},
                {"categorie": "continuité d'exploitation", "analyse": "À vérifier avec le plan de contingence, les scénarios de panne et les modalités d'escalade."},
                {"categorie": "maintenance préventive", "analyse": "À objectiver avec les plans de maintenance, les délais d'intervention et les stocks de pièces critiques."},
                {"categorie": "charge mentale", "analyse": "Risque RPS potentiel si les équipes compensent une fragilité technique ou une incertitude de dépannage."},
            ]
        )
    if is_classification_theme(themes):
        consequences.extend(
            [
                {"categorie": "carrière", "analyse": "Impact possible sur évolution professionnelle, reconnaissance du poste et trajectoire de carrière."},
                {"categorie": "rémunération", "analyse": "Effet possible sur salaire de base, primes liées au coefficient ou évolutions futures."},
                {"categorie": "égalité de traitement", "analyse": "Comparer la situation avec des salariés aux fonctions, responsabilités et niveaux d'autonomie similaires."},
                {"categorie": "reconnaissance du travail réel", "analyse": "Objectiver l'écart éventuel entre fiche de poste et fonctions réellement exercées."},
            ]
        )
    if is_inaptitude_theme(themes):
        consequences.extend(
            [
                {"categorie": "maintien dans l'emploi", "analyse": "Point central : vérifier les adaptations, formations et postes compatibles avant toute conclusion."},
                {"categorie": "santé au travail", "analyse": "Respecter les restrictions médicales et éviter toute exposition incompatible avec l'avis du médecin du travail."},
                {"categorie": "reclassement", "analyse": "Contrôler le périmètre, la réalité et la traçabilité des recherches de reclassement."},
                {"categorie": "rupture du contrat", "analyse": "Risque de licenciement pour inaptitude si l'impossibilité de reclassement est invoquée."},
            ]
        )
    if is_overtime_counter_theme(themes):
        consequences.extend(
            [
                {"categorie": "rémunération", "analyse": "Impact direct si des heures effectuées ne sont pas payées, majorées ou récupérées correctement."},
                {"categorie": "temps de repos", "analyse": "Vérifier les repos compensateurs, récupérations et effets sur la fatigue."},
                {"categorie": "compteurs", "analyse": "Risque d'écart entre pointage, compteur logiciel et bulletin de paie."},
                {"categorie": "charge de travail", "analyse": "Identifier si les heures supplémentaires traduisent un besoin structurel d'effectifs ou d'organisation."},
            ]
        )
    if is_paid_leave_theme(themes):
        consequences.extend(
            [
                {"categorie": "rémunération nette", "analyse": "Impact possible si la méthode appliquée ne retient pas le résultat le plus favorable entre maintien et dixième lorsque le cadre applicable l'exige."},
                {"categorie": "salariés postés", "analyse": "Vérifier le traitement des primes et majorations liées aux horaires postés dans l'assiette de calcul."},
                {"categorie": "éléments variables", "analyse": "Contrôler l'intégration ou l'exclusion des primes variables, rappels, majorations et éléments exceptionnels selon leur nature."},
                {"categorie": "régularisation", "analyse": "Demander la période contrôlée, le nombre de salariés concernés et le montant global des écarts éventuels."},
                {"categorie": "année civile", "analyse": "Analyser le raccordement des périodes de référence et d'acquisition si la méthode ou le calendrier annuel a changé."},
            ]
        )
    return consequences


def benefit_balance(themes: list[dict[str, Any]]) -> dict[str, Any]:
    company_benefits = [
        "flexibilité",
        "remplacement plus facile",
        "couverture des postes",
        "continuité de production",
        "optimisation des effectifs",
        "baisse de contraintes organisationnelles",
    ]
    employee_benefits = [
        "rémunération éventuelle à chiffrer",
        "organisation plus prévisible si le dispositif est encadré",
        "volontariat si prévu par le projet",
        "garanties écrites",
        "repos compensateur si prévu",
        "autres contreparties à négocier",
    ]
    if has_theme(themes, "rémunération", "primes"):
        employee_benefits.insert(0, "gain financier potentiel à vérifier sur fiche de paie et population concernée")
    if is_cssct_theme(themes):
        company_benefits = [
            "continuité d'exploitation sécurisée",
            "réduction des indisponibilités techniques",
            "meilleure anticipation des pannes",
            "maîtrise des risques industriels",
        ]
        employee_benefits = [
            "conditions de travail sécurisées",
            "réduction de la charge mentale",
            "consignes d'escalade plus claires",
            "meilleure prévention des incidents",
            "DUERP actualisé",
        ]
    if is_paid_leave_theme(themes):
        company_benefits = [
            "sécurisation du paramétrage paie",
            "réduction du risque de litige individuel ou collectif",
            "clarification des règles de calcul appliquées",
        ]
        employee_benefits = [
            "application de la méthode la plus favorable lorsque le cadre applicable l'exige",
            "régularisation des écarts défavorables éventuels",
            "transparence sur l'assiette et les périodes de référence",
            "contrôle spécifique des salariés postés et éléments variables",
        ]
    if is_classification_theme(themes):
        company_benefits = ["clarification des emplois réellement tenus", "grille de classification mieux documentée", "réduction du risque de contestation individuelle"]
        employee_benefits = ["reconnaissance du travail réel", "réexamen du coefficient si les critères le justifient", "meilleure égalité de traitement entre postes comparables"]
    if is_inaptitude_theme(themes):
        company_benefits = ["dossier de reclassement mieux tracé", "adaptations de poste objectivées", "réduction du risque contentieux"]
        employee_benefits = ["maintien dans l'emploi recherché loyalement", "prise en compte des restrictions médicales", "visibilité sur les postes compatibles et formations possibles"]
    if is_overtime_counter_theme(themes):
        company_benefits = ["fiabilisation du suivi du temps", "clarification des compteurs", "réduction des écarts entre pointage et paie"]
        employee_benefits = ["paiement ou récupération des heures dues", "meilleure transparence des compteurs", "contrôle des majorations et repos compensateurs"]
    return {
        "avantages_probables_pour_l_entreprise": company_benefits,
        "avantages_eventuels_pour_les_salaries": dedupe(employee_benefits),
        "conclusion": "Équilibre social à vérifier.",
    }


def risk_watchpoints(themes: list[dict[str, Any]]) -> list[str]:
    risks = [
        "risque juridique à qualifier avec une source précise",
        "compatibilité à analyser avec les textes locaux, la convention collective et le Code du travail",
        "risque d'absence de contrepartie",
        "risque d'impact sur un autre accord",
        "risque de perte de droit si le projet modifie une garantie existante",
    ]
    if is_worktime_rest_theme(themes) or is_overtime_counter_theme(themes) or has_theme(themes, "astreinte"):
        risks.extend(
            [
                "risque santé-sécurité",
                "risque fatigue",
                "risque RPS",
                "risque de banalisation d'une dérogation",
                "risque sur récupération et sécurité process",
            ]
        )
    if is_cssct_theme(themes):
        risks.extend(
            [
                "risque technique sur équipements critiques",
                "risque sécurité process",
                "risque de rupture de continuité d'exploitation",
                "risque de maintenance préventive insuffisante",
                "risque de stock insuffisant sur pièces critiques",
                "risque d'escalade mal définie en cas de panne",
                "risque de DUERP non actualisé",
                "risque RPS lié à la charge mentale et au stress opérationnel",
            ]
        )
    if is_paid_leave_theme(themes):
        risks.extend(
            [
                "risque de non-comparaison entre maintien de salaire et règle du dixième",
                "risque d'assiette de calcul incomplète",
                "risque de perte de rémunération nette non détectée",
                "risque de traitement défavorable des salariés postés ou des éléments variables",
                "risque de raccordement incorrect des périodes lors du passage à l'année civile",
                "risque d'absence de régularisation rétroactive si des écarts sont confirmés",
                "risque d'inventer une règle locale sans source précise",
            ]
        )
    if is_classification_theme(themes):
        risks.extend(
            [
                "risque de sous-classification du poste réellement tenu",
                "risque d'écart entre fiche de poste et fonctions exercées",
                "risque d'inégalité de traitement avec des salariés similaires",
                "risque de critères conventionnels non vérifiés",
                "risque d'absence de réexamen du coefficient malgré une évolution de poste",
            ]
        )
    if is_inaptitude_theme(themes):
        risks.extend(
            [
                "risque de restrictions médicales insuffisamment prises en compte",
                "risque d'étude de poste incomplète",
                "risque de recherches de reclassement non tracées",
                "risque d'adaptations ou formations non étudiées",
                "risque de consultation CSE absente ou insuffisante si elle est requise",
                "risque de licenciement pour inaptitude sans démonstration complète de l'impossibilité de reclassement",
            ]
        )
    if is_overtime_counter_theme(themes):
        risks.extend(
            [
                "risque d'heures effectuées non validées",
                "risque d'heures supplémentaires non payées ou non majorées",
                "risque d'écart entre pointage, badgeage, compteur et paie",
                "risque de récupération ou repos compensateur mal appliqué",
                "risque de dépassement du contingent non identifié",
                "risque de paramétrage logiciel erroné",
            ]
        )
    if has_theme(themes, "disciplinaire"):
        risks.extend(["risque de procédure insuffisamment documentée", "risque de sanction disproportionnée à vérifier"])
    if has_theme(themes, "rémunération", "primes"):
        risks.extend(["risque d'inégalité de traitement", "risque d'effet paie mal chiffré"])
    return dedupe(risks)


def missing_information(themes: list[dict[str, Any]]) -> list[str]:
    missing = [
        "texte exact du projet",
        "comparaison avant/après",
        "salariés concernés",
        "fréquence prévue",
        "durée de la mesure",
        "justification direction",
        "données chiffrées",
        "contreparties proposées",
    ]
    if is_worktime_rest_theme(themes) or has_theme(themes, "astreinte"):
        missing.extend(["analyse de risques", "avis du médecin du travail si pertinent", "consultation CSSCT si pertinente", "mesures de prévention"])
    if is_cssct_theme(themes):
        missing.extend(
            [
                "état réel de la climatisation SNCC/PROVOX et des analyseurs",
                "historique incidents, dysfonctionnements et alertes",
                "liste des pièces critiques en stock",
                "délai de réapprovisionnement des pièces manquantes",
                "plan de contingence en cas de panne",
                "scénarios de panne évalués",
                "analyse sécurité process",
                "évaluation charge mentale et RPS",
                "mise à jour DUERP",
                "mesures de prévention immédiates",
            ]
        )
    if is_paid_leave_theme(themes):
        missing.extend(
            [
                "méthode actuellement appliquée par l'entreprise",
                "date exacte d'un éventuel changement de méthode",
                "règle utilisée avant et après le changement évoqué",
                "comparaison maintien de salaire / règle du dixième",
                "éléments inclus et exclus de l'assiette de calcul",
                "période de référence et période d'acquisition utilisées",
                "populations concernées",
                "données de paie nécessaires au contrôle",
                "exemples anonymisés de calcul",
                "nombre de salariés contrôlés",
                "montant global des écarts éventuels",
                "historique des régularisations",
                "paramétrage fonctionnel du logiciel de paie",
            ]
        )
    if is_classification_theme(themes):
        missing.extend(
            [
                "fiche de poste actuelle",
                "fonctions réellement exercées",
                "niveau d'autonomie",
                "responsabilités",
                "technicité",
                "comparaison avec salariés similaires",
                "historique des changements de poste",
                "critères conventionnels à vérifier",
                "éléments permettant une demande de réexamen du coefficient",
            ]
        )
    if is_inaptitude_theme(themes):
        missing.extend(
            [
                "avis du médecin du travail",
                "restrictions médicales",
                "étude de poste",
                "postes disponibles",
                "adaptations possibles",
                "formations envisageables",
                "périmètre de reclassement",
                "consultation éventuelle du CSE",
                "échanges avec le salarié",
                "traçabilité des recherches",
            ]
        )
    if is_overtime_counter_theme(themes):
        missing.extend(
            [
                "relevés de pointage",
                "compteurs",
                "heures validées ou refusées",
                "heures payées ou récupérées",
                "règles de majoration",
                "règles de récupération",
                "contingent",
                "repos compensateur",
                "paramétrage logiciel",
                "exemples anonymisés",
                "période à contrôler",
            ]
        )
    return dedupe(missing)


def documents_to_request_detailed(themes: list[dict[str, Any]]) -> list[str]:
    documents = [
        "projet écrit complet",
        "tableau comparatif ancien/nouveau",
        "note explicative direction",
        "analyse d'impact",
        "planning ou simulations",
        "historique des dérogations existantes",
    ]
    if is_worktime_rest_theme(themes) or has_theme(themes, "astreinte"):
        documents.extend(["données d'absentéisme/fatigue si pertinentes", "évaluation des risques", "mise à jour DUERP si pertinente", "avis ou contribution CSSCT si nécessaire"])
    if is_cssct_theme(themes):
        documents.extend(
            [
                "état technique climatisation locaux SNCC/PROVOX",
                "état technique des analyseurs en continu",
                "registre incidents, dysfonctionnements et alertes",
                "inventaire des pièces critiques et stocks disponibles",
                "délais de réapprovisionnement fournisseurs",
                "plan de contingence et scénarios de panne",
                "procédure d'escalade en cas de panne",
                "plan de maintenance préventive",
                "analyse sécurité process",
                "mise à jour DUERP",
                "analyse RPS / charge mentale",
                "mesures de prévention immédiates",
            ]
        )
    if is_paid_leave_theme(themes):
        documents.extend(
            [
                "note détaillée de méthode de calcul de l'indemnité de congés payés",
                "règle utilisée avant et après le changement évoqué",
                "date exacte du changement de méthode ou de paramétrage",
                "exemples anonymisés de calcul",
                "comparaison dixième / maintien pour plusieurs profils",
                "éléments de rémunération intégrés et exclus de l'assiette",
                "nombre de salariés concernés",
                "montant global des écarts éventuels",
                "historique des régularisations",
                "paramétrage fonctionnel du logiciel de paie pertinent, sans données personnelles inutiles",
                "données de paie agrégées nécessaires au contrôle",
                "échantillons anonymisés salariés postés, variables et profils standards",
            ]
        )
    if is_classification_theme(themes):
        documents.extend(
            [
                "fiche de poste actuelle",
                "descriptif des fonctions réellement exercées",
                "éléments sur le niveau d'autonomie",
                "éléments sur les responsabilités",
                "éléments sur la technicité",
                "comparaison anonymisée avec salariés similaires",
                "historique des changements de poste",
                "grille et critères conventionnels de classification",
                "éléments de polyvalence ou pesée de poste",
                "demande de réexamen du coefficient",
            ]
        )
    if is_inaptitude_theme(themes):
        documents.extend(
            [
                "avis du médecin du travail",
                "restrictions médicales",
                "étude de poste",
                "liste des postes disponibles",
                "analyse des adaptations possibles",
                "formations envisageables",
                "périmètre de reclassement",
                "éléments de consultation éventuelle du CSE",
                "échanges avec le salarié",
                "traçabilité des recherches de reclassement",
            ]
        )
    if is_overtime_counter_theme(themes):
        documents.extend(
            [
                "relevés de pointage",
                "compteurs d'heures",
                "heures validées et refusées",
                "règles de majoration",
                "règles de récupération",
                "contingent applicable",
                "règles de repos compensateur",
                "paramétrage logiciel",
                "exemples anonymisés",
                "période à contrôler",
            ]
        )
    if has_theme(themes, "rémunération", "primes"):
        documents.extend(["simulation paie", "population bénéficiaire", "coût global et critères d'attribution"])
    return dedupe(documents + documents_to_request(themes))


def main_cse_questions(themes: list[dict[str, Any]]) -> list[str]:
    questions = [
        "Quel problème concret justifie cette modification ?",
        "Sur quels indicateurs la direction s'appuie-t-elle ?",
        "Combien de salariés seraient concernés ?",
        "Quelle comparaison avant/après pouvez-vous communiquer ?",
        "Le dispositif serait-il temporaire ou permanent ?",
        "Comment le CSE pourra-t-il suivre les effets réels après mise en œuvre ?",
    ]
    if is_worktime_rest_theme(themes):
        questions.extend(["Quelle fréquence d'utilisation est envisagée ?", "Quelles conséquences sur la fatigue ont été évaluées ?", "Quelles mesures de prévention sont prévues ?", "Quelles contreparties sont proposées ?"])
    if is_classification_theme(themes):
        questions = [
            "Quelle fiche de poste est actuellement retenue pour ce salarié ou ce groupe de salariés ?",
            "Quelles fonctions sont réellement exercées au quotidien ?",
            "Quel niveau d'autonomie, de responsabilité et de technicité est reconnu ?",
            "Quels critères conventionnels justifient le coefficient actuel ?",
            "Existe-t-il des salariés similaires avec une classification ou un coefficient différent ?",
            "Quels changements de poste, de périmètre ou de polyvalence ont été constatés ?",
            "La direction accepte-t-elle un réexamen du coefficient ?",
        ]
    if is_inaptitude_theme(themes):
        questions = [
            "Quel avis le médecin du travail a-t-il rendu et quelles restrictions médicales s'appliquent ?",
            "Quelle étude de poste a été réalisée ?",
            "Quels postes disponibles ont été recensés dans le périmètre de reclassement ?",
            "Quelles adaptations de poste ou formations ont été envisagées ?",
            "Quels postes ont été considérés comme compatibles ou incompatibles, et pour quels motifs ?",
            "Le salarié a-t-il été associé aux échanges sur les possibilités de reclassement ?",
            "Quelle traçabilité des recherches de reclassement pouvez-vous transmettre ?",
            "Une consultation du CSE est-elle requise ou prévue sur ce dossier ?",
        ]
    if is_overtime_counter_theme(themes):
        questions = [
            "Quels relevés de pointage ou de badgeage couvrent la période concernée ?",
            "Quel est le solde des compteurs d'heures au début et à la fin de la période ?",
            "Quelles heures ont été validées, refusées, payées ou récupérées ?",
            "Quelles règles de majoration sont appliquées aux heures supplémentaires ?",
            "Quel contingent et quel repos compensateur sont applicables ?",
            "Comment le logiciel calcule-t-il les compteurs et les récupérations ?",
            "Pouvez-vous fournir des exemples anonymisés de calcul ?",
            "Quelle période doit être contrôlée ?",
        ]
    if is_cssct_theme(themes):
        questions = [
            "Quel est l'état réel de la climatisation des locaux SNCC PROVOX et des analyseurs ?",
            "Quels incidents, dysfonctionnements ou alertes ont été recensés ?",
            "Quelles pièces critiques sont en stock ?",
            "Quel est le délai de réapprovisionnement des pièces manquantes ?",
            "Quel plan de contingence existe en cas de panne ?",
            "Quels risques pour la sécurité process ont été identifiés ?",
            "Quelles conséquences sur la charge mentale des équipes ?",
            "Le DUERP a-t-il été mis à jour ?",
            "Quels scénarios de panne ont été évalués ?",
            "Quelles mesures de prévention immédiates sont prévues ?",
        ]
    if is_paid_leave_theme(themes):
        questions = [
            "Quelle méthode de calcul de l'indemnité de congés payés est actuellement appliquée ?",
            "Les deux méthodes, maintien de salaire et règle du dixième, sont-elles comparées pour chaque salarié lorsque le droit applicable l'exige ?",
            "Quels éléments de rémunération entrent dans l'assiette du dixième ?",
            "Quels éléments sont exclus de l'assiette et pour quel motif ?",
            "Quelle conséquence a eu le passage éventuel à l'année civile ?",
            "À quelle date le paramétrage ou la méthode de paie a-t-il changé ?",
            "Combien de salariés ont été contrôlés ?",
            "Existe-t-il des écarts défavorables ?",
            "Une régularisation rétroactive est-elle prévue si des anomalies sont constatées ?",
            "Quels exemples anonymisés avant/après pouvez-vous communiquer pour les salariés postés, variables et profils standards ?",
        ]
    if has_theme(themes, "astreinte"):
        questions.extend(["Quels postes ou services seraient intégrés au dispositif d'astreinte ?", "Comment le repos après intervention serait-il garanti ?", "Quelle indemnisation est prévue pour l'astreinte et les interventions ?"])
    if has_theme(themes, "disciplinaire"):
        questions.extend(["Quels faits précis sont reprochés et à quelles dates ?", "Quels éléments de preuve ont été communiqués au salarié ?", "La sanction envisagée est-elle proportionnée aux faits établis ?"])
    if has_theme(themes, "droit syndical", "relations collectives"):
        questions.extend(["Quels mandats et quels représentants sont concernés ?", "Le crédit d'heures est-il modifié, conditionné ou déplacé ?", "Quelles garanties sont prévues pour préserver l'exercice du mandat ?"])
    if has_theme(themes, "rémunération", "primes"):
        questions.extend(["Quel montant exact est prévu et pour quelle période ?", "Quels salariés seraient inclus ou exclus du dispositif ?", "Quelle simulation de paie permet de mesurer l'effet réel ?"])
    return dedupe(questions)[:10]


def conditional_followups(themes: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    if themes and is_paid_leave_theme(themes):
        return [
            {
                "si_reponse_direction": "le logiciel calcule automatiquement",
                "relances": [
                    "Quel paramétrage est utilisé ?",
                    "Qui l'a validé ?",
                    "Depuis quelle date ?",
                    "Un contrôle comparatif maintien de salaire / dixième a-t-il été réalisé ?",
                ],
            },
            {
                "si_reponse_direction": "il n'y a aucune perte",
                "relances": [
                    "Sur quel échantillon ?",
                    "Avec quelle méthode de comparaison ?",
                    "Pouvez-vous fournir des exemples anonymisés avant/après ?",
                ],
            },
            {
                "si_reponse_direction": "le changement d'année civile est neutre",
                "relances": [
                    "Quelle étude d'impact le démontre ?",
                    "Comment les périodes de référence ont-elles été raccordées ?",
                    "Comment les éléments variables ont-ils été traités ?",
                ],
            },
        ]
    if themes and is_classification_theme(themes):
        return [
            {"si_reponse_direction": "le coefficient est conforme", "relances": ["Quels critères conventionnels avez-vous appliqués ?", "Comment les fonctions réellement exercées ont-elles été prises en compte ?", "Quelle comparaison avec des postes similaires a été réalisée ?"]},
            {"si_reponse_direction": "la fiche de poste n'a pas changé", "relances": ["Les responsabilités réelles ont-elles évolué ?", "La polyvalence ou la technicité ont-elles augmenté ?", "Depuis quelle date le périmètre réel du poste est-il constaté ?"]},
            {"si_reponse_direction": "pas de réexamen prévu", "relances": ["Quelle procédure de réexamen existe ?", "Quels éléments le salarié ou le CSE peut-il transmettre ?", "Sous quel délai une réponse motivée peut-elle être donnée ?"]},
        ]
    if themes and is_inaptitude_theme(themes):
        return [
            {"si_reponse_direction": "aucun poste disponible", "relances": ["Quel périmètre a été recherché ?", "À quelle date la liste des postes a-t-elle été arrêtée ?", "Les adaptations ou formations ont-elles été étudiées ?"]},
            {"si_reponse_direction": "reclassement impossible", "relances": ["Quels postes ont été examinés un par un ?", "Quels motifs précis d'incompatibilité sont retenus ?", "Quelle traçabilité pouvez-vous transmettre ?"]},
            {"si_reponse_direction": "le salarié ne peut pas tenir le poste", "relances": ["Quelle restriction médicale l'interdit ?", "Quel aménagement de poste a été étudié ?", "Le médecin du travail a-t-il été sollicité sur l'adaptation envisagée ?"]},
        ]
    if themes and is_overtime_counter_theme(themes):
        return [
            {"si_reponse_direction": "le compteur est automatique", "relances": ["Quel paramétrage logiciel est utilisé ?", "Qui valide les anomalies ?", "Comment sont traitées les heures refusées ?"]},
            {"si_reponse_direction": "les heures ont été récupérées", "relances": ["À quelles dates ?", "Avec quel solde avant/après ?", "Le repos compensateur ou la majoration applicable a-t-il été respecté ?"]},
            {"si_reponse_direction": "aucun écart paie", "relances": ["Sur quelle période le contrôle a-t-il été réalisé ?", "Quels exemples anonymisés le démontrent ?", "Le rapprochement pointage / compteur / bulletin a-t-il été fait ?"]},
        ]
    return [
        {"si_reponse_direction": "besoin d'organisation", "relances": ["Quel besoin précis ?", "Depuis quand ?", "Sur quels postes ?", "Avec quelles données ?"]},
        {"si_reponse_direction": "pas d'impact", "relances": ["Quelle évaluation permet de l'affirmer ?", "Qui l'a réalisée ?", "Quels indicateurs seront suivis ?"]},
        {"si_reponse_direction": "c'est légal", "relances": ["Quel texte précis invoquez-vous ?", "Comment l'articulez-vous avec l'accord existant ?", "Quelles garanties sont prévues ?"]},
    ]


def cssct_point(themes: list[dict[str, Any]], text: str) -> dict[str, Any]:
    normalized = normalize(text)
    probable = is_cssct_theme(themes) or is_worktime_rest_theme(themes) or is_overtime_counter_theme(themes) or has_theme(themes, "astreinte") or any(
        term in normalized for term in ["fatigue", "nuit", "securite", "sante", "risque"]
    )
    if is_cssct_theme(themes):
        return {
            "statut": "Point CSSCT probable",
            "questions_cssct": [
                "Quel est l'état réel de la climatisation des locaux SNCC PROVOX et des analyseurs ?",
                "Quels incidents, dysfonctionnements ou alertes ont été recensés ?",
                "Quelles pièces critiques sont en stock ?",
                "Quel est le délai de réapprovisionnement des pièces manquantes ?",
                "Quel plan de contingence existe en cas de panne ?",
                "Quels risques pour la sécurité process ont été identifiés ?",
                "Quelles conséquences sur la charge mentale des équipes ?",
                "Le DUERP a-t-il été mis à jour ?",
                "Quels scénarios de panne ont été évalués ?",
                "Quelles mesures de prévention immédiates sont prévues ?",
            ],
        }
    return {
        "statut": "Point CSSCT probable" if probable else "Point CSSCT à vérifier selon l'impact santé-sécurité",
        "questions_cssct": [
            "Quels impacts sur la fatigue sont identifiés ?",
            "Quels impacts sur le sommeil et la récupération sont anticipés ?",
            "Quels risques d'erreurs opérationnelles ou de sécurité process sont évalués ?",
            "Quels accidents, presque accidents ou signaux faibles sont à examiner ?",
            "Quel lien avec les RPS est envisagé ?",
            "Le DUERP doit-il être mis à jour ?",
            "Quelles mesures de prévention sont prévues ?",
            "Un suivi médical ou une contribution du médecin du travail est-il nécessaire ?",
        ]
        if probable
        else ["Vérifier si le projet a un impact sur santé, sécurité, conditions de travail ou organisation."],
    }


def cfdt_position_to_build(themes: list[dict[str, Any]]) -> dict[str, Any]:
    non_acceptables = [
        "absence de projet écrit",
        "absence de comparaison avant/après",
        "absence d'analyse d'impact pour les salariés",
        "absence de garantie ou de suivi",
    ]
    if is_worktime_rest_theme(themes) or is_overtime_counter_theme(themes) or has_theme(themes, "astreinte"):
        non_acceptables.extend(["réduction de repos ou hausse de contrainte sans prévention", "banalisation d'une dérogation"])
    if is_cssct_theme(themes):
        non_acceptables.extend(
            [
                "absence d'état technique documenté",
                "absence de plan de contingence",
                "absence de mise à jour DUERP si les scénarios de panne sont confirmés",
                "absence de mesures de prévention immédiates",
            ]
        )
    if is_paid_leave_theme(themes):
        non_acceptables.extend(
            [
                "absence de méthode de calcul écrite",
                "absence de comparaison maintien de salaire / règle du dixième",
                "absence d'exemples anonymisés de calcul",
                "absence de justification sur l'assiette retenue",
                "absence de contrôle des salariés postés et éléments variables",
                "absence de régularisation si des écarts défavorables sont confirmés",
            ]
        )
        return {
            "points_non_acceptables_sans_garantie": dedupe(non_acceptables),
            "points_negociables": ["période de contrôle", "calendrier de régularisation", "format des données agrégées", "échantillons anonymisés", "clause de revoyure paie"],
            "contreparties_possibles": ["régularisation rétroactive", "contrôle annuel partagé", "information individuelle si un écart est identifié", "tableau de suivi CSE anonymisé"],
            "conditions_minimales": [
                "source locale ou conventionnelle identifiée, ou constat explicite d'absence de règle locale précise",
                "méthode actuelle vérifiée",
                "comparaison maintien de salaire / dixième documentée",
                "assiette et périodes de référence explicitées",
                "données de paie nécessaires communiquées sous forme proportionnée et anonymisée",
            ],
            "consultation_des_salaries": "Recueillir des exemples terrain de baisse constatée sans collecter de données personnelles inutiles.",
            "alternative_a_travailler": "Demander un audit paie ciblé sur les congés payés avec restitution anonymisée au CSE.",
        }
    if is_classification_theme(themes):
        non_acceptables.extend(["absence de fiche de poste à jour", "absence de prise en compte des fonctions réelles", "absence de critères conventionnels vérifiés", "absence de comparaison avec postes similaires"])
        return {
            "points_non_acceptables_sans_garantie": dedupe(non_acceptables),
            "points_negociables": ["calendrier de réexamen", "périmètre des postes comparables", "format des éléments anonymisés", "modalités de réponse motivée"],
            "contreparties_possibles": ["réexamen du coefficient", "mise à jour de la fiche de poste", "rappel salarial si un écart est établi", "revue collective de postes similaires"],
            "conditions_minimales": ["fiche de poste actuelle", "fonctions réelles documentées", "critères conventionnels identifiés", "comparaison anonymisée avec salariés similaires"],
            "consultation_des_salaries": "Recueillir le descriptif factuel des missions réellement exercées et des évolutions de poste.",
            "alternative_a_travailler": "Demander une revue RH ciblée de classification avec réponse écrite et critères explicités.",
        }
    if is_inaptitude_theme(themes):
        non_acceptables.extend(["absence d'avis du médecin du travail", "absence d'étude de poste", "absence de recherche tracée de reclassement", "absence d'étude des adaptations ou formations possibles"])
        return {
            "points_non_acceptables_sans_garantie": dedupe(non_acceptables),
            "points_negociables": ["périmètre de reclassement", "délai de recherche", "modalités d'échanges avec le salarié", "formation ou adaptation de poste"],
            "contreparties_possibles": ["maintien dans l'emploi par adaptation", "formation de reclassement", "recherche élargie de postes compatibles", "suivi écrit avec le salarié"],
            "conditions_minimales": ["avis médical et restrictions", "étude de poste", "liste des postes disponibles", "traçabilité des recherches", "échanges avec le salarié"],
            "consultation_des_salaries": "Échanger avec le salarié concerné dans le respect de la confidentialité médicale.",
            "alternative_a_travailler": "Demander une reprise contradictoire des recherches de reclassement et adaptations possibles.",
        }
    if is_overtime_counter_theme(themes):
        non_acceptables.extend(["absence de relevés de pointage", "absence de compteurs vérifiables", "absence de règle claire de majoration ou récupération", "absence de rapprochement avec la paie"])
        return {
            "points_non_acceptables_sans_garantie": dedupe(non_acceptables),
            "points_negociables": ["période de contrôle", "format des extractions anonymisées", "règles de validation des heures", "calendrier de régularisation"],
            "contreparties_possibles": ["paiement des heures dues", "récupération conforme", "correction du compteur", "contrôle périodique CSE anonymisé"],
            "conditions_minimales": ["relevés de pointage", "compteurs", "règles de majoration", "heures validées/refusées", "paramétrage logiciel", "exemples anonymisés"],
            "consultation_des_salaries": "Recueillir les écarts constatés sans collecter de données personnelles inutiles.",
            "alternative_a_travailler": "Demander un audit paie/temps de travail sur la période à contrôler.",
        }
    return {
        "points_non_acceptables_sans_garantie": dedupe(non_acceptables),
        "points_negociables": ["périmètre", "durée d'application", "phase de test", "fréquence maximale", "modalités de suivi CSE/CSSCT"],
        "contreparties_possibles": ["repos compensateur", "prime ou majoration si pertinent", "délai de prévenance renforcé", "volontariat encadré si adapté", "clause de revoyure"],
        "conditions_minimales": ["projet écrit complet", "sources locales vérifiées", "impact salariés objectivé", "consultation des salariés concernés", "validation juridique avant position définitive"],
        "consultation_des_salaries": "Recueillir le retour des salariés concernés avant position définitive.",
        "alternative_a_travailler": "Demander à la direction une alternative moins contraignante et mieux encadrée.",
    }


def elected_summary(missing: list[str], documents: list[str]) -> dict[str, Any]:
    priorities = dedupe([documents[0], documents[1], missing[0], "analyse d'impact salariés"])[:3]
    return {
        "avant_de_prendre_position_demander_en_priorite": priorities,
        "conclusion": "Position définitive à construire après analyse des documents, vérification juridique et retour des salariés concernés.",
    }


def build_detailed_cse_report(title: str, text: str, base: dict[str, Any], sources: list[dict[str, Any]]) -> dict[str, Any]:
    themes = base["detected_themes"]
    sources = cse_sources_for_theme(sources, themes)
    source_status = cse_source_status(sources, themes, base["source_status"])
    confidence = cse_confidence(sources)
    enriched_sources = enrich_sources_for_cse(sources, themes)
    current_checks = current_situation_checks(themes, sources)
    compare_rows = comparison_table(themes, sources)
    consequences = employee_consequences(themes)
    benefits = benefit_balance(themes)
    risks = risk_watchpoints(themes)
    missing = missing_information(themes)
    requested_documents = documents_to_request_detailed(themes)
    questions = main_cse_questions(themes)
    relances = conditional_followups(themes)
    cssct = cssct_point(themes, text)
    cfdt_position = cfdt_position_to_build(themes)
    synthesis = elected_summary(missing, requested_documents)
    return {
        "kind": "cse-point-analysis",
        "generated_at": now_iso(),
        "point_cse": title,
        "titre": title,
        "sujet_detecte": main_subject(text, themes),
        "statut_source_locale": source_status,
        "niveau_de_confiance": confidence,
        "prudence_warning": PRUDENCE_WARNING,
        "source_status": source_status,
        "1_ce_que_la_direction_semble_vouloir_faire": direction_intent(text, themes),
        "2_textes_locaux_potentiellement_concernes": enriched_sources,
        "3_situation_actuelle_a_verifier": current_checks,
        "4_points_a_comparer_avant_apres": compare_rows,
        "5_consequences_concretes_pour_les_salaries": consequences,
        "6_a_qui_profite_le_changement": benefits,
        "7_risques_et_points_de_vigilance": risks,
        "8_informations_manquantes": missing,
        "9_documents_a_demander": requested_documents,
        "10_questions_principales_a_poser_en_cse": questions,
        "11_relances_conditionnelles": relances,
        "12_point_cssct_eventuel": cssct,
        "13_position_cfdt_a_construire": cfdt_position,
        "14_synthese_pour_l_elu": synthesis,
        "prudence_juridique": [
            "Ne pas conclure que le projet est légal ou illégal sans source précise.",
            "Distinguer source locale, hypothèse, analyse syndicale, question à poser et action recommandée.",
            "Confronter les sources locales à la convention collective et au Code du travail avant position définitive.",
        ],
        "1_ce_que_la_direction_semble_vouloir_presenter": direction_intent(text, themes),
        "2_ce_que_nous_savons": {
            "sujet": main_subject(text, themes),
            "themes_detectes": theme_names(themes),
            "requêtes_bible": base["generated_queries"],
        },
        "3_ce_que_disent_les_textes_locaux": sources,
        "4_accords_lies": [
            {
                "document": source.get("document"),
                "page": source.get("page"),
                "article": source.get("article_or_section"),
                "pertinence": source.get("match_score"),
                "niveau_de_confiance": source.get("confidence_level"),
            }
            for source in sources
        ],
        "5_questions_a_poser_a_la_direction": questions,
        "6_questions_de_relance_selon_reponse": relances,
        "7_documents_complementaires_a_demander": requested_documents,
        "8_risques_pour_les_salaries": risks,
        "9_opportunites_eventuelles": ["clarifier les règles applicables", "obtenir des garanties écrites", "préparer une position CFDT argumentée"],
        "10_position_cfdt_a_construire": cfdt_position,
        "11_avis_motive_requis": "à vérifier",
        "12_informations_manquantes_avant_de_prendre_position": missing,
        "detected_themes": themes,
        "generated_queries": base["generated_queries"],
        "security_notice": "Private local CSE analysis. Do not commit generated reports.",
    }


def build_cse_analysis(title: str, text: str, limit: int) -> dict[str, Any]:
    base = build_document_analysis(title, text, limit)
    sources = base["C_textes_locaux_potentiellement_concernes"]
    return build_detailed_cse_report(title, text, base, sources)
    return {
        "kind": "cse-point-analysis",
        "generated_at": now_iso(),
        "point_cse": title,
        "prudence_warning": PRUDENCE_WARNING,
        "source_status": base["source_status"],
        "1_ce_que_la_direction_semble_vouloir_presenter": base["B_ce_que_le_document_semble_vouloir_modifier_ou_presenter"],
        "2_ce_que_nous_savons": {
            "sujet": base["A_sujet_principal"],
            "themes_detectes": [theme["theme"] for theme in base["detected_themes"]],
            "requêtes_bible": base["generated_queries"],
        },
        "3_ce_que_disent_les_textes_locaux": sources,
        "4_accords_lies": [
            {
                "document": source.get("document"),
                "page": source.get("page"),
                "article": source.get("article_or_section"),
                "pertinence": source.get("match_score"),
                "niveau_de_confiance": source.get("confidence_level"),
            }
            for source in sources
        ],
        "5_questions_a_poser_a_la_direction": questions_for(base["detected_themes"]),
        "6_questions_de_relance_selon_reponse": [
            "Pouvez-vous préciser la base du changement proposé ?",
            "Pouvez-vous confirmer que les textes locaux cités ont été pris en compte ?",
            "Quels éléments mesurables permettront d'évaluer l'impact pour les salariés ?",
        ],
        "7_documents_complementaires_a_demander": documents_to_request(base["detected_themes"]),
        "8_risques_pour_les_salaries": [
            "risque à qualifier après lecture des textes cités",
            "compatibilité à vérifier avec les accords locaux",
            "impact concret à objectiver avant position définitive",
        ],
        "9_opportunites_eventuelles": [
            "clarifier les règles applicables",
            "obtenir des garanties écrites",
            "préparer une position CFDT argumentée",
        ],
        "10_position_cfdt_a_construire": "Position à construire après vérification humaine des sources et échanges avec les salariés concernés.",
        "11_avis_motive_requis": "à vérifier",
        "12_informations_manquantes_avant_de_prendre_position": documents_to_request(base["detected_themes"]),
        "security_notice": "Private local CSE analysis. Do not commit generated reports.",
    }


def extract_document_text(path: Path) -> str:
    extension = path.suffix.lower()
    if extension == ".pdf":
        pages, _ = bible.extract_pdf(path)
    elif extension == ".docx":
        pages, _ = bible.extract_docx(path)
    elif extension == ".txt":
        pages, _ = bible.extract_txt(path)
    else:
        raise SystemExit("Format non supporté pour l'analyse documentaire V1.")
    return "\n\n".join(page.get("text", "") for page in pages).strip()


def print_sources(sources: list[dict[str, Any]]) -> None:
    if not sources:
        print(NO_RELEVANT_SOURCE)
        print("Ne jamais interpréter l'absence de résultat comme l'absence de droit.")
        return
    for source in sources[:8]:
        print(
            f"- {source.get('document')} | page {source.get('page')} | "
            f"{source.get('article_or_section') or 'article non détecté'} | "
            f"score {source.get('match_score')} | {source.get('source_status')}"
        )


def print_list(title: str, values: list[Any], limit: int = 8) -> None:
    print(title)
    for value in values[:limit]:
        if isinstance(value, dict):
            label = value.get("categorie") or value.get("element") or value.get("si_reponse_direction") or value.get("document") or "item"
            detail = value.get("analyse") or value.get("risque_ou_effet_possible") or value.get("relances") or value.get("role_probable_du_document") or ""
            if isinstance(detail, list):
                detail = "; ".join(str(item) for item in detail)
            print(f"- {label}: {detail}")
        else:
            print(f"- {value}")


def print_comparison_rows(rows: list[dict[str, str]], limit: int = 6) -> None:
    print("4. POINTS À COMPARER AVANT / APRÈS")
    for row in rows[:limit]:
        print(
            f"- {row['element']} | actuel: {row['situation_actuelle']} | "
            f"projet: {row['projet_direction']} | vigilance: {row['risque_ou_effet_possible']}"
        )


def print_cse_summary(report: dict[str, Any]) -> None:
    print("POINT CSE")
    print(f"Titre: {report['titre']}")
    print(f"Sujet détecté: {report['sujet_detecte']}")
    print(f"Statut source locale: {report['statut_source_locale']}")
    print(f"Niveau de confiance: {report['niveau_de_confiance']}")
    print("")
    print("1. CE QUE LA DIRECTION SEMBLE VOULOIR FAIRE")
    print(report["1_ce_que_la_direction_semble_vouloir_faire"])
    print("")
    print("2. TEXTES LOCAUX POTENTIELLEMENT CONCERNÉS")
    if not report["2_textes_locaux_potentiellement_concernes"]:
        print(report["statut_source_locale"])
    for source in report["2_textes_locaux_potentiellement_concernes"][:6]:
        print(
            f"- {source.get('document')} | page {source.get('page')} | "
            f"{source.get('article') or 'article non détecté'} | score {source.get('score')} | "
            f"{source.get('role_probable_du_document')}"
        )
        print(f"  raison: {source.get('raison_de_pertinence')}")
    print("")
    print_list("3. SITUATION ACTUELLE À VÉRIFIER", report["3_situation_actuelle_a_verifier"])
    print("")
    print_comparison_rows(report["4_points_a_comparer_avant_apres"])
    print("")
    print_list("5. CONSÉQUENCES CONCRÈTES POUR LES SALARIÉS", report["5_consequences_concretes_pour_les_salaries"], 16)
    print("")
    print("6. À QUI PROFITE LE CHANGEMENT ?")
    print_list("Avantages probables pour l'entreprise", report["6_a_qui_profite_le_changement"]["avantages_probables_pour_l_entreprise"], 6)
    print_list("Avantages éventuels pour les salariés", report["6_a_qui_profite_le_changement"]["avantages_eventuels_pour_les_salaries"], 6)
    print(report["6_a_qui_profite_le_changement"]["conclusion"])
    print("")
    print_list("7. RISQUES ET POINTS DE VIGILANCE", report["7_risques_et_points_de_vigilance"], 16)
    print("")
    print_list("8. INFORMATIONS MANQUANTES", report["8_informations_manquantes"], 18)
    print("")
    print_list("9. DOCUMENTS À DEMANDER", report["9_documents_a_demander"], 18)
    print("")
    print_list("10. QUESTIONS PRINCIPALES À POSER EN CSE", report["10_questions_principales_a_poser_en_cse"], 10)
    print("")
    print_list("11. RELANCES CONDITIONNELLES", report["11_relances_conditionnelles"], 3)
    print("")
    print("12. POINT CSSCT ÉVENTUEL")
    print(report["12_point_cssct_eventuel"]["statut"])
    print_list("Questions CSSCT", report["12_point_cssct_eventuel"]["questions_cssct"], 8)
    print("")
    print("13. POSITION CFDT À CONSTRUIRE")
    print_list("Points non acceptables sans garantie", report["13_position_cfdt_a_construire"]["points_non_acceptables_sans_garantie"], 6)
    print_list("Conditions minimales", report["13_position_cfdt_a_construire"]["conditions_minimales"], 5)
    print("")
    print("14. SYNTHÈSE POUR L'ÉLU")
    for index, item in enumerate(report["14_synthese_pour_l_elu"]["avant_de_prendre_position_demander_en_priorite"], start=1):
        print(f"{index}. {item}")
    print(report["14_synthese_pour_l_elu"]["conclusion"])
    print(PRUDENCE_WARNING)
    return
    print(f"POINT CSE: {report['point_cse']}")
    print(f"Statut source: {report['source_status']}")
    print(f"Sujet: {report['2_ce_que_nous_savons']['sujet']}")
    print("Textes locaux liés:")
    print_sources(report["3_ce_que_disent_les_textes_locaux"])
    print("Questions à poser:")
    for question in report["5_questions_a_poser_a_la_direction"][:6]:
        print(f"- {question}")
    print(PRUDENCE_WARNING)


def print_document_summary(report: dict[str, Any]) -> None:
    print(f"DOCUMENT: {report['title']}")
    print(f"Statut source: {report['source_status']}")
    print(f"Sujet principal: {report['A_sujet_principal']}")
    print("Textes locaux potentiellement concernés:")
    print_sources(report["C_textes_locaux_potentiellement_concernes"])
    print(PRUDENCE_WARNING)


def command_analyze_cse(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    report = build_cse_analysis(args.title or args.subject[:80], args.subject, args.limit)
    path = BRIDGE_REPORT_DIR / f"cse-analysis-{stamp()}.private.json"
    write_private_json(path, report)
    print_cse_summary(report)
    return report


def command_analyze_document(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    path = Path(args.path).expanduser()
    if not path.exists() or not path.is_file():
        raise SystemExit("Document local introuvable.")
    text = extract_document_text(path)
    if not text:
        raise SystemExit("Aucun texte exploitable extrait du document local.")
    report = build_document_analysis(args.title or path.name, text, args.limit)
    output = BRIDGE_REPORT_DIR / f"document-analysis-{stamp()}.private.json"
    write_private_json(output, report)
    print_document_summary(report)
    return report


def scenario_validation_text(report: dict[str, Any]) -> str:
    return normalize(json.dumps(report, ensure_ascii=False, sort_keys=True))


def validate_scenario(scenario: dict[str, Any], report: dict[str, Any], sources: list[dict[str, Any]], missing_sections: list[str]) -> list[dict[str, Any]]:
    text = scenario_validation_text(report)
    checks = [
        {
            "name": "sections_cse_requises",
            "ok": not missing_sections,
            "detail": "sections présentes" if not missing_sections else ", ".join(missing_sections),
        },
        {
            "name": "sources_ou_prudence_locale",
            "ok": bool(sources) or bool(scenario.get("allow_no_sources")) or report.get("statut_source_locale") == NO_PRECISE_PAID_LEAVE_RULE,
            "detail": f"{len(sources)} source(s) filtrée(s)",
        },
    ]

    expected_theme = scenario.get("expected_theme")
    if expected_theme:
        detected = report.get("sujet_detecte") or report.get("A_sujet_principal") or ""
        checks.append(
            {
                "name": "profil_metier_detecte",
                "ok": normalize(detected) == normalize(expected_theme),
                "detail": detected,
            }
        )

    detected_themes = normalize(" ".join(theme_names(report.get("detected_themes", []))))
    for forbidden_theme in scenario.get("forbidden_themes", []):
        checks.append(
            {
                "name": f"theme_absent_{normalize(forbidden_theme).replace(' ', '_')}",
                "ok": normalize(forbidden_theme) not in detected_themes,
                "detail": forbidden_theme,
            }
        )

    for required in scenario.get("must_contain", []):
        checks.append(
            {
                "name": f"contenu_present_{normalize(required).replace(' ', '_')}",
                "ok": normalize(required) in text,
                "detail": required,
            }
        )

    for forbidden in scenario.get("must_not_contain", []):
        checks.append(
            {
                "name": f"contenu_absent_{normalize(forbidden).replace(' ', '_')}",
                "ok": normalize(forbidden) not in text,
                "detail": forbidden,
            }
        )
    return checks


def command_run_scenarios(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    rows = []
    for scenario in SCENARIOS:
        if scenario["kind"] == "cse":
            report = build_cse_analysis(scenario["title"], scenario["text"], args.limit)
            sources = report["3_ce_que_disent_les_textes_locaux"]
        else:
            report = build_document_analysis(scenario["title"], scenario["text"], args.limit)
            sources = report["C_textes_locaux_potentiellement_concernes"]
        missing_sections = [section for section in REQUIRED_CSE_SECTIONS if not report.get(section)]
        validations = validate_scenario(scenario, report, sources, missing_sections)
        section_check_ok = all(check["ok"] for check in validations)
        rows.append(
            {
                "id": scenario["id"],
                "expected": scenario["expected"],
                "source_status": report["source_status"],
                "section_check_ok": section_check_ok,
                "missing_sections": missing_sections,
                "validations": validations,
                "questions_count": len(report.get("10_questions_principales_a_poser_en_cse", [])),
                "comparison_rows_count": len(report.get("4_points_a_comparer_avant_apres", [])),
                "top_sources": [
                    {
                        "document": source.get("document"),
                        "page": source.get("page"),
                        "score": source.get("match_score"),
                        "confidence": source.get("confidence_level"),
                    }
                    for source in sources[:3]
                ],
            }
        )
    report = {
        "generated_at": now_iso(),
        "scenarios": rows,
        "prudence_warning": PRUDENCE_WARNING,
        "security_notice": "Private scenario report. Do not commit.",
    }
    write_private_json(BRIDGE_TEST_DIR / f"integration-scenarios-{stamp()}.private.json", report)
    print("SCÉNARIOS D'INTÉGRATION")
    for row in rows:
        failed = [check["name"] for check in row["validations"] if not check["ok"]]
        status = "fiche OK" if row["section_check_ok"] else f"contrôles KO: {', '.join(failed)}"
        print(f"- {row['id']} | {row['source_status']} | {status} | top sources: {len(row['top_sources'])}")
    failed_rows = [row for row in rows if not row["section_check_ok"]]
    if failed_rows:
        raise SystemExit("Scénarios en échec: " + ", ".join(row["id"] for row in failed_rows))
    return report


def command_diagnose(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    chunks = bible.read_jsonl(bible.INDEX_DIR / "chunks.private.jsonl")
    report = {
        "generated_at": now_iso(),
        "bible_index_available": bool(chunks),
        "chunks": len(chunks),
        "commands": [
            "python automation/scripts/nexus_bible_bridge.py analyze-cse --subject \"...\"",
            "python automation/scripts/nexus_bible_bridge.py analyze-document --path \"C:\\\\chemin\\\\document.pdf\"",
            "python automation/scripts/nexus_bible_bridge.py run-scenarios",
        ],
        "prudence_warning": PRUDENCE_WARNING,
        "security_notice": "Local integration diagnostic. Do not commit generated reports.",
    }
    write_private_json(BRIDGE_REPORT_DIR / f"integration-diagnose-{stamp()}.private.json", report)
    print(f"Bible Accords disponible: {'oui' if chunks else 'non'}")
    print(f"Chunks indexés: {len(chunks)}")
    print(PRUDENCE_WARNING)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CFDT Nexus - Bible Accords integration bridge")
    sub = parser.add_subparsers(dest="command", required=True)

    p_cse = sub.add_parser("analyze-cse")
    p_cse.add_argument("--subject", required=True)
    p_cse.add_argument("--title")
    p_cse.add_argument("--limit", type=int, default=6)
    p_cse.add_argument("--format", choices=["detailed"], default="detailed")

    p_doc = sub.add_parser("analyze-document")
    p_doc.add_argument("--path", required=True)
    p_doc.add_argument("--title")
    p_doc.add_argument("--limit", type=int, default=6)

    p_scenarios = sub.add_parser("run-scenarios")
    p_scenarios.add_argument("--limit", type=int, default=5)

    sub.add_parser("diagnose")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "analyze-cse":
        command_analyze_cse(args)
    elif args.command == "analyze-document":
        command_analyze_document(args)
    elif args.command == "run-scenarios":
        command_run_scenarios(args)
    elif args.command == "diagnose":
        command_diagnose(args)
    else:
        raise SystemExit(f"Commande inconnue: {args.command}")


if __name__ == "__main__":
    main()
