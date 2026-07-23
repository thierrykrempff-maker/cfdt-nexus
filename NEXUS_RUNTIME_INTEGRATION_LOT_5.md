# Runtime Integration LOT 5 — Protection Sociale

## État avant le LOT

Le dépôt contient un pipeline documentaire local Protection Sociale : audit, import, normalisation, extraction de métadonnées et chunks techniques LOT 1A à LOT 1D. La façade commune déclare `protection_sociale` avec le statut `NOT_READY` car aucun expert autonome ni adaptateur spécialisé n'existe. Les sorties LOT 1D préparent une recherche future mais ne fournissent ni index sémantique ni API de recherche.

## Composants réellement réutilisés

- `automation.protection_sociale.chunk_models.Chunk` valide les sorties préparées LOT 1D.
- Les métadonnées LOT 1D fournissent domaine, sous-domaine et type documentaire.
- Le `GenericConnectorAdapter` transforme la projection métadonnées seule vers les objets du Core.
- `EngineRegistry`, `ExecutionPlanner` et `PipelineExecutor` exécutent réellement l'adaptation.
- `CommonExpertOrchestrator` reçoit un rapport technique non décisionnel.

## Architecture après raccordement

`Question → interface locale → routeur historique → experts historiques → détection Protection Sociale → lecture bornée LOT 1D → mapper Runtime → GenericConnectorAdapter → PipelineExecutor → CommonExpertOrchestrator → rapport enrichi`

La recherche est lexicale, déterministe, bornée et limitée aux métadonnées. Le texte des chunks, les chemins relatifs, les noms de fichiers et les identifiants du corpus ne sont jamais transmis au Core, au rapport ou aux diagnostics.

## Détection et feature flag

La détection utilise d'abord les domaines et intentions du routeur, puis une liste fermée de termes Protection Sociale. Les marqueurs ambigus nécessitent un contexte santé, mutuelle ou prévoyance afin de limiter les faux positifs Paie et Retraite.

Le flag `NEXUS_PROTECTION_SOCIALE_RUNTIME_ENABLED` est indépendant et désactivé par défaut. Sa désactivation conserve le parcours historique.

## Fallback et diagnostics

Toute indisponibilité, absence de résultat ou erreur de mapping, d'adaptation, de Core ou d'orchestration retourne exactement le rapport antérieur. Les diagnostics sont limités à `protection_sociale_called`, `protection_sociale_runtime_ms`, `protection_sociale_elements_used` et `protection_sociale_fallback`.

## Confidentialité et limites

Le corpus reste ignoré par Git et strictement en lecture seule. Aucun calcul de remboursement, couverture, capital, rente, indemnité, maintien de salaire ou reste à charge n'est effectué. Le rapport indique uniquement les références rapprochées et la nécessité d'une vérification auprès de l'organisme compétent.

Ne sont pas raccordés : un moteur métier Protection Sociale, une recherche sémantique, les connecteurs CPAM ou externes, et toute API distante.

## Tests

Les tests utilisent uniquement des chunks synthétiques et couvrent le flag, la détection, les faux positifs, la lecture seule, l'appel du modèle existant, le mapper, l'adaptateur générique, `PipelineExecutor`, `CommonExpertOrchestrator`, les fallbacks, l'intégration serveur et la confidentialité.
