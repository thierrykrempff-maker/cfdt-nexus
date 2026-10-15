"""Dossier « Nexus → Claude » : Nexus rassemble les sources, Claude les analyse (« second cerveau » du délégué syndical).

Nexus ne rédige pas d'analyse. Selon la situation, il réunit **toutes** ses sources :
- le Code du travail (Légifrance, texte intégral des articles de référence) et la jurisprudence (Judilibre) ;
- la convention collective des industries chimiques (IDCC 44), les accords d'entreprise INEOS et les PV du CE/CSE (archives locales) ;
- les guides et explications officiels : CDTN, service-public, CNIL, DREETS Grand Est (dont le droit local Alsace-Moselle), CARSAT, INRS,
  ANACT, URSSAF, Assurance maladie, ministère du Travail, France Chimie, Défenseur des droits, Agirc-Arrco…
puis écrit un dossier dont les sources sont numérotées [S1], [S2]… avec une consigne adaptée :

- ``question``  : une question syndicale ou juridique ;
- ``agenda``    : un ordre du jour de CSE, point par point (enjeu, précédents, questions à la direction, avis à rendre) ;
- ``defense``   : la défense d'un salarié (procédure, motif, preuves, délais, stratégie).

Usages : boutons de l'interface Nexus (copie dans le presse-papiers : action volontaire de l'utilisateur) ou ligne de commande pour une
session Claude Code (``python -I claude_dossier.py "question"``, ``--agenda "point 1" "point 2"``, ``--defense "type" "faits"``).
Le dossier contient des extraits de documents confidentiels : il n'est jamais écrit sur disque par ce module ni repris dans les
rapports et exports de Nexus.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
import datetime
import os
import sys
from typing import Any

if __package__ in (None, ""):  # exécution directe : rendre importables les modules voisins et la racine du dépôt
    _HERE = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, _HERE)
    sys.path.insert(0, os.path.dirname(os.path.dirname(_HERE)))

from official_sources_search import _plain, keywords_for_sources, matching_topics, search_official_sources  # noqa: E402
from pv_archive_search import search_archive  # noqa: E402

ARCHIVE_ROWS = 6
MAX_QUESTION_CHARS = 1500
MAX_AGENDA_POINTS = 10
MAX_FACTS_CHARS = 3000
COMPACT_TEXT_CHARS = 1500
COMPACT_LIMITS = {"law": 4, "decisions": 2, "convention": 2, "reglement": 2, "accords": 3, "pv": 4, "extra": 4, "docs": 3}

ROLE = (
    "L'utilisateur est délégué syndical CFDT et élu au CSE d'INEOS Sarralbe (Moselle : le droit local d'Alsace-Moselle s'applique), "
    "branche des industries chimiques (IDCC 44). Réponds à ce titre : arguments syndicaux, droits des élus et des salariés, "
    "questions à poser à la direction, démarches concrètes."
)

COMMON_RULES = """\
Règles :
1. N'utilise aucune connaissance extérieure au dossier. Si le dossier ne permet pas de répondre à un point, dis-le clairement.
2. Cite la source de chaque affirmation, sous la forme [S3]. Ne cite jamais une source qui n'est pas dans le dossier.
3. Hiérarchie des normes : loi, convention de branche, accord d'entreprise, règlement intérieur (qui ne peut être moins favorable) ; signale le plus favorable et les dérogations possibles ;
   signale toute règle propre à l'Alsace-Moselle si le dossier en contient.
4. Les extraits peuvent être tronqués ou mal reconnus (OCR) : ne conclus pas sur un extrait douteux, signale-le.
5. Ne recopie pas de noms de salariés (désigne « un salarié » et la date) sauf demande expresse.
6. Termine par les vérifications à faire (version en vigueur, avenants, dénonciation) et rappelle que ce n'est pas un avis juridique :
   un point sensible se valide auprès de la fédération ou d'un conseil.\
"""

INSTRUCTIONS = {
    "question": (
        "Analyse la question ci-dessous **uniquement** à partir des sources numérotées de ce dossier.\n"
        "Structure : règle légale ; convention collective ; accords INEOS ; ce qui a été dit ou décidé en CE/CSE (avec les dates) ; "
        "jurisprudence ; points d'attention et contradictions entre sources ; questions à poser à la direction.\n\n" + COMMON_RULES
    ),
    "agenda": (
        "Prépare la réunion de CSE ci-dessous, **point par point**, uniquement à partir des sources numérotées de ce dossier.\n"
        "Pour chaque point : (a) l'enjeu et ce que la loi, la convention et les accords imposent (consultation obligatoire ? délai ? "
        "documents à obtenir ?) ; (b) les précédents dans les PV (dates, positions de la direction et des organisations syndicales, "
        "engagements non tenus) ; (c) la jurisprudence utile ; (d) les questions précises à poser à la direction ; (e) la position "
        "syndicale conseillée (avis favorable, défavorable, réserves, demande de report ou d'expertise) avec ses justifications ; "
        "(f) les risques et les pièges.\nPuis une synthèse : points prioritaires, ordre de traitement, documents à réclamer avant la séance.\n\n"
        + COMMON_RULES
    ),
    "paie": (
        "Contrôle la situation de paie ou de congés décrite ci-dessous, **uniquement** à partir des sources numérotées de ce dossier.\n"
        "Structure : (a) ce qui doit figurer sur le bulletin et comment se calcule l'élément en cause (base légale, convention, accord INEOS, guide Nibelis ou document de paie du dossier) ; "
        "(b) le contrôle étape par étape : données à relever (heures, taux, majorations, primes, période, jours de congés acquis/pris/maintenus), formule, écart éventuel — ne calcule que si le dossier donne les taux et règles, sinon dis ce qui manque ; "
        "(c) ce qui a été décidé en CE/CSE et dans les accords (avenants, protocoles salariaux) ; "
        "(d) droits liés aux congés et absences (maladie, maternité, paternité, congé supplémentaire de naissance, jours fériés, droit local d'Alsace-Moselle) ; "
        "(e) prescription et délais : les écarts de salaire se réclament dans la limite indiquée par les sources ; "
        "(f) pièces à réunir (bulletins, relevés de badgeuse ou de planning, décompte Kelio) et courrier de demande de régularisation à rédiger (modèle) ; "
        "(g) démarches : demande écrite, délégué, inspection du travail, prud'hommes — dans quel ordre.\n\n"
        + COMMON_RULES
    ),
    "defense": (
        "Prépare la défense du salarié décrit ci-dessous, **uniquement** à partir des sources numérotées de ce dossier.\n"
        "Structure : (a) qualification de la situation et règles applicables (loi, convention, accords, règlement intérieur et son échelle de sanctions, droit local) ; (b) procédure : "
        "étapes obligatoires, délais, assistance du salarié (conseiller du salarié, représentant du personnel), consultation du CSE, "
        "points de forme qui peuvent invalider ; (c) fond : le motif est-il réel et sérieux ? ce qu'il faut prouver et par qui ; "
        "(d) précédents : ce qui a été traité en CE/CSE et dans les accords, jurisprudence favorable et défavorable ; (e) pièces et "
        "informations à réclamer à l'employeur ; (f) stratégie : négociation, contestation, délais de recours, ordre des démarches ; "
        "(g) indemnités et conséquences financières si les sources les donnent ; (h) ce que le délégué syndical fait lui-même, tout de suite.\n"
        "Signale les délais de prescription et de recours qui figurent dans les sources, et ce qui manque pour conclure.\n\n" + COMMON_RULES
    ),
}


def _row_text(row: Mapping[str, Any]) -> str:
    return str(row.get("excerpt") or "").strip()


def _header(row: Mapping[str, Any]) -> str:
    return " — ".join(str(part) for part in (row.get("title"), row.get("date"), row.get("instance"), row.get("reference")) if part)


def _archive_rows(corpus: str, attempts: Sequence[tuple[str, bool]]) -> tuple[list[dict[str, Any]], str]:
    """Passages d'une archive locale. ``attempts`` : (requête, strict) du plus précis au plus large ; on s'arrête au premier
    qui donne des résultats (un repli trop large noierait le dossier de passages hors sujet). Renvoie (lignes, statut)."""

    status = "READY"
    for query, strict in attempts:
        result = search_archive(corpus, query, limit=ARCHIVE_ROWS, strict=strict)  # strict : tous les mots ensemble
        if result.get("status") != "READY":
            status = str(result.get("status"))
            continue
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        for row in result.get("results") or []:
            if corpus == "accords" and ("ccnic" in _plain(row.get("title")) or "reglement interieur" in _plain(row.get("title"))):
                continue  # la convention collective et le règlement intérieur ont chacun leur section
            key = _plain(row.get("excerpt"))[:160]
            if key and key not in seen:
                seen.add(key)
                rows.append(row)
        if rows:
            return rows[:ARCHIVE_ROWS], "READY"
    return [], status


def gather(text: str, *, full_text: bool = True) -> dict[str, Any]:
    """Interroge toutes les sources pour un texte (question, point d'ordre du jour, situation). Ne lève jamais d'exception."""

    official = search_official_sources(text, full_text=full_text)
    topics = matching_topics(text)
    keywords = keywords_for_sources(text)
    query = " ".join(keywords) if keywords else text
    attempts = [(query, True)]
    if topics:
        attempts.append((" ".join(topics[0]["terms"]), True))
    attempts.append((query, False))
    pv_rows, pv_status = _archive_rows("pv", attempts)
    accord_rows, accord_status = _archive_rows("accords", attempts)
    docs_rows, docs_status = _archive_rows("docs", attempts)
    sections = official.get("sections") or {}

    def part(name: str) -> tuple[list[Mapping[str, Any]], str]:
        item = sections.get(name) or {}
        return list(item.get("rows") or []), str(item.get("status") or "UNAVAILABLE")

    reference, reference_status = part("reference")
    free, _ = part("legifrance")
    decisions, decisions_status = part("judilibre")
    convention, convention_status = part("convention")
    reglement, reglement_status = part("reglement")
    extra, _ = part("autres")
    return {
        "text": text,
        "topics": [topic["label"] for topic in topics[:2]],
        "law": [*reference, *free], "decisions": decisions, "convention": convention, "reglement": reglement,
        "accords": accord_rows, "pv": pv_rows, "extra": extra, "docs": docs_rows,
        "statuses": {"Légifrance": reference_status, "Judilibre": decisions_status, "Convention collective": convention_status, "Règlement intérieur": reglement_status,
                     "Accords": accord_status, "PV": pv_status, "Documents": docs_status},
    }


class _Numbering:
    """Numérotation [S#] commune à tout le dossier ; une source déjà citée n'est pas recopiée."""

    def __init__(self) -> None:
        self.count = 0
        self.cited: dict[str, int] = {}

    def number(self, row: Mapping[str, Any]) -> tuple[int, bool]:
        key = _plain(f"{row.get('url') or ''}|{row.get('title') or ''}|{_row_text(row)[:80]}")
        if key in self.cited:
            return self.cited[key], True
        self.count += 1
        self.cited[key] = self.count
        return self.count, False


def _render(gathered: Mapping[str, Any], numbering: _Numbering, level: str, compact: bool) -> list[str]:
    lines: list[str] = []
    limit = COMPACT_LIMITS if compact else {}

    def body_of(row: Mapping[str, Any]) -> str:
        body = str(row.get("full_text") or row.get("excerpt") or "")
        return body[:COMPACT_TEXT_CHARS] + ("…" if compact and len(body) > COMPACT_TEXT_CHARS else "")

    def block(title: str, key: str, render, empty: str) -> None:
        lines.extend(["", f"{level} {title}", ""])
        rows = list(gathered[key])[: limit.get(key, 99)]
        if not rows:
            lines.append(f"_{empty}_")
            return
        for row in rows:
            number, again = numbering.number(row)
            if again:
                lines.extend([f"(déjà cité plus haut : [S{number}] {row.get('title')})", ""])
            else:
                lines.extend(render(number, row))

    def law(n: int, row: Mapping[str, Any]) -> list[str]:
        link = f" — {row['url']}" if row.get("url") else ""
        return [f"**[S{n}] {row.get('title')}** ({row.get('detail') or 'en vigueur'}){link}", "", f"> {body_of(row)}", ""]

    def decision(n: int, row: Mapping[str, Any]) -> list[str]:
        link = f" — {row['url']}" if row.get("url") else ""
        return [f"**[S{n}] {row.get('title')}** — {row.get('detail') or ''}{link}", "", f"> {row.get('excerpt')}", ""]

    def convention(n: int, row: Mapping[str, Any]) -> list[str]:
        return [f"**[S{n}] Convention collective IDCC 44 — {row.get('detail') or ''}**", "", f"> {row.get('excerpt')}", ""]

    def convention_like(n: int, row: Mapping[str, Any]) -> list[str]:
        return [f"**[S{n}] {row.get('title')} — {row.get('detail') or ''}**", "", f"> {row.get('excerpt')}", ""]

    def passage(n: int, row: Mapping[str, Any]) -> list[str]:
        return [f"**[S{n}] {_header(row)}**", "", f"> {_row_text(row)}", ""]

    def guide(n: int, row: Mapping[str, Any]) -> list[str]:
        link = f" — {row['url']}" if row.get("url") else ""
        return [f"**[S{n}] {row.get('title')}** ({row.get('detail')}){link}", "", f"> {row.get('excerpt')}", ""]

    block("A. Code du travail (Légifrance, texte officiel en vigueur)", "law", law, "Aucun article retrouvé pour ce sujet.")
    block("B. Jurisprudence de la Cour de cassation (Judilibre — résumés officiels)", "decisions", decision,
          "Aucune décision retrouvée pour ce sujet.")
    block("C. Convention collective nationale des industries chimiques (IDCC 44 — édition septembre 2013)", "convention", convention,
          "Aucun passage retrouvé dans la convention collective.")
    block("D. Accords d'entreprise INEOS Sarralbe (archive locale)", "accords", passage, "Aucun accord retrouvé.")
    block("D bis. Règlement intérieur d'INEOS Sarralbe (version du 1er octobre 2018)", "reglement", convention_like,
          "Aucun passage du règlement intérieur ne correspond.")
    block("E. PV du CE/CSE (archive locale, 2000-2024)", "pv", passage, "Aucun PV retrouvé.")
    block("F. Autres sources officielles (guides et explications : CDTN, service-public, CNIL, DREETS Grand Est, CARSAT, INRS…)",
          "extra", guide, "Aucune page de ces sites ne correspond à ce sujet.")
    block("G. Documents syndicaux et de référence (paie, congés, NAO, branche, guides — dossiers « cfdt » et « paies et congés »)", "docs", passage,
          "Aucun document correspondant.")
    return lines


def _notes(statuses: Mapping[str, str]) -> list[str]:
    return [f"- {label} : source non consultée ({status}). Ne pas en conclure qu'il n'y a rien."
            for label, status in statuses.items() if status != "READY"]


def _limits(notes: Sequence[str]) -> list[str]:
    return [
        "",
        "## Limites de la recherche",
        "",
        "- Recherche automatique par mots-clés : une absence de résultat ne prouve pas l'absence de règle ou de précédent.",
        "- Légifrance : articles de référence du sujet (liste limitée) ; vérifier les autres textes applicables.",
        "- Section F : guides et explications officiels ; ils orientent mais ne remplacent ni la loi ni la jurisprudence.",
        "- Judilibre : résumés officiels, pas les arrêts complets ; décisions sélectionnées par mots-clés.",
        "- Convention collective : édition de septembre 2013 de l'archive locale ; la version en vigueur peut différer.",
        "- Accords et PV : texte océrisé (erreurs possibles) ; pas de PV de CHSCT/CSSCT ; vérifier version en vigueur, avenants, dénonciation.",
        *notes,
        "- Ce dossier contient des extraits de documents confidentiels : ne le partager qu'avec des personnes habilitées.",
    ]


def _head(mode: str, title: str) -> list[str]:
    return [f"# {title} — {datetime.date.today().isoformat()}", "", "## Consigne", "", ROLE, "", INSTRUCTIONS[mode], ""]


def _counts(gathered_list: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    names = {"law": "loi", "decisions": "jurisprudence", "convention": "convention", "accords": "accords", "pv": "pv", "extra": "autres",
             "docs": "documents", "reglement": "reglement_interieur"}
    return {label: sum(len(g[key]) for g in gathered_list) for key, label in names.items()}


def build_claude_dossier(question: object, *, mode: str = "question", situation: str = "", topic_text: str = "") -> dict[str, Any]:
    """Dossier Markdown pour une question (``question``) ou la défense d'un salarié (``defense``, avec ``situation`` = faits)."""

    text = " ".join(str(question or "").split())[:MAX_QUESTION_CHARS]
    if not text:
        return {"status": "EMPTY_QUERY", "markdown": "", "sources": 0, "notice": "Saisissez une question."}
    mode = mode if mode in ("question", "defense", "paie") else "question"
    facts = "\n".join(" ".join(line.split()) for line in str(situation or "").splitlines() if line.strip())[:MAX_FACTS_CHARS]
    # défense : la recherche part du type de situation et de la description du salarié ; l'ensemble des faits n'est qu'affiché
    topic = " ".join(str(topic_text or "").split())[:600]
    gathered = gather(f"{text} {topic or facts[:600]}".strip() if mode in ("defense", "paie") else text)
    numbering = _Numbering()
    sources = _render(gathered, numbering, "###", compact=False)
    topic_line = (f"Sujet reconnu par Nexus : {' ; '.join(gathered['topics'])}." if gathered["topics"]
                  else "Aucun sujet type reconnu : recherche par mots-clés.")
    heading = {"defense": "## Situation du salarié", "paie": "## Situation de paie ou de congés à contrôler"}.get(mode)
    middle = [heading, "", text, "", facts or "_Faits non précisés._"] if heading else ["## Question", "", text]
    title = {"question": "Dossier Nexus pour analyse", "defense": "Dossier Nexus — défense d'un salarié",
             "paie": "Dossier Nexus — contrôle de paie et de congés"}[mode]
    markdown = "\n".join([*_head(mode, title), *middle, "", topic_line, "", "## Sources", *sources,
                          *_limits(_notes(gathered["statuses"]))]) + "\n"
    return {"status": "READY", "markdown": markdown, "sources": numbering.count, "counts": _counts([gathered])}


def build_agenda_dossier(points: Sequence[Any], meeting: object = "") -> dict[str, Any]:
    """Dossier pour un ordre du jour de CSE : toutes les sources, point par point (compact, sources numérotées une seule fois)."""

    cleaned: list[tuple[str, str]] = []
    for item in list(points)[:MAX_AGENDA_POINTS]:
        raw = item.get("title") if isinstance(item, Mapping) else item
        title = " ".join(str(raw or "").split())[:300]
        if title:
            position = str(item.get("position") or len(cleaned) + 1) if isinstance(item, Mapping) else str(len(cleaned) + 1)
            cleaned.append((position[:12], title))
    if not cleaned:
        return {"status": "EMPTY_QUERY", "markdown": "", "sources": 0, "notice": "Aucun point d'ordre du jour."}
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(lambda pair: gather(pair[1]), cleaned))
    numbering = _Numbering()
    body: list[str] = ["## Sources, point par point"]
    notes: dict[str, str] = {}
    for (position, title), gathered in zip(cleaned, results):
        body.extend(["", f"## Point {position} — {title}"])
        if gathered["topics"]:
            body.append(f"Sujet reconnu par Nexus : {' ; '.join(gathered['topics'])}.")
        body.extend(_render(gathered, numbering, "###", compact=True))
        notes.update({label: status for label, status in gathered["statuses"].items() if status != "READY"})
    label = " ".join(str(meeting or "").split())[:160]
    markdown = "\n".join([*_head("agenda", "Dossier Nexus — préparation du CSE"),
                          f"## Réunion{': ' + label if label else ''}", "",
                          *[f"{position}. {title}" for position, title in cleaned], "", *body, *_limits(_notes(notes))]) + "\n"
    return {"status": "READY", "markdown": markdown, "sources": numbering.count, "points": len(cleaned), "counts": _counts(results)}


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    usage = ('usage : python -I claude_dossier.py "question"\n'
             '        python -I claude_dossier.py --agenda "point 1" "point 2" ...\n'
             '        python -I claude_dossier.py --defense "type de situation" "faits (anonymisés)"')
    if not args:
        print(usage, file=sys.stderr)
        return 2
    for name in ("NEXUS_OFFICIAL_SOURCES_BLOCK_ENABLED", "NEXUS_ACCORDS_ARCHIVE_ENABLED", "NEXUS_PV_ARCHIVE_ENABLED"):
        os.environ.setdefault(name, "true")
    if args[0] == "--agenda":
        dossier = build_agenda_dossier([{"title": title} for title in args[1:]])
    elif args[0] == "--defense":
        if len(args) < 2:
            print(usage, file=sys.stderr)
            return 2
        dossier = build_claude_dossier(args[1], mode="defense", situation=" ".join(args[2:]))
    else:
        dossier = build_claude_dossier(" ".join(args))
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(dossier["markdown"] or dossier.get("notice", ""))
    return 0 if dossier["status"] == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
