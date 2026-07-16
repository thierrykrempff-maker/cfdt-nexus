"""Recommended connector-study waves; no connector is implemented here."""
from __future__ import annotations

WAVE_ORDER={
 "WAVE_0":("legifrance","judilibre","code_travail_numerique","cnil","alsace_moselle_local_law"),
 "WAVE_1":("inrs","dreets_grand_est","dreal_grand_est","ineris","aida","aria"),
 "WAVE_2":("anact","ameli","assurance_maladie_risques_professionnels","urssaf","service_public"),
 "WAVE_3":("echa","georisques","anssi","france_chimie","observatoire_chimie","opco_2i"),
 "WAVE_4":("assurance_retraite","agirc_arrco","france_competences","caf","gestis"),
}

def recommended_sources(catalog)->tuple:
 return tuple(sorted(catalog,key=lambda source:(int(source.development_wave[-1]),source.development_rank,source.source_id)))
