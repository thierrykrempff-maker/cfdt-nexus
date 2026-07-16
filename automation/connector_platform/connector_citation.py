from dataclasses import dataclass

@dataclass(frozen=True)
class Citation:
 url:str;title:str;author:str|None;date:str|None;version:str|None;authority:str;license_id:str;confidence:str
 def __post_init__(self):
  if not self.url.startswith("https://") or not self.title or not self.authority:raise ValueError("invalid citation")
