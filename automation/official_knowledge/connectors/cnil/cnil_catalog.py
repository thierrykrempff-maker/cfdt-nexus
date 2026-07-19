"""Facts verified manually from official sources on 2026-07-16."""
VERIFIED_ON="2026-07-16"
ACCESS_MECHANISMS=(
 {"mechanism":"cnil_targeted_pages","verified":True,"official_uri":"https://www.cnil.fr/fr/recherche","access_mode":"targeted_pages","authentication":False,"pagination":"site-dependent","format":"text/html","refresh_frequency":"unknown","stability":"probable","recommended":True,"limits":"allow-list and low navigation depth"},
 {"mechanism":"cnil_news_catalog","verified":True,"official_uri":"https://www.cnil.fr/fr/actualite","access_mode":"paginated_catalog","authentication":False,"pagination":"confirmed","format":"text/html","refresh_frequency":"irregular","stability":"probable","recommended":True,"limits":"metadata discovery only"},
 {"mechanism":"data_gouv_datasets","verified":True,"official_uri":"https://www.data.gouv.fr/organizations/cnil/datasets","access_mode":"open_data_catalog","authentication":False,"pagination":"catalog-managed","format":"mixed structured files","refresh_frequency":"dataset-dependent","stability":"probable","recommended":True,"limits":"dataset-by-dataset license and personal-data review"},
 {"mechanism":"legifrance_deliberations","verified":True,"official_uri":"https://www.legifrance.gouv.fr/cnil/","access_mode":"official_reference","authentication":False,"pagination":"confirmed","format":"text/html","refresh_frequency":"publication-dependent","stability":"high","recommended":True,"limits":"future Legifrance contract required"},
 {"mechanism":"public_cnil_api","verified":False,"official_uri":"https://www.cnil.fr/","access_mode":"unknown","authentication":"unknown","pagination":"unknown","format":"unknown","refresh_frequency":"unknown","stability":"unknown","recommended":False,"limits":"no explicit official CNIL content API documentation found"},
 {"mechanism":"rss_or_atom","verified":False,"official_uri":"https://www.cnil.fr/fr/actualite","access_mode":"unknown","authentication":False,"pagination":"n/a","format":"unknown","refresh_frequency":"unknown","stability":"unknown","recommended":False,"limits":"not confirmed"},
 {"mechanism":"sitemap_xml","verified":False,"official_uri":"https://www.cnil.fr/sitemap.xml","access_mode":"unknown","authentication":False,"pagination":"n/a","format":"xml_or_unknown","refresh_frequency":"unknown","stability":"unknown","recommended":False,"limits":"not confirmed by study tooling"},
 {"mechanism":"robots_txt","verified":False,"official_uri":"https://www.cnil.fr/robots.txt","access_mode":"policy_document","authentication":False,"pagination":"n/a","format":"text_or_unknown","refresh_frequency":"unknown","stability":"unknown","recommended":False,"limits":"must be rechecked before network activation"},
 {"mechanism":"etag_last_modified","verified":False,"official_uri":"https://www.cnil.fr/","access_mode":"http_metadata","authentication":False,"pagination":"n/a","format":"headers","refresh_frequency":"unknown","stability":"unknown","recommended":False,"limits":"not confirmed"},
)

LICENSE_CATEGORIES={
 "web_text":{"license_id":"CC-BY-ND-4.0-FR","attribution":True,"modification":False,"redistribution":True,"cache":"pending","full_text_storage":"pending","extracts":"pending","review_status":"pending"},
 "guides_reports_pdf":{"license_id":"CC-BY-ND-4.0-FR-unless-stated","attribution":True,"modification":False,"redistribution":"conditional","cache":"pending","full_text_storage":"pending","extracts":"pending","review_status":"pending"},
 "deliberation":{"license_id":"legifrance-terms-review","attribution":True,"modification":False,"redistribution":"pending","cache":"pending","full_text_storage":"pending","extracts":"pending","review_status":"pending"},
 "news_press_faq":{"license_id":"CC-BY-ND-4.0-FR","attribution":True,"modification":False,"redistribution":True,"cache":"pending","full_text_storage":"pending","extracts":"pending","review_status":"pending"},
 "images_video":{"license_id":"CC-BY-NC-ND-4.0-FR-or-third-party","attribution":True,"modification":False,"redistribution":"restricted","cache":False,"full_text_storage":False,"extracts":False,"review_status":"restricted"},
 "open_dataset":{"license_id":"Licence-Ouverte-2.0-default","attribution":True,"modification":True,"redistribution":True,"cache":True,"full_text_storage":"dataset_review","extracts":True,"review_status":"pending"},
}

THEME_PRIORITIES={
 "priority_high":("employee_surveillance","video_surveillance","geolocation","time_tracking","biometrics","professional_messaging","professional_devices","employee_access_right","personnel_files","health_data","union_data","telework","workplace_ai","cybersecurity_breaches","recruitment","data_retention"),
 "priority_medium":("questionnaires_surveys","photos_directories","subcontracting","data_transfers"),
 "out_of_scope_initially":(),
}

# LOT 0 declarations. These do not authorize access or collection.
from .cnil_models import CnilDocumentFamily,CnilPlannedCapability

CNIL_ALLOWED_DOMAINS=frozenset({"cnil.fr"})
CNIL_DOCUMENT_FAMILIES=tuple(CnilDocumentFamily)
CNIL_PLANNED_CAPABILITIES=(
 CnilPlannedCapability("public_metadata","Read public publication metadata"),
 CnilPlannedCapability("metadata_discovery","Discover public metadata incrementally"),
 CnilPlannedCapability("document_registry","Register validated metadata in the common registry"),
)
CNIL_CATALOG_DESCRIPTION="Architecture-only catalogue for future public CNIL metadata; no collection is implemented in LOT 0."
