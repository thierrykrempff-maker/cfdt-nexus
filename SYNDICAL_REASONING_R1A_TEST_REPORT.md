# LOT R1A — Rapport de tests

## Référence

- SHA audité : `acfb7812d70677a355457a265a144df214f8ca28`
- Branche : `main`
- État : R0 et R1A non committés

## Couverture

- qualifications concurrentes ;
- détection des dimensions ;
- questions automatiques et priorités ;
- cinq stratégies progressives ;
- arguments salarié et employeur ;
- preuves indispensables, utiles et complémentaires ;
- cinq scénarios synthétiques ;
- sélection Runtime R1A ;
- conservation du feature flag R0 ;
- déterminisme, confidentialité et metadata-only.

## Résultats

- Suite ciblée R0 + R1A : `40 passed in 0.61s`.
- Suite élargie Runtime, orchestrateur, experts, connecteurs et confidentialité :
  `306 passed, 1352 deselected, 3 subtests passed in 1.55s`.
- Répertoire `tests/` : `1039 passed in 7.26s`.
- Suite complète : `2516 passed, 128 subtests passed, 3 failed in 24.09s`.

Les trois échecs de la suite complète sont les anomalies historiques qualifiées :

1. `automation/adapters/test_payroll.py::DependencyTests::test_import_does_not_load_forbidden_packages`
2. `automation/contracts/test_contracts.py::IsolationAndCompatibilityTests::test_import_does_not_load_domain_packages`
3. `automation/experts/test_paie_referential_integration.py::test_integration_failure_preserves_legacy_expert_payload`

Aucun nouvel échec n'est introduit par le LOT R1A.

## Contrôles

- Confidentialité et modèle metadata-only : conformes.
- Appel réseau ou dépendance réseau nouvelle : aucun.
- API publiques : importables.
- Syntaxe Python 3.10 : validée.
- `git diff --check` : réussi.
