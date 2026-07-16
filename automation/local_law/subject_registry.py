"""Initial matters requiring verification; no entitlement or duration is inferred."""
from __future__ import annotations
from .alsace_moselle_models import LocalRule

RULES=(
 LocalRule("AM-WAGE-L1226-23","Personal impediment and wage maintenance check","employment_contract_suspension",("57","67","68"),
  applicability_conditions=("cause_personnelle_independante_de_la_volonte","duree_relativement_sans_importance"),
  legal_references=("Code du travail, article L.1226-23",),payroll_impact_hint="comparison_required_no_fixed_duration",
  source_ids=("alsace_moselle_local_law","alsace_moselle_case_law"),warnings=("do_not_invent_duration","deduct_mandatory_regime_benefits_if_legally_required")),
 LocalRule("AM-WAGE-L1226-24","Commercial clerk special-rule check","employment_contract_suspension",("57","67","68"),
  personal_scope=("commercial_clerk_if_legal_conditions_met",),legal_references=("Code du travail, article L.1226-24",),
  payroll_impact_hint="distinct_from_L1226-23",source_ids=("alsace_moselle_local_law","alsace_moselle_case_law"),warnings=("do_not_merge_with_L1226-23",)),
 LocalRule("AM-HOLIDAY-DEC26","26 December local holiday verification","sunday_and_public_holidays",("57","67","68"),
  legal_references=("Code du travail — dispositions locales à vérifier",),source_ids=("alsace_moselle_local_law",),warnings=("holiday_status_does_not_prove_paid_non_working_day",)),
 LocalRule("AM-HOLIDAY-GOOD-FRIDAY","Good Friday municipal-scope verification","sunday_and_public_holidays",("57","67","68"),
  applicability_conditions=("municipality_scope_verified",),legal_references=("Code du travail — dispositions locales à vérifier",),source_ids=("alsace_moselle_local_law",),warnings=("municipality_information_required",)),
 LocalRule("AM-SUNDAY","Sunday-work local-rule verification","sunday_and_public_holidays",("57","67","68"),legal_references=("Code du travail — droit local du repos dominical à vérifier",),source_ids=("alsace_moselle_local_law",),warnings=("check_derogations_shift_work_and_agreements",)),
 LocalRule("AM-NOTICE","Local termination-notice verification","termination_notice",("57","67","68"),legal_references=("Droit local — texte et jurisprudence à auditer",),current_status="not_investigated",source_ids=("alsace_moselle_local_law","alsace_moselle_case_law"),warnings=("no_automatic_duration",)),
 LocalRule("AM-OTHER","Other local-law matter","other",("57","67","68"),legal_references=("Source officielle à identifier",),current_status="not_investigated",source_ids=("alsace_moselle_local_law",)),
)

def rules_for(area:str)->tuple[LocalRule,...]: return tuple(rule for rule in RULES if rule.legal_area==area)
