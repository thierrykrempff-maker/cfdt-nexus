"""Fact extraction for realistic disciplinary assistance."""

from __future__ import annotations

import re
import unicodedata

from .disciplinary_models import (
    DisciplinaryActCategory,
    DisciplinaryFactExtraction,
)
from .models import SyndicalCaseInput


ACT_CATEGORY_MARKERS: tuple[tuple[DisciplinaryActCategory, tuple[str, ...]], ...] = (
    (
        DisciplinaryActCategory.THREAT_OR_VIOLENCE,
        ("menace", "menace de", "violence", "agression", "frappe", "coup"),
    ),
    (
        DisciplinaryActCategory.ALLEGED_HARASSMENT,
        ("harcelement", "harceler", "agissements repetes"),
    ),
    (
        DisciplinaryActCategory.ALCOHOL_OR_DRUGS,
        ("alcool", "alcoolise", "ivresse", "stupefiant", "drogue", "cannabis"),
    ),
    (
        DisciplinaryActCategory.INSULTING_OR_INAPPROPRIATE_BEHAVIOR,
        (
            "fils de pute",
            "injure",
            "injurieux",
            "insulte",
            "propos grossier",
            "propos irrespectueux",
            "comportement injurieux",
            "comportement irrespectueux",
            "tag",
            "tag grossier",
            "tag injurieux",
            "inscription",
            "inscription grossiere",
            "inscription injurieuse",
            "graffiti",
        ),
    ),
    (
        DisciplinaryActCategory.MATERIAL_DAMAGE,
        (
            "degradation materielle",
            "materiel degrade",
            "equipement endommage",
            "dommage materiel",
            "casse volontairement",
            "deterioration",
        ),
    ),
    (
        DisciplinaryActCategory.SAFETY_BREACH,
        (
            "manquement a la securite",
            "regle de securite",
            "consigne de securite",
            "mise en danger",
            "incident de securite",
            "equipement de securite",
        ),
    ),
    (
        DisciplinaryActCategory.TECHNICAL_ERROR,
        (
            "erreur de manipulation",
            "erreur technique",
            "mauvaise manipulation",
            "mauvais reglage",
            "defaut de procedure technique",
            "incident technique",
        ),
    ),
    (
        DisciplinaryActCategory.INSUBORDINATION,
        (
            "insubordination",
            "refus d ordre",
            "refus d executer",
            "refus de consigne",
            "ordre refuse",
        ),
    ),
    (
        DisciplinaryActCategory.ABSENCE_OR_LATENESS,
        (
            "absence injustifiee",
            "retard",
            "retards",
            "abandon de poste",
            "ne s est pas presente",
        ),
    ),
    (
        DisciplinaryActCategory.IT_MISUSE,
        (
            "usage abusif des outils informatiques",
            "outil informatique",
            "messagerie professionnelle",
            "internet au travail",
            "ordinateur de l entreprise",
            "donnees informatiques",
        ),
    ),
    (
        DisciplinaryActCategory.INTERPERSONAL_CONFLICT,
        (
            "conflit interpersonnel",
            "conflit avec un collegue",
            "altercation verbale",
            "mesentente",
        ),
    ),
)


def case_text(case_or_text: SyndicalCaseInput | str) -> str:
    if isinstance(case_or_text, SyndicalCaseInput):
        return " ".join(
            [case_or_text.question]
            + [item.statement for item in case_or_text.declared_facts]
            + [item.statement for item in case_or_text.established_facts]
        )
    return str(case_or_text)


def normalize_disciplinary_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return " ".join(
        "".join(char for char in normalized if not unicodedata.combining(char))
        .lower()
        .replace("’", " ")
        .replace("'", " ")
        .split()
    )


def extract_disciplinary_facts(
    case_or_text: SyndicalCaseInput | str,
) -> DisciplinaryFactExtraction:
    raw = case_text(case_or_text)
    text = normalize_disciplinary_text(raw)
    category = _act_category(text)
    exact_behavior = _exact_words_or_behavior(raw, text, category)
    target_identified = _target_identified(text)
    target_type = _target_type(text, target_identified)
    location = _location(text)
    public_visibility = _tri_state(
        text,
        positive=("visible par", "visible de", "en public", "diffuse", "affiche"),
        negative=("non visible", "pas visible", "espace prive", "message prive"),
    )
    material_damage = _tri_state(
        text,
        positive=(
            "degradation",
            "deterioration",
            "endommage",
            "dommage materiel",
            "cout de remise en etat",
        ),
        negative=(
            "aucune degradation",
            "sans degradation",
            "seulement necessite un nettoyage",
            "effacable",
            "nettoye rapidement",
        ),
    )
    threat_or_violence = _tri_state(
        text,
        positive=("menace", "violence", "agression", "frappe", "coup"),
        negative=("aucune menace", "sans menace", "aucune violence", "sans violence"),
    )
    repetition = _tri_state(
        text,
        positive=("repete", "plusieurs fois", "recidive", "faits similaires"),
        negative=(
            "fait isole",
            "geste isole",
            "propos isole",
            "propos grossier isole",
            "premiere fois",
            "incident unique",
        ),
    )
    employee_admission = _tri_state(
        text,
        positive=(
            "reconnait etre l auteur",
            "reconnait les faits",
            "reconnait l inscription",
            "reconnait avoir ecrit",
            "reconnait avoir inscrit",
            "apres avoir ecrit",
            "a ecrit la phrase",
            "admet les faits",
            "admet etre l auteur",
            "a avoue",
        ),
        negative=(
            "conteste etre l auteur",
            "nie etre l auteur",
            "ne reconnait pas les faits",
            "conteste les faits",
        ),
    )
    prior_warnings = _tri_state(
        text,
        positive=("avertissement anterieur", "antecedent disciplinaire", "deja sanctionne"),
        negative=("aucun antecedent", "sans antecedent", "jamais sanctionne"),
    )
    evidence = tuple(
        label
        for label, markers in (
            ("photographie", ("photo", "photographie")),
            ("vidéo", ("video",)),
            ("témoignage", ("temoin", "temoignage")),
            ("aveu", ("aveu", "a avoue")),
            ("trace écrite", ("courriel", "message")),
        )
        if _positive_evidence_marker(text, markers)
    )
    context = tuple(
        label
        for label, markers in (
            ("journée difficile", ("journee difficile",)),
            ("ambiance de travail dégradée", ("ambiance degradee", "climat degrade")),
            ("énervement", ("enervement", "sous le coup de la colere")),
            ("conflit de travail", ("conflit", "altercation", "tension")),
            ("charge ou fatigue alléguée", ("surcharge", "charge de travail", "fatigue")),
        )
        if any(marker in text for marker in markers)
    )
    sanction = _sanction(text)
    missing = _facts_missing(
        exact_behavior=exact_behavior,
        target_identified=target_identified,
        location=location,
        public_visibility=public_visibility,
        material_damage=material_damage,
        repetition=repetition,
        employee_admission=employee_admission,
        evidence=evidence,
        prior_warnings=prior_warnings,
        sanction=sanction,
    )
    return DisciplinaryFactExtraction(
        alleged_act=_alleged_act(category, exact_behavior),
        act_category=category,
        exact_words_or_behavior=exact_behavior,
        target_identified=target_identified,
        target_type=target_type,
        location=location,
        public_visibility=public_visibility,
        material_damage=material_damage,
        threat_or_violence=threat_or_violence,
        repetition=repetition,
        employee_admission=employee_admission,
        employer_evidence=evidence,
        context_claimed=context,
        prior_warnings=prior_warnings,
        sanction_considered=sanction,
        facts_missing=missing,
    )


def _act_category(text: str) -> DisciplinaryActCategory:
    for category, markers in ACT_CATEGORY_MARKERS:
        if any(marker in text for marker in markers):
            return category
    return DisciplinaryActCategory.UNSPECIFIED_FACTS


def _exact_words_or_behavior(
    raw: str,
    text: str,
    category: DisciplinaryActCategory,
) -> str | None:
    quoted = re.search(r"[«\"]\s*([^»\"]{2,180}?)\s*[»\"]", raw)
    if quoted:
        return quoted.group(1).strip()
    if "fils de pute" in text:
        return "fils de pute"
    labels = {
        DisciplinaryActCategory.TECHNICAL_ERROR: "erreur de manipulation technique",
        DisciplinaryActCategory.INSUBORDINATION: "refus d'exécuter une instruction",
        DisciplinaryActCategory.ABSENCE_OR_LATENESS: "absence ou retard",
        DisciplinaryActCategory.THREAT_OR_VIOLENCE: "menace ou violence alléguée",
        DisciplinaryActCategory.ALLEGED_HARASSMENT: "harcèlement allégué",
        DisciplinaryActCategory.MATERIAL_DAMAGE: "dégradation matérielle alléguée",
        DisciplinaryActCategory.SAFETY_BREACH: "manquement à la sécurité allégué",
        DisciplinaryActCategory.IT_MISUSE: "usage informatique abusif allégué",
        DisciplinaryActCategory.ALCOHOL_OR_DRUGS: "fait lié à l'alcool ou aux stupéfiants",
        DisciplinaryActCategory.INTERPERSONAL_CONFLICT: "conflit interpersonnel",
    }
    if category == DisciplinaryActCategory.INSULTING_OR_INAPPROPRIATE_BEHAVIOR:
        return "inscription ou propos grossier"
    return labels.get(category)


def _target_identified(text: str) -> bool | None:
    if any(
        marker in text
        for marker in (
            "ne visait personne",
            "personne en particulier",
            "aucune personne visee",
            "non adresse a une personne",
        )
    ):
        return False
    if any(
        marker in text
        for marker in (
            "visant clairement",
            "vise son superieur",
            "contre son superieur",
            "contre un collegue",
            "adresse a son",
            "insulte son",
        )
    ):
        return True
    return None


def _target_type(text: str, identified: bool | None) -> str | None:
    if identified is False:
        return "aucune personne précisément identifiée"
    if any(marker in text for marker in ("superieur", "manager", "chef", "responsable")):
        return "supérieur hiérarchique"
    if "collegue" in text:
        return "collègue"
    if any(marker in text for marker in ("employeur", "direction")):
        return "employeur ou direction"
    if "public" in text:
        return "public"
    return None


def _location(text: str) -> str | None:
    for label, markers in (
        ("installation de l'entreprise", ("installation de l entreprise",)),
        ("équipement de l'entreprise", ("equipement de l entreprise", "sur un equipement")),
        ("mur ou surface de l'entreprise", ("sur un mur", "graffiti sur")),
        ("vestiaire", ("vestiaire",)),
        ("poste de travail", ("poste de travail",)),
    ):
        if any(marker in text for marker in markers):
            return label
    return None


def _sanction(text: str) -> str | None:
    for label, markers in (
        ("licenciement", ("licenciement",)),
        ("mise à pied disciplinaire", ("mise a pied disciplinaire",)),
        ("avertissement", ("avertissement",)),
        ("blâme", ("blame",)),
        ("sanction non précisée", ("sanction envisagee", "sanction disciplinaire")),
    ):
        if any(marker in text for marker in markers):
            return label
    return None


def _tri_state(
    text: str,
    *,
    positive: tuple[str, ...],
    negative: tuple[str, ...],
) -> bool | None:
    if any(marker in text for marker in negative):
        return False
    if any(marker in text for marker in positive):
        return True
    return None


def _positive_evidence_marker(text: str, markers: tuple[str, ...]) -> bool:
    if not any(marker in text for marker in markers):
        return False
    return not any(
        negative in text
        for marker in markers
        for negative in (
            "aucun " + marker,
            "aucune " + marker,
            "sans " + marker,
            "pas de " + marker,
        )
    )


def _alleged_act(
    category: DisciplinaryActCategory,
    exact_behavior: str | None,
) -> str:
    if category == DisciplinaryActCategory.INSULTING_OR_INAPPROPRIATE_BEHAVIOR:
        detail = f' contenant « {exact_behavior} »' if exact_behavior else ""
        return "inscription ou comportement grossier allégué" + detail
    if exact_behavior:
        return exact_behavior
    return "faits disciplinaires insuffisamment précisés"


def _facts_missing(
    *,
    exact_behavior: str | None,
    target_identified: bool | None,
    location: str | None,
    public_visibility: bool | None,
    material_damage: bool | None,
    repetition: bool | None,
    employee_admission: bool | None,
    evidence: tuple[str, ...],
    prior_warnings: bool | None,
    sanction: str | None,
) -> tuple[str, ...]:
    values = (
        ("formulation ou comportement exact", exact_behavior),
        ("personne éventuellement visée", target_identified),
        ("lieu précis", location),
        ("visibilité de l'acte", public_visibility),
        ("conséquence matérielle", material_damage),
        ("caractère isolé ou répété", repetition),
        ("position du salarié sur les faits", employee_admission),
        ("preuves invoquées par l'employeur", evidence),
        ("antécédents disciplinaires", prior_warnings),
        ("sanction envisagée", sanction),
    )
    return tuple(label for label, value in values if value is None or value == ())
