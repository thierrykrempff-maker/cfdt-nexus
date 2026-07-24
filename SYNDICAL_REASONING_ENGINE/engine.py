"""Deterministic, non-decisional syndical reasoning engine."""

from __future__ import annotations

import unicodedata

from .models import (
    Citation,
    FactStatus,
    SourceContradiction,
    SourceVerification,
    SyndicalCaseInput,
    SyndicalReasoningReport,
)
from .protocol import PROTOCOL_STEPS
from .prudence import caution_alerts, determine_confidence
from .source_policy import hierarchy_labels, rank_sources
from .strategies import build_action_options, chronological_plan


DOMAIN_MARKERS = {
    "employment_contract": (
        "contrat", "avenant", "changement de poste", "equipe postee",
        "modification des conditions",
    ),
    "working_time": ("horaire", "travail poste", "equipe postee", "5x8", "nuit"),
    "payroll": ("remuneration", "prime", "salaire", "bulletin"),
    "health_safety": ("sante", "securite", "fatigue", "contrainte", "risque"),
    "cse_consultation": ("cse", "consultation", "information du cse", "reorganisation"),
    "disciplinary": ("sanction", "avertissement", "licenciement"),
    "discrimination_harassment": ("discrimination", "harcelement"),
    "personal_data": ("donnees personnelles", "rgpd", "geolocalisation"),
    "social_protection": ("cpam", "invalidite", "prevoyance"),
    "retirement": ("retraite", "carriere", "c2p", "penibilite"),
}


RIGHTS_BY_DOMAIN = {
    "employment_contract": "Droit possible à une information claire et à l'examen du consentement requis.",
    "working_time": "Droit possible au respect des durées, repos et règles conventionnelles applicables.",
    "payroll": "Droit possible au maintien ou à la régularisation des éléments de rémunération dus.",
    "health_safety": "Droit à la protection de la santé et à la prévention des risques.",
    "cse_consultation": "Droit collectif possible à l'information ou à la consultation du CSE.",
    "disciplinary": "Droit au contradictoire et au respect de la procédure disciplinaire.",
    "discrimination_harassment": "Droit à la protection contre discrimination et harcèlement.",
    "personal_data": "Droit à la protection et à la minimisation des données personnelles.",
}


class SyndicalReasoningEngine:
    """Assemble a cautious report from supplied facts and metadata only."""

    def analyze(self, case: SyndicalCaseInput) -> SyndicalReasoningReport:
        if not isinstance(case, SyndicalCaseInput):
            raise TypeError("case must be a SyndicalCaseInput")
        domains = self._domains(case)
        all_sources = case.available_sources + case.available_internal_sources
        ranked_sources = rank_sources(all_sources, domains)
        contradictions = self._contradictions(all_sources)
        missing = self._missing_information(case)
        confidence = determine_confidence(case, ranked_sources, len(contradictions))
        options = build_action_options(case, domains)
        citations = tuple(
            Citation(
                item.source.source_id,
                item.source.title,
                item.source.authority,
                item.source.canonical_url,
                item.source.verification,
            )
            for item in ranked_sources
            if item.source.verification is not SourceVerification.MISSING
        )
        established = tuple(item.statement for item in case.established_facts)
        declared = tuple(item.statement for item in case.declared_facts)
        hypotheses = tuple(item.statement for item in case.hypotheses)
        qualification = tuple(
            f"Qualification provisoire à vérifier : {self._domain_label(domain)}."
            for domain in domains
        ) or ("Qualification impossible sans domaine ni faits complémentaires.",)
        evidence = tuple(
            dict.fromkeys(
                [
                    "décision ou instruction écrite de l'employeur",
                    "contrat de travail et avenants",
                    *[item.title for item in case.available_pieces if not item.verified],
                    *missing,
                ]
            )
        )
        return SyndicalReasoningReport(
            situation_summary=self._summary(case),
            retained_facts=established + declared,
            hypotheses=hypotheses,
            missing_information=missing,
            provisional_qualification=qualification,
            domains=domains,
            main_issues=tuple(self._domain_label(item) for item in domains),
            sources=ranked_sources,
            source_hierarchy=hierarchy_labels(ranked_sources),
            contradictions=contradictions,
            possible_employee_rights=tuple(
                RIGHTS_BY_DOMAIN[item] for item in domains if item in RIGHTS_BY_DOMAIN
            ),
            employer_obligations_or_risks=tuple(
                f"Vérifier les obligations de l'employeur relatives à {self._domain_label(item)}."
                for item in domains
            ),
            representative_roles=self._roles(domains),
            urgency=case.urgency,
            confidence=confidence,
            action_options=options,
            recommended_strategy=(
                "Adopter une démarche progressive : clarifier par écrit, réunir les "
                "preuves et sources applicables, puis choisir l'intervention adaptée "
                "sans préjuger de la légalité de la décision."
            ),
            action_plan=chronological_plan(options),
            evidence_to_obtain=evidence,
            follow_up_questions=self._questions(case, domains),
            caution_alerts=caution_alerts(case, domains),
            citations=citations,
            analysis_limits=self._limits(case, ranked_sources, contradictions),
            completed_steps=tuple(item.value for item in PROTOCOL_STEPS),
        )

    @staticmethod
    def _normalize(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value)
        return " ".join(
            "".join(char for char in normalized if not unicodedata.combining(char))
            .lower()
            .split()
        )

    def _domains(self, case: SyndicalCaseInput) -> tuple[str, ...]:
        selected = set(case.suspected_domains)
        haystack = self._normalize(
            " ".join(
                [case.question]
                + [item.statement for item in case.declared_facts]
                + [item.statement for item in case.established_facts]
            )
        )
        for domain, markers in DOMAIN_MARKERS.items():
            if any(marker in haystack for marker in markers):
                selected.add(domain)
        return tuple(sorted(selected))

    @staticmethod
    def _contradictions(sources):
        pairs = set()
        for source in sources:
            for other in source.contradicts_source_ids:
                pairs.add(tuple(sorted((source.source_id, other))))
        return tuple(
            SourceContradiction(pair, "Contradiction déclarée entre sources.")
            for pair in sorted(pairs)
        )

    @staticmethod
    def _missing_information(case: SyndicalCaseInput) -> tuple[str, ...]:
        missing = list(case.missing_information)
        required = (
            ("qualité de la personne concernée", case.person_capacity),
            ("contexte ou établissement", case.workplace_context),
            ("date ou période des faits", case.fact_period),
            ("objectif recherché", case.desired_outcome),
        )
        missing.extend(label for label, value in required if not value)
        if not case.available_sources and not case.available_internal_sources:
            missing.append("sources applicables vérifiées")
        if not case.available_pieces:
            missing.append("pièces étayant la décision et la situation")
        return tuple(dict.fromkeys(missing))

    @staticmethod
    def _summary(case: SyndicalCaseInput) -> str:
        return (
            "La demande porte sur une situation déclarée qui nécessite de distinguer "
            "les faits prouvés, les hypothèses et les règles effectivement applicables."
        )

    @staticmethod
    def _domain_label(domain: str) -> str:
        return domain.replace("_", " ")

    @staticmethod
    def _roles(domains: tuple[str, ...]) -> tuple[str, ...]:
        roles = ["Délégué syndical : accompagner, clarifier et structurer la démarche."]
        if "cse_consultation" in domains:
            roles.append("CSE : vérifier la dimension collective et ses attributions.")
        if "health_safety" in domains:
            roles.append("CSE/CSSCT : examiner les impacts santé-sécurité selon leurs compétences.")
        if "discrimination_harassment" in domains:
            roles.append("Défenseur des droits ou inspection du travail : orientation possible après vérification.")
        if "social_protection" in domains:
            roles.append("Organisme de protection sociale : vérifier les droits relevant de sa compétence.")
        return tuple(roles)

    @staticmethod
    def _questions(case: SyndicalCaseInput, domains: tuple[str, ...]) -> tuple[str, ...]:
        questions = [
            "Quelle décision écrite a été remise, par qui et à quelle date ?",
            "Le contrat ou un avenant décrit-il les horaires ou l'organisation concernés ?",
            "Quels accords et usages sont effectivement applicables ?",
        ]
        if "cse_consultation" in domains:
            questions.append("Le projet est-il collectif et le CSE a-t-il reçu une information formelle ?")
        if "payroll" in domains:
            questions.append("Quels éléments de rémunération ou primes seraient modifiés ?")
        return tuple(questions)

    @staticmethod
    def _limits(case, sources, contradictions):
        limits = []
        if not case.established_facts:
            limits.append("Aucun fait n'est encore établi par une pièce vérifiée.")
        if not sources:
            limits.append("Aucune source applicable n'a été fournie ou vérifiée.")
        if contradictions:
            limits.append("Des contradictions entre sources exigent une revue experte.")
        limits.append("La qualification reste provisoire et ne constitue pas une décision juridique.")
        return tuple(limits)
