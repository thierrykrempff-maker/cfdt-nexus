# CNIL — migration Connector Platform LOT 2

## Architecture avant

CNIL exposait un protocole et une façade dont toutes les opérations étaient bloquées, des modèles sérialisables, une sélection allow-list, une politique documentaire et de licences issue de l'étude d'accès, ainsi qu'un parseur réservé aux données synthétiques. Les refus, la provenance et les empreintes relevaient de composants spécifiques.

## Architecture après

`cnil_platform.py` est l'unique composition interne. Il utilise `ConnectorContract`, `ConnectorState`, `Capability`, `ConnectorMetadata`, `validate_contract`, `DocumentPolicy`, `LicenseId`, `ConnectorRegistry`, `ConnectorStatistics`, `Metric`, `HealthReport`, `ConnectorPlatformError`, `ErrorCode` et la politique de sécurité commune.

Les modèles historiques proposent des conversions explicites vers `Citation` et `Provenance` et utilisent `fingerprint_metadata`. Les classes, fonctions et modèles CNIL existants restent les façades publiques. La migration repose sur la composition et non sur un héritage artificiel.

## Comportements conservés

- source désactivée et statut `architecture_only` ;
- `NETWORK_DISABLED_BY_DEFAULT` ;
- message `CNIL_CONNECTOR_NETWORK_NOT_IMPLEMENTED` inchangé ;
- toutes les opérations de découverte, récupération, validation par connecteur, parsing par connecteur et synchronisation restent bloquées ;
- politique `METADATA_ONLY` ;
- licence historique CC BY-ND conservée, avec les statuts de revue existants dans le catalogue ;
- allow-list, refus transactionnels, contrôles MIME/taille/thème et sérialisation inchangés ;
- statistiques et métriques à zéro, santé `disabled`.

L'exception générique reste un sous-type de `RuntimeError`. Aucun transport, endpoint, API, téléchargement, authentification, cache, scheduler ou scraping n'est ajouté. L'étude d'accès et le parseur synthétique ne sont pas modifiés.

## Limites et tests

Les capacités déclarées (`HTML`, `PDF`, `OPEN_DATA`, `MANUAL`) décrivent uniquement les formats documentaires historiques ; elles n'activent aucune opération. Les tests de migration couvrent le contrat, l'état, la licence, les citations, la provenance, l'empreinte, la sécurité, le registre, la santé, les statistiques, les métriques, les erreurs et la compatibilité de sérialisation et d'imports.
