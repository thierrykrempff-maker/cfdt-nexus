"""Deterministic source qualification and source-to-facts comparison.

The engine consumes only the factual core and source records already returned by
the existing retrieval pipeline.  It never retrieves, invents or completes a
legal rule.  A comparison can be emitted only when a traceable source contains
an actual excerpt.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import re
from typing import Iterable, Mapping, Sequence
import unicodedata

from .factual_core import CaseFactualCore


class ApplicabilityStatus(str, Enum):
    APPLICABLE = "APPLICABLE"
    POTENTIALLY_APPLICABLE = "POTENTIALLY_APPLICABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    CANNOT_DETERMINE = "CANNOT_DETERMINE"
    SUPERSEDED = "SUPERSEDED"
    LESS_FAVORABLE_THAN_INTERNAL_RULE = "LESS_FAVORABLE_THAN_INTERNAL_RULE"


class LegalNature(str, Enum):
    COMPANY_AGREEMENT = "COMPANY_AGREEMENT"
    COLLECTIVE_AGREEMENT = "COLLECTIVE_AGREEMENT"
    STATUTE = "STATUTE"
    REGULATION = "REGULATION"
    CASE_LAW = "CASE_LAW"
    ADMINISTRATIVE_DECISION = "ADMINISTRATIVE_DECISION"
    OFFICIAL_GUIDANCE = "OFFICIAL_GUIDANCE"
    PREVENTION_GUIDANCE = "PREVENTION_GUIDANCE"
    INTERNAL_POLICY = "INTERNAL_POLICY"
    CSE_MINUTES = "CSE_MINUTES"
    OTHER = "OTHER"


class ProvisionalConclusion(str, Enum):
    SUPPORTS_EMPLOYEE = "SUPPORTS_EMPLOYEE"
    SUPPORTS_EMPLOYER = "SUPPORTS_EMPLOYER"
    MIXED = "MIXED"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"
    NEGOTIATION_LEVER = "NEGOTIATION_LEVER"
    PROCEDURAL_RISK = "PROCEDURAL_RISK"
    EVIDENCE_RISK = "EVIDENCE_RISK"
    PREVENTION_ISSUE = "PREVENTION_ISSUE"


@dataclass(frozen=True, slots=True)
class DocumentSearchQuery:
    axis: str
    query: str
    purpose: str


@dataclass(frozen=True, slots=True)
class ApplicableSource:
    source_id: str
    source_provider: str
    source_title: str
    document_type: str
    legal_nature: LegalNature
    hierarchy_level: int
    publication_date: str | None
    effective_date: str | None
    version_date: str | None
    article_or_clause: str | None
    precise_excerpt: str
    source_location: str | None
    retrieval_status: str
    authenticity_status: str
    applicability_status: ApplicabilityStatus
    relevance_score: int
    factual_similarity_score: int
    employee_argument: str
    employer_counterargument: str
    facts_supporting_application: tuple[str, ...]
    facts_limiting_application: tuple[str, ...]
    missing_facts: tuple[str, ...]
    confidence_level: str
    rejection_reason: str | None
    citation_ready: bool

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["legal_nature"] = self.legal_nature.value
        payload["applicability_status"] = self.applicability_status.value
        return payload


@dataclass(frozen=True, slots=True)
class RuleToFactsAnalysis:
    issue: str
    source_reference: str
    rule_summary: str
    legal_conditions: tuple[str, ...]
    facts_matching: tuple[str, ...]
    facts_not_matching: tuple[str, ...]
    facts_disputed: tuple[str, ...]
    facts_missing: tuple[str, ...]
    employee_interpretation: str
    employer_interpretation: str
    provisional_conclusion: ProvisionalConclusion
    confidence: str
    next_action: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["provisional_conclusion"] = self.provisional_conclusion.value
        return payload


@dataclass(frozen=True, slots=True)
class SourceToFactsReport:
    search_queries: tuple[DocumentSearchQuery, ...]
    applicable_sources: tuple[ApplicableSource, ...]
    rule_to_facts_analysis: tuple[RuleToFactsAnalysis, ...]
    rejected_sources: tuple[tuple[str, str], ...]
    missing_source_requirements: tuple[str, ...]
    adversarial_analysis: tuple[tuple[str, str], ...]
    control_device_hypotheses: tuple[str, ...]
    analysis_suspended: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "search_queries": [asdict(item) for item in self.search_queries],
            "applicable_sources": [
                item.to_dict() for item in self.applicable_sources
            ],
            "rule_to_facts_analysis": [
                item.to_dict() for item in self.rule_to_facts_analysis
            ],
            "rejected_sources": [
                {"source_reference": reference, "reason": reason}
                for reference, reason in self.rejected_sources
            ],
            "missing_source_requirements": list(self.missing_source_requirements),
            "adversarial_analysis": dict(self.adversarial_analysis),
            "control_device_hypotheses": list(
                self.control_device_hypotheses
            ),
            "analysis_suspended": self.analysis_suspended,
        }


_STOP_WORDS = {
    "avec", "dans", "pour", "sans", "sous", "chez", "entre", "apres", "avant",
    "ainsi", "alors", "comme", "cette", "celui", "celle", "elles", "leurs",
    "des", "les", "une", "sur", "est", "sont", "ete", "etre", "doit", "dont",
    "plus", "moins", "tout", "tous", "fait", "faits", "dossier", "salarie",
    "employeur", "direction", "question", "preciser", "verifier", "mesure",
}
_SENSITIVE = re.compile(
    r"(?:[A-Z]:\\|/(?:tmp|home|Users)/|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|"
    r"\bFR\d{2}[A-Z0-9]{23}\b|\b\d{13,15}\b)",
    re.IGNORECASE,
)
_EVENT_SOURCE_TERMS: dict[str, tuple[str, ...]] = {
    "INSULTING_EMAILS": (
        "courriel", "email", "injure", "insulte", "propos", "discipline",
        "sanction", "reglement interieur", "alcool",
    ),
    "BREAKS_AND_BADGE_CONTROL": (
        "pause", "badge", "badgeage", "tourniquet", "controle acces",
        "controle temps", "finalite", "conservation", "discipline", "sanction",
    ),
    "INSULTING_TAG": (
        "tag", "inscription", "degradation", "injure", "propos", "nettoyage",
        "discipline", "sanction", "reglement interieur", "risque psychosocial",
    ),
    "WORK_SCHEDULE_CHANGE": (
        "horaire", "poste", "cycle", "3x8", "5x8", "travail poste",
        "travail de nuit", "laboratoire", "labo", "delai de prevenance",
    ),
    "PPE_AVAILABILITY_OR_SUITABILITY": (
        "epi", "equipement de protection", "lunettes", "risque chimique",
        "protection individuelle", "securite", "operation dangereuse",
    ),
    "TECHNICAL_ERROR_AND_OUTDATED_PROCEDURE": (
        "procedure", "instruction", "version", "recette", "mise a jour",
        "formation", "accessible", "risque chimique",
    ),
    "POSITIVE_ALCOHOL_TEST": (
        "alcool", "alcoolemie", "ethylotest", "ebriete", "chariot",
        "contre expertise", "controle", "reglement interieur", "securite",
    ),
    "INSULTING_BEHAVIOR": (
        "injure", "insulte", "propos", "fatigue", "repos", "planning",
        "superieur", "hierarchique", "discipline", "sanction",
    ),
}
_EVENT_SEARCH_TERMS: dict[str, tuple[str, str, str, str, str, str]] = {
    "INSULTING_EMAILS": (
        "courriels propos insultants",
        "règlement intérieur procédure disciplinaire",
        "courriels complets destinataires preuve",
        "ancienneté antécédents proportionnalité sanction",
        "alcool contexte travail prévention",
        "mutation sanction cumul mesures",
    ),
    "BREAKS_AND_BADGE_CONTROL": (
        "pauses temps de travail",
        "règlement intérieur pauses procédure disciplinaire",
        "badgeage contrôle accès finalité information consultation CSE",
        "chronologie sanctions proportionnalité pauses",
        "organisation pauses sécurité site Seveso",
        "sanction pauses données badgeage",
    ),
    "INSULTING_TAG": (
        "tag inscription propos installation",
        "règlement intérieur procédure disciplinaire",
        "photographie attribution témoins preuve",
        "nettoyage sanction proportionnalité double sanction",
        "souffrance risques psychosociaux temps de travail",
        "lettre recadrage sanction disciplinaire",
    ),
    "WORK_SCHEDULE_CHANGE": (
        "passage jour travail posté 3x8 5x8 laboratoire",
        "accord temps de travail délai prévenance volontariat",
        "contrat clause horaires cycle de travail",
        "vie personnelle proportionnalité licenciement horaires",
        "fatigue repos travail posté organisation",
        "modification contrat horaires caractère temporaire",
    ),
    "PPE_AVAILABILITY_OR_SUITABILITY": (
        "EPI équipement protection individuelle risque chimique",
        "consigne sécurité fourniture adaptation EPI",
        "stock remise signalement lunettes correctrices",
        "proportionnalité sanction EPI indisponible",
        "analyse risque opération chimique dangereuse",
        "arrêt opération instruction sécurité",
    ),
    "TECHNICAL_ERROR_AND_OUTDATED_PROCEDURE": (
        "procédure recette chimique version obsolète",
        "instruction accessible formation mise à jour",
        "historique informatique version affichée preuve",
        "erreur technique défaillance organisationnelle sanction",
        "risque chimique organisation formation",
        "faute insuffisance procédure applicable",
    ),
    "POSITIVE_ALCOHOL_TEST": (
        "alcoolémie poste à risque chariot",
        "règlement intérieur procédure contrôle alcool",
        "éthylotest taux appareil contre expertise",
        "ancienneté antécédents proportionnalité sanction alcool",
        "sécurité prévention alcool poste dangereux",
        "licenciement contrôle positif alcool",
    ),
    "INSULTING_BEHAVIOR": (
        "propos insultants supérieur hiérarchique",
        "règlement intérieur procédure disciplinaire",
        "témoins propos exacts publicité preuve",
        "ancienneté antécédents proportionnalité sanction injures",
        "fatigue repos planning enchaînement postes",
        "sanction licenciement propos insultants",
    ),
}


def _normalize(value: object) -> str:
    decomposed = unicodedata.normalize("NFKD", str(value or ""))
    return " ".join(
        "".join(char for char in decomposed if not unicodedata.combining(char))
        .casefold()
        .replace("’", " ")
        .replace("'", " ")
        .replace("_", " ")
        .replace("-", " ")
        .split()
    )


def _clean(value: object, *, limit: int = 700) -> str:
    text = " ".join(str(value or "").split())
    if not text or _SENSITIVE.search(text):
        return ""
    return text[:limit]


def _dedupe(values: Iterable[str]) -> tuple[str, ...]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = _clean(value)
        key = _normalize(cleaned)
        if cleaned and key not in seen:
            output.append(cleaned)
            seen.add(key)
    return tuple(output)


def _sequence_texts(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(str(item) for item in value if item)


def _tokens(value: object) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]{3,}", _normalize(value))
        if token not in _STOP_WORDS
        and (len(token) >= 4 or token in {"epi", "cse", "rps", "cnil"})
    }


def _concept_tokens(value: object) -> set[str]:
    concepts: set[str] = set()
    for token in _tokens(value):
        concepts.add(token)
        for suffix in ("ements", "ement", "ations", "ation", "ees", "ee", "es", "er", "e", "s"):
            if token.endswith(suffix) and len(token) - len(suffix) >= 5:
                concepts.add(token[: -len(suffix)])
                break
    return concepts


def _topic_relevant(
    core: CaseFactualCore,
    source_text: str,
    source_title: str,
    nature: LegalNature,
) -> bool:
    terms = _EVENT_SOURCE_TERMS.get(core.event_category)
    if not terms:
        return True
    normalized_title = _normalize(source_title)
    excluded_titles = {
        "INSULTING_EMAILS": ("teletravail", "accord sur la mise en place du cse"),
        "INSULTING_TAG": ("teletravail", "accord sur la mise en place du cse"),
        "WORK_SCHEDULE_CHANGE": (
            "teletravail",
            "compte epargne temps",
            "accord cet",
            "restauration",
            "astreinte",
            "mise en place du cse",
        ),
        "PPE_AVAILABILITY_OR_SUITABILITY": ("teletravail", "astreinte"),
        "TECHNICAL_ERROR_AND_OUTDATED_PROCEDURE": (
            "teletravail",
            "mise en place du cse",
        ),
        "POSITIVE_ALCOHOL_TEST": ("teletravail", "mise en place du cse"),
        "INSULTING_BEHAVIOR": ("teletravail", "mise en place du cse"),
    }
    if any(
        marker in normalized_title
        for marker in excluded_titles.get(core.event_category, ())
    ):
        return False
    normalized_text = _normalize(source_text)
    if core.event_category == "TECHNICAL_ERROR_AND_OUTDATED_PROCEDURE":
        strong_match = (
            "recette" in normalized_text
            or "instruction" in normalized_text
            or (
                "procedure" in normalized_text
                and any(
                    marker in normalized_text
                    for marker in ("version", "obsolete", "mise a jour")
                )
            )
        )
        if not strong_match:
            return False
    if (
        core.event_category == "INSULTING_TAG"
        and nature
        in {
            LegalNature.COMPANY_AGREEMENT,
            LegalNature.INTERNAL_POLICY,
            LegalNature.COLLECTIVE_AGREEMENT,
            LegalNature.CASE_LAW,
        }
        and not any(
            marker in normalized_text
            for marker in (
                "tag",
                "inscription",
                "degradation materielle",
                "injure",
                "propos",
            )
        )
    ):
        return False
    source_concepts = _concept_tokens(source_text)
    return any(
        bool(source_concepts & _concept_tokens(term))
        for term in terms
    )


def _facts(core: CaseFactualCore) -> tuple[str, ...]:
    return _dedupe(
        (
            core.primary_grievance_or_decision,
            *core.facts_certain,
            *core.facts_admitted,
            *core.facts_disputed,
            *core.facts_alleged,
            *core.health_and_safety_context,
            *core.working_time_context,
            *core.secondary_topics,
            *core.evidence_mentioned,
            core.contract_change_considered,
            core.sanction_or_measure_considered,
        )
    )


def build_source_search_queries(
    core: CaseFactualCore,
) -> tuple[DocumentSearchQuery, ...]:
    """Build six bounded queries from structured facts, never from the raw case."""

    targeted = _EVENT_SEARCH_TERMS.get(core.event_category)
    main = _clean(core.primary_grievance_or_decision, limit=180)
    evidence = " ; ".join(_dedupe(core.evidence_mentioned)[:2])
    health = " ; ".join(
        _dedupe(
            (
                *core.health_and_safety_context,
                *core.working_time_context,
                *core.secondary_topics,
            )
        )[:3]
    )
    consequence = _clean(
        core.contract_change_considered
        if core.contract_change_considered != "Non identifié"
        else core.sanction_or_measure_considered,
        limit=140,
    )
    generic_rows = (
        ("A_MAIN_ACT", main, "Identifier la règle liée à l'acte ou à la décision principale."),
        (
            "B_PROCEDURE",
            " ".join(item for item in (main, consequence, "procédure applicable") if item),
            "Identifier la procédure et ses garanties.",
        ),
        (
            "C_EVIDENCE_OR_CONTROL",
            " ".join(item for item in (main, evidence, "preuve dispositif contrôle") if item),
            "Contrôler la preuve ou le dispositif mobilisé.",
        ),
        (
            "D_PROPORTIONALITY",
            " ".join(item for item in (main, consequence, "proportionnalité") if item),
            "Comparer le grief, le contexte et la mesure envisagée.",
        ),
        (
            "E_HEALTH_SAFETY_ORGANISATION",
            " ".join(item for item in (main, health, "prévention organisation") if item),
            "Identifier le contexte de santé, sécurité ou organisation.",
        ),
        (
            "F_CONTRACT_OR_DISCIPLINE",
            " ".join(item for item in (main, consequence, "contrat discipline") if item),
            "Qualifier la conséquence contractuelle ou disciplinaire.",
        ),
    )
    if targeted:
        rows = tuple(
            (axis, targeted[index], purpose)
            for index, (axis, _query, purpose) in enumerate(generic_rows)
        )
    else:
        rows = generic_rows
    return tuple(
        DocumentSearchQuery(axis, query[:320], purpose)
        for axis, query, purpose in rows
        if query
    )


def _provider(source: Mapping[str, object]) -> str:
    origin = _normalize(source.get("origin"))
    explicit = _clean(
        source.get("source_officielle")
        or source.get("official_origin")
        or source.get("provider")
    )
    if explicit:
        return explicit
    providers = {
        "bible accords": "INEOS Sarralbe",
        "nexus bible bridge": "INEOS Sarralbe",
        "legifrance code travail": "Légifrance",
        "judilibre jurisprudence": "Cour de cassation - JUDILIBRE",
        "cdtn pratique officielle": "Code du travail numérique",
        "cnil": "CNIL",
        "carsat": "CARSAT",
        "inrs": "INRS",
        "anact": "ANACT",
    }
    return providers.get(origin, _clean(source.get("origin")) or "Source non identifiée")


def _legal_nature(source: Mapping[str, object]) -> LegalNature:
    layer = _normalize(source.get("source_layer"))
    provider = _normalize(_provider(source))
    document = _normalize(
        " ".join(
            str(source.get(key) or "")
            for key in ("document", "title", "document_type", "content_type")
        )
    )
    if layer == "accord entreprise":
        return (
            LegalNature.INTERNAL_POLICY
            if any(item in document for item in ("reglement interieur", "procedure", "note"))
            else LegalNature.COMPANY_AGREEMENT
        )
    if layer == "convention collective":
        return LegalNature.COLLECTIVE_AGREEMENT
    if layer == "code travail":
        return (
            LegalNature.REGULATION
            if any(item in document for item in ("decret", "arrete", "reglement"))
            else LegalNature.STATUTE
        )
    if layer in {"jurisprudence", "prudhommes"}:
        return LegalNature.CASE_LAW
    if layer == "historique cse":
        return LegalNature.CSE_MINUTES
    if any(item in provider for item in ("carsat", "inrs")):
        return LegalNature.PREVENTION_GUIDANCE
    if "cnil" in provider and any(
        item in document for item in ("decision", "sanction", "deliberation")
    ):
        return LegalNature.ADMINISTRATIVE_DECISION
    if any(item in provider for item in ("cnil", "anact", "code du travail numerique")):
        return LegalNature.OFFICIAL_GUIDANCE
    return LegalNature.OTHER


def _hierarchy(nature: LegalNature) -> int:
    return {
        LegalNature.COMPANY_AGREEMENT: 1,
        LegalNature.INTERNAL_POLICY: 1,
        LegalNature.COLLECTIVE_AGREEMENT: 2,
        LegalNature.STATUTE: 3,
        LegalNature.REGULATION: 3,
        LegalNature.CASE_LAW: 4,
        LegalNature.ADMINISTRATIVE_DECISION: 5,
        LegalNature.OFFICIAL_GUIDANCE: 5,
        LegalNature.PREVENTION_GUIDANCE: 5,
        LegalNature.CSE_MINUTES: 6,
        LegalNature.OTHER: 7,
    }[nature]


def _title(source: Mapping[str, object]) -> str:
    return _clean(source.get("document") or source.get("title"), limit=260)


def _excerpt(source: Mapping[str, object]) -> str:
    return _clean(
        source.get("precise_excerpt")
        or source.get("excerpt")
        or source.get("principle_summary")
        or source.get("summary")
        or source.get("resume_court"),
        limit=700,
    )


def _location(source: Mapping[str, object]) -> str | None:
    value = _clean(
        source.get("article")
        or source.get("article_or_section")
        or source.get("location")
        or source.get("url_or_id")
        or source.get("url")
        or source.get("official_id")
        or source.get("legifrance_id")
        or source.get("judilibre_id"),
        limit=300,
    )
    return value or None


def _source_id(source: Mapping[str, object], title: str, excerpt: str) -> str:
    explicit = _clean(
        source.get("official_id")
        or source.get("legifrance_id")
        or source.get("judilibre_id"),
        limit=160,
    )
    if explicit:
        return explicit
    digest = hashlib.sha256(
        "\x1f".join((_provider(source), title, _location(source) or "", excerpt)).encode(
            "utf-8"
        )
    ).hexdigest()[:20]
    return f"source-{digest}"


def _fact_matches(core: CaseFactualCore, source_text: str) -> tuple[str, ...]:
    source_tokens = _concept_tokens(source_text)
    return _dedupe(
        fact
        for fact in _facts(core)
        if len(_concept_tokens(fact) & source_tokens) >= 1
    )[:5]


def _factual_similarity(
    source: Mapping[str, object],
    core: CaseFactualCore,
    matches: tuple[str, ...],
) -> int:
    if _legal_nature(source) is not LegalNature.CASE_LAW:
        return min(100, len(matches) * 22)
    criteria = {
        "acte": bool(matches),
        "statut": bool(
            _tokens(" ".join(core.persons_and_roles))
            & _tokens(source.get("faits_utiles") or source.get("excerpt"))
        ),
        "contexte": bool(
            _tokens(" ".join(core.workplace_context + core.health_and_safety_context))
            & _tokens(source.get("faits_utiles") or source.get("excerpt"))
        ),
        "reconnaissance": bool(core.facts_admitted or core.facts_disputed),
        "anciennete": "anciennete" in _normalize(source.get("faits_utiles")),
        "antecedents": "antecedent" in _normalize(source.get("faits_utiles")),
        "sanction": bool(
            _tokens(core.sanction_or_measure_considered)
            & _tokens(source.get("solution_retenue") or source.get("summary"))
        ),
        "employeur": bool(source.get("difference_avec_dossier") or source.get("selection_limits")),
    }
    supplied = source.get("ressemblance_avec_dossier")
    if isinstance(supplied, Sequence) and not isinstance(supplied, (str, bytes)):
        for index, _item in enumerate(supplied[:8]):
            criteria[f"connector_{index}"] = True
    return min(100, sum(criteria.values()) * 13)


def _relevance(
    source: Mapping[str, object],
    core: CaseFactualCore,
    title: str,
    excerpt: str,
    matches: tuple[str, ...],
) -> int:
    fact_tokens = _concept_tokens(" ".join(_facts(core)))
    source_tokens = _concept_tokens(
        " ".join((title, excerpt, str(source.get("_context") or "")))
    )
    overlap = len(fact_tokens & source_tokens)
    score = min(75, overlap * 9) + min(24, len(matches) * 12)
    try:
        router_score = float(source.get("_router_score") or source.get("score") or 0)
    except (TypeError, ValueError):
        router_score = 0
    return min(100, int(round(score + min(5, max(0, router_score) / 20))))


def _case_law_traceable(source: Mapping[str, object]) -> bool:
    return bool(
        _clean(source.get("juridiction"))
        and _clean(source.get("decision_date"))
        and _clean(source.get("case_number") or source.get("judilibre_id"))
    )


def _conditions(excerpt: str) -> tuple[str, ...]:
    segments = re.split(r"(?<=[.;:])\s+|\n+", excerpt)
    meaningful = [
        segment.strip(" -")
        for segment in segments
        if len(segment.strip()) >= 24
    ]
    return _dedupe(meaningful[:3])


def _applicability(
    source: Mapping[str, object],
    nature: LegalNature,
    relevance: int,
    similarity: int,
) -> ApplicabilityStatus:
    if source.get("less_favorable_than_internal_rule") is True:
        return ApplicabilityStatus.LESS_FAVORABLE_THAN_INTERNAL_RULE
    state = _normalize(source.get("etat") or source.get("status"))
    if any(item in state for item in ("abroge", "superseded", "remplace")):
        return ApplicabilityStatus.SUPERSEDED
    if relevance < 20:
        return ApplicabilityStatus.NOT_APPLICABLE
    if nature is LegalNature.CASE_LAW and similarity < 39:
        return ApplicabilityStatus.NOT_APPLICABLE
    if source.get("is_in_force") is True and relevance >= 55:
        return ApplicabilityStatus.APPLICABLE
    return ApplicabilityStatus.POTENTIALLY_APPLICABLE


def _rejection_reason(
    *,
    source: Mapping[str, object],
    title: str,
    excerpt: str,
    relevance: int,
    similarity: int,
    nature: LegalNature,
    topic_relevant: bool,
) -> str | None:
    raw_excerpt = " ".join(
        str(source.get(key) or "")
        for key in (
            "precise_excerpt",
            "excerpt",
            "principle_summary",
            "summary",
            "resume_court",
        )
    )
    if not title:
        return "titre de source absent"
    if _SENSITIVE.search(raw_excerpt):
        return "extrait écarté par le contrôle de confidentialité"
    if not excerpt:
        return "extrait précis indisponible"
    if not topic_relevant:
        return "source générique ou hors sujet pour le fait principal"
    if nature is LegalNature.CASE_LAW:
        if not _case_law_traceable(source):
            return "décision non traçable : juridiction, date ou numéro absent"
        if similarity < 39:
            return "moins de trois critères de comparaison factuelle établis"
    if relevance < 20:
        return "lien factuel insuffisant avec le dossier"
    return None


def _arguments(
    title: str,
    matches: tuple[str, ...],
    limiting: tuple[str, ...],
) -> tuple[str, str]:
    employee = (
        f"Le salarié peut demander l'application vérifiée de « {title} » au fait suivant : "
        f"{matches[0]}"
        if matches
        else f"Le salarié ne peut invoquer « {title} » sans fait d'application établi."
    )
    employer = (
        f"La direction peut opposer que l'application de « {title} » reste limitée "
        f"par : {limiting[0]}"
        if limiting
        else f"La direction peut demander de vérifier le champ et la version de « {title} »."
    )
    return employee, employer


def _source(
    source: Mapping[str, object],
    core: CaseFactualCore,
) -> ApplicableSource:
    title = _title(source)
    excerpt = _excerpt(source)
    nature = _legal_nature(source)
    context = " ".join((title, excerpt, _clean(source.get("_context"))))
    topic_relevant = _topic_relevant(core, context, title, nature)
    matches = _fact_matches(core, context)
    limiting = _dedupe(
        (
            *core.facts_disputed,
            *core.facts_alleged,
            *_sequence_texts(source.get("selection_limits")),
            *_sequence_texts(source.get("difference_avec_dossier")),
        )
    )[:5]
    similarity = _factual_similarity(source, core, matches)
    relevance = _relevance(source, core, title, excerpt, matches)
    rejection = _rejection_reason(
        source=source,
        title=title,
        excerpt=excerpt,
        relevance=relevance,
        similarity=similarity,
        nature=nature,
        topic_relevant=topic_relevant,
    )
    applicability = (
        ApplicabilityStatus.NOT_APPLICABLE
        if rejection
        else _applicability(source, nature, relevance, similarity)
    )
    employee, employer = _arguments(title or "source sans titre", matches, limiting)
    location = _location(source)
    authentic = bool(
        source.get("official_id")
        or source.get("legifrance_id")
        or source.get("judilibre_id")
        or location
    )
    citation_ready = bool(
        not rejection
        and title
        and excerpt
        and location
        and authentic
        and applicability
        not in {ApplicabilityStatus.NOT_APPLICABLE, ApplicabilityStatus.SUPERSEDED}
    )
    return ApplicableSource(
        source_id=_source_id(source, title, excerpt),
        source_provider=_provider(source),
        source_title=title or "Source sans titre",
        document_type=_clean(source.get("document_type") or source.get("content_type"))
        or nature.value,
        legal_nature=nature,
        hierarchy_level=_hierarchy(nature),
        publication_date=_clean(source.get("publication_date")) or None,
        effective_date=_clean(source.get("date_debut")) or None,
        version_date=_clean(
            source.get("version_start_date")
            or source.get("version")
            or source.get("updated_at")
        )
        or None,
        article_or_clause=_clean(
            source.get("article") or source.get("article_or_section")
        )
        or None,
        precise_excerpt=excerpt,
        source_location=location,
        retrieval_status="RETRIEVED" if excerpt else "INCOMPLETE",
        authenticity_status="TRACEABLE_REFERENCE" if authentic else "UNVERIFIED",
        applicability_status=applicability,
        relevance_score=relevance,
        factual_similarity_score=similarity,
        employee_argument=employee,
        employer_counterargument=employer,
        facts_supporting_application=matches,
        facts_limiting_application=limiting,
        missing_facts=_dedupe(core.facts_missing)[:5],
        confidence_level=(
            "HIGH"
            if citation_ready and relevance >= 70
            else "MEDIUM"
            if citation_ready
            else "LOW"
        ),
        rejection_reason=rejection,
        citation_ready=citation_ready,
    )


def _conclusion(source: ApplicableSource) -> ProvisionalConclusion:
    if source.legal_nature is LegalNature.PREVENTION_GUIDANCE:
        return ProvisionalConclusion.PREVENTION_ISSUE
    if source.missing_facts:
        return ProvisionalConclusion.INSUFFICIENT_INFORMATION
    if source.facts_supporting_application and source.facts_limiting_application:
        return ProvisionalConclusion.MIXED
    if source.legal_nature is LegalNature.CASE_LAW:
        return ProvisionalConclusion.EVIDENCE_RISK
    return ProvisionalConclusion.NEGOTIATION_LEVER


def _analysis(source: ApplicableSource, core: CaseFactualCore) -> RuleToFactsAnalysis:
    conditions = _conditions(source.precise_excerpt)
    missing = source.missing_facts or (
        "Version, champ d'application et document local à confirmer.",
    )
    difference = (
        source.facts_limiting_application
        if source.facts_limiting_application
        else ("Aucun écart démontré ; le champ d'application reste à vérifier.",)
    )
    next_action = (
        f"Obtenir ou vérifier {source.article_or_clause or source.source_location} "
        f"dans « {source.source_title} »."
    )
    if source.legal_nature is LegalNature.CASE_LAW:
        next_action = (
            "Cette décision fournit un élément de comparaison, mais ne garantit "
            "pas la même issue, notamment parce que les actes, statuts, contextes, "
            "antécédents, procédures ou sanctions peuvent différer."
        )
    return RuleToFactsAnalysis(
        issue=core.primary_grievance_or_decision,
        source_reference=(
            f"{source.source_provider} — {source.source_title}"
            + (
                f" — {source.article_or_clause}"
                if source.article_or_clause
                else ""
            )
        ),
        rule_summary=source.precise_excerpt,
        legal_conditions=conditions,
        facts_matching=source.facts_supporting_application,
        facts_not_matching=difference,
        facts_disputed=_dedupe(core.facts_disputed),
        facts_missing=missing,
        employee_interpretation=source.employee_argument,
        employer_interpretation=source.employer_counterargument,
        provisional_conclusion=_conclusion(source),
        confidence=source.confidence_level,
        next_action=next_action,
    )


def _missing_requirements(
    core: CaseFactualCore,
    available: tuple[ApplicableSource, ...],
) -> tuple[str, ...]:
    present = {item.legal_nature for item in available if item.citation_ready}
    providers = {
        _normalize(item.source_provider)
        for item in available
        if item.citation_ready
    }
    required = [
        (LegalNature.COMPANY_AGREEMENT, "Accord INEOS ou règle interne exacte, version et clause applicables."),
        (LegalNature.COLLECTIVE_AGREEMENT, "CCNIC IDCC 44 : article, avenant ou chapitre pertinent."),
        (LegalNature.STATUTE, "Code du travail : article précis en vigueur."),
    ]
    if core.event_category in {
        "INSULTING_EMAILS",
        "INSULTING_BEHAVIOR",
        "POSITIVE_ALCOHOL_TEST",
        "WORK_SCHEDULE_CHANGE",
    }:
        required.append(
            (
                LegalNature.CASE_LAW,
                "Jurisprudence traçable et comparable sur plusieurs critères factuels.",
            )
        )
    if core.event_category == "BREAKS_AND_BADGE_CONTROL" and not any(
        "cnil" in provider for provider in providers
    ):
        required.append(
            (
                LegalNature.OFFICIAL_GUIDANCE,
                "CNIL : ressource réelle sur finalité, information, conservation "
                "et usage secondaire du dispositif de contrôle.",
            )
        )
    if core.event_category == "PPE_AVAILABILITY_OR_SUITABILITY" and not any(
        provider in {"carsat", "inrs"} for provider in providers
    ):
        required.append(
            (
                LegalNature.PREVENTION_GUIDANCE,
                "CARSAT ou INRS : ressource réelle sur fourniture, adaptation et "
                "disponibilité des EPI.",
            )
        )
    if core.event_category == "TECHNICAL_ERROR_AND_OUTDATED_PROCEDURE":
        required.append(
            (
                LegalNature.INTERNAL_POLICY,
                "Procédure ou instruction chimique réellement accessible à la "
                "date des faits, avec son numéro et sa version.",
            )
        )
    if core.event_category == "INSULTING_BEHAVIOR" and not any(
        provider in {"anact", "inrs", "carsat"} for provider in providers
    ):
        required.append(
            (
                LegalNature.PREVENTION_GUIDANCE,
                "ANACT, INRS ou CARSAT : ressource réelle sur fatigue, repos ou "
                "organisation du travail.",
            )
        )
    return _dedupe(label for nature, label in required if nature not in present)


def analyze_source_to_facts(
    core: CaseFactualCore,
    sources: Sequence[Mapping[str, object]],
) -> SourceToFactsReport:
    queries = build_source_search_queries(core)
    if core.blocking_ambiguities:
        return SourceToFactsReport(
            queries,
            (),
            (),
            (),
            _dedupe(
                (
                    *core.blocking_ambiguities,
                    "La comparaison juridique commencera après clarification des faits.",
                )
            ),
            (
                ("best_employee_argument", "Aucune conclusion avant clarification."),
                ("best_employer_argument", "Aucune conclusion avant clarification."),
                ("determinative_evidence", core.blocking_ambiguities[0]),
                ("determinative_procedure", "Suspendre l'analyse de fond."),
                ("main_employee_risk", "Répondre sur une règle ou un fait mal identifié."),
                ("main_negotiation_lever", "Obtenir d'abord les pièces et précisions manquantes."),
            ),
            (),
            True,
        )

    qualified = tuple(_source(source, core) for source in sources)
    accepted = tuple(
        sorted(
            (item for item in qualified if not item.rejection_reason),
            key=lambda item: (
                item.hierarchy_level,
                -item.relevance_score,
                item.source_title.casefold(),
            ),
        )
    )
    rejected = tuple(
        (item.source_title, item.rejection_reason or "source non retenue")
        for item in qualified
        if item.rejection_reason
    )
    analyses = tuple(
        _analysis(item, core) for item in accepted if item.citation_ready
    )
    missing = _missing_requirements(core, accepted)
    best_employee = (
        analyses[0].employee_interpretation
        if analyses
        else "Aucune source traçable ne permet encore de soutenir un argument juridique."
    )
    best_employer = (
        analyses[0].employer_interpretation
        if analyses
        else "La direction peut demander que la règle et son champ soient d'abord établis."
    )
    control_hypotheses = (
        (
            "Usage prévu par la finalité initiale et correctement déclaré.",
            "Usage secondaire dont la compatibilité, l'information ou la consultation "
            "doivent être démontrées.",
            "Informations insuffisantes pour conclure sur la licéité ou la preuve.",
        )
        if core.event_category == "BREAKS_AND_BADGE_CONTROL"
        else ()
    )
    return SourceToFactsReport(
        queries,
        accepted,
        analyses,
        rejected,
        missing,
        (
            ("best_employee_argument", best_employee),
            ("best_employer_argument", best_employer),
            (
                "determinative_evidence",
                core.evidence_mentioned[0]
                if core.evidence_mentioned
                else "La pièce exacte invoquée par la direction.",
            ),
            (
                "determinative_procedure",
                "Vérifier chronologie, information, consultation et garanties applicables.",
            ),
            (
                "main_employee_risk",
                "Un fait reconnu ou une preuve régulière peut limiter la contestation.",
            ),
            (
                "main_negotiation_lever",
                "Utiliser les faits non établis, les écarts de procédure et les mesures alternatives.",
            ),
        ),
        control_hypotheses,
        False,
    )
