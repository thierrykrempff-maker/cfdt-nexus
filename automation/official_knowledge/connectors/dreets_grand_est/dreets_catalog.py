"""Offline access study and domain taxonomy; facts not verified remain pending."""

OFFICIAL_DOMAIN="grand-est.dreets.gouv.fr"
STUDY_STATUS="pending_official_review"
ACCESS_STUDY=(
 {"mechanism":"targeted_official_pages","status":"officially_observed","access_mode":"targeted_pages","authentication":"none_observed","pagination":"observed","format":"html","recommended":True,"caveat":"metadata-only collection; legal classification remains document-specific"},
 {"mechanism":"official_api","status":"not_identified_in_limited_review","access_mode":"unknown","authentication":"unknown","pagination":"unknown","format":"unknown","recommended":False,"caveat":"absence was not established; no endpoint or developer documentation was identified"},
 {"mechanism":"rss_or_atom","status":"rss_link_observed_payload_unverified","access_mode":"published_link","authentication":"none_observed","pagination":"not_applicable","format":"rss_expected","recommended":False,"caveat":"the published RSS endpoint could not be parsed by the review tool; Atom was not identified"},
 {"mechanism":"sitemap","status":"html_site_plan_observed_xml_unverified","access_mode":"published_link","authentication":"none_observed","pagination":"not_applicable","format":"html","recommended":False,"caveat":"the SPIP site-plan page is not evidence of an XML sitemap"},
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
