"""Observed centralized ARACT representation; no regional transport."""
from dataclasses import dataclass
from enum import StrEnum

class RegionalEvidence(StrEnum):HTTP_CONFIRMED="http_confirmed"; SITEMAP_OBSERVED="sitemap_observed"

@dataclass(frozen=True)
class RegionalEntity:
 region_id:str;label:str;official_url:str;evidence:RegionalEvidence;centralized_on_anact:bool=True
 def __post_init__(self):
  if not self.region_id or not self.label or not self.official_url.startswith("https://www.anact.fr/") or not self.centralized_on_anact:raise ValueError("invalid centralized ARACT entity")

REGIONAL_ENTITIES=(
 RegionalEntity("grand_est","Grand Est","https://www.anact.fr/grand-est",RegionalEvidence.HTTP_CONFIRMED),
 RegionalEntity("centre_val_de_loire","Centre-Val de Loire","https://www.anact.fr/centre-val-de-loire",RegionalEvidence.SITEMAP_OBSERVED),
 RegionalEntity("guadeloupe","Guadeloupe","https://www.anact.fr/guadeloupe",RegionalEvidence.SITEMAP_OBSERVED),
 RegionalEntity("hauts_de_france","Hauts-de-France","https://www.anact.fr/hauts-de-france",RegionalEvidence.SITEMAP_OBSERVED),
 RegionalEntity("ile_de_france","Île-de-France","https://www.anact.fr/ile-de-france",RegionalEvidence.SITEMAP_OBSERVED),
 RegionalEntity("corse","Corse","https://www.anact.fr/corse",RegionalEvidence.SITEMAP_OBSERVED),
 RegionalEntity("la_reunion","La Réunion","https://www.anact.fr/la-reunion",RegionalEvidence.SITEMAP_OBSERVED),
)
REGION_BY_ID={entity.region_id:entity for entity in REGIONAL_ENTITIES}
