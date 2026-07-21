# France Chimie — LOT 0 — Audit d'architecture préalable

## Décision

Le futur connecteur France Chimie peut être intégré sans modifier la Connector Platform, le Document Registry ni les connecteurs existants. Le modèle de référence doit être la chaîne INRS complète pour la découverte hors ligne et la synchronisation, complétée par la forme minimale et récente du moteur CARSAT.

Ce LOT 0 est exclusivement documentaire. Aucun domaine, endpoint, transport ou mécanisme de collecte n'est activé. Aucun appel réseau ni scraping n'a été effectué.

## Périmètre examiné

- façades, contrats, modèles, catalogues et compositions Connector Platform d'INRS et CARSAT ;
- découverte de métadonnées INRS par injection explicite ;
- modèles et synchronisations `METADATA_ONLY` INRS et CARSAT ;
- API publique de `automation.official_knowledge.document_registry` ;
- tests d'architecture, d'intégration, de découverte et de synchronisation ;
- garde-fous d'absence de réseau, téléchargement, PDF, HTML et contenu documentaire.

## Emplacement et nommage recommandés

Le connecteur devra être créé dans :

`automation/official_knowledge/connectors/france_chimie/`

Conventions recommandées :

- identifiant Connector Platform et Document Registry : `france_chimie` ;
- préfixe Python : `FranceChimie` pour les classes et `FRANCE_CHIMIE_` pour les constantes ;
- modules futurs : `france_chimie_connector.py`, `france_chimie_contract.py`, `france_chimie_models.py`, `france_chimie_platform.py`, `france_chimie_catalog.py`, puis `france_chimie_metadata.py`, `france_chimie_discovery.py` et `france_chimie_sync.py` ;
- tests colocalisés : architecture, intégration plateforme, découverte de métadonnées et synchronisation.

L'identifiant `france_chimie` respecte le format du Document Registry et évite un nom de paquet avec trait d'union.

## Intégration Connector Platform

Le LOT d'architecture devra reproduire les invariants INRS et CARSAT :

- `ConnectorState.ARCHITECTURE_ONLY` ;
- `enabled = false` ;
- `DocumentPolicy.METADATA_ONLY` ;
- `LicenseId.DOCUMENT_SPECIFIC` tant que les droits ne sont pas officiellement qualifiés ;
- `DEFAULT_SECURITY_POLICY` et `NETWORK_DISABLED_BY_DEFAULT` ;
- santé `DISABLED`, statistiques et métriques à zéro ;
- façade dont `discover()`, `fetch()` et `synchronize()` échouent fermées avec `ErrorCode.NETWORK_DISABLED` ;
- aucun `Capability.SYNC`, `DISCOVERY`, `DOWNLOAD`, `AUTHENTICATION`, `CACHE` ou autre capacité active avant validation séparée.

La liste des domaines officiels France Chimie n'est pas affirmée dans cet audit hors ligne. Elle devra être établie par une revue officielle distincte avant d'alimenter une allowlist ou un `DocumentValidator`. Aucun sous-domaine ne devra être accepté implicitement.

## Interfaces publiques du Document Registry

Le futur connecteur doit importer uniquement l'API publique exposée par `automation.official_knowledge.document_registry` :

- `DocumentRecord`, `DocumentStatus` et `ChangeKind` ;
- `DocumentRegistry` et, si nécessaire, le protocole public `DocumentStorage` ;
- `DocumentValidator` avec une configuration de domaines injectée ;
- `stable_document_id()` ;
- opérations `register_document()`, `update_document()`, `mark_removed()`, `find_document()` et `find_by_connector()`.

Il ne doit accéder ni à `_storage`, ni à `_validator`, ni aux méthodes privées du registre. Le registre reste injecté explicitement ; aucun singleton, registre global ou cache documentaire n'est autorisé.

## Convention de découverte des métadonnées

Le modèle INRS est la référence : un tuple immuable de mappings synthétiques ou prévalidés est injecté dans une fonction de découverte pure, bornée et déterministe. La découverte :

- reste désactivée par défaut et exige une activation booléenne explicite ;
- impose un quota borné, recommandé entre 1 et 100 ;
- canonicalise l'URL avant de calculer l'identité ;
- valide HTTPS et une allowlist exacte de domaines ;
- refuse PDF, données binaires, HTML brut et champs de contenu (`content`, `full_text`, `body`, `raw_html`, etc.) ;
- refuse les champs inconnus et les doublons contradictoires ;
- trie sa sortie de façon stable ;
- ne lit et n'écrit jamais le Document Registry.

Le modèle minimal doit contenir uniquement les métadonnées compatibles avec `DocumentRecord` et, si nécessaire, des références institutionnelles bornées conservées séparément. Aucun résumé susceptible de devenir un extrait documentaire ne devrait être prévu par défaut.

## Identité documentaire

L'identité doit être calculée exclusivement ainsi :

`stable_document_id("france_chimie", canonical_url)`

L'URL doit être canonicalisée avant le calcul. Une référence France Chimie éventuelle reste un champ de métadonnée et ne participe pas au `document_id`. Cette règle garantit que découverte et synchronisation produisent exactement la même identité. Lors d'une redirection explicitement validée, le moteur conserve le `document_id` antérieur tout en mettant à jour l'URL canonique.

## Synchronisation `METADATA_ONLY`

Le moteur recommandé reprend `InrsDocumentSync`/`CarsatDocumentSync` :

1. injection explicite d'un `DocumentRegistry` et d'un tuple immuable de métadonnées ;
2. lecture de l'état connu avec `find_by_connector("france_chimie")` ;
3. enregistrement des nouveautés avec `register_document()` ;
4. mise à jour via `update_document()` ;
5. suppression logique via `mark_removed()` ;
6. redirections fournies explicitement et validées en échec fermé ;
7. événements immuables triés par `(document_id, event_type)`.

Les seuls événements publics sont `NEW`, `UPDATED`, `REMOVED`, `REDIRECTED` et `UNCHANGED`. Les changements spécialisés du registre (`TITLE_CHANGED`, `DATE_CHANGED`, etc.) sont regroupés en `UPDATED`. Chaque événement contient uniquement `document_id`, `connector_name`, `event_type`, `detected_at`, `previous_snapshot` et `new_snapshot`. Les snapshots sont limités aux métadonnées de `DocumentRecord`.

La synchronisation doit être déterministe et idempotente : un document inchangé produit `UNCHANGED`, une ressource déjà supprimée ne produit pas une seconde suppression, et une redirection conserve l'identité lorsqu'elle relie une ancienne URL connue à une nouvelle métadonnée présente.

## Garde-fous et tests requis

Les futurs tests devront couvrir :

- contrat Connector Platform valide, état `ARCHITECTURE_ONLY`, désactivation et échec réseau fermé ;
- import public et compatibilité structurelle avec le Document Registry ;
- identité stable commune entre découverte, registre et synchronisation ;
- HTTPS, domaine exact, canonicalisation, PDF et HTML refusés ;
- champs de contenu et valeurs binaires impossibles à conserver ;
- quotas, doublons, ordre déterministe et dates ISO ;
- `NEW`, toutes les mises à jour de métadonnées, `REMOVED`, `REDIRECTED`, `UNCHANGED` ;
- immutabilité, stabilité, reproductibilité et idempotence des événements ;
- redirections invalides refusées en échec fermé ;
- analyse AST interdisant `requests`, `httpx`, `aiohttp`, `urllib`, `urllib.request`, `http.client` et `socket` dans les modules opérationnels ;
- aucune écriture hors des méthodes publiques du registre et aucune donnée réelle dans les fixtures.

## Écarts à éviter

- Ne pas copier la tolérance CARSAT à tout domaine : France Chimie devra disposer d'une allowlist exacte après validation officielle.
- Ne pas déclarer `HTML` ou `PDF` comme capacités opérationnelles au seul motif que ces formats pourraient exister.
- Ne pas dupliquer les modèles génériques du Document Registry ni accéder à ses détails internes.
- Ne pas créer de client HTTP, scraper, cache, persistance locale de document ou index de texte.
- Ne pas inventer de taxonomie, fréquence de collecte, endpoint, licence ou politique de redirection.

## Séquencement recommandé

1. LOT 0 d'architecture : façade inactive, contrat, modèles déclaratifs, catalogue et tests hors ligne.
2. Revue officielle séparée : domaine(s), mentions légales, licence, familles documentaires et mécanismes d'accès.
3. LOT de découverte : métadonnées injectées uniquement, allowlist validée et quotas.
4. LOT de synchronisation : intégration au Document Registry selon le moteur INRS/CARSAT.
5. Activation éventuelle : uniquement après validation juridique, sécurité et tests complets.

Conclusion : l'architecture existante est suffisante. Aucune évolution des composants communs n'est nécessaire pour accueillir France Chimie.
