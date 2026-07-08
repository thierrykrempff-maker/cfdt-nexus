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
    "cssct_securite",
    "droit_syndical",
    "disciplinaire",
    "inaptitude_reclassement",
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
    "defense",
    "sanction",
    "disciplinaire",
    "reorganisation",
    "consultation",
    "negociation",
    "signer",
    "cssct",
]

JURISTE_PROMPT_VERSION = "EXPERT_JURISTE_CFDT_NEXUS_V1"
JURISTE_PROMPT_CONTRACT = "agents/juriste/EXPERT_JURISTE_CFDT_NEXUS_V1.md"

MODE_DEFENSE = "DEFENSE_SALARIE"
MODE_NEGOCIATION = "NEGOCIATION_ACCORD"
MODE_CSE = "CSE_CSSCT"
BUSINESS_MODE_ORDER = [MODE_NEGOCIATION, MODE_CSE, MODE_DEFENSE]

SOURCE_LAYER_ORDER = [
    "accord_entreprise",
    "convention_collective",
    "code_travail",
    "jurisprudence",
    "prudhommes",
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


def route_intents(answer: dict[str, Any]) -> set[str]:
    route = answer.get("route", {})
    return {str(intent) for intent in route.get("intents", [])}


def detect_business_modes(answer: dict[str, Any]) -> list[str]:
    domains = route_domains(answer)
    intents = route_intents(answer)
    query = normalize(answer.get("query", ""))
    modes: list[str] = []
    if "preparer_negociation" in intents or has_any(
        query,
        [
            "projet d accord",
            "projet accord",
            "accord reduisant",
            "avenant",
            "negociation",
            "avant de signer",
            "signature",
            "signer",
            "contre proposition",
            "contre-proposition",
        ],
    ):
        modes.append(MODE_NEGOCIATION)
    cse_collective_signal = "cssct_securite" in domains or (
        "cse" in domains
        and has_any(
            query,
            [
                "consultation",
                "information consultation",
                "reorganisation",
                "suppression de postes",
                "changement d horaires",
                "documents demander",
                "questions poser",
                "ordre du jour",
                "point cse",
                "proces verbal",
                "pv",
            ],
        )
    )
    if cse_collective_signal or "preparer_cse" in intents or "preparer_cssct" in intents or has_any(
        query,
        [
            "cssct",
            "consultation",
            "information consultation",
            "reorganisation",
            "suppression de postes",
            "changement d horaires",
            "documents demander",
            "questions poser",
            "ordre du jour",
            "point cse",
            "proces verbal",
            "pv",
        ],
    ):
        modes.append(MODE_CSE)
    if domains & {"disciplinaire", "classification_carriere", "inaptitude_reclassement"} or "analyser_situation_individuelle" in intents or has_any(
        query,
        [
            "defense",
            "defendre",
            "sanction",
            "disciplinaire",
            "erreur de manipulation",
            "contester",
            "plusieurs salaries",
            "mal calcule",
            "construire le dossier",
            "dossier salarie",
        ],
    ):
        modes.append(MODE_DEFENSE)
    if not modes and applies(answer):
        modes.append(MODE_DEFENSE)
    return [mode for mode in BUSINESS_MODE_ORDER if mode in set(modes)]


def primary_business_mode(answer: dict[str, Any]) -> str | None:
    modes = detect_business_modes(answer)
    return modes[0] if modes else None


def short_response(answer: dict[str, Any]) -> str:
    domains = route_domains(answer)
    query = normalize(answer.get("query", ""))
    router_short = answer.get("short_answer")
    primary_mode = primary_business_mode(answer)
    if primary_mode == MODE_NEGOCIATION:
        return (
            "Avant toute signature, Nexus doit comparer le projet avec les droits existants, mesurer les pertes "
            "ou garanties pour les salaries, identifier les clauses a securiser et preparer une position de "
            "negociation. La decision politique de signer reste au delegue syndical."
        )
    if primary_mode == MODE_CSE:
        return (
            "Le dossier doit etre traite comme un point CSE/CSSCT a documenter: demander les pieces utiles, "
            "verifier s'il s'agit d'une information ou consultation, preparer les questions et faire tracer les "
            "engagements ou reserves au proces-verbal."
        )
    if primary_mode == MODE_DEFENSE and "disciplinaire" in domains:
        return (
            "La defense doit partir des faits precis reproches, des preuves communiquees, du respect de la procedure "
            "et de la proportionnalite de la sanction eventuelle. A ce stade, il faut securiser le dossier avant "
            "toute position definitive."
        )
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
    primary_mode = primary_business_mode(answer)
    if primary_mode == MODE_NEGOCIATION:
        return "Projet d'accord ou d'avenant a analyser avant position syndicale, avec comparaison droits actuels / modifications proposees."
    if primary_mode == MODE_CSE:
        return "Point CSE/CSSCT ou dossier collectif a preparer, avec verification des documents, informations, consultations et impacts salaries."
    if primary_mode == MODE_DEFENSE and "disciplinaire" in domains:
        return "Situation disciplinaire individuelle ou collective a preparer sous l'angle des faits, preuves, procedure, droits de defense et proportionnalite."
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


def source_context_text(source: dict[str, Any]) -> str:
    return normalize(
        " ".join(
            str(part)
            for part in [
                source.get("document"),
                source.get("document_type"),
                source.get("source_layer"),
                source.get("source_layer_label"),
                source.get("article"),
                source.get("article_or_section"),
                source.get("location"),
                source.get("excerpt"),
                source.get("summary"),
                source.get("resume_court"),
                source.get("principle_summary"),
                source.get("theme"),
                source.get("ranking_reasons"),
            ]
            if part
        )
    )


def legal_terms_for_answer(answer: dict[str, Any]) -> list[str]:
    domains = route_domains(answer)
    query = normalize(answer.get("query", ""))
    terms: list[str] = []
    if "astreinte" in domains or "astreinte" in query:
        terms.extend(
            [
                "astreinte",
                "intervention",
                "temps de travail effectif",
                "repos",
                "reprise",
                "contrepartie",
                "l3121-9",
                "l3121-10",
                "l3121-11",
                "l3131",
                "nuit",
                "majoration",
            ]
        )
    if "temps_travail" in domains:
        terms.extend(["temps de travail", "travail effectif", "repos", "horaire", "duree", "5x8", "35 h"])
    if "paie_remuneration" in domains:
        terms.extend(["paie", "bulletin", "majoration", "prime", "salaire", "heures supplementaires", "nuit", "dimanche"])
    if "disciplinaire" in domains:
        terms.extend(["sanction", "disciplinaire", "faute", "procedure", "entretien", "grief", "reglement interieur"])
    if "classification_carriere" in domains:
        terms.extend(["classification", "coefficient", "fonctions", "fiche de poste", "qualification", "emploi"])
    if "cse" in domains:
        terms.extend(["cse", "consultation", "information", "reorganisation", "suppression de poste", "horaires", "pv"])
    if "cssct_securite" in domains:
        terms.extend(["cssct", "sante", "securite", "risque", "fatigue", "conditions de travail"])
    if not terms:
        terms.extend([domain for domain in domains if domain != "bible_accords"])
    return unique(terms, limit=30)


def source_relevance_score(answer: dict[str, Any], source: dict[str, Any]) -> tuple[int, list[str]]:
    context = source_context_text(source)
    layer = normalize(source.get("source_layer") or source.get("document_type"))
    document = normalize(source.get("document"))
    terms = legal_terms_for_answer(answer)
    score = 0
    reasons: list[str] = []
    for term in terms:
        normalized = normalize(term)
        if normalized and normalized in context:
            score += 8
            reasons.append(f"terme utile: {term}")
    if layer == "code_travail":
        score += 20
        reasons.append("source normative Code du travail")
    elif layer in {"accord_entreprise", "convention_collective"}:
        score += 16
        reasons.append("source collective applicable au socle Nexus")
    elif layer == "jurisprudence":
        score += 14
        reasons.append("decision officielle utile pour l'interpretation")
    elif layer in {"pratique_officielle", "pratique"}:
        score += 4
        reasons.append("source explicative ou pratique")

    domains = route_domains(answer)
    if "disciplinaire" in domains and has_any(context, ["reglement interieur", "sanction", "disciplinaire", "l1331", "l1332"]):
        score += 28
        reasons.append("cible directement la procedure ou sanction disciplinaire")
    if "astreinte" in domains and has_any(context, ["astreinte", "l3121-9", "l3121-10", "l3121-11"]):
        score += 30
        reasons.append("cible directement l'astreinte ou l'intervention")
    if "temps_travail" in domains and has_any(context, ["repos", "travail effectif", "temps de travail", "l3131", "l3132"]):
        score += 18
        reasons.append("cible le temps de travail ou le repos")
    if "classification_carriere" in domains and has_any(context, ["classification", "coefficient", "fonctions", "emploi"]):
        score += 28
        reasons.append("cible directement la classification")
    if "cse" in domains and has_any(context, ["cse", "consultation", "information", "reorganisation", "pv"]):
        score += 24
        reasons.append("cible directement le sujet CSE")
    if "paie_remuneration" in domains and has_any(context, ["majoration", "bulletin", "prime", "salaire", "heures supplementaires"]):
        score += 18
        reasons.append("utile pour le controle paie")

    if "disciplinaire" in domains and "cse" in document and not has_any(context, ["sanction", "disciplinaire", "faute"]):
        score -= 40
        reasons.append("source CSE non determinante pour une sanction individuelle")
    if "cse" in domains and not has_any(context, ["cse", "consultation", "information consultation", "reorganisation", "pv"]):
        if score >= 42:
            score = 35
            reasons.append("utile pour le contexte d'impact, mais non determinante sur les droits CSE")
    if "teletravail" in document and not has_any(answer.get("query", ""), ["teletravail", "travail a distance"]):
        score -= 35
        reasons.append("document lexicalement proche mais hors sujet probable")
    if not source.get("excerpt") and layer not in {"code_travail", "jurisprudence"}:
        score -= 4
        reasons.append("extrait absent ou faible")
    return score, unique(reasons, limit=5)


def source_selection(answer: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    buckets = {
        "source_principale": [],
        "source_complementaire": [],
        "source_contextuelle": [],
        "source_ecartee": [],
    }
    for source in answer.get("sources", []):
        if not isinstance(source, dict):
            continue
        score, reasons = source_relevance_score(answer, source)
        label = source_label_for_layer(source)
        selected = {
            "source": label,
            "source_layer": source.get("source_layer"),
            "article": source.get("article") or source.get("article_or_section"),
            "role_score": score,
            "raison": "; ".join(reasons) or "Source conservee comme contexte documentaire.",
            "extrait": str(source.get("excerpt") or "")[:420],
            "decision_id": source.get("judilibre_id") or source.get("official_id"),
            "source_ref": source,
        }
        if score >= 42:
            buckets["source_principale"].append(selected)
        elif score >= 24:
            buckets["source_complementaire"].append(selected)
        elif score >= 10:
            buckets["source_contextuelle"].append(selected)
        else:
            selected["raison"] = selected["raison"] + " Source non determinante pour le raisonnement juridique."
            buckets["source_ecartee"].append(selected)
    for key, values in buckets.items():
        buckets[key] = sorted(values, key=lambda item: int(item.get("role_score") or 0), reverse=True)[:8]
    return buckets


def selected_source_refs(selection: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    refs = []
    for key in ["source_principale", "source_complementaire"]:
        for item in selection.get(key, []):
            source = item.get("source_ref")
            if isinstance(source, dict):
                refs.append(source)
    return refs


def public_source_selection(selection: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    public: dict[str, list[dict[str, Any]]] = {}
    for key, values in selection.items():
        public[key] = [
            {name: value for name, value in item.items() if name != "source_ref"}
            for item in values
        ]
    return public


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


def legal_reasoning(answer: dict[str, Any], selection: dict[str, list[dict[str, Any]]] | None = None) -> list[str]:
    domains = route_domains(answer)
    query = normalize(answer.get("query", ""))
    primary_mode = primary_business_mode(answer)
    if selection is None:
        selection = source_selection(answer)
    rules = applicable_rules(answer, selection)
    applications = fact_application(answer, selection)
    conclusion = provisional_legal_conclusion(answer)
    argued = [
        "Regle certaine: l'analyse ci-dessous ne s'appuie que sur les sources principales ou complementaires retenues par l'Expert Juriste.",
        *[f"Regle applicable: {rule}" for rule in rules[:5]],
        *applications[:5],
        f"Conclusion provisoire: {conclusion['position']} - {conclusion['pourquoi']}",
    ]
    if primary_mode == MODE_NEGOCIATION:
        return unique(
            [
                *argued,
            "Regle certaine: un projet d'accord doit etre compare aux droits existants et aux normes superieures avant position syndicale.",
            "Interpretation: une reduction du repos ou une modification d'horaires constitue un point de vigilance fort pour les salaries.",
            "Hypothese: le projet peut etre negociable seulement si les garanties, contreparties, perimetres et suivis sont ecrits et controles.",
            "Information manquante: texte complet du projet, droits actuels, categories concernees, justification direction et impacts chiffrables.",
            ],
            limit=12,
        )
    if primary_mode == MODE_CSE:
        return unique(
            [
                *argued,
            "Regle certaine: un dossier collectif presente au CSE doit etre analyse a partir des documents transmis, des impacts salaries et des questions a inscrire.",
            "Interpretation: une reorganisation avec postes ou horaires modifiees peut appeler information, consultation ou suivi CSE/CSSCT selon ses effets.",
            "Hypothese: les enjeux sante-securite deviennent prioritaires si les horaires, charges, effectifs ou conditions de travail sont modifies.",
            "Information manquante: note projet, calendrier, effectifs avant/apres, horaires cibles, analyse des risques et consequences par categorie.",
            ],
            limit=12,
        )
    if primary_mode == MODE_DEFENSE and "disciplinaire" in domains:
        return unique(
            [
                *argued,
            "Regle certaine: une defense disciplinaire exige d'abord des faits dates, des preuves communiquees et le controle des droits de defense.",
            "Interpretation: une erreur de manipulation ne justifie pas automatiquement une sanction si le contexte, les consignes, la formation ou l'organisation expliquent l'incident.",
            "Hypothese: la sanction peut etre contestable si la procedure, la preuve ou la proportionnalite sont fragiles.",
            "Information manquante: convocation, faits reproches, preuves, antecedents, consignes, formation et consequences reelles de l'erreur.",
            ],
            limit=12,
        )
    if "droit_syndical" in domains and "reunion" in query:
        return unique(
            [
                *argued,
            "Regle certaine: la question doit etre qualifiee comme exercice d'un mandat ou participation CSE avant d'etre traitee comme sujet de repos.",
            "Interpretation: le traitement du temps depend de la nature de la reunion et du role exact du salarie.",
            "Hypothese: si la participation est liee au mandat, le temps ne se traite pas comme une simple initiative personnelle.",
            "Information manquante: texte local ou conventionnel fixant le traitement lorsque la reunion tombe sur un repos 5x8.",
            ],
            limit=12,
        )
    if {"temps_travail", "astreinte"}.issubset(domains):
        return unique(
            [
                *argued,
            "Regle certaine: l'intervention d'astreinte, le repos et la paie doivent etre controles separement.",
            "Interpretation: la reprise apres intervention ne peut etre appreciee qu'avec les heures reelles de fin et de reprise.",
            "Hypothese: les temps annexes ne sont a retenir que si la source applicable les integre.",
            "Information manquante: accord d'astreinte applicable, pointage, compteur et bulletin de la periode.",
            ],
            limit=12,
        )
    if "classification_carriere" in domains:
        return unique(
            [
                *argued,
            "Regle certaine: une demande de classification suppose une comparaison entre classement actuel et fonctions reelles.",
            "Interpretation: l'ecart doit etre rattache a des criteres objectifs du texte applicable, pas seulement a un ressenti.",
            "Hypothese: des fonctions depassant durablement la fiche de poste peuvent justifier une demande de reexamen motivee.",
            "Information manquante: criteres conventionnels, coefficient actuel et preuves des missions exercees.",
            ],
            limit=12,
        )
    return unique(
        [
            *argued,
            "Regle certaine: Nexus ne peut raisonner que sur les sources locales retrouvees.",
            "Information manquante: faits exacts et texte applicable a la situation.",
        ],
        limit=10,
    )


def defense_strategy(answer: dict[str, Any]) -> dict[str, list[str] | str]:
    domains = route_domains(answer)
    query = normalize(answer.get("query", ""))
    modes = set(detect_business_modes(answer))
    if MODE_NEGOCIATION in modes:
        return {
            "argument_principal": (
                "Refuser de raisonner sur une signature tant que le projet n'est pas compare aux droits actuels, "
                "aux normes superieures et aux impacts concrets pour les salaries."
            ),
            "arguments_complementaires": [
                "Exiger un tableau avant/apres des droits modifies.",
                "Demander le perimetre exact, les categories concernees, les garanties de repos et les contreparties.",
                "Conditionner la discussion a un suivi CSE/CSSCT et a une clause de revoyure.",
            ],
            "position_probable_direction": (
                "La direction peut soutenir que la reduction du repos ou la souplesse proposee est necessaire a la continuite d'activite."
            ),
            "contre_arguments": [
                "Demander la preuve du besoin operationnel et les alternatives etudiees.",
                "Rappeler qu'une perte de protection doit etre strictement encadree, compensee et controlable.",
            ],
        }
    if MODE_CSE in modes:
        return {
            "argument_principal": (
                "Obtenir une information complete et loyale avant toute discussion de fond sur la reorganisation."
            ),
            "arguments_complementaires": [
                "Demander les impacts sur emploi, horaires, charge, competences, remuneration et sante-securite.",
                "Faire inscrire au proces-verbal les documents demandes, reponses donnees et reserves des elus.",
                "Relancer par ecrit si les donnees restent incompletes.",
            ],
            "position_probable_direction": (
                "La direction peut soutenir que le projet releve de son pouvoir d'organisation ou que les informations transmises suffisent."
            ),
            "contre_arguments": [
                "Ramener la discussion aux impacts concrets pour les salaries et aux documents manquants.",
                "Demander des indicateurs de suivi et des engagements dates.",
            ],
        }
    if "disciplinaire" in domains:
        return {
            "argument_principal": (
                "Contester toute qualification disciplinaire automatique en exigeant des faits precis, une preuve loyale, "
                "des consignes claires et une sanction proportionnee."
            ),
            "arguments_complementaires": [
                "Verifier si la procedure, les delais et les droits de defense ont ete respectes.",
                "Documenter le contexte de l'erreur: formation, urgence, charge, effectifs, consignes contradictoires.",
                "Comparer la reaction de la direction avec les pratiques anterieures pour des faits comparables.",
            ],
            "position_probable_direction": (
                "La direction peut soutenir que le salarie connaissait la procedure et que l'erreur a cree un risque ou un dommage."
            ),
            "contre_arguments": [
                "Demander les preuves exactes et la consigne applicable au moment des faits.",
                "Rappeler qu'une erreur ne suffit pas sans faute et proportionnalite demontrees.",
            ],
        }
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


def litigation_sources(answer: dict[str, Any], selection: dict[str, list[dict[str, Any]]] | None = None) -> list[dict[str, Any]]:
    candidate_sources = selected_source_refs(selection) if selection else answer.get("sources", [])
    sources = []
    for source in candidate_sources:
        if not isinstance(source, dict):
            continue
        layer = normalize(source.get("source_layer") or source.get("document_type"))
        document = normalize(source.get("document"))
        if layer in {"jurisprudence", "prudhommes"} or "cour de cassation" in document or "prud" in document:
            sources.append(source)
    return sources[:3]


def first_source_value(source: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        value = source.get(key)
        if value:
            return value
    return None


def as_text_list(value: Any, fallback: str) -> list[str]:
    if isinstance(value, list):
        return unique(str(item) for item in value if item)
    if isinstance(value, tuple):
        return unique(str(item) for item in value if item)
    if value:
        return [str(value)]
    return [fallback]


def decision_reference(source: dict[str, Any]) -> str:
    parts = [
        source.get("juridiction") or source.get("document"),
        source.get("chamber"),
        source.get("decision_date"),
        f"pourvoi {source.get('case_number')}" if source.get("case_number") else None,
        source.get("official_id"),
    ]
    return " | ".join(str(part) for part in parts if part)


def procedural_status(source: dict[str, Any]) -> str:
    value = first_source_value(
        source,
        [
            "procedural_status",
            "etat_procedure",
            "appeal_status",
            "pourvoi_status",
            "decision_status",
        ],
    )
    if value:
        return str(value)
    if source.get("source_layer") == "prudhommes":
        return "Information non disponible dans Nexus: verifier appel, confirmation, infirmation ou cassation."
    return "Information non disponible dans les metadonnees Nexus."


def jurisprudence_question_for_answer(answer: dict[str, Any]) -> str:
    domains = route_domains(answer)
    if "astreinte" in domains:
        return "Dans quelles conditions une intervention d'astreinte affecte-t-elle le temps de travail, le repos et les droits associes ?"
    if "disciplinaire" in domains:
        return "La faute reprochee et la procedure suffisent-elles a justifier une sanction proportionnee ?"
    if "classification_carriere" in domains:
        return "Les fonctions reellement exercees justifient-elles une classification differente ?"
    if "cse" in domains:
        return "Quels droits d'information/consultation ou de preuve sont utiles pour le dossier collectif ?"
    return "Quelle interpretation la decision peut-elle apporter au dossier Nexus ?"


def jurisprudence_use_for_defense(answer: dict[str, Any], source: dict[str, Any]) -> str:
    domains = route_domains(answer)
    excerpt = str(source.get("summary") or source.get("resume_court") or source.get("principle_summary") or source.get("excerpt") or "")
    if "astreinte" in domains:
        return (
            "La decision est utile seulement si ses faits portent aussi sur astreinte, intervention, repos ou temps de travail effectif. "
            "Elle sert alors a argumenter la separation entre disponibilite, intervention et consequences temps/paie."
        )
    if "disciplinaire" in domains:
        return (
            "La decision peut aider a discuter la preuve de la faute, la procedure ou la proportionnalite, sans transformer l'argument d'une partie en regle."
        )
    if "classification_carriere" in domains:
        return "La decision peut aider a comparer fonctions reelles, criteres de classement et preuves retenues."
    if "cse" in domains:
        return "La decision peut aider a anticiper la discussion sur information, consultation ou preuve des impacts collectifs."
    return "Apport a verifier a partir de l'extrait et du texte complet avant reutilisation."


def retained_jurisprudence_analysis(
    answer: dict[str, Any],
    selection: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    analyses: list[dict[str, Any]] = []
    for source in litigation_sources(answer, selection):
        excerpt = str(
            source.get("summary")
            or source.get("resume_court")
            or source.get("principle_summary")
            or source.get("solution")
            or source.get("excerpt")
            or ""
        )
        analyses.append(
            {
                "decision": decision_reference(source),
                "question_juridique": jurisprudence_question_for_answer(answer),
                "faits_pertinents": (
                    "Faits isoles par Nexus: " + str(first_source_value(source, ["faits", "facts", "faits_etablis"]))
                    if first_source_value(source, ["faits", "facts", "faits_etablis"])
                    else "Nexus ne dispose pas de faits detailles isoles; comparer avec prudence a partir de l'extrait."
                ),
                "solution": excerpt[:700] if excerpt else "Solution non isolee dans les metadonnees Nexus.",
                "ressemblance_avec_dossier": litigation_similarity(answer, source),
                "difference_a_verifier": [
                    "Verifier si les horaires, la preuve, le statut du salarie et la source applicable sont comparables.",
                    "Verifier la portee procedurale de la decision et son eventuelle confirmation, infirmation ou cassation.",
                ],
                "apport_reel_a_la_defense": jurisprudence_use_for_defense(answer, source),
                "statut_procedural": procedural_status(source),
            }
        )
    return analyses


def adversarial_litigation_analysis(
    answer: dict[str, Any],
    strategy: dict[str, Any],
    selection: dict[str, list[dict[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    analyses: list[dict[str, Any]] = []
    for source in litigation_sources(answer, selection):
        employee_args = first_source_value(
            source,
            ["argumentation_salarie", "arguments_salarie", "demandes_salarie", "employee_arguments", "claimant_arguments"],
        )
        employer_args = first_source_value(
            source,
            ["argumentation_employeur", "arguments_employeur", "defense_employeur", "employer_arguments", "defendant_arguments"],
        )
        judge_reasoning = first_source_value(
            source,
            ["raisonnement_juge", "motifs", "principle_summary", "summary", "resume_court", "solution", "excerpt"],
        )
        facts = first_source_value(source, ["faits", "facts", "faits_etablis"])
        proof = first_source_value(source, ["preuves_determinantes", "proof", "evidence", "elements_preuve"])
        result = first_source_value(source, ["resultat", "solution", "decision_type", "publication"])
        analyses.append(
            {
                "decision": decision_reference(source),
                "source_layer": source.get("source_layer"),
                "statut_procedural": procedural_status(source),
                "argumentation_salarie": as_text_list(
                    employee_args,
                    "Non disponible dans les donnees Nexus: ne pas reconstituer l'argument du salarie sans lecture de la decision complete.",
                ),
                "argumentation_employeur": as_text_list(
                    employer_args,
                    "Non disponible dans les donnees Nexus: anticiper la contradiction via la strategie de defense, sans l'attribuer a cette decision.",
                ),
                "raisonnement_du_juge": {
                    "faits_etablis": as_text_list(
                        facts,
                        "Faits etablis non isoles dans les metadonnees Nexus: verifier le texte complet.",
                    ),
                    "regle_appliquee": as_text_list(
                        judge_reasoning,
                        "Regle ou motif non isole dans les metadonnees Nexus.",
                    ),
                    "preuves_determinantes": as_text_list(
                        proof,
                        "Preuves determinantes non identifiees automatiquement par Nexus.",
                    ),
                    "resultat": as_text_list(result, "Resultat procedural non isole dans les metadonnees Nexus."),
                },
                "enseignements_dossier_nexus": {
                    "ressemblances": litigation_similarity(answer, source),
                    "differences_importantes": [
                        "Comparer les faits reels du dossier avec les faits de la decision avant reutilisation.",
                        "Verifier si la decision porte sur le meme type de contrat, d'organisation du travail et de preuve.",
                    ],
                    "arguments_reutilisables": reusable_litigation_arguments(source),
                    "arguments_adverses_a_anticiper": as_text_list(
                        strategy.get("position_probable_direction"),
                        "Aucun argument adverse specifique n'a ete extrait.",
                    ),
                    "preuves_qui_font_la_difference": [
                        "Chronologie precise.",
                        "Pieces contemporaines: planning, pointage, bulletin, consignes, mails ou comptes rendus selon le sujet.",
                    ],
                    "faiblesses_a_eviter": [
                        "Presenter une proximite de mots comme une proximite juridique.",
                        "Transformer l'argument d'une partie en regle de droit.",
                        "Utiliser une decision isolee sans verifier sa portee et son historique procedural.",
                    ],
                },
                "source_quality_warning": source.get("source_quality_warning"),
            }
        )
    return analyses


def litigation_similarity(answer: dict[str, Any], source: dict[str, Any]) -> list[str]:
    domains = [domain for domain in answer.get("route", {}).get("domains", []) if domain != "bible_accords"]
    theme = source.get("theme") or source.get("document")
    values = []
    if domains:
        values.append("Meme zone d'analyse Nexus: " + ", ".join(str(domain) for domain in domains[:4]) + ".")
    if theme:
        values.append("Theme ou document rapproche: " + str(theme)[:220])
    if source.get("query"):
        values.append("Decision remontee par recherche: " + str(source["query"])[:220])
    return values or ["Ressemblance non qualifiee automatiquement: verifier les faits de la decision."]


def reusable_litigation_arguments(source: dict[str, Any]) -> list[str]:
    values = []
    for key in ["principle_summary", "summary", "resume_court", "solution", "excerpt"]:
        value = source.get(key)
        if value:
            values.append("A verifier et reformuler comme argument: " + str(value)[:420])
            break
    if not values:
        values.append("Aucun argument reutilisable n'est extrait automatiquement de cette source.")
    return values


def source_briefs(answer: dict[str, Any], limit: int = 5) -> list[str]:
    return source_documents(answer, limit=limit)


def findings(answer: dict[str, Any], limit: int | None = None) -> list[str]:
    return unique((str(item) for item in answer.get("findings", []) if item), limit=limit)


def missing_facts(answer: dict[str, Any], depends: list[str]) -> list[str]:
    values = list(depends)
    if not answer.get("documents_to_request"):
        values.append("Information manquante: documents du dossier non encore fournis ou non identifies par Nexus.")
    values.extend(str(item) for item in answer.get("questions_to_ask", [])[:4])
    return unique(values, limit=10)


def source_rule_statement(source: dict[str, Any], answer: dict[str, Any]) -> str:
    domains = route_domains(answer)
    label = source_label_for_layer(source)
    context = source_context_text(source)
    excerpt = str(source.get("excerpt") or "").strip()
    suffix = f" Extrait utile: {excerpt[:260]}" if excerpt else ""
    if "astreinte" in domains and has_any(context, ["l3121-9", "astreinte"]):
        return (
            f"{label}: la source sert a distinguer la periode d'astreinte de l'intervention effective "
            f"et a verifier les contreparties applicables.{suffix}"
        )
    if "astreinte" in domains and has_any(context, ["l3121-10", "intervention", "temps de travail effectif"]):
        return (
            f"{label}: la source sert a qualifier l'intervention comme temps a traiter distinctement de la simple disponibilite d'astreinte.{suffix}"
        )
    if "temps_travail" in domains and has_any(context, ["repos", "l3131", "l3132", "travail effectif", "temps de travail"]):
        return f"{label}: la source encadre le temps de travail, le repos ou la reprise apres interruption.{suffix}"
    if "paie_remuneration" in domains and has_any(context, ["majoration", "bulletin", "prime", "salaire", "heures supplementaires"]):
        return f"{label}: la source aide a controler la rubrique paie, les majorations ou les contreparties dues.{suffix}"
    if "disciplinaire" in domains and has_any(context, ["sanction", "disciplinaire", "reglement interieur", "l1331", "l1332"]):
        return f"{label}: la source sert a verifier la qualification disciplinaire, la procedure, les griefs et la proportionnalite.{suffix}"
    if "classification_carriere" in domains and has_any(context, ["classification", "coefficient", "fonctions", "emploi"]):
        return f"{label}: la source sert a comparer les fonctions reelles, l'emploi ou le coefficient applicable.{suffix}"
    if "cse" in domains and has_any(context, ["cse", "consultation", "information", "reorganisation"]):
        return f"{label}: la source sert a qualifier l'information/consultation et les documents CSE attendus.{suffix}"
    return f"{label}: source retenue pour completer le raisonnement juridique Nexus.{suffix}"


def applicable_rules(answer: dict[str, Any], selection: dict[str, list[dict[str, Any]]] | None = None) -> list[str]:
    if selection is None:
        selection = source_selection(answer)
    selected_refs = selected_source_refs(selection)
    if selected_refs:
        return unique((source_rule_statement(source, answer) for source in selected_refs), limit=8)
    values = []
    for layer in source_layers_analysis(answer):
        label = layer.get("label") or layer.get("source_layer")
        if layer.get("status") == "present":
            values.append(f"{label}: {layer.get('summary')}")
        elif layer.get("source_layer") in {"code_travail", "jurisprudence", "prudhommes"}:
            values.append(f"{label or layer.get('source_layer')}: {layer.get('summary')}")
    if not values:
        values.append("Aucune source applicable distincte n'est suffisante pour conclure sans verification.")
    return unique(values, limit=8)


def facts_from_question(answer: dict[str, Any]) -> list[str]:
    domains = route_domains(answer)
    query = normalize(answer.get("query", ""))
    facts: list[str] = []
    if "astreinte" in domains:
        facts.append("Le salarie est place en astreinte et une intervention effective est indiquee.")
    if "nuit" in query:
        facts.append("L'intervention est signalee comme intervenue la nuit.")
    if "repos" in query and has_any(query, ["interrompu", "reprend", "reprise"]):
        facts.append("Le repos est presente comme interrompu avant une reprise du poste.")
    if "paie_remuneration" in domains:
        facts.append("Le bulletin ou les compteurs paie sont contestes ou a controler.")
    if "disciplinaire" in domains:
        facts.append("La direction reproche une erreur ou un non-respect de procedure au salarie.")
    if "classification_carriere" in domains:
        facts.append("Le salarie invoque un ecart entre fonctions reelles et classification ou fiche de poste.")
    if "cse" in domains:
        facts.append("La direction presente un projet collectif au CSE avec impacts possibles sur emploi, horaires ou organisation.")
    if not facts:
        facts.append("Les faits connus sont ceux de la question; ils doivent etre completes par les pieces du dossier.")
    return unique(facts, limit=8)


def fact_application(answer: dict[str, Any], selection: dict[str, list[dict[str, Any]]]) -> list[str]:
    domains = route_domains(answer)
    query = normalize(answer.get("query", ""))
    applications: list[str] = []
    if "astreinte" in domains:
        applications.extend(
            [
                "Application aux faits: la disponibilite d'astreinte et l'intervention ne doivent pas etre confondues; l'intervention declenche un traitement propre en temps et en paie.",
                "Application aux faits: si l'intervention de nuit a interrompu le repos, il faut recalculer le repos a partir de la fin reelle d'intervention et verifier la base permettant la reprise du poste.",
                "Application aux faits: l'indemnite ou contrepartie d'astreinte ne suffit pas a solder le dossier si du temps d'intervention, des majorations ou une recuperation restent dus.",
            ]
        )
        if not any(item.get("source_layer") == "code_travail" for item in selection.get("source_principale", []) + selection.get("source_complementaire", [])):
            applications.append("Limite d'application: aucun article Code du travail exploitable n'est disponible dans cette reponse; la position repose donc surtout sur les sources locales et la methode de controle.")
    if "disciplinaire" in domains:
        applications.extend(
            [
                "Application aux faits: une erreur de manipulation ne suffit pas, seule, a etablir une faute sanctionnable; il faut verifier la consigne, la formation, le contexte et la preuve.",
                "Application aux faits: la defense doit attaquer d'abord la precision des griefs, puis la procedure et enfin la proportionnalite de la sanction envisagee.",
            ]
        )
    if "classification_carriere" in domains:
        applications.extend(
            [
                "Application aux faits: la contestation devient defendable si les fonctions depassant la fiche de poste sont reelles, durables, prouvees et rattachees aux criteres de classification.",
                "Application aux faits: un simple depannage ou une mission ponctuelle sera plus fragile qu'une responsabilite exercee regulierement.",
            ]
        )
    if MODE_NEGOCIATION in detect_business_modes(answer) or has_any(query, ["reduire le repos", "repos a 9 heures", "repos à 9 heures"]):
        applications.extend(
            [
                "Application aux faits: reduire le repos a 9 heures est un signal de perte de garantie; la delegation doit exiger la base juridique, les cas limites, les compensations et le suivi.",
                "Application aux faits: le projet ne doit pas etre negocie seulement comme une souplesse d'organisation mais comme une modification des protections temps de travail/repos.",
            ]
        )
    if MODE_CSE in detect_business_modes(answer):
        applications.extend(
            [
                "Application aux faits: suppression de postes, changement d'horaires et modification des taches justifient de demander les impacts precis avant de se prononcer.",
                "Application aux faits: les elus doivent obtenir les donnees emploi, charge, horaires, risques et calendrier, puis faire acter les reponses et reserves au PV.",
            ]
        )
    if not applications:
        applications.append("Application aux faits: les sources retenues doivent etre rapprochees des dates, pieces et personnes concernees avant conclusion definitive.")
    return unique(applications, limit=8)


def provisional_legal_conclusion(answer: dict[str, Any]) -> dict[str, str]:
    domains = route_domains(answer)
    modes = set(detect_business_modes(answer))
    query = normalize(answer.get("query", ""))
    if MODE_NEGOCIATION in modes or has_any(query, ["repos a 9 heures", "repos à 9 heures", "reduire le repos"]):
        return {
            "position": "plutot defavorable en l'etat",
            "pourquoi": (
                "un projet qui reduit le repos est une perte potentielle de protection; il ne devrait etre discute qu'avec base juridique, perimetre strict, "
                "contreparties, suivi et garanties ecrites. La decision de signature reste politique et syndicale."
            ),
        }
    if MODE_CSE in modes:
        return {
            "position": "favorable a une exigence d'information complete",
            "pourquoi": (
                "le CSE dispose d'un dossier defendable pour demander pieces, delais, impacts et reponses tracees avant toute position sur une reorganisation "
                "touchant postes, horaires ou taches."
            ),
        }
    if "astreinte" in domains:
        return {
            "position": "plutot favorable au salarie",
            "pourquoi": (
                "si les releves confirment une intervention de nuit suivie d'une reprise sans repos suffisant ou sans paiement distinct, "
                "le meilleur angle est de separer astreinte, intervention, repos et bulletin. La conclusion exacte reste incertaine sur les montants "
                "tant que l'accord, les horaires et le bulletin ne sont pas rapproches."
            ),
        }
    if "disciplinaire" in domains:
        return {
            "position": "plutot favorable a une defense",
            "pourquoi": (
                "une erreur de manipulation n'emporte pas automatiquement sanction si la preuve, la procedure, les consignes, la formation ou "
                "la proportionnalite sont discutables."
            ),
        }
    if "classification_carriere" in domains:
        return {
            "position": "plutot favorable si les fonctions sont durables et prouvees",
            "pourquoi": (
                "la demande peut etre defendable lorsque les fonctions reellement exercees excedent objectivement le classement actuel; elle devient faible "
                "si les faits restent ponctuels ou non rattaches aux criteres conventionnels."
            ),
        }
    return {
        "position": "incertaine",
        "pourquoi": "les sources disponibles ne permettent pas de qualifier une position plus nette sans faits et pieces complementaires.",
    }


def argued_short_response(answer: dict[str, Any], conclusion: dict[str, str]) -> str:
    domains = route_domains(answer)
    if conclusion.get("position") == "plutot defavorable en l'etat":
        return (
            "La position juridique de travail est defavorable en l'etat: reduire le repos constitue une perte potentielle de protection et ne peut pas etre "
            "analyse comme une simple souplesse d'organisation. Il faut exiger la base juridique, le perimetre, les contreparties et les garanties ecrites."
        )
    if conclusion.get("position") == "favorable a une exigence d'information complete":
        return (
            "Le CSE dispose d'un angle solide pour refuser une discussion superficielle: suppression de postes, horaires et taches exigent documents, impacts, "
            "delais utiles et reponses tracees. La premiere action est une demande ecrite de pieces et de questions a inscrire au PV."
        )
    if "astreinte" in domains:
        return (
            "La position provisoire est plutot favorable au salarie: une astreinte n'est pas la meme chose que l'intervention realisee pendant l'astreinte. "
            "L'intervention doit etre isolee, tracee et controlee comme du temps a traiter en paie; si elle interrompt le repos puis que le salarie reprend "
            "son poste, la regularite de la reprise et du compteur repos devient le point central. Le premier acte concret est de rapprocher releve "
            "d'intervention, planning de reprise, accord d'astreinte, compteur et bulletin."
        )
    if "disciplinaire" in domains:
        return (
            "Le dossier est defendable si la direction se contente d'invoquer une erreur ou un non-respect de procedure sans preuve precise, formation claire "
            "et sanction proportionnee. Le meilleur angle est de discuter les faits, le contexte de travail et la procedure avant d'admettre une faute."
        )
    if "classification_carriere" in domains:
        return (
            "La contestation est juridiquement defendable si les fonctions reellement exercees depassent durablement la fiche de poste et correspondent aux "
            "criteres d'un classement superieur. Le meilleur argument est un tableau fonctions reelles / criteres / preuves."
        )
    return short_response(answer)


def defense_argumentation_detail(answer: dict[str, Any], strategy: dict[str, Any]) -> dict[str, Any]:
    domains = route_domains(answer)
    modes = set(detect_business_modes(answer))
    proof = "Chronologie precise et piece contemporaine directement liee au fait."
    weakness = "Le dossier reste fragile si les faits ou la source applicable ne sont pas prouves."
    tipping = "Une piece datee, objective et concordante peut faire basculer l'analyse."
    if MODE_NEGOCIATION in modes:
        proof = "Projet complet, tableau avant/apres, justification operationnelle, categories concernees et impacts repos/paie."
        weakness = "La faiblesse principale serait de negocier sur un texte incomplet ou sans chiffrage des impacts."
        tipping = "La preuve qui fait basculer: demonstration que la reduction de repos cree une perte de protection non compensee ou non conforme."
    elif MODE_CSE in modes:
        proof = "Note projet, effectifs avant/apres, planning cible, impacts par metier, analyse de risques et calendrier."
        weakness = "La faiblesse principale serait une discussion CSE sans documents suffisants ni delai utile."
        tipping = "La preuve qui fait basculer: impacts concrets sur postes, horaires, charge ou sante non documentes par la direction."
    elif "astreinte" in domains:
        proof = "Releve d'appel/intervention, heure de fin, planning de reprise, compteur repos et bulletin detaille."
        weakness = "La faiblesse principale serait l'absence de trace horaire ou une clause d'accord prevoyant une derogation encadree."
        tipping = "La preuve qui fait basculer: intervention de nuit tracee, reprise imposee et absence de repos ou de paiement distinct."
    elif "disciplinaire" in domains:
        proof = "Convocation, griefs ecrits, preuves direction, consignes applicables, formation et elements de contexte."
        weakness = "La faiblesse serait une faute clairement prouvee, grave, repetee ou precedee de consignes non ambigues."
        tipping = "La preuve qui fait basculer: absence de formation/consigne claire, pression d'organisation ou incoherence des griefs."
    elif "classification_carriere" in domains:
        proof = "Fiche de poste, missions reelles datees, preuves de responsabilite/autonomie et comparaison avec criteres de classification."
        weakness = "La faiblesse serait le caractere ponctuel ou non prouve des fonctions invoquees."
        tipping = "La preuve qui fait basculer: missions superieures exercees regulierement et reconnues dans des ecrits."
    return {
        "argument_principal_salarie": strategy.get("argument_principal"),
        "arguments_complementaires": strategy.get("arguments_complementaires", []),
        "argument_probable_employeur": strategy.get("position_probable_direction"),
        "reponse_argument_employeur": strategy.get("contre_arguments", []),
        "faiblesse_du_dossier": weakness,
        "preuve_pouvant_faire_basculer": tipping,
        "preuve_prioritaire": proof,
    }


def ordered_action_strategy(answer: dict[str, Any], pieces: list[str], action: list[str]) -> list[str]:
    domains = route_domains(answer)
    modes = set(detect_business_modes(answer))
    if MODE_NEGOCIATION in modes:
        return [
            "Action immediate: demander le projet d'accord complet et un tableau droits actuels / droits proposes.",
            "Demande ecrite: exiger la base juridique de la reduction du repos, le perimetre et les categories concernees.",
            "Pieces a securiser: accord actuel, projet, plannings, impacts repos/paie, justification operationnelle et alternatives.",
            "Intervention DS/CSE: consulter les salaries concernes et demander un suivi CSE/CSSCT si les impacts sont collectifs.",
            "Contestation: refuser une lecture trop generale si les clauses sont vagues, non controlees ou moins protectrices.",
            "Escalade eventuelle: appui juridique avant signature si le texte touche au repos, a la sante ou a des garanties imperatives.",
        ]
    if MODE_CSE in modes:
        return [
            "Action immediate: demander par ecrit les documents manquants avant la reunion ou en debut de seance.",
            "Demande ecrite: obtenir impacts emploi, horaires, charge, competences, calendrier et mesures d'accompagnement.",
            "Pieces a securiser: note projet, organigrammes avant/apres, planning cible, analyse de risques et indicateurs de suivi.",
            "Intervention DS/CSE: poser les questions prioritaires et faire inscrire reponses, reserves et engagements au PV.",
            "Contestation: demander report ou relance si les informations ne permettent pas une discussion utile.",
            "Escalade eventuelle: solliciter appui juridique ou expertise selon l'ampleur et les impacts du projet.",
        ]
    if "astreinte" in domains:
        return [
            "Action immediate: figer la chronologie appel/intervention/fin/reprise et demander le releve d'intervention.",
            "Demande ecrite: demander a la direction la disposition d'accord appliquee, le traitement repos et le detail de paie.",
            "Pieces a securiser: planning, pointage, compteur repos, bulletin, recapitulatif astreinte et preuve de l'appel.",
            "Intervention DS/CSE: porter le sujet si plusieurs salaries ou une pratique de reprise apres intervention sont concernes.",
            "Contestation: demander correction du bulletin ou regularisation du repos si les traces contredisent le traitement applique.",
            "Escalade eventuelle: solliciter appui juridique si la direction refuse d'expliquer la base appliquee ou maintient une pratique a risque.",
        ]
    if "disciplinaire" in domains:
        return [
            "Action immediate: ne pas repondre a chaud; reconstituer les faits et demander les preuves reprochees.",
            "Demande ecrite: demander griefs precis, procedure suivie, consignes et preuves.",
            "Pieces a securiser: formation, habilitations, modes operatoires, contexte de charge, mails et temoignages utiles.",
            "Intervention DS/CSE si pertinente: alerter sur consignes ou organisation si l'erreur vient du systeme de travail.",
            "Contestation: contester la sanction si preuve, procedure ou proportionnalite sont insuffisantes.",
            "Escalade eventuelle: appui juridique en cas de sanction lourde ou de risque licenciement.",
        ]
    if "classification_carriere" in domains:
        return [
            "Action immediate: etablir un tableau des fonctions reellement exercees avec dates et preuves.",
            "Demande ecrite: demander les criteres retenus pour le coefficient actuel et un reexamen motive.",
            "Pieces a securiser: fiche de poste, organigramme, consignes, mails, comptes rendus et comparaisons internes.",
            "Intervention DS/CSE si pertinente: traiter les ecarts collectifs ou les emplois mal classes.",
            "Contestation: formuler une demande argumentee de classification ou rappel si les criteres sont remplis.",
            "Escalade eventuelle: appui juridique si refus non motive ou enjeu financier significatif.",
        ]
    return action


def split_evidence(pieces: list[str]) -> tuple[list[str], list[str]]:
    indispensables = pieces[:5] or ["Chronologie precise et pieces directement liees aux faits."]
    useful = pieces[5:10] or ["Elements de comparaison et contexte organisationnel si disponibles."]
    return indispensables, useful


def immediate_action_for_mode(mode: str, answer: dict[str, Any]) -> str:
    if mode == MODE_NEGOCIATION:
        return "Demander le projet d'accord complet, un tableau avant/apres et les impacts par categorie avant toute position."
    if mode == MODE_CSE:
        return "Demander par ecrit les documents manquants et preparer les questions prioritaires a faire inscrire au PV."
    if mode == MODE_DEFENSE and "disciplinaire" in route_domains(answer):
        return "Recuperer la convocation, les faits reproches, les preuves et construire une chronologie avant l'entretien ou la reponse."
    return "Securiser les faits et les pieces, puis demander a la direction la source appliquee et sa justification ecrite."


def contradictory_matrix(
    representative_argument: str,
    direction_argument: str,
    counter_argument: str,
    proof: str,
    risk: str,
) -> list[dict[str, str]]:
    return [
        {
            "argument_salarie_representants": representative_argument,
            "argument_probable_direction": direction_argument,
            "contre_argument": counter_argument,
            "preuve_necessaire": proof,
            "risque_ou_faiblesse": risk,
        }
    ]


def project_modifications(answer: dict[str, Any]) -> list[str]:
    query = normalize(answer.get("query", ""))
    values = []
    if has_any(query, ["reduisant le repos", "reduction du repos"]):
        values.append("Projet signale: reduction du repos entre deux periodes de travail.")
    if has_any(query, ["changement d horaires", "changement d'horaires", "horaires"]):
        values.append("Projet signale: changement d'horaires ou d'organisation du travail.")
    if has_any(query, ["suppression de postes", "supprimer des postes"]):
        values.append("Projet signale: suppression ou modification de postes.")
    if has_any(query, ["astreinte"]):
        values.append("Projet ou dossier lie au regime d'astreinte et a ses contreparties.")
    if not values:
        values.append("Modification proposee a obtenir dans un projet ecrit complet avant analyse definitive.")
    return unique(values, limit=6)


def likely_categories(answer: dict[str, Any]) -> list[str]:
    query = normalize(answer.get("query", ""))
    categories = []
    if has_any(query, ["atelier", "postes", "horaires", "5x8", "travail poste"]):
        categories.extend(["salaries de l'atelier concerne", "personnel poste ou soumis aux nouveaux horaires"])
    if has_any(query, ["astreinte"]):
        categories.extend(["salaries integres au dispositif d'astreinte", "services amenes a intervenir hors poste"])
    if has_any(query, ["sanction", "disciplinaire", "erreur de manipulation"]):
        categories.append("salarie vise par la procedure et eventuels salaries exposes a la meme consigne")
    if not categories:
        categories.append("categories concernees a identifier dans le projet ou les pieces transmises")
    return unique(categories, limit=6)


def negotiation_recommendation(answer: dict[str, Any]) -> str:
    query = normalize(answer.get("query", ""))
    if has_any(query, ["reduisant le repos", "reduction du repos"]):
        return "defavorable en l'etat sur le plan juridique/social, sauf demonstration de conformite, garanties ecrites et contreparties suffisantes."
    if not answer.get("sources"):
        return "informations insuffisantes."
    return "negociable sous conditions, sous reserve du projet ecrit complet et de la comparaison avec les droits actuels."


def defense_mode_analysis(
    answer: dict[str, Any],
    established: list[str],
    depends: list[str],
    strategy: dict[str, Any],
    pieces: list[str],
    risks: list[str],
    action: list[str],
) -> dict[str, Any]:
    indispensables, utiles = split_evidence(pieces)
    return {
        "mode": MODE_DEFENSE,
        "reponse_claire": short_response(answer),
        "qualification_juridique": qualification(answer),
        "faits_etablis": unique([*findings(answer, limit=6), *established[:4]], limit=10),
        "faits_manquants": missing_facts(answer, depends),
        "regle_applicable": applicable_rules(answer),
        "meilleur_argument_salarie": strategy.get("argument_principal"),
        "arguments_complementaires": strategy.get("arguments_complementaires", []),
        "position_probable_employeur": strategy.get("position_probable_direction"),
        "contre_arguments": strategy.get("contre_arguments", []),
        "preuves_indispensables": indispensables,
        "pieces_utiles": utiles,
        "risques_du_dossier": risks,
        "strategie_progressive": action,
        "action_immediate_recommandee": immediate_action_for_mode(MODE_DEFENSE, answer),
        "analyse_contradictoire": contradictory_matrix(
            str(strategy.get("argument_principal") or "Argument salarie a construire a partir des faits."),
            str(strategy.get("position_probable_direction") or "Position direction a confirmer par ecrit."),
            "; ".join(str(item) for item in strategy.get("contre_arguments", [])[:2]),
            indispensables[0],
            risks[0] if risks else "Risque: dossier insuffisamment documente.",
        ),
    }


def negotiation_mode_analysis(
    answer: dict[str, Any],
    strategy: dict[str, Any],
    pieces: list[str],
    risks: list[str],
    action: list[str],
) -> dict[str, Any]:
    modifications = project_modifications(answer)
    current_rights = source_briefs(answer, limit=5)
    return {
        "mode": MODE_NEGOCIATION,
        "objet_reel_du_projet": modifications,
        "comparaison_avec_accord_existant": current_rights or ["Accord existant a identifier et comparer article par article."],
        "droits_actuels": applicable_rules(answer),
        "modifications_proposees": modifications,
        "gains_possibles": [
            "Clarification ecrite des garanties et du perimetre.",
            "Contreparties negociees, suivi CSE/CSSCT et clause de revoyure si le projet est maintenu.",
        ],
        "pertes_de_droits": [
            "Reduction possible du repos ou de la protection actuelle si le projet abaisse les garanties existantes.",
            "Risque de banalisation d'une exception si les conditions ne sont pas strictement encadrees.",
        ],
        "risques_juridiques": [
            "Non-conformite avec les normes superieures si le repos minimal ou les garanties imperatives ne sont pas respectes.",
            "Clause ambigue ou insuffisamment delimitee rendant l'application contestable.",
        ],
        "risques_pratiques_salaries": [
            "Fatigue, desorganisation familiale, erreurs operationnelles, tensions d'effectifs ou perte de recuperation.",
            "Difficulte de controle si les compteurs, plannings et exceptions ne sont pas tracables.",
        ],
        "categories_salaries_concernees": likely_categories(answer),
        "clauses_ambigues": ["Perimetre, duree, exceptions, repos, contreparties, suivi et sanctions en cas de non-respect."],
        "clauses_a_securiser": [
            "Champ d'application precis.",
            "Garantie de repos et modalites de recuperation.",
            "Contreparties et methode de controle.",
            "Clause de suivi CSE/CSSCT et clause de revoyure.",
        ],
        "position_probable_direction": "La direction peut invoquer la continuite d'activite, la flexibilite ou la necessite operationnelle.",
        "arguments_negociation": [
            "Exiger la demonstration factuelle du besoin.",
            "Comparer le projet aux droits actuels et aux normes superieures.",
            "Conditionner toute evolution a des garanties ecrites, mesurables et controlables.",
        ],
        "contre_propositions": [
            "Phase test limitee dans le temps.",
            "Volontariat ou perimetre strict si juridiquement possible.",
            "Repos compensateur/contrepartie renforces et suivi anonymise partage au CSE.",
        ],
        "points_non_negociables_vigilance": [
            "Respect des normes imperatives de repos et de sante-securite.",
            "Pas de signature sans projet complet, impacts, categories concernees et modalites de suivi.",
        ],
        "questions_avant_signature": [
            "Quel est le besoin operationnel documente ?",
            "Quels droits actuels sont modifies, article par article ?",
            "Quelles categories de salaries sont concernees et avec quelles garanties ?",
            "Comment les repos, compteurs et contreparties seront-ils controles ?",
            "Quelles conditions minimales doivent etre reunies avant toute signature ?",
        ],
        "recommandation": negotiation_recommendation(answer),
        "strategie_progressive": action,
        "action_immediate_recommandee": immediate_action_for_mode(MODE_NEGOCIATION, answer),
        "analyse_contradictoire": contradictory_matrix(
            "Les representants peuvent soutenir qu'aucune reduction de garantie ne doit etre signee sans besoin prouve, compensation et controle.",
            "La direction peut soutenir que l'accord est necessaire pour l'organisation du travail ou la continuite d'activite.",
            "Demander la preuve du besoin, le tableau avant/apres, les impacts salaries et les garanties ecrites.",
            pieces[0] if pieces else "Projet d'accord complet et tableau comparatif avant/apres.",
            risks[0] if risks else "Risque: signer un texte trop vague ou moins protecteur que les garanties existantes.",
        ),
    }


def cse_mode_analysis(
    answer: dict[str, Any],
    strategy: dict[str, Any],
    pieces: list[str],
    risks: list[str],
    action: list[str],
) -> dict[str, Any]:
    docs_received = source_briefs(answer, limit=5)
    return {
        "mode": MODE_CSE,
        "nature_juridique_du_sujet": qualification(answer),
        "information_ou_consultation_eventuelle": (
            "A verifier selon l'objet exact, les impacts sur l'emploi, l'organisation, les horaires et la sante-securite."
        ),
        "documents_recus": docs_received or ["Aucun document CSE transmis dans les donnees Nexus."],
        "documents_manquants": unique(
            [
                "Note de presentation du projet.",
                "Organigrammes et effectifs avant/apres.",
                "Planning cible et horaires compares.",
                "Calendrier de mise en oeuvre.",
                "Analyse des impacts charge de travail, sante, securite et competences.",
                "Mesures d'accompagnement et alternatives etudiees.",
                *pieces[:4],
            ],
            limit=12,
        ),
        "delais_a_verifier": [
            "Date de remise des documents.",
            "Date de reunion et delai utile d'analyse.",
            "Existence d'une consultation formelle et echeance eventuelle d'avis.",
        ],
        "questions_prioritaires": unique(
            [
                "Quel est l'objectif precis du projet et quelles alternatives ont ete etudiees ?",
                "Quels postes, horaires, charges et competences changent concretement ?",
                "Quels risques sante-securite et fatigue ont ete evalues ?",
                "Quels indicateurs permettront de suivre les effets apres mise en oeuvre ?",
                *[str(item) for item in answer.get("questions_to_ask", [])[:6]],
            ],
            limit=12,
        ),
        "reponses_probables_direction": [
            "La direction peut presenter le projet comme necessaire a l'organisation, a la competitivite ou a la continuite d'activite.",
            "Elle peut minimiser les impacts en les presentant comme simples ajustements d'horaires ou d'effectifs.",
        ],
        "relances_et_contre_arguments": [
            "Demander les donnees factuelles qui justifient le projet.",
            "Exiger le detail des impacts par atelier, metier, equipe et regime horaire.",
            "Demander une reponse ecrite lorsque les documents ou chiffres manquent.",
        ],
        "consequences_salaries": [
            "Effets possibles sur charge, fatigue, repos, vie personnelle, competence, emploi et remuneration.",
            "Risque de transfert de charge ou de perte de reperes si le projet est insuffisamment encadre.",
        ],
        "enjeux_sante_securite": [
            "A verifier en priorite si les horaires, effectifs, charges, nuits, astreintes ou postes sensibles changent.",
            "Demander DUERP, analyse de risques et avis des acteurs prevention si necessaire.",
        ],
        "donnees_indicateurs_a_demander": [
            "Effectifs avant/apres par equipe.",
            "Absenteisme, accidents/incidents, heures supplementaires, astreintes, formations, charge et polyvalence.",
            "Suivi des compteurs temps/repos et alertes fatigue.",
        ],
        "action_possible_apres_reunion": [
            "Relance ecrite des documents manquants.",
            "Question complementaire CSE ou CSSCT.",
            "Demande de suivi a une date determinee.",
            "Reserve ou point de desaccord a faire acter au PV.",
        ],
        "points_pv": [
            "Documents demandes et non remis.",
            "Reponses precises de la direction.",
            "Engagements, echeances, indicateurs et reserves des elus.",
        ],
        "strategie_progressive": action,
        "action_immediate_recommandee": immediate_action_for_mode(MODE_CSE, answer),
        "analyse_contradictoire": contradictory_matrix(
            "Les representants peuvent demander une information complete, loyale et exploitable avant toute position.",
            "La direction peut soutenir que les documents fournis suffisent ou que le projet releve de son pouvoir d'organisation.",
            "Relancer sur les impacts concrets, les donnees manquantes, les risques et les engagements a tracer au PV.",
            "Note projet, effectifs avant/apres, planning cible, analyse des risques et calendrier.",
            risks[0] if risks else "Risque: avis ou discussion CSE fonde sur des informations incompletes.",
        ),
    }


def build_business_mode_analysis(
    answer: dict[str, Any],
    established: list[str],
    depends: list[str],
    strategy: dict[str, Any],
    pieces: list[str],
    risks: list[str],
    action: list[str],
) -> list[dict[str, Any]]:
    result = []
    for mode in detect_business_modes(answer):
        if mode == MODE_DEFENSE:
            result.append(defense_mode_analysis(answer, established, depends, strategy, pieces, risks, action))
        elif mode == MODE_NEGOCIATION:
            result.append(negotiation_mode_analysis(answer, strategy, pieces, risks, action))
        elif mode == MODE_CSE:
            result.append(cse_mode_analysis(answer, strategy, pieces, risks, action))
    return result


def evidence_documents(answer: dict[str, Any]) -> list[str]:
    domains = route_domains(answer)
    query = normalize(answer.get("query", ""))
    modes = set(detect_business_modes(answer))
    pieces = ["Chronologie precise des faits et dates concernees."]
    if MODE_NEGOCIATION in modes:
        pieces.extend(
            [
                "Projet d'accord ou d'avenant complet en version modifiable et signee/proposee.",
                "Tableau comparatif droits actuels / modifications proposees.",
                "Justification operationnelle du projet et alternatives etudiees.",
                "Liste des categories de salaries concernees.",
                "Simulation des impacts sur repos, horaires, paie, compteurs et organisation.",
            ]
        )
    if MODE_CSE in modes:
        pieces.extend(
            [
                "Note de presentation CSE du projet.",
                "Organigrammes, effectifs et postes avant/apres.",
                "Plannings et horaires actuels/cibles.",
                "Analyse des impacts sante, securite, charge et competences.",
                "Calendrier de mise en oeuvre et mesures d'accompagnement.",
            ]
        )
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
    if "disciplinaire" in domains:
        pieces.extend(
            [
                "Convocation et eventuelle notification de sanction.",
                "Pieces permettant de verifier la procedure disciplinaire et les delais.",
                "Faits reproches dates et decrits precisement.",
                "Preuves communiquees par la direction.",
                "Consignes, modes operatoires, formations et habilitations lies a l'erreur reprochee.",
                "Elements de contexte: charge, urgence, effectifs, panne, consignes contradictoires.",
            ]
        )
    pieces.extend(str(item) for item in answer.get("documents_to_request", []))
    return unique(pieces, limit=12)


def recommended_action(answer: dict[str, Any]) -> list[str]:
    domains = route_domains(answer)
    query = normalize(answer.get("query", ""))
    modes = set(detect_business_modes(answer))
    actions = ["Niveau 1: verifier les faits et securiser les preuves avant toute conclusion."]
    if MODE_NEGOCIATION in modes:
        actions.extend(
            [
                "Niveau 2: exiger le projet complet et le tableau avant/apres avant toute position.",
                "Niveau 3: preparer les conditions minimales, contre-propositions et points non negociables.",
                "Niveau 4: consulter les salaries concernes et demander un suivi CSE/CSSCT si les impacts sont collectifs.",
            ]
        )
    elif MODE_CSE in modes:
        actions.extend(
            [
                "Niveau 2: demander les documents manquants par ecrit avant ou pendant la reunion.",
                "Niveau 3: poser les questions prioritaires et faire acter les reponses, reserves et engagements au PV.",
                "Niveau 4: prevoir une relance ou un point de suivi CSE/CSSCT apres la reunion.",
            ]
        )
    elif "classification_carriere" in domains:
        actions.extend(
            [
                "Niveau 2: construire un tableau fonctions reelles / criteres de classification / preuves.",
                "Niveau 3: demander a la direction les criteres justifiant le coefficient actuel et un reexamen motive.",
            ]
        )
    elif "disciplinaire" in domains:
        actions.extend(
            [
                "Niveau 2: construire la chronologie et demander les preuves communiquees par la direction.",
                "Niveau 3: preparer les observations du salarie sur faits, contexte, procedure et proportionnalite.",
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
    modes = set(detect_business_modes(answer))
    points: list[str] = []
    if MODE_NEGOCIATION in modes:
        points.extend(
            [
                "Risque: negocier un texte avant d'avoir le tableau complet des droits actuels et des droits modifies.",
                "Risque: accepter une clause vague sur le repos, les horaires, les contreparties ou le suivi.",
            ]
        )
    if MODE_CSE in modes:
        points.extend(
            [
                "Risque: traiter la reunion comme une simple information alors que les impacts peuvent appeler une consultation ou un suivi.",
                "Risque: laisser une reponse orale vague sans inscription precise au proces-verbal.",
            ]
        )
    if "disciplinaire" in domains:
        points.extend(
            [
                "Risque: repondre sans connaitre les faits precis, dates et preuves retenus par la direction.",
                "Risque: ne pas traiter la proportionnalite de la sanction au regard du contexte et des consequences reelles.",
            ]
        )
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
    primary_mode = primary_business_mode(answer)
    if primary_mode == MODE_NEGOCIATION:
        return (
            "Position de travail: ne pas raisonner en signature/non-signature a ce stade ; demander le projet complet, "
            "comparer les droits actuels et exiger des garanties ecrites avant toute position syndicale."
        )
    if primary_mode == MODE_CSE:
        return (
            "Position de travail: traiter le point comme un dossier CSE/CSSCT a documenter, obtenir les pieces manquantes, "
            "poser les questions prioritaires et faire inscrire les engagements ou reserves au PV."
        )
    if primary_mode == MODE_DEFENSE and "disciplinaire" in domains:
        return (
            "Position de travail: construire la defense sur faits, preuves, procedure, contexte de l'erreur et proportionnalite "
            "avant d'accepter la qualification disciplinaire de la direction."
        )
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
    modes = set(detect_business_modes(answer))
    questions: list[str] = []
    if MODE_NEGOCIATION in modes:
        questions.extend(
            [
                "Quel besoin precis justifie le projet d'accord ou d'avenant ?",
                "Quel tableau compare les droits actuels et les modifications proposees ?",
                "Quelles categories de salaries sont concernees et avec quelles garanties ?",
                "Quelles contreparties, controles et clauses de revoyure sont proposes ?",
            ]
        )
    if MODE_CSE in modes:
        questions.extend(
            [
                "S'agit-il d'une information simple ou d'une consultation du CSE ?",
                "Quels documents justifient le projet et ses impacts sur emploi, horaires, charge et sante-securite ?",
                "Quels indicateurs seront suivis apres mise en oeuvre ?",
                "Quelles reponses la direction accepte-t-elle de faire inscrire au proces-verbal ?",
            ]
        )
    if "disciplinaire" in domains:
        questions.extend(
            [
                "Quels faits precis sont reproches, a quelles dates et avec quelles preuves ?",
                "Quelles consignes, formations ou modes operatoires etaient applicables au moment des faits ?",
                "Pourquoi la direction estime-t-elle une sanction proportionnee plutot qu'un rappel, accompagnement ou formation ?",
            ]
        )
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

    selection = source_selection(answer)
    conclusion = provisional_legal_conclusion(answer)
    response = argued_short_response(answer, conclusion)
    established = established_points(answer)
    depends = depends_on_local_texts(answer)
    reasoning = legal_reasoning(answer, selection)
    sources = source_documents(answer)
    risks = vigilance_points(answer)
    position = proposed_position(answer)
    expert_limits = limits(answer)
    pieces = evidence_documents(answer)
    action = ordered_action_strategy(answer, pieces, recommended_action(answer))
    strategy = defense_strategy(answer)
    argumentation_detail = defense_argumentation_detail(answer, strategy)
    litigation_analysis = adversarial_litigation_analysis(answer, strategy, selection)
    retained_jurisprudence = retained_jurisprudence_analysis(answer, selection)
    certainty = certainty_level(established, reasoning, depends)
    layers = source_layers_analysis(answer)
    modes = detect_business_modes(answer)
    business_analysis = build_business_mode_analysis(answer, established, depends, strategy, pieces, risks, action)
    rules = applicable_rules(answer, selection)
    application = fact_application(answer, selection)
    known_facts = facts_from_question(answer)
    public_selection = public_source_selection(selection)

    return {
        "active": True,
        "name": "Expert Juriste droit du travail V0 renforce",
        "prompt_version": JURISTE_PROMPT_VERSION,
        "prompt_contract": JURISTE_PROMPT_CONTRACT,
        "modes_metier": modes,
        "mode_metier_principal": modes[0] if modes else None,
        "response_courte": response,
        "reponse_courte": response,
        "qualification_juridique_situation": qualification(answer),
        "selection_juridique_sources": public_selection,
        "sources_retenues_principales": public_selection.get("source_principale", []),
        "sources_retenues_complementaires": public_selection.get("source_complementaire", []),
        "sources_contextuelles": public_selection.get("source_contextuelle", []),
        "sources_ecartees": public_selection.get("source_ecartee", []),
        "faits_connus": known_facts,
        "regle_applicable": rules,
        "application_aux_faits": application,
        "conclusion_provisoire_juridique": conclusion,
        "argumentation_de_defense": argumentation_detail,
        "strategie_action_ordonnee": action,
        "jurisprudence_retenue_analysee": retained_jurisprudence,
        "reponse_juridique_argumentee": {
            "regle_applicable": rules,
            "application_aux_faits": application,
            "conclusion_provisoire": conclusion,
            "argumentation_de_defense": argumentation_detail,
            "strategie_action": action,
        },
        "analyse_metier": business_analysis,
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
        "analyse_contradictoire_contentieux": litigation_analysis,
        "action_conseillee": action,
        "position_de_travail_proposee": position,
        "questions_a_poser_direction": direction_questions(answer),
        "questions_a_poser": direction_questions(answer),
        "niveau_de_confiance": answer.get("confidence", "a verifier"),
        "limites": expert_limits,
    }
