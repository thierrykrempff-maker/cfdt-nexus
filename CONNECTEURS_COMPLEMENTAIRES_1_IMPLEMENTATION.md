# Connecteurs complémentaires 1 — Implémentation

## Référence

- SHA audité : `bd16f8644f8e5d1767e7f026478aaf95d9ddade7`
- Sources : Défenseur des droits, Ministère du Travail et Service-Public
- Politique : `METADATA_ONLY`
- Synchronisation contrôlée : `2026-07-24`

## Architecture

Une façade commune et indépendante enregistre les trois sources dans la
Connector Platform. Chaque contrat est validé, désactivé par défaut, sans
transport et limité à la capacité manuelle metadata-only.

Les catalogues JSON ne contiennent que des métadonnées publiques. Ils sont :

1. validés par domaine officiel et HTTPS ;
2. transformés en `DocumentRecord` avec
   `stable_document_id(connector_id, canonical_url)` ;
3. persistables par le `DocumentRegistry` existant ;
4. dédupliqués et synchronisables de manière idempotente ;
5. chargés par le Runtime uniquement quand les marqueurs métier sont
   pertinents ;
6. transmis au Connector Adapter, au Core et à l'orchestrateur sous forme de
   citations sans contenu documentaire.

## État des connecteurs

| Connecteur | Domaine officiel | Documents | Citations | Catégorie Runtime |
|---|---|---:|---:|---|
| Défenseur des droits | `www.defenseurdesdroits.fr` | 4 | 4 | autorité indépendante |
| Ministère du Travail | `travail-emploi.gouv.fr` | 4 | 4 | doctrine administrative |
| Service-Public | `www.service-public.fr` | 4 | 4 | information pratique officielle |

Total : 12 documents et 12 citations metadata-only.

## Sélection Runtime

- Défenseur des droits : discrimination, harcèlement discriminatoire,
  égalité, liberté syndicale, handicap au travail, aménagement raisonnable et
  lanceurs d'alerte.
- Ministère du Travail : inspection du travail, procédures de licenciement,
  salariés protégés, rupture conventionnelle collective, actualités
  réglementaires et interprétations administratives.
- Service-Public : démarches des salariés, formalités, formulaires Cerfa,
  modèles de lettres et demandes administratives.

Les résultats de plusieurs sources sont fusionnés sans doublon. Une question
de paie sans rapport n'active aucun de ces connecteurs. Les catégories de
source distinctes préservent la hiérarchie officielle lors du passage dans le
Connector Adapter.

## Fichiers du lot

- `NEXUS_RUNTIME_INTEGRATION/official_connectors_runtime.py`
- `automation/official_knowledge/additional_metadata_feed.py`
- `automation/official_knowledge/test_additional_metadata_feed.py`
- `automation/official_knowledge/connectors/complementary_official/__init__.py`
- `automation/official_knowledge/connectors/complementary_official/models.py`
- `automation/official_knowledge/connectors/complementary_official/platform.py`
- `automation/official_knowledge/connectors/complementary_official/connector.py`
- `automation/official_knowledge/connectors/complementary_official/defenseur_droits_metadata.json`
- `automation/official_knowledge/connectors/complementary_official/ministere_travail_metadata.json`
- `automation/official_knowledge/connectors/complementary_official/service_public_metadata.json`
- `automation/official_knowledge/connectors/complementary_official/test_complementary_official.py`
- `tests/test_runtime_complementary_official_connectors.py`
- `CONNECTEURS_COMPLEMENTAIRES_1_IMPLEMENTATION.md`
- `CONNECTEURS_COMPLEMENTAIRES_1_TEST_REPORT.md`

## Confidentialité et limites

- aucune donnée personnelle, d'entreprise ou interne ;
- aucun texte intégral, résumé, extrait, HTML, PDF ou chunk ;
- aucun chemin local dans les sorties ;
- aucun client HTTP et aucun appel réseau dans le nouveau connecteur ;
- aucune authentification ni secret ;
- actualisation distante automatique hors périmètre.
