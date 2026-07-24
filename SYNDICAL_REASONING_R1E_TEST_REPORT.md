# Rapport de tests R1E

Le lot couvre les modèles immuables, quinze scénarios synthétiques, la chronologie, les acteurs, les questions, les preuves, les comparaisons, les urgences, les stratégies, l'articulation R1A–R1E, le Runtime, la confidentialité et l'absence de calcul.

## Résultats

- R1E : 58 réussites.
- Chaîne R0 à R1E : 196 réussites.
- Runtime syndical : 40 réussites.
- Orchestrateur commun : 14 réussites.
- Protection Sociale concernée : 75 réussites.
- Répertoire `tests/` : 1 235 réussites.
- Suite complète : 2 712 réussites et 128 sous-tests réussis.
- Nouveaux échecs : aucun.

Les trois échecs historiques restent strictement inchangés :

- `automation/adapters/test_payroll.py::DependencyTests::test_import_does_not_load_forbidden_packages`
- `automation/contracts/test_contracts.py::IsolationAndCompatibilityTests::test_import_does_not_load_domain_packages`
- `automation/experts/test_paie_referential_integration.py::test_integration_failure_preserves_legacy_expert_payload`

La syntaxe Python 3.10, l'API publique et `git diff --check` sont valides. Aucun import réseau, calcul réel, document médical ou donnée personnelle réelle n'est introduit.
