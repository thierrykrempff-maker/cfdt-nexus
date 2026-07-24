# Connecteurs complémentaires 2 — Rapport de tests

## Référence

- SHA audité : `bd16f8644f8e5d1767e7f026478aaf95d9ddade7`
- Python : syntaxe 3.10 validée
- Réseau : neutralisé dans les tests

## Tests ciblés

Résultat : **43 réussites**, aucun échec.

Couverture :

- contrats et enregistrement Connector Platform ;
- catalogues publics et validation HTTPS ;
- identités stables ;
- Document Registry, persistance JSON, idempotence et déduplication ;
- sélection Runtime par marqueurs et domaines ;
- citations metadata-only ;
- passage Connector Adapter et Core ;
- absence de réseau et confidentialité.

## Tests élargis

Connector Platform, Document Registry, Runtime, confidentialité et
connecteurs : **458 réussites**, 686 désélectionnés, aucun échec.

## Scénarios

Cinq scénarios métier sont couverts :

1. CPAM — IJSS pendant un arrêt maladie ;
2. URSSAF — assiette des cotisations et avantages en nature ;
3. Agirc-Arrco — acquisition des points de retraite complémentaire ;
4. CPAM + URSSAF — traitement multisource des IJSS et cotisations ;
5. CPAM + URSSAF + Agirc-Arrco — passage commun par Connector Adapter et Core.

Un scénario CSE témoin confirme l'absence d'activation injustifiée.

- scénarios individuels activés : 3/3 ;
- citations individuelles exploitables : 3/3 ;
- fallback `OFFICIAL_CONNECTORS_NO_RESULT` : 0/3 ;
- doublons dans le scénario multisource : 0.

## Suite complète

Résultat : **2 476 réussites, 128 sous-tests réussis et 3 échecs historiques
qualifiés** en 29,17 secondes.

Échecs historiques inchangés :

- `automation/adapters/test_payroll.py::DependencyTests::test_import_does_not_load_forbidden_packages`
- `automation/contracts/test_contracts.py::IsolationAndCompatibilityTests::test_import_does_not_load_domain_packages`
- `automation/experts/test_paie_referential_integration.py::test_integration_failure_preserves_legacy_expert_payload`

Nouveaux échecs : 0.

## Contrôles

- documents Assurance Maladie : 4 ;
- documents URSSAF : 4 ;
- documents Agirc-Arrco : 4 ;
- citations exploitables : 12 ;
- doublons : 0 ;
- données confidentielles : 0 ;
- contenu documentaire stocké : 0 ;
- appels réseau pendant les tests : 0 ;
- fallbacks supprimés : 3 chemins `OFFICIAL_CONNECTORS_NO_RESULT` ;
- `git diff --check` : réussi ;
- syntaxe Python 3.10 : validée.

## Anomalies restantes

- anomalie nouvelle : 0 ;
- anomalies historiques hors périmètre : 3 ;
- fallback propre aux scénarios pertinents : 0.

## Verdict

**CONNECTEURS COMPLÉMENTAIRES 2 VALIDÉS**
