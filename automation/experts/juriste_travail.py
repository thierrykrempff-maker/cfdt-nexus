#!/usr/bin/env python
"""
Expert Juriste droit du travail V0 renforce.

The expert enriches a validated Assistant DS Router answer without changing the
route. It only reasons from the router output and the sources already selected.
"""

from __future__ import annotations

from typing import Any

from .utils import has_any, normalize, route_domains, source_documents, unique


JURISTE_DOMAINS = {
    "cse",
    "droit_syndical",
    "temps_travail",
    "astreinte",
    "classification_carriere",
}

JURISTE_KEYWORDS = [
    "cse",
    "mandat",
    "droit syndical",
    "reunion",
    "delegation",
    "temps de travail",
    "repos",
    "astreinte",
    "classification",
    "coefficient",
    "convention collective",
    "accord",
    "contester",
    "droits",
]

JURISTE_PROMPT_VERSION = "EXPERT_JURISTE_CFDT_NEXUS_V1"
JURISTE_PROMPT_CONTRACT = "agents/juriste/EXPERT_JURISTE_CFDT_NEXUS_V1.md"

SOURCE_LAYER_ORDER = [
    "accord_entreprise",
    "convention_collective",
    "code_travail",
    "jurisprudence",
    "pratique_officielle",
]

PURE_PAY_CONTROL_KEYWORDS = [
    "bulletin",
    "paie",
    "majoration",
    "salaire",
    "prime",
    "heures de nuit",
    "dimanche",
]

LEGAL_SIGNAL_KEYWORDS = [
    "cse",
    "mandat",
    "delegation",
    "repos",
    "astreinte",
    "classification",
    "fiche de poste",
    "contester",
    "droit",
    "droits",
    "peut-il",
    "peut il",
    "accord",
    "convention collective",
]


def is_pure_pay_control(answer: dict[str, Any]) -> bool:
    query = normalize(answer.get("query", ""))
    domains = route_domains(answer)
    if "paie_remuneration" not in domains and not has_any(query, PURE_PAY_CONTROL_KEYWORDS):
        return False
    if has_any(query, LEGAL_SIGNAL_KEYWORDS):
        return False
    return has_any(query, ["controler", "controle", "manque", "fausse", "bulletin", "majoration", "paie"])


def applies(answer: dict[str, Any]) -> bool:
    domains = route_domains(answer)
    query = answer.get("query", "")
    if is_pure_pay_control(answer):
        return False
    if domains & JURISTE_DOMAINS:
        return True
    return has_any(query, JURISTE_KEYWORDS)


def short_response(answer: dict[str, Any]) -> str:
    domains = route_domains(answer)
    query = normalize(answer.get("query", ""))
    router_short = answer.get("short_answer")
    if "droit_syndical" in domains and "reunion" in query and "repos" in query:
        return (
            "La question releve d'abord du mandat CSE et de la qualification du temps de reunion. "
            "Nexus ne conclut pas sans verifier le statut du participant, la nature de la reunion et le texte local "
            "applicable lorsque la reunion tombe sur un repos."
        )
    if {"temps_travail", "astreinte", "paie_remuneration"}.issubset(domains):
        return (
            "La situation doit etre separee entre astreinte, temps d'intervention, repos apres intervention et trace paie. "
            "Le droit exact depend de l'accord d'astreinte, des horaires reels et des bulletins."
        )
    if "classification_carriere" in domains:
        return (
            "Une contestation de classification se prepare en comparant les fonctions reellement exercees, le coefficient "
            "actuel et les criteres des textes applicables. Nexus ne tranche pas sans ces pieces."
        )
    return router_short or "L'expert juriste ne conclut pas sans source locale suffisante."


def qualification(answer: dict[str, Any]) -> str:
    domains = route_domains(answer)
    query = normalize(answer.get("query", ""))
    if "droit_syndical" in domains and "reunion" in query:
        return "Situation d'exercice d'un mandat ou de participation CSE, avec incidence possible sur le temps de travail ou le repos."
    if {"temps_travail", "astreinte"}.issubset(domains):
        return "Situation individuelle d'astreinte avec intervention, effet possible sur le repos et reprise du poste."
    if "classification_carriere" in domains:
        return "Situation individuelle de classification/carriere a qualifier au regard des fonctions reellement exercees."
    if "temps_travail" in domains:
        return "Situation de temps de travail ou de repos a rapprocher des textes locaux applicables."
    return "Question juridique locale a qualifier a partir des sources disponibles et des faits exacts."


def established_points(answer: dict[str, Any]) -> list[str]:
    domains = [domain for domain in answer.get("route", {}).get("domains", []) if domain != "bible_accords"]
    points: list[str] = []
    if domains:
        points.append("Regle certaine: le routage Nexus qualifie la demande sur " + ", ".join(domains) + ".")
    if answer.get("sources"):
        points.append("Regle certaine: des sources locales principales ont ete retrouvees et doivent encadrer l'analyse.")
        points.extend("Source locale identifiee: " + source for source in source_documents(answer, limit=4))
    else:
        points.append("Information manquante: aucune source locale principale n'est disponible dans la reponse Nexus.")
    if answer.get("issue_groups"):
        group_names = [str(group.get("name") or group.get("id")) for group in answer["issue_groups"]]
        points.append("Regle certaine: Nexus separe les enjeux en groupes distincts: " + ", ".join(group_names) + ".")
    return points


def source_layers_analysis(answer: dict[str, Any]) -> list[dict[str, Any]]:
    layers = answer.get("source_layers", [])
    by_id = {str(layer.get("id")): layer for layer in layers if isinstance(layer, dict)}
    result: list[dict[str, Any]] = []
    for layer_id in SOURCE_LAYER_ORDER:
        layer = by_id.get(layer_id)
        if not layer:
            result.append(
                {
                    "source_layer": layer_id,
                    "status": "absent",
                    "summary": "Aucune source pertinente validee n'a ete trouvee dans cette couche.",
                    "sources": [],
                }
            )
            continue
        sources = layer.get("sources", []) if isinstance(layer.get("sources"), list) else []
        labels = [source_label_for_layer(source) for source in sources if isinstance(source, dict)]
        status = layer.get("status") or ("present" if labels else "absent")
        result.append(
            {
                "source_layer": layer_id,
                "label": layer.get("label") or layer.get("title") or layer_id,
                "status": status,
                "summary": layer_summary(layer, labels),
                "sources": labels[:5],
            }
        )
    return result


def source_label_for_layer(source: dict[str, Any]) -> str:
    parts = [str(source.get("document") or "Document")]
    page = source.get("page")
    if page:
        parts.append(f"page {page}")
    article = source.get("article") or source.get("article_or_section")
    if article:
        parts.append(str(article))
    excerpt = source.get("excerpt")
    if excerpt:
        parts.append("extrait: " + str(excerpt)[:220])
    return " | ".join(parts)


def layer_summary(layer: dict[str, Any], labels: list[str]) -> str:
    if labels:
        return f"{len(labels)} source(s) remontee(s) par Nexus pour cette couche."
    absent = layer.get("absent_message")
    if absent:
        return str(absent)
    return "Aucune source pertinente validee n'a ete trouvee dans cette couche."


def depends_on_local_texts(answer: dict[str, Any]) -> list[str]:
    domains = route_domains(answer)
    query = normalize(answer.get("query", ""))
    items = [
        "Information manquante: date, champ d'application et remplacement eventuel des textes cites.",
        "Information manquante: articulation entre accord local, convention collective et norme superieure applicable.",
    ]
    if "droit_syndical" in domains or "reunion" in query:
        items.extend(
            [
                "Information manquante: statut exact du participant a la reunion CSE.",
                "Information manquante: nature de la reunion et base de convocation ou de participation.",
                "Information manquante: traitement local du temps de reunion, delegation ou representation pendant un repos.",
            ]
        )
    if "astreinte" in domains:
        items.extend(
            [
                "Information manquante: disposition precise de l'accord d'astreinte applicable a l'intervention.",
                "Information manquante: heures reelles de debut, de fin et de reprise du poste.",
            ]
        )
    if "paie_remuneration" in domains:
        items.append("Information manquante: regle locale de paie ou de majoration effectivement appliquee.")
    if "classification_carriere" in domains:
        items.extend(
            [
                "Information manquante: coefficient, emploi repere et fiche de poste actuellement retenus.",
                "Information manquante: fonctions reellement exercees, niveau d'autonomie, technicite et responsabilites.",
            ]
        )
    return unique(items, limit=10)


def certainty_level(established: list[str], reasoning: list[str], missing: list[str]) -> dict[str, list[str]]:
    interpretations = [item for item in reasoning if normalize(item).startswith("interpretation")]
    hypotheses = [item for item in reasoning if normalize(item).startswith("hypothese")]
    return {
        "regle_certaine": [item for item in established if normalize(item).startswith("regle certaine")],
        "interpretation_juridique": interpretations,
        "hypothese": hypotheses,
        "information_manquante": unique(missing, limit=8),
    }


def legal_reasoning(answer: dict[str, Any]) -> list[str]:
    domains = route_domains(answer)
    query = normalize(answer.get("query", ""))
    if "droit_syndical" in domains and "reunion" in query:
        return [
            "Regle certaine: la question doit etre qualifiee comme exercice d'un mandat ou participation CSE avant d'etre traitee comme sujet de repos.",
            "Interpretation: le traitement du temps depend de la nature de la reunion et du role exact du salarie.",
            "Hypothese: si la participation est liee au mandat, le temps ne se traite pas comme une simple initiative personnelle.",
            "Information manquante: texte local ou conventionnel fixant le traitement lorsque la reunion tombe sur un repos 5x8.",
        ]
    if {"temps_travail", "astreinte"}.issubset(domains):
        return [
            "Regle certaine: l'intervention d'astreinte, le repos et la paie doivent etre controles separement.",
            "Interpretation: la reprise apres intervention ne peut etre appreciee qu'avec les heures reelles de fin et de reprise.",
            "Hypothese: les temps annexes ne sont a retenir que si la source applicable les integre.",
            "Information manquante: accord d'astreinte applicable, pointage, compteur et bulletin de la periode.",
        ]
    if "classification_carriere" in domains:
        return [
            "Regle certaine: une demande de classification suppose une comparaison entre classement actuel et fonctions reelles.",
            "Interpretation: l'ecart doit etre rattache a des criteres objectifs du texte applicable, pas seulement a un ressenti.",
            "Hypothese: des fonctions depassant durablement la fiche de poste peuvent justifier une demande de reexamen motivee.",
            "Information manquante: criteres conventionnels, coefficient actuel et preuves des missions exercees.",
        ]
    return [
        "Regle certaine: Nexus ne peut raisonner que sur les sources locales retrouvees.",
        "Information manquante: faits exacts et texte applicable a la situation.",
    ]


def defense_strategy(answer: dict[str, Any]) -> dict[str, list[str] | str]:
    domains = route_domains(answer)
    query = normalize(answer.get("query", ""))
    if "droit_syndical" in domains and "reunion" in query:
        return {
            "argument_principal": (
                "Qualifier juridiquement la participation comme temps lie au mandat ou a une convocation CSE, "
                "puis en deduire le traitement temps/repos applicable."
            ),
            "arguments_complementaires": [
                "Verifier si la reunion est convoquee par l'employeur ou rattachee a l'exercice normal du mandat.",
                "Comparer le traitement applique aux autres elus ou participants dans une situation comparable.",
                "Controler la trace du temps dans les compteurs, le planning et les documents CSE.",
            ],
            "position_probable_direction": (
                "La direction peut soutenir que la presence pendant un repos releve de l'organisation personnelle "
                "du salarie ou que seul un credit d'heures est mobilisable."
            ),
            "contre_arguments": [
                "Demander la base ecrite de cette position et son articulation avec le mandat.",
                "Rappeler que le traitement depend du titre de participation et de la source applicable, pas seulement du jour de repos.",
            ],
        }
    if {"temps_travail", "astreinte"}.issubset(domains):
        return {
            "argument_principal": (
                "Distinguer l'astreinte, l'intervention effective, le repos interrompu et les consequences paie pour "
                "eviter qu'un seul libelle masque plusieurs droits."
            ),
            "arguments_complementaires": [
                "Rapprocher les heures reelles d'appel, d'intervention, de trajet eventuel et de reprise du poste.",
                "Verifier les contreparties d'astreinte, le paiement de l'intervention et le compteur de repos.",
                "Controler si les sources Code du travail et accords locaux imposent un repos minimal ou une regularisation.",
            ],
            "position_probable_direction": (
                "La direction peut soutenir que l'accord d'astreinte prevoit la contrepartie, que la reprise etait "
                "operationnellement necessaire ou que la paie a deja integre l'intervention."
            ),
            "contre_arguments": [
                "Demander la ligne de calcul et la source exacte appliquee.",
                "Comparer la trace de paie avec le pointage et les releves d'intervention.",
                "Separarer la compensation d'astreinte du paiement du temps d'intervention et du respect du repos.",
            ],
        }
    if "classification_carriere" in domains:
        return {
            "argument_principal": (
                "Objectiver l'ecart entre les fonctions reellement exercees et la classification actuelle, puis le "
                "rattacher aux criteres applicables."
            ),
            "arguments_complementaires": [
                "Comparer fiche de poste, missions reelles, autonomie, technicite, responsabilites et coefficient.",
                "Reunir des exemples concrets de missions exercees durablement.",
                "Verifier les dispositions de la convention collective et les usages ou accords locaux pertinents.",
            ],
            "position_probable_direction": (
                "La direction peut soutenir que les taches invoquees sont ponctuelles, deja incluses dans le poste "
                "ou insuffisantes pour justifier un autre coefficient."
            ),
            "contre_arguments": [
                "Produire une chronologie et des preuves de regularite des missions.",
                "Demander les criteres objectifs retenus pour le coefficient actuel.",
                "Comparer avec des postes ou fonctions similaires lorsque des elements de comparaison existent.",
            ],
        }
    return {
        "argument_principal": "Qualifier les faits et les rattacher aux sources Nexus reellement remontees.",
        "arguments_complementaires": [
            "Verifier le champ d'application des textes cites.",
            "Ne conclure qu'apres controle des pieces indispensables.",
        ],
        "position_probable_direction": "La direction peut contester les faits, le champ du texte ou la portee de l'interpretation.",
        "contre_arguments": ["Demander une position ecrite et la source precise appliquee par la direction."],
    }


def evidence_documents(answer: dict[str, Any]) -> list[str]:
    domains = route_domains(answer)
    query = normalize(answer.get("query", ""))
    pieces = ["Chronologie precise des faits et dates concernees."]
    if "droit_syndical" in domains or "reunion" in query:
        pieces.extend(
            [
                "Convocation ou ordre du jour de la reunion CSE.",
                "Element etablissant le mandat ou le titre de participation du salarie.",
                "Planning 5x8 et identification du repos concerne.",
                "Trace du temps: compteur, credit d'heures, pointage ou recapitulatif.",
            ]
        )
    if "astreinte" in domains:
        pieces.extend(
            [
                "Accord ou consigne d'astreinte applicable a la periode.",
                "Releve d'appel ou d'intervention avec heures de debut et de fin.",
                "Planning de reprise du poste et compteur de repos.",
                "Bulletin de paie et recapitulatif des astreintes de la periode.",
            ]
        )
    if "paie_remuneration" in domains:
        pieces.extend(
            [
                "Bulletin de paie de la periode contestee.",
                "Pointage, compteur d'heures et detail des majorations appliquees.",
            ]
        )
    if "classification_carriere" in domains:
        pieces.extend(
            [
                "Contrat de travail et avenants.",
                "Fiche de poste actuelle et ancienne fiche si elle existe.",
                "Coefficient, emploi repere et classification actuellement retenus.",
                "Preuves des fonctions reellement exercees: mails, consignes, comptes rendus, organigramme.",
                "Elements de comparaison avec des fonctions ou postes similaires si disponibles.",
            ]
        )
    pieces.extend(str(item) for item in answer.get("documents_to_request", []))
    return unique(pieces, limit=12)


def recommended_action(answer: dict[str, Any]) -> list[str]:
    domains = route_domains(answer)
    query = normalize(answer.get("query", ""))
    actions = ["Niveau 1: verifier les faits et securiser les preuves avant toute conclusion."]
    if "classification_carriere" in domains:
        actions.extend(
            [
                "Niveau 2: construire un tableau fonctions reelles / criteres de classification / preuves.",
                "Niveau 3: demander a la direction les criteres justifiant le coefficient actuel et un reexamen motive.",
            ]
        )
    elif {"temps_travail", "astreinte"}.issubset(domains):
        actions.extend(
            [
                "Niveau 2: demander la regle appliquee pour l'intervention, le repos et la paie.",
                "Niveau 3: solliciter une regularisation ecrite si le pointage, le repos ou le bulletin ne correspondent pas aux sources.",
            ]
        )
    elif "droit_syndical" in domains or "reunion" in query:
        actions.extend(
            [
                "Niveau 2: demander la base de traitement du temps de reunion et sa trace dans les compteurs.",
                "Niveau 3: porter une question en CSE si le traitement local est incertain ou incoherent.",
            ]
        )
    else:
        actions.append("Niveau 2: demander a la direction la source et la justification ecrite de sa position.")
    actions.append("Niveau 4: envisager un appui juridique specialise seulement si le dossier est documente et que le blocage persiste.")
    return unique(actions, limit=6)


def vigilance_points(answer: dict[str, Any]) -> list[str]:
    domains = route_domains(answer)
    query = normalize(answer.get("query", ""))
    points: list[str] = []
    if "droit_syndical" in domains and "reunion" in query:
        points.extend(
            [
                "Risque: assimiler la question a une modification collective du repos alors qu'elle porte d'abord sur le mandat.",
                "Risque: confondre reunion CSE, delegation, invitation et presence volontaire.",
            ]
        )
    if "astreinte" in domains:
        points.extend(
            [
                "Risque: melanger droit au repos, indemnisation d'astreinte et paiement de l'intervention.",
                "Risque: oublier les heures exactes ou les compteurs dans l'analyse de reprise du poste.",
            ]
        )
    if "classification_carriere" in domains:
        points.extend(
            [
                "Risque: demander un reclassement sans relier les faits aux criteres de classification.",
                "Risque: s'appuyer sur une fiche de poste non actualisee sans preuves des fonctions reelles.",
            ]
        )
    if not points:
        points.append("Risque: conclure trop vite sans verifier le champ des sources locales.")
    return points


def proposed_position(answer: dict[str, Any]) -> str:
    domains = route_domains(answer)
    query = normalize(answer.get("query", ""))
    if "droit_syndical" in domains and "reunion" in query:
        return (
            "Position de travail: demander la qualification de la reunion, le statut du salarie et le texte de traitement "
            "du temps avant toute conclusion sur paiement, recuperation ou imputation."
        )
    if {"temps_travail", "astreinte"}.issubset(domains):
        return (
            "Position de travail: verifier d'abord l'accord d'astreinte et les horaires reels, puis traiter separement repos, "
            "temps d'intervention et consequences paie."
        )
    if "classification_carriere" in domains:
        return (
            "Position de travail: objectiver l'ecart entre fonctions reelles et classification actuelle, puis demander un "
            "reexamen motive si les criteres du texte applicable sont remplis."
        )
    return answer.get("working_position") or "Position de travail: completer les sources et les faits avant conclusion."


def direction_questions(answer: dict[str, Any]) -> list[str]:
    domains = route_domains(answer)
    query = normalize(answer.get("query", ""))
    questions: list[str] = []
    if "droit_syndical" in domains and "reunion" in query:
        questions.extend(
            [
                "A quel titre le salarie participe-t-il a la reunion CSE ?",
                "Quelle base locale ou conventionnelle fixe le traitement du temps de reunion ?",
                "Comment ce temps est-il trace si la reunion tombe sur un repos 5x8 ?",
            ]
        )
    if "astreinte" in domains:
        questions.extend(
            [
                "Quelle disposition de l'accord d'astreinte est appliquee a cette intervention ?",
                "Quelle heure de fin d'intervention et quelle heure de reprise sont retenues ?",
            ]
        )
    if "paie_remuneration" in domains:
        questions.append("Ou apparait l'intervention sur le bulletin, le compteur ou le recapitulatif paie ?")
    if "classification_carriere" in domains:
        questions.extend(
            [
                "Quels criteres conventionnels justifient le coefficient actuel ?",
                "Quelles fonctions reelles sont reconnues au-dela de la fiche de poste ?",
                "Quels elements prouvent la duree et la regularite des fonctions exercees ?",
            ]
        )
    questions.extend(answer.get("questions_to_ask", [])[:3])
    return unique(questions, limit=8)


def limits(answer: dict[str, Any]) -> list[str]:
    items = [
        "L'expert juriste ne remplace pas une validation juridique humaine.",
        "Il ne dispose que des sources principales selectionnees par le routeur V1.2, dont Legifrance seulement si le connecteur est configure et a repondu.",
    ]
    if not answer.get("sources"):
        items.append("Aucune source locale principale n'a ete trouvee pour conclure.")
    if answer.get("warnings"):
        items.extend(str(warning) for warning in answer["warnings"])
    return unique(items, limit=8)


def enrich(answer: dict[str, Any]) -> dict[str, Any]:
    active = applies(answer)
    if not active:
        return {
            "active": False,
            "name": "Expert Juriste droit du travail V0 renforce",
            "prompt_version": JURISTE_PROMPT_VERSION,
            "prompt_contract": JURISTE_PROMPT_CONTRACT,
            "reason": "Question hors perimetre juriste pour cette orchestration.",
        }

    response = short_response(answer)
    established = established_points(answer)
    depends = depends_on_local_texts(answer)
    reasoning = legal_reasoning(answer)
    sources = source_documents(answer)
    risks = vigilance_points(answer)
    position = proposed_position(answer)
    expert_limits = limits(answer)
    pieces = evidence_documents(answer)
    action = recommended_action(answer)
    strategy = defense_strategy(answer)
    certainty = certainty_level(established, reasoning, depends)
    layers = source_layers_analysis(answer)

    return {
        "active": True,
        "name": "Expert Juriste droit du travail V0 renforce",
        "prompt_version": JURISTE_PROMPT_VERSION,
        "prompt_contract": JURISTE_PROMPT_CONTRACT,
        "response_courte": response,
        "reponse_courte": response,
        "qualification_juridique_situation": qualification(answer),
        "sources_par_couche": layers,
        "ce_qui_est_certain": established,
        "ce_qui_est_etabli_par_sources": established,
        "ce_qui_depend_des_textes_locaux": depends,
        "ce_qui_depend_accord_statut_element_manquant": depends,
        "niveau_de_certitude_detaille": certainty,
        "sources_a_verifier": sources,
        "sources_utilisees": sources,
        "pieces_a_recuperer": pieces,
        "raisonnement_juridique_prudent": reasoning,
        "analyse_et_raisonnement": reasoning,
        "risques_points_vigilance": risks,
        "strategie_de_defense": strategy,
        "action_conseillee": action,
        "position_de_travail_proposee": position,
        "questions_a_poser_direction": direction_questions(answer),
        "questions_a_poser": direction_questions(answer),
        "niveau_de_confiance": answer.get("confidence", "a verifier"),
        "limites": expert_limits,
    }
