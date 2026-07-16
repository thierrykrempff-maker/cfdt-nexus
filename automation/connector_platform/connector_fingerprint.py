import hashlib

def fingerprint_bytes(data:bytes)->str:
 if not isinstance(data,bytes):raise TypeError("bytes required")
 return hashlib.sha256(data).hexdigest()
def fingerprint_metadata(values:tuple[str,...])->str:return fingerprint_bytes("\x1f".join(values).encode("utf-8"))
