from dataclasses import dataclass

@dataclass(frozen=True)
class SecurityPolicy:
 network_disabled_by_default:bool=True
 read_only:bool=True
 no_post:bool=True
 no_delete:bool=True
 no_authentication:bool=True
 no_secrets:bool=True
 no_private_endpoint:bool=True
 no_external_redirection:bool=True
 def __post_init__(self):
  if not all(vars(self).values()):raise ValueError("LOT 0 security controls cannot be weakened")

DEFAULT_SECURITY_POLICY=SecurityPolicy()
