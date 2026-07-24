# LOT R1B — Implémentation

## Architecture

R1B ajoute une projection disciplinaire au `SYNDICAL_REASONING_ENGINE`. Elle
reçoit le contrat transverse `SyndicalCaseInput`, conserve intégralement le
rapport prudent R0 et réutilise les contrats de question, preuve, position et
stratégie introduits avec R1A.

Le moteur ne qualifie jamais définitivement une mesure. Toutes les
qualifications sont des candidates provisoires associées aux informations
décisives encore nécessaires.

## Procédures et situations couvertes

- rappel à l'ordre potentiellement non disciplinaire ;
- avertissement et blâme ;
- mise à pied, mutation et rétrogradation disciplinaires ;
- licenciement pour faute simple, grave ou lourde ;
- insuffisance professionnelle et insuffisance de résultats ;
- abandon de poste ;
- refus d'une modification du contrat ;
- représentant du personnel potentiellement protégé.

Lorsqu'un licenciement pour faute est évoqué, les degrés simple, grave et lourde
restent ouverts jusqu'à vérification des faits, preuves et effets.

## Analyse produite

L'analyse contient :

- la nature possible de la mesure ;
- onze contrôles de procédure, de délais, de motivation et de sources ;
- des questions automatiques triées par priorité ;
- une position salarié et une position employeur indépendantes ;
- des preuves indispensables, utiles et complémentaires ;
- six stratégies progressives, ou sept lorsqu'une protection est possible ;
- une vérification spécifique du mandat et de l'autorisation administrative
  éventuelle ;
- le rapport transverse R0.

## Runtime

Le feature flag existant `NEXUS_SYNDICAL_REASONING_RUNTIME_ENABLED` est conservé.
La sélection spécialisée suit l'ordre :

1. R1B pour un besoin disciplinaire ;
2. R1A pour un changement du contrat ou des conditions de travail ;
3. R0 pour toute autre question syndicale.

Le fallback historique est inchangé. L'analyse exposée est déterministe,
metadata-only et ne contient ni pièce brute ni identifiant personnel.

## Limites

- aucune sanction n'est déclarée justifiée ou injustifiée ;
- aucune protection ni autorisation administrative n'est présumée ;
- les délais et sources doivent être confirmés sur des pièces datées et des
  textes à jour ;
- aucune jurisprudence n'est déclarée comparable sans vérification ;
- aucune donnée réelle, aucun réseau et aucun connecteur ne sont introduits.
