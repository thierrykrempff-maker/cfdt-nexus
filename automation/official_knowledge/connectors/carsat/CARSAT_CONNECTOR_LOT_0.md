# CARSAT — LOT 0 — Audit et architecture du connecteur

## Périmètre

Ce lot crée uniquement un contrat Connector Platform inactif. Aucun site n'a été consulté, aucun endpoint n'est enregistré et aucun transport, téléchargement, scraping, cache, scheduler, index ou mécanisme d'authentification n'est créé.

## Missions à confirmer officiellement

Le catalogue prépare cinq axes institutionnels généraux : prévention des risques professionnels, retraite, service social, tarification des accidents du travail et maladies professionnelles, et santé au travail. Leur périmètre exact, leur articulation régionale et l'autorité de chaque publication devront être vérifiés dans un lot d'étude séparé.

## Familles documentaires préparées

- guides de prévention et fiches pratiques ;
- recommandations techniques et publications régionales ;
- informations retraite et service social ;
- informations de tarification AT/MP ;
- formulaires, FAQ, actualités et outils.

Aucun schéma de référence documentaire stable n'est affirmé. Les identifiants éventuels devront être constatés sur des sources officielles avant d'être modélisés.

## Possibilités futures non validées

API, RSS, HTML, PDF, OpenData et saisie manuelle sont enregistrés exclusivement comme sujets de revue. Leur état est `pending_official_review` et `operational = false`. Leur présence, leur licence, leurs conditions d'utilisation et leur stabilité ne sont pas présumées.

## Politique documentaire

La politique est `METADATA_ONLY` avec `LicenseId.DOCUMENT_SPECIFIC`. Toute citation future devra préserver URL, titre, attribution CARSAT, date, version, niveau d'autorité, licence et confiance. La provenance devra conserver l'identifiant de source, l'URL canonique et une empreinte déterministe des métadonnées.

## Sécurité et limites

Le connecteur reste `enabled = false`, `architecture_only`, `NETWORK_DISABLED_BY_DEFAULT` et `HealthStatus.DISABLED`. Découverte, récupération et synchronisation lèvent `CARSAT_CONNECTOR_NETWORK_NOT_IMPLEMENTED`, compatible avec `RuntimeError`. Les statistiques et métriques restent à zéro.

Risques à étudier : pluralité régionale des CARSAT, responsabilités partagées avec l'Assurance retraite et l'Assurance maladie, droits document par document, versionnement, références, autorité respective des ressources nationales et régionales, redirections éventuelles vers des domaines administratifs distincts.

## Points restant à étudier

1. missions et périmètres officiels par organisme ;
2. mentions légales, licences et règles de réutilisation ;
3. structure documentaire, identifiants et versionnement ;
4. existence technique d'API, RSS, sitemap, HTML structuré, PDF ou OpenData ;
5. stratégie de citation et de provenance par famille ;
6. éventuel lot d'accès en lecture seule, uniquement après validation séparée.
