# Filtre de pertinence Sarralbe V1

## Objectif

Ce module qualifie localement les résultats temporaires de veille pour déterminer leur utilité réelle pour le mandat CFDT à Sarralbe.

Il fonctionne par règles explicites et déterministes. Il ne simule pas une IA.

## Entrées

Le moteur lit par défaut le dernier fichier privé généré par les connecteurs :

```text
local-index/watch-connectors/*.private.json
```

Ces fichiers sont ignorés par Git et ne doivent pas être committés.

## Sorties

Le moteur écrit un rapport local privé dans :

```text
local-index/watch-relevance/
```

Le rapport contient les scores, thèmes, domaines, agents et actions suggérées.

## Commande

Depuis la racine du dépôt :

```bash
node watch/relevance/score-sarralbe.js
```

## Scoring

Le score est sur 100 :

- `0-24` : FAIBLE ;
- `25-49` : À SURVEILLER ;
- `50-74` : IMPORTANT ;
- `75-100` : PRIORITAIRE.

Chaque point ajouté doit avoir une raison visible.

## Prudence

Une action suggérée n'est jamais exécutée automatiquement.

Statut constant :

```text
ACTION SUGGÉRÉE — VALIDATION HUMAINE REQUISE
```

## Sécurité

Le module ne lit aucun accord INEOS, aucun PV CSE, aucune BDESE et aucune donnée nominative.

