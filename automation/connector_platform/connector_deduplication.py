from dataclasses import dataclass

@dataclass(frozen=True)
class DeduplicationResult:
 unique_fingerprints:tuple[str,...];duplicate_fingerprints:tuple[str,...]
def deduplicate(values:list[str])->DeduplicationResult:
 seen=set();unique=[];duplicates=[]
 for value in values:
  if value in seen:
   if value not in duplicates:duplicates.append(value)
  else:seen.add(value);unique.append(value)
 return DeduplicationResult(tuple(unique),tuple(duplicates))
