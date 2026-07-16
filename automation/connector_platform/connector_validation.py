from dataclasses import dataclass
from .connector_contract import ConnectorContract
from .connector_document import DocumentPolicy
from .connector_license import LICENSE_POLICIES

@dataclass(frozen=True)
class ValidationResult:
 valid:bool;errors:tuple[str,...]=()

_RANK={DocumentPolicy.FORBIDDEN:0,DocumentPolicy.METADATA_ONLY:1,DocumentPolicy.EXCERPTS:2,DocumentPolicy.FULLTEXT_ALLOWED:3}

def validate_contract(contract:ConnectorContract)->ValidationResult:
 errors=[];maximum=LICENSE_POLICIES[contract.license_id].maximum_policy
 if _RANK[contract.document_policy]>_RANK[maximum]:errors.append("document_policy_exceeds_license")
 if not contract.security.network_disabled_by_default:errors.append("network_must_be_disabled")
 return ValidationResult(not errors,tuple(errors))
