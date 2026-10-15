"""Contrôles automatiques des extraits d'un dossier « Nexus → Claude » : provenance, lisibilité, pertinence, divergences.

Objectif : ne garder que l'information utile et fiable, et dire clairement ce qui a été écarté ou doit être vérifié.

- **Provenance** : un extrait d'une archive locale (PV, accords, documents) est relu dans le texte complet du document source (service
  local) ; il porte la mention « vérifié dans le document » ou « non retrouvé dans le document ».
- **Lisibilité** : un extrait océrisé illisible (suites de lettres sans sens) est écarté.
- **Pertinence** : un extrait qui ne contient aucun mot distinctif de la question est écarté (il ne vient du moteur que par un autre
  mot de sa fenêtre de recherche).
- **Divergences** : les durées, taux et montants cités par plusieurs sources pour la même notion (préavis, délai, majoration…) sont
  rapprochés : si les valeurs diffèrent, la divergence est signalée à Claude pour vérification (la comparaison est mécanique : à confirmer).

Aucune exception ne remonte à l'appelant ; rien n'est écrit sur disque.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import re
from typing import Any

from agreement_compare import _base_url, _service_call
from official_extra_sources import _plain, _stems

MIN_QUALITY = 0.8
MAX_VERIFIED_ROWS = 24

# Notions dont la valeur chiffrée doit être cohérente d'une source à l'autre.
_NOTIONS = (
    "preavis", "delai", "duree", "majoration", "indemnite", "anciennete", "prescription", "taux", "prime", "plafond",
    "minimum", "maximum", "seuil", "periode", "maintien", "repos", "jours", "conge",
)
_VALUE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(jours? ouvrables?|jours? ouvres?|jours?|semaines?|mois|ans?|annees?|heures?|%|euros?|€)", re.I)
_UNIT_FAMILY = {"jour": "jours", "jours": "jours", "semaine": "semaines", "semaines": "semaines", "mois": "mois", "an": "ans", "ans": "ans",
                "annee": "ans", "annees": "ans", "heure": "heures", "heures": "heures", "%": "%", "euro": "euros", "euros": "euros", "€": "euros"}


_SMALL_WORDS = frozenset(
    "le la les de du des un une et ou en au aux ce se sa son ses ne pas par sur sous dans que qui est a il elle on nous vous ils "
    "elles sont été être pour avec sans mais donc or ni car plus si y ces mon ma mes ton ta tes leur leurs notre votre cet cette "
    "lui moi toi eux ici là où quoi dont tout tous non oui peu bien mieux très trop fait fin art".split()
)


def text_quality(text: object) -> float:
    """Part (0 à 1) des mots d'un extrait qui ressemblent à du français lisible. Un extrait court est jugé lisible.

    Sont suspects : les fragments de 1 à 3 lettres qui ne sont pas des mots courants, les mots très longs, les suites de
    « l », « i » ou « | » (confusions de l'océrisation), les lettres répétées trois fois et les mots sans voyelle."""

    tokens = re.findall(r"[^\W\d_]+", str(text or ""))
    if len(tokens) < 8:
        return 1.0
    sound = 0
    for token in tokens:
        low = token.lower()
        if len(low) > 20 or re.search(r"[lI]{4,}", token) or re.search(r"(.)\1\1", low):
            continue
        if len(low) <= 3:
            if low in _SMALL_WORDS or (len(low) == 1 and low in "ayàyû"):
                sound += 1
            continue
        if re.search(r"[aeiouyàâäéèêëîïôöùûüœæ]", low) and not re.search(r"[^aeiouyàâäéèêëîïôöùûüœæ]{6,}", low):
            sound += 1
    return round(sound / len(tokens), 2)


def _squash(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", _plain(value))


def _document_index(corpus: str, cache: dict[str, Any]) -> dict[str, str]:
    """fichier -> référence courte, pour un corpus (une seule requête par corpus)."""

    key = f"index:{corpus}"
    if key not in cache:
        base = _base_url()
        listing = _service_call(f"{base}/api/documents?corpus={corpus}") if base else None
        items = listing.get("documents") if listing else None
        cache[key] = {str(item.get("fichier")): str(item.get("id")) for item in (items or []) if isinstance(item, Mapping)}
    return cache[key]


def _document_text(corpus: str, reference: str, cache: dict[str, Any]) -> str:
    key = f"text:{corpus}:{reference}"
    if key not in cache:
        base = _base_url()
        payload = _service_call(f"{base}/api/document", {"corpus": corpus, "id": reference}) if base else None
        cache[key] = _squash(payload.get("texte")) if payload else ""
    return cache[key]


def verify_provenance(row: dict[str, Any], corpus: str, cache: dict[str, Any]) -> str:
    """'verifie', 'non_retrouve' ou 'non_controle' (service ou document indisponible)."""

    source = str(row.get("_source") or "")
    if not source:
        return "non_controle"
    reference = _document_index(corpus, cache).get(source)
    if not reference:
        return "non_controle"
    document = _document_text(corpus, reference, cache)
    core = _squash(str(row.get("excerpt") or "").strip("… ").replace("…", " "))
    if not document or len(core) < 40:
        return "non_controle"
    probe = core[:240]
    return "verifie" if probe in document else "non_retrouve"


def check_rows(
    gathered: dict[str, Any],
    query: str,
) -> dict[str, Any]:
    """Contrôle et filtre les extraits d'un ``gather``. Modifie ``gathered`` ; renvoie le bilan par section (gardés / écartés)."""

    wanted = _stems(query)
    cache: dict[str, Any] = {}
    report: dict[str, Any] = {}
    budget = MAX_VERIFIED_ROWS
    corpus_of = {"pv": "pv", "accords": "accords", "docs": "docs"}
    for key in ("pv", "accords", "docs", "extra", "convention", "reglement"):
        kept: list[dict[str, Any]] = []
        dropped = {"illisible": 0, "hors_sujet": 0}
        for row in gathered.get(key, []):
            text = str(row.get("excerpt") or "")
            if text_quality(text) < MIN_QUALITY:
                dropped["illisible"] += 1
                continue
            if wanted and key in ("pv", "accords", "docs", "extra") and not (set(wanted) & set(_stems(text))):
                dropped["hors_sujet"] += 1
                continue
            if key in corpus_of and budget > 0:
                budget -= 1
                row["verification"] = verify_provenance(row, corpus_of[key], cache)
            kept.append(row)
        gathered[key] = kept
        report[key] = {"gardes": len(kept), **dropped}
    return report


def _values(text: str) -> list[tuple[str, str, float, str]]:
    """(notion, unité, valeur, citation) trouvés dans un texte."""

    found = []
    plain = _plain(text)
    for match in _VALUE.finditer(text):
        number = float(match.group(1).replace(",", "."))
        raw_unit = match.group(2).strip().lower()
        words = _plain(raw_unit).split()
        unit = _UNIT_FAMILY.get(raw_unit) or _UNIT_FAMILY.get(words[0] if words else "", raw_unit)
        before = _plain(text[max(0, match.start() - 60):match.start()])
        notion = next((n for n in _NOTIONS if n in before.split()[-6:] or n in " ".join(before.split()[-6:])), "")
        if notion:
            found.append((notion, unit, number, text[max(0, match.start() - 40):match.end() + 15].strip()))
    return found


def find_divergences(labelled_rows: Sequence[tuple[str, str]]) -> list[str]:
    """``labelled_rows`` : (étiquette de source, texte). Renvoie des phrases décrivant les valeurs différentes pour une même notion."""

    table: dict[tuple[str, str], dict[float, list[str]]] = {}
    for label, text in labelled_rows:
        try:
            values = _values(text)
        except Exception:  # noqa: BLE001 - le rapprochement ne doit jamais bloquer le dossier
            continue
        for notion, unit, number, _quote in values:
            table.setdefault((notion, unit), {}).setdefault(number, []).append(label)
    lines = []
    for (notion, unit), values in sorted(table.items()):
        if len(values) < 2:
            continue
        parts = " ; ".join(f"{value:g} {unit} selon {', '.join(sorted(set(labels))[:4])}" for value, labels in sorted(values.items()))
        lines.append(f"« {notion} » : {parts}")
    return lines[:8]
