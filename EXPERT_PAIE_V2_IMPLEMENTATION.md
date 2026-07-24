# Implémentation Expert Paie V2

## Architecture

Le package sépare modèles, normalisation, sélection, validation, comparaisons,
calcul Decimal, orchestration et scénarios. Le Runtime P2A possède son propre
feature flag et ne modifie pas le comportement historique lorsqu'il est
désactivé.

## Frontières

- Détection : identifie une incidence potentielle.
- Contrôle : rapproche les sources disponibles.
- Simulation : emploie uniquement des données synthétiques.
- Calcul autorisé : exige une règle active, autorisée, complète et cohérente.
- Refus : expose le motif, les données et documents manquants et l'action.

## Modèles et normalisation

Les modèles immuables couvrent période, salarié synthétique, événements,
compteurs, rubriques, paramètres, règles, variables, unités, comparaisons,
calculs, refus, preuves, questions et stratégies. Les décimales, dates, unités
et provenances sont contrôlées sans correction silencieuse.

## Règles et validation

La sélection respecte : accord INEOS, convention collective, Code du travail,
paramètre officiel puis règle interne validée. Une règle inactive, à vérifier,
contestée ou non autorisée ne peut produire aucun calcul.

## Comparaisons

Le moteur propose planning/Kelio, Kelio/Nibelis, règle/traitement observé et
IJSS/maintien/subrogation, avec concordance, écart apparent, anomalie possible,
données insuffisantes ou absence d'anomalie. Une rubrique du mois suivant est
reconnue comme décalage potentiel afin d'éviter une fausse alerte.

## Calcul et explications

Le calcul synthétique autorisé emploie `Decimal`, trace base, quantité, taux,
formule, étapes, arrondi, résultat et source. Les versions salarié et expert
restent prudentes et ne déclarent jamais une erreur certaine.

## Questions, preuves et stratégies

Les questions sont hiérarchisées. Les preuves sont classées indispensables,
utiles et complémentaires. Cinq stratégies couvrent reconstitution,
comparaison, vérification, régularisation et recours.

## Articulation et Runtime

R1C qualifie les événements de temps ; R1E qualifie maladie, IJSS,
subrogation et prévoyance ; Expert Paie V2 contrôle les conséquences paie ;
R2C peut recevoir les constats collectifs. Le flag
`NEXUS_EXPERT_PAIE_V2_RUNTIME_ENABLED` est désactivé par défaut. Toute exception
produit un fallback technique sans casser l'expert historique.

## Confidentialité et limites

Aucun bulletin, salaire, taux, matricule, compteur ou dossier réels n'est
présent. Aucun réseau ni chargement documentaire n'est utilisé. La validation
humaine reste obligatoire.
