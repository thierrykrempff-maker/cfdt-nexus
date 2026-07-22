# CFDT Nexus — campagne de validation fonctionnelle V1

## Finalité

Cette campagne évalue CFDT Nexus comme s’il devait être présenté demain à des délégués syndicaux CFDT. Elle mesure le comportement réellement observable du Runtime intégré sans définir ni suggérer les réponses métier attendues.

La matrice associée contient exactement 100 scénarios synthétiques. Aucun nom de salarié, matricule, document réel ou autre donnée personnelle n’est utilisé.

## Protocole d’exécution

Pour chaque scénario :

1. partir d’une session Runtime propre ;
2. configurer uniquement les feature flags nécessaires au scénario ;
3. soumettre exactement la question indiquée ;
4. relever les domaines, experts, connecteurs, sources, diagnostics et fallbacks réellement observés ;
5. noter séparément chaque dimension de 0 à 5 ;
6. consigner les écarts factuels sans réécrire la réponse ni corriger le produit pendant la campagne.

Les champs `domaines_attendus`, `experts_attendus`, `connecteurs_attendus` et `comportement_attendu` décrivent le parcours et les propriétés attendus. Ils ne constituent jamais une réponse juridique, conventionnelle ou chiffrée.

## Barème

Chaque dimension reçoit une note entière de 0 à 5 :

| Dimension | 0 | 3 | 5 |
|---|---|---|---|
| Routage | absent ou erroné | domaine principal atteint avec écarts | domaines et experts attendus atteints sans bruit |
| Exactitude juridique | dangereuse ou non fondée | globalement juste mais incomplète | exacte, nuancée et hiérarchisée |
| Qualité paie | calcul ou lecture inutilisable | traitement partiel | traitement cohérent, vérifiable et prudent |
| Utilisation des accords | accord ignoré ou mal priorisé | accord cité sans articulation complète | accord pertinent correctement articulé avec les normes supérieures |
| Utilisation des connecteurs | appel injustifié ou source perdue | sources partielles | connecteurs pertinents, provenance et fallback maîtrisés |
| Qualité de la synthèse | contradictoire | compréhensible avec redites | structurée, concise et actionnable |
| Références | absentes ou inventées | références partielles | références vérifiables, datées et correctement qualifiées |
| Lisibilité | incompréhensible | lisible avec effort | claire pour un représentant du personnel |
| Pertinence globale | hors sujet | utile mais incomplète | répond au besoin et explicite ses limites |

Une dimension non applicable doit être marquée `NA`, jamais artificiellement notée. Le score du scénario est la moyenne des seules dimensions applicables, ramenée sur 100. Une note de 0 en exactitude juridique, confidentialité ou provenance impose une revue bloquante indépendamment de la moyenne.

## Feature flags et observations

Les exécutions doivent relever au minimum l’état de :

- `NEXUS_CORE_RUNTIME_ENABLED` ;
- `NEXUS_CONNECTOR_RUNTIME_ENABLED` ;
- `NEXUS_CSE_MEMORY_RUNTIME_ENABLED` ;
- `NEXUS_RETIREMENT_RUNTIME_ENABLED` ;
- `NEXUS_PROTECTION_SOCIALE_RUNTIME_ENABLED` ;
- `NEXUS_OFFICIAL_CONNECTORS_RUNTIME_ENABLED`.

Pour les connecteurs officiels du LOT 6, une attente de raccordement signifie qu’une métadonnée officielle admissible est déjà fournie au Runtime. La campagne n’attend aucun accès réseau ni aucune collecte distante.

## Statistiques à produire après exécution

Le rapport d’exécution devra calculer :

- moyenne générale et médiane sur 100 ;
- moyenne par dimension de notation ;
- moyenne par domaine principal et par domaine attendu ;
- moyenne par expert attendu ;
- moyenne et taux d’appel par connecteur attendu ;
- taux de routage exact, de fallback et de réponses sans références ;
- cinq domaines, experts ou connecteurs les plus faibles avec effectif associé ;
- écarts entre difficulté facile, intermédiaire et complexe ;
- recommandations classées en bloquantes V1, importantes et différables.

Les agrégats doivent toujours afficher leur effectif. Aucun classement ne doit être publié pour un groupe comportant moins de trois scénarios sans signaler la faible représentativité.

## Critères de readiness proposés

- aucun incident de confidentialité ;
- aucun contenu ou référence inventé ;
- aucun échec utilisateur non absorbé par le fallback ;
- score global d’au moins 80/100 ;
- aucune moyenne de domaine inférieure à 70/100 ;
- routage conforme dans au moins 90 % des scénarios ;
- connecteurs attendus utilisés ou explicitement diagnostiqués dans au moins 90 % des cas applicables.

Ces seuils servent à décider de la readiness ; ils ne modifient aucun moteur et ne constituent pas une validation juridique des réponses.
