# Experts Nexus

Cette zone accueille les experts metier appeles apres le routage Assistant DS.

## Experts prevus

- Expert Juriste droit du travail ;
- Expert DRH contradicteur ;
- Expert Paie ;
- Expert HSE / site Seveso.

## Etat V2.1

`juriste_travail.py` reste le socle juriste, renforce en V2.1.

Depuis le contrat `agents/juriste/EXPERT_JURISTE_CFDT_NEXUS_V1.md`, l'expert
juriste porte aussi une doctrine de reponse plus complete :

- reponse claire a la question posee ;
- sources analysees par couche juridique ;
- niveau de certitude separe entre regle certaine, interpretation, hypothese et information manquante ;
- strategie de defense du salarie avec position probable de la direction et contre-arguments ;
- analyse contradictoire des decisions ou dossiers contentieux reellement remontes ;
- modes metier `DEFENSE_SALARIE`, `NEGOCIATION_ACCORD` et `CSE_CSSCT` pour transformer les sources en aide de travail syndical ;
- pieces utiles a recuperer ;
- action progressive avant tout contentieux.

L'expert juriste :

- consomme la sortie validee du routeur V1.2 ;
- ne modifie pas le routage ;
- n'appelle aucun service externe ;
- n'invente pas de regle absente des sources ;
- distingue regle certaine, interpretation, hypothese et information manquante ;
- produit qualification juridique, analyse, vigilance, position de travail et limites ;
- travaille dans l'interet des salaries sans masquer les sources defavorables ni decider politiquement a la place du delegue syndical.

`paie.py` ajoute l'Expert Paie V0 :

- controle salaire, coefficient, heures, majorations, primes, astreinte, recuperations, compteurs et bulletin ;
- liste les rubriques, donnees, documents et sources necessaires ;
- ne produit aucun calcul detaille si les heures, taux, assiette, source et valeur bulletin ne sont pas disponibles.

`orchestrator.py` assure la premiere coordination locale :

- appelle Juriste et/ou Paie selon la question ;
- transporte le mode metier principal et les analyses metier dans la reponse locale ;
- produit une synthese Nexus unique ;
- conserve les analyses par expertise sans simple concatenation ;
- dedoublonne sources, documents, questions et limites.

Les experts DRH contradicteur et HSE / site Seveso restent reserves pour des missions ulterieures.
