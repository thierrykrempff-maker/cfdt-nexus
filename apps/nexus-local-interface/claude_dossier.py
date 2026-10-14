"""Dossier « Nexus → Claude » : Nexus rassemble les sources, Claude les analyse.

Nexus ne rédige pas d'analyse. Pour une question, il réunit **uniquement** :
- le Code du travail (Légifrance, texte intégral des articles de référence) ;
- la jurisprudence de la Cour de cassation (Judilibre) ;
- la convention collective des industries chimiques (IDCC 44, archive locale) ;
- les accords d'entreprise INEOS (archive locale) ;
- les PV du CE/CSE (archive locale),
puis écrit un dossier numéroté [S1], [S2]… avec une consigne : Claude doit répondre en s'appuyant sur ces seules sources.

Deux usages, même dossier :
- bouton « Préparer le dossier pour Claude » de l'interface Nexus (copie dans le presse-papiers : action volontaire de l'utilisateur) ;
- ligne de commande, pour une session Claude Code : ``python -I claude_dossier.py "question"``.

Le dossier contient des extraits de documents confidentiels (PV, accords) : il n'est jamais écrit sur disque par ce module
ni repris dans les rapports et exports de Nexus.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
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

INSTRUCTIONS = """\
Analyse la question ci-dessous **uniquement** à partir des sources numérotées de ce dossier (Code du travail, jurisprudence,
convention collective, accords d'entreprise, PV du CE/CSE, guides officiels). Règles :
1. N'utilise aucune connaissance extérieure au dossier. Si le dossier ne permet pas de répondre à un point, dis-le clairement.
2. Cite la source de chaque affirmation, sous la forme [S3]. Ne cite jamais une source qui n'est pas dans le dossier.
3. Structure la réponse : règle légale ; ce que prévoit la convention collective ; ce que prévoient les accords INEOS ;
   ce qui a été dit ou décidé en CE/CSE (avec les dates) ; jurisprudence ; points d'attention et contradictions entre sources.
4. Hiérarchie des normes : loi, convention de branche, accord d'entreprise ; signale l'application du plus favorable et les dérogations possibles.
5. Les extraits peuvent être tronqués ou mal reconnus (OCR) : ne conclus pas sur un extrait douteux, signale-le.
6. Termine par les vérifications à faire (version en vigueur, avenants, dénonciation) et les questions à poser à la direction.
7. Tu n'es pas avocat : rappelle de faire valider un point sensible par la fédération ou un conseil juridique.\
"""


def _dossier_row_text(row: Mapping[str, Any]) -> str:
    return str(row.get("excerpt") or "").strip()


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
            if corpus == "accords" and "ccnic" in _plain(row.get("title")):
                continue  # la convention collective a sa propre section
            key = _plain(row.get("excerpt"))[:160]
            if key and key not in seen:
                seen.add(key)
                rows.append(row)
        if rows:
            return rows[:ARCHIVE_ROWS], "READY"
    return [], status


def _header(row: Mapping[str, Any]) -> str:
    return " — ".join(str(part) for part in (row.get("title"), row.get("date"), row.get("instance"), row.get("reference")) if part)


def build_claude_dossier(question: object) -> dict[str, Any]:
    """Dossier Markdown pour Claude. Ne lève jamais d'exception ; ``status`` : READY, EMPTY_QUERY ou DISABLED."""

    text = " ".join(str(question or "").split())[:MAX_QUESTION_CHARS]
    if not text:
        return {"status": "EMPTY_QUERY", "markdown": "", "sources": 0, "notice": "Saisissez une question."}
    official = search_official_sources(text, full_text=True)
    topics = matching_topics(text)
    keywords = keywords_for_sources(text)
    query = " ".join(keywords) if keywords else text
    attempts = [(query, True)]
    if topics:
        attempts.append((" ".join(topics[0]["terms"]), True))
    attempts.append((query, False))
    pv_rows, pv_status = _archive_rows("pv", attempts)
    accord_rows, accord_status = _archive_rows("accords", attempts)
    sections = official.get("sections") or {}

    counter = 0
    lines: list[str] = []
    notes: list[str] = []

    def add(title: str, rows: Sequence[Mapping[str, Any]], render, empty: str) -> None:
        nonlocal counter
        lines.extend(["", f"### {title}", ""])
        if not rows:
            lines.append(f"_{empty}_")
            return
        for row in rows:
            counter += 1
            lines.extend(render(counter, row))

    def law(number: int, row: Mapping[str, Any]) -> list[str]:
        body = str(row.get("full_text") or row.get("excerpt") or "")
        link = f" — {row['url']}" if row.get("url") else ""
        return [f"**[S{number}] {row.get('title')}** ({row.get('detail') or 'en vigueur'}){link}", "", f"> {body}", ""]

    def decision(number: int, row: Mapping[str, Any]) -> list[str]:
        link = f" — {row['url']}" if row.get("url") else ""
        return [f"**[S{number}] {row.get('title')}** — {row.get('detail') or ''}{link}", "", f"> {row.get('excerpt')}", ""]

    def passage(number: int, row: Mapping[str, Any]) -> list[str]:
        return [f"**[S{number}] {_header(row)}**", "", f"> {_dossier_row_text(row)}", ""]

    def guide(number: int, row: Mapping[str, Any]) -> list[str]:
        link = f" — {row['url']}" if row.get("url") else ""
        return [f"**[S{number}] {row.get('title')}** ({row.get('detail')}){link}", "", f"> {row.get('excerpt')}", ""]

    def part(name: str) -> tuple[list[Mapping[str, Any]], str]:
        item = sections.get(name) or {}
        return list(item.get("rows") or []), str(item.get("status") or "UNAVAILABLE")

    reference, reference_status = part("reference")
    free, _ = part("legifrance")
    decisions, decisions_status = part("judilibre")
    convention, convention_status = part("convention")
    extra, _ = part("autres")

    lines.extend(["## Sources"])
    add("A. Code du travail (Légifrance, texte officiel en vigueur)", [*reference, *free], law,
        "Aucun article retrouvé pour cette question.")
    add("B. Jurisprudence de la Cour de cassation (Judilibre — résumés officiels)", decisions, decision,
        "Aucune décision retrouvée pour cette question.")
    add("C. Convention collective nationale des industries chimiques (IDCC 44 — édition septembre 2013)", convention,
        lambda n, r: [f"**[S{n}] Convention collective IDCC 44 — {r.get('detail') or ''}**", "", f"> {r.get('excerpt')}", ""],
        "Aucun passage retrouvé dans la convention collective.")
    add("D. Accords d'entreprise INEOS Sarralbe (archive locale)", accord_rows, passage, "Aucun accord retrouvé.")
    add("E. PV du CE/CSE (archive locale, 2000-2024)", pv_rows, passage, "Aucun PV retrouvé.")
    add("F. Autres sources officielles (explications et guides : CDTN, service-public, CNIL, DREETS Grand Est, CARSAT, INRS)",
        extra, guide, "Aucune page de ces sites ne correspond à la question.")

    for label, status in (("Légifrance", reference_status), ("Judilibre", decisions_status),
                          ("Convention collective", convention_status), ("Accords", accord_status), ("PV", pv_status)):
        if status not in ("READY",):
            notes.append(f"- {label} : source non consultée ({status}). Ne pas en conclure qu'il n'y a rien.")
    topic_line = f"Sujet reconnu par Nexus : {' ; '.join(t['label'] for t in topics[:2])}." if topics else "Aucun sujet type reconnu : recherche par mots-clés."
    head = [
        f"# Dossier Nexus pour analyse — {datetime.date.today().isoformat()}",
        "",
        "## Consigne",
        "",
        INSTRUCTIONS,
        "",
        "## Question",
        "",
        text,
        "",
        topic_line,
    ]
    tail = [
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
    return {"status": "READY", "markdown": "\n".join([*head, *lines, *tail]) + "\n", "sources": counter,
            "counts": {"loi": len(reference) + len(free), "jurisprudence": len(decisions), "convention": len(convention),
                       "accords": len(accord_rows), "pv": len(pv_rows), "autres": len(extra)}}


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("usage : python -I claude_dossier.py \"question\"", file=sys.stderr)
        return 2
    for name in ("NEXUS_OFFICIAL_SOURCES_BLOCK_ENABLED", "NEXUS_ACCORDS_ARCHIVE_ENABLED", "NEXUS_PV_ARCHIVE_ENABLED"):
        os.environ.setdefault(name, "true")
    dossier = build_claude_dossier(" ".join(args))
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(dossier["markdown"] or dossier.get("notice", ""))
    return 0 if dossier["status"] == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
