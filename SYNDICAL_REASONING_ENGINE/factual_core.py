"""Shared factual core and field-ready preparation for employee cases.

The module extracts only information present in the request.  It deliberately
separates the primary event from secondary context before routing, retrieval or
question generation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import re
import unicodedata
from typing import Iterable

from .factual_models import (
    CanonicalFact,
    FactCategory,
    FactConfidence,
    FactFormulation,
    FactualSource,
)


QUESTION_SALARIE = "QUESTION_SALARIE"
ASSISTANCE_ENTRETIEN_DISCIPLINAIRE = "ASSISTANCE_ENTRETIEN_DISCIPLINAIRE"


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value or "")
    return " ".join(
        "".join(char for char in decomposed if not unicodedata.combining(char))
        .lower()
        .replace("’", " ")
        .replace("'", " ")
        .split()
    )


def _dedupe(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = " ".join(str(value).split()).strip(" -")
        key = normalize(cleaned)
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


@dataclass(frozen=True)
class ActionableQuestion:
    question: str
    target: str
    purpose: str
    priority: str
    answer_type: str
    changes_analysis_if: str
    follow_up: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ActionableDocument:
    document: str
    purpose: str
    confirms_or_rules_out: str
    priority: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class CaseFactualCore:
    requested_path: str
    primary_event: str
    primary_grievance_or_decision: str
    event_category: str
    employee_position: str
    employer_position: str
    facts_certain: list[str] = field(default_factory=list)
    facts_admitted: list[str] = field(default_factory=list)
    facts_disputed: list[str] = field(default_factory=list)
    facts_alleged: list[str] = field(default_factory=list)
    facts_missing: list[str] = field(default_factory=list)
    dates_and_chronology: list[str] = field(default_factory=list)
    persons_and_roles: list[str] = field(default_factory=list)
    workplace_context: list[str] = field(default_factory=list)
    health_and_safety_context: list[str] = field(default_factory=list)
    working_time_context: list[str] = field(default_factory=list)
    mandate_context: list[str] = field(default_factory=list)
    evidence_mentioned: list[str] = field(default_factory=list)
    sanction_or_measure_considered: str = "À préciser"
    contract_change_considered: str = "Non identifié"
    collective_impact_possible: bool = False
    legal_ambiguities: list[str] = field(default_factory=list)
    blocking_ambiguities: list[str] = field(default_factory=list)
    secondary_topics: list[str] = field(default_factory=list)
    forbidden_inferences: list[str] = field(default_factory=list)
    confidence_level: str = "LOW"
    search_query: str = ""
    origin_session_id: str = ""
    canonical_facts: list[CanonicalFact] = field(default_factory=list)
    fact_formulation_count: int = 0
    fact_duplicate_count: int = 0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


SECTION_KEYS = {
    "faits fournis": "facts_certain",
    "faits reconnus": "facts_admitted",
    "faits contestes": "facts_disputed",
    "faits allegues": "facts_alleged",
    "faits non etablis": "facts_not_established",
    "contexte": "facts_context",
    "consequences": "facts_consequence",
    "informations manquantes deja identifiees": "facts_missing",
    "informations manquantes": "facts_missing",
}


def _structured_sections(query: str) -> dict[str, list[str]]:
    sections = {value: [] for value in SECTION_KEYS.values()}
    current: str | None = None
    for raw_line in str(query).splitlines():
        line = raw_line.strip()
        heading = normalize(line.rstrip(":"))
        if heading in SECTION_KEYS:
            current = SECTION_KEYS[heading]
            continue
        if line.endswith(":"):
            current = None
            continue
        if not line.startswith("- ") or current is None:
            continue
        value = line[2:].strip()
        if current == "facts_missing":
            value = re.split(r"\s+\[importance:", value, maxsplit=1)[0].strip()
        if value and not normalize(value).startswith("aucun element fourni"):
            sections[current].append(value)
    return {key: _dedupe(values) for key, values in sections.items()}


_SECTION_CATEGORY = {
    "facts_certain": FactCategory.CERTAIN,
    "facts_admitted": FactCategory.ADMITTED,
    "facts_alleged": FactCategory.ALLEGED,
    "facts_disputed": FactCategory.DISPUTED,
    "facts_not_established": FactCategory.NOT_ESTABLISHED,
    "facts_context": FactCategory.CONTEXT,
    "facts_consequence": FactCategory.CONSEQUENCE,
    "facts_missing": FactCategory.MISSING_INFORMATION,
}
_CATEGORY_SOURCE = {
    FactCategory.CERTAIN: FactualSource.USER_PROVIDED,
    FactCategory.ADMITTED: FactualSource.USER_ADMITTED,
    FactCategory.ALLEGED: FactualSource.USER_ALLEGED,
    FactCategory.DISPUTED: FactualSource.USER_DISPUTED,
    FactCategory.NOT_ESTABLISHED: FactualSource.USER_NOT_ESTABLISHED,
    FactCategory.CONTEXT: FactualSource.USER_CONTEXT,
    FactCategory.CONSEQUENCE: FactualSource.USER_CONSEQUENCE,
    FactCategory.MISSING_INFORMATION: FactualSource.USER_MISSING_INFORMATION,
}
_CATEGORY_CONFIDENCE = {
    FactCategory.CERTAIN: FactConfidence.HIGH,
    FactCategory.ADMITTED: FactConfidence.HIGH,
    FactCategory.ALLEGED: FactConfidence.LOW,
    FactCategory.DISPUTED: FactConfidence.MEDIUM,
    FactCategory.NOT_ESTABLISHED: FactConfidence.LOW,
    FactCategory.CONTEXT: FactConfidence.MEDIUM,
    FactCategory.CONSEQUENCE: FactConfidence.MEDIUM,
    FactCategory.MISSING_INFORMATION: FactConfidence.LOW,
}
_META_WRAPPERS = (
    r"^(?:un\s+)?element\s+defavorable\s+(?:est\s+)?reconnu\s*:\s*",
    r"^fait\s+reconnu\s*:\s*",
    r"^le\s+salarie\s+reconnait\s+au\s+moins\s+cet\s+element\s*:\s*",
    r"^le\s+salarie\s+reconnait\s+certains\s+elements\s*:\s*",
)
_NOT_ESTABLISHED_MARKERS = (
    "aurait",
    "serait",
    "pourrait",
    "semble",
    "n est pas etabli",
    "non etabli",
    "reste a verifier",
    "reste a confirmer",
)


@dataclass(frozen=True)
class _FactCandidate:
    text: str
    category: FactCategory
    factual_source: FactualSource
    ordinal: int


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:20]
    return f"{prefix}-{digest}"


def _strip_meta_wrapper(value: str) -> str:
    cleaned = " ".join(str(value).split()).strip(" -")
    normalized = normalize(cleaned)
    for pattern in _META_WRAPPERS:
        match = re.match(pattern, normalized)
        if match:
            words_to_remove = len(normalized[: match.end()].split())
            words = cleaned.split()
            cleaned = " ".join(words[words_to_remove:]).lstrip(": ").strip()
            break
    return cleaned


def _category_for_text(category: FactCategory, text: str) -> FactCategory:
    normalized = normalize(text)
    if category is FactCategory.CERTAIN:
        if "reconnait" in normalized or "admet" in normalized:
            return FactCategory.ADMITTED
        if any(marker in normalized for marker in _NOT_ESTABLISHED_MARKERS):
            return FactCategory.NOT_ESTABLISHED
    return category


def _communication_admission_key(text: str) -> str | None:
    """Unify only equivalent admissions of authorship for a communication.

    Nearby facts such as admitting particular words, recipients or diffusion
    deliberately do not match this signature.
    """

    normalized = normalize(text)
    if not re.search(r"\b(?:courriels?|emails?|messages?)\b", normalized):
        return None
    if re.search(
        r"\breconnait\s+(?:avoir\s+)?(?:envoye|ecrit)\b",
        normalized,
    ) or re.search(r"\breconnait\s+etre\s+l\s+auteur\b", normalized):
        return "admission:communication-authorship"
    return None


def _semantic_key(category: FactCategory, text: str) -> str:
    normalized = normalize(_strip_meta_wrapper(text)).strip(" .,:;")
    if category is FactCategory.ADMITTED:
        communication = _communication_admission_key(normalized)
        if communication:
            return communication
    return normalized


def _canonical_text(category: FactCategory, candidates: list[_FactCandidate]) -> str:
    if (
        category is FactCategory.ADMITTED
        and any(_communication_admission_key(item.text) for item in candidates)
    ):
        return "Le salarié reconnaît être l’auteur des courriels."
    return _strip_meta_wrapper(candidates[0].text).rstrip(".") + "."


def _subject(text: str) -> str:
    normalized = normalize(text)
    if "salarie" in normalized or "elu" in normalized:
        return "EMPLOYEE"
    if any(marker in normalized for marker in ("employeur", "direction")):
        return "EMPLOYER"
    if any(marker in normalized for marker in ("collegue", "superviseur", "responsable")):
        return "THIRD_PARTY"
    if any(marker in normalized for marker in ("document", "procedure", "reglement", "preuve")):
        return "DOCUMENT_OR_EVIDENCE"
    return "CASE"


def _allegation_author(category: FactCategory, text: str) -> str | None:
    normalized = normalize(text)
    if category is FactCategory.ADMITTED:
        return "EMPLOYEE"
    if category not in {FactCategory.ALLEGED, FactCategory.DISPUTED}:
        return None
    if re.search(r"\b(?:employeur|direction|responsable|superviseur)\b", normalized):
        return "EMPLOYER"
    if re.search(r"\b(?:salarie|elu)\b", normalized):
        return "EMPLOYEE"
    return "UNSPECIFIED"


def _fact_candidates(
    sections: dict[str, list[str]],
    query: str,
) -> list[_FactCandidate]:
    candidates: list[_FactCandidate] = []
    ordinal = 0
    if any(sections.values()):
        section_rows = sections.items()
    else:
        section_rows = (("facts_certain", _sentences(query)),)
    for section, values in section_rows:
        category = _SECTION_CATEGORY[section]
        for value in values:
            resolved = _category_for_text(category, value)
            candidates.append(
                _FactCandidate(
                    text=" ".join(value.split()).strip(" -"),
                    category=resolved,
                    factual_source=_CATEGORY_SOURCE[category],
                    ordinal=ordinal,
                )
            )
            ordinal += 1
    return candidates


def _session_id(
    candidates: list[_FactCandidate],
    requested_path: str | None,
    explicit_session_id: str | None,
) -> str:
    if explicit_session_id is not None:
        cleaned = " ".join(explicit_session_id.split())
        if not cleaned:
            raise ValueError("origin_session_id must be non-empty")
        return cleaned
    identities = sorted(
        {
            f"{item.category.value}:{_semantic_key(item.category, item.text)}"
            for item in candidates
        }
    )
    return _stable_id("session", requested_path or "AUTO", *identities)


def _canonicalize_facts(
    sections: dict[str, list[str]],
    query: str,
    requested_path: str | None,
    explicit_session_id: str | None,
) -> tuple[str, list[CanonicalFact], int]:
    candidates = _fact_candidates(sections, query)
    session_id = _session_id(candidates, requested_path, explicit_session_id)
    groups: dict[tuple[FactCategory, str], list[_FactCandidate]] = {}
    for candidate in candidates:
        key = (candidate.category, _semantic_key(candidate.category, candidate.text))
        groups.setdefault(key, []).append(candidate)

    facts: list[CanonicalFact] = []
    for (category, semantic_key), group in groups.items():
        canonical_text = _canonical_text(category, group)
        fact_id = _stable_id(
            "fact",
            session_id,
            category.value,
            semantic_key,
        )
        formulations = tuple(
            FactFormulation(
                formulation_id=_stable_id(
                    "formulation",
                    session_id,
                    candidate.factual_source.value,
                    normalize(candidate.text),
                    str(candidate.ordinal),
                ),
                text=candidate.text,
                factual_source=candidate.factual_source,
                semantic_duplicate_of=fact_id if index else None,
            )
            for index, candidate in enumerate(group)
        )
        facts.append(
            CanonicalFact(
                fact_id=fact_id,
                canonical_text=canonical_text,
                category=category,
                subject=_subject(canonical_text),
                allegation_author=_allegation_author(category, canonical_text),
                factual_source=group[0].factual_source,
                confidence=_CATEGORY_CONFIDENCE[category],
                original_formulations=formulations,
                origin_session_id=session_id,
            )
        )
    duplicate_count = len(candidates) - len(facts)
    return session_id, facts, duplicate_count


def _fact_texts(
    facts: Iterable[CanonicalFact],
    *categories: FactCategory,
) -> list[str]:
    accepted = set(categories)
    return [fact.canonical_text for fact in facts if fact.category in accepted]


def _sentences(query: str) -> list[str]:
    cleaned = re.sub(r"(?m)^\s*-\s*", "", str(query))
    return _dedupe(
        part.strip()
        for part in re.split(r"(?<=[.!?])\s+|\n+", cleaned)
        if len(part.strip()) > 5 and ":" not in part[:45]
    )


def _contains(text: str, *markers: str) -> bool:
    return any(marker in text for marker in markers)


def _category(text: str) -> str:
    if re.search(r"regle (?:dite )?(?:des )?10 ?%|regle du dixieme", text):
        return "AMBIGUOUS_TEN_PERCENT_RULE"
    if _contains(text, "tourniquet", "badgeage") and _contains(
        text, "pause cigarette", "pauses cigarettes", "pauses"
    ):
        return "BREAKS_AND_BADGE_CONTROL"
    if _contains(text, "epi", "visiere", "sur lunettes", "gants specifiques"):
        return "PPE_AVAILABILITY_OR_SUITABILITY"
    if (
        _contains(text, "procedure", "consigne", "instruction")
        and _contains(
            text,
            "obsolete",
            "plus a jour",
            "ancienne version",
            "version",
            "diffuse",
            "diffusion",
            "accessible",
            "connaissance",
            "formation",
        )
        and _contains(
            text,
            "travail",
            "poste",
            "salarie",
            "employeur",
            "chimique",
            "operation",
            "sanction",
        )
    ) or _contains(text, "catalyseur", "recette", "procedure accessible sur le terminal"):
        return "TECHNICAL_ERROR_AND_OUTDATED_PROCEDURE"
    if _contains(text, "ethylotest", "alcoolemie") or (
        "cariste" in text and "alcool" in text
    ):
        return "POSITIVE_ALCOHOL_TEST"
    if _contains(text, "courriel", "courriels", "messagerie") and _contains(
        text, "insult", "injur", "grossier"
    ):
        return "INSULTING_EMAILS"
    if _contains(text, "tag", "graffiti", "inscription") and _contains(
        text, "grossier", "injur", "fils de pute"
    ):
        return "INSULTING_TAG"
    if _contains(text, "insult", "injur", "propos grossier"):
        return "INSULTING_BEHAVIOR"
    if (
        _contains(
            text,
            "fatigue",
            "epuisement",
            "sommeil",
            "repos insuffisant",
            "manque de repos",
            "risque d accident",
            "danger",
            "securite",
        )
        and _contains(
            text,
            "travail poste",
            "poste de nuit",
            "postes de nuit",
            "travail de nuit",
            "nuits",
            "cycle",
            "3x8",
            "5x8",
        )
    ):
        return "NIGHT_WORK_FATIGUE"
    if (
        _contains(text, "cse", "elu", "representant du personnel", "mandat")
        and _contains(text, "reunion", "convocation", "convoque")
        and _contains(
            text,
            "jour de repos",
            "repos",
            "hors horaire",
            "hors temps de travail",
            "5x8",
            "temps de reunion",
        )
    ):
        return "CSE_MEETING_REST_TIME"
    if (
        _contains(
            text,
            "heures supplementaires",
            "heures en plus",
            "temps supplementaire",
        )
        and _contains(
            text,
            "non paye",
            "pas paye",
            "impaye",
            "bulletin",
            "fiche de paie",
            "paie",
            "pointage",
        )
    ):
        return "UNPAID_OVERTIME"
    if (
        _contains(text, "classification", "coefficient", "niveau", "groupe")
        and _contains(
            text,
            "taches reellement",
            "taches reelles",
            "fonctions reellement",
            "missions exercees",
            "travail reel",
            "responsabilites",
            "autonomie",
            "technicite",
            "ne correspond",
        )
    ):
        return "CLASSIFICATION_ACTUAL_DUTIES"
    if (
        _contains(
            text,
            "passage",
            "passer",
            "passe en",
            "changement",
            "oblige",
            "impose",
        )
        and _contains(
            text,
            "horaire de jour",
            "travail de jour",
            "equipe de jour",
            "jour vers",
            "equipe postee",
            "travail poste",
            "3x8",
            "cycle poste",
            "equipes alternantes",
        )
    ):
        return "WORK_SCHEDULE_CHANGE"
    if "cssct" in text and _contains(
        text, "reunion", "heures de delegation", "credit d heures", "heures"
    ):
        return "CSSCT_MEETING_TIME"
    if _contains(text, "convocation", "sanction", "mise a pied", "avertissement"):
        return "DISCIPLINARY_CASE_UNSPECIFIED"
    return "GENERAL_EMPLOYEE_QUESTION"


PRIMARY_MARKERS = {
    "AMBIGUOUS_TEN_PERCENT_RULE": ("regle", "10 %", "10%"),
    "BREAKS_AND_BADGE_CONTROL": ("pause", "badgeage", "tourniquet"),
    "PPE_AVAILABILITY_OR_SUITABILITY": ("epi", "visiere", "gants", "sur-lunettes"),
    "TECHNICAL_ERROR_AND_OUTDATED_PROCEDURE": (
        "catalyseur",
        "concentration",
        "recette",
        "procedure",
    ),
    "POSITIVE_ALCOHOL_TEST": ("ethylotest", "alcoolemie", "0,8", "alcoolisee"),
    "INSULTING_EMAILS": ("courriel", "mail", "messagerie"),
    "INSULTING_TAG": ("tag", "inscription", "graffiti"),
    "INSULTING_BEHAVIOR": ("insult", "injur", "propos"),
    "WORK_SCHEDULE_CHANGE": ("3x8", "rythme poste", "horaire", "cycle"),
    "CSE_MEETING_REST_TIME": ("cse", "reunion", "repos"),
    "UNPAID_OVERTIME": ("heures", "pointage", "paie", "bulletin"),
    "CLASSIFICATION_ACTUAL_DUTIES": (
        "classification",
        "coefficient",
        "taches",
        "fonctions",
    ),
    "NIGHT_WORK_FATIGUE": ("fatigue", "nuit", "travail poste", "securite"),
    "CSSCT_MEETING_TIME": ("cssct", "reunion"),
    "DISCIPLINARY_CASE_UNSPECIFIED": ("convocation", "sanction", "reproch"),
    "GENERAL_EMPLOYEE_QUESTION": (),
}


def _primary_fact(category: str, facts: list[str], query: str) -> str:
    markers = PRIMARY_MARKERS[category]
    for fact in facts:
        text = normalize(fact)
        if not markers or any(normalize(marker) in text for marker in markers):
            return fact.rstrip(".") + "."
    direct = _sentences(query)
    for sentence in direct:
        text = normalize(sentence)
        if not markers or any(normalize(marker) in text for marker in markers):
            return sentence.rstrip(".") + "."
    return "La demande du salarié doit être précisée."


def _grievance(category: str, primary: str, text: str) -> str:
    labels = {
        "AMBIGUOUS_TEN_PERCENT_RULE": "Disparition alléguée d'une règle non définie appelée « règle des 10 % ».",
        "BREAKS_AND_BADGE_CONTROL": "Pauses jugées trop fréquentes ou trop longues, avec utilisation envisagée de données de badgeage.",
        "PPE_AVAILABILITY_OR_SUITABILITY": "Adéquation, disponibilité ou utilisation des EPI à vérifier au regard du risque réel, sans préjuger la conduite du salarié.",
        "TECHNICAL_ERROR_AND_OUTDATED_PROCEDURE": "Applicabilité, mise à jour et diffusion effective d'une procédure interne potentiellement obsolète à vérifier.",
        "POSITIVE_ALCOHOL_TEST": "Contrôle d'alcoolémie annoncé positif sur un poste présenté comme à risque.",
        "INSULTING_EMAILS": "Envoi de courriels insultants.",
        "INSULTING_TAG": "Inscription ou tag grossier sur une installation.",
        "INSULTING_BEHAVIOR": "Propos insultants ou injurieux.",
        "WORK_SCHEDULE_CHANGE": "Passage imposé ou proposé d'un horaire de jour vers un rythme posté.",
        "CSE_MEETING_REST_TIME": "Traitement du temps consacré à une réunion CSE organisée pendant un repos.",
        "UNPAID_OVERTIME": "Écart allégué entre les heures supplémentaires tracées et leur paiement.",
        "CLASSIFICATION_ACTUAL_DUTIES": "Adéquation de la classification aux fonctions réellement exercées.",
        "NIGHT_WORK_FATIGUE": "Fatigue liée au travail de nuit ou posté et prévention des risques associés.",
        "CSSCT_MEETING_TIME": "Refus ou traitement contesté du temps destiné à une réunion CSSCT.",
        "DISCIPLINARY_CASE_UNSPECIFIED": "Grief disciplinaire à préciser.",
        "GENERAL_EMPLOYEE_QUESTION": primary,
    }
    value = labels[category]
    if category == "WORK_SCHEDULE_CHANGE" and "temporaire" in text:
        value = "Passage temporaire annoncé d'un horaire de jour vers un cycle posté."
    if category == "TECHNICAL_ERROR_AND_OUTDATED_PROCEDURE" and _contains(
        text, "sanction", "faute", "reproch", "disciplinaire", "mise a pied"
    ):
        value = (
            "Applicabilité et diffusion d'une procédure interne à vérifier avant "
            "de qualifier le grief disciplinaire allégué."
        )
    return value


def _employee_position(
    admitted: list[str], disputed: list[str], alleged: list[str]
) -> str:
    if admitted and disputed:
        return (
            "Le salarié reconnaît certains éléments mais conteste leur portée : "
            + admitted[0]
            + " "
            + disputed[0]
        )
    if admitted:
        return "Le salarié reconnaît au moins cet élément : " + admitted[0]
    if disputed:
        return "Le salarié conteste au moins cet élément : " + disputed[0]
    if alleged:
        return "La position du salarié doit être confirmée ; des éléments sont seulement allégués."
    return "La position exacte du salarié reste à recueillir."


def _employer_position(facts: list[str]) -> str:
    for fact in facts:
        text = normalize(fact)
        if _contains(text, "employeur", "direction", "responsable", "superviseur"):
            return fact
    return "La position précise de l'employeur reste à demander."


def _conditional_missing_information(category: str) -> list[str]:
    """List decisive information to obtain without turning it into a fact."""

    return {
        "WORK_SCHEDULE_CHANGE": [
            "Contrat, avenants et clause relative aux horaires.",
            "Cycle projeté, durée et délai de prévenance.",
            "Accord collectif applicable et éventuelle consultation du CSE.",
            "Conséquences personnelles concrètes et alternatives étudiées.",
        ],
        "TECHNICAL_ERROR_AND_OUTDATED_PROCEDURE": [
            "Version applicable de la procédure à la date des faits.",
            "Preuve de diffusion, d'accès et de formation du salarié.",
            "Consignes contradictoires ou alertes préalables éventuelles.",
        ],
        "CSE_MEETING_REST_TIME": [
            "Qualité du participant et nature exacte de la réunion CSE.",
            "Convocation, horaires, trajet et planning de repos.",
            "Accord ou usage applicable au traitement du temps de réunion.",
        ],
        "UNPAID_OVERTIME": [
            "Période, pointages et bulletins concernés.",
            "Validation hiérarchique ou nécessité des heures.",
            "Règle locale de décompte et de majoration.",
        ],
        "CLASSIFICATION_ACTUAL_DUTIES": [
            "Fiche de poste, tâches réelles et période d'exercice.",
            "Autonomie, responsabilités et technicité démontrables.",
            "Coefficient actuel et grille conventionnelle applicable.",
        ],
        "NIGHT_WORK_FATIGUE": [
            "Cycles, nuits, pauses et repos réellement accomplis.",
            "Charge, effectifs, incidents et alertes collectives tracés.",
            "DUERP et mesures de prévention du travail de nuit.",
        ],
    }.get(category, [])


def _matching(facts: list[str], markers: tuple[str, ...]) -> list[str]:
    return [
        fact
        for fact in facts
        if any(marker in normalize(fact) for marker in markers)
    ]


def build_case_factual_core(
    query: str,
    requested_path: str | None = None,
    origin_session_id: str | None = None,
) -> CaseFactualCore:
    sections = _structured_sections(query)
    structured = any(sections.values())
    session_id, canonical_facts, duplicate_count = _canonicalize_facts(
        sections,
        query,
        requested_path,
        origin_session_id,
    )
    provided = (
        _fact_texts(
            canonical_facts,
            FactCategory.CERTAIN,
            FactCategory.CONTEXT,
            FactCategory.CONSEQUENCE,
        )
        if structured
        else [
            fact.canonical_text
            for fact in canonical_facts
            if fact.category is not FactCategory.MISSING_INFORMATION
        ]
    )
    admitted = _fact_texts(canonical_facts, FactCategory.ADMITTED)
    disputed = _fact_texts(canonical_facts, FactCategory.DISPUTED)
    alleged = _fact_texts(
        canonical_facts,
        FactCategory.ALLEGED,
        FactCategory.NOT_ESTABLISHED,
    )
    missing = _fact_texts(canonical_facts, FactCategory.MISSING_INFORMATION)
    all_facts = [
        fact.canonical_text
        for fact in canonical_facts
        if fact.category is not FactCategory.MISSING_INFORMATION
    ]
    text = normalize(" ".join(all_facts or [query]))
    category = _category(text)
    primary = _primary_fact(category, provided + admitted + alleged, query)

    path = requested_path or (
        ASSISTANCE_ENTRETIEN_DISCIPLINAIRE
        if category
        in {
            "INSULTING_EMAILS",
            "INSULTING_TAG",
            "INSULTING_BEHAVIOR",
            "PPE_AVAILABILITY_OR_SUITABILITY",
            "TECHNICAL_ERROR_AND_OUTDATED_PROCEDURE",
            "POSITIVE_ALCOHOL_TEST",
            "DISCIPLINARY_CASE_UNSPECIFIED",
            "BREAKS_AND_BADGE_CONTROL",
        }
        and re.search(r"convocation|sanction|faute|mise a pied|licenciement|reproch", text)
        else QUESTION_SALARIE
    )
    blocking = []
    if category == "AMBIGUOUS_TEN_PERCENT_RULE":
        blocking.append("Définir ce que désigne exactement l'expression « règle des 10 % ».")
    if "incomplet" in text:
        blocking.append("Obtenir la partie manquante du récit avant toute conclusion.")
    if category == "CSSCT_MEETING_TIME" and _contains(
        text, "reunion cssct", "heures de delegation"
    ):
        blocking.append("Distinguer le temps de réunion CSSCT du crédit d'heures de délégation.")

    evidence = _matching(
        all_facts,
        (
            "courriel",
            "badge",
            "tourniquet",
            "photo",
            "temoin",
            "historique informatique",
            "terminal",
            "ethylotest",
            "reglement interieur",
            "convocation",
            "planning",
            "contrat",
        ),
    )
    dates = _matching(
        all_facts,
        (
            "date",
            "heure",
            "depuis",
            "pendant",
            "six mois",
            "quatre ans",
            "huit ans",
            "quinze ans",
            "successifs",
        ),
    )
    persons = _matching(
        all_facts,
        (
            "salarie",
            "collegue",
            "superviseur",
            "employeur",
            "direction",
            "elu",
            "secretaire du cse",
            "cariste",
            "technicien",
            "operateur",
        ),
    )
    safety = _matching(
        all_facts,
        (
            "seveso",
            "securite",
            "epi",
            "acide",
            "fuite de vapeur",
            "risque",
            "alcool",
            "fatigue",
            "souffrance",
        ),
    )
    working_time = _matching(
        all_facts,
        (
            "horaire",
            "poste de nuit",
            "3x8",
            "cycle",
            "pause",
            "repos",
            "week-end",
            "jours feries",
            "temps de travail",
        ),
    )
    mandate = _matching(
        all_facts,
        (
            "cse",
            "cssct",
            "mandat",
            "elu",
            "delegation",
        ),
    )
    secondary = []
    if category == "INSULTING_EMAILS" and "alcool" in text:
        secondary.append("Consommation d'alcool alléguée comme contexte, sans remplacer les courriels comme grief.")
    if category == "INSULTING_BEHAVIOR" and "fatigue" in text:
        secondary.append("Fatigue et surcharge alléguées comme contexte, sans effacer les propos.")
    if category == "BREAKS_AND_BADGE_CONTROL" and "seveso" in text:
        secondary.append("Finalité de sécurité Seveso du badgeage, distincte du grief relatif aux pauses.")
    if category == "WORK_SCHEDULE_CHANGE" and _contains(text, "remuneration", "salaire", "prime"):
        secondary.append("Rémunération éventuelle, secondaire par rapport au changement imposé.")

    forbidden = [
        "Ne pas injecter un fait, un document ou un scénario absent de la demande.",
        "Ne pas présenter une allégation comme une preuve.",
        "Ne pas promettre une issue favorable ou défavorable.",
    ]
    category_forbidden = {
        "INSULTING_EMAILS": "Ne pas remplacer les courriels insultants par l'alcool comme grief principal.",
        "INSULTING_BEHAVIOR": "Ne pas transformer des injures en menace ou violence sans fait correspondant.",
        "BREAKS_AND_BADGE_CONTROL": "Ne pas confondre finalité de sécurité du badgeage et licéité de son usage disciplinaire.",
        "PPE_AVAILABILITY_OR_SUITABILITY": "Ne pas conclure que l'indisponibilité alléguée supprime automatiquement toute faute.",
        "TECHNICAL_ERROR_AND_OUTDATED_PROCEDURE": "Ne pas transformer une procédure potentiellement obsolète en défaut de compétence.",
        "WORK_SCHEDULE_CHANGE": "Ne pas déduire démission, volontariat ou acceptation d'un avantage salarial.",
        "CSE_MEETING_REST_TIME": "Ne pas transformer une convocation à une réunion CSE en convocation disciplinaire.",
        "UNPAID_OVERTIME": "Ne pas conclure à un impayé avant rapprochement du pointage et du bulletin.",
        "CLASSIFICATION_ACTUAL_DUTIES": "Ne pas déduire une classification des seuls intitulés de poste.",
        "NIGHT_WORK_FATIGUE": "Ne pas transformer une fatigue alléguée en diagnostic médical individuel.",
        "AMBIGUOUS_TEN_PERCENT_RULE": "Ne pas supposer qu'il s'agit de la règle légale du dixième.",
    }
    if category in category_forbidden:
        forbidden.append(category_forbidden[category])

    sanction = "À préciser"
    for label in ("licenciement", "mise à pied", "avertissement", "sanction"):
        if label in text:
            sanction = label
            break
    contract_change = (
        _grievance(category, primary, text)
        if category == "WORK_SCHEDULE_CHANGE"
        else "Non identifié"
    )
    search_parts = [
        _grievance(category, primary, text),
        *admitted[:1],
        *disputed[:1],
        *secondary[:2],
    ]
    if category == "TECHNICAL_ERROR_AND_OUTDATED_PROCEDURE":
        search_parts.append(primary)
    return CaseFactualCore(
        requested_path=path,
        primary_event=primary,
        primary_grievance_or_decision=_grievance(category, primary, text),
        event_category=category,
        employee_position=_employee_position(admitted, disputed, alleged),
        employer_position=_employer_position([*alleged, *provided]),
        facts_certain=provided,
        facts_admitted=admitted,
        facts_disputed=disputed,
        facts_alleged=alleged,
        facts_missing=missing,
        dates_and_chronology=dates,
        persons_and_roles=persons,
        workplace_context=_matching(
            all_facts,
            ("laboratoire", "site industriel", "installation", "travail", "production"),
        ),
        health_and_safety_context=safety,
        working_time_context=working_time,
        mandate_context=mandate,
        evidence_mentioned=evidence,
        sanction_or_measure_considered=sanction,
        contract_change_considered=contract_change,
        collective_impact_possible=_contains(
            text,
            "effectif",
            "equipe de jour",
            "autres salaries",
            "cse",
            "cssct",
            "collectif",
        ),
        legal_ambiguities=_dedupe(
            [*missing[:5], *_conditional_missing_information(category)]
        ),
        blocking_ambiguities=_dedupe(blocking),
        secondary_topics=_dedupe(secondary),
        forbidden_inferences=_dedupe(forbidden),
        confidence_level=(
            "LOW" if blocking else "HIGH" if category != "GENERAL_EMPLOYEE_QUESTION" else "MEDIUM"
        ),
        search_query=" ".join(_dedupe(search_parts)),
        origin_session_id=session_id,
        canonical_facts=canonical_facts,
        fact_formulation_count=sum(
            len(fact.original_formulations) for fact in canonical_facts
        ),
        fact_duplicate_count=duplicate_count,
    )


def _q(
    question: str,
    target: str,
    purpose: str,
    priority: str,
    answer_type: str,
    changes: str,
    follow_up: str,
) -> ActionableQuestion:
    return ActionableQuestion(
        question=question,
        target=target,
        purpose=purpose,
        priority=priority,
        answer_type=answer_type,
        changes_analysis_if=changes,
        follow_up=follow_up,
    )


def _d(
    document: str,
    purpose: str,
    confirms: str,
    priority: str,
) -> ActionableDocument:
    return ActionableDocument(document, purpose, confirms, priority)


def _event_questions(core: CaseFactualCore) -> tuple[list[ActionableQuestion], list[ActionableQuestion], list[ActionableDocument], list[ActionableQuestion]]:
    category = core.event_category
    employee: list[ActionableQuestion] = []
    employer: list[ActionableQuestion] = []
    documents: list[ActionableDocument] = []
    checks: list[ActionableQuestion] = []

    if category == "AMBIGUOUS_TEN_PERCENT_RULE":
        employee.append(_q(
            "Que désigne exactement pour vous la « règle des 10 % » ?",
            "EMPLOYEE",
            "Identifier la règle avant toute analyse de fond.",
            "BLOCKING",
            "FREE_TEXT",
            "Le type de source et l'analyse changent entièrement selon la définition.",
            "Demander un exemple concret avant et après le changement.",
        ))
        documents.append(_d(
            "Texte ou support de l'ancienne « règle des 10 % »",
            "Identifier son fondement et son contenu exact.",
            "Écarter une confusion avec la règle légale du dixième.",
            "BLOCKING",
        ))
    elif category == "BREAKS_AND_BADGE_CONTROL":
        employee.extend([
            _q("Quelles pauses reconnaissez-vous exactement ?", "EMPLOYEE", "Séparer les faits admis du calcul patronal.", "BLOCKING", "FREE_TEXT", "La défense change selon le nombre et la durée reconnus.", "Comparer avec les relevés complets."),
            _q("Aviez-vous été informé que le tourniquet pouvait contrôler les pauses ?", "EMPLOYEE", "Vérifier la transparence du dispositif.", "HIGH", "YES_NO", "Une absence d'information fragilise l'usage disciplinaire.", "Demander la notice remise aux salariés."),
        ])
        employer.extend([
            _q("Comment avez-vous calculé chaque pause reprochée ?", "EMPLOYER", "Contrôler la méthode et l'intégrité de la preuve.", "BLOCKING", "FREE_TEXT", "Un calcul approximatif fragilise le grief.", "Exiger le détail date par date."),
            _q("Quelle finalité déclarée autorise l'usage disciplinaire du tourniquet ?", "EMPLOYER", "Comparer la finalité sécurité à l'usage de contrôle.", "BLOCKING", "DOCUMENT", "Une finalité différente impose un contrôle de licéité.", "Demander registre, notice RGPD et information CSE."),
            _q("Le CSE a-t-il été informé ou consulté sur cet usage ?", "EMPLOYER", "Vérifier la garantie collective du dispositif de contrôle.", "HIGH", "YES_NO", "L'absence de consultation peut fragiliser l'usage.", "Demander l'avis et le procès-verbal."),
        ])
        documents.extend([
            _d("Relevés complets du tourniquet", "Contrôler dates, passages et méthode.", "Confirmer ou écarter les durées reprochées.", "BLOCKING"),
            _d("Notice RGPD et registre du traitement", "Identifier finalité, accès et conservation.", "Vérifier si l'usage disciplinaire était déclaré.", "BLOCKING"),
            _d("Information ou consultation du CSE", "Contrôler la mise en place du contrôle.", "Confirmer les garanties collectives.", "HIGH"),
        ])
        checks.append(_q("La CNIL ou une source officielle encadre-t-elle cet usage précis ?", "DOCUMENT", "Vérifier la licéité sans l'inventer.", "HIGH", "DOCUMENT", "La stratégie probatoire dépend des conditions applicables.", "Comparer la source aux faits et à la notice locale."))
    elif category == "PPE_AVAILABILITY_OR_SUITABILITY":
        employee.extend([
            _q("Quels EPI étaient réellement disponibles au moment de l'opération ?", "EMPLOYEE", "Établir les moyens accessibles.", "BLOCKING", "FREE_TEXT", "La responsabilité change si l'EPI requis manquait.", "Identifier témoins et signalements."),
            _q("Aviez-vous signalé la buée ou l'inadaptation avant l'opération ?", "EMPLOYEE", "Vérifier l'alerte préalable.", "HIGH", "YES_NO", "Un signalement connu renforce la défaillance préventive.", "Demander la trace du signalement."),
            _q("Pouviez-vous arrêter ou reporter l'opération ?", "EMPLOYEE", "Apprécier le choix laissé au salarié.", "HIGH", "YES_NO", "La poursuite malgré une alternative peut fragiliser sa position.", "Préciser l'urgence et la consigne reçue."),
        ])
        employer.extend([
            _q("Quelle consigne EPI précise s'appliquait à cette opération ?", "EMPLOYER", "Identifier la protection attendue sans présumer un grief.", "BLOCKING", "DOCUMENT", "Sans consigne précise, l'analyse de prévention reste incomplète.", "Demander sa version applicable."),
            _q("Quelle protection compatible avec les lunettes de vue était disponible ?", "EMPLOYER", "Contrôler l'adaptation des EPI.", "BLOCKING", "DOCUMENT", "Une protection inadaptée peut engager l'organisation.", "Demander registre de fourniture et stock."),
        ])
        documents.extend([
            _d("Consigne EPI applicable", "Identifier l'équipement obligatoire.", "Confirmer le manquement exact.", "BLOCKING"),
            _d("Registre de fourniture et état du stock EPI", "Vérifier disponibilité et adaptation.", "Confirmer ou écarter la rupture annoncée.", "BLOCKING"),
            _d("Signalements et DUERP", "Documenter le risque et les alertes.", "Évaluer la responsabilité préventive.", "HIGH"),
        ])
    elif category == "TECHNICAL_ERROR_AND_OUTDATED_PROCEDURE":
        employee.extend([
            _q("Quelle recette était affichée sur votre terminal au moment du dosage ?", "EMPLOYEE", "Identifier la consigne réellement accessible.", "BLOCKING", "DOCUMENT", "Une version obsolète change la qualification de l'erreur.", "Conserver une copie horodatée."),
            _q("Aviez-vous reçu une autre consigne écrite ou orale ?", "EMPLOYEE", "Vérifier la connaissance du nouveau dosage.", "HIGH", "FREE_TEXT", "Une consigne claire peut renforcer le grief.", "Identifier auteur, date et témoins."),
        ])
        employer.extend([
            _q("À quelle date et heure la nouvelle recette a-t-elle été publiée ?", "EMPLOYER", "Reconstituer la chronologie informatique.", "BLOCKING", "DATE", "Une publication postérieure ou non accessible fragilise le grief.", "Demander les journaux système."),
            _q("Quel contrôle croisé devait empêcher une erreur de dosage ?", "EMPLOYER", "Évaluer l'organisation et les responsabilités.", "HIGH", "FREE_TEXT", "L'absence de contrôle peut révéler une défaillance organisationnelle.", "Demander la procédure de validation."),
        ])
        documents.extend([
            _d("Version horodatée de la recette", "Établir la consigne accessible.", "Confirmer ou écarter l'obsolescence.", "BLOCKING"),
            _d("Journaux de publication et de consultation", "Dater la diffusion et l'accès.", "Établir la connaissance possible du salarié.", "BLOCKING"),
            _d("Fiche de lot et contrôle croisé", "Reconstituer l'opération.", "Répartir les responsabilités techniques.", "HIGH"),
        ])
    elif category == "POSITIVE_ALCOHOL_TEST":
        employee.extend([
            _q("Avez-vous pu demander une contre-expertise immédiatement ?", "EMPLOYEE", "Vérifier l'effectivité de la garantie.", "BLOCKING", "YES_NO", "Une impossibilité peut fragiliser la preuve.", "Préciser l'heure et la réponse donnée."),
            _q("Aviez-vous déjà pris le chariot avant le contrôle ?", "EMPLOYEE", "Mesurer le risque concret.", "HIGH", "YES_NO", "La gravité peut varier selon l'exposition effective.", "Identifier témoins et badgeage."),
        ])
        employer.extend([
            _q("Quelle clause du règlement intérieur autorise ce contrôle ?", "EMPLOYER", "Vérifier le fondement du contrôle.", "BLOCKING", "DOCUMENT", "Une clause inapplicable fragilise la procédure.", "Demander la version en vigueur."),
            _q("Quelle unité, quel appareil et quelle heure figurent au procès-verbal ?", "EMPLOYER", "Contrôler la fiabilité du résultat.", "BLOCKING", "DOCUMENT", "Une donnée imprécise empêche une conclusion fiable.", "Demander calibration et procès-verbal."),
        ])
        documents.extend([
            _d("Règlement intérieur en vigueur", "Vérifier postes et procédure contrôlables.", "Confirmer le fondement du contrôle.", "BLOCKING"),
            _d("Procès-verbal et calibration de l'éthylotest", "Contrôler heure, unité et fiabilité.", "Écarter une irrégularité supposée.", "BLOCKING"),
            _d("Preuve de proposition de contre-expertise", "Vérifier la garantie réelle.", "Confirmer ou écarter une contestation procédurale.", "HIGH"),
        ])
    elif category in {"INSULTING_EMAILS", "INSULTING_TAG", "INSULTING_BEHAVIOR"}:
        medium = "courriels" if category == "INSULTING_EMAILS" else "propos ou inscription"
        employee.extend([
            _q(f"Que reconnaissez-vous exactement concernant les {medium} ?", "EMPLOYEE", "Fixer la position avant la stratégie.", "BLOCKING", "FREE_TEXT", "La stratégie diffère entre reconnaissance et contestation.", "Faire préciser chaque élément admis."),
            _q("Quels mots exacts ont été employés ?", "EMPLOYEE", "Délimiter le grief sans reformulation.", "BLOCKING", "FREE_TEXT", "La gravité dépend des termes exacts.", "Comparer avec la preuve complète."),
            _q("Avez-vous présenté des excuses ou exprimé des regrets ?", "EMPLOYEE", "Préparer une atténuation si les faits sont reconnus.", "HIGH", "YES_NO", "Des excuses rapides peuvent soutenir la proportionnalité.", "Préparer une formulation sincère."),
        ])
        if category == "INSULTING_BEHAVIOR":
            employee.append(_q("Quel planning et quels repos aviez-vous avant les faits ?", "EMPLOYEE", "Objectiver la fatigue alléguée.", "HIGH", "DOCUMENT", "Des repos insuffisants renforcent le contexte sans supprimer la faute.", "Rassembler planning et pointage."))
        employer.extend([
            _q("Quel grief exact retenez-vous, mot pour mot ?", "EMPLOYER", "Empêcher une aggravation abstraite du grief.", "BLOCKING", "FREE_TEXT", "Une menace alléguée doit être prouvée séparément.", "Faire acter la réponse au compte rendu."),
            _q("Quelles preuves complètes établissent le contenu et la diffusion ?", "EMPLOYER", "Contrôler preuve, destinataires et publicité.", "BLOCKING", "DOCUMENT", "Une preuve partielle peut changer la qualification.", "Demander les pièces non tronquées."),
            _q("Quelle sanction envisagez-vous et quels précédents comparez-vous ?", "EMPLOYER", "Examiner proportionnalité et égalité de traitement.", "HIGH", "FREE_TEXT", "Un traitement incohérent ouvre une contestation ou négociation.", "Demander les précédents anonymisés."),
        ])
        documents.extend([
            _d("Preuve complète des propos ou écrits", "Établir mots, date, destinataires et diffusion.", "Confirmer le grief exact.", "BLOCKING"),
            _d("Convocation et lettre de griefs", "Contrôler objet, dates et qualification.", "Écarter un grief ajouté tardivement.", "BLOCKING"),
            _d("Règlement intérieur et sanctions comparables", "Vérifier règle et proportionnalité.", "Comparer l'égalité de traitement.", "HIGH"),
        ])
    elif category == "WORK_SCHEDULE_CHANGE":
        employee.extend([
            _q("Quel cycle exact et quels horaires vous ont été communiqués ?", "EMPLOYEE", "Mesurer le changement réel.", "BLOCKING", "DOCUMENT", "La présence de nuit ou de week-end change l'analyse.", "Demander le planning écrit."),
            _q("Quelle contrainte familiale ou personnelle concrète souhaitez-vous faire valoir ?", "EMPLOYEE", "Documenter l'impact sans demander de détail médical excessif.", "HIGH", "FREE_TEXT", "Une atteinte importante renforce la proportionnalité.", "Identifier un aménagement possible."),
            _q("Quelles contraintes de transport le nouveau cycle créerait-il ?", "EMPLOYEE", "Mesurer une difficulté pratique vérifiable.", "MEDIUM", "FREE_TEXT", "Une impossibilité concrète peut soutenir un aménagement.", "Rassembler horaires de transport ou justificatifs utiles."),
            _q("Quel est votre objectif : maintien en journée, aménagement ou négociation ?", "EMPLOYEE", "Aligner la stratégie sur l'objectif réel.", "HIGH", "CHOICE", "La ligne syndicale dépend de la solution recherchée.", "Préparer une proposition prioritaire et une alternative."),
        ])
        employer.extend([
            _q("Quelle clause du contrat autoriserait ce changement ?", "EMPLOYER", "Qualifier la portée du contrat.", "BLOCKING", "DOCUMENT", "Une clause absente ou limitée peut changer la qualification.", "Demander contrat et avenants."),
            _q("Le changement est-il temporaire ou permanent, et quel délai de prévenance retenez-vous ?", "EMPLOYER", "Vérifier la durée et l'organisation possible.", "BLOCKING", "CHOICE", "Une durée indéterminée contredit le caractère temporaire.", "Faire confirmer la date d'effet par écrit."),
            _q("Quels volontaires ou quelles permutations avez-vous recherchés ?", "EMPLOYER", "Tester les alternatives moins contraignantes.", "HIGH", "FREE_TEXT", "L'absence de recherche fragilise la proportionnalité.", "Demander les critères de choix."),
            _q("Quel accord INEOS encadre le passage en horaires postés ?", "EMPLOYER", "Identifier la règle locale prioritaire.", "HIGH", "DOCUMENT", "L'accord peut prévoir garanties, délais ou contreparties.", "Demander la clause précise."),
        ])
        if core.collective_impact_possible:
            employer.extend([
                _q("Quels effectifs de jour resteraient après le changement ?", "EMPLOYER", "Mesurer l'impact collectif et la charge.", "HIGH", "FREE_TEXT", "Une réduction d'effectif peut justifier une intervention collective.", "Demander le tableau avant et après."),
                _q("Le CSE a-t-il été informé ou consulté sur cette organisation ?", "EMPLOYER", "Vérifier la dimension collective.", "HIGH", "YES_NO", "Une réorganisation collective peut appeler une consultation.", "Demander ordre du jour et procès-verbal."),
            ])
        documents.extend([
            _d("Contrat et avenants", "Lire la clause exacte sur les horaires.", "Qualifier contrat ou conditions de travail.", "BLOCKING"),
            _d("Courrier de changement et planning projeté", "Établir durée, cycle et délai.", "Confirmer les contraintes réelles.", "BLOCKING"),
            _d("Accord INEOS sur horaires postés", "Identifier garanties et contreparties.", "Comparer la décision au droit local.", "HIGH"),
        ])
        if core.collective_impact_possible:
            documents.append(
                _d("Effectifs avant/après du laboratoire", "Mesurer la réduction éventuelle de l'équipe de jour.", "Confirmer l'impact collectif et la charge restante.", "HIGH")
            )
    elif category == "CSE_MEETING_REST_TIME":
        employee.extend([
            _q("Quelle était votre qualité pour cette réunion CSE ?", "EMPLOYEE", "Identifier le régime du temps de réunion.", "BLOCKING", "CHOICE", "Le traitement dépend du mandat et de la nature de la réunion.", "Faire préciser mandat, convocation et horaires."),
            _q("Le repos a-t-il été déplacé, réduit ou maintenu ?", "EMPLOYEE", "Mesurer la conséquence concrète sur le repos.", "HIGH", "FREE_TEXT", "Le traitement dépend de l'atteinte effective au repos.", "Comparer planning prévu et réalisé."),
        ])
        employer.extend([
            _q("Quel texte ou accord fonde le traitement de ce temps de réunion ?", "EMPLOYER", "Identifier la règle applicable.", "BLOCKING", "DOCUMENT", "Paiement, récupération et imputation dépendent du texte applicable.", "Demander la clause précise."),
            _q("Comment le temps et le repos ont-ils été enregistrés ?", "EMPLOYER", "Contrôler le traitement en paie et planning.", "HIGH", "DOCUMENT", "Un écart de compteur peut nécessiter une régularisation.", "Rapprocher convocation, planning et bulletin."),
        ])
        documents.extend([
            _d("Convocation à la réunion CSE", "Établir nature, date et horaires de la réunion.", "Distinguer réunion d'instance et autre activité.", "BLOCKING"),
            _d("Planning, compteur de temps et bulletin", "Contrôler temps et repos.", "Confirmer paiement, récupération ou écart.", "HIGH"),
            _d("Accord CSE ou règle applicable au temps de réunion", "Identifier le régime local.", "Déterminer les garanties applicables.", "HIGH"),
        ])
    elif category == "UNPAID_OVERTIME":
        employee.extend([
            _q("Quelles heures supplémentaires figurent au pointage mais pas sur le bulletin ?", "EMPLOYEE", "Chiffrer l'écart sans le présumer.", "BLOCKING", "DOCUMENT", "Le volume et les dates déterminent la vérification.", "Établir un tableau date par date."),
            _q("Ces heures étaient-elles demandées, validées ou rendues nécessaires par la charge ?", "EMPLOYEE", "Établir les conditions de réalisation.", "HIGH", "FREE_TEXT", "La connaissance de l'employeur influence l'analyse.", "Identifier consignes et témoins."),
        ])
        employer.append(_q("Comment les pointages ont-ils été rapprochés de la paie ?", "EMPLOYER", "Contrôler le traitement des heures.", "BLOCKING", "DOCUMENT", "Un écart inexpliqué appelle une vérification.", "Demander le détail du calcul."))
        documents.extend([
            _d("Pointages détaillés", "Reconstituer les heures réalisées.", "Établir les dates et durées.", "BLOCKING"),
            _d("Bulletins de paie correspondants", "Comparer paiement et majorations.", "Confirmer ou écarter l'écart.", "BLOCKING"),
            _d("Planning et validation des heures", "Établir la connaissance de l'employeur.", "Qualifier les conditions de réalisation.", "HIGH"),
        ])
    elif category == "CLASSIFICATION_ACTUAL_DUTIES":
        employee.extend([
            _q("Quelles tâches, responsabilités et autonomie exercez-vous réellement ?", "EMPLOYEE", "Comparer le travail réel aux critères de classification.", "BLOCKING", "FREE_TEXT", "La classification dépend des fonctions démontrables.", "Donner des exemples datés."),
            _q("Depuis quand ces fonctions sont-elles exercées ?", "EMPLOYEE", "Délimiter la période concernée.", "HIGH", "DATE", "La durée influence la portée de la demande.", "Rassembler les traces correspondantes."),
        ])
        employer.append(_q("Quels critères conventionnels justifient le coefficient actuel ?", "EMPLOYER", "Obtenir la méthode de classement.", "BLOCKING", "DOCUMENT", "La comparaison exige les critères réellement appliqués.", "Demander fiche de poste et grille."))
        documents.extend([
            _d("Fiche de poste et avenants", "Identifier les fonctions contractuelles.", "Comparer fonctions prévues et réelles.", "BLOCKING"),
            _d("Grille de classification applicable", "Identifier les critères conventionnels.", "Comparer niveau, autonomie et technicité.", "BLOCKING"),
            _d("Preuves des tâches réellement exercées", "Documenter le travail réel.", "Établir responsabilités et autonomie.", "HIGH"),
        ])
    elif category == "NIGHT_WORK_FATIGUE":
        employee.extend([
            _q("Quels cycles, nuits et repos ont précédé la fatigue signalée ?", "EMPLOYEE", "Objectiver l'organisation du travail.", "BLOCKING", "DOCUMENT", "L'analyse dépend des horaires et repos réels.", "Rassembler planning et pointage."),
            _q("Quels incidents, erreurs ou alertes de sécurité ont été signalés ?", "EMPLOYEE", "Relier l'organisation à un risque professionnel vérifiable.", "HIGH", "FREE_TEXT", "Des alertes tracées renforcent le besoin de prévention.", "Éviter tout détail médical individuel inutile."),
        ])
        employer.extend([
            _q("Quelle évaluation des risques couvre le travail de nuit et la fatigue ?", "EMPLOYER", "Contrôler la prévention collective.", "BLOCKING", "DOCUMENT", "L'absence d'évaluation peut révéler une lacune de prévention.", "Demander DUERP et plan d'action."),
            _q("Quels ajustements de cycle, pauses ou effectifs ont été étudiés ?", "EMPLOYER", "Identifier les mesures de prévention.", "HIGH", "FREE_TEXT", "Les mesures concrètes permettent d'évaluer l'organisation.", "Demander les décisions et leur suivi."),
        ])
        documents.extend([
            _d("Plannings et relevés de repos", "Objectiver cycles et repos.", "Vérifier l'exposition organisationnelle.", "BLOCKING"),
            _d("DUERP et plan de prévention du travail de nuit", "Identifier les risques et mesures collectives.", "Évaluer la prévention sans donnée médicale individuelle.", "BLOCKING"),
            _d("Signalements et comptes rendus CSE/CSSCT pertinents", "Rechercher les alertes collectives.", "Documenter les mesures déjà discutées.", "HIGH"),
        ])
    elif category == "CSSCT_MEETING_TIME":
        employee.extend([
            _q("Quel mandat exerciez-vous pour cette réunion CSSCT ?", "EMPLOYEE", "Identifier le droit applicable.", "BLOCKING", "CHOICE", "La qualification du temps dépend du rôle.", "Demander la preuve du mandat."),
            _q("Avez-vous pu assister à la réunion malgré le refus ?", "EMPLOYEE", "Connaître la conséquence réelle.", "BLOCKING", "YES_NO", "Un empêchement effectif change le risque d'entrave.", "Préciser retenue, absence ou autre conséquence."),
        ])
        employer.extend([
            _q("Quel texte impose le canal que vous considérez obligatoire ?", "EMPLOYER", "Contrôler le fondement du refus.", "BLOCKING", "DOCUMENT", "Une simple pratique peut être insuffisante.", "Demander accord, note ou règlement."),
            _q("Traitez-vous ce temps comme réunion CSSCT ou crédit d'heures ?", "EMPLOYER", "Empêcher la confusion entre deux régimes.", "BLOCKING", "CHOICE", "Paiement et imputation dépendent de la qualification.", "Faire confirmer le traitement du compteur."),
        ])
        documents.extend([
            _d("Convocation CSSCT", "Établir objet, horaires et qualité du participant.", "Confirmer qu'il s'agit d'une réunion de l'instance.", "BLOCKING"),
            _d("Accord CSE et règle interne de déclaration", "Identifier le régime et le canal applicable.", "Confirmer ou écarter le motif du refus.", "BLOCKING"),
            _d("Compteur et bulletin concernés", "Mesurer la conséquence.", "Établir imputation ou retenue éventuelle.", "HIGH"),
        ])
    else:
        employee.extend([
            _q("Quel fait ou quelle décision voulez-vous contester en priorité ?", "EMPLOYEE", "Identifier l'objet réel du dossier.", "BLOCKING", "FREE_TEXT", "Le domaine et les sources dépendent de la réponse.", "Demander la chronologie et les documents."),
            _q("Quel résultat concret souhaitez-vous obtenir ?", "EMPLOYEE", "Définir l'objectif syndical.", "HIGH", "CHOICE", "La stratégie varie entre contestation et négociation.", "Hiérarchiser une solution principale et une alternative."),
        ])
        employer.append(_q("Quelle décision précise avez-vous prise ou envisagez-vous ?", "EMPLOYER", "Distinguer projet, mesure et sanction.", "BLOCKING", "FREE_TEXT", "La procédure dépend de l'état de la décision.", "Demander sa confirmation écrite."))
        documents.append(_d("Décision ou demande écrite de l'employeur", "Fixer l'objet et la date.", "Confirmer la mesure réellement en cause.", "BLOCKING"))

    checks.extend([
        _q("Les faits admis et contestés sont-ils séparés dans le dossier ?", "DOCUMENT", "Éviter qu'une reconnaissance partielle devienne un aveu global.", "HIGH", "YES_NO", "Une confusion fragilise la défense.", "Corriger la chronologie factuelle."),
        _q("Existe-t-il un précédent interne réellement comparable ?", "DOCUMENT", "Contrôler l'égalité de traitement.", "MEDIUM", "DOCUMENT", "Un écart peut soutenir contestation ou négociation.", "Comparer faits, preuve et sanction."),
    ])
    return employee, employer, documents, checks


def _cap_questions(values: list[ActionableQuestion]) -> list[ActionableQuestion]:
    seen: set[str] = set()
    counts = {"BLOCKING": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    limits = {"BLOCKING": 5, "HIGH": 8, "MEDIUM": 5, "LOW": 5}
    output: list[ActionableQuestion] = []
    for item in values:
        key = normalize(item.question)
        if key in seen or counts[item.priority] >= limits[item.priority]:
            continue
        seen.add(key)
        counts[item.priority] += 1
        output.append(item)
    order = {"BLOCKING": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    return sorted(output, key=lambda item: (order[item.priority], item.question))


def build_actionable_preparation(core: CaseFactualCore) -> dict[str, object]:
    employee, employer, documents, checks = _event_questions(core)
    document_seen: set[str] = set()
    document_rows = []
    for item in documents:
        key = normalize(item.document)
        if key not in document_seen:
            document_seen.add(key)
            document_rows.append(item.to_dict())
    employee = _cap_questions(employee)
    employer = _cap_questions(employer)
    checks = _cap_questions(checks)
    return {
        "questions_for_employee": [item.to_dict() for item in employee],
        "questions_for_employer": [item.to_dict() for item in employer],
        "documents_to_request": document_rows[:8],
        "representative_checks": [item.to_dict() for item in checks],
        "limits": {
            "blocking_questions_max": 5,
            "high_priority_questions_max": 8,
            "complementary_questions_max": 5,
        },
    }


def build_provisional_union_position(core: CaseFactualCore) -> dict[str, str]:
    admitted = core.facts_admitted[0] if core.facts_admitted else ""
    strong = (
        "Le dossier comporte une ambiguïté bloquante qui interdit une conclusion prématurée."
        if core.blocking_ambiguities
        else "La défense peut s'appuyer sur les faits encore non établis, les preuves à contrôler et les responsabilités organisationnelles à vérifier."
    )
    weak = (
        "Un élément défavorable est reconnu : " + admitted
        if admitted
        else "La position exacte du salarié et les éléments défavorables doivent encore être recueillis."
    )
    return {
        "employee_strength": strong,
        "employee_weakness": weak,
        "point_to_challenge": (
            "Contester toute qualification qui dépasse le grief, la preuve ou les faits réellement établis."
        ),
        "point_to_negotiate": (
            "Négocier une mesure proportionnée ou une solution pratique compatible avec l'objectif du salarié, sans promettre le résultat."
        ),
        "do_not_say": (
            "Ne pas nier un fait reconnu, ne pas présenter une allégation comme prouvée et ne pas annoncer que le dossier est gagné."
        ),
    }
