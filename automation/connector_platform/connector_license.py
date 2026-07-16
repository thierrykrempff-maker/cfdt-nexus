from dataclasses import dataclass
from enum import StrEnum
from .connector_document import DocumentPolicy

class LicenseId(StrEnum):
 LICENCE_OUVERTE="LICENCE_OUVERTE"; CC_BY="CC_BY"; CC_BY_SA="CC_BY_SA"; CC_BY_ND="CC_BY_ND"
 CC_BY_NC="CC_BY_NC"; CC_BY_NC_SA="CC_BY_NC_SA"; CC_BY_NC_ND="CC_BY_NC_ND"
 UNKNOWN="UNKNOWN"; DOCUMENT_SPECIFIC="DOCUMENT_SPECIFIC"

@dataclass(frozen=True)
class LicensePolicy:
 license_id:LicenseId; maximum_policy:DocumentPolicy; attribution_required:bool=True; review_required:bool=False

LICENSE_POLICIES={
 LicenseId.LICENCE_OUVERTE:LicensePolicy(LicenseId.LICENCE_OUVERTE,DocumentPolicy.FULLTEXT_ALLOWED),
 LicenseId.CC_BY:LicensePolicy(LicenseId.CC_BY,DocumentPolicy.FULLTEXT_ALLOWED),
 LicenseId.CC_BY_SA:LicensePolicy(LicenseId.CC_BY_SA,DocumentPolicy.FULLTEXT_ALLOWED),
 LicenseId.CC_BY_ND:LicensePolicy(LicenseId.CC_BY_ND,DocumentPolicy.EXCERPTS),
 LicenseId.CC_BY_NC:LicensePolicy(LicenseId.CC_BY_NC,DocumentPolicy.EXCERPTS),
 LicenseId.CC_BY_NC_SA:LicensePolicy(LicenseId.CC_BY_NC_SA,DocumentPolicy.EXCERPTS),
 LicenseId.CC_BY_NC_ND:LicensePolicy(LicenseId.CC_BY_NC_ND,DocumentPolicy.METADATA_ONLY),
 LicenseId.UNKNOWN:LicensePolicy(LicenseId.UNKNOWN,DocumentPolicy.METADATA_ONLY,review_required=True),
 LicenseId.DOCUMENT_SPECIFIC:LicensePolicy(LicenseId.DOCUMENT_SPECIFIC,DocumentPolicy.METADATA_ONLY,review_required=True),
}
