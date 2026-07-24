# Rapport de tests R2B

## Résultats

- Tests R2B ciblés : 40 réussites.
- Chaîne Syndical Reasoning R0 à R2B et intégration Runtime : 311 réussites.
- Tests CSE Memory concernés : 78 réussites.
- Tests Common Expert Orchestrator : 14 réussites.
- Répertoire `tests/` : 1 310 réussites.
- Suite complète : 2 787 réussites et 128 sous-tests réussis.
- Échecs nouveaux : aucun.

Les trois seuls échecs de la suite complète sont les anomalies historiques
qualifiées :

1. `automation/adapters/test_payroll.py::DependencyTests::test_import_does_not_load_forbidden_packages`
2. `automation/contracts/test_contracts.py::IsolationAndCompatibilityTests::test_import_does_not_load_domain_packages`
3. `automation/experts/test_paie_referential_integration.py::test_integration_failure_preserves_legacy_expert_payload`

## Contrôles

- Fixtures : synthétiques, anonymes, fictives et metadata-only.
- Document réel : aucun.
- Réseau : aucun import ni appel.
- Délais : aucun calcul juridique automatique.
- Cible syntaxique : Python 3.10.
- API publique : importable.
- `git diff --check` : réussi.
