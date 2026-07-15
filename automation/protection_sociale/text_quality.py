"""Deterministic text quality scoring without business interpretation."""
from __future__ import annotations
import re
from collections import Counter
def quality_level(score:int)->str:
    if score>=90:return "excellent"
    if score>=75:return "good"
    if score>=55:return "acceptable"
    if score>=25:return "poor"
    return "unusable"
def assess_quality(text:str,source:dict)->dict:
    if not text.strip():return {"score":0,"level":"unusable","flags":["empty_text"],"warnings":["empty text"]}
    score=100; flags=[]; length=len(text); lines=[x.strip() for x in text.splitlines() if x.strip() and not x.startswith("--- ")]
    if length<100:score-=40;flags.append("very_short_text")
    elif length<300:score-=20;flags.append("short_text")
    if length>5_000_000:score-=10;flags.append("very_long_text")
    abnormal=sum((ord(c)<32 and c not in "\n\t") or c=="\ufffd" for c in text)
    if abnormal:score-=min(30,10+abnormal);flags.append("abnormal_characters")
    normalized=[re.sub(r"\s+"," ",x.casefold()) for x in lines if len(x)>=3]; repetitions=sum(n-1 for n in Counter(normalized).values() if n>1)
    if normalized and repetitions/len(normalized)>.3:score-=15;flags.append("important_repetition")
    if len(lines)>=8 and sum(len(x)<20 for x in lines)/len(lines)>.65:score-=15;flags.append("excessive_fragmentation")
    empty_pages=sum(str(x).startswith("page_without_text:") for x in source.get("warnings",[]))
    if empty_pages:score-=min(25,5+3*empty_pages);flags.append("pages_without_text")
    if source.get("extraction_status") in {"extracted_with_warnings","failed","unreadable"}:score-=8;flags.append("partial_or_warned_extraction")
    score=max(0,min(100,score));return {"score":score,"level":quality_level(score),"flags":flags,"warnings":[x.replace('_',' ') for x in flags]}
