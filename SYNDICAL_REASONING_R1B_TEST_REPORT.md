# LOT R1B — Rapport de tests

## Référence

- SHA audité : `acfb7812d70677a355457a265a144df214f8ca28`
- Branche : `main`
- État : R0, R1A et R1B non committés

## Couverture

- qualifications disciplinaires concurrentes et provisoires ;
- procédure, dates, convocation, entretien, assistance et notification ;
- questions automatiques prioritaires ;
- argumentations salarié et employeur indépendantes ;
- preuves indispensables, utiles et complémentaires ;
- stratégies graduées ;
- salarié protégé et autorisation administrative éventuelle ;
- sept scénarios synthétiques ;
- sélection Runtime R1B, priorité sur R1A et conservation de R0 ;
- feature flag, fallback, déterminisme, metadata-only et confidentialité.

## Résultats

- Suites ciblées R0, R1A et R1B : `75 passed in 0.61s`.
- Runtime, orchestrateur et raisonnement syndical :
  `243 passed, 845 deselected in 1.08s`.
- Répertoire `tests/` : `1074 passed in 6.78s`.
- Suite complète :
  `2551 passed, 128 subtests passed, 3 failed in 21.30s`.

Les trois échecs sont les anomalies historiques qualifiées :

1. `automation/adapters/test_payroll.py::DependencyTests::test_import_does_not_load_forbidden_packages`
2. `automation/contracts/test_contracts.py::IsolationAndCompatibilityTests::test_import_does_not_load_domain_packages`
3. `automation/experts/test_paie_referential_integration.py::test_integration_failure_preserves_legacy_expert_payload`

Aucun nouvel échec n'est introduit par R1B.

## Contrôles

- Confidentialité et metadata-only : conformes.
- Réseau, connecteur ou donnée réelle nouvelle : aucun.
- API publiques R0, R1A et R1B : importables.
- Syntaxe Python 3.10 : validée.
- `git diff --check` : réussi.
