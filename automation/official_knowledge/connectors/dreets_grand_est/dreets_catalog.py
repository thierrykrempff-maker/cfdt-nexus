"""Offline access study and domain taxonomy; facts not verified remain pending."""

OFFICIAL_DOMAIN="grand-est.dreets.gouv.fr"
STUDY_STATUS="pending_official_review"
ACCESS_STUDY=(
 {"mechanism":"targeted_official_pages","status":STUDY_STATUS,"access_mode":"targeted_pages","authentication":"unknown","pagination":"unknown","format":"unknown","recommended":False,"caveat":"official terms, robots and page stability must be reviewed"},
 {"mechanism":"official_api","status":STUDY_STATUS,"access_mode":"unknown","authentication":"unknown","pagination":"unknown","format":"unknown","recommended":False,"caveat":"no endpoint inferred"},
 {"mechanism":"rss_or_atom","status":STUDY_STATUS,"access_mode":"unknown","authentication":"unknown","pagination":"not_applicable","format":"unknown","recommended":False,"caveat":"feed existence not asserted"},
 {"mechanism":"sitemap","status":STUDY_STATUS,"access_mode":"unknown","authentication":"unknown","pagination":"not_applicable","format":"unknown","recommended":False,"caveat":"sitemap existence not asserted"},
)

LICENSE_STUDY={
 "web_pages":{"license_id":"UNKNOWN","review_status":STUDY_STATUS,"cache":False,"full_text":False,"index_level":"METADATA_ONLY","extracts":False,"citation_required":True},
 "downloadable_documents":{"license_id":"DOCUMENT_SPECIFIC_REVIEW","review_status":STUDY_STATUS,"cache":False,"full_text":False,"index_level":"METADATA_ONLY","extracts":False,"citation_required":True},
 "legal_or_regulatory_references":{"license_id":"AUTHORITATIVE_SOURCE_TERMS_REQUIRED","review_status":STUDY_STATUS,"cache":False,"full_text":False,"index_level":"METADATA_ONLY","extracts":False,"citation_required":True},
}

DOMAIN_FAMILIES=("inspection_du_travail","relations_collectives","elections_professionnelles","cse","sante_au_travail","dialogue_social","temps_de_travail","licenciement","rupture","egalite_professionnelle","discrimination","harcelement","apprentissage","emploi","formation","jeunes_travailleurs","travailleurs_etrangers","salaires","representation_du_personnel","questions_reponses_officielles")

QUESTION_INTENTS={
 "cse_during_leave":("cse","representation_du_personnel","temps_de_travail"),
 "information_consultation_deadlines":("cse","relations_collectives","dialogue_social"),
 "protected_employee_rights":("inspection_du_travail","representation_du_personnel","licenciement"),
}
