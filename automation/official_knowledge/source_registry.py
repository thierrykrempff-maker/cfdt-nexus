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
SOURCES=tuple(SourceDefinition(source_id=sid,display_name=name,publisher=publisher,
    source_type="existing_internal_connector" if sid in _EXISTING_DOMAINS else "unknown",
    official_domains=_EXISTING_DOMAINS.get(sid,()), authority_level="unknown", domain_tags=(),
    kill_switch_key=sid.upper(), connector_status="architecture_only", enabled=False) for sid,name,publisher in _NAMES)
SOURCE_REGISTRY={s.source_id:s for s in SOURCES}

def get_source(source_id: str) -> SourceDefinition: return SOURCE_REGISTRY[source_id]
def list_sources() -> tuple[SourceDefinition,...]: return SOURCES
