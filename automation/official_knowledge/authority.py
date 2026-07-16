"""Explicit authority levels; origin alone never determines legal authority."""
AUTHORITY_LEVELS = frozenset({"primary_law","official_case_law","official_regulation","official_guidance","official_practical_information","official_prevention_guidance","official_social_security_information","institutional_information","unknown"})

def validate_authority(level: str) -> str:
    if level not in AUTHORITY_LEVELS: raise ValueError("unknown authority level")
    return level
