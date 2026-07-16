# DREETS Grand Est — migration Connector Platform LOT 1

## Architecture avant

Le connecteur portait directement ses drapeaux `enabled` et `connector_status`, ses validations documentaires et ses refus réseau. Les modèles DREETS géraient seuls la restriction `METADATA_ONLY`. Les opérations indisponibles levaient directement une `RuntimeError` contenant le contrat historique.

## Architecture après

`dreets_platform.py` compose les composants génériques et devient la source de vérité interne :

- `ConnectorContract`, `ConnectorState`, `Capability` et `ConnectorMetadata` ;
- `validate_contract`, `DocumentPolicy` et `LicenseId` ;
- `Citation`, `Provenance` et empreinte générique ;
- `ConnectorRegistry` ;
- `ConnectorStatistics`, `Metric` et `HealthReport` ;
- `ConnectorPlatformError` et `ErrorCode` ;
- politique `SecurityPolicy` par défaut.

Les classes et fonctions DREETS historiques restent des façades de compatibilité. Il s'agit d'une composition contractuelle, pas d'un héritage fragile de dataclasses immuables.

## Compatibilité ascendante

- `DreetsGrandEstConnector.enabled` reste `False` ;
- `connector_status` reste `architecture_only` ;
- les méthodes `discover_resources`, `fetch_resource` et `classify_resource` restent indisponibles ;
- `synchronize` reste indisponible ;
- l'exception reste compatible avec `RuntimeError` et conserve exactement `DREETS_GRAND_EST_CONNECTOR_NETWORK_NOT_IMPLEMENTED` ;
- les modèles `DreetsDocumentType`, `DreetsResourceCandidate` et `ClassificationResult` sont conservés ;
- les dictionnaires sérialisés et règles de classement historiques ne changent pas.

Les modèles historiques ajoutent seulement des conversions explicites vers `DocumentPolicy`, `LicenseId`, `Citation` et `Provenance`.

## Garde-fous inchangés

Le contrat générique reste désactivé, `architecture_only`, `METADATA_ONLY` et sous `NETWORK_DISABLED_BY_DEFAULT`. Les capacités déclarées sont documentaires (`HTML`, `RSS`, `SITEMAP`, `PDF`, `MANUAL`) ; aucune capacité d'authentification, cache, synchronisation ou téléchargement n'est accordée.

Aucun transport, endpoint, cache actif, ordonnanceur, téléchargement, authentification ou scraping n'est introduit. Les statistiques et métriques sont initialisées à zéro et la santé est `disabled`.

## Tests de migration

Les tests vérifient la composition Connector Platform, l'état, la licence, les citations, la provenance, la politique documentaire, la sécurité, les capacités, le registre, les statistiques, les métriques, les erreurs et la compatibilité ascendante des refus historiques.
