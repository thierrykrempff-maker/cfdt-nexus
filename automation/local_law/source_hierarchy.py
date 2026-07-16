"""Authority is attached to each source role and never flattened."""
from dataclasses import dataclass

@dataclass(frozen=True)
class LocalLawSource:
    source_id:str; role:str; authority_level:str; normative:bool

SOURCES=(
 LocalLawSource("alsace_moselle_local_law","statutes_and_regulations","primary_law",True),
 LocalLawSource("alsace_moselle_case_law","case_law","official_case_law",True),
 LocalLawSource("dreets_grand_est_local_law","administrative_guidance","official_guidance",False),
 LocalLawSource("service_public_local_law","practical_information","official_practical_information",False),
)

def source_for(source_id:str)->LocalLawSource:
    return next(source for source in SOURCES if source.source_id==source_id)
