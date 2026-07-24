# Implémentation R2A — Moteur de raisonnement CSE

## Architecture

Le domaine est composé de modèles immuables, d'une politique déterministe, d'un
moteur prudent et de quinze scénarios synthétiques. La façade publique expose les
contrats stables. Le Runtime sélectionne R2A seulement lorsqu'un besoin CSE
collectif est détecté ; un cas individuel isolé revient à R1A.

## Modèles et chronologie

Le modèle décrit le projet, les effectifs et services, la décision, la mise en
œuvre, l'information/consultation, l'avis, les documents et les impacts. La
chronologie sépare annonce, information, transmission, réunion, avis, décision
et mise en œuvre, avec date certaine ou approximative, acteur, confiance et
échéance.

## Qualification et dimension collective

La dimension distingue cas isolé, répétition, pratique générale, projet identifié
et projet non démontré. Les sorties utilisent uniquement des formulations
prudentes : dimension collective possible, consultation potentiellement requise,
mise en œuvre anticipée apparente et éléments insuffisants pour conclure.

## Information, consultation et négociation

Une politique unique indique le mécanisme potentiel, l'acteur compétent, le
moment d'intervention, les pièces nécessaires et les points à confirmer. Elle
sépare clairement CSE et organisations syndicales.

## Documents et historique CSE

Les demandes sont classées indispensables, utiles et complémentaires. La
passerelle `CSEMemoryLookup` est injectée et metadata-only. Un résultat historique
invite à consulter la source ; il ne prouve ni engagement ni réponse.

## Entrave, contradictoire et stratégies

Le risque d'entrave contient indices, lacunes, alternatives, actions préalables
et recommandation de revue juridique. Deux positions distinctes présentent les
arguments du CSE/salariés et de l'employeur. Cinq niveaux gradués vont de la
sécurisation au recours.

## Articulation R1A–R1E

- individuel isolé : R1A principal ;
- sanction liée au projet : complément R1B ;
- horaires et conséquences paie : complément R1C ;
- discrimination : complément R1D ;
- santé, absence, inaptitude : complément R1E ;
- projet collectif documenté : R2A principal.

## Runtime et confidentialité

Le feature flag syndical existant est conservé. Toute exception entraîne le
fallback historique. Aucun contenu documentaire, chemin local, chunk, donnée
personnelle ou document réel n'est exposé.

## Limites

Le moteur ne conclut ni à l'obligation certaine de consultation, ni à une
illégalité, ni à un délit d'entrave, ni à une expertise. Il ne traite pas le fond
santé-sécurité réservé à un futur domaine CSSCT.
