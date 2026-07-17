"""Declarative ANACT catalogue based only on repository-known information."""
from dataclasses import dataclass

from .anact_models import AccessMode,AccessStatus,AnactResourceType,AnactSource,AnactTheme,GeographicScope

@dataclass(frozen=True)
class SourceFamily:
 family_id:str;label:str;resource_type:AnactResourceType;priority:int
 themes:tuple[AnactTheme,...];access_status:AccessStatus=AccessStatus.PENDING_OFFICIAL_REVIEW
 def __post_init__(self):
  if not self.family_id or not self.label or not 1<=self.priority<=5 or not self.themes:raise ValueError("invalid source family")

ANACT_NATIONAL_SOURCE=AnactSource("anact_national","ANACT", "https://www.anact.fr",GeographicScope.NATIONAL,access_modes=(AccessMode.API,AccessMode.OFFICIAL_FEED,AccessMode.HTML,AccessMode.DOCUMENT,AccessMode.MANUAL))
SOURCES=(ANACT_NATIONAL_SOURCE,)
SOURCE_BY_ID={source.source_id:source for source in SOURCES}

SOURCE_FAMILIES=(
 SourceFamily("thematic_pages","Pages thématiques",AnactResourceType.THEMATIC_PAGE,1,(AnactTheme.WORKING_CONDITIONS,AnactTheme.QVCT,AnactTheme.WORK_ORGANIZATION)),
 SourceFamily("publications","Publications",AnactResourceType.PUBLICATION,1,(AnactTheme.QVCT,AnactTheme.SOCIAL_DIALOGUE,AnactTheme.OCCUPATIONAL_HEALTH)),
 SourceFamily("guides","Guides",AnactResourceType.GUIDE,1,(AnactTheme.OCCUPATIONAL_RISK_PREVENTION,AnactTheme.WORKLOAD,AnactTheme.REMOTE_WORK)),
 SourceFamily("tools","Outils",AnactResourceType.TOOL,2,(AnactTheme.WORK_ORGANIZATION,AnactTheme.MANAGEMENT)),
 SourceFamily("dossiers","Dossiers",AnactResourceType.DOSSIER,1,(AnactTheme.WORK_TRANSFORMATIONS,AnactTheme.PSYCHOSOCIAL_RISKS)),
 SourceFamily("studies","Études",AnactResourceType.STUDY,2,(AnactTheme.ABSENTEEISM,AnactTheme.OCCUPATIONAL_WEAR,AnactTheme.JOB_RETENTION)),
 SourceFamily("practical_sheets","Fiches pratiques",AnactResourceType.PRACTICAL_SHEET,1,(AnactTheme.QVCT,AnactTheme.PROFESSIONAL_EQUALITY)),
 SourceFamily("aract_resources","Ressources régionales ARACT",AnactResourceType.REGIONAL_RESOURCE,2,(AnactTheme.WORKING_CONDITIONS,AnactTheme.SOCIAL_DIALOGUE)),
 SourceFamily("news","Actualités",AnactResourceType.NEWS,3,(AnactTheme.WORK_TRANSFORMATIONS,)),
 SourceFamily("events","Événements",AnactResourceType.EVENT,4,(AnactTheme.SOCIAL_DIALOGUE,AnactTheme.QVCT)),
 SourceFamily("structured_data","Données structurées éventuelles",AnactResourceType.STRUCTURED_DATA,5,(AnactTheme.OTHER,)),
)
FAMILY_BY_ID={family.family_id:family for family in SOURCE_FAMILIES}

CONFIRMED_ENTRY_POINTS={
 "homepage":"https://www.anact.fr/",
 "themes":"https://www.anact.fr/themes",
 "regions":"https://www.anact.fr/regions",
 "grand_est":"https://www.anact.fr/grand-est",
 "robots":"https://www.anact.fr/robots.txt",
 "sitemap":"https://www.anact.fr/sitemap.xml",
}

def get_source(source_id:str)->AnactSource:
 try:return SOURCE_BY_ID[source_id]
 except KeyError as error:raise KeyError(f"unknown ANACT source: {source_id}") from error
