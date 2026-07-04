# Connecteurs veille V1

## Objectif

Ce dossier contient les premiers connecteurs locaux de veille CFDT Nexus.

La V1 est volontairement limitée :

- peu de sources ;
- uniquement des pages publiques simples ;
- pas de scraping agressif ;
- pas de contournement de protection ;
- pas d'API inventée ;
- pas de données privées ;
- pas de publication automatique.

## Fichiers

- `sources-status.json` : état des sources testées, méthode retenue et limites.
- `fetch-watch.js` : commande locale de test pour les sources automatisables.

## Commande locale

Depuis la racine du dépôt :

```bash
node watch/connectors/fetch-watch.js
```

La commande écrit par défaut dans :

```text
local-index/watch-connectors/
```

Ce dossier est ignoré par Git. Les résultats réels de veille ne doivent pas être committés, car ils sont temporaires.

## Sources automatisées en V1

- INRS : page publique des actualités.
- France Chimie : page publique d'accueil / À la une.

## Sources manuelles ou à vérifier

- CFDT officielle : accès automatique instable/protégé, flux simple non confirmé.
- FCE-CFDT : page publique stable, mais le connecteur local reçoit `HTTP 403` en V1.
- Cour de cassation : page actualités demandant JS/cookies, flux simple non confirmé.
- ANACT : accès automatisé bloqué par protection anti-robot.

## Sorties métier prévues

Une nouveauté détectée pourra ensuite devenir :

- une alerte CSE ;
- une question CSSCT ;
- une veille juridique ;
- une idée d'article ;
- un point à vérifier dans les accords Sarralbe.

## Sécurité

Le connecteur ne doit jamais :

- lire un accord INEOS ;
- lire un PV CSE ;
- lire une BDESE ;
- utiliser un token ;
- utiliser une clé API ;
- publier sur le site public ;
- envoyer des données à un service externe.
