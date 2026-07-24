# Implémentation R2C

## Architecture

Le domaine est isolé en quatre modules : modèles immuables, politiques
déterministes, moteur prudent et vingt scénarios synthétiques. La façade
publique expose les contrats stables. Le Runtime injecte le moteur et conserve
son feature flag et son fallback historiques.

## Modèles et chronologie

Les contrats représentent les réclamations, alertes potentielles, expertises,
enquêtes, saisines, preuves, acteurs, documents, questions, résolutions,
argumentations et stratégies. La chronologie sépare signalement, réclamation,
alerte formelle, résolution, réponse, engagement, mesure corrective et clôture.

## Réclamations et alertes

Le moteur distingue demande individuelle, réclamation individuelle, série de
cas similaires, réclamation collective, revendication, négociation et
contentieux individuel. Les alertes relatives aux droits des personnes,
économiques, sociales, au fonctionnement dégradé ou à un risque collectif ne
sont que des hypothèses à confirmer.

## Expertises, enquêtes et escalade

Les expertises sont décrites par objet, fondement potentiel, faits favorables
et défavorables, pièces, délai potentiel, financement à vérifier, décideur,
risques et confiance. Les enquêtes imposent licéité, neutralité,
confidentialité et périmètre. L'escalade va de la relance interne au recours,
avec compétence, prérequis, avantages, limites et alternative.

## Documents, questions et résolutions

Les demandes sont classées indispensables, utiles et complémentaires. Les
questions sont critiques, prioritaires, utiles ou complémentaires. Les
résolutions sont toujours des projets à relire, adapter et, si nécessaire,
faire valider juridiquement.

## Argumentation et stratégies

Deux positions contradictoires sont produites sans trancher. Cinq stratégies
graduées couvrent documentation, action interne, investigation, alerte ou
expertise potentielle, puis recours.

## Articulation

- R2A reste principal pour consultation et réorganisation.
- R2B traite ordre du jour, documents et fonctionnement courant.
- R2C traite la dimension collective, l'alerte, l'expertise et l'escalade.
- R1A à R1E restent principaux sur les dossiers individuels correspondants.

## Runtime et CSE Memory

L'activation exige un contexte CSE et des marqueurs collectifs ou
institutionnels. Le mot « alerte » seul et le cas individuel isolé ne
déclenchent pas R2C. L'historique est injecté par protocole metadata-only,
trié de façon déterministe et toujours présenté comme une piste à vérifier.

## Confidentialité et limites

Aucun document, PV, témoignage, donnée économique ou identité réels n'est
présent. Aucun réseau n'est utilisé. R2C ne traite ni le fond CSSCT, ni le DGI,
ni un diagnostic médical, ni une qualification automatique, ni un calcul de
délai ou de financement.
