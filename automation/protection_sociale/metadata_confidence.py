"""Deterministic confidence calculation for metadata evidence."""
LEVELS=((.9,"very_high"),(.75,"high"),(.5,"medium"),(.25,"low"),(0,"very_low"))
SOURCE_SCORES={"labeled_header":.95,"title":.85,"filename":.65,"path":.55,"content_frequency":.50,"absent":0.0}
def confidence_level(score:float)->str:
    return next(level for threshold,level in LEVELS if score>=threshold)
def confidence(source:str,frequency:int=1,coherent:bool=True,contradiction:bool=False)->tuple[float,str]:
    score=SOURCE_SCORES.get(source,0.0)+min(.1,max(0,frequency-1)*.02)
    if coherent:score+=.03
    if contradiction:score-=.35
    score=max(0,min(1,score));return round(score,2),confidence_level(score)
def quality_level(score:int)->str:
    if score>=85:return "excellent"
    if score>=70:return "good"
    if score>=50:return "acceptable"
    if score>=25:return "poor"
    return "unusable"
