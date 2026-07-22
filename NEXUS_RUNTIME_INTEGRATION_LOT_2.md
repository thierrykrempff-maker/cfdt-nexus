# Nexus Runtime Integration — LOT 2

## Objet

Ce lot raccorde au Runtime les résultats de connecteurs déjà récupérés par le routeur historique. Il ne crée aucun connecteur, aucune API et aucun moteur. Le raccordement est progressif, désactivé par défaut et non bloquant.

## Architecture avant le lot

Le routeur appelait directement, selon la question et sa configuration, les scripts Légifrance, JUDILIBRE et Code du travail numérique. Il normalisait leurs résultats dans `answer.sources`. Juriste Travail et le générateur de rapport consommaient ensuite ces dictionnaires historiques. Le LOT 1 raccordait Juriste et Paie au Core, mais les résultats des connecteurs ne traversaient ni le Connector Adapter ni le Core V3.

## Architecture après le lot

Le chemin historique demeure inchangé :

`question -> serveur local -> assistant_ds_router -> connecteurs historiques -> answer.sources -> Juriste/rapport historique`

Avec `NEXUS_CORE_RUNTIME_ENABLED=true` et `NEXUS_CONNECTOR_RUNTIME_ENABLED=true`, une branche supplémentaire s'exécute après la récupération historique :

`answer.sources -> RuntimeConnectorPayloadMapper -> ConnectorResponseSnapshot -> GenericConnectorAdapter -> objets Core -> PipelineExecutor -> CommonExpertOrchestrator -> rapport enrichi`

Le routeur continue de décider quelles sources appeler. La couche Runtime ne modifie ni cette décision, ni le classement, ni le raisonnement juridique.

## Connecteurs réellement raccordés

- Légifrance Code du travail : origine Runtime `legifrance_code_travail`, catégorie `LEGISLATION`.
- JUDILIBRE : origine Runtime `judilibre_jurisprudence`, catégorie `CASE_LAW`.
- Code du travail numérique : origine Runtime `cdtn_pratique_officielle`, catégorie `ADMINISTRATIVE_DOCTRINE`.

Le mapper traite uniquement les sources déjà présentes dans la réponse du routeur. Il n'effectue aucun appel réseau. Un connecteur sollicité sans résultat produit un snapshot vide structuré.

## Connecteurs restant en attente

CARSAT, CNIL, INRS, DREETS Grand Est, ANACT et France Chimie possèdent des composants hors ligne, des modèles ou des moteurs de synchronisation. Ils ne sont toutefois pas appelés par `assistant_ds_router.py` et aucun de leurs résultats n'arrive dans `answer.sources`. Les brancher dans ce lot aurait nécessité une nouvelle logique de collecte ou de sélection, explicitement hors périmètre.

CPAM et CSSCT ne sont ni créés ni raccordés.

## Connector Adapter et Core V3

`RuntimeConnectorPayloadMapper` construit les objets publics `ConnectorAdapterInput`, `ConnectorDescriptor`, `ConnectorSourceSnapshot`, `ConnectorQuerySnapshot`, `ConnectorResponseSnapshot` et `ConnectorDocumentSnapshot`. `RuntimeCoreIntegration` appelle ensuite le véritable `GenericConnectorAdapter`.

Les `DocumentReference`, `Evidence`, `Finding` et `Provenance` produits sont enregistrés comme sorties d'un moteur d'intégration dans le véritable pipeline Core V3. Une façade immuable et minimale transmet au `CommonExpertOrchestrator` le statut d'adaptation et les compteurs de preuves, sans réexécuter les connecteurs ni exposer leur contenu dans les diagnostics.

## Feature flags et fallback

- `NEXUS_CONNECTOR_RUNTIME_ENABLED` : désactivé par défaut ; active la création et l'adaptation des snapshots.
- `NEXUS_CORE_RUNTIME_ENABLED` : doit également être activé pour exécuter le pipeline Core.

Si le flag connecteur est désactivé, le comportement LOT 1 est conservé. Une erreur de mapping produit `CONNECTOR_SNAPSHOT_MAPPING_FAILED`. Une erreur du Connector Adapter produit `CONNECTOR_ADAPTER_FAILED`. Dans les deux cas, les sources historiques restent dans `answer`, le rapport utilisateur reste disponible et Juriste/Paie peuvent continuer à traverser le Core.

## Diagnostics

Les diagnostics indiquent uniquement : activation, appel du Connector Adapter, nombre de connecteurs sollicités, nombre de snapshots, nombre de preuves intégrées, fallback et code technique. Ils ne contiennent aucune question, source, exception, stack trace, donnée personnelle ni contenu documentaire.

## Fichiers

Créé dans le package Runtime :

- `NEXUS_RUNTIME_INTEGRATION/connector_mapper.py`

Modifiés :

- `NEXUS_RUNTIME_INTEGRATION/__init__.py`
- `NEXUS_RUNTIME_INTEGRATION/config.py`
- `NEXUS_RUNTIME_INTEGRATION/integration.py`
- `NEXUS_RUNTIME_INTEGRATION/models.py`
- `apps/nexus-local-interface/server.py`

Tests créés :

- `tests/test_runtime_connector_mapper.py`
- `tests/test_runtime_connector_integration.py`
- `tests/test_runtime_connector_server_and_confidentiality.py`

Documentation :

- `NEXUS_RUNTIME_INTEGRATION_LOT_2.md`
- `NEXUS_RUNTIME_INTEGRATION_LOT_2_MATRIX.json`

## Tests et garanties

Les tests couvrent l'activation et la désactivation, les trois connecteurs raccordés, les snapshots vides, l'appel réel du Connector Adapter, le passage Core, le CommonExpertOrchestrator, le fallback de mapping, le fallback d'adaptation, la conservation du rapport historique et la confidentialité des diagnostics.

## Limites

Ce lot adapte uniquement les résultats déjà récupérés. Il ne change pas l'authentification, la disponibilité ou la qualité des services sources. Il ne raccorde pas les connecteurs officiels modernes absents du flux du routeur et ne modifie pas le raisonnement métier.
