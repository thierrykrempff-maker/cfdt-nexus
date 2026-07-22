# Runtime Integration LOT 6 — connecteurs officiels existants

## Inventaire vérifié

Six paquets existent sous `automation/official_knowledge/connectors`.

| Connecteur | État constaté | Données hors ligne | Raccordement LOT 6 |
|---|---|---:|---:|
| CNIL | découverte de métadonnées injectées, testée ; transport bloqué | oui | oui |
| DREETS Grand Est | découverte de métadonnées injectées, testée ; transport bloqué | oui | oui |
| INRS | découverte et synchronisation de métadonnées injectées, testées | oui | oui |
| CARSAT | modèles et synchronisation testés, sans façade de découverte | partiel | non |
| France Chimie | validation et synchronisation testées, domaines actifs vides | partiel | non |
| ANACT | socle et synchronisation testés ; découverte publique non implémentée ; transports historiques isolés | partiel | non |

Légifrance, JUDILIBRE et Code du Travail Numérique restent raccordés par le LOT 2 et ne sont pas réimplémentés ici.

## Architecture

Le flag `NEXUS_OFFICIAL_CONNECTORS_RUNTIME_ENABLED`, désactivé par défaut, autorise uniquement le traitement de métadonnées déjà présentes dans `answer.sources`. Les origines reconnues sont `cnil`, `dreets_grand_est` et `inrs`.

La passerelle appelle les API publiques de découverte existantes, produit des `ConnectorAdapterInput` sans contenu, puis les ajoute aux entrées déjà transmises à `GenericConnectorAdapter`. Les résultats suivent le chemin existant : Connector Adapter → Nexus Core V3 → `PipelineExecutor` → `CommonExpertOrchestrator`.

Tout lot invalide ferme l'ensemble de la contribution LOT 6. Les entrées des LOT précédents et le rapport historique restent inchangés. Le diagnostic se limite à `connector_runtime_called`, `connector_runtime_ms`, `connectors_used` et `connector_runtime_fallback`.

## Limites

- Aucun transport, scraping, téléchargement ou accès au réseau n'est ajouté.
- Le LOT ne découvre pas lui-même de nouvelle source : il traite uniquement des métadonnées déjà fournies par le routeur.
- CARSAT nécessite une façade de découverte publique avant raccordement.
- France Chimie reste bloqué tant que sa politique de domaines actifs est vide.
- ANACT reste bloqué tant que sa découverte publique lève `operation_not_implemented`.

## Tests

Les tests couvrent le flag, l'appel réel des trois façades, le fail-closed, la confidentialité, le passage par le Connector Adapter, le Core, le pipeline, l'orchestrateur commun et le serveur local.
