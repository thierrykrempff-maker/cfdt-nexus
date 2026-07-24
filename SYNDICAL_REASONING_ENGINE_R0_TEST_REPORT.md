# LOT R0 — Rapport de tests

Ce rapport est finalisé après exécution de toutes les validations.

## Référence

- SHA audité : `acfb7812d70677a355457a265a144df214f8ca28`
- Branche : `main`
- Python : 3.10 requis

## Couverture ciblée

- contrats d'entrée et sortie ;
- séparation faits / hypothèses ;
- informations manquantes ;
- qualification multi-domaines ;
- hiérarchie et contradictions ;
- confiance et prudence ;
- options progressives ;
- citations metadata-only ;
- scénario laboratoire / équipe postée ;
- feature flag, fallback et non-régression Runtime ;
- confidentialité et absence réseau.

## Résultats

- Tests ciblés R0 : 23 réussites.
- Suites élargies Runtime, orchestrateur, experts, connecteurs et
  confidentialité : 274 réussites, 3 sous-tests réussis, 1 367 tests
  désélectionnés.
- Suite `tests/` : 1 022 réussites.
- Suite complète : 2 499 réussites, 128 sous-tests réussis et 3 échecs
  historiques qualifiés.
- Nouvel échec : aucun.

## Échecs historiques

1. `automation/adapters/test_payroll.py::DependencyTests::test_import_does_not_load_forbidden_packages`
2. `automation/contracts/test_contracts.py::IsolationAndCompatibilityTests::test_import_does_not_load_domain_packages`
3. `automation/experts/test_paie_referential_integration.py::test_integration_failure_preserves_legacy_expert_payload`

Ces trois anomalies sont identiques à l'état de référence et ne sont pas
corrigées dans R0.

## Contrôles

- fixtures synthétiques uniquement ;
- aucun appel réseau dans les tests R0 ;
- aucune donnée personnelle réelle ;
- aucun document INEOS réel ;
- aucun chemin local dans les vues ou diagnostics ;
- feature flag désactivé par défaut ;
- rapport historique conservé à l'identique hors activation réussie ;
- syntaxe Python 3.10 validée ;
- `git diff --check` validé.

## Verdict

**LOT R0 — SOCLE DU MOTEUR DE RAISONNEMENT SYNDICAL VALIDÉ**
