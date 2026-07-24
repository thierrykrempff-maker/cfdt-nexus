# LOT R1C — Rapport de tests

## Référence

- SHA audité : `af9ef9be31677b3beef450c83df479e32319cdcb`
- Branche : `syndical-reasoning-r1c-working-time`
- État : aucun commit, push, merge, rebase ou squash

## Couverture

- qualifications prudentes et notions voisines ;
- organisation, horaires, pauses, repos, nuit, postes et 5x8 ;
- astreinte, intervention et déplacement ;
- Kelio, Nibelis et comparaisons metadata-only ;
- questions en quatre niveaux ;
- preuves et limites probatoires ;
- positions contradictoires ;
- cinq stratégies graduées ;
- dix scénarios synthétiques ;
- articulation R1A/R1B/R1C ;
- feature flag, Runtime et fallback ;
- immutabilité, déterminisme, confidentialité et Python 3.10.

## Résultats

- R1C seul : `47 passed in 0.46s`.
- Suites ciblées R0 à R1C : `122 passed in 0.63s`.
- Runtime, orchestrateur et raisonnement syndical :
  `290 passed, 845 deselected in 1.24s`.
- Répertoire `tests/` : `1121 passed in 6.55s`.
- Suite complète :
  `2598 passed, 128 subtests passed, 3 failed in 30.88s`.

Les trois échecs sont les anomalies historiques qualifiées :

1. `automation/adapters/test_payroll.py::DependencyTests::test_import_does_not_load_forbidden_packages`
2. `automation/contracts/test_contracts.py::IsolationAndCompatibilityTests::test_import_does_not_load_domain_packages`
3. `automation/experts/test_paie_referential_integration.py::test_integration_failure_preserves_legacy_expert_payload`

Aucun nouvel échec n'est introduit par R1C.

## Contrôles

- Confidentialité et fixtures synthétiques : conformes.
- Calcul réel de paie : aucun.
- Import Expert Paie ou réseau : aucun.
- API publiques R0 à R1C : importables.
- Syntaxe Python 3.10 : validée.
- `git diff --check` : réussi.
