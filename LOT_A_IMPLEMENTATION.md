# LOT A — Raccordement Runtime des connecteurs officiels

## Référence

- SHA audité : `bd16f8644f8e5d1767e7f026478aaf95d9ddade7`
- Périmètre : CARSAT, France Chimie, ANACT et Droit local
- Politique documentaire : `METADATA_ONLY`
- Date de synchronisation des catalogues contrôlés : `2026-07-24`

## Architecture retenue

Le raccordement réutilise exclusivement les composants publics déjà présents :

1. les catalogues JSON fournissent des métadonnées publiques, déterministes et sans contenu ;
2. `additional_metadata_feed` valide les domaines, HTTPS et les champs autorisés ;
3. le `DocumentRegistry` assure l'identité stable, la persistance JSON, l'idempotence, les mises à jour et les suppressions logiques ;
4. `OfficialConnectorsRuntime` sélectionne uniquement les connecteurs pertinents ;
5. les métadonnées sont converties en snapshots par le Connector Adapter, puis transmises au Core et à l'orchestrateur commun ;
6. les citations publiques sont dédupliquées avant fusion avec les autres sources.

Le chargement est hors ligne. Le script de synchronisation explicite ne contient aucun client HTTP et ne contacte aucune source distante.

## Fichiers réellement modifiés ou créés

- `NEXUS_RUNTIME_INTEGRATION/official_connectors_runtime.py`
- `automation/local_law/public_metadata.json`
- `automation/official_knowledge/additional_metadata_feed.py`
- `automation/official_knowledge/connectors/anact/public_metadata.json`
- `automation/official_knowledge/connectors/carsat/public_metadata.json`
- `automation/official_knowledge/connectors/france_chimie/public_metadata.json`
- `automation/official_knowledge/test_additional_metadata_feed.py`
- `automation/scripts/sync_additional_official_metadata.py`
- `tests/test_runtime_additional_official_connectors.py`
- `LOT_A_IMPLEMENTATION.md`
- `LOT_A_TEST_REPORT.md`

## État par connecteur

| Connecteur | Contrat / catalogue | Documents actifs | Citations exploitables | Activation Runtime |
|---|---:|---:|---:|---|
| CARSAT | conforme | 3 | 3 | retraite, C2P, prévention et risques professionnels |
| France Chimie | conforme | 2 | 2 | convention, classification, coefficients et accords Chimie |
| ANACT | conforme | 3 | 3 | QVCT, ARACT, transformations et organisation du travail |
| Droit local | conforme | 2 | 2 | Alsace-Moselle, jours fériés et maintien de salaire local |

Total : 10 documents metadata-only et 10 citations publiques.

Les catalogues utilisent des URL HTTPS autorisées. Les identifiants sont générés par `stable_document_id(connector_name, canonical_url)`. La date `last_checked` est renseignée et persistée. Les synchronisations répétées produisent le même registre et ne créent aucun doublon.

## Sélection et fusion Runtime

- sélection par marqueurs métier et domaines routés ;
- absence d'activation sur une question de paie sans rapport ;
- déduplication par identité documentaire stable ;
- coexistence avec Légifrance, JUDILIBRE, CDTN, CNIL, DREETS et INRS ;
- catégories de sources conservées pour appliquer la hiérarchie officielle ;
- passage vérifié par le Connector Adapter, le Core V3 et l'orchestrateur commun.

Quatre scénarios dédiés sont couverts :

1. CARSAT — C2P et départ anticipé ;
2. France Chimie — classification conventionnelle ;
3. ANACT — démarche QVCT ;
4. Droit local — maintien du salaire en Alsace-Moselle.

Dans chacun de ces scénarios, le connecteur attendu est appelé, produit au moins une citation et ne déclenche plus `OFFICIAL_CONNECTORS_NO_RESULT`.

## Confidentialité et limites

- aucune donnée personnelle, d'entreprise ou interne ;
- aucun texte intégral, extrait, HTML, PDF ou chunk ;
- aucun chemin local dans les résultats publics ;
- aucun appel réseau pendant les tests ;
- aucun secret ni identifiant d'authentification ;
- catalogues publics contrôlés et synchronisation locale explicite.

Limite acceptée : ce LOT fournit une alimentation metadata-only contrôlée. Une actualisation distante automatique n'est pas introduite.
