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
    kill_switch_key=sid.upper(), connector_status="architecture_only", enabled=False) for sid,name,publisher in _NAMES)
SOURCE_REGISTRY={s.source_id:s for s in SOURCES}

def get_source(source_id: str) -> SourceDefinition: return SOURCE_REGISTRY[source_id]
def list_sources() -> tuple[SourceDefinition,...]: return SOURCES
