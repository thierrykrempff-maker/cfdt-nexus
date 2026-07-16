from dataclasses import dataclass,field

@dataclass(frozen=True)
class ConnectorMetadata:
 connector_id:str;display_name:str;publisher:str;description:str="";tags:tuple[str,...]=field(default_factory=tuple)
 def __post_init__(self):
  if not self.connector_id or not self.connector_id.replace("_","").isalnum() or not self.display_name or not self.publisher:raise ValueError("invalid connector metadata")
