# Connecteurs complémentaires 1 — Rapport de tests

## Référence

- SHA audité : `bd16f8644f8e5d1767e7f026478aaf95d9ddade7`
- Python : syntaxe 3.10 validée
- Réseau : interdit pendant les tests

## Tests propres au lot

Résultat : **32 réussites**, aucun échec.

Couverture :

- contrats et enregistrement Connector Platform ;
- désactivation par défaut et politique metadata-only ;
- domaines officiels et HTTPS ;
- catalogues publics et identités stables ;
- rejet des champs de contenu et domaines tiers ;
- persistance JSON, idempotence et déduplication ;
- sélection Runtime ;
- citations ;
- fusion multi-source et hiérarchie ;
- passage par Connector Adapter et Core ;
- confidentialité et absence de réseau.

## Tests élargis impactés

Connector Platform, Document Registry, Runtime, confidentialité et connecteurs :
**453 réussites**, 686 désélectionnés, aucun échec.

## Scénarios métier

Trois scénarios principaux et un scénario multi-source réussissent :

1. discrimination syndicale — Défenseur des droits ;
2. procédure de licenciement — Ministère du Travail ;
3. démarche de modification du contrat — Service-Public ;
4. harcèlement au travail — fusion Défenseur des droits et Service-Public.

Le scénario témoin de paie ne déclenche aucune activation injustifiée.

Pour les trois scénarios principaux :

- connecteur attendu activé : 3/3 ;
- citation exploitable : 3/3 ;
- fallback `OFFICIAL_CONNECTORS_NO_RESULT` : 0/3.

## Suite complète

Résultat : **2 465 réussites, 128 sous-tests réussis et 3 échecs historiques
qualifiés** en 29,68 secondes.

Échecs historiques inchangés :

- `automation/adapters/test_payroll.py::DependencyTests::test_import_does_not_load_forbidden_packages`
- `automation/contracts/test_contracts.py::IsolationAndCompatibilityTests::test_import_does_not_load_domain_packages`
- `automation/experts/test_paie_referential_integration.py::test_integration_failure_preserves_legacy_expert_payload`

Nouveaux échecs : 0.

## Contrôles

- catalogues JSON : valides ;
- synchronisation déterministe : validée ;
- documents par connecteur : 4, 4 et 4 ;
- citations exploitables : 12 ;
- doublons : 0 ;
- données confidentielles : 0 ;
- contenu documentaire stocké : 0 ;
- appels réseau pendant les tests : 0 ;
- fallbacks supprimés : 3 chemins `OFFICIAL_CONNECTORS_NO_RESULT` sur les
  scénarios pertinents ;
- `git diff --check` : réussi ;
- syntaxe Python 3.10 : validée.

## Anomalies restantes

- anomalie nouvelle : 0 ;
- anomalies historiques hors périmètre : 3 ;
- fallback propre aux trois scénarios pertinents : 0.

## Verdict

**CONNECTEURS COMPLÉMENTAIRES 1 VALIDÉS**
