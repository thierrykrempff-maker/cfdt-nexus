# Experts Nexus

Cette zone accueille les experts metier appeles apres le routage Assistant DS.

## Experts prevus

- Expert Juriste droit du travail ;
- Expert DRH contradicteur ;
- Expert Paie ;
- Expert HSE / site Seveso.

## Etat V2

Seul `juriste_travail.py` est implemente en V0.

L'expert juriste :

- consomme la sortie validee du routeur V1.2 ;
- ne modifie pas le routage ;
- n'appelle aucun service externe ;
- n'invente pas de regle absente des sources ;
- indique clairement quand une conclusion depend d'un texte local ou d'une donnee manquante.

Les autres experts sont reserves pour des missions ulterieures.
