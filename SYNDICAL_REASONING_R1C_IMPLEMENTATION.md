# LOT R1C — Implémentation

## Architecture

R1C est une extension indépendante et metadata-only du
`SYNDICAL_REASONING_ENGINE`. Il reçoit un `SyndicalCaseInput`, conserve le rapport
transverse R0 et produit une projection typée dédiée au temps de travail.

Il ne dépend ni d'Expert Paie, ni de Kelio, ni de Nibelis. Ces noms désignent
uniquement des types de pièces synthétiques à rapprocher.

## Modèles

Les contrats immuables couvrent :

- trente-trois situations de temps, organisation, pause, repos et contrepartie ;
- organisation du travail et cycle ;
- horaires théoriques, déclarés et constatés ;
- astreintes, interventions, pauses et repos ;
- qualifications prudentes avec faits favorables, fragilités, données manquantes,
  sources, confiance, conséquences et urgence ;
- questions critiques, prioritaires, utiles et complémentaires ;
- preuves avec utilité, portée et limite probatoire ;
- comparaisons documentaires ;
- incidences potentielles sur la rémunération ;
- positions contradictoires ;
- cinq stratégies graduées ;
- articulation R1A/R1B/R1C.

## Distinctions garanties

- astreinte et intervention pendant astreinte ;
- trajet habituel et déplacement professionnel ;
- pause libre et pause interrompue avec disponibilité ;
- repos compensateur et récupération informelle ;
- travail de nuit et heure nocturne ponctuelle ;
- compteur technique et preuve définitive d'une erreur de paie.

## Comparaisons

Le moteur prépare neuf rapprochements déterministes :

- planning/badgeages ;
- planning/Kelio ;
- astreinte/intervention ;
- intervention/repos ;
- événement/Nibelis ;
- accord/traitement observé ;
- cycle prévu/cycle appliqué ;
- jours travaillés/compensation ;
- absence ou congé/compteur.

Les sorties parlent uniquement d'incohérence apparente, anomalie à vérifier,
événement non retrouvé, traitement potentiellement incomplet ou données
insuffisantes. Des explications alternatives sont toujours conservées.

## Incidences potentielles

R1C peut signaler heures supplémentaires, nuit, dimanche, jour férié, astreinte,
intervention, déplacement, repos compensateur, prime de poste, compteur ou
régularisation potentiels. Chaque résultat porte un niveau de vraisemblance et
les données requises. `calculation_performed` reste toujours faux.

## Stratégies

1. sécurisation factuelle ;
2. comparaison structurée ;
3. demande interne ;
4. action syndicale ou collective ;
5. recours adapté.

Chaque niveau décrit objectif, urgence, avantages, limites, risques, pièces,
résultat attendu et étape suivante.

## Articulation

- sanction ou procédure : R1B principal, R1C complémentaire si nécessaire ;
- modification imposée ou passage de jour en poste : R1A principal, R1C
  complémentaire ;
- compteur, pause, repos, astreinte ou contrepartie autonome : R1C principal ;
- autre demande syndicale : R0.

Aucune analyse complémentaire ne remplace ni ne contredit la qualification
principale.

## Runtime

Le feature flag existant est conservé. Le Runtime appelle R1C uniquement en
présence d'un domaine ou d'indicateurs temporels suffisants. Toute exception
spécialisée déclenche le fallback historique stable. Les résultats exposés sont
des métadonnées structurées.

## Confidentialité et limites

- fixtures anonymes et explicitement synthétiques ;
- aucun bulletin, planning, relevé ou document réel ;
- aucun réseau ni contenu documentaire ;
- aucun montant, taux, formule ou total de paie ;
- aucune violation ni erreur de paie déclarée comme certaine ;
- sources et périodes à confirmer avant toute conclusion.
