"""Offline trigger for a future router integration; this module is not wired to it."""
from __future__ import annotations
import unicodedata
from .alsace_moselle_models import EmploymentContext, TriggerAssessment
from .applicability import assess_applicability
from . import ALSACE_MOSELLE_HEALTH_INSURANCE_REGIME, ALSACE_MOSELLE_LOCAL_LAW

LABOUR={"maladie","arret maladie","accident","absence personnelle","maintien de salaire","carence","ijss","prevoyance","dimanche","jour ferie","26 decembre","vendredi saint","preavis","rupture"}
LOCALITY={"alsace","moselle","bas-rhin","haut-rhin","sarralbe"}
HEALTH={"regime local","assurance maladie locale","regime local d'assurance maladie"}

def _norm(text:str)->str:
    return "".join(c for c in unicodedata.normalize("NFKD",text.casefold()) if not unicodedata.combining(c))

def evaluate_local_law_check(question:str,context:EmploymentContext|None=None)->TriggerAssessment:
    text=_norm(question); context=context or EmploymentContext(); applicability=assess_applicability(context)
    labour=any(term in text for term in LABOUR); locality=any(term in text for term in LOCALITY); health=any(term in text for term in HEALTH)
    territorial_signal=locality or applicability.status in {"applicable","probably_applicable","applicability_uncertain"}
    required=health or (labour and territorial_signal)
    domains=[]
    if health: domains.append(ALSACE_MOSELLE_HEALTH_INSURANCE_REGIME)
    if labour and territorial_signal: domains.append(ALSACE_MOSELLE_LOCAL_LAW)
    warnings=list(applicability.warnings)
    if health: warnings.append("health_insurance_regime_does_not_prove_local_employment_law")
    if required: warnings.append("official_sources_and_scope_must_be_verified_before_application")
    queries=[]
    if ALSACE_MOSELLE_LOCAL_LAW in domains: queries.extend(("Légifrance droit local champ applicable","DREETS Grand Est droit local travail","JUDILIBRE jurisprudence droit local"))
    if ALSACE_MOSELLE_HEALTH_INSURANCE_REGIME in domains: queries.append("source officielle régime local assurance maladie affiliation")
    return TriggerAssessment(required,tuple(domains),applicability.status,applicability.missing_facts,tuple(queries),tuple(dict.fromkeys(warnings)))
