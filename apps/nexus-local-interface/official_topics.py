"""Sujets syndicaux courants et articles de référence du Code du travail (bloc « Sources officielles »).

Chaque sujet se déclenche quand la question (sans accents, en minuscules) contient, pour CHAQUE groupe de ``when``,
au moins une des racines indiquées. Les articles sont ensuite lus sur Légifrance (texte officiel, version en vigueur) :
cette table ne contient que des numéros, jamais de texte juridique. Elle est ordonnée du plus spécifique au plus général.

``generic`` : sujet large, ignoré quand un sujet plus précis est reconnu (ex. « en CSE » dans une question sur un licenciement).
``ri_terms`` : mots cherchés dans le règlement intérieur d'INEOS (un passage par notion : échelle des sanctions, alcool…).
``terms`` : mots OBLIGATOIRES (tous ensemble) cherchés dans la convention collective et dans Judilibre quand le sujet est reconnu.
"""

from __future__ import annotations

from typing import Any

TOPICS: list[dict[str, Any]] = [
    {
        "key": "licenciement_economique",
        "label": "Licenciement pour motif économique",
        "when": [["licenci"], ["economi"]],
        "articles": ["L1233-3", "L1233-4", "L1233-5", "L1233-8", "L1233-61", "L1234-9"],
        "terms": ["licenciement", "economique"],
    },
    {
        "key": "licenciement_personnel",
        "label": "Licenciement pour motif personnel (insuffisance professionnelle, faute…)",
        "when": [["licenci"], ["insuffisan", "incompeten", "professionnel", "personnel", "disciplin", "faute", "cause reelle"]],
        "articles": ["L1232-1", "L1232-2", "L1232-6", "L1234-1", "L1234-9", "L1235-1", "L1235-3"],
        "terms": ["licenciement"],
        "ri_terms": ["sanction", "licenciement", "faute grave", "droits de la defense"],
    },
    {
        "key": "sanction_disciplinaire",
        "label": "Sanction disciplinaire",
        "when": [["sanction", "disciplin", "avertissement", "blame", "mise a pied", "entretien prealable", "retard", "faute", "reproch", "insubordination", "absence injustifiee", "abandon de poste"]],
        "articles": ["L1331-1", "L1332-1", "L1332-2", "L1332-4"],
        "terms": ["sanction"],
        "ri_terms": ["sanction", "avertissement", "blame", "mise a pied", "licenciement", "droits de la defense"],
    },
    {
        "key": "rupture_conventionnelle",
        "label": "Rupture conventionnelle",
        "when": [["rupture conventionnelle", "rupture amiable"]],
        "articles": ["L1237-11", "L1237-13", "L1237-14"],
        "terms": ["rupture", "conventionnelle"],
    },
    {
        "key": "demission_preavis",
        "label": "Démission et préavis",
        "when": [["demission", "preavis"]],
        "articles": ["L1237-1", "L1234-1"],
        "terms": ["preavis"],
    },
    {
        "key": "inaptitude",
        "label": "Inaptitude et reclassement",
        "when": [["inapti", "reclassement"]],
        "articles": ["L1226-2", "L1226-2-1", "L1226-10", "L1226-12"],
        "terms": ["inaptitude"],
    },
    {
        "key": "heures_supplementaires",
        "label": "Heures supplémentaires",
        "when": [["heures supplementaires", "heure supplementaire", "majoration", "contingent"]],
        "articles": ["L3121-27", "L3121-28", "L3121-36"],
        "terms": ["heures", "supplementaires"],
    },
    {
        "key": "repos_nuit",
        "label": "Repos quotidien et hebdomadaire, travail de nuit",
        "when": [["repos", "travail de nuit", "travailleur de nuit", "nuit"]],
        "articles": ["L3131-1", "L3132-2", "L3122-1", "L3122-5"],
        "terms": ["repos"],
    },
    {
        "key": "astreinte",
        "label": "Astreintes",
        "when": [["astreinte"]],
        "articles": ["L3121-9", "L3121-10", "L3121-11"],
        "terms": ["astreinte"],
    },
    {
        "key": "alcool_stupefiants",
        "label": "Alcool, stupéfiants et dépistage sur le lieu de travail",
        "when": [["alcool", "alcoolemie", "ethylotest", "stupefiant", "drogue", "depistage", "test salivaire"]],
        "articles": ["R4228-20", "L1321-1", "L4121-1"],
        "terms": ["alcool"],
        "ri_terms": ["alcool", "stupefiants", "test", "sanction"],
    },
    {
        "key": "reglement_interieur",
        "label": "Règlement intérieur",
        "when": [["reglement interieur"]],
        "articles": ["L1321-1", "L1321-2", "L1321-3", "L1321-4", "L1322-1", "L1311-2"],
        "terms": ["reglement"],
    },
    {
        "key": "bulletin_paie",
        "label": "Bulletin de paie",
        "when": [["bulletin", "fiche de paie", "fiche de salaire", "nibelis", "kelio"]],
        "articles": ["L3243-2", "R3243-1", "L3245-1"],
        "terms": ["bulletin"],
    },
    {
        "key": "regularisation_salaire",
        "label": "Régularisation et rappel de salaire",
        "when": [["regularisation", "rappel de salaire", "impaye", "retenue sur salaire", "erreur de paie", "salaire manquant", "manque", "ecart"],
                 ["paie", "salaire", "bulletin", "heure", "prime", "indemnite"]],
        "articles": ["L3245-1", "L3251-1", "L3241-1"],
        "terms": ["salaire"],
    },
    {
        "key": "maladie_indemnites",
        "label": "Maladie, indemnités journalières et maintien de salaire",
        "when": [["maladie", "arret de travail", "arret maladie", "indemnites journalieres", "subrogation", "ijss"]],
        "articles": ["L1226-1", "D1226-1", "D1226-3"],
        "terms": ["maladie"],
    },
    {
        "key": "conges_naissance",
        "label": "Congés de maternité, de paternité et de naissance",
        "when": [["maternite", "paternite", "naissance", "adoption", "conge parental", "csn"]],
        "articles": ["L1225-17", "L1225-35", "L1225-4"],
        "terms": ["naissance"],
    },
    {
        "key": "jours_feries",
        "label": "Jours fériés",
        "when": [["ferie"]],
        "articles": ["L3133-1", "L3133-3"],
        "terms": ["feries"],
    },
    {
        "key": "conges_payes",
        "label": "Congés payés",
        "when": [["conges payes", "conge paye", "conges annuels"]],
        "articles": ["L3141-3", "L3141-5", "L3141-12", "L3141-24"],
        "terms": ["conges"],
    },
    {
        "key": "accident_securite",
        "label": "Santé, sécurité et accident du travail",
        "when": [["accident", "securite", "danger", "maladie professionnelle"]],
        "articles": ["L4121-1", "L4121-2", "L4131-1"],
        "terms": ["accident"],
    },
    {
        "key": "harcelement",
        "label": "Harcèlement",
        "when": [["harcel"]],
        "articles": ["L1152-1", "L1152-4", "L1153-1"],
        "terms": ["harcelement"],
        "ri_terms": ["harcelement", "sanction"],
    },
    {
        "key": "heures_delegation",
        "label": "Heures de délégation des élus",
        "when": [["delegation", "delegue", "elu"], ["heure", "credit"]],
        "articles": ["L2315-7", "L2315-9"],
        "terms": ["heures", "delegation"],
    },
    {
        "key": "salarie_protege",
        "label": "Protection des représentants du personnel",
        "when": [["protege", "protection", "licenci"], ["representant", "delegue syndical", "elu", "mandat"]],
        "articles": ["L2411-1", "L2411-5", "L2421-3"],
        "terms": ["representants"],
    },
    {
        "key": "cse_consultation",
        "generic": True,
        "label": "Attributions et consultations du CSE",
        "when": [["cse", "comite social", "consultation"]],
        "articles": ["L2312-8", "L2312-14", "L2312-15"],
        "terms": ["consultation"],
    },
    {
        "key": "negociation_accords",
        "generic": True,
        "label": "Négociation annuelle et accords collectifs",
        "when": [["nao", "negociation", "accord", "denonciation", "avenant", "revision"]],
        "articles": ["L2242-1", "L2261-7-1", "L2261-9", "L2261-13"],
        "terms": ["negociation"],
    },
    {
        "key": "teletravail",
        "label": "Télétravail",
        "when": [["teletravail"]],
        "articles": ["L1222-9", "L1222-10"],
        "terms": ["teletravail"],
    },
    {
        "key": "formation_entretien",
        "label": "Formation et entretien professionnel",
        "when": [["formation", "entretien professionnel"]],
        "articles": ["L6315-1", "L6321-1"],
        "terms": ["formation"],
    },
]
