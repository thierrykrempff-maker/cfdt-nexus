# Connecteurs complémentaires 2 — Implémentation

## Référence

- SHA audité : `bd16f8644f8e5d1767e7f026478aaf95d9ddade7`
- Sources : Assurance Maladie (CPAM), URSSAF et Agirc-Arrco
- Politique documentaire : `METADATA_ONLY`
- Synchronisation contrôlée : `2026-07-24`

## Architecture

Les trois sources réutilisent la façade commune des connecteurs officiels :

1. contrat Connector Platform validé et désactivé par défaut ;
2. catalogue JSON public et hors ligne ;
3. validation stricte du domaine officiel et de HTTPS ;
4. identité `stable_document_id(connector_id, canonical_url)` ;
5. persistance déterministe dans le `DocumentRegistry` ;
6. sélection Runtime par contexte métier ;
7. adaptation vers le Core et l'orchestrateur sans contenu documentaire.

## Connecteurs

| Connecteur | Identifiant | Domaine | Documents | Citations |
|---|---|---|---:|---:|
| Assurance Maladie (CPAM) | `assurance_maladie` | `www.ameli.fr` | 4 | 4 |
| URSSAF | `urssaf` | `www.urssaf.fr` | 4 | 4 |
| Agirc-Arrco | `agirc_arrco` | `www.agirc-arrco.fr` | 4 | 4 |

Total : 12 documents publics et 12 citations metadata-only.

## Sélection Runtime

- Assurance Maladie : IJSS, arrêt maladie, AT/MP, invalidité, maternité et
  temps partiel thérapeutique.
- URSSAF : cotisations, exonérations, assiettes, rémunérations, heures
  supplémentaires et avantages en nature.
- Agirc-Arrco : retraite complémentaire, points, carrière, départ, retraite
  progressive et droits complémentaires.

Le domaine `protection_sociale` active l'Assurance Maladie. Le domaine
`retraite_penibilite` active CARSAT et Agirc-Arrco, qui couvrent des niveaux
complémentaires. Les marqueurs précis évitent l'activation des trois sources
sur une question CSE sans rapport.

Les scénarios combinant IJSS et cotisations fusionnent Assurance Maladie et
URSSAF. Les identités documentaires restent uniques. Les catégories de source
`SOCIAL_SECURITY_BODY` permettent au Connector Adapter de préserver la
hiérarchie officielle.

## Fichiers du lot

- `NEXUS_RUNTIME_INTEGRATION/official_connectors_runtime.py`
- `automation/official_knowledge/additional_metadata_feed.py`
- `automation/official_knowledge/test_additional_metadata_feed.py`
- `automation/official_knowledge/connectors/complementary_official/platform.py`
- `automation/official_knowledge/connectors/complementary_official/test_complementary_official.py`
- `automation/official_knowledge/connectors/complementary_official/assurance_maladie_metadata.json`
- `automation/official_knowledge/connectors/complementary_official/urssaf_metadata.json`
- `automation/official_knowledge/connectors/complementary_official/agirc_arrco_metadata.json`
- `tests/test_runtime_additional_official_connectors.py`
- `tests/test_runtime_social_official_connectors.py`
- `CONNECTEURS_COMPLEMENTAIRES_2_IMPLEMENTATION.md`
- `CONNECTEURS_COMPLEMENTAIRES_2_TEST_REPORT.md`

## Confidentialité

- aucune donnée personnelle, d'entreprise ou interne ;
- aucun dossier d'assuré ou d'employeur ;
- aucun texte intégral, résumé, extrait, PDF, HTML ou chunk ;
- aucun client HTTP et aucun appel réseau dans les tests ;
- aucun secret, jeton ou identifiant d'authentification ;
- uniquement des métadonnées de pages publiques officielles.
