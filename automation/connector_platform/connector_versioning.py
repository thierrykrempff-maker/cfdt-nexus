from dataclasses import dataclass

@dataclass(frozen=True)
class DocumentVersion:
 document_id:str;version_id:str;fingerprint:str;previous_version_id:str|None=None
 def __post_init__(self):
  if not self.document_id or not self.version_id or not self.fingerprint:raise ValueError("invalid version")
  if self.previous_version_id==self.version_id:raise ValueError("self reference")
def changed(left:DocumentVersion,right:DocumentVersion)->bool:return left.fingerprint!=right.fingerprint
