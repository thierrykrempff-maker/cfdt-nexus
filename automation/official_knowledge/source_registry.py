"""Versioned registry; no endpoint is inferred for uninvestigated sources."""
from __future__ import annotations
from .source_models import SourceDefinition

_NAMES = (
 ("cnil","CNIL","Commission nationale de l'informatique et des libertés"),
 ("inrs","INRS","Institut national de recherche et de sécurité"),
 ("anact","ANACT","Agence nationale pour l'amélioration des conditions de travail"),
 ("ameli","Ameli","Assurance Maladie"), ("service_public","Service-Public.fr","Direction de l'information légale et administrative"),
 ("urssaf","URSSAF","URSSAF"), ("assurance_retraite","Assurance retraite","Assurance retraite"),
 ("agirc_arrco","Agirc-Arrco","Agirc-Arrco"), ("legifrance","Légifrance","Direction de l'information légale et administrative"),
 ("judilibre","JUDILIBRE","Cour de cassation"), ("code_travail_numerique","Code du travail numérique","Ministère du Travail"),
)
_EXISTING_DOMAINS={"legifrance":("api.piste.gouv.fr","oauth.piste.gouv.fr"),"judilibre":("api.piste.gouv.fr","oauth.piste.gouv.fr"),"code_travail_numerique":("code.travail.gouv.fr",)}
_CNIL_DOMAINS=("cnil.fr","linc.cnil.fr","data.gouv.fr","legifrance.gouv.fr")
SOURCES=tuple(SourceDefinition(source_id=sid,display_name=name,publisher=publisher,
    source_type="targeted_pages" if sid=="cnil" else "existing_internal_connector" if sid in _EXISTING_DOMAINS else "unknown",
    official_domains=_CNIL_DOMAINS if sid=="cnil" else _EXISTING_DOMAINS.get(sid,()),
    allowed_access_modes=("targeted_pages","open_data_catalog","legifrance_reference") if sid=="cnil" else (),
    authority_level="official_guidance" if sid=="cnil" else "unknown", domain_tags=("personal_data","work",) if sid=="cnil" else (),
    kill_switch_key=sid.upper(), connector_status="architecture_only", enabled=False) for sid,name,publisher in _NAMES) + (
 SourceDefinition(source_id="alsace_moselle_local_law",display_name="Droit local d'Alsace-Moselle — textes",
    publisher="République française",source_type="existing_internal_connector",official_domains=("legifrance.gouv.fr",),
    authority_level="primary_law",domain_tags=("ALSACE_MOSELLE_LOCAL_LAW",),kill_switch_key="ALSACE_MOSELLE_LOCAL_LAW",enabled=False,connector_status="architecture_only"),
 SourceDefinition(source_id="alsace_moselle_case_law",display_name="Droit local d'Alsace-Moselle — jurisprudence",
    publisher="Cour de cassation",source_type="existing_internal_connector",official_domains=("courdecassation.fr","legifrance.gouv.fr"),
    authority_level="official_case_law",domain_tags=("ALSACE_MOSELLE_LOCAL_LAW",),kill_switch_key="ALSACE_MOSELLE_CASE_LAW",enabled=False,connector_status="architecture_only"),
 SourceDefinition(source_id="dreets_grand_est_local_law",display_name="DREETS Grand Est — droit local du travail",
    publisher="DREETS Grand Est",source_type="targeted_pages",official_domains=("grand-est.dreets.gouv.fr",),
    authority_level="official_guidance",domain_tags=("ALSACE_MOSELLE_LOCAL_LAW",),kill_switch_key="DREETS_GRAND_EST",enabled=False,connector_status="architecture_only"),
 SourceDefinition(source_id="service_public_local_law",display_name="Service-Public.fr — informations pratiques droit local",
    publisher="Direction de l'information légale et administrative",source_type="targeted_pages",official_domains=("service-public.fr",),
    authority_level="official_practical_information",domain_tags=("ALSACE_MOSELLE_LOCAL_LAW",),kill_switch_key="SERVICE_PUBLIC_LOCAL_LAW",enabled=False,connector_status="architecture_only"),
 SourceDefinition(source_id="dreets_grand_est",display_name="DREETS Grand Est",
    publisher="Ministère du Travail",source_type="targeted_pages",official_domains=("grand-est.dreets.gouv.fr",),
    authority_level="official_guidance",domain_tags=("employment_law","labour_inspection","social_dialogue","occupational_health"),
    kill_switch_key="DREETS_GRAND_EST",enabled=False,connector_status="architecture_only",
    notes="Access, terms and licenses require official review before any network implementation."),
)
SOURCE_REGISTRY={s.source_id:s for s in SOURCES}

def get_source(source_id: str) -> SourceDefinition: return SOURCE_REGISTRY[source_id]
def list_sources() -> tuple[SourceDefinition,...]: return SOURCES

# The prioritized catalog is descriptive; registry membership remains the smaller
# operational/architectural allow-list and does not activate catalog entries.
from .source_catalog import CATALOG_BY_ID
CATALOG_SOURCE_IDS=frozenset(CATALOG_BY_ID)
