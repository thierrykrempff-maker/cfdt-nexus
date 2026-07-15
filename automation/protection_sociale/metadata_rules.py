"""Explicit, non-legal metadata rules for Protection sociale."""
from __future__ import annotations
import re,unicodedata
THEMES={
 "mutuelle":{"garanties":("garantie","garanties"),"remboursement":("remboursement","remboursé"),"optique":("optique","lunettes"),"dentaire":("dentaire","dentaires"),"hospitalisation":("hospitalisation","hospitalier"),"pharmacie":("pharmacie","pharmaceutique"),"médecine_douce":("médecine douce","osteopath"),"audioprothèse":("audioproth","appareil auditif")},
 "prévoyance":{"incapacité":("incapacité","incapacite"),"invalidité":("invalidité","invalidite"),"décès":("décès","deces"),"rente":("rente",),"capital":("capital",),"maintien_salaire":("maintien de salaire","maintien salaire")},
 "autre":{"portabilité":("portabilité","portabilite"),"cotisations":("cotisation",),"affiliation":("affiliation",),"dispense":("dispense",),"bénéficiaires":("bénéficiaire","beneficiaire","ayant droit")}}
DOCUMENT_TYPES={"notice":("notice d'information","notice"),"contrat":("contrat",),"avenant":("avenant",),"tableau_garanties":("tableau de garanties","garanties"),"formulaire":("formulaire",),"conditions_générales":("conditions générales","conditions generales")}
PUBLICS={"salariés":("salarié","salaries","salariés"),"retraités":("retraité","retraites","retraités"),"ayants_droit":("ayant droit","ayants droit"),"catégorie_professionnelle":("cadre","non cadre","catégorie professionnelle"),"régime_concerné":("régime général","regime general","alsace moselle")}
LABELS={"organisme_émetteur":r"(?:organisme\s+émetteur|émetteur)\s*[:\-]\s*([^\n]{2,120})","assureur":r"assureur\s*[:\-]\s*([^\n]{2,120})","contrat":r"(?:contrat|n[°o]\s*de\s*contrat)\s*[:\-]\s*([^\n]{2,100})","référence":r"réf(?:érence)?\s*[:\-]\s*([^\n]{2,80})","version":r"version\s*[:\-]\s*([^\n]{1,50})"}
DATE_LABELS={"date_effet":r"(?:date\s+d['’]effet|effet\s+au)\s*[:\-]?\s*(\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4})","date_mise_à_jour":r"(?:mise\s+à\s+jour|actualisé\s+le)\s*[:\-]?\s*(\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4})","date_fin":r"(?:date\s+de\s+fin|expire\s+le|expiration)\s*[:\-]?\s*(\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4})"}
def normalized(value:str)->str:
    return "".join(c for c in unicodedata.normalize("NFKD",value.casefold()) if not unicodedata.combining(c))
def keyword_counts(text:str,terms:tuple[str,...])->int:
    value=normalized(text);return sum(len(re.findall(r"(?<!\w)"+re.escape(normalized(t))+r"(?!\w)",value)) for t in terms)
def labeled_values(text:str,pattern:str)->list[str]:
    return list(dict.fromkeys(x.strip(" .;\t") for x in re.findall(pattern,text,re.I) if x.strip(" .;\t")))
